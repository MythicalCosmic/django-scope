import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

logger = logging.getLogger("telescope.consumers")


class TelescopeConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time telescope entry updates."""

    async def connect(self):
        # Check authorization before accepting the connection
        if not await self._is_authorized():
            await self.close()
            return

        await self.channel_layer.group_add("telescope", self.channel_name)
        await self.accept()
        logger.debug("Telescope WebSocket connected: %s", self.channel_name)

    async def _is_authorized(self):
        from ..settings import get_config

        auth_callback = get_config("AUTHORIZATION")
        if auth_callback and callable(auth_callback):
            user = self.scope.get("user")
            if user is None or user.is_anonymous:
                return False
            # Build a minimal request-like object from scope for the callback
            from django.http import HttpRequest
            request = HttpRequest()
            request.user = user
            request.META = dict(self.scope.get("headers", []))
            try:
                return auth_callback(request)
            except Exception:
                return False

        # Fall back to DEBUG mode check
        from django.conf import settings
        return getattr(settings, "DEBUG", False)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("telescope", self.channel_name)
        logger.debug("Telescope WebSocket disconnected: %s", self.channel_name)

    async def receive_json(self, content, **kwargs):
        msg_type = content.get("type")
        if msg_type == "filter":
            self._filters = content.get("filters", {})

    async def telescope_entries(self, event):
        """Handle batched telescope entries broadcast."""
        entries = event.get("entries", [])
        filters = getattr(self, "_filters", None)
        allowed_types = filters.get("types") if filters else None

        for entry in entries:
            if allowed_types and entry.get("type_slug") not in allowed_types:
                continue
            await self.send_json({"type": "entry", "data": entry})

    async def telescope_entry(self, event):
        """Handle single telescope entry broadcast (backwards compat)."""
        entry = event.get("entry", {})

        filters = getattr(self, "_filters", None)
        if filters:
            allowed_types = filters.get("types")
            if allowed_types and entry.get("type_slug") not in allowed_types:
                return

        await self.send_json({"type": "entry", "data": entry})
