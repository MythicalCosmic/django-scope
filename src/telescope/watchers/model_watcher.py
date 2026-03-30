from django.db.models.signals import post_delete, post_save, pre_save

from ..entry_type import EntryType
from ..recorder import Recorder
from .base import BaseWatcher

# Store original field values for change tracking
_ORIGINAL_VALUES_ATTR = "_telescope_original_values"


class ModelWatcher(BaseWatcher):
    def register(self):
        pre_save.connect(self._on_pre_save)
        post_save.connect(self._on_post_save)
        post_delete.connect(self._on_post_delete)

    def _should_ignore(self, sender):
        # Ignore telescope's own models
        if sender._meta.app_label == "telescope":
            return True
        # Ignore Django internal models
        if sender._meta.app_label in ("contenttypes", "sessions", "admin"):
            return True
        return False

    def _on_pre_save(self, sender, instance, **kwargs):
        if self._should_ignore(sender):
            return

        # Store original values for change detection
        if instance.pk:
            try:
                original = sender.objects.filter(pk=instance.pk).values().first()
                if original:
                    setattr(instance, _ORIGINAL_VALUES_ATTR, original)
            except Exception:
                pass

    def _on_post_save(self, sender, instance, created, **kwargs):
        if self._should_ignore(sender):
            return

        action = "created" if created else "updated"
        changes = {}

        if not created and hasattr(instance, _ORIGINAL_VALUES_ATTR):
            original = getattr(instance, _ORIGINAL_VALUES_ATTR)
            for field in sender._meta.fields:
                field_name = field.attname
                old_val = original.get(field_name)
                new_val = getattr(instance, field_name, None)
                if str(old_val) != str(new_val):
                    changes[field_name] = {"old": str(old_val), "new": str(new_val)}
            delattr(instance, _ORIGINAL_VALUES_ATTR)

        tags = [f"model:{sender.__name__}", f"action:{action}"]
        if instance.pk:
            tags.append(f"id:{instance.pk}")

        content = {
            "model": f"{sender._meta.app_label}.{sender.__name__}",
            "action": action,
            "key": str(instance.pk),
            "changes": changes,
        }

        Recorder.record(entry_type=EntryType.MODEL, content=content, tags=tags)

    def _on_post_delete(self, sender, instance, **kwargs):
        if self._should_ignore(sender):
            return

        tags = [f"model:{sender.__name__}", "action:deleted"]
        if instance.pk:
            tags.append(f"id:{instance.pk}")

        content = {
            "model": f"{sender._meta.app_label}.{sender.__name__}",
            "action": "deleted",
            "key": str(instance.pk),
            "changes": {},
        }

        Recorder.record(entry_type=EntryType.MODEL, content=content, tags=tags)
