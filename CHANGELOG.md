# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-04-23

### Added

- **Stats API** (`/api/stats`) -- response time percentiles (P50/P75/P95/P99), Apdex score, error rate, throughput, slow query pattern analysis, cache hit rate. Supports time range selection (1h, 6h, 24h, 7d).
- **Health API** (`/api/health`) -- per-watcher status reporting (healthy, failed, disabled) with dependency tracking and error messages.
- **MCP integration** -- Model Context Protocol server with 6 tools for AI coding assistants (Claude, Cursor, Windsurf). Install with `pip install django-scope[mcp]`, start with `python manage.py telescope_mcp`.
- **Transaction watcher** -- tracks `BEGIN`, `COMMIT`, `ROLLBACK`, and `SAVEPOINT` boundaries with transaction duration.
- **Storage watcher** -- monitors file storage operations (`save`, `delete`, `open`, `exists`).
- **Stats dashboard page** -- percentile bars, Apdex gauge, error rate, cache performance, slow query patterns.
- **Health dashboard page** -- watcher status grid with healthy/failed/disabled indicators.
- **Glassmorphism UI** -- frosted glass cards, glow-on-hover effects, staggered entry animations, pulse ring on live indicator.
- **Universal sensitive data redaction** -- applied automatically in the recorder to all 19 entry types, not just requests.
- **Configurable settings** -- `BODY_SIZE_LIMIT`, `LOG_LEVEL`, `MODEL_CHANGE_TRACKING`, `SENSITIVE_HEADERS`, `SENSITIVE_FIELDS`, `APDEX_THRESHOLD`.

### Fixed

- **N+1 detection** -- `family_hash` was computed but never saved to the database column (always NULL). Now properly extracted and persisted.
- **N+1 tagging** -- previously only the Nth+ query got the `n+1` tag. Now all queries in the pattern are tagged retroactively before flush.
- **SQL normalization** -- added handling for escaped quotes, floats, hex literals, negative numbers, and variable-length `IN` clauses.
- **N+1 in commands** -- management commands now initialize query tracking scope, enabling N+1 detection outside HTTP requests.
- **Recording toggle** -- was mutating `django.conf.settings` directly (not thread-safe) and the `RECORDING` config was never actually checked in the recording path. Now uses thread-safe runtime state.
- **`end_scope()` bug** -- was resetting `recording_var` to `True`, overriding any global recording disable.
- **`CacheWatcher.record_operation()`** -- method did not exist, causing `AttributeError` at runtime when using `TelescopeCacheBackend`.
- **Query pattern memory leak** -- `_query_patterns` ContextVar was never reset between requests.

### Changed

- **Log watcher** default level changed from `DEBUG` to `WARNING` to prevent database flooding.
- **Broadcast** -- now batched (single WebSocket message per flush) and runs in a background thread instead of blocking the response.
- **`bulk_create`** calls now use `batch_size` parameter.
- **Session keys** are hashed (SHA-256 prefix) instead of stored in plaintext.
- **Response/request headers** filtered against configurable `SENSITIVE_HEADERS` list.
- **JSON payloads** recursively masked against `SENSITIVE_FIELDS` patterns.
- **Model field changes** mask sensitive field names automatically.
- **WebSocket consumer** now checks authorization before accepting connections.

### Database

- New migration `0002_add_indexes` -- composite index on `(entry_id, tag)`, index on `family_hash`.
- New migration `0003_entry_type_update` -- adds `TRANSACTION` (18) and `STORAGE` (19) entry type choices.

## [1.0.1] - 2026-03-31

### Fixed

- CSRF token handling for API endpoints.
- Cache watcher tracked methods registration.

## [1.0.0] - 2026-03-30

Initial release.

- 17 watchers: Request, Query, Exception, Model, Log, Cache, Redis, Mail, View, Event, Command, Dump, Client Request, Gate, Notification, Schedule, Batch.
- Vue.js SPA dashboard with dark/light themes.
- WebSocket real-time updates via Django Channels.
- Request-scoped buffering with single bulk write.
- Automatic cache backend detection.
- Authorization gate and entry pruning.
