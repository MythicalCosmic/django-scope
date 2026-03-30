from enum import IntEnum


class EntryType(IntEnum):
    REQUEST = 1
    QUERY = 2
    EXCEPTION = 3
    MODEL = 4
    LOG = 5
    CACHE = 6
    REDIS = 7
    MAIL = 8
    VIEW = 9
    EVENT = 10
    COMMAND = 11
    DUMP = 12
    CLIENT_REQUEST = 13
    GATE = 14
    NOTIFICATION = 15
    SCHEDULE = 16
    BATCH = 17

    @property
    def label(self):
        return self.name.replace("_", " ").title()

    @property
    def slug(self):
        return self.name.lower().replace("_", "-")

    @classmethod
    def from_slug(cls, slug):
        name = slug.upper().replace("-", "_")
        return cls[name]
