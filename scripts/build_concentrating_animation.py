"""Generate the device and browser assets for the Concentrating scene."""

from __future__ import annotations

import math
from pathlib import Path

from animation_assets import write_anim, write_webp
from PIL import Image, ImageDraw

WIDTH = 72
HEIGHT = 16
FPS = 12
TEXT = "CONCENTRATING"
SCALE = 2
LETTER_GAP = 2
TEXT_WIDTH = len(TEXT) * 5 * SCALE + (len(TEXT) - 1) * LETTER_GAP
BRAIN_FRAMES = 44
SCROLL_STEP = 2
SCROLL_FRAMES = math.ceil((WIDTH + TEXT_WIDTH) / SCROLL_STEP) + 1
PAUSE_FRAMES = 6
FRAME_COUNT = BRAIN_FRAMES + SCROLL_FRAMES + PAUSE_FRAMES

BACKGROUND = (3, 3, 8)
BRAIN_FILL = (27, 5, 14)
AMBER = (255, 164, 46)
GOLD = (255, 207, 87)
RED = (236, 42, 76)
CORAL = (255, 78, 119)
PINK = (255, 143, 166)
CYAN = (45, 225, 255)
WHITE = (255, 248, 219)

GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01110"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    # The stepped diagonal is deliberately explicit so N never reads as H.
    "N": ("10001", "11001", "11001", "10101", "10011", "10011", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
}

PET_HOTSPOTS = (
    (21, 6, 0),
    (28, 10, 8),
    (35, 5, 16),
    (42, 9, 24),
    (49, 5, 32),
    (53, 9, 40),
)

NEURAL_PATH = ((16, 8), (23, 4), (30, 10), (37, 5), (45, 10), (52, 5), (60, 8), (70, 8))


def dim(color: tuple[int, int, int], level: float) -> tuple[int, int, int]:
    """Return a brightness-scaled RGB color."""
    return tuple(round(channel * level) for channel in color)


def blend(
    first: tuple[int, int, int],
    second: tuple[int, int, int],
    amount: float,
) -> tuple[int, int, int]:
    """Blend two RGB colors by a normalized amount."""
    return tuple(
        round(first_channel + (second_channel - first_channel) * amount)
        for first_channel, second_channel in zip(first, second, strict=True)
    )


