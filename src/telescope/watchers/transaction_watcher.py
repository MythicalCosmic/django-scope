import re
import time
from contextvars import ContextVar

from django.db.backends.signals import connection_created

from ..entry_type import EntryType
from ..recorder import Recorder
from .base import BaseWatcher

# Track open transactions per connection (thread-safe via ContextVar)
_transaction_start: ContextVar[dict] = ContextVar("telescope_txn_start", default=None)

_TRANSACTION_SQL = re.compile(
    r"^\s*(BEGIN|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT|END)\b",
    re.IGNORECASE,
)

_patched_connections = set()


class TransactionWatcher(BaseWatcher):
    """Records database transaction boundaries (BEGIN/COMMIT/ROLLBACK/SAVEPOINT)."""

    def register(self):
        connection_created.connect(self._on_connection_created, dispatch_uid="telescope_txn_watcher")

    @staticmethod
    def _on_connection_created(sender, connection, **kwargs):
        conn_id = id(connection)
        if conn_id in _patched_connections:
            return
        _patched_connections.add(conn_id)
        connection.execute_wrappers.append(_transaction_wrapper)


def _get_txn_starts():
    starts = _transaction_start.get()
    if starts is None:
        starts = {}
        _transaction_start.set(starts)
    return starts


def _transaction_wrapper(execute, sql, params, many, context):
    """Execute wrapper that intercepts transaction boundary SQL."""
    sql_str = str(sql).strip()

    # Skip non-transaction SQL
    match = _TRANSACTION_SQL.match(sql_str)
    if not match:
        return execute(sql, params, many, context)

    connection = context.get("connection")
    alias = getattr(connection, "alias", "default") if connection else "default"
    action = match.group(1).upper()

    start = time.perf_counter()
    result = execute(sql, params, many, context)
    duration_ms = (time.perf_counter() - start) * 1000

    txn_starts = _get_txn_starts()

    if action == "BEGIN":
        txn_starts[alias] = time.perf_counter()
        _record_transaction("begin", alias, duration_ms)
    elif action in ("COMMIT", "END"):
        txn_duration = _calc_txn_duration(txn_starts, alias)
        _record_transaction("commit", alias, duration_ms, txn_duration)
    elif action == "ROLLBACK":
        txn_duration = _calc_txn_duration(txn_starts, alias)
        _record_transaction("rollback", alias, duration_ms, txn_duration)
        tags = ["transaction:rollback"]
        # Already recorded below, but add an extra tag
    elif action.startswith("SAVEPOINT"):
        _record_transaction("savepoint", alias, duration_ms, savepoint=sql_str)
    elif action.startswith("RELEASE"):
        _record_transaction("release_savepoint", alias, duration_ms, savepoint=sql_str)

    return result


def _calc_txn_duration(txn_starts, alias):
    begin_time = txn_starts.pop(alias, None)
    if begin_time is not None:
        return round((time.perf_counter() - begin_time) * 1000, 2)
    return None


def _record_transaction(action, alias, duration_ms, txn_duration=None, savepoint=None):
    tags = [f"transaction:{action}", f"connection:{alias}"]

    content = {
        "action": action,
        "connection": alias,
        "duration": round(duration_ms, 2),
    }
    if txn_duration is not None:
        content["transaction_duration"] = txn_duration
    if savepoint:
        content["savepoint"] = savepoint

    Recorder.record(entry_type=EntryType.TRANSACTION, content=content, tags=tags)
