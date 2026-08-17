"""Generate the device and browser assets for the I-heart-my-wife scene."""

from __future__ import annotations

from pathlib import Path

from animation_assets import write_anim, write_webp
from PIL import Image, ImageDraw

WIDTH = 72
HEIGHT = 16
FPS = 12
FRAME_COUNT = 72

NORMAL_BACKGROUND = (5, 4, 9)
NORMAL_TEXT = (255, 248, 250)
NORMAL_HEART = (255, 42, 79)
INVERTED_BACKGROUND = (255, 243, 239)
INVERTED_TEXT = (17, 8, 14)
INVERTED_HEART = (177, 0, 43)
PULSE_HEART = (255, 151, 170)

GLYPHS = {
    "E": ("111", "100", "110", "100", "111"),
    "F": ("111", "100", "110", "100", "100"),
    "I": ("111", "010", "010", "010", "111"),
    "M": ("10001", "11011", "10101", "10001", "10001"),
    "W": ("10001", "10001", "10101", "10101", "01010"),
    "Y": ("10001", "01010", "00100", "00100", "00100"),
}

HEART = (
    "0110110",
    "1111111",
    "1111111",
    "1111111",
    "0111110",
    "0011100",
    "0001000",
)

LARGE_I = (
    "111",
    "010",
    "010",
    "010",
    "010",
    "010",
    "111",
)


def draw_pixels(
    draw: ImageDraw.ImageDraw,
    glyph: tuple[str, ...],
    x: int,
    y: int,
    *,
    color: tuple[int, int, int],
    scale_x: int = 2,
    scale_y: int = 2,
) -> None:
    for row, bits in enumerate(glyph):
        for column, bit in enumerate(bits):
            if bit != "1":
                continue
            left = x + column * scale_x
            top = y + row * scale_y
            draw.rectangle(
                (left, top, left + scale_x - 1, top + scale_y - 1),
                fill=color,
            )


def draw_message(*, inverted: bool, heart_pulsing: bool) -> Image.Image:
    background = INVERTED_BACKGROUND if inverted else NORMAL_BACKGROUND
    text_color = INVERTED_TEXT if inverted else NORMAL_TEXT
    heart_color = PULSE_HEART if heart_pulsing else INVERTED_HEART if inverted else NORMAL_HEART

    frame = Image.new("RGB", (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(frame)
    draw_pixels(draw, LARGE_I, 1, 1, color=text_color)
    draw_pixels(draw, HEART, 12, 1, color=heart_color)

    for word, x, y in (("MY", 38, 2), ("WIFE", 32, 9)):
        cursor = x
        for character in word:
            glyph = GLYPHS[character]
            draw_pixels(draw, glyph, cursor, y, color=text_color, scale_y=1)
            cursor += (len(glyph[0]) * 2) + 2
    return frame


def composite_wave(
    source: Image.Image,
    target: Image.Image,
    radius: float,
) -> Image.Image:
    frame = source.copy()
    source_pixels = source.load()
    target_pixels = target.load()
    frame_pixels = frame.load()
    center_x = 18.5
    for x in range(WIDTH):
        distance = abs(x - center_x)
        if distance <= radius:
            for y in range(HEIGHT):
                frame_pixels[x, y] = target_pixels[x, y]
        elif distance <= radius + 0.8:
            for y in range(HEIGHT):
                original = source_pixels[x, y]
                frame_pixels[x, y] = tuple(min(255, round(channel * 1.35)) for channel in original)
    return frame


def render_frames() -> list[Image.Image]:
    """Render a six-second heartbeat-driven positive/negative loop."""
    frames: list[Image.Image] = []
    for index in range(FRAME_COUNT):
        heart_pulsing = index in {8, 9, 11, 12, 36, 37, 39, 40}
        normal = draw_message(inverted=False, heart_pulsing=heart_pulsing)
        inverted = draw_message(inverted=True, heart_pulsing=heart_pulsing)

        if 12 <= index < 28:
            radius = ((index - 11) / 16) * 55
            frame = composite_wave(normal, inverted, radius)
        elif 28 <= index < 40:
            frame = inverted.copy()
        elif 40 <= index < 56:
            radius = ((index - 39) / 16) * 55
            frame = composite_wave(inverted, normal, radius)
        else:
            frame = normal.copy()

        normal.close()
        inverted.close()
        frames.append(frame)
    return frames


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frames = render_frames()
    try:
        write_anim(
            frames,
            root / "src/busybar_home/assets/love_my_wife_72x16.anim",
            fps=FPS,
        )
        write_webp(
            frames,
            root / "src/busybar_home/static/animations/love_my_wife_72x16.webp",
            fps=FPS,
        )
    finally:
        for frame in frames:
            frame.close()


if __name__ == "__main__":
    main()
