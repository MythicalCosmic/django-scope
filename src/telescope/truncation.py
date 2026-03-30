import json

from .settings import get_config


def truncate_content(content, max_kb=None):
    """Truncate content dict to stay within size limits."""
    if max_kb is None:
        max_kb = get_config("ENTRY_SIZE_LIMIT")
    max_bytes = max_kb * 1024

    serialized = json.dumps(content, default=str)
    if len(serialized) <= max_bytes:
        return content

    # Truncate large string values
    truncated = _truncate_dict(content, max_bytes)
    return truncated


def _truncate_dict(obj, max_bytes, depth=0):
    if depth > 10:
        return "..."

    if isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            result[key] = _truncate_dict(value, max_bytes, depth + 1)
        return result
    elif isinstance(obj, list):
        if len(obj) > 100:
            return [_truncate_dict(item, max_bytes, depth + 1) for item in obj[:100]] + [f"... ({len(obj) - 100} more)"]
        return [_truncate_dict(item, max_bytes, depth + 1) for item in obj]
    elif isinstance(obj, str):
        if len(obj) > 2048:
            return obj[:2048] + f"... (truncated {len(obj) - 2048} chars)"
        return obj
    return obj
