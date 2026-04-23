import time

from ..entry_type import EntryType
from ..recorder import Recorder
from .base import BaseWatcher

TRACKED_METHODS = ("get", "set", "delete", "clear", "get_many", "set_many", "delete_many", "has_key", "incr", "decr")

_patched_classes = set()


class CacheWatcher(BaseWatcher):
    """Records cache operations by patching cache backend classes.

    Works with any cache backend (django-redis, memcached, file, locmem, etc.)
    by patching methods on the actual backend class so all threads see it.
    """

    def register(self):
        from django.core.cache import caches
        from django.conf import settings

        for alias in settings.CACHES:
            try:
                cache = caches[alias]
                self._patch_cache_class(type(cache), alias)
            except Exception:
                pass

    def _patch_cache_class(self, cache_cls, alias):
        """Patch methods on the cache backend class (not instance) so all threads get it."""
        cls_id = id(cache_cls)
        if cls_id in _patched_classes:
            return
        _patched_classes.add(cls_id)

        for method_name in TRACKED_METHODS:
            original = getattr(cache_cls, method_name, None)
            if original is None:
                continue
            if getattr(original, "_telescope_patched", False):
                continue
            wrapped = _make_wrapper(method_name, original)
            setattr(cache_cls, method_name, wrapped)

    @staticmethod
    def record_operation(operation, key=None, value=None, hit=None,
                         duration_ms=0, backend_alias="default"):
        """Public API for TelescopeCacheBackend to record cache operations."""
        args = ()
        if key is not None and value is not None:
            args = (key, value)
        elif key is not None:
            args = (key,)
        _record(operation, args, {}, value, duration_ms, backend_alias)


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
                alias = getattr(self, "_alias", "default")
                _record(method_name, args, kwargs, result, duration_ms, alias)
            except Exception:
                pass
    wrapper._telescope_patched = True
    wrapper.__name__ = method_name
    wrapper.__qualname__ = f"CacheWatcher.{method_name}"
    return wrapper


def _record(operation, args, kwargs, result, duration_ms, backend_alias):
    key = None
    value = None
    hit = None

    if operation in ("get", "has_key"):
        key = str(args[0]) if args else None
        if operation == "get":
            default = args[1] if len(args) > 1 else kwargs.get("default")
            hit = result is not None and result != default
    elif operation == "set":
        key = str(args[0]) if args else None
        value = repr(args[1])[:512] if len(args) > 1 else None
    elif operation == "delete":
        key = str(args[0]) if args else None
    elif operation == "get_many":
        key = str(args[0]) if args else None
        hit = bool(result) if result is not None else None
    elif operation == "set_many":
        key = str(list(args[0].keys())) if args and isinstance(args[0], dict) else None
    elif operation == "delete_many":
        key = str(args[0]) if args else None
    elif operation in ("incr", "decr"):
        key = str(args[0]) if args else None

    tags = [f"cache:{operation}"]
    if hit is True:
        tags.append("hit")
    elif hit is False and operation == "get":
        tags.append("miss")

    content = {
        "type": operation,
        "key": key,
        "value": value,
        "hit": hit,
        "duration": round(duration_ms, 2),
        "backend": backend_alias,
    }

    Recorder.record(entry_type=EntryType.CACHE, content=content, tags=tags)
