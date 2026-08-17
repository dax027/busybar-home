import pytest

from busybar_home.clients.fake import FakeDeviceClient
from busybar_home.dashboard import DashboardController


def test_controller_activates_scene_and_tracks_selection() -> None:
    client = FakeDeviceClient()
    controller = DashboardController(client)

    state, snapshot = controller.activate("focus")

    assert state["active_preset"] == "focus"
    assert snapshot.connected is True
    assert client.scenes[-1].front.text == "BUSY"
    assert client.scenes[-1].back.text == "DEEP FOCUS"
    assert client.scenes[-1].rear_cue == "One task. No inbox."


def test_focus_scene_exposes_busy_checklist_animation() -> None:
    controller = DashboardController(FakeDeviceClient())

    state, _snapshot = controller.activate("focus")
    focus = next(preset for preset in state["presets"] if preset["id"] == "focus")

    assert focus["front"]["text"] == "BUSY"
    assert focus["front_animated"] is True
    assert focus["front_preview"] == "/static/animations/busy_checklist_v2_72x16.webp"


def test_controller_toggles_dynamic_updates_without_device_command() -> None:
    client = FakeDeviceClient()
    controller = DashboardController(client)

    state = controller.set_dynamic(True)

    assert state["dynamic_enabled"] is True
    assert client.scenes == []


def test_controller_rejects_unknown_scene() -> None:
    controller = DashboardController(FakeDeviceClient())

    with pytest.raises(KeyError):
        controller.activate("unknown")


def test_coding_scene_exposes_terminal_style_and_personal_cue() -> None:
    controller = DashboardController(FakeDeviceClient())

    state, _snapshot = controller.activate("coding")
    coding = next(preset for preset in state["presets"] if preset["id"] == "coding")

    assert coding["front"]["text"] == "CODING"
    assert coding["front_style"] == "terminal"
    assert coding["front_animated"] is True
    assert coding["front_preview"] == "/static/animations/coding_72x16.webp"
    assert coding["rear_cue"] == "Write. Run. Refine."


def test_meeting_scene_exposes_live_microphone_animation() -> None:
    controller = DashboardController(FakeDeviceClient())

    state, _snapshot = controller.activate("meeting")
    meeting = next(preset for preset in state["presets"] if preset["id"] == "meeting")

    assert meeting["front"]["text"] == "ON A CALL"
    assert meeting["front_animated"] is True
    assert meeting["front_preview"] == "/static/animations/on_a_call_mic_72x16.webp"


def test_away_scene_exposes_brb_clock_animation() -> None:
    controller = DashboardController(FakeDeviceClient())

    state, _snapshot = controller.activate("away")
    away = next(preset for preset in state["presets"] if preset["id"] == "away")

    assert away["front"]["text"] == "BRB"
    assert away["front_animated"] is True
    assert away["front_preview"] == "/static/animations/away_brb_clock_72x16.webp"
    assert away["back"]["text"] == "SHORT BREAK"
    assert away["rear_cue"] == "Pause. Reset. Return."


def test_available_scene_exposes_neon_animation() -> None:
    controller = DashboardController(FakeDeviceClient())

    state, _snapshot = controller.activate("available")
    available = next(preset for preset in state["presets"] if preset["id"] == "available")

    assert available["front"]["text"] == "FREE"
    assert available["front_animated"] is True
    assert available["front_preview"] == "/static/animations/available_neon_72x16.webp"


def test_wife_scene_exposes_heartbeat_inversion_animation() -> None:
    controller = DashboardController(FakeDeviceClient())

    state, _snapshot = controller.activate("wife")
    wife = next(preset for preset in state["presets"] if preset["id"] == "wife")

    assert wife["front"]["text"] == "I ♥ MY WIFE"
    assert wife["front_animated"] is True
    assert wife["front_preview"] == "/static/animations/love_my_wife_72x16.webp"
    assert wife["back"]["text"] == "LUCKY HUSBAND"
    assert wife["rear_cue"] == "Tell her. Show her."


def test_hacking_scene_exposes_cyberpunk_style_and_personal_cue() -> None:
    controller = DashboardController(FakeDeviceClient())

    state, _snapshot = controller.activate("hacking")
    hacking = next(preset for preset in state["presets"] if preset["id"] == "hacking")

    assert hacking["front"]["text"] == "HACKING"
    assert hacking["front_style"] == "cyberpunk"
    assert hacking["front_animated"] is True
    assert hacking["front_preview"] == "/static/animations/hacking_fawkes_72x16.webp"
    assert hacking["rear_cue"] == "Map. Probe. Learn."


def test_low_social_battery_scene_exposes_battery_style_and_private_cue() -> None:
    controller = DashboardController(FakeDeviceClient())

    state, _snapshot = controller.activate("low-social-battery")
    preset = next(item for item in state["presets"] if item["id"] == "low-social-battery")

    assert preset["front"]["text"] == "LOW SOCIAL"
    assert preset["front_style"] == "low_battery"
    assert preset["front_animated"] is True
    assert preset["front_preview"] == ("/static/animations/low_social_battery_72x16.webp")
    assert preset["back"]["text"] == "SOCIAL BATTERY"
    assert preset["rear_cue"] == "Quiet mode. Recharge."


def test_daydreaming_scene_exposes_sky_style_and_personal_cue() -> None:
    controller = DashboardController(FakeDeviceClient())

    state, _snapshot = controller.activate("daydreaming")
    preset = next(item for item in state["presets"] if item["id"] == "daydreaming")

    assert preset["front"]["text"] == "DAYDREAMING"
    assert preset["front"]["color"] == "#69C6FF"
    assert preset["front_style"] == "daydream"
    assert preset["front_animated"] is True
    assert preset["front_preview"] == "/static/animations/daydreaming_72x16.webp"
    assert preset["back"]["text"] == "WANDER MODE"
    assert preset["rear_cue"] == "Let ideas drift."
