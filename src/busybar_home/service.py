"""Application use cases."""

from busybar_home.client import DeviceClient
from busybar_home.models import DeviceSnapshot, DisplayScene


class BusyBarService:
    """Coordinate BUSY Bar actions through a replaceable client."""

    def __init__(self, client: DeviceClient) -> None:
        self._client = client

    def apply_scene(self, scene: DisplayScene) -> DeviceSnapshot:
        """Apply a scene through the selected client and return its status."""
        self._client.show_scene(scene)
        return self._client.snapshot()
