from typing import Any

from busybar_home.clients.official import OfficialBusyBarClient
from busybar_home.models import DisplayScene


class RecordingSdkClient:
    def __init__(self) -> None:
        self.draw_calls: list[Any] = []
        self.clear_before_draw: list[bool] = []

    def display_draw(self, payload: Any, *, clear_before_draw: bool = False) -> None:
        self.draw_calls.append(payload)
        self.clear_before_draw.append(clear_before_draw)


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


def test_official_adapter_renders_terminal_scene_with_static_cursor() -> None:
    from busybar_home.models import FrontStyle

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
    )

    client.show_scene(scene)

    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    assert elements["status-background"].fill_colors == ["#000000FF"]
    assert elements["status"].text == "> CODING_"
    assert elements["status"].color == "#42FF88FF"
    assert not any(element_id.startswith("status-outline") for element_id in elements)


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


def test_official_adapter_renders_low_social_battery_glyph() -> None:
    from busybar_home.models import FrontStyle

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
    )

    client.show_scene(scene)

    elements = {element.id: element for element in sdk_client.draw_calls[0].elements}
    assert elements["status-background"].fill_colors == ["#000000FF"]
    assert elements["battery-outline"].border_color == "#FFFFFFFF"
    assert elements["battery-level"].fill_colors == ["#FF4D4DFF"]
    assert elements["battery-cap"].fill_colors == ["#FFFFFFFF"]
    assert elements["status"].text == "LOW SOCIAL"
    assert elements["status"].font == "tiny"
    assert elements["status"].align == "mid_left"
    assert (elements["status"].x, elements["status"].y) == (24, 6)
    assert elements["status-battery"].text == "BATTERY"
    assert elements["status-battery"].color == "#FFFFFFFF"
    assert (elements["status-battery"].x, elements["status-battery"].y) == (24, 12)
