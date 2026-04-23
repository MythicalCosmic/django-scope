import hashlib
from collections import defaultdict

import pytest

from telescope.context import end_scope, start_scope
from telescope.entry_type import EntryType
from telescope.models import TelescopeEntry, TelescopeEntryTag
from telescope.recorder import Recorder
from telescope.watchers.query_watcher import QueryWatcher, reset_query_tracking


@pytest.mark.django_db
class TestFamilyHashPersistence:
    """Verify family_hash is extracted from content and saved to the model column."""

    def test_family_hash_persisted(self):
        content = {
            "sql": "SELECT * FROM users WHERE id = ?",
            "duration": 1.5,
            "family_hash": "abc123def456",
        }
        Recorder.record(entry_type=EntryType.QUERY, content=content, tags=["slow"])

        entry = TelescopeEntry.objects.first()
        assert entry is not None
        assert entry.family_hash == "abc123def456"

    def test_family_hash_none_when_not_in_content(self):
        content = {"sql": "SELECT 1", "duration": 0.1}
        Recorder.record(entry_type=EntryType.QUERY, content=content)

        entry = TelescopeEntry.objects.first()
        assert entry is not None
        assert entry.family_hash is None

    def test_family_hash_queryable(self):
        for i in range(3):
            Recorder.record(
                entry_type=EntryType.QUERY,
                content={"sql": f"SELECT {i}", "family_hash": "same_hash"},
            )
        Recorder.record(
            entry_type=EntryType.QUERY,
            content={"sql": "SELECT other", "family_hash": "different_hash"},
        )

        results = TelescopeEntry.objects.filter(family_hash="same_hash")
        assert results.count() == 3


@pytest.mark.django_db
class TestRetroactiveNPlusOneTagging:
    """Verify ALL queries in an N+1 pattern get tagged, not just the Nth+."""

    def test_all_queries_tagged_when_threshold_met(self):
        start_scope()
        reset_query_tracking()

        family_hash = "test_pattern_hash"
        for i in range(6):
            Recorder.record(
                entry_type=EntryType.QUERY,
                content={
                    "sql": f"SELECT * FROM users WHERE id = {i}",
                    "duration": 1.0,
                    "family_hash": family_hash,
                },
                tags=[],
            )

        Recorder.flush()
        end_scope()

        entries = TelescopeEntry.objects.filter(family_hash=family_hash)
        assert entries.count() == 6

        for entry in entries:
            tags = list(entry.tags.values_list("tag", flat=True))
            assert "n+1" in tags, f"Entry {entry.uuid} missing n+1 tag"
            assert entry.content["n_plus_one"] is True

    def test_threshold_configurable(self, settings):
        settings.TELESCOPE = {**settings.TELESCOPE, "N_PLUS_ONE_THRESHOLD": 3}

        start_scope()
        reset_query_tracking()

        family_hash = "threshold_test_hash"
        for i in range(3):
            Recorder.record(
                entry_type=EntryType.QUERY,
                content={"sql": f"SELECT {i}", "duration": 1.0, "family_hash": family_hash},
                tags=[],
            )

        Recorder.flush()
        end_scope()

        entries = TelescopeEntry.objects.filter(family_hash=family_hash)
        assert entries.count() == 3
        for entry in entries:
            tags = list(entry.tags.values_list("tag", flat=True))
            assert "n+1" in tags

    def test_below_threshold_not_tagged(self):
        start_scope()
        reset_query_tracking()

        family_hash = "below_threshold_hash"
        # Default threshold is 5, only send 4
        for i in range(4):
            Recorder.record(
                entry_type=EntryType.QUERY,
                content={"sql": f"SELECT {i}", "duration": 1.0, "family_hash": family_hash},
                tags=[],
            )

        Recorder.flush()
        end_scope()

        entries = TelescopeEntry.objects.filter(family_hash=family_hash)
        assert entries.count() == 4
        for entry in entries:
            tags = list(entry.tags.values_list("tag", flat=True))
            assert "n+1" not in tags

    def test_different_queries_not_tagged(self):
        start_scope()
        reset_query_tracking()

        for i in range(6):
            Recorder.record(
                entry_type=EntryType.QUERY,
                content={"sql": f"SELECT * FROM table_{i}", "duration": 1.0, "family_hash": f"unique_hash_{i}"},
                tags=[],
            )

        Recorder.flush()
        end_scope()

        entries = TelescopeEntry.objects.all()
        assert entries.count() == 6
        for entry in entries:
            tags = list(entry.tags.values_list("tag", flat=True))
            assert "n+1" not in tags

    def test_non_query_entries_unaffected(self):
        start_scope()
        reset_query_tracking()

        # Mix of query and non-query entries
        for i in range(6):
            Recorder.record(
                entry_type=EntryType.QUERY,
                content={"sql": f"SELECT {i}", "duration": 1.0, "family_hash": "repeated_hash"},
                tags=[],
            )
        Recorder.record(
            entry_type=EntryType.LOG,
            content={"level": "INFO", "message": "test"},
            tags=[],
        )

        Recorder.flush()
        end_scope()

        log_entry = TelescopeEntry.objects.filter(type=EntryType.LOG.value).first()
        assert log_entry is not None
        tags = list(log_entry.tags.values_list("tag", flat=True))
        assert "n+1" not in tags


