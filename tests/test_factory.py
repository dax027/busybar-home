import pytest

from busybar_home.clients.fake import FakeDeviceClient
from busybar_home.config import ClientKind, Settings
from busybar_home.factory import HardwareAccessDisabledError, create_client


def test_factory_builds_fake_by_default() -> None:
    assert isinstance(create_client(Settings()), FakeDeviceClient)


def test_factory_refuses_official_client_without_safety_flag() -> None:
    settings = Settings(client_kind=ClientKind.OFFICIAL, allow_hardware=False)

    with pytest.raises(HardwareAccessDisabledError, match="BUSYBAR_ALLOW_HARDWARE"):
        create_client(settings)
