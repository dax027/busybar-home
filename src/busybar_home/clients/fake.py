"""In-memory device client for local development and tests."""

from dataclasses import dataclass, field

from busybar_home.models import DeviceSnapshot, DisplayScene


@dataclass(slots=True)
class FakeDeviceClient:
    """Record requested actions without network or hardware access."""

    firmware_version: str = "fake-1.0"
    scenes: list[DisplayScene] = field(default_factory=list)
    closed: bool = False

    def snapshot(self) -> DeviceSnapshot:
        self._ensure_open()
        return DeviceSnapshot(connected=True, firmware_version=self.firmware_version)

    def show_scene(self, scene: DisplayScene) -> None:
        self._ensure_open()
        self.scenes.append(scene)

    def close(self) -> None:
        self.closed = True

    def _ensure_open(self) -> None:
        if self.closed:
            raise RuntimeError("client is closed")
