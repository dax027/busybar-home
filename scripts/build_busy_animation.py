"""Generate the device and browser assets for the Busy checklist scene."""

from __future__ import annotations

from pathlib import Path

from animation_assets import write_anim, write_webp
from PIL import Image, ImageDraw

WIDTH = 72
HEIGHT = 16
FPS = 12
FRAME_COUNT = 96

BACKGROUND_TOP = (20, 5, 5)
BACKGROUND_BOTTOM = (57, 15, 9)
WHITE = (250, 248, 242)
PAPER = (225, 224, 214)
INK = (31, 25, 25)
ORANGE = (255, 92, 53)
ORANGE_DIM = (132, 42, 25)
PENCIL_YELLOW = (255, 195, 64)
PENCIL_WOOD = (247, 208, 139)
PENCIL_ERASER = (255, 105, 145)

GLYPHS = {
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "Y": ("10001", "01010", "00100", "00100", "00100", "00100", "00100"),
}


def background_color(y: int) -> tuple[int, int, int]:
    ratio = y / (HEIGHT - 1)
    return tuple(
        round(top + ((bottom - top) * ratio))
        for top, bottom in zip(BACKGROUND_TOP, BACKGROUND_BOTTOM, strict=True)
    )


def draw_large_text(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    cursor = x
    for character in "BUSY":
        glyph = GLYPHS[character]
        for row, bits in enumerate(glyph):
            for column, bit in enumerate(bits):
                if bit == "1":
                    left = cursor + column * 2
                    top = y + row * 2
                    draw.rectangle((left + 1, top + 1, left + 2, top + 2), fill=ORANGE_DIM)
                    draw.rectangle((left, top, left + 1, top + 1), fill=WHITE)
        cursor += 12


def draw_checkmark(draw: ImageDraw.ImageDraw, y: int, progress: int) -> None:
    points = ((4, y), (5, y + 1), (6, y), (7, y - 1))
    for point in points[:progress]:
        draw.point(point, fill=ORANGE)


def draw_pencil(draw: ImageDraw.ImageDraw, tip_x: int, tip_y: int) -> None:
    """Draw a thick diagonal pencil with distinct tip, wood, body, and eraser."""
    draw.point((tip_x, tip_y), fill=INK)
    draw.point((tip_x + 1, tip_y), fill=PENCIL_WOOD)
    draw.point((tip_x + 1, tip_y - 1), fill=PENCIL_WOOD)

    for step in range(4):
        x = tip_x + 2 + step
        y = tip_y - 1 - step
        draw.point((x, y), fill=PENCIL_YELLOW)
        draw.point((x + 1, y), fill=ORANGE)

    draw.point((tip_x + 6, tip_y - 4), fill=PENCIL_ERASER)
    draw.point((tip_x + 7, tip_y - 4), fill=PENCIL_ERASER)


def draw_clipboard(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    cycle = frame_index // 24
    within_step = frame_index % 24
    completed = min(cycle, 3)
    pulse = cycle == 3 and within_step < 8
    frame_color = ORANGE if pulse else ORANGE_DIM

    draw.rectangle((1, 2, 18, 15), fill=frame_color)
    draw.rectangle((2, 3, 17, 15), fill=PAPER)
    draw.rectangle((6, 0, 13, 3), fill=ORANGE)
    draw.rectangle((8, 1, 11, 2), fill=INK)

    rows = (5, 9, 13)
    for index, row_y in enumerate(rows):
        draw.rectangle((3, row_y - 1, 6, row_y + 1), outline=INK)
        draw.line((9, row_y, 15, row_y), fill=INK)
        if index < completed:
            draw_checkmark(draw, row_y, 4)

    if cycle < 3:
        active_y = rows[cycle]
        check_progress = max(0, min(4, (within_step - 5) // 3 + 1))
        if within_step >= 5:
            draw_checkmark(draw, active_y, check_progress)
        pencil_tip_x = 8 - min(4, within_step // 4)
        draw_pencil(draw, pencil_tip_x, active_y)


def render_frames() -> list[Image.Image]:
    """Render an eight-second checklist loop."""
    frames: list[Image.Image] = []
    for index in range(FRAME_COUNT):
        frame = Image.new("RGB", (WIDTH, HEIGHT))
        draw = ImageDraw.Draw(frame)
        for y in range(HEIGHT):
            draw.line((0, y, WIDTH - 1, y), fill=background_color(y))

        draw_clipboard(draw, index)
        draw_large_text(draw, 22, 1)
        frames.append(frame)
    return frames


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frames = render_frames()
    try:
        write_anim(
            frames,
            root / "src/busybar_home/assets/busy_checklist_v2_72x16.anim",
            fps=FPS,
        )
        write_webp(
            frames,
            root / "src/busybar_home/static/animations/busy_checklist_v2_72x16.webp",
            fps=FPS,
        )
    finally:
        for frame in frames:
            frame.close()


if __name__ == "__main__":
    main()
