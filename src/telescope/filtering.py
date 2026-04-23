from django.db.models import Q

from .entry_type import EntryType
from .models import TelescopeEntry


def apply_filters(queryset, params):
    """Apply query filters from request parameters."""

    # Filter by entry type
    entry_type = params.get("type")
    if entry_type:
        try:
            et = EntryType.from_slug(entry_type)
            queryset = queryset.filter(type=et.value)
        except (KeyError, ValueError):
            pass

    # Filter by tag
    tag = params.get("tag")
    if tag:
        queryset = queryset.filter(tags__tag=tag)

    # Filter by batch_id
    batch_id = params.get("batch_id")
    if batch_id:
        queryset = queryset.filter(batch_id=batch_id)

    # Filter by family_hash
    family_hash = params.get("family_hash")
    if family_hash:
        queryset = queryset.filter(family_hash=family_hash)

    # Search in content (JSON contains) — cap length to prevent abuse
    search = params.get("search")
    if search:
        search = search[:200]
        queryset = queryset.filter(
            Q(content__icontains=search) | Q(tags__tag__icontains=search)
        ).distinct()

    # Cursor-based pagination (before=<id>)
    before = params.get("before")
    if before:
        try:
            queryset = queryset.filter(id__lt=int(before))
        except (ValueError, TypeError):
            pass

    # Limit
    limit = params.get("limit", 50)
    try:
        limit = min(int(limit), 100)
    except (ValueError, TypeError):
        limit = 50

    return queryset[:limit]
