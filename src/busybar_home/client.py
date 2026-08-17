"""Device boundary used by the application and tests."""

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from busybar_home.models import DeviceLog, DeviceSnapshot, DisplayFrame, DisplayScene


class DisplayOwnershipError(RuntimeError):
    """Raised when another BUSY application currently owns the displays."""


@runtime_checkable
class DeviceClient(Protocol):
    """Minimal BUSY Bar operations needed by this application."""

    def snapshot(self) -> DeviceSnapshot:
        """Return a small device-health snapshot."""

    def front_screen_frame(self) -> DisplayFrame:
        """Return the current front display as decoded RGB pixels."""

    def stream_front_screen_frames(self) -> AsyncIterator[DisplayFrame]:
        """Yield live front-display frames until the consumer disconnects."""

    def show_scene(self, scene: DisplayScene) -> None:
        """Show a coordinated scene on both displays."""

    def capture_logs(self) -> DeviceLog:
        """Snapshot and read the device's bounded diagnostic log."""

    def close(self) -> None:
        """Release resources held by the client."""
