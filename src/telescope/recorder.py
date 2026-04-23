import logging
import threading
import uuid
from collections import defaultdict
from contextvars import ContextVar

from .context import get_batch_id, get_buffer, is_recording
from .entry_type import EntryType
from .redaction import redact_sensitive
from .truncation import truncate_content

logger = logging.getLogger("telescope.recorder")

# Re-entrancy guard: prevent telescope from recording its own DB queries
_persisting: ContextVar[bool] = ContextVar("telescope_persisting", default=False)


class Recorder:
    """Central write path: buffer entries during request, flush at end."""

    @classmethod
    def record(cls, entry_type: EntryType, content: dict, tags: list[str] | None = None):
        if _persisting.get(False):
            return
        if not is_recording():
            return

        from .settings import get_config

        if not get_config("ENABLED") or not get_config("RECORDING"):
            return

        content = truncate_content(content)
        content = redact_sensitive(content)

        entry_data = {
            "uuid": str(uuid.uuid4()),
            "batch_id": get_batch_id(),
            "type": entry_type.value,
            "content": content,
            "tags": tags or [],
            "family_hash": content.get("family_hash"),
        }

        buf = get_buffer()
        if buf is not None:
            buf.append(entry_data)
        else:
            # No active scope — write immediately
            cls._persist([entry_data])

    @classmethod
    def flush(cls):
        """Flush buffered entries to DB and broadcast via WebSocket."""
        buf = get_buffer()
        if not buf:
            return

        entries = list(buf)
        buf.clear()
        # Retroactively tag all queries in N+1 patterns before persisting
        cls._tag_n_plus_one(entries)
        cls._persist(entries)

    @classmethod
    def _tag_n_plus_one(cls, entries):
        """Tag ALL queries in patterns that exceed the N+1 threshold."""
        from .settings import get_config

        threshold = get_config("N_PLUS_ONE_THRESHOLD")
        query_type = EntryType.QUERY.value

        # Count family_hash occurrences among query entries
        hash_counts: dict[str, int] = defaultdict(int)
        for entry in entries:
            if entry["type"] == query_type:
                fh = entry.get("family_hash")
                if fh:
                    hash_counts[fh] += 1

        # Find patterns that crossed the threshold
        bad_hashes = {h for h, c in hash_counts.items() if c >= threshold}
        if not bad_hashes:
            return

        # Tag ALL entries (including the first ones) for those patterns
        for entry in entries:
            if entry["type"] == query_type:
                fh = entry.get("family_hash")
                if fh in bad_hashes:
                    if "n+1" not in entry["tags"]:
                        entry["tags"].append("n+1")
                    entry["content"]["n_plus_one"] = True

    @classmethod
    def _persist(cls, entries):
        if not entries:
            return

        from .models import TelescopeEntry, TelescopeEntryTag

        db_entries = []
        tag_map = {}  # uuid -> tags list

        for entry_data in entries:
            entry = TelescopeEntry(
                uuid=entry_data["uuid"],
                batch_id=entry_data.get("batch_id"),
                family_hash=entry_data.get("family_hash"),
                type=entry_data["type"],
                content=entry_data["content"],
            )
            db_entries.append(entry)
            if entry_data.get("tags"):
                tag_map[entry_data["uuid"]] = entry_data["tags"]

        token = _persisting.set(True)
        try:
            created = TelescopeEntry.objects.bulk_create(db_entries, batch_size=50)

            # Create tags
            tag_objects = []
            for entry in created:
                tags = tag_map.get(str(entry.uuid), [])
                for tag in tags:
                    tag_objects.append(TelescopeEntryTag(entry=entry, tag=tag))
            if tag_objects:
                TelescopeEntryTag.objects.bulk_create(tag_objects, batch_size=100)

            # Broadcast via WebSocket in a background thread to avoid blocking
            cls._broadcast_async(created, tag_map)

        except Exception:
            logger.exception("Failed to persist telescope entries")
        finally:
            _persisting.reset(token)

    @classmethod
    def _broadcast_async(cls, entries, tag_map=None):
        """Send entries to WebSocket clients in a background thread."""
        try:
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            if channel_layer is None:
                return

            # Build all messages upfront (fast, no I/O)
            from .serializers import _get_summary

            tag_map = tag_map or {}
            batch = []
            for entry in entries:
                entry_type = EntryType(entry.type)
                tags = tag_map.get(str(entry.uuid), [])
                batch.append({
                    "uuid": str(entry.uuid),
                    "batch_id": str(entry.batch_id) if entry.batch_id else None,
                    "type": entry.type,
                    "type_label": entry_type.label,
                    "type_slug": entry_type.slug,
                    "summary": _get_summary(entry_type, entry.content or {}),
                    "content": entry.content,
                    "tags": tags,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                })

            # Send in a daemon thread so we don't block the response
            thread = threading.Thread(
                target=cls._do_broadcast,
                args=(channel_layer, batch),
                daemon=True,
            )
            thread.start()

        except Exception:
            logger.debug("WebSocket broadcast setup failed", exc_info=True)

    @classmethod
    def _do_broadcast(cls, channel_layer, batch):
        """Actual broadcast — runs in background thread."""
        try:
            from asgiref.sync import async_to_sync

            # Send a single batched message instead of one per entry
            message = {
                "type": "telescope.entries",
                "entries": batch,
            }
            async_to_sync(channel_layer.group_send)("telescope", message)
        except Exception:
            logger.debug("WebSocket broadcast failed", exc_info=True)
