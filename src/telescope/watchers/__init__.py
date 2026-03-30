import logging

from ..settings import get_config
from .base import BaseWatcher

logger = logging.getLogger("telescope.watchers")


class WatcherRegistry:
    _watchers: dict[str, BaseWatcher] = {}
    _registered = False

    # Maps watcher names to their module paths
    WATCHER_MAP = {
        "RequestWatcher": "telescope.watchers.request_watcher.RequestWatcher",
        "QueryWatcher": "telescope.watchers.query_watcher.QueryWatcher",
        "ExceptionWatcher": "telescope.watchers.exception_watcher.ExceptionWatcher",
        "ModelWatcher": "telescope.watchers.model_watcher.ModelWatcher",
        "LogWatcher": "telescope.watchers.log_watcher.LogWatcher",
        "CacheWatcher": "telescope.watchers.cache_watcher.CacheWatcher",
        "MailWatcher": "telescope.watchers.mail_watcher.MailWatcher",
        "RedisWatcher": "telescope.watchers.redis_watcher.RedisWatcher",
        "ViewWatcher": "telescope.watchers.view_watcher.ViewWatcher",
        "EventWatcher": "telescope.watchers.event_watcher.EventWatcher",
        "CommandWatcher": "telescope.watchers.command_watcher.CommandWatcher",
        "DumpWatcher": "telescope.watchers.dump_watcher.DumpWatcher",
        "ClientRequestWatcher": "telescope.watchers.client_request_watcher.ClientRequestWatcher",
        "GateWatcher": "telescope.watchers.gate_watcher.GateWatcher",
        "NotificationWatcher": "telescope.watchers.notification_watcher.NotificationWatcher",
        "ScheduleWatcher": "telescope.watchers.schedule_watcher.ScheduleWatcher",
        "BatchWatcher": "telescope.watchers.batch_watcher.BatchWatcher",
    }

    @classmethod
    def register_all(cls):
        if cls._registered:
            return
        cls._registered = True

        watcher_config = get_config("WATCHERS")

        for name, dotted_path in cls.WATCHER_MAP.items():
            opts = watcher_config.get(name, {})
            if not opts.get("enabled", False):
                continue

            try:
                module_path, class_name = dotted_path.rsplit(".", 1)
                import importlib

                module = importlib.import_module(module_path)
                watcher_cls = getattr(module, class_name)
                watcher = watcher_cls(options=opts)
                watcher.register()
                cls._watchers[name] = watcher
                logger.debug("Registered watcher: %s", name)
            except Exception:
                logger.exception("Failed to register watcher: %s", name)

    @classmethod
    def get(cls, name):
        return cls._watchers.get(name)

    @classmethod
    def all(cls):
        return cls._watchers

    @classmethod
    def reset(cls):
        """Reset registry (for testing)."""
        cls._watchers = {}
        cls._registered = False
