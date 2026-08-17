import base64
from types import SimpleNamespace
from typing import Any

from busybar_home.clients.official import (
    MAX_LOG_BYTES,
    OfficialBusyBarClient,
    _decode_stream_frame,
)
from busybar_home.models import DisplayScene


class RecordingSdkClient:
    def __init__(self) -> None:
        self.draw_calls: list[Any] = []
        self.clear_before_draw: list[bool] = []
        self.upload_calls: list[tuple[str, str, bytes]] = []
        self.clear_calls = 0

    def display_clear(self) -> None:
        self.clear_calls += 1

    def assets_upload(self, application_name: str, path: str, payload: bytes) -> None:
        self.upload_calls.append((application_name, path, payload))

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


class RecordingScreenSdkClient:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def screen(self, display: str) -> bytes:
        self.calls.append(display)
        return bytes((12, 34, 210)) * (72 * 16)


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


def test_official_adapter_reads_front_screen_and_converts_bgr_to_rgb() -> None:
    sdk_client = RecordingScreenSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client

    frame = client.front_screen_frame()

    assert (frame.width, frame.height) == (72, 16)
    assert frame.rgb[:6] == bytes((210, 34, 12, 210, 34, 12))
    assert len(frame.rgb) == 72 * 16 * 3
    assert sdk_client.calls == ["front"]


def test_official_adapter_decodes_stream_frame_and_converts_bgr_to_rgb() -> None:
    raw_bgr = bytes((12, 34, 210)) * (72 * 16)

    frame = _decode_stream_frame(
        {
            "width": 72,
            "height": 16,
            "encoding": "PLAIN",
            "pixel_format": "RGB888",
            "data": base64.b64encode(raw_bgr).decode("ascii"),
        }
    )

    assert frame is not None
    assert (frame.width, frame.height) == (72, 16)
    assert frame.rgb[:6] == bytes((210, 34, 12, 210, 34, 12))


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


def test_official_adapter_releases_and_replaces_in_memory_animation() -> None:
    from busybar_home.models import DisplayAnimation, FrontStyle

    sdk_client = RecordingSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client
    client._display_priority = 100
    first = DisplayScene.from_text(
        "Custom ticker",
        "FIRST",
        "CUSTOM TICKER",
        "#FFFFFF",
        "Your message is live.",
        FrontStyle.STATUS,
        DisplayAnimation("custom_ticker.anim", stock=False, payload=b"bicycle0-first"),
    )
    second = DisplayScene.from_text(
        "Custom ticker",
        "SECOND",
        "CUSTOM TICKER",
        "#FFFFFF",
        "Your message is live.",
        FrontStyle.STATUS,
        DisplayAnimation("custom_ticker.anim", stock=False, payload=b"bicycle0-second"),
    )

    client.show_scene(first)
    client.show_scene(first)
    client.show_scene(second)

    assert sdk_client.clear_calls == 2
    assert [call[2] for call in sdk_client.upload_calls] == [
        b"bicycle0-first",
        b"bicycle0-second",
    ]
    assert len(sdk_client.draw_calls) == 3


def test_official_adapter_uploads_and_renders_busy_checklist_animation() -> None:
    from busybar_home.models import DisplayAnimation, FrontStyle

    sdk_client = RecordingSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client
    client._display_priority = 100
    scene = DisplayScene.from_text(
        "Deep focus",
        "BUSY",
        "DEEP FOCUS",
        "#FF5C35",
        "One task. No inbox.",
        FrontStyle.STATUS,
        DisplayAnimation("busy_checklist_v2_72x16.anim", stock=False),
    )

    client.show_scene(scene)

    assert len(sdk_client.upload_calls) == 1
    application_name, path, payload = sdk_client.upload_calls[0]
    assert application_name == "busybar-home"
    assert path == "busy_checklist_v2_72x16.anim"
    assert payload.startswith(b"bicycle0")
    assert sdk_client.clear_calls == 1
    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    animation = elements["status-animation"]
    assert animation.path == "busy_checklist_v2_72x16.anim"
    assert animation.loop is True


