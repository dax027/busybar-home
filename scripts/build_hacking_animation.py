"""Generate the device and browser assets for the Hacking scene."""

from __future__ import annotations

import random
from pathlib import Path

from animation_assets import write_anim, write_webp
from PIL import Image, ImageDraw

WIDTH = 72
HEIGHT = 16
FPS = 12
FRAME_COUNT = 108

BLACK = (2, 3, 8)
CYAN = (35, 217, 255)
MAGENTA = (255, 45, 178)
MASK = (235, 239, 230)
MASK_SHADOW = (166, 174, 174)
INK = (10, 13, 20)

GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("111", "010", "010", "010", "010", "010", "111"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
}


def draw_mask(
    draw: ImageDraw.ImageDraw, offset_x: int = 0, color: tuple[int, int, int] = MASK
) -> None:
    """Draw a compact, stylized Guy Fawkes-inspired mask."""
    cx = 36 + offset_x
    outline = (
        (cx - 6, 0),
        (cx + 6, 0),
        (cx + 9, 2),
        (cx + 10, 6),
        (cx + 7, 12),
        (cx + 2, 15),
        (cx - 2, 15),
        (cx - 7, 12),
        (cx - 10, 6),
        (cx - 9, 2),
    )
    draw.polygon(outline, fill=color)

    # Temple and cheek planes keep the pale face from reading as a flat skull.
    shadow = MASK_SHADOW if color == MASK else color
    draw.line((cx - 9, 5, cx - 7, 10, cx - 4, 12), fill=shadow)
    draw.line((cx + 9, 5, cx + 7, 10, cx + 4, 12), fill=shadow)

    # High brows are separate from the narrow, half-lidded eyes.
    draw.line((cx - 8, 4, cx - 5, 2, cx - 1, 3), fill=INK)
    draw.line((cx + 1, 3, cx + 5, 2, cx + 8, 4), fill=INK)
    draw.line((cx - 7, 5, cx - 4, 4, cx - 2, 5), fill=INK)
    draw.line((cx + 2, 5, cx + 4, 4, cx + 7, 5), fill=INK)

    # Long nose, lifted moustache, broad smile, and a vertical pointed goatee.
    draw.line((cx, 4, cx - 1, 9, cx, 10, cx + 1, 9), fill=shadow)
    draw.line((cx - 8, 9, cx - 5, 11, cx - 2, 10, cx, 9), fill=INK)
    draw.line((cx, 9, cx + 2, 10, cx + 5, 11, cx + 8, 9), fill=INK)
    draw.line((cx - 6, 11, cx - 3, 13, cx, 12, cx + 3, 13, cx + 6, 11), fill=INK)
    draw.line((cx - 1, 12, cx - 1, 14), fill=INK)
    draw.line((cx, 12, cx, 15), fill=INK)
    draw.line((cx + 1, 12, cx + 1, 14), fill=INK)


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


def add_scan_noise(draw: ImageDraw.ImageDraw, rng: random.Random, strength: int) -> None:
    for _ in range(strength):
        y = rng.randrange(HEIGHT)
        x = rng.randrange(WIDTH)
        length = rng.randrange(2, 13)
        color = CYAN if rng.randrange(2) else MAGENTA
        draw.line((x, y, min(WIDTH - 1, x + length), y), fill=color)


def render_mask_frame(index: int, rng: random.Random) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    draw = ImageDraw.Draw(frame)
    reveal = min(HEIGHT, max(0, index * 2 - 2))

    ghost = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    ghost_draw = ImageDraw.Draw(ghost)
    draw_mask(ghost_draw, -1, MAGENTA)
    draw_mask(ghost_draw, 1, CYAN)
    draw_mask(ghost_draw)
    if reveal:
        frame.paste(ghost.crop((0, 0, WIDTH, reveal)), (0, 0))
    add_scan_noise(draw, rng, max(1, 8 - index // 2))
    return frame


def render_mask_hold(index: int, rng: random.Random) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    draw = ImageDraw.Draw(frame)
    if index % 11 == 0:
        draw_mask(draw, -1, MAGENTA)
        draw_mask(draw, 1, CYAN)
    draw_mask(draw)
    draw.line((2, 1, 17, 1), fill=MAGENTA)
    draw.line((54, 14, 69, 14), fill=CYAN)
    add_scan_noise(draw, rng, 1 if index % 4 else 3)
    return frame


def render_transition(index: int, rng: random.Random) -> Image.Image:
    base = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    base_draw = ImageDraw.Draw(base)
    draw_mask(base_draw)
    frame = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    draw = ImageDraw.Draw(frame)
    progress = index / 23
    for y in range(HEIGHT):
        direction = -1 if y % 2 else 1
        spread = round(progress * (18 + (y % 5) * 4))
        jitter = rng.randrange(-2, 3)
        shift = direction * spread + jitter
        row = base.crop((0, y, WIDTH, y + 1))
        frame.paste(row, (shift, y))
        if progress > 0.25 and y % 3 == 0:
            draw.line((0, y, WIDTH - 1, y), fill=CYAN if y % 2 else MAGENTA)
    add_scan_noise(draw, rng, 3 + index // 4)
    return frame


def render_word_frame(index: int, rng: random.Random) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), BLACK)
    draw = ImageDraw.Draw(frame)
    word = "HACKING"
    x = (WIDTH - text_width(word)) // 2
    jitter = 1 if index % 13 == 0 else 0
    draw_word(draw, word, x - 1 - jitter, 5, MAGENTA)
    draw_word(draw, word, x + 1 + jitter, 5, CYAN)
    draw_word(draw, word, x, 4, (238, 244, 255))

    # Intermittent horizontal displacement makes the colored echoes feel blurred.
    if index % 7 in {0, 1}:
        y = 4 + (index * 3) % 7
        band = frame.crop((0, y, WIDTH, min(HEIGHT, y + 2)))
        frame.paste(band, (3 if index % 2 else -3, y))
    add_scan_noise(draw, rng, 2 if index % 5 == 0 else 0)
    return frame


def render_frames() -> list[Image.Image]:
    """Render a seamless nine-second mask-to-wordmark loop."""
    frames: list[Image.Image] = []
    for index in range(FRAME_COUNT):
        rng = random.Random(0xFA5C + index)
        if index < 12:
            frame = render_mask_frame(index, rng)
        elif index < 36:
            frame = render_mask_hold(index - 12, rng)
        elif index < 60:
            frame = render_transition(index - 36, rng)
        elif index < 96:
            frame = render_word_frame(index - 60, rng)
        else:
            frame = render_word_frame(index - 60, rng)
            fade = (index - 95) / 12
            frame = Image.blend(frame, Image.new("RGB", frame.size, BLACK), fade)
        frames.append(frame)
    return frames


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frames = render_frames()
    try:
        write_anim(
            frames,
            root / "src/busybar_home/assets/hacking_fawkes_72x16.anim",
            fps=FPS,
        )
        write_webp(
            frames,
            root / "src/busybar_home/static/animations/hacking_fawkes_72x16.webp",
            fps=FPS,
        )
    finally:
        for frame in frames:
            frame.close()


if __name__ == "__main__":
    main()
