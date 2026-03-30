from abc import ABC, abstractmethod


class BaseWatcher(ABC):
    """Abstract base class for all telescope watchers."""

    def __init__(self, options=None):
        self.options = options or {}

    @abstractmethod
    def register(self):
        """Hook into Django/Python to start watching. Called once at startup."""

    def unregister(self):
        """Unhook. Optional — most watchers don't need this."""

    @property
    def name(self):
        return self.__class__.__name__