def test_official_adapter_uploads_and_renders_call_animation() -> None:
    from busybar_home.models import DisplayAnimation, FrontStyle

    sdk_client = RecordingSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client
    client._display_priority = 100
    scene = DisplayScene.from_text(
        "In a meeting",
        "ON A CALL",
        "MEETING MODE",
        "#EF3D77",
        "Capture decisions.",
        FrontStyle.STATUS,
        DisplayAnimation("on_a_call_mic_72x16.anim", stock=False),
    )

    client.show_scene(scene)

    assert len(sdk_client.upload_calls) == 1
    assert sdk_client.clear_calls == 1
    application_name, path, payload = sdk_client.upload_calls[0]
    assert application_name == "busybar-home"
    assert path == "on_a_call_mic_72x16.anim"
    assert payload.startswith(b"bicycle0")
    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    animation = elements["status-animation"]
    assert animation.path == "on_a_call_mic_72x16.anim"
    assert animation.loop is True


def test_official_adapter_uploads_and_renders_away_brb_clock_animation() -> None:
    from busybar_home.models import DisplayAnimation, FrontStyle

    sdk_client = RecordingSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client
    client._display_priority = 100
    scene = DisplayScene.from_text(
        "Stepped away",
        "BRB",
        "SHORT BREAK",
        "#FFBF47",
        "Pause. Reset. Return.",
        FrontStyle.STATUS,
        DisplayAnimation("away_brb_clock_72x16.anim", stock=False),
    )

    client.show_scene(scene)

    assert len(sdk_client.upload_calls) == 1
    application_name, path, payload = sdk_client.upload_calls[0]
    assert application_name == "busybar-home"
    assert path == "away_brb_clock_72x16.anim"
    assert payload.startswith(b"bicycle0")
    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    animation = elements["status-animation"]
    assert animation.path == "away_brb_clock_72x16.anim"
    assert animation.loop is True


def test_official_adapter_uploads_and_renders_available_neon_animation() -> None:
    from busybar_home.models import DisplayAnimation, FrontStyle

    sdk_client = RecordingSdkClient()
    client = OfficialBusyBarClient.__new__(OfficialBusyBarClient)
    client._client = sdk_client
    client._display_priority = 100
    scene = DisplayScene.from_text(
        "Available",
        "FREE",
        "RESET WINDOW",
        "#47D18C",
        "Clear quick replies.",
        FrontStyle.STATUS,
        DisplayAnimation("available_neon_72x16.anim", stock=False),
    )

    client.show_scene(scene)

    assert len(sdk_client.upload_calls) == 1
    application_name, path, payload = sdk_client.upload_calls[0]
    assert application_name == "busybar-home"
    assert path == "available_neon_72x16.anim"
    assert payload.startswith(b"bicycle0")
    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    animation = elements["status-animation"]
    assert animation.path == "available_neon_72x16.anim"
    assert animation.loop is True


def test_official_adapter_uploads_and_renders_hacking_animation() -> None:
    from busybar_home.models import DisplayAnimation, FrontStyle

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
        DisplayAnimation("hacking_fawkes_72x16.anim", stock=False),
    )

    client.show_scene(scene)

    assert len(sdk_client.upload_calls) == 1
    application_name, path, payload = sdk_client.upload_calls[0]
    assert application_name == "busybar-home"
    assert path == "hacking_fawkes_72x16.anim"
    assert payload.startswith(b"bicycle0")
    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    animation = elements["status-animation"]
    assert animation.path == "hacking_fawkes_72x16.anim"
    assert animation.loop is True


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


def test_official_adapter_uploads_and_renders_daydreaming_animation() -> None:
    from busybar_home.models import DisplayAnimation, FrontStyle

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
        DisplayAnimation("daydreaming_72x16.anim", stock=False),
    )

    client.show_scene(scene)

    assert len(sdk_client.upload_calls) == 1
    application_name, path, payload = sdk_client.upload_calls[0]
    assert application_name == "busybar-home"
    assert path == "daydreaming_72x16.anim"
    assert payload.startswith(b"bicycle0")
    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    animation = elements["status-animation"]
    assert animation.path == "daydreaming_72x16.anim"
    assert animation.loop is True

    client.show_scene(scene)

    assert len(sdk_client.upload_calls) == 1
