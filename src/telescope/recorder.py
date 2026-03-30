import logging
import uuid

from .context import get_batch_id, get_buffer, is_recording
from .entry_type import EntryType
from .truncation import truncate_content

logger = logging.getLogger("telescope.recorder")


class Recorder:
    """Central write path: buffer entries during request, flush at end."""

    @classmethod
    def record(cls, entry_type: EntryType, content: dict, tags: list[str] | None = None):
        if not is_recording():
            return

        from .settings import get_config

        if not get_config("ENABLED"):
            return

        content = truncate_content(content)

        entry_data = {
            "uuid": str(uuid.uuid4()),
            "batch_id": get_batch_id(),
            "type": entry_type.value,
            "content": content,
            "tags": tags or [],
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

        cls._persist(buf)
        buf.clear()

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
                type=entry_data["type"],
                content=entry_data["content"],
            )
            db_entries.append(entry)
            if entry_data.get("tags"):
                tag_map[entry_data["uuid"]] = entry_data["tags"]

        try:
            created = TelescopeEntry.objects.bulk_create(db_entries)

            # Create tags
            tag_objects = []
            for entry in created:
                tags = tag_map.get(str(entry.uuid), [])
                for tag in tags:
                    tag_objects.append(TelescopeEntryTag(entry=entry, tag=tag))
            if tag_objects:
                TelescopeEntryTag.objects.bulk_create(tag_objects)

            # Broadcast via WebSocket
            cls._broadcast(created)

        except Exception:
            logger.exception("Failed to persist telescope entries")

    @classmethod
    def _broadcast(cls, entries):
        """Send new entries to connected WebSocket clients."""
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync

            channel_layer = get_channel_layer()
            if channel_layer is None:
                return

            for entry in entries:
                message = {
                    "type": "telescope.entry",
                    "entry": {
                        "uuid": str(entry.uuid),
                        "batch_id": str(entry.batch_id) if entry.batch_id else None,
                        "type": entry.type,
                        "type_label": EntryType(entry.type).label,
                        "type_slug": EntryType(entry.type).slug,
                        "content": entry.content,
                        "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    },
                }
                async_to_sync(channel_layer.group_send)("telescope", message)

        except Exception:
            # WebSocket broadcast is best-effort
            logger.debug("WebSocket broadcast failed", exc_info=True)
