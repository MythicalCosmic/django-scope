from telescope.entry_type import EntryType


class TestEntryType:
    def test_all_types_defined(self):
        assert len(EntryType) == 19

    def test_label(self):
        assert EntryType.REQUEST.label == "Request"
        assert EntryType.CLIENT_REQUEST.label == "Client Request"

    def test_slug(self):
        assert EntryType.REQUEST.slug == "request"
        assert EntryType.CLIENT_REQUEST.slug == "client-request"

    def test_from_slug(self):
        assert EntryType.from_slug("request") == EntryType.REQUEST
        assert EntryType.from_slug("client-request") == EntryType.CLIENT_REQUEST

    def test_values_are_sequential(self):
        values = [e.value for e in EntryType]
        assert values == list(range(1, 20))
