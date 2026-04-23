"""Universal sensitive data redaction applied to all entry content."""

from .settings import get_config

_MASK = "********"


def redact_sensitive(content, depth=0):
    """Recursively mask sensitive field values in any content dict."""
    if depth > 8:
        return content
    if isinstance(content, dict):
        sensitive = get_config("SENSITIVE_FIELDS")
        result = {}
        for key, value in content.items():
            if isinstance(key, str) and any(s in key.lower() for s in sensitive):
                result[key] = _MASK
            elif isinstance(value, (dict, list)):
                result[key] = redact_sensitive(value, depth + 1)
            else:
                result[key] = value
        return result
    if isinstance(content, list):
        return [redact_sensitive(item, depth + 1) for item in content[:100]]
    return content
