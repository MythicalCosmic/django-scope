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
    "RECORDING": True,
    "AUTHORIZATION": None,  # callable(request) -> bool; defaults to DEBUG
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
        return merged.get(key, DEFAULTS.get(key))
    return merged
