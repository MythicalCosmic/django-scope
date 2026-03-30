from django.apps import AppConfig


class TelescopeConfig(AppConfig):
    name = "telescope"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = "Django Telescope"

    def ready(self):
        from .settings import get_config

        if get_config("ENABLED"):
            from .watchers import WatcherRegistry

            WatcherRegistry.register_all()
