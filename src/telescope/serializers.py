from .entry_type import EntryType


def serialize_entry_list(entry):
    """Serialize an entry for list views (summary)."""
    content = entry.content or {}
    entry_type = EntryType(entry.type)

    summary = _get_summary(entry_type, content)

    # Use prefetched tags if available to avoid extra queries
    if hasattr(entry, "_prefetched_objects_cache") and "tags" in entry._prefetched_objects_cache:
        tags = [t.tag for t in entry._prefetched_objects_cache["tags"]]
    elif entry.pk:
        tags = list(entry.tags.values_list("tag", flat=True))
    else:
        tags = []

    return {
        "uuid": str(entry.uuid),
        "batch_id": str(entry.batch_id) if entry.batch_id else None,
        "type": entry.type,
        "type_label": entry_type.label,
        "type_slug": entry_type.slug,
        "summary": summary,
        "content": content,
        "created_at": entry.created_at.isoformat(),
        "tags": tags,
    }


def serialize_entry_detail(entry):
    """Serialize an entry for detail views (full content)."""
    base = serialize_entry_list(entry)
    base["content"] = entry.content
    return base


def _get_summary(entry_type, content):
    """Extract a short summary for list display."""
    match entry_type:
        case EntryType.REQUEST:
            method = content.get("method", "")
            path = content.get("path", "")
            status = content.get("status_code", "")
            duration = content.get("duration", "")
            return f"{method} {path} → {status} ({duration}ms)"

        case EntryType.QUERY:
            sql = content.get("sql", "")
            duration = content.get("duration", "")
            return f"{sql[:100]} ({duration}ms)"

        case EntryType.EXCEPTION:
            cls = content.get("class", "")
            msg = content.get("message", "")
            return f"{cls}: {msg[:100]}"

        case EntryType.MODEL:
            model = content.get("model", "")
            action = content.get("action", "")
            key = content.get("key", "")
            return f"{action} {model} #{key}"

        case EntryType.LOG:
            level = content.get("level", "")
            msg = content.get("message", "")
            return f"[{level}] {msg[:100]}"

        case EntryType.CACHE:
            op = content.get("type", "")
            key = content.get("key", "")
            hit = content.get("hit")
            hit_str = " (hit)" if hit else " (miss)" if hit is not None else ""
            return f"{op} {key}{hit_str}"

        case EntryType.REDIS:
            cmd = content.get("command", "")
            args = content.get("args", [])
            return f"{cmd} {' '.join(str(a) for a in args[:3])}"

        case EntryType.MAIL:
            to = content.get("to", [])
            subject = content.get("subject", "")
            return f"To: {', '.join(to[:3])} — {subject[:60]}"

        case EntryType.VIEW:
            template = content.get("template", "")
            duration = content.get("duration", "")
            return f"{template} ({duration}ms)"

        case EntryType.EVENT:
            signal = content.get("signal", "")
            sender = content.get("sender", "")
            return f"{signal} from {sender}"

        case EntryType.COMMAND:
            cmd = content.get("command", "")
            duration = content.get("duration", "")
            return f"{cmd} ({duration}ms)"

        case EntryType.DUMP:
            label = content.get("label", "")
            dump = content.get("dump", "")
            prefix = f"{label}: " if label else ""
            return f"{prefix}{dump[:100]}"

        case EntryType.CLIENT_REQUEST:
            method = content.get("method", "")
            url = content.get("url", "")
            status = content.get("status_code", "")
            return f"{method} {url[:80]} → {status}"

        case EntryType.GATE:
            perm = content.get("permission", "")
            result = "granted" if content.get("result") else "denied"
            return f"{perm} — {result}"

        case EntryType.NOTIFICATION:
            notification = content.get("notification", "")
            recipient = content.get("recipient", "")
            return f"{notification} → {recipient}"

        case EntryType.SCHEDULE:
            task = content.get("task", "")
            status = content.get("status", "")
            return f"{task} ({status})"

        case EntryType.BATCH:
            batch_id = content.get("batch_id", "")
            task = content.get("task", "")
            return f"Batch {batch_id[:8]}... — {task}"

        case EntryType.TRANSACTION:
            action = content.get("action", "")
            conn = content.get("connection", "")
            txn_dur = content.get("transaction_duration")
            dur_str = f" ({txn_dur}ms)" if txn_dur is not None else ""
            return f"{action} on {conn}{dur_str}"

        case EntryType.STORAGE:
            action = content.get("action", "")
            path = content.get("path", "")
            duration = content.get("duration", "")
            return f"{action} {path} ({duration}ms)"

        case _:
            return str(content)[:100]
