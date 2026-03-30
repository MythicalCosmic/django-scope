import sys
import traceback

from django.core.signals import got_request_exception

from ..entry_type import EntryType
from ..recorder import Recorder
from .base import BaseWatcher


class ExceptionWatcher(BaseWatcher):
    _original_excepthook = None

    def register(self):
        got_request_exception.connect(self._on_request_exception)
        # Also catch unhandled exceptions outside requests
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._excepthook

    def unregister(self):
        got_request_exception.disconnect(self._on_request_exception)
        if self._original_excepthook:
            sys.excepthook = self._original_excepthook

    def _on_request_exception(self, sender, request=None, **kwargs):
        exc_info = sys.exc_info()
        if exc_info[1] is None:
            return
        self._record_exception(exc_info[1], request=request)

    def _excepthook(self, exc_type, exc_value, exc_tb):
        self._record_exception(exc_value)
        if self._original_excepthook:
            self._original_excepthook(exc_type, exc_value, exc_tb)

    def _record_exception(self, exception, request=None):
        tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        frames = self._extract_frames(exception)

        tags = [f"exception:{type(exception).__name__}"]
        if request and hasattr(request, "path"):
            tags.append(f"path:{request.path}")

        content = {
            "class": type(exception).__qualname__,
            "module": type(exception).__module__,
            "message": str(exception),
            "trace": "".join(tb_lines),
            "frames": frames,
            "line": frames[-1]["line"] if frames else None,
            "file": frames[-1]["file"] if frames else None,
        }

        Recorder.record(
            entry_type=EntryType.EXCEPTION,
            content=content,
            tags=tags,
        )

    def _extract_frames(self, exception):
        frames = []
        tb = exception.__traceback__
        while tb:
            frame = tb.tb_frame
            frames.append({
                "file": frame.f_code.co_filename,
                "line": tb.tb_lineno,
                "function": frame.f_code.co_name,
                "context": self._get_source_context(frame.f_code.co_filename, tb.tb_lineno),
            })
            tb = tb.tb_next
        return frames

    def _get_source_context(self, filename, lineno, context_lines=5):
        try:
            with open(filename) as f:
                lines = f.readlines()
            start = max(0, lineno - context_lines - 1)
            end = min(len(lines), lineno + context_lines)
            return {
                "start_line": start + 1,
                "lines": [line.rstrip() for line in lines[start:end]],
                "highlight_line": lineno,
            }
        except Exception:
            return None
