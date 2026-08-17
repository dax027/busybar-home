"""Generate the device and browser assets for the Away BRB clock scene."""

from __future__ import annotations

from pathlib import Path

from animation_assets import write_anim, write_webp
from PIL import Image, ImageDraw

WIDTH = 72
HEIGHT = 16
FPS = 12
FRAME_COUNT = 96

NAVY_TOP = (5, 10, 24)
NAVY_BOTTOM = (12, 22, 43)
WHITE = (247, 249, 255)
AMBER = (255, 191, 71)
AMBER_DIM = (118, 72, 29)
BLUE_SHADOW = (34, 77, 121)

GLYPHS = {
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
}

SECOND_HAND_ENDPOINTS = (
    (8, 3),
    (11, 5),
    (13, 8),
    (11, 11),
    (8, 13),
    (5, 11),
    (3, 8),
    (5, 5),
)


def background_color(y: int) -> tuple[int, int, int]:
    ratio = y / (HEIGHT - 1)
    return tuple(
        round(top + ((bottom - top) * ratio))
        for top, bottom in zip(NAVY_TOP, NAVY_BOTTOM, strict=True)
    )


def draw_large_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    color: tuple[int, int, int],
) -> None:
    """Draw a double-height, double-width 5x7 pixel wordmark."""
    cursor = x
    for character in text:
        glyph = GLYPHS[character]
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit == "1":
                    left = cursor + column * 2
                    top = y + row * 2
                    draw.rectangle((left, top, left + 1, top + 1), fill=color)
        cursor += 12


def draw_clock(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    """Draw a clock whose second hand advances once per second."""
    tick_frame = frame_index % FPS
    rim_color = AMBER if tick_frame < 2 else AMBER_DIM
    draw.ellipse((1, 1, 15, 15), outline=rim_color, width=1)
    draw.point((8, 2), fill=AMBER)
    draw.point((14, 8), fill=AMBER)
    draw.point((8, 14), fill=AMBER)
    draw.point((2, 8), fill=AMBER)

    draw.line((8, 8, 6, 6), fill=WHITE)
    draw.line((8, 8, 11, 6), fill=WHITE)
    second_index = (frame_index // FPS) % len(SECOND_HAND_ENDPOINTS)
    draw.line((8, 8, *SECOND_HAND_ENDPOINTS[second_index]), fill=AMBER)
    draw.point((8, 8), fill=WHITE)


def draw_chasing_dots(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    active_dot = (frame_index // 8) % 3
    for index, x in enumerate((61, 66, 70)):
        color = AMBER if index == active_dot else AMBER_DIM
        draw.rectangle((x, 7, min(WIDTH - 1, x + 1), 8), fill=color)


def render_frames() -> list[Image.Image]:
    """Render an eight-second seamless BRB clock loop."""
    frames: list[Image.Image] = []
    for index in range(FRAME_COUNT):
        frame = Image.new("RGB", (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(frame)
        for y in range(HEIGHT):
            draw.line((0, y, WIDTH - 1, y), fill=background_color(y))

        draw_clock(draw, index)
        draw_large_text(draw, "BRB", 22, 2, BLUE_SHADOW)
        draw_large_text(draw, "BRB", 21, 1, WHITE)
        draw_chasing_dots(draw, index)
        frames.append(frame)
    return frames


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frames = render_frames()
    try:
        write_anim(
            frames,
            root / "src/busybar_home/assets/away_brb_clock_72x16.anim",
            fps=FPS,
        )
        write_webp(
            frames,
            root / "src/busybar_home/static/animations/away_brb_clock_72x16.webp",
            fps=FPS,
        )
    finally:
        for frame in frames:
            frame.close()


if __name__ == "__main__":
    main()
