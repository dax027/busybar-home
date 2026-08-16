import pytest

from busybar_home.clients.fake import FakeDeviceClient
from busybar_home.models import DisplayMessage, DisplayScene
from busybar_home.service import BusyBarService


def test_service_records_scene_without_hardware() -> None:
    client = FakeDeviceClient(firmware_version="test-firmware")
    scene = DisplayScene(
        name="Focus",
        front=DisplayMessage("  FOCUS  ", "#ff5c35"),
        back=DisplayMessage("Deep work", "#ff5c35"),
    )

    snapshot = BusyBarService(client).apply_scene(scene)

    assert snapshot.connected is True
    assert snapshot.firmware_version == "test-firmware"
    assert client.scenes == [scene]
    assert client.scenes[0].front == DisplayMessage("FOCUS", "#FF5C35")


def test_fake_client_rejects_actions_after_close() -> None:
    client = FakeDeviceClient()
    client.close()

    with pytest.raises(RuntimeError, match="closed"):
        client.snapshot()
