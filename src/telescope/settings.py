import threading

from django.conf import settings

DEFAULTS = {
    "ENABLED": True,
    "PATH": "telescope/",
    "DB_CONNECTION": None,
    "IGNORE_PATHS": [r"^/telescope/", r"^/static/", r"^/favicon\.ico$"],
    "IGNORE_METHODS": [],
    "IGNORE_STATUS_CODES": [],
    "SLOW_QUERY_THRESHOLD": 100,  # ms
    "N_PLUS_ONE_THRESHOLD": 5,
    "ENTRY_LIFETIME_HOURS": 24,
    "ENTRY_SIZE_LIMIT": 64,  # KB
    "BODY_SIZE_LIMIT": 64,  # KB — max captured request/response body size
    "RECORDING": True,
    "AUTHORIZATION": None,  # callable(request) -> bool; defaults to DEBUG
    "LOG_LEVEL": "WARNING",  # minimum log level to capture
    "MODEL_CHANGE_TRACKING": True,  # fetch original values on model update
    "SENSITIVE_HEADERS": [
        "Authorization",
        "Proxy-Authorization",
        "Cookie",
        "Set-Cookie",
        "X-Api-Key",
        "X-Auth-Token",
        "X-Csrf-Token",
    ],
    "SENSITIVE_FIELDS": [
        "password",
        "secret",
        "token",
        "key",
        "csrf",
        "ssn",
        "credit_card",
        "card_number",
        "cvv",
    ],
    "WATCHERS": {
        "RequestWatcher": {"enabled": True},
        "QueryWatcher": {"enabled": True},
        "ExceptionWatcher": {"enabled": True},
        "ModelWatcher": {"enabled": True},
        "LogWatcher": {"enabled": True},
        "CacheWatcher": {"enabled": True},
        "MailWatcher": {"enabled": True},
        "RedisWatcher": {"enabled": False},
        "ViewWatcher": {"enabled": True},
        "EventWatcher": {"enabled": True},
        "CommandWatcher": {"enabled": True},
        "DumpWatcher": {"enabled": True},
        "ClientRequestWatcher": {"enabled": False},
        "GateWatcher": {"enabled": True},
        "NotificationWatcher": {"enabled": True},
        "ScheduleWatcher": {"enabled": False},
        "BatchWatcher": {"enabled": False},
    },
}

# Thread-safe runtime state for values toggled at runtime (e.g. RECORDING).
# This avoids mutating django.conf.settings which is not thread-safe.
_runtime_lock = threading.Lock()
_runtime_state: dict = {}


def set_runtime(key, value):
    """Set a runtime override for a config key (thread-safe)."""
    with _runtime_lock:
        _runtime_state[key] = value


def get_config(key=None):
    user_config = getattr(settings, "TELESCOPE", {})
    merged = {**DEFAULTS, **user_config}

    if key == "WATCHERS":
        watchers = {**DEFAULTS["WATCHERS"]}
        user_watchers = user_config.get("WATCHERS", {})
        for name, opts in user_watchers.items():
            if name in watchers:
                watchers[name] = {**watchers[name], **opts}
            else:
                watchers[name] = opts
        return watchers

    if key is not None:
        # Runtime overrides take precedence
        with _runtime_lock:
            if key in _runtime_state:
                return _runtime_state[key]
        return merged.get(key, DEFAULTS.get(key))
    return merged
