import uuid

from django.db import models

from .entry_type import EntryType


class TelescopeEntry(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    batch_id = models.UUIDField(null=True, blank=True, db_index=True)
    family_hash = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    type = models.SmallIntegerField(choices=[(t.value, t.label) for t in EntryType], db_index=True)
    content = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "telescope_entries"
        ordering = ["-id"]
        indexes = [
            models.Index(fields=["-created_at", "type"]),
        ]

    def __str__(self):
        return f"{EntryType(self.type).label} {self.uuid}"

    @property
    def entry_type(self):
        return EntryType(self.type)


class TelescopeEntryTag(models.Model):
    entry = models.ForeignKey(TelescopeEntry, on_delete=models.CASCADE, related_name="tags")
    tag = models.CharField(max_length=255, db_index=True)

    class Meta:
        db_table = "telescope_entries_tags"
        indexes = [
            models.Index(fields=["entry", "tag"]),
        ]

    def __str__(self):
        return self.tag


class TelescopeMonitoring(models.Model):
    tag = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = "telescope_monitoring"

    def __str__(self):
        return self.tag
