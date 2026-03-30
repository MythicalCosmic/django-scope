default_app_config = "telescope.apps.TelescopeConfig"


def dump(value, *, label=None):
    """Public API: record a dump entry from user code."""
    import inspect
    from .entry_type import EntryType
    from .recorder import Recorder

    frame = inspect.currentframe().f_back
    caller = f"{frame.f_code.co_filename}:{frame.f_lineno}"

    Recorder.record(
        entry_type=EntryType.DUMP,
        content={
            "dump": repr(value),
            "label": label,
            "caller": caller,
        },
    )


def notify(notification_class, recipient, channels=None):
    """Public API: record a notification entry."""
    from .entry_type import EntryType
    from .recorder import Recorder

    Recorder.record(
        entry_type=EntryType.NOTIFICATION,
        content={
            "notification": notification_class.__name__ if isinstance(notification_class, type) else str(notification_class),
            "recipient": str(recipient),
            "channels": channels or [],
        },
    )
