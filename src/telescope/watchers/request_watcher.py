import hashlib
import json

from ..entry_type import EntryType
from ..recorder import Recorder
from ..settings import get_config
from .base import BaseWatcher


class RequestWatcher(BaseWatcher):
    """Records HTTP request/response data. Driven by middleware."""

    def register(self):
        pass

    def record_request(self, request, response, duration_ms):
        tags = [f"status:{response.status_code}"]

        if hasattr(request, "user") and request.user.is_authenticated:
            tags.append(f"user:{request.user.pk}")

        if response.status_code >= 500:
            tags.append("error")
        elif response.status_code >= 400:
            tags.append("client-error")

        if duration_ms > 1000:
            tags.append("slow")

        content = {
            "method": request.method,
            "path": request.get_full_path(),
            "ip_address": self._get_client_ip(request),
            "status_code": response.status_code,
            "duration": round(duration_ms, 2),
            "request_headers": self._get_headers(request),
            "response_headers": self._filter_response_headers(response),
            "payload": self._get_payload(request),
            "response_body": self._get_response_body(response),
            "middleware": getattr(request, "_telescope_middleware_list", []),
            "controller_action": self._get_controller(request),
            "session": self._get_session(request),
            "user": self._get_user(request),
        }

        Recorder.record(
            entry_type=EntryType.REQUEST,
            content=content,
            tags=tags,
        )

    def _get_client_ip(self, request):
        x_forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded:
            return x_forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")

    def _get_sensitive_headers(self):
        return {h.lower() for h in get_config("SENSITIVE_HEADERS")}

    def _get_headers(self, request):
        sensitive = self._get_sensitive_headers()
        headers = {}
        for key, value in request.META.items():
            if key.startswith("HTTP_"):
                header_name = key[5:].replace("_", "-").title()
                if header_name.lower() in sensitive:
                    headers[header_name] = "********"
                else:
                    headers[header_name] = value
            elif key in ("CONTENT_TYPE", "CONTENT_LENGTH"):
                headers[key.replace("_", "-").title()] = value
        return headers

    def _filter_response_headers(self, response):
        sensitive = self._get_sensitive_headers()
        headers = {}
        for key, value in response.items():
            if key.lower() in sensitive:
                headers[key] = "********"
            else:
                headers[key] = value
        return headers

    def _get_sensitive_fields(self):
        return get_config("SENSITIVE_FIELDS")

    def _mask_sensitive(self, data, depth=0):
        """Recursively mask sensitive fields in dicts."""
        if depth > 5:
            return data
        if isinstance(data, dict):
            sensitive = self._get_sensitive_fields()
            masked = {}
            for key, value in data.items():
                if any(s in key.lower() for s in sensitive):
                    masked[key] = "********"
                elif isinstance(value, (dict, list)):
                    masked[key] = self._mask_sensitive(value, depth + 1)
                else:
                    masked[key] = value
            return masked
        if isinstance(data, list):
            return [self._mask_sensitive(item, depth + 1) for item in data[:50]]
        return data

    def _get_payload(self, request):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return dict(request.GET)

        content_type = request.content_type if hasattr(request, "content_type") else ""
        max_bytes = get_config("BODY_SIZE_LIMIT") * 1024

        if "json" in content_type:
            try:
                if len(request.body) > max_bytes:
                    return {"_truncated": f"Request body too large ({len(request.body)} bytes)"}
                data = json.loads(request.body)
                return self._mask_sensitive(data)
            except (json.JSONDecodeError, ValueError):
                return {}

        if request.POST:
            data = dict(request.POST)
            return self._mask_sensitive(data)

        return {}

    def _get_response_body(self, response):
        content_type = response.get("Content-Type", "")
        max_bytes = get_config("BODY_SIZE_LIMIT") * 1024

        if "json" in content_type:
            if len(response.content) > max_bytes:
                return {"_truncated": f"Response body too large ({len(response.content)} bytes)"}
            try:
                data = json.loads(response.content)
                return self._mask_sensitive(data)
            except (json.JSONDecodeError, ValueError):
                pass
        if "text/html" in content_type:
            return f"<HTML Response: {len(response.content)} bytes>"
        return None

    def _get_controller(self, request):
        if hasattr(request, "resolver_match") and request.resolver_match:
            rm = request.resolver_match
            if rm.func:
                func = rm.func
                if hasattr(func, "view_class"):
                    return f"{func.view_class.__module__}.{func.view_class.__qualname__}"
                return f"{func.__module__}.{func.__qualname__}"
        return None

    def _get_session(self, request):
        if hasattr(request, "session") and request.session.session_key:
            # Hash the session key — storing raw keys is a session hijack risk
            hashed = hashlib.sha256(request.session.session_key.encode()).hexdigest()[:16]
            return {"id": f"sha256:{hashed}"}
        return None

    def _get_user(self, request):
        if hasattr(request, "user") and request.user.is_authenticated:
            user = request.user
            return {
                "id": user.pk,
                "name": getattr(user, "get_full_name", lambda: str(user))(),
                "email": getattr(user, "email", ""),
            }
        return None
