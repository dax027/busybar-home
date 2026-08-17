"""Generate the device and browser assets for the Daydreaming scene."""

from __future__ import annotations

import math
from pathlib import Path

from animation_assets import write_anim, write_webp
from PIL import Image, ImageDraw

WIDTH = 72
HEIGHT = 16
FPS = 12
FRAME_COUNT = 288

GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "I": ("111", "010", "010", "010", "010", "010", "111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
}

PUFFY_CLOUD = (
    (4, 0, 5, 2),
    (2, 2, 10, 2),
    (0, 4, 15, 3),
)
WISPY_CLOUD = (
    (5, 0, 3, 1),
    (2, 1, 8, 2),
    (0, 3, 12, 2),
)
TINY_CLOUD = (
    (2, 0, 3, 1),
    (0, 1, 8, 2),
)


def sky_color(y: int) -> tuple[int, int, int]:
    """Return a gentle vertical sky gradient."""
    top = (139, 216, 255)
    bottom = (90, 186, 244)
    ratio = y / (HEIGHT - 1)
    return tuple(
        round(start + ((end - start) * ratio)) for start, end in zip(top, bottom, strict=True)
    )


def draw_cloud(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    *,
    color: tuple[int, int, int],
    shape: tuple[tuple[int, int, int, int], ...],
) -> None:
    """Draw one asymmetric pixel-cloud silhouette."""
    for cloud_x, cloud_y, width, height in shape:
        left = x + cloud_x
        top = y + cloud_y
        draw.rectangle(
            (left, top, left + width - 1, top + height - 1),
            fill=color,
        )


def drifting_x(frame_index: int, cloud_width: int, phase: float) -> int:
    """Move a cloud right-to-left once per loop with a staggered phase."""
    progress = ((frame_index / FRAME_COUNT) + phase) % 1
    return WIDTH - round((WIDTH + cloud_width) * progress)


def bobbing_y(frame_index: int, base_y: int, phase: float) -> int:
    """Give each cloud a subtle, differently phased one-pixel rise and fall."""
    progress = (frame_index / FRAME_COUNT) + phase
    return base_y + round(math.sin(progress * math.tau))


def text_width(text: str) -> int:
    """Measure the custom pixel text."""
    return sum(len(GLYPHS[character][0]) + 1 for character in text) - 1


def draw_pixel_text(draw: ImageDraw.ImageDraw, text: str, x: int, y: int) -> None:
    """Draw a small dark label that stays readable over the moving clouds."""
    cursor = x
    shadow = (218, 244, 255)
    foreground = (24, 59, 99)
    for color, offset in ((shadow, (1, 1)), (foreground, (0, 0))):
        cursor = x
        for character in text:
            glyph = GLYPHS[character]
            for row, bits in enumerate(glyph):
                for column, bit in enumerate(bits):
                    if bit == "1":
                        draw.point((cursor + column + offset[0], y + row + offset[1]), fill=color)
            cursor += len(glyph[0]) + 1


def render_frames() -> list[Image.Image]:
    """Render one seamless twenty-four-second cloud loop."""
    frames: list[Image.Image] = []
    label = "DAYDREAMING"
    label_x = (WIDTH - text_width(label)) // 2
    for frame_index in range(FRAME_COUNT):
        frame = Image.new("RGB", (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(frame)
        for y in range(HEIGHT):
            draw.line((0, y, WIDTH - 1, y), fill=sky_color(y))

        draw_cloud(
            draw,
            drifting_x(frame_index, 15, 0.12),
            bobbing_y(frame_index, 9, 0.08),
            color=(247, 252, 255),
            shape=PUFFY_CLOUD,
        )
        draw_cloud(
            draw,
            drifting_x(frame_index, 12, 0.58),
            bobbing_y(frame_index, 1, 0.47),
            color=(210, 239, 255),
            shape=WISPY_CLOUD,
        )
        draw_cloud(
            draw,
            drifting_x(frame_index, 8, 0.83),
            bobbing_y(frame_index, 7, 0.71),
            color=(234, 247, 255),
            shape=TINY_CLOUD,
        )
        draw_pixel_text(draw, label, label_x, 4)
        frames.append(frame)
    return frames


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frames = render_frames()
    try:
        write_anim(
            frames,
            root / "src/busybar_home/assets/daydreaming_72x16.anim",
            fps=FPS,
        )
        write_webp(
            frames,
            root / "src/busybar_home/static/animations/daydreaming_72x16.webp",
            fps=FPS,
        )
    finally:
        for frame in frames:
            frame.close()


if __name__ == "__main__":
    main()
