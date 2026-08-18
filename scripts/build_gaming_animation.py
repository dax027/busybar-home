"""Generate the device and browser assets for the Gaming scene."""

from __future__ import annotations

from pathlib import Path

from animation_assets import write_anim, write_webp
from PIL import Image, ImageDraw

WIDTH = 72
HEIGHT = 16
FPS = 12
FRAME_COUNT = 96

BACKGROUND = (2, 2, 12)
INK = (7, 5, 22)
WHITE = (246, 247, 255)
CYAN = (44, 224, 255)
MAGENTA = (255, 54, 190)
VIOLET = (139, 92, 246)
YELLOW = (255, 218, 78)
GREEN = (76, 255, 160)
PALETTE = (MAGENTA, VIOLET, CYAN, GREEN, YELLOW)

GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
}


def dim(color: tuple[int, int, int], level: float) -> tuple[int, int, int]:
    return tuple(round(channel * level) for channel in color)


def draw_gamepad(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    """Draw a compact controller with animated buttons and power rails."""
    body = (
        (22, 4),
        (27, 2),
        (45, 2),
        (50, 4),
        (55, 13),
        (51, 15),
        (44, 10),
        (28, 10),
        (21, 15),
        (17, 13),
    )
    draw.polygon(body, fill=dim(VIOLET, 0.26), outline=VIOLET)
    draw.line((27, 3, 45, 3), fill=CYAN)
    draw.line((20, 12, 24, 7), fill=dim(CYAN, 0.55))
    draw.line((52, 12, 48, 7), fill=dim(MAGENTA, 0.55))

    # D-pad.
    draw.rectangle((24, 5, 30, 7), fill=WHITE)
    draw.rectangle((26, 3, 28, 9), fill=WHITE)
    draw.rectangle((26, 5, 28, 7), fill=INK)

    # Face buttons pulse independently so the controller reads as active.
    a_color = YELLOW if frame_index % 12 < 7 else dim(YELLOW, 0.32)
    b_color = MAGENTA if (frame_index + 5) % 14 < 8 else dim(MAGENTA, 0.32)
    draw.rectangle((44, 5, 46, 7), fill=a_color)
    draw.rectangle((48, 4, 50, 6), fill=b_color)
    draw.point((45, 6), fill=WHITE)
    draw.point((49, 5), fill=WHITE)

    # Center buttons and a traveling power indicator.
    draw.line((34, 6, 35, 6), fill=dim(WHITE, 0.6))
    draw.line((38, 6, 39, 6), fill=dim(WHITE, 0.6))
    power_x = 31 + (frame_index % 12)
    draw.point((power_x, 10), fill=GREEN)


def render_controller_frame(index: int) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    controller = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw_gamepad(ImageDraw.Draw(controller), index)
    reveal_width = min(WIDTH, max(0, index * 6))
    if reveal_width:
        left = (WIDTH - reveal_width) // 2
        right = left + reveal_width
        frame.paste(controller.crop((left, 0, right, HEIGHT)), (left, 0))
    draw = ImageDraw.Draw(frame)
    if index >= 9:
        rail = min(15, (index - 8) * 2)
        draw.line((2, 1, 2 + rail, 1), fill=MAGENTA)
        draw.line((69 - rail, 14, 69, 14), fill=CYAN)
    return frame


def render_transition(index: int) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(frame)
    draw_gamepad(draw, index + 30)
    progress = index / 11
    for y in range(HEIGHT):
        length = round(progress * (36 + (y % 4) * 7))
        color = PALETTE[y % len(PALETTE)]
        draw.line((36 - length, y, 36 + length, y), fill=dim(color, 0.35 + progress * 0.45))
    return frame


def draw_gaming_word(draw: ImageDraw.ImageDraw, frame_index: int, *, inverse: bool) -> None:
    cursor = 3
    for letter_index, character in enumerate("GAMING"):
        glyph = GLYPHS[character]
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit != "1":
                    continue
                x = cursor + column * 2
                y = 1 + row * 2
                if inverse:
                    color = INK
                else:
                    phase = (letter_index + row + frame_index // 3) % len(PALETTE)
                    color = PALETTE[phase]
                draw.rectangle((x, y, x + 1, y + 1), fill=color)
                if not inverse and (row + column + frame_index) % 9 == 0:
                    draw.point((x, y), fill=WHITE)
        cursor += 11


def render_word_frame(index: int) -> Image.Image:
    inverse = index in {20, 21, 43}
    background = dim(CYAN if index == 20 else MAGENTA, 0.72) if inverse else BACKGROUND
    frame = Image.new("RGB", (WIDTH, HEIGHT), background)
    draw = ImageDraw.Draw(frame)
    draw_gaming_word(draw, index, inverse=inverse)

    # Brief pixel displacement gives the loop an arcade-screen snap without hurting readability.
    if index % 17 == 0 and not inverse:
        y = 2 + (index * 3) % 10
        band = frame.crop((0, y, WIDTH, min(HEIGHT, y + 2)))
        frame.paste(band, (2, y))
    return frame


def render_frames() -> list[Image.Image]:
    """Render an eight-second controller-to-arcade-wordmark loop."""
    frames: list[Image.Image] = []
    for index in range(FRAME_COUNT):
        if index < 30:
            frame = render_controller_frame(index)
        elif index < 42:
            frame = render_transition(index - 30)
        elif index < 90:
            frame = render_word_frame(index - 42)
        else:
            word = render_word_frame(index - 42)
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
            root / "src/busybar_home/assets/gaming_arcade_72x16.anim",
            fps=FPS,
        )
        write_webp(
            frames,
            root / "src/busybar_home/static/animations/gaming_arcade_72x16.webp",
            fps=FPS,
        )
    finally:
        for frame in frames:
            frame.close()


if __name__ == "__main__":
    main()
