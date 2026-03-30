# django-telescope

An elegant debug assistant for Django, inspired by Laravel Telescope.

## Installation

```bash
pip install django-telescope
```

Add to your Django settings:

```python
INSTALLED_APPS = [
    "daphne",
    "telescope",
    # ... your apps
]

TELESCOPE = {
    "ENABLED": True,
}
```

Add the middleware:

```python
MIDDLEWARE = [
    "telescope.middleware.TelescopeMiddleware",
    # ... other middleware
]
```

Add URL routing:

```python
from django.urls import include, path

urlpatterns = [
    path("telescope/", include("telescope.urls")),
]
```

## Features

- Real-time monitoring via WebSockets
- 17 watchers: requests, queries, exceptions, models, logs, cache, mail, Redis, views, events, commands, dumps, HTTP client, gates, notifications, schedules, batches
- N+1 query detection
- Beautiful Vue.js dashboard with dark/light themes
- Request-scoped buffering with bulk writes
