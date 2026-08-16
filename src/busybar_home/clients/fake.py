"""In-memory device client for local development and tests."""

from dataclasses import dataclass, field

from busybar_home.models import DeviceLog, DeviceSnapshot, DisplayScene


@dataclass(slots=True)
class FakeDeviceClient:
    """Record requested actions without network or hardware access."""

    firmware_version: str = "fake-1.0"
    device_name: str = "Demo BUSY Bar"
    battery_percent: int = 84
    power_state: str = "charging"
    api_version: str = "fake-25.0.0"
    uptime: str = "00d 02h 14m 00s"
    log_content: str = "[demo] BUSY Bar diagnostic log\n[demo] No physical device was contacted.\n"
    scenes: list[DisplayScene] = field(default_factory=list)
    log_capture_count: int = 0
    closed: bool = False

    def snapshot(self) -> DeviceSnapshot:
        self._ensure_open()
        return DeviceSnapshot(
            connected=True,
            firmware_version=self.firmware_version,
            device_name=self.device_name,
            battery_percent=self.battery_percent,
            power_state=self.power_state,
            api_version=self.api_version,
            uptime=self.uptime,
        )

    def show_scene(self, scene: DisplayScene) -> None:
        self._ensure_open()
        self.scenes.append(scene)

    def capture_logs(self) -> DeviceLog:
        self._ensure_open()
        self.log_capture_count += 1
        payload = self.log_content.encode("utf-8")
        return DeviceLog(
            path="/ext/log.txt",
            content=self.log_content,
            size_bytes=len(payload),
        )

    def close(self) -> None:
        self.closed = True

    def _ensure_open(self) -> None:
        if self.closed:
            raise RuntimeError("client is closed")
