import hashlib
import time
from collections import defaultdict
from contextvars import ContextVar

from django.db import connections

from ..entry_type import EntryType
from ..recorder import Recorder
from ..settings import get_config
from .base import BaseWatcher

# Track query patterns per request for N+1 detection
_query_patterns: ContextVar[dict | None] = ContextVar("telescope_query_patterns", default=None)


def reset_query_tracking():
    _query_patterns.set(defaultdict(int))


def get_query_patterns():
    return _query_patterns.get()


class QueryWatcher(BaseWatcher):
    def register(self):
        # Install execute_wrapper on all database connections
        for alias in connections:
            conn = connections[alias]
            conn.execute_wrappers.append(self._execute_wrapper)

    def _execute_wrapper(self, execute, sql, params, many, context):
        start = time.perf_counter()
        try:
            result = execute(sql, params, many, context)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._record_query(sql, params, duration_ms, context)
        return result

    def _record_query(self, sql, params, duration_ms, context):
        slow_threshold = get_config("SLOW_QUERY_THRESHOLD")
        n_plus_one_threshold = get_config("N_PLUS_ONE_THRESHOLD")

        # Normalize SQL for pattern hashing
        sql_str = str(sql)
        pattern_hash = hashlib.md5(self._normalize_sql(sql_str).encode()).hexdigest()

        tags = []
        is_slow = duration_ms >= slow_threshold
        if is_slow:
            tags.append("slow")

        # N+1 detection
        is_n_plus_one = False
        patterns = get_query_patterns()
        if patterns is not None:
            patterns[pattern_hash] += 1
            if patterns[pattern_hash] >= n_plus_one_threshold:
                is_n_plus_one = True
                tags.append("n+1")

        # Get connection alias from context
        connection = context.get("connection", None)
        alias = getattr(connection, "alias", "default") if connection else "default"

        content = {
            "sql": sql_str,
            "bindings": self._serialize_params(params),
            "duration": round(duration_ms, 2),
            "connection": alias,
            "slow": is_slow,
            "n_plus_one": is_n_plus_one,
            "family_hash": pattern_hash,
        }

        Recorder.record(
            entry_type=EntryType.QUERY,
            content=content,
            tags=tags,
        )

    def _normalize_sql(self, sql):
        """Normalize SQL for pattern matching (replace literals with ?)."""
        import re

        sql = re.sub(r"'[^']*'", "?", sql)
        sql = re.sub(r"\b\d+\b", "?", sql)
        sql = re.sub(r"\s+", " ", sql).strip()
        return sql

    def _serialize_params(self, params):
        if params is None:
            return []
        try:
            if isinstance(params, (list, tuple)):
                return [str(p) for p in params]
            return str(params)
        except Exception:
            return "<unserializable>"
