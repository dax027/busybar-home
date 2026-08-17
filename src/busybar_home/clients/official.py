"""Narrow adapter around the official ``busylib`` package.

Importing this module is safe. Constructing the adapter creates the SDK client,
and calling its methods may communicate with a physical BUSY Bar.
"""

from pathlib import Path
from typing import Any

from busybar_home.client import DisplayOwnershipError
from busybar_home.models import DeviceLog, DeviceSnapshot, DisplayScene, FrontStyle

MAX_LOG_BYTES = 512 * 1024
ANIMATION_ASSET_DIR = Path(__file__).resolve().parents[1] / "assets"


class OfficialBusyBarClient:
    """Adapt the official SDK to the application-owned client interface."""

    def __init__(
        self,
        address: str,
        *,
        token: str | None = None,
        display_priority: int = 100,
    ) -> None:
        from busylib import BusyBar

        self._client: Any = BusyBar(address, token=token)
        self._display_priority = display_priority
        self._uploaded_assets: set[str] = set()

    def snapshot(self) -> DeviceSnapshot:
        name = self._client.name()
        power = self._client.status_power()
        firmware = self._client.status_firmware()
        system = self._client.status_system()
        return DeviceSnapshot(
            connected=True,
            firmware_version=firmware.version,
            device_name=name.name,
            battery_percent=power.battery_charge,
            power_state=str(power.state) if power.state is not None else None,
            api_version=system.api_semver,
            uptime=system.uptime,
        )

    def capture_logs(self) -> DeviceLog:
        dump = self._client.log_dump()
        path = dump.path or "/ext/log.txt"
        payload = self._client.storage_read(path)
        size_bytes = len(payload)
        truncated = size_bytes > MAX_LOG_BYTES
        visible_payload = payload[-MAX_LOG_BYTES:] if truncated else payload
        return DeviceLog(
            path=path,
            content=visible_payload.decode("utf-8", errors="replace"),
            size_bytes=size_bytes,
            truncated=truncated,
        )

    def show_scene(self, scene: DisplayScene) -> None:
        from busylib import exceptions, types

        if scene.front_animation is not None:
            animation = scene.front_animation
            if not animation.stock:
                uploaded_assets = getattr(self, "_uploaded_assets", set())
                if animation.path not in uploaded_assets:
                    payload = (ANIMATION_ASSET_DIR / animation.path).read_bytes()
                    self._client.assets_upload("busybar-home", animation.path, payload)
                    uploaded_assets.add(animation.path)
                    self._uploaded_assets = uploaded_assets
            animation_source = (
                {"stock_path": f"animations/{animation.path}"}
                if animation.stock
                else {"path": animation.path}
            )
            front_elements = [
                types.AnimationElement(
                    id="status-animation",
                    type="animation",
                    x=0,
                    y=0,
                    display=types.DisplayName.FRONT,
                    loop=animation.loop,
                    await_previous_end=False,
                    section=animation.section,
                    opacity=100,
                    **animation_source,
                )
            ]
        elif scene.front_style is FrontStyle.LOW_BATTERY:
            front_elements = [
                types.RectangleElement(
                    id="status-background",
                    type="rectangle",
                    x=0,
                    y=0,
                    width=72,
                    height=16,
                    fill="solid",
                    fill_colors=["#000000"],
                    border_width=0,
                    display=types.DisplayName.FRONT,
                ),
                types.RectangleElement(
                    id="battery-outline",
                    type="rectangle",
                    x=3,
                    y=3,
                    width=16,
                    height=10,
                    fill="none",
                    border_width=1,
                    border_color="#FFFFFF",
                    display=types.DisplayName.FRONT,
                ),
                types.RectangleElement(
                    id="battery-level",
                    type="rectangle",
                    x=5,
                    y=5,
                    width=3,
                    height=6,
                    fill="solid",
                    fill_colors=[scene.front.color],
                    border_width=0,
                    display=types.DisplayName.FRONT,
                ),
                types.RectangleElement(
                    id="battery-cap",
                    type="rectangle",
                    x=19,
                    y=6,
                    width=2,
                    height=4,
                    fill="solid",
                    fill_colors=["#FFFFFF"],
                    border_width=0,
                    display=types.DisplayName.FRONT,
                ),
                types.TextElement(
                    id="status",
                    type="text",
                    x=24,
                    y=6,
                    align="mid_left",
                    text=scene.front.text,
                    font="tiny",
                    color="#FFFFFF",
                    display=types.DisplayName.FRONT,
                ),
                types.TextElement(
                    id="status-battery",
                    type="text",
                    x=24,
                    y=12,
                    align="mid_left",
                    text="BATTERY",
                    font="tiny",
                    color="#FFFFFF",
                    display=types.DisplayName.FRONT,
                ),
            ]
        elif scene.front_style is FrontStyle.DAYDREAM:
            cloud_rectangles = (
                ("cloud-left-base", 1, 11, 16, 3),
                ("cloud-left-rise", 4, 9, 6, 5),
                ("cloud-left-mid", 9, 10, 5, 4),
                ("cloud-right-base", 55, 3, 16, 3),
                ("cloud-right-rise", 61, 1, 6, 5),
                ("cloud-right-mid", 57, 2, 6, 4),
            )
            front_elements = [
                types.RectangleElement(
                    id="status-background",
                    type="rectangle",
                    x=0,
                    y=0,
                    width=72,
                    height=16,
                    fill="solid",
                    fill_colors=[scene.front.color],
                    border_width=0,
                    display=types.DisplayName.FRONT,
                ),
                *[
                    types.RectangleElement(
                        id=element_id,
                        type="rectangle",
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        fill="solid",
                        fill_colors=["#FFFFFF"],
                        border_width=0,
                        display=types.DisplayName.FRONT,
                    )
                    for element_id, x, y, width, height in cloud_rectangles
                ],
                types.TextElement(
                    id="status",
                    type="text",
                    x=36,
                    y=8,
                    align="center",
                    text=scene.front.text,
                    font="normal",
                    color="#183B63",
                    display=types.DisplayName.FRONT,
                ),
            ]
        elif scene.front_style is FrontStyle.TERMINAL:
            front_elements = [
                types.RectangleElement(
                    id="status-background",
                    type="rectangle",
                    x=0,
                    y=0,
                    width=72,
                    height=16,
                    fill="solid",
                    fill_colors=["#000000"],
                    border_width=0,
                    display=types.DisplayName.FRONT,
                ),
                types.TextElement(
                    id="status",
                    type="text",
                    x=36,
                    y=8,
                    align="center",
                    text=f"> {scene.front.text}_",
                    font="bold",
                    color=scene.front.color,
                    display=types.DisplayName.FRONT,
                ),
            ]
        elif scene.front_style is FrontStyle.CYBERPUNK:
            front_elements = [
                types.RectangleElement(
                    id="status-background",
                    type="rectangle",
                    x=0,
                    y=0,
                    width=72,
                    height=16,
                    fill="solid",
                    fill_colors=["#000000"],
                    border_width=0,
                    display=types.DisplayName.FRONT,
                ),
                types.RectangleElement(
                    id="glitch-magenta",
                    type="rectangle",
                    x=0,
                    y=1,
                    width=16,
                    height=1,
                    fill="solid",
                    fill_colors=["#FF2DB2"],
                    border_width=0,
                    display=types.DisplayName.FRONT,
                ),
                types.RectangleElement(
                    id="glitch-cyan",
                    type="rectangle",
                    x=55,
                    y=14,
                    width=17,
                    height=1,
                    fill="solid",
                    fill_colors=["#23D9FF"],
                    border_width=0,
                    display=types.DisplayName.FRONT,
                ),
                types.TextElement(
                    id="status-shadow-cyan",
                    type="text",
                    x=35,
                    y=8,
                    align="center",
                    text=scene.front.text,
                    font="bold",
                    color="#23D9FF",
                    display=types.DisplayName.FRONT,
                ),
                types.TextElement(
                    id="status-shadow-magenta",
                    type="text",
                    x=37,
                    y=8,
                    align="center",
                    text=scene.front.text,
                    font="bold",
                    color="#FF2DB2",
                    display=types.DisplayName.FRONT,
                ),
                types.TextElement(
                    id="status",
                    type="text",
                    x=36,
                    y=8,
                    align="center",
                    text=scene.front.text,
                    font="bold",
                    color="#F6F7FF",
                    display=types.DisplayName.FRONT,
                ),
            ]
        else:
            outline_offsets = (
                (-1, -1),
                (0, -1),
                (1, -1),
                (-1, 0),
                (1, 0),
                (-1, 1),
                (0, 1),
                (1, 1),
            )
            outline_elements = [
                types.TextElement(
                    id=f"status-outline-{index}",
                    type="text",
                    x=36 + offset_x,
                    y=8 + offset_y,
                    align="center",
                    text=scene.front.text,
                    font="bold",
                    color="#FFFFFF",
                    display=types.DisplayName.FRONT,
                )
                for index, (offset_x, offset_y) in enumerate(outline_offsets)
            ]
            front_elements = [
                types.RectangleElement(
                    id="status-background",
                    type="rectangle",
                    x=0,
                    y=0,
                    width=72,
                    height=16,
                    fill="solid",
                    fill_colors=[scene.front.color],
                    border_width=0,
                    display=types.DisplayName.FRONT,
                ),
                *outline_elements,
                types.TextElement(
                    id="status",
                    type="text",
                    x=36,
                    y=8,
                    align="center",
                    text=scene.front.text,
                    font="bold",
                    color="#000000",
                    display=types.DisplayName.FRONT,
                ),
            ]

        try:
            self._client.display_draw(
                types.DisplayElements(
                    application_name="busybar-home",
                    priority=self._display_priority,
                    elements=[
                        *front_elements,
                        types.RectangleElement(
                            id="rear-accent",
                            type="rectangle",
                            x=0,
                            y=0,
                            width=4,
                            height=80,
                            fill="solid",
                            fill_colors=[scene.back.color],
                            border_width=0,
                            display=types.DisplayName.BACK,
                        ),
                        types.TextElement(
                            id="status-back",
                            type="text",
                            x=12,
                            y=18,
                            align="mid_left",
                            text=scene.back.text,
                            font="normal",
                            color="#FFFFFF",
                            display=types.DisplayName.BACK,
                        ),
                        types.TextElement(
                            id="rear-cue",
                            type="text",
                            x=12,
                            y=48,
                            align="mid_left",
                            text=scene.rear_cue,
                            font="small",
                            color="#B8B8B8",
                            display=types.DisplayName.BACK,
                        ),
                        types.RectangleElement(
                            id="rear-rule",
                            type="rectangle",
                            x=12,
                            y=68,
                            width=136,
                            height=1,
                            fill="solid",
                            fill_colors=["#555555"],
                            border_width=0,
                            display=types.DisplayName.BACK,
                        ),
                        types.TextElement(
                            id="rear-signature",
                            type="text",
                            x=12,
                            y=75,
                            align="mid_left",
                            text="BUSY / HOME",
                            font="tiny",
                            color="#777777",
                            display=types.DisplayName.BACK,
                        ),
                    ],
                ),
                clear_before_draw=True,
            )
        except exceptions.BusyBarAPIError as error:
            if error.code == 409 and "low priority" in str(error).lower():
                raise DisplayOwnershipError(
                    "Another BUSY application currently owns the display"
                ) from error
            raise

    def close(self) -> None:
        self._client.close()
