<div align="center">

# Django Scope

**Real-time debugging and observability dashboard for Django**

[![PyPI](https://img.shields.io/pypi/v/django-scope?color=4f46e5&style=flat-square)](https://pypi.org/project/django-scope/)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/django-scope?period=total&units=INTERNATIONAL_SYSTEM&left_color=black&right_color=green&left_text=downloads)](https://pepy.tech/projects/django-scope)
[![Python](https://img.shields.io/pypi/pyversions/django-scope?color=3776ab&style=flat-square)](https://pypi.org/project/django-scope/)
[![Django](https://img.shields.io/badge/django-4.2%20%7C%205.x%20%7C%206.x-0c4b33?style=flat-square)](https://www.djangoproject.com/)
[![License](https://img.shields.io/pypi/l/django-scope?color=22c55e&style=flat-square)](LICENSE)

Monitor requests, queries, exceptions, cache, models, logs, and 13 more event types -- all from a standalone dashboard with live WebSocket updates.

[Installation](#installation) -- [Configuration](#configuration) -- [Watchers](#watchers) -- [MCP Integration](#mcp-integration) -- [API Reference](#api-reference)

</div>

---

## Overview

Django Scope provides a standalone Vue.js dashboard that captures everything happening in your Django application. Unlike debug toolbars that inject into HTML responses, Django Scope works with APIs, SPAs, mobile backends, and background tasks. Data is stored in your database and streamed to the dashboard in real time over WebSocket.

**v2.0** adds a Stats API with response percentiles and Apdex scores, a Health API for watcher status monitoring, MCP integration for AI assistant tooling (Claude, Cursor, Windsurf), transaction tracking, file storage monitoring, and a redesigned glassmorphism dashboard.

### Key capabilities

- **19 watchers** covering HTTP, database, cache, models, exceptions, logs, mail, signals, commands, and more
- **N+1 query detection** with automatic pattern grouping and threshold alerts
- **Stats dashboard** with P50/P75/P95/P99 percentiles, Apdex score, error rates, and cache hit rates
- **Health monitoring** showing per-watcher status (healthy / failed / disabled)
- **MCP server** exposing telemetry tools for AI coding assistants
- **WebSocket live feed** with staggered entry animations
- **Sensitive data redaction** applied automatically to all entry types
- **Zero-config cache monitoring** that works with any Django cache backend

---

## Comparison

### vs Django Debug Toolbar

| Capability | Debug Toolbar | Django Scope |
|:---|:---|:---|
| Interface | Injected into HTML | Standalone SPA dashboard |
| API / SPA support | No (requires HTML response) | Full support |
| Real-time updates | No | WebSocket live feed |
| Background tasks | Not supported | Commands, Celery, batches |
| Data persistence | Lost on refresh | Stored in database |
| N+1 detection | Manual inspection | Automatic with thresholds |
| Stats / analytics | None | Percentiles, Apdex, error rates |
| Cache monitoring | Basic panel | Full operation-level tracking |
| Production use | Not recommended | Authorization gate + pruning |

### vs Silk

| Capability | Silk | Django Scope |
|:---|:---|:---|
| Scope | Requests + queries | 19 watcher types |
| Real-time | Requires refresh | WebSocket live feed |
| Frontend | Server-rendered HTML | Vue.js SPA with themes |
| Cache / Redis | Not tracked | Auto-detected, zero config |
| Model changes | Not tracked | Field-level change tracking |
| N+1 detection | Not built-in | Automatic pattern detection |
| AI integration | None | MCP server with 6 tools |

### vs Sentry / New Relic / Datadog

Those are production monitoring platforms. Django Scope is a **development and debugging tool** -- local, free, instant, with code-level detail and no third-party data transfer. They complement each other.

---

## Installation

### 1. Install the package

```bash
pip install django-scope
```

Optional extras:

```bash
pip install django-scope[redis]   # Redis watcher support
pip install django-scope[mcp]     # MCP server for AI assistants
```

### 2. Configure Django

```python
# settings.py

INSTALLED_APPS = [
    "daphne",        # For WebSocket support (optional)
    # ... your apps
    "telescope",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "telescope.middleware.TelescopeMiddleware",
    # ...
]
```

### 3. Add URL routing

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("telescope/", include("telescope.urls")),
    # ...
]
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Open the dashboard

```
http://localhost:8000/telescope/
```

### WebSocket support (optional)

For real-time live updates, configure ASGI:

```python
# asgi.py
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from telescope.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter(websocket_urlpatterns),
})
```

```python
# settings.py
ASGI_APPLICATION = "myproject.asgi.application"
CHANNEL_LAYERS = {
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
}
```

Without ASGI, the dashboard works normally -- you just won't see live updates.

---

## Configuration

All settings live in a single `TELESCOPE` dictionary:

```python
TELESCOPE = {
    "ENABLED": True,
    "RECORDING": True,
    "IGNORE_PATHS": [r"^/telescope/", r"^/static/", r"^/favicon\.ico$"],
    "IGNORE_METHODS": [],
    "IGNORE_STATUS_CODES": [],

    # Query analysis
    "SLOW_QUERY_THRESHOLD": 100,    # ms
    "N_PLUS_ONE_THRESHOLD": 5,

    # Data management
    "ENTRY_LIFETIME_HOURS": 24,
    "ENTRY_SIZE_LIMIT": 64,         # KB per entry
    "BODY_SIZE_LIMIT": 64,          # KB for request/response body capture

    # Security
    "AUTHORIZATION": lambda request: request.user.is_staff,
    "LOG_LEVEL": "WARNING",
    "MODEL_CHANGE_TRACKING": True,

    # Sensitive data redaction
    "SENSITIVE_HEADERS": [
        "Authorization", "Cookie", "Set-Cookie",
        "X-Api-Key", "X-Auth-Token",
    ],
    "SENSITIVE_FIELDS": [
        "password", "secret", "token", "key", "csrf",
        "ssn", "credit_card", "cvv",
    ],

    # Stats
    "APDEX_THRESHOLD": 500,         # ms

    # Watchers
    "WATCHERS": {
        "RequestWatcher":       {"enabled": True},
        "QueryWatcher":         {"enabled": True},
        "ExceptionWatcher":     {"enabled": True},
        "ModelWatcher":         {"enabled": True},
        "LogWatcher":           {"enabled": True},
        "CacheWatcher":         {"enabled": True},
        "MailWatcher":          {"enabled": True},
        "ViewWatcher":          {"enabled": True},
        "EventWatcher":         {"enabled": True},
        "CommandWatcher":       {"enabled": True},
        "DumpWatcher":          {"enabled": True},
        "GateWatcher":          {"enabled": True},
        "NotificationWatcher":  {"enabled": True},
        "RedisWatcher":         {"enabled": False},
        "ClientRequestWatcher": {"enabled": False},
        "ScheduleWatcher":      {"enabled": False},
        "BatchWatcher":         {"enabled": False},
        "TransactionWatcher":   {"enabled": False},
        "StorageWatcher":       {"enabled": False},
    },
}
```

---

## Watchers

### Request Watcher

Captures HTTP requests and responses: method, path, headers, payload, response body, status code, duration, resolved view, and user/session. Sensitive headers and payload fields are automatically redacted.

### Query Watcher

Records every database query with SQL, bindings, execution time, and connection alias. Detects:

- **Slow queries** -- flagged when duration exceeds `SLOW_QUERY_THRESHOLD`
- **N+1 patterns** -- flagged when the same normalized query repeats `N_PLUS_ONE_THRESHOLD` times in a single request. All queries in the pattern are tagged (not just the Nth one).

SQL normalization handles string literals, integers, floats, hex values, negative numbers, and variable-length `IN` clauses to produce consistent pattern hashes.

### Exception Watcher

Captures unhandled exceptions with full stack trace, exception class, message, and source context around the error line.

### Model Watcher

Tracks create, update, and delete operations. Records field-level changes on updates (old vs new values). Sensitive fields (password, token, etc.) are masked automatically. Change tracking can be disabled via `MODEL_CHANGE_TRACKING: False` for performance.

### Log Watcher

Captures Python logging entries. Default minimum level is `WARNING` (configurable via `LOG_LEVEL`). Filters out Django's internal debug noise and telescope's own logs.

### Cache Watcher

Monitors `get`, `set`, `delete`, `clear`, `get_many`, `set_many`, `delete_many`, `has_key`, `incr`, `decr`. Records key, value, hit/miss status, duration, and backend alias. Works with any cache backend automatically -- no configuration needed.

### Redis Watcher

Captures raw Redis commands with arguments, duration, and connection info. Patches `redis-py` and `django-redis`.

```python
"RedisWatcher": {"enabled": True}
```

### Mail Watcher

Records outgoing emails: recipients, subject, body, and attachment names.

### View Watcher

Tracks template rendering: template name and render duration.

### Event Watcher

Records Django signal dispatches. Ignores internal signals (`pre_save`, `post_save`, `request_started`, etc.) to avoid noise.

### Command Watcher

Captures management command execution: name, arguments, exit code, output, and duration. Includes N+1 detection within commands.

### Dump Watcher

Inspect values from anywhere in your code:

```python
import telescope

telescope.dump(some_object, label="Debug data")
```

### Client Request Watcher

Monitors outgoing HTTP requests via `requests` or `httpx`: URL, method, status, headers, duration.

### Gate Watcher

Tracks permission checks: user, permission, and grant/deny result.

### Notification Watcher

Records notifications: class, recipient, and delivery channels.

### Schedule Watcher

Tracks Celery Beat task execution. Requires `celery`.

### Batch Watcher

Monitors Celery group/chord operations. Requires `celery`.

### Transaction Watcher

Tracks database transaction boundaries: `BEGIN`, `COMMIT`, `ROLLBACK`, and `SAVEPOINT` with transaction duration.

```python
"TransactionWatcher": {"enabled": True}
```

### Storage Watcher

Monitors file storage operations: `save`, `delete`, `open`, `exists` with duration and backend class.

```python
"StorageWatcher": {"enabled": True}
```

---

## API Endpoints

All endpoints require authorization (defaults to `DEBUG = True`, configurable via `AUTHORIZATION`).

| Method | Path | Description |
|:---|:---|:---|
| `GET` | `/api/entries` | List entries with filtering and pagination |
| `GET` | `/api/entries/<type_slug>` | List entries by type |
| `GET` | `/api/entry/<uuid>` | Entry detail |
| `GET` | `/api/batch/<batch_id>` | All entries in a request batch |
| `DELETE` | `/api/entry/<uuid>/delete` | Delete single entry |
| `DELETE` | `/api/clear?type=<slug>` | Clear entries (optionally by type) |
| `GET` | `/api/status` | Entry counts and recording state |
| `GET` | `/api/stats?range=24h` | Percentiles, Apdex, error rate, cache stats |
| `GET` | `/api/health` | Per-watcher health status |
| `POST` | `/api/toggle-recording` | Toggle recording on/off |
| `GET/POST/DELETE` | `/api/monitoring` | Manage monitored tags |

### Query parameters for list endpoints

| Parameter | Description |
|:---|:---|
| `search` | Full-text search in content and tags |
| `tag` | Filter by tag (e.g. `slow`, `n+1`, `status:500`) |
| `batch_id` | Filter by request batch |
| `family_hash` | Group N+1 queries by pattern |
| `before` | Cursor-based pagination (entry ID) |
| `limit` | Results per page (max 100, default 50) |

### Stats response

```json
{
  "range": "24h",
  "requests": {
    "total": 1250,
    "percentiles": {"p50": 12.5, "p75": 45.2, "p95": 180.0, "p99": 520.0},
    "apdex": 0.945,
    "error_rate": 2.4,
    "throughput_per_minute": 8.68
  },
  "queries": {
    "total": 5200,
    "slow_patterns": [{"family_hash": "...", "count": 42, "avg_duration": 150.2}],
    "n_plus_one_patterns": 3
  },
  "cache": {"total": 890, "hits": 756, "hit_rate": 84.94}
}
```

---

## MCP Integration

Django Scope includes an MCP (Model Context Protocol) server that exposes telemetry data to AI coding assistants like Claude, Cursor, and Windsurf.

### Setup

```bash
pip install django-scope[mcp]
python manage.py telescope_mcp
```

### Available tools

| Tool | Description |
|:---|:---|
| `get_recent_requests` | Recent HTTP requests, filterable by status code |
| `get_slow_queries` | Queries above a duration threshold |
| `get_exceptions` | Recent unhandled exceptions |
| `get_n1_patterns` | N+1 query patterns grouped by family hash |
| `search_entries` | Full-text search across all entry types |
| `get_stats_summary` | Application stats for a time range |

---

## Management Commands

```bash
# Prune entries older than configured lifetime (default 24h)
python manage.py telescope_prune

# Prune entries older than 6 hours
python manage.py telescope_prune --hours 6

# Clear all entries
python manage.py telescope_clear

# Clear only query entries
python manage.py telescope_clear --type query

# Start MCP server
python manage.py telescope_mcp
```

---

## Authorization

Default: dashboard accessible only when `DEBUG = True`.

```python
# Staff users only
TELESCOPE = {
    "AUTHORIZATION": lambda request: request.user.is_staff,
}
```

```python
# Custom logic
def telescope_authorized(request):
    if not request.user.is_authenticated:
        return False
    return request.user.email.endswith("@company.com")

TELESCOPE = {
    "AUTHORIZATION": telescope_authorized,
}
```

Authorization is enforced on HTTP API endpoints, WebSocket connections, and the SPA template.

---

## Performance

- **Request-scoped buffering** -- entries collected in memory, written in a single `bulk_create` per request
- **Async WebSocket broadcast** -- runs in a background thread, does not block the response
- **Re-entrancy guard** -- telescope's own queries are never recorded
- **Sensitive data redaction** -- applied once in the recorder, covers all 19 entry types
- **Path filtering** -- dashboard and static file routes excluded by default
- **Configurable pruning** -- automatic cleanup of old entries

---

## Database

Three tables:

| Table | Purpose |
|:---|:---|
| `telescope_entries` | All recorded entries (UUID, type, JSON content, batch ID, family hash, timestamps) |
| `telescope_entries_tags` | Searchable tags for filtering (composite index on entry + tag) |
| `telescope_monitoring` | Selective monitoring configuration |

Indexes on `created_at + type`, `batch_id`, `family_hash`, and `entry + tag` for efficient queries.

---

## Requirements

| Dependency | Version |
|:---|:---|
| Python | 3.10+ |
| Django | 4.2+ |
| channels | 4.0+ |
| daphne | 4.2+ (optional, for ASGI) |
| redis / django-redis | 4.0+ / 5.0+ (optional) |
| celery | any (optional, for Schedule/Batch watchers) |
| mcp | 1.0+ (optional, for AI integration) |

---

## License

MIT

---

<div align="center">

Built by [MythicalCosmic](https://github.com/MythicalCosmic)

</div>
