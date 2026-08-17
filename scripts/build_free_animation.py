"""Generate the device and browser assets for the Free neon-sign scene."""

from __future__ import annotations

from pathlib import Path

from animation_assets import write_anim, write_webp
from PIL import Image, ImageDraw

WIDTH = 72
HEIGHT = 16
FPS = 12
FRAME_COUNT = 96

BACKGROUND = (2, 7, 8)
NEON_CORE = (191, 255, 219)
NEON_TUBE = (71, 209, 140)
NEON_GLOW = (10, 91, 55)
NEON_FAINT = (5, 35, 25)

GLYPHS = {
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
}

STARTUP_LEVELS = (0.08, 0.15, 0.75, 0.12, 0.9, 0.2, 1.0, 0.42, 1.0, 0.7, 1.0, 1.0)


def dim(color: tuple[int, int, int], level: float) -> tuple[int, int, int]:
    return tuple(round(channel * level) for channel in color)


def letter_levels(frame_index: int) -> tuple[float, float, float, float]:
    if frame_index < len(STARTUP_LEVELS):
        level = STARTUP_LEVELS[frame_index]
        return (level, level, level, level)
    if frame_index >= 84:
        level = max(0.08, 1 - ((frame_index - 84) / 11))
        return (level, level, level, level)

    levels = [1.0, 1.0, 1.0, 1.0]
    if frame_index in {31, 32}:
        levels[1] = 0.22
    if frame_index == 49:
        levels = [0.45, 0.45, 0.45, 0.45]
    if frame_index in {67, 68}:
        levels[3] = 0.28
    return tuple(levels)


def draw_border(draw: ImageDraw.ImageDraw, level: float) -> None:
    glow = dim(NEON_GLOW, level)
    tube = dim(NEON_TUBE, level)
    draw.rectangle((1, 0, 70, 15), outline=glow)
    draw.line((3, 0, 68, 0), fill=tube)
    draw.line((3, 15, 68, 15), fill=tube)
    draw.point((1, 2), fill=tube)
    draw.point((1, 13), fill=tube)
    draw.point((70, 2), fill=tube)
    draw.point((70, 13), fill=tube)


def draw_letter(
    draw: ImageDraw.ImageDraw,
    character: str,
    x: int,
    y: int,
    level: float,
) -> None:
    glyph = GLYPHS[character]
    glow = dim(NEON_GLOW, level)
    tube = dim(NEON_TUBE, level)
    core = dim(NEON_CORE, level)
    for row, bits in enumerate(glyph):
        for column, bit in enumerate(bits):
            if bit != "1":
                continue
            left = x + column * 2
            top = y + row * 2
            draw.rectangle((left - 1, top, left + 2, top + 1), fill=glow)
            draw.rectangle((left, top, left + 1, top + 1), fill=tube)
            if level > 0.6:
                draw.point((left, top), fill=core)


def render_frames() -> list[Image.Image]:
    """Render an eight-second neon ignition and glow loop."""
    frames: list[Image.Image] = []
    for index in range(FRAME_COUNT):
        frame = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
        draw = ImageDraw.Draw(frame)
        levels = letter_levels(index)
        border_level = max(0.12, sum(levels) / len(levels) * 0.75)
        draw_border(draw, border_level)

        cursor = 13
        for character, level in zip("FREE", levels, strict=True):
            draw_letter(draw, character, cursor, 1, level)
            cursor += 12

        if max(levels) < 0.2:
            draw.line((13, 14, 58, 14), fill=NEON_FAINT)
        frames.append(frame)
    return frames


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frames = render_frames()
    try:
        write_anim(
            frames,
            root / "src/busybar_home/assets/available_neon_72x16.anim",
            fps=FPS,
        )
        write_webp(
            frames,
            root / "src/busybar_home/static/animations/available_neon_72x16.webp",
            fps=FPS,
        )
    finally:
        for frame in frames:
            frame.close()


if __name__ == "__main__":
    main()
