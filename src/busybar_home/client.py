"""Device boundary used by the application and tests."""

from typing import Protocol, runtime_checkable

from busybar_home.models import DeviceSnapshot, DisplayScene


class DisplayOwnershipError(RuntimeError):
    """Raised when another BUSY application currently owns the displays."""


@runtime_checkable
class DeviceClient(Protocol):
    """Minimal BUSY Bar operations needed by this application."""

    def snapshot(self) -> DeviceSnapshot:
        """Return a small device-health snapshot."""

    def show_scene(self, scene: DisplayScene) -> None:
        """Show a coordinated scene on both displays."""

    def close(self) -> None:
        """Release resources held by the client."""
