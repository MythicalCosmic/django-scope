import hashlib
import time
from collections import defaultdict
from contextvars import ContextVar

from django.db.backends.signals import connection_created

from ..entry_type import EntryType
from ..recorder import Recorder
from ..settings import get_config
from .base import BaseWatcher

# Track query patterns per request for N+1 detection
_query_patterns: ContextVar[dict | None] = ContextVar("telescope_query_patterns", default=None)

# Track which connections already have the wrapper installed
_patched_connections = set()


def reset_query_tracking():
    _query_patterns.set(defaultdict(int))


def get_query_patterns():
    return _query_patterns.get()


class QueryWatcher(BaseWatcher):
    _instance = None

    def register(self):
        QueryWatcher._instance = self
        # Install on any connections that already exist
        from django.db import connections
        for alias in connections:
            try:
                conn = connections[alias]
                self._install_wrapper(conn)
            except Exception:
                pass

        # Listen for new connections so every future connection gets the wrapper
        connection_created.connect(self._on_connection_created, dispatch_uid="telescope_query_watcher")

    @staticmethod
    def _on_connection_created(sender, connection, **kwargs):
        """Called whenever Django creates a new database connection."""
        instance = QueryWatcher._instance
        if instance:
            instance._install_wrapper(connection)

    def _install_wrapper(self, connection):
        """Install the execute_wrapper on a connection if not already installed."""
        conn_id = id(connection)
        if conn_id in _patched_connections:
            return
        _patched_connections.add(conn_id)
        connection.execute_wrappers.append(self._execute_wrapper)

    # Transaction boundary SQL — skip to avoid double-recording with TransactionWatcher
    _TRANSACTION_SQL = frozenset({"BEGIN", "COMMIT", "ROLLBACK", "END", "SAVEPOINT", "RELEASE"})

    def _execute_wrapper(self, execute, sql, params, many, context):
        sql_str = str(sql)
        # Skip telescope's own queries to prevent recursion
        if "telescope_" in sql_str:
            return execute(sql, params, many, context)
        # Skip transaction boundary SQL (handled by TransactionWatcher)
        first_word = sql_str.lstrip().split(None, 1)[0].upper() if sql_str.strip() else ""
        if first_word in self._TRANSACTION_SQL:
            return execute(sql, params, many, context)

        start = time.perf_counter()
        try:
            result = execute(sql, params, many, context)
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            self._record_query(sql_str, params, duration_ms, context)
        return result

    def _record_query(self, sql_str, params, duration_ms, context):
        slow_threshold = get_config("SLOW_QUERY_THRESHOLD")
        n_plus_one_threshold = get_config("N_PLUS_ONE_THRESHOLD")
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

        # Escaped single-quoted strings: 'it''s a test' -> ?
        sql = re.sub(r"'(?:[^']|'')*'", "?", sql)
        # Hex literals: 0xFF -> ?
        sql = re.sub(r"\b0[xX][0-9a-fA-F]+\b", "?", sql)
        # Float/decimal literals: 3.14 -> ?
        sql = re.sub(r"\b\d+\.\d+\b", "?", sql)
        # Negative numbers: -42 -> ?
        sql = re.sub(r"(?<=\W)-\d+\b", "?", sql)
        # Integer literals: 42 -> ?
        sql = re.sub(r"\b\d+\b", "?", sql)
        # Normalize variable-length IN clauses: IN (?, ?, ?) -> IN (?)
        sql = re.sub(r"IN\s*\(\?(?:\s*,\s*\?)*\)", "IN (?)", sql, flags=re.IGNORECASE)
        # Collapse whitespace
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
