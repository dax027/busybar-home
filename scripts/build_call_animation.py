"""Generate the device and browser assets for the On a Call scene."""

from __future__ import annotations

import math
from pathlib import Path

from animation_assets import write_anim, write_webp
from PIL import Image, ImageDraw

WIDTH = 72
HEIGHT = 16
FPS = 12
FRAME_COUNT = 72

BLACK = (3, 4, 8)
WHITE = (248, 249, 255)
PINK = (255, 63, 129)
DEEP_PINK = (121, 18, 67)

GLYPHS = {
    " ": ("000",) * 7,
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
}


def text_width(text: str) -> int:
    return sum(len(GLYPHS[character][0]) + 1 for character in text) - 1


def draw_word(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    cursor = x
    for character in text:
        glyph = GLYPHS[character]
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit == "1":
                    draw.point((cursor + column, y + row), fill=color)
        cursor += len(glyph[0]) + 1


def draw_microphone(draw: ImageDraw.ImageDraw, glow: int) -> None:
    """Draw a compact live microphone with a pulsing inner capsule."""
    if glow:
        draw.rectangle((5, 1, 12, 10), fill=DEEP_PINK)
    draw.rectangle((7, 2, 10, 9), fill=WHITE)
    draw.rectangle((8, 3, 9, 8), fill=PINK)
    draw.rectangle((5, 7, 6, 10), fill=PINK)
    draw.rectangle((11, 7, 12, 10), fill=PINK)
    draw.rectangle((6, 10, 11, 11), fill=PINK)
    draw.rectangle((8, 12, 9, 13), fill=PINK)
    draw.rectangle((6, 14, 11, 14), fill=PINK)


def render_frames() -> list[Image.Image]:
    """Render a six-second seamless live-level loop."""
    frames: list[Image.Image] = []
    label = "ON A CALL"
    label_x = WIDTH - text_width(label) - 2
    for index in range(FRAME_COUNT):
        frame = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
        draw = ImageDraw.Draw(frame)

        phase = index / FRAME_COUNT * math.tau
        levels = (
            2 + round((math.sin(phase * 2.0) + 1) * 1.5),
            3 + round((math.sin(phase * 3.0 + 1.4) + 1) * 2.0),
        )
        for x, level in zip((1, 15), levels, strict=True):
            top = 8 - level
            bottom = 7 + level
            draw.rectangle((x, top, x + 1, bottom), fill=PINK)

        draw_microphone(draw, glow=1 if index % 18 in {0, 1, 2} else 0)

        # A magenta offset gives the oversized white letters a live-signal edge.
        draw_word(draw, label, label_x + 1, 5, PINK)
        draw_word(draw, label, label_x, 4, WHITE)
        frames.append(frame)
    return frames


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frames = render_frames()
    try:
        write_anim(
            frames,
            root / "src/busybar_home/assets/on_a_call_mic_72x16.anim",
            fps=FPS,
        )
        write_webp(
            frames,
            root / "src/busybar_home/static/animations/on_a_call_mic_72x16.webp",
            fps=FPS,
        )
    finally:
        for frame in frames:
            frame.close()


if __name__ == "__main__":
    main()
