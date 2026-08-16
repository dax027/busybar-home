"""Client construction with a hard safety gate for real hardware."""

from busybar_home.client import DeviceClient
from busybar_home.clients.fake import FakeDeviceClient
from busybar_home.config import ClientKind, Settings


class HardwareAccessDisabledError(RuntimeError):
    """Raised when real-device access has not been explicitly enabled."""


def create_client(settings: Settings) -> DeviceClient:
    """Create the configured client without silently selecting real hardware."""
    if settings.client_kind is ClientKind.FAKE:
        return FakeDeviceClient()
    if not settings.allow_hardware:
        raise HardwareAccessDisabledError(
            "official client requested, but BUSYBAR_ALLOW_HARDWARE is not true"
        )

    # Keep this lazy so fake-only development and tests never initialize the SDK.
    from busybar_home.clients.official import OfficialBusyBarClient

    return OfficialBusyBarClient(
        settings.device_address,
        token=settings.access_token,
        display_priority=settings.display_priority,
    )
