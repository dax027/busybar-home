"""Generate the device and browser assets for the Focused scene."""

from __future__ import annotations

import math
from pathlib import Path

from animation_assets import write_anim, write_webp
from PIL import Image, ImageDraw

WIDTH = 72
HEIGHT = 16
FPS = 12
FRAME_COUNT = 96

BACKGROUND = (1, 4, 10)
CYAN = (63, 231, 255)
VIOLET = (139, 92, 246)
WHITE = (244, 252, 255)
BLUE = (31, 97, 160)

GLYPHS = {
    "C": ("11111", "10000", "10000", "10000", "10000", "10000", "11111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("1111", "1000", "1000", "1110", "1000", "1000", "1111"),
    "F": ("1111", "1000", "1000", "1110", "1000", "1000", "1000"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
}

PARTICLES = (
    (2, 2, CYAN),
    (9, 13, VIOLET),
    (15, 4, BLUE),
    (21, 15, CYAN),
    (27, 1, VIOLET),
    (44, 14, BLUE),
    (50, 3, CYAN),
    (57, 12, VIOLET),
    (64, 5, BLUE),
    (70, 14, CYAN),
    (4, 9, VIOLET),
    (67, 1, CYAN),
)


def dim(color: tuple[int, int, int], level: float) -> tuple[int, int, int]:
    """Return a brightness-scaled RGB color."""
    return tuple(round(channel * level) for channel in color)


def smoothstep(value: float) -> float:
    """Ease a normalized value at both ends."""
    return value * value * (3 - 2 * value)


def render_collapse(index: int) -> Image.Image:
    """Pull peripheral distraction pixels into a single center point."""
    frame = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(frame)
    progress = smoothstep(index / 27)
    center_x, center_y = 35.5, 7.5

    for particle_index, (start_x, start_y, color) in enumerate(PARTICLES):
        wobble = math.sin((index + particle_index * 3) * 0.45) * (1 - progress)
        x = round(start_x + (center_x - start_x) * progress)
        y = round(start_y + (center_y - start_y) * progress + wobble)
        draw.point((x, y), fill=dim(color, 0.45 + progress * 0.55))
        if progress < 0.72:
            trail_x = round(start_x + (center_x - start_x) * max(0, progress - 0.08))
            trail_y = round(start_y + (center_y - start_y) * max(0, progress - 0.08))
            draw.point((trail_x, trail_y), fill=dim(color, 0.24))

    # Dim corner marks imply a wide field of attention before it narrows.
    inset = round(progress * 23)
    left = 1 + inset
    right = WIDTH - 2 - inset
    bracket_color = dim(CYAN, 0.28 + progress * 0.5)
    draw.line((left, 1, left + 4, 1), fill=bracket_color)
    draw.line((left, 1, left, 4), fill=bracket_color)
    draw.line((right - 4, 14, right, 14), fill=bracket_color)
    draw.line((right, 11, right, 14), fill=bracket_color)
    return frame


def render_lock(index: int) -> Image.Image:
    """Close a cyan-violet targeting aperture around the focal point."""
    frame = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(frame)
    progress = smoothstep(index / 13)
    half_width = round(31 - progress * 24)
    half_height = round(6 - progress * 3)
    left = 36 - half_width
    right = 35 + half_width
    top = 8 - half_height
    bottom = 7 + half_height

    draw.line((left, top, left + 5, top), fill=CYAN)
    draw.line((left, top, left, top + 3), fill=CYAN)
    draw.line((right - 5, bottom, right, bottom), fill=VIOLET)
    draw.line((right, bottom - 3, right, bottom), fill=VIOLET)
    draw.line((0, 8, left - 2, 8), fill=dim(BLUE, 0.65))
    draw.line((right + 2, 7, WIDTH - 1, 7), fill=dim(BLUE, 0.65))
    draw.point((35, 7), fill=WHITE)
    draw.point((36, 8), fill=WHITE)

    if index >= 11:
        flash = 1.0 if index == 12 else 0.55
        draw.line((31, 7, 40, 7), fill=dim(WHITE, flash))
        draw.line((35, 3, 35, 12), fill=dim(WHITE, flash))
    return frame


def draw_word(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    """Draw a full-width, two-pixel-scale FOCUSED wordmark."""
    pulse = 0.88 + 0.12 * math.sin(frame_index * math.tau / 36)
    cursor = 0
    for letter_index, character in enumerate("FOCUSED"):
        glyph = GLYPHS[character]
        base = CYAN if letter_index < 4 else VIOLET
        color = dim(base, pulse)
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit != "1":
                    continue
                x = cursor + column * 2
                y = 1 + row * 2
                draw.rectangle((x, y, x + 1, y + 1), fill=color)
                if (row * 3 + column + letter_index + frame_index // 9) % 13 == 0:
                    draw.point((x, y), fill=WHITE)
        cursor += len(glyph[0]) * 2 + 1


def render_word(index: int) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw_word(ImageDraw.Draw(frame), index)
    return frame


def render_frames() -> list[Image.Image]:
    """Render an eight-second distraction-to-focus loop."""
    frames: list[Image.Image] = []
    for index in range(FRAME_COUNT):
        if index < 28:
            frame = render_collapse(index)
        elif index < 42:
            frame = render_lock(index - 28)
        elif index < 90:
            frame = render_word(index - 42)
        else:
            word = render_word(index - 42)
            fade = (index - 89) / 7
            frame = Image.blend(word, Image.new("RGB", word.size, BACKGROUND), fade)
            word.close()
        frames.append(frame)
    return frames


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frames = render_frames()
    try:
        write_anim(
            frames,
            root / "src/busybar_home/assets/focused_lock_72x16.anim",
            fps=FPS,
        )
        write_webp(
            frames,
            root / "src/busybar_home/static/animations/focused_lock_72x16.webp",
            fps=FPS,
        )
    finally:
        for frame in frames:
            frame.close()


if __name__ == "__main__":
    main()