class TestSqlNormalization:
    """Verify SQL normalization produces consistent hashes."""

    def setup_method(self):
        self.watcher = QueryWatcher(options={})

    def test_integer_normalization(self):
        sql1 = self.watcher._normalize_sql("SELECT * FROM users WHERE id = 42")
        sql2 = self.watcher._normalize_sql("SELECT * FROM users WHERE id = 999")
        assert sql1 == sql2

    def test_string_normalization(self):
        sql1 = self.watcher._normalize_sql("SELECT * FROM users WHERE name = 'John'")
        sql2 = self.watcher._normalize_sql("SELECT * FROM users WHERE name = 'Jane'")
        assert sql1 == sql2

    def test_escaped_quotes(self):
        sql1 = self.watcher._normalize_sql("SELECT * FROM users WHERE name = 'O''Brien'")
        sql2 = self.watcher._normalize_sql("SELECT * FROM users WHERE name = 'Smith'")
        assert sql1 == sql2

    def test_float_normalization(self):
        sql1 = self.watcher._normalize_sql("SELECT * FROM prices WHERE amount > 3.14")
        sql2 = self.watcher._normalize_sql("SELECT * FROM prices WHERE amount > 99.99")
        assert sql1 == sql2

    def test_hex_normalization(self):
        sql1 = self.watcher._normalize_sql("SELECT * FROM data WHERE flags = 0xFF")
        sql2 = self.watcher._normalize_sql("SELECT * FROM data WHERE flags = 0x00")
        assert sql1 == sql2

    def test_in_clause_normalization(self):
        sql1 = self.watcher._normalize_sql("SELECT * FROM users WHERE id IN (1, 2)")
        sql2 = self.watcher._normalize_sql("SELECT * FROM users WHERE id IN (1, 2, 3, 4, 5)")
        assert sql1 == sql2

    def test_whitespace_normalization(self):
        sql1 = self.watcher._normalize_sql("SELECT  *  FROM   users   WHERE  id = 1")
        sql2 = self.watcher._normalize_sql("SELECT * FROM users WHERE id = 2")
        assert sql1 == sql2

    def test_different_queries_different_hashes(self):
        sql1 = self.watcher._normalize_sql("SELECT * FROM users WHERE id = 1")
        sql2 = self.watcher._normalize_sql("SELECT * FROM orders WHERE id = 1")
        assert sql1 != sql2

    def test_hash_consistency(self):
        """Same normalized SQL should always produce the same hash."""
        sql = "SELECT * FROM users WHERE id = 42 AND name = 'John'"
        hash1 = hashlib.md5(self.watcher._normalize_sql(sql).encode()).hexdigest()
        hash2 = hashlib.md5(self.watcher._normalize_sql(sql).encode()).hexdigest()
        assert hash1 == hash2
