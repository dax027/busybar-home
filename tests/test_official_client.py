from types import SimpleNamespace
from typing import Any

from busybar_home.clients.official import MAX_LOG_BYTES, OfficialBusyBarClient
from busybar_home.models import DisplayScene


class RecordingSdkClient:
    def __init__(self) -> None:
        self.draw_calls: list[Any] = []
        self.clear_before_draw: list[bool] = []

    def display_draw(self, payload: Any, *, clear_before_draw: bool = False) -> None:
        self.draw_calls.append(payload)
        self.clear_before_draw.append(clear_before_draw)


class RecordingStatusSdkClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def name(self) -> SimpleNamespace:
        self.calls.append("name")
        return SimpleNamespace(name="Office BUSY Bar")

    def status_power(self) -> SimpleNamespace:
        self.calls.append("status_power")
        return SimpleNamespace(battery_charge=73, state="charging")

    def status_firmware(self) -> SimpleNamespace:
        self.calls.append("status_firmware")
        return SimpleNamespace(version="1.2.3")

    def status_system(self) -> SimpleNamespace:
        self.calls.append("status_system")
        return SimpleNamespace(api_semver="25.0.0", uptime="01d 02h 03m 04s")


class RecordingLogSdkClient:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.calls: list[tuple[str, str | None]] = []

    def log_dump(self) -> SimpleNamespace:
        self.calls.append(("log_dump", None))
        return SimpleNamespace(path="/ext/log.txt")

    def storage_read(self, path: str) -> bytes:
        self.calls.append(("storage_read", path))
        return self.payload


def test_official_adapter_reads_bounded_device_status_fields() -> None:
    sdk_client = RecordingStatusSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client

    snapshot = client.snapshot()

    assert snapshot.connected is True
    assert snapshot.device_name == "Office BUSY Bar"
    assert snapshot.battery_percent == 73
    assert snapshot.power_state == "charging"
    assert snapshot.firmware_version == "1.2.3"
    assert snapshot.api_version == "25.0.0"
    assert snapshot.uptime == "01d 02h 03m 04s"
    assert sdk_client.calls == [
        "name",
        "status_power",
        "status_firmware",
        "status_system",
    ]


def test_official_adapter_captures_default_device_log_with_size_limit() -> None:
    payload = b"old-prefix" + (b"x" * MAX_LOG_BYTES)
    sdk_client = RecordingLogSdkClient(payload)
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client

    log = client.capture_logs()

    assert log.path == "/ext/log.txt"
    assert log.size_bytes == len(payload)
    assert log.truncated is True
    assert log.content == "x" * MAX_LOG_BYTES
    assert sdk_client.calls == [
        ("log_dump", None),
        ("storage_read", "/ext/log.txt"),
    ]


def test_official_adapter_draws_both_displays_at_work_session_priority() -> None:
    sdk_client = RecordingSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client
    client._display_priority = 100
    scene = DisplayScene.from_text(
        "Focus",
        "FOCUS",
        "DEEP FOCUS",
        "#FF5C35",
        "One task. No inbox.",
    )

    client.show_scene(scene)

    payload = sdk_client.draw_calls[0]
    assert payload.application_name == "busybar-home"
    assert payload.priority == 100
    assert sdk_client.clear_before_draw == [True]
    elements = {element.id: element for element in payload.elements}
    assert elements["status-background"].fill_colors == ["#FF5C35FF"]
    assert elements["status"].text == "FOCUS"
    assert elements["status"].font == "bold"
    assert elements["status"].color == "#000000FF"
    assert (elements["status"].x, elements["status"].y) == (36, 8)
    assert elements["status"].align == "center"
    outline = [elements[f"status-outline-{index}"] for index in range(8)]
    assert all(element.color == "#FFFFFFFF" for element in outline)
    assert all(element.font == "bold" for element in outline)
    assert elements["status-back"].text == "DEEP FOCUS"
    assert elements["rear-cue"].text == "One task. No inbox."


def test_official_adapter_renders_stock_terminal_animation() -> None:
    from busybar_home.models import DisplayAnimation, FrontStyle

    sdk_client = RecordingSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client
    client._display_priority = 100
    scene = DisplayScene.from_text(
        "Coding",
        "CODING",
        "BUILD MODE",
        "#42FF88",
        "Write. Run. Refine.",
        FrontStyle.TERMINAL,
        DisplayAnimation("coding_72x16.anim"),
    )

    client.show_scene(scene)

    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    animation = elements["status-animation"]
    assert animation.stock_path == "animations/coding_72x16.anim"
    assert animation.section == "default"
    assert animation.loop is True
    assert animation.display == "front"
    assert "status-background" not in elements


def test_official_adapter_renders_cyberpunk_scene_with_glitch_layers() -> None:
    from busybar_home.models import FrontStyle

    sdk_client = RecordingSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client
    client._display_priority = 100
    scene = DisplayScene.from_text(
        "Hacking",
        "HACKING",
        "CYBER OPS",
        "#FF2DB2",
        "Map. Probe. Learn.",
        FrontStyle.CYBERPUNK,
    )

    client.show_scene(scene)

    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    assert elements["status-background"].fill_colors == ["#000000FF"]
    assert elements["status"].text == "HACKING"
    assert elements["status-shadow-cyan"].color == "#23D9FFFF"
    assert elements["status-shadow-magenta"].color == "#FF2DB2FF"
    assert elements["glitch-cyan"].fill_colors == ["#23D9FFFF"]
    assert elements["glitch-magenta"].fill_colors == ["#FF2DB2FF"]


def test_official_adapter_renders_stock_low_social_battery_animation() -> None:
    from busybar_home.models import DisplayAnimation, FrontStyle

    sdk_client = RecordingSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client
    client._display_priority = 100
    scene = DisplayScene.from_text(
        "Low social battery",
        "LOW SOCIAL",
        "SOCIAL BATTERY",
        "#FF4D4D",
        "Quiet mode. Recharge.",
        FrontStyle.LOW_BATTERY,
        DisplayAnimation("low_social_battery_72x16.anim"),
    )

    client.show_scene(scene)

    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    animation = elements["status-animation"]
    assert animation.stock_path == "animations/low_social_battery_72x16.anim"
    assert animation.section == "default"
    assert animation.loop is True
    assert animation.display == "front"


def test_official_adapter_renders_daydreaming_sky_and_clouds() -> None:
    from busybar_home.models import FrontStyle

    sdk_client = RecordingSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client
    client._display_priority = 100
    scene = DisplayScene.from_text(
        "Daydreaming",
        "DAYDREAMING",
        "WANDER MODE",
        "#69C6FF",
        "Let ideas drift.",
        FrontStyle.DAYDREAM,
    )

    client.show_scene(scene)

    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    assert elements["status-background"].fill_colors == ["#69C6FFFF"]
    assert elements["status"].text == "DAYDREAMING"
    assert elements["status"].font == "normal"
    assert elements["status"].color == "#183B63FF"
    cloud_ids = [element_id for element_id in elements if element_id.startswith("cloud-")]
    assert len(cloud_ids) == 6
    assert all(elements[element_id].fill_colors == ["#FFFFFFFF"] for element_id in cloud_ids)
