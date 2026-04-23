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


class StatsView(TelescopeApiMixin, View):
    """Analytics dashboard: percentiles, Apdex, error rates, throughput, slow queries, cache stats."""

    def get(self, request):
        from datetime import timedelta

        from django.db.models import Avg, Count, Q
        from django.utils import timezone

        # Parse time range
        range_param = request.GET.get("range", "24h")
        hours = {"1h": 1, "6h": 6, "24h": 24, "7d": 168}.get(range_param, 24)
        cutoff = timezone.now() - timedelta(hours=hours)

        base_qs = TelescopeEntry.objects.filter(created_at__gte=cutoff)

        # --- Request stats ---
        request_qs = base_qs.filter(type=EntryType.REQUEST.value)
        request_count = request_qs.count()

        durations = list(
            request_qs.values_list("content__duration", flat=True)
            .exclude(content__duration__isnull=True)
            .order_by("content__duration")
        )
        # Filter to valid numeric durations
        durations = sorted(d for d in durations if isinstance(d, (int, float)))

        percentiles = self._calc_percentiles(durations)

        # Apdex: satisfied < T, tolerating < 4T, frustrated >= 4T
        apdex_threshold = get_config("APDEX_THRESHOLD")
        apdex = self._calc_apdex(durations, apdex_threshold)

        # Error rate
        error_count = request_qs.filter(content__status_code__gte=500).count()
        error_rate = round(error_count / request_count * 100, 2) if request_count else 0

        # Throughput (requests per minute)
        minutes = hours * 60
        throughput = round(request_count / minutes, 2) if minutes else 0

        # --- Slow query top-10 ---
        query_qs = base_qs.filter(type=EntryType.QUERY.value).exclude(family_hash__isnull=True)
        slow_queries = (
            query_qs.values("family_hash")
            .annotate(count=Count("id"), avg_duration=Avg("content__duration"))
            .order_by("-count")[:10]
        )
        slow_query_list = []
        for sq in slow_queries:
            # Get a sample SQL for this hash
            sample = query_qs.filter(family_hash=sq["family_hash"]).values_list("content__sql", flat=True).first()
            slow_query_list.append({
                "family_hash": sq["family_hash"],
                "count": sq["count"],
                "avg_duration": round(sq["avg_duration"] or 0, 2),
                "sample_sql": str(sample)[:200] if sample else None,
            })

        # --- Cache stats ---
        cache_qs = base_qs.filter(type=EntryType.CACHE.value)
        cache_total = cache_qs.count()
        cache_hits = cache_qs.filter(content__hit=True).count()
        cache_hit_rate = round(cache_hits / cache_total * 100, 2) if cache_total else 0

        # --- N+1 patterns ---
        n1_count = base_qs.filter(
            type=EntryType.QUERY.value,
            tags__tag="n+1",
        ).values("family_hash").distinct().count()

        return JsonResponse({
            "range": range_param,
            "requests": {
                "total": request_count,
                "percentiles": percentiles,
                "apdex": apdex,
                "apdex_threshold": apdex_threshold,
                "error_count": error_count,
                "error_rate": error_rate,
                "throughput_per_minute": throughput,
            },
            "queries": {
                "total": query_qs.count(),
                "slow_patterns": slow_query_list,
                "n_plus_one_patterns": n1_count,
            },
            "cache": {
                "total": cache_total,
                "hits": cache_hits,
                "hit_rate": cache_hit_rate,
            },
        })

    @staticmethod
    def _calc_percentiles(sorted_durations):
        if not sorted_durations:
            return {"p50": 0, "p75": 0, "p95": 0, "p99": 0}
        n = len(sorted_durations)
        return {
            "p50": round(sorted_durations[int(n * 0.50)], 2),
            "p75": round(sorted_durations[int(n * 0.75)], 2),
            "p95": round(sorted_durations[int(n * 0.95)], 2),
            "p99": round(sorted_durations[min(int(n * 0.99), n - 1)], 2),
        }

    @staticmethod
    def _calc_apdex(durations, threshold):
        if not durations:
            return 0
        satisfied = sum(1 for d in durations if d < threshold)
        tolerating = sum(1 for d in durations if threshold <= d < threshold * 4)
        total = len(durations)
        return round((satisfied + tolerating / 2) / total, 3)


class HealthView(TelescopeApiMixin, View):
    """Watcher health status."""

    def get(self, request):
        from ..watchers import WatcherRegistry

        health = WatcherRegistry.health()

        healthy = sum(1 for v in health.values() if v.get("status") == "healthy")
        failed = sum(1 for v in health.values() if v.get("status") == "failed")
        disabled = sum(1 for v in health.values() if v.get("status") == "disabled")

        return JsonResponse({
            "summary": {
                "healthy": healthy,
                "failed": failed,
                "disabled": disabled,
                "total": len(health),
            },
            "watchers": health,
        })
