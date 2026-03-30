import uuid
from contextvars import ContextVar

# Unique ID grouping all entries from the same request/command
batch_id_var: ContextVar[str | None] = ContextVar("telescope_batch_id", default=None)

# Buffer of entries to be flushed at end of request
buffer_var: ContextVar[list | None] = ContextVar("telescope_buffer", default=None)

# Whether recording is active for this scope
recording_var: ContextVar[bool] = ContextVar("telescope_recording", default=True)


def start_scope():
    """Begin a new telescope scope (called at request start)."""
    batch_id_var.set(str(uuid.uuid4()))
    buffer_var.set([])
    recording_var.set(True)


def end_scope():
    """End the current telescope scope."""
    batch_id_var.set(None)
    buffer_var.set(None)
    recording_var.set(True)


def get_batch_id():
    return batch_id_var.get()


def get_buffer():
    return buffer_var.get()


def is_recording():
    return recording_var.get()
