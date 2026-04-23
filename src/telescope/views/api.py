import json

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from ..entry_type import EntryType
from ..filtering import apply_filters
from ..models import TelescopeEntry, TelescopeMonitoring
from ..pruning import clear_entries
from ..serializers import serialize_entry_detail, serialize_entry_list
from ..settings import get_config


@method_decorator(csrf_exempt, name="dispatch")
class TelescopeApiMixin:
    """Authorization check + CSRF exemption for telescope API."""

    def dispatch(self, request, *args, **kwargs):
        if not self._is_authorized(request):
            return JsonResponse({"error": "Unauthorized"}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def _is_authorized(self, request):
        auth_callback = get_config("AUTHORIZATION")
        if auth_callback and callable(auth_callback):
            return auth_callback(request)
        from django.conf import settings
        return getattr(settings, "DEBUG", False)


class EntryListView(TelescopeApiMixin, View):
    """List entries with filtering and pagination."""

    def get(self, request):
        qs = TelescopeEntry.objects.prefetch_related("tags").all()
        qs = apply_filters(qs, request.GET)

        entries = [serialize_entry_list(e) for e in qs]
        try:
            limit = min(max(int(request.GET.get("limit", 50)), 1), 100)
        except (ValueError, TypeError):
            limit = 50
        return JsonResponse({
            "entries": entries,
            "has_more": len(entries) == limit,
        })


class TypedEntryListView(TelescopeApiMixin, View):
    """List entries filtered by type slug."""

    def get(self, request, type_slug):
        try:
            entry_type = EntryType.from_slug(type_slug)
        except (KeyError, ValueError):
            return JsonResponse({"error": "Invalid type"}, status=400)

        qs = TelescopeEntry.objects.prefetch_related("tags").filter(type=entry_type.value)
        qs = apply_filters(qs, request.GET)

        entries = [serialize_entry_list(e) for e in qs]
        try:
            limit = min(max(int(request.GET.get("limit", 50)), 1), 100)
        except (ValueError, TypeError):
            limit = 50
        return JsonResponse({
            "entries": entries,
            "type": {"value": entry_type.value, "label": entry_type.label, "slug": entry_type.slug},
            "has_more": len(entries) == limit,
        })


class EntryDetailView(TelescopeApiMixin, View):
    """Get a single entry by UUID."""

    def get(self, request, uuid):
        try:
            entry = TelescopeEntry.objects.prefetch_related("tags").get(uuid=uuid)
        except TelescopeEntry.DoesNotExist:
            return JsonResponse({"error": "Not found"}, status=404)

        return JsonResponse({"entry": serialize_entry_detail(entry)})


class BatchDetailView(TelescopeApiMixin, View):
    """Get all entries in a batch."""

    def get(self, request, batch_id):
        qs = TelescopeEntry.objects.prefetch_related("tags").filter(batch_id=batch_id).order_by("id")
        entries = [serialize_entry_list(e) for e in qs]
        return JsonResponse({"entries": entries, "batch_id": batch_id})


class EntryDeleteView(TelescopeApiMixin, View):
    """Delete a single entry."""

    def delete(self, request, uuid):
        try:
            entry = TelescopeEntry.objects.get(uuid=uuid)
            entry.delete()
            return JsonResponse({"message": "Deleted"})
        except TelescopeEntry.DoesNotExist:
            return JsonResponse({"error": "Not found"}, status=404)


class ClearEntriesView(TelescopeApiMixin, View):
    """Clear all entries, optionally filtered by type."""

    def delete(self, request):
        type_slug = request.GET.get("type")
        entry_type = None
        if type_slug:
            try:
                entry_type = EntryType.from_slug(type_slug).value
            except (KeyError, ValueError):
                return JsonResponse({"error": "Invalid type"}, status=400)

        count = clear_entries(entry_type=entry_type)
        return JsonResponse({"deleted": count})


class StatusView(TelescopeApiMixin, View):
    """Get telescope status and entry counts."""

    def get(self, request):
        from django.db.models import Count

        counts = (
            TelescopeEntry.objects.values("type")
            .annotate(count=Count("id"))
            .order_by("type")
        )

        type_counts = {}
        total = 0
        for item in counts:
            et = EntryType(item["type"])
            type_counts[et.slug] = {"label": et.label, "count": item["count"]}
            total += item["count"]

        return JsonResponse({
            "enabled": get_config("ENABLED"),
            "recording": get_config("RECORDING"),
            "total_entries": total,
            "types": type_counts,
        })


class ToggleRecordingView(TelescopeApiMixin, View):
    """Toggle recording on/off."""

    def post(self, request):
        from ..settings import set_runtime

        try:
            body = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            body = {}

        recording = body.get("recording")
        if recording is None:
            new_value = not get_config("RECORDING")
        else:
            new_value = bool(recording)

        set_runtime("RECORDING", new_value)
        return JsonResponse({"recording": new_value})


class MonitoringView(TelescopeApiMixin, View):
    """Manage monitored tags."""

    def get(self, request):
        tags = list(TelescopeMonitoring.objects.values_list("tag", flat=True))
        return JsonResponse({"tags": tags})

    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        tag = body.get("tag")
        if not tag:
            return JsonResponse({"error": "Tag required"}, status=400)

        TelescopeMonitoring.objects.get_or_create(tag=tag)
        return JsonResponse({"message": f"Now monitoring: {tag}"})

    def delete(self, request):
        tag = request.GET.get("tag")
        if tag:
            TelescopeMonitoring.objects.filter(tag=tag).delete()
        return JsonResponse({"message": "Removed"})
