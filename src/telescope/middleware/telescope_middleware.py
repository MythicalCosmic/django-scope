import re
import time

from django.utils.deprecation import MiddlewareMixin

from ..context import end_scope, start_scope
from ..recorder import Recorder
from ..settings import get_config


class TelescopeMiddleware(MiddlewareMixin):
    """Request lifecycle: scope → watchers → flush."""

    def process_request(self, request):
        if not get_config("ENABLED"):
            return None

        if self._should_ignore(request):
            return None

        start_scope()
        request._telescope_start_time = time.perf_counter()
        request._telescope_active = True
        return None

    def process_response(self, request, response):
        if not getattr(request, "_telescope_active", False):
            return response

        # Let the RequestWatcher handle response recording
        duration_ms = (time.perf_counter() - request._telescope_start_time) * 1000
        request._telescope_duration_ms = duration_ms

        # Record request entry via the watcher
        from ..watchers import WatcherRegistry

        request_watcher = WatcherRegistry.get("RequestWatcher")
        if request_watcher:
            request_watcher.record_request(request, response, duration_ms)

        # Flush all buffered entries for this request
        Recorder.flush()
        end_scope()

        return response

    def process_exception(self, request, exception):
        # Exception watcher handles this via signal, but we store the exception
        # on the request for the exception watcher to pick up
        request._telescope_exception = exception
        return None

    def _should_ignore(self, request):
        path = request.path
        ignore_paths = get_config("IGNORE_PATHS")
        for pattern in ignore_paths:
            if re.search(pattern, path):
                return True

        ignore_methods = get_config("IGNORE_METHODS")
        if ignore_methods and request.method in ignore_methods:
            return True

        return False
