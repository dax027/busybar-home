"""Bounded custom ticker rendering shared by preview and device deployment."""

from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass
from enum import StrEnum

from PIL import Image, ImageColor, ImageDraw, ImageFont

from busybar_home.animation import encode_anim, encode_webp
from busybar_home.models import DisplayAnimation, DisplayScene, FrontStyle

WIDTH = 72
HEIGHT = 16
FPS = 12
MIN_SPEED = 16
MAX_SPEED = 72
MAX_MESSAGE_LENGTH = 48
MAX_FRAMES = 360


class TickerEffect(StrEnum):
    """Visual treatments available for ticker text."""

    CLEAN = "clean"
    PULSE = "pulse"
    LETTER_FLASH = "letter_flash"
    COLOR_WAVE = "color_wave"
    INVERT = "invert"


@dataclass(frozen=True, slots=True)
class TickerConfig:
    """Validated user controls for one ticker animation."""

    message: str
    font_color: str = "#FFFFFF"
    background_color: str = "#111111"
    speed: int = 32
    effect: TickerEffect = TickerEffect.CLEAN

    def __post_init__(self) -> None:
        message = " ".join(self.message.split())
        if not message:
            raise ValueError("ticker message must not be empty")
        if len(message) > MAX_MESSAGE_LENGTH:
            raise ValueError(f"ticker message must be {MAX_MESSAGE_LENGTH} characters or fewer")
        if any(ord(character) < 32 or ord(character) > 126 for character in message):
            raise ValueError("ticker message must use printable ASCII characters")
        if not MIN_SPEED <= self.speed <= MAX_SPEED:
            raise ValueError(f"ticker speed must be between {MIN_SPEED} and {MAX_SPEED}")
        font_color = _normalize_color(self.font_color)
        background_color = _normalize_color(self.background_color)
        effect = TickerEffect(self.effect)
        object.__setattr__(self, "message", message)
        object.__setattr__(self, "font_color", font_color)
        object.__setattr__(self, "background_color", background_color)
        object.__setattr__(self, "effect", effect)


@dataclass(frozen=True, slots=True)
class TickerAssets:
    """The paired browser and device encodings for a ticker."""

    animation: bytes
    preview: bytes
    frame_count: int


def build_ticker_assets(config: TickerConfig) -> TickerAssets:
    """Render one configuration to identical device and browser animations."""
    frames = render_ticker_frames(config)
    try:
        return TickerAssets(
            animation=encode_anim(frames, fps=FPS),
            preview=encode_webp(frames, fps=FPS),
            frame_count=len(frames),
        )
    finally:
        for frame in frames:
            frame.close()


def build_ticker_scene(config: TickerConfig) -> DisplayScene:
    """Build a deployable scene with an in-memory custom animation."""
    assets = build_ticker_assets(config)
    return DisplayScene.from_text(
        "Custom ticker",
        config.message,
        "CUSTOM TICKER",
        config.font_color,
        "Your message is live.",
        FrontStyle.STATUS,
        DisplayAnimation("custom_ticker.anim", stock=False, payload=assets.animation),
    )


def render_ticker_frames(config: TickerConfig) -> list[Image.Image]:
    """Render one complete right-to-left ticker loop."""
    font = ImageFont.load_default(size=12)
    text_width = math.ceil(font.getlength(config.message))
    travel = WIDTH + text_width + 10
    frame_count = min(MAX_FRAMES, max(24, math.ceil((travel / config.speed) * FPS)))
    text_y = _text_y(font, config.message)
    base_font = ImageColor.getrgb(config.font_color)
    base_background = ImageColor.getrgb(config.background_color)
    frames: list[Image.Image] = []

    for index in range(frame_count):
        progress = index / max(1, frame_count - 1)
        text_x = WIDTH - round(progress * travel)
        font_color, background_color = _frame_colors(
            config.effect,
            index,
            base_font,
            base_background,
        )
        frame = Image.new("RGB", (WIDTH, HEIGHT), background_color)
        draw = ImageDraw.Draw(frame)
        if config.effect in {TickerEffect.LETTER_FLASH, TickerEffect.COLOR_WAVE}:
            _draw_characters(
                draw,
                config,
                font,
                text_x,
                text_y,
                index,
                font_color,
            )
        else:
            draw.text((text_x, text_y), config.message, font=font, fill=font_color)
        frames.append(frame)
    return frames


def _draw_characters(
    draw: ImageDraw.ImageDraw,
    config: TickerConfig,
    font: ImageFont.ImageFont,
    x: int,
    y: int,
    frame_index: int,
    base_color: tuple[int, int, int],
) -> None:
    cursor = float(x)
    for character_index, character in enumerate(config.message):
        color = base_color
        visible = True
        if config.effect is TickerEffect.LETTER_FLASH:
            visible = (character_index + (frame_index // 3)) % 4 != 0
        elif config.effect is TickerEffect.COLOR_WAVE:
            hue = ((character_index * 0.09) + (frame_index * 0.015)) % 1
            color = tuple(round(channel * 255) for channel in colorsys.hsv_to_rgb(hue, 0.78, 1))
        if visible:
            draw.text((round(cursor), y), character, font=font, fill=color)
        cursor += font.getlength(character)


def _frame_colors(
    effect: TickerEffect,
    frame_index: int,
    font_color: tuple[int, int, int],
    background_color: tuple[int, int, int],
) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    if effect is TickerEffect.INVERT and frame_index % 30 in range(20, 25):
        return background_color, font_color
    if effect is TickerEffect.PULSE:
        level = 0.45 + (0.55 * ((math.sin(frame_index * math.tau / 24) + 1) / 2))
        pulsed = tuple(
            round(background + ((foreground - background) * level))
            for foreground, background in zip(font_color, background_color, strict=True)
        )
        return pulsed, background_color
    return font_color, background_color


def _text_y(font: ImageFont.ImageFont, message: str) -> int:
    left, top, right, bottom = font.getbbox(message)
    del left, right
    return ((HEIGHT - (bottom - top)) // 2) - top


def _normalize_color(value: str) -> str:
    color = value.strip().upper()
    if len(color) != 7 or not color.startswith("#"):
        raise ValueError("ticker colors must use #RRGGBB format")
    try:
        ImageColor.getrgb(color)
    except ValueError as error:
        raise ValueError("ticker colors must use #RRGGBB format") from error
    return color