def draw_pet_scale(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    """Draw tiny heat-scale markers that cue a medical scan."""
    scale = (RED, CORAL, AMBER, GOLD, WHITE)
    for index, color in enumerate(scale):
        brightness = 1.0 if (frame_index // 3) % len(scale) == index else 0.42
        draw.point((5, 4 + index * 2), fill=dim(color, brightness))
        draw.point((66, 4 + index * 2), fill=dim(color, brightness))


def draw_pet_brain(draw: ImageDraw.ImageDraw, frame_index: int) -> None:
    """Draw a side-view brain with independently flashing PET-scan regions."""
    brain = (
        (12, 8),
        (14, 5),
        (18, 3),
        (24, 1),
        (34, 1),
        (43, 2),
        (50, 4),
        (56, 6),
        (59, 9),
        (56, 12),
        (50, 13),
        (44, 13),
        (40, 12),
        (36, 14),
        (29, 14),
        (25, 13),
        (19, 13),
        (15, 11),
    )
    brainstem = ((39, 11), (45, 12), (47, 14), (44, 15), (39, 14), (36, 12))
    pulse = 0.76 + 0.14 * math.sin(frame_index * 0.34)
    draw.polygon(brain, fill=BRAIN_FILL, outline=dim(PINK, pulse))
    draw.polygon(brainstem, fill=BRAIN_FILL, outline=dim(CORAL, pulse))

    # Side-view folds follow different paths, avoiding the mirrored top-down look.
    fold = dim(CORAL, 0.5 + 0.14 * math.sin(frame_index * 0.43))
    draw.line((18, 7, 21, 4, 27, 4, 30, 6, 26, 8, 20, 8), fill=fold)
    draw.line((31, 3, 37, 3, 40, 5, 37, 7, 32, 6), fill=fold)
    draw.line((43, 4, 49, 5, 52, 7, 48, 8, 43, 7), fill=fold)
    draw.line((17, 10, 23, 10, 27, 12, 32, 10, 36, 11), fill=fold)
    draw.line((39, 9, 44, 10, 49, 9, 54, 10), fill=fold)

    # A narrow scan beam sweeps through the image behind the brighter heat regions.
    scan_x = 14 + (frame_index * 2) % 44
    draw.line((scan_x, 3, scan_x, 12), fill=dim(CYAN, 0.2))

    for x, y, phase_offset in PET_HOTSPOTS:
        heat = (math.sin((frame_index + phase_offset) * math.tau / 28) + 1) / 2
        if heat < 0.25:
            continue
        core = blend(RED, WHITE, heat)
        halo = blend(CORAL, AMBER, heat)
        draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=dim(halo, 0.48 + heat * 0.35))
        draw.point((x, y), fill=core)
        if heat > 0.88:
            draw.point((x - 2, y), fill=dim(GOLD, 0.6))
            draw.point((x + 2, y), fill=dim(GOLD, 0.6))


def draw_neural_discharge(draw: ImageDraw.ImageDraw, progress: float) -> None:
    """Fire a bright signal across the brain and out toward the scrolling text."""
    segment_progress = progress * (len(NEURAL_PATH) - 1)
    complete_segments = int(segment_progress)
    for index in range(complete_segments):
        draw.line((*NEURAL_PATH[index], *NEURAL_PATH[index + 1]), fill=CYAN)

    if complete_segments < len(NEURAL_PATH) - 1:
        local = segment_progress - complete_segments
        start_x, start_y = NEURAL_PATH[complete_segments]
        end_x, end_y = NEURAL_PATH[complete_segments + 1]
        current_x = round(start_x + (end_x - start_x) * local)
        current_y = round(start_y + (end_y - start_y) * local)
        draw.line((start_x, start_y, current_x, current_y), fill=CYAN)
    else:
        current_x, current_y = NEURAL_PATH[-1]

    draw.point((current_x, current_y), fill=WHITE)
    if 0 < current_x < WIDTH - 1:
        draw.point((current_x - 1, current_y), fill=dim(CYAN, 0.6))
        draw.point((current_x + 1, current_y), fill=dim(CYAN, 0.6))


def render_brain_frame(index: int) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(frame)
    draw_pet_scale(draw, index)
    draw_pet_brain(draw, index)
    if index >= 30:
        draw_neural_discharge(draw, min(1.0, (index - 30) / 13))
    return frame


def draw_firing_letter(
    draw: ImageDraw.ImageDraw,
    character: str,
    x: int,
    letter_index: int,
    frame_index: int,
) -> None:
    """Draw one chunky glyph that fires as it crosses the center synapse."""
    glyph = GLYPHS[character]
    center_x = x + 5
    distance = abs(center_x - (WIDTH - 1) / 2)
    intensity = max(0.0, 1.0 - distance / 10)
    pulse = 0.78 + 0.12 * math.sin((frame_index + letter_index * 3) * 0.35)
    color = blend(dim(GOLD, pulse), CYAN, intensity)

    for row, bits in enumerate(glyph):
        for column, bit in enumerate(bits):
            if bit != "1":
                continue
            pixel_x = x + column * SCALE
            pixel_y = 1 + row * SCALE
            draw.rectangle(
                (pixel_x, pixel_y, pixel_x + SCALE - 1, pixel_y + SCALE - 1),
                fill=color,
            )
            if intensity > 0.72 and (row * 2 + column + frame_index) % 5 == 0:
                draw.point((pixel_x, pixel_y), fill=WHITE)

    if intensity > 0.65 and frame_index % 4 < 2:
        spark = blend(CYAN, WHITE, intensity)
        draw.line((center_x, 0, center_x - 2, 2), fill=spark)
        draw.line((center_x, 15, center_x + 2, 13), fill=spark)
        draw.point((center_x + 3, 0), fill=dim(CYAN, intensity))
        draw.point((center_x - 3, 15), fill=dim(CYAN, intensity))


def render_scroll_frame(index: int) -> Image.Image:
    frame = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(frame)
    cursor = WIDTH - index * SCROLL_STEP
    for letter_index, character in enumerate(TEXT):
        if cursor < WIDTH and cursor + 10 >= 0:
            draw_firing_letter(draw, character, cursor, letter_index, index)
        cursor += 5 * SCALE + LETTER_GAP

    # Dim fixed synapse points make the firing position legible without obscuring text.
    draw.point((35, 0), fill=dim(CYAN, 0.45))
    draw.point((36, 15), fill=dim(CYAN, 0.45))
    return frame


def render_frames() -> list[Image.Image]:
    """Render a PET-brain intro followed by a neural-firing text marquee."""
    frames: list[Image.Image] = []
    for index in range(FRAME_COUNT):
        if index < BRAIN_FRAMES:
            frame = render_brain_frame(index)
        elif index < BRAIN_FRAMES + SCROLL_FRAMES:
            frame = render_scroll_frame(index - BRAIN_FRAMES)
        else:
            frame = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
        frames.append(frame)
    return frames


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    frames = render_frames()
    try:
        write_anim(
            frames,
            root / "src/busybar_home/assets/concentrating_neural_72x16.anim",
            fps=FPS,
        )
        write_webp(
            frames,
            root / "src/busybar_home/static/animations/concentrating_neural_72x16.webp",
            fps=FPS,
        )
    finally:
        for frame in frames:
            frame.close()


if __name__ == "__main__":
    main()
