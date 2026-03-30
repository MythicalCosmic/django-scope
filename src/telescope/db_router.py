from .settings import get_config

APP_LABEL = "telescope"


class TelescopeRouter:
    """Routes telescope models to a separate database if configured."""

    def _db(self):
        return get_config("DB_CONNECTION")

    def db_for_read(self, model, **hints):
        if model._meta.app_label == APP_LABEL:
            return self._db()
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == APP_LABEL:
            return self._db()
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.app_label == APP_LABEL or obj2._meta.app_label == APP_LABEL:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        target = self._db() or "default"
        if app_label == APP_LABEL:
            return db == target
        return None
