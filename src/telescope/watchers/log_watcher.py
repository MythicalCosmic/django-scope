import logging

from ..entry_type import EntryType
from ..recorder import Recorder
from ..settings import get_config
from .base import BaseWatcher


class TelescopeLogHandler(logging.Handler):
    """Custom logging handler that records log entries to telescope."""

    def emit(self, record):
        # Skip telescope's own log messages to avoid recursion
        if record.name.startswith("telescope"):
            return
        # Skip Django's internal debug noise
        if record.name.startswith("django.") and record.levelno < logging.WARNING:
            return

        try:
            tags = [f"level:{record.levelname.lower()}"]
            if record.levelno >= logging.ERROR:
                tags.append("error")

            content = {
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name,
                "context": {
                    "file": record.pathname,
                    "line": record.lineno,
                    "function": record.funcName,
                },
            }

            if record.exc_info and record.exc_info[1]:
                import traceback

                content["exception"] = "".join(traceback.format_exception(*record.exc_info))

            Recorder.record(entry_type=EntryType.LOG, content=content, tags=tags)
        except Exception:
            # Never let telescope logging break the application
            pass


class LogWatcher(BaseWatcher):
    _handler = None

    def register(self):
        self._handler = TelescopeLogHandler()
        # Use configurable level — default WARNING to avoid flooding DB
        level_name = get_config("LOG_LEVEL")
        level = getattr(logging, level_name, logging.WARNING)
        self._handler.setLevel(level)
        root_logger = logging.getLogger()
        root_logger.addHandler(self._handler)

    def unregister(self):
        if self._handler:
            root_logger = logging.getLogger()
            root_logger.removeHandler(self._handler)
