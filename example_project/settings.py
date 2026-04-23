from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

SECRET_KEY = "django-insecure-telescope-example-key-do-not-use-in-production"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "daphne",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "telescope",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "telescope.middleware.TelescopeMiddleware",
]

ROOT_URLCONF = "urls"
ASGI_APPLICATION = "asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

STATIC_URL = "/static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

TELESCOPE = {
    "ENABLED": True,
    "RECORDING": True,
    "WATCHERS": {
        "RequestWatcher": {"enabled": True},
        "QueryWatcher": {"enabled": True},
        "ExceptionWatcher": {"enabled": True},
        "ModelWatcher": {"enabled": True},
        "LogWatcher": {"enabled": True},
        "DumpWatcher": {"enabled": True},
        "CacheWatcher": {"enabled": True},
        "RedisWatcher": {"enabled": False},
        "ViewWatcher": {"enabled": False},
        "EventWatcher": {"enabled": False},
        "MailWatcher": {"enabled": False},
        "ClientRequestWatcher": {"enabled": False},
        "CommandWatcher": {"enabled": False},
        "GateWatcher": {"enabled": False},
        "NotificationWatcher": {"enabled": False},
        "ScheduleWatcher": {"enabled": False},
        "BatchWatcher": {"enabled": False},
    },
}
