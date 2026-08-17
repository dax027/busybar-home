"""Application-owned models independent of the BUSY Bar SDK."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class FrontStyle(StrEnum):
    STATUS = "status"
    TERMINAL = "terminal"
    CYBERPUNK = "cyberpunk"
    LOW_BATTERY = "low_battery"
    DAYDREAM = "daydream"


@dataclass(frozen=True, slots=True)
class DisplayMessage:
    """Text and color for one BUSY Bar display."""

    text: str
    color: str = "#FFFFFF"

    def __post_init__(self) -> None:
        normalized = self.text.strip()
        if not normalized:
            raise ValueError("display text must not be empty")
        color = self.color.strip().upper()
        if len(color) != 7 or not color.startswith("#"):
            raise ValueError("display color must use #RRGGBB format")
        try:
            int(color[1:], 16)
        except ValueError as error:
            raise ValueError("display color must use #RRGGBB format") from error
        object.__setattr__(self, "text", normalized)
        object.__setattr__(self, "color", color)


@dataclass(frozen=True, slots=True)
class DisplayAnimation:
    """Device-native animation selected independently of the official SDK."""

    path: str
    stock: bool = True
    section: str = "default"
    loop: bool = True

    def __post_init__(self) -> None:
        path = self.path.strip()
        section = self.section.strip()
        if not path or not path.lower().endswith(".anim"):
            raise ValueError("animation path must name an .anim file")
        path_parts = path.split("/")
        if (
            path.startswith("/")
            or "\\" in path
            or any(part in {"", ".", ".."} for part in path_parts)
        ):
            raise ValueError("animation path must be relative and must not traverse directories")
        if not section:
            raise ValueError("animation section must not be empty")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "section", section)


@dataclass(frozen=True, slots=True)
class DisplayScene:
    """Content shown together on the front and rear displays."""

    name: str
    front: DisplayMessage
    back: DisplayMessage
    rear_cue: str = "Stay intentional."
    front_style: FrontStyle = FrontStyle.STATUS
    front_animation: DisplayAnimation | None = None

    def __post_init__(self) -> None:
        normalized = self.name.strip()
        if not normalized:
            raise ValueError("scene name must not be empty")
        cue = self.rear_cue.strip()
        if not cue:
            raise ValueError("rear cue must not be empty")
        object.__setattr__(self, "name", normalized)
        object.__setattr__(self, "rear_cue", cue)

    @classmethod
    def from_text(
        cls,
        name: str,
        front_text: str,
        back_text: str,
        color: str,
        rear_cue: str = "Stay intentional.",
        front_style: FrontStyle = FrontStyle.STATUS,
        front_animation: DisplayAnimation | None = None,
    ) -> Self:
        """Build a two-display scene with one shared accent color."""
        return cls(
            name=name,
            front=DisplayMessage(front_text, color),
            back=DisplayMessage(back_text, color),
            rear_cue=rear_cue,
            front_style=front_style,
            front_animation=front_animation,
        )


@dataclass(frozen=True, slots=True)
class DeviceSnapshot:
    """Small, stable status model returned by every client implementation."""

    connected: bool
    firmware_version: str | None = None
    device_name: str | None = None
    battery_percent: int | None = None
    power_state: str | None = None
    api_version: str | None = None
    uptime: str | None = None


@dataclass(frozen=True, slots=True)
class DeviceLog:
    """One bounded diagnostic log captured from device storage."""

    path: str
    content: str
    size_bytes: int
    truncated: bool = False
