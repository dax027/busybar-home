import pytest

from busybar_home.clients.fake import FakeDeviceClient
from busybar_home.models import DisplayAnimation, DisplayMessage, DisplayScene
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
    assert snapshot.device_name == "Demo BUSY Bar"
    assert snapshot.battery_percent == 84
    assert snapshot.power_state == "charging"
    assert client.scenes == [scene]
    assert client.scenes[0].front == DisplayMessage("FOCUS", "#FF5C35")


def test_fake_client_rejects_actions_after_close() -> None:
    client = FakeDeviceClient()
    client.close()

    with pytest.raises(RuntimeError, match="closed"):
        client.snapshot()


def test_fake_client_captures_deterministic_device_log() -> None:
    client = FakeDeviceClient(log_content="fake diagnostic\n")

    log = client.capture_logs()

    assert log.path == "/ext/log.txt"
    assert log.content == "fake diagnostic\n"
    assert log.size_bytes == 16
    assert log.truncated is False
    assert client.log_capture_count == 1


def test_display_animation_rejects_unsafe_or_non_native_paths() -> None:
    with pytest.raises(ValueError, match="relative"):
        DisplayAnimation("../coding_72x16.anim")
    with pytest.raises(ValueError, match="relative"):
        DisplayAnimation(r"animations\coding_72x16.anim")
    with pytest.raises(ValueError, match=r"\.anim"):
        DisplayAnimation("coding.gif")
