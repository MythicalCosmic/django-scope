import time

from ..entry_type import EntryType
from ..recorder import Recorder
from .base import BaseWatcher

_TRACKED_METHODS = ("save", "delete", "exists", "listdir", "size", "url")
_patched = False


class StorageWatcher(BaseWatcher):
    """Records file storage operations (save, delete, exists, etc.)."""

    def register(self):
        global _patched
        if _patched:
            return
        _patched = True

        from django.core.files.storage import Storage

        for method_name in _TRACKED_METHODS:
            original = getattr(Storage, method_name, None)
            if original is None:
                continue
            if getattr(original, "_telescope_patched", False):
                continue
            wrapped = _make_wrapper(method_name, original)
            setattr(Storage, method_name, wrapped)


def _make_wrapper(method_name, original):
    def wrapper(self, *args, **kwargs):
        start = time.perf_counter()
        result = None
        try:
            result = original(self, *args, **kwargs)
            return result
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            try:
                _record_storage(method_name, args, result, duration_ms, self)
            except Exception:
                pass

    wrapper._telescope_patched = True
    wrapper.__name__ = method_name
    wrapper.__qualname__ = f"StorageWatcher.{method_name}"
    return wrapper


def _record_storage(action, args, result, duration_ms, storage_instance):
    # Extract file path from first argument
    path = str(args[0]) if args else None

    # Skip cache backend file operations to avoid double-recording
    backend_name = type(storage_instance).__name__
    if "cache" in backend_name.lower():
        return

    tags = [f"storage:{action}"]

    content = {
        "action": action,
        "path": path,
        "duration": round(duration_ms, 2),
        "backend": f"{type(storage_instance).__module__}.{backend_name}",
    }

    # Add result info for specific operations
    if action == "exists" and result is not None:
        content["exists"] = bool(result)
    elif action == "size" and result is not None:
        content["size"] = result
    elif action == "save" and result is not None:
        content["saved_path"] = str(result)

    Recorder.record(entry_type=EntryType.STORAGE, content=content, tags=tags)
