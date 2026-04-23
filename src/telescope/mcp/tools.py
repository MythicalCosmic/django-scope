"""MCP tool implementations — query telescope data for AI assistants."""

from datetime import timedelta

from django.db.models import Avg, Count
from django.utils import timezone

from ..entry_type import EntryType
from ..models import TelescopeEntry
from ..settings import get_config


def get_recent_requests(limit=20, status_code=None):
    """Get recent HTTP request entries."""
    qs = TelescopeEntry.objects.filter(type=EntryType.REQUEST.value).order_by("-id")
    if status_code:
        qs = qs.filter(content__status_code=status_code)
    entries = qs[:limit]
    return [
        {
            "uuid": str(e.uuid),
            "method": e.content.get("method"),
            "path": e.content.get("path"),
            "status_code": e.content.get("status_code"),
            "duration_ms": e.content.get("duration"),
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]


def get_slow_queries(threshold_ms=None, limit=20):
    """Get slow database queries above threshold."""
    if threshold_ms is None:
        threshold_ms = get_config("SLOW_QUERY_THRESHOLD")
    qs = (
        TelescopeEntry.objects.filter(type=EntryType.QUERY.value)
        .order_by("-id")
    )
    entries = []
    for e in qs[:limit * 3]:  # Over-fetch since we filter in Python
        duration = e.content.get("duration", 0)
        if duration >= threshold_ms:
            entries.append({
                "uuid": str(e.uuid),
                "sql": e.content.get("sql", "")[:300],
                "duration_ms": duration,
                "connection": e.content.get("connection"),
                "n_plus_one": e.content.get("n_plus_one", False),
                "created_at": e.created_at.isoformat(),
            })
            if len(entries) >= limit:
                break
    return entries


def get_exceptions(limit=20):
    """Get recent exceptions."""
    entries = TelescopeEntry.objects.filter(
        type=EntryType.EXCEPTION.value
    ).order_by("-id")[:limit]
    return [
        {
            "uuid": str(e.uuid),
            "class": e.content.get("class"),
            "message": e.content.get("message", "")[:200],
            "file": e.content.get("file"),
            "line": e.content.get("line"),
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]


def get_n1_patterns(limit=10):
    """Get N+1 query patterns grouped by family_hash."""
    threshold = get_config("N_PLUS_ONE_THRESHOLD")
    cutoff = timezone.now() - timedelta(hours=24)

    patterns = (
        TelescopeEntry.objects.filter(
            type=EntryType.QUERY.value,
            created_at__gte=cutoff,
        )
        .exclude(family_hash__isnull=True)
        .exclude(family_hash="")
        .values("family_hash")
        .annotate(count=Count("id"), avg_duration=Avg("content__duration"))
        .filter(count__gte=threshold)
        .order_by("-count")[:limit]
    )

    result = []
    for p in patterns:
        sample = (
            TelescopeEntry.objects.filter(family_hash=p["family_hash"])
            .values_list("content__sql", flat=True)
            .first()
        )
        result.append({
            "family_hash": p["family_hash"],
            "count": p["count"],
            "avg_duration_ms": round(p["avg_duration"] or 0, 2),
            "sample_sql": str(sample)[:300] if sample else None,
        })
    return result


def search_entries(query, entry_type=None, limit=20):
    """Search entries by content or tags."""
    from django.db.models import Q

    qs = TelescopeEntry.objects.all()
    if entry_type:
        try:
            et = EntryType.from_slug(entry_type)
            qs = qs.filter(type=et.value)
        except (KeyError, ValueError):
            pass

    qs = qs.filter(
        Q(content__icontains=query) | Q(tags__tag__icontains=query)
    ).distinct().order_by("-id")[:limit]

    return [
        {
            "uuid": str(e.uuid),
            "type": EntryType(e.type).slug,
            "content_preview": str(e.content)[:200],
            "created_at": e.created_at.isoformat(),
        }
        for e in qs
    ]


def get_stats_summary(range_hours=24):
    """Get overall stats summary."""
    cutoff = timezone.now() - timedelta(hours=range_hours)
    base_qs = TelescopeEntry.objects.filter(created_at__gte=cutoff)

    request_qs = base_qs.filter(type=EntryType.REQUEST.value)
    request_count = request_qs.count()

    error_count = request_qs.filter(content__status_code__gte=500).count()

    query_count = base_qs.filter(type=EntryType.QUERY.value).count()
    exception_count = base_qs.filter(type=EntryType.EXCEPTION.value).count()

    n1_patterns = (
        base_qs.filter(type=EntryType.QUERY.value, tags__tag="n+1")
        .values("family_hash")
        .distinct()
        .count()
    )

    cache_qs = base_qs.filter(type=EntryType.CACHE.value)
    cache_total = cache_qs.count()
    cache_hits = cache_qs.filter(content__hit=True).count()

    return {
        "range_hours": range_hours,
        "requests": request_count,
        "errors": error_count,
        "error_rate": round(error_count / request_count * 100, 2) if request_count else 0,
        "queries": query_count,
        "exceptions": exception_count,
        "n_plus_one_patterns": n1_patterns,
        "cache_total": cache_total,
        "cache_hits": cache_hits,
        "cache_hit_rate": round(cache_hits / cache_total * 100, 2) if cache_total else 0,
    }
