"""Shared writers for BUSY Bar device animations and browser previews."""

from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image


def write_webp(frames: list[Image.Image], output: Path, *, fps: int) -> None:
    """Write a lossless, looping browser preview."""
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        output,
        format="WEBP",
        save_all=True,
        append_images=frames[1:],
        duration=round(1000 / fps),
        loop=0,
        lossless=True,
        minimize_size=True,
    )


def write_anim(frames: list[Image.Image], output: Path, *, fps: int) -> None:
    """Write an uncompressed BUSY Bar animation container."""
    if not frames:
        raise ValueError("At least one animation frame is required")
    width, height = frames[0].size
    if any(frame.size != (width, height) for frame in frames):
        raise ValueError("All animation frames must have the same dimensions")

    header_format = "<8s BBBB BHB II III"
    section_format = "<IIIB"
    frame_format = "<BBH"
    section_name = b"default\0"
    section_length = struct.calcsize(section_format) + len(section_name)
    header_length = struct.calcsize(header_format)
    raw_frame_length = width * height * 3
    encoded_frames: list[tuple[int, bytes]] = []
    for frame in frames:
        rgb = frame.convert("RGB").tobytes()
        bgr = bytearray(len(rgb))
        bgr[0::3] = rgb[2::3]
        bgr[1::3] = rgb[1::3]
        bgr[2::3] = rgb[0::3]
        payload = bytes(bgr)
        if encoded_frames and encoded_frames[-1][1] == payload:
            duration, previous_payload = encoded_frames[-1]
            if duration < 255:
                encoded_frames[-1] = (duration + 1, previous_payload)
                continue
        encoded_frames.append((1, payload))

    frames_chunk_length = sum(
        struct.calcsize(frame_format) + len(payload) for _duration, payload in encoded_frames
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as animation:
        animation.write(
            struct.pack(
                header_format,
                b"bicycle0",
                0,
                width,
                height,
                0,
                fps,
                raw_frame_length,
                0,
                section_length,
                frames_chunk_length,
                1,
                len(encoded_frames),
                len(frames),
            )
        )
        animation.write(
            struct.pack(
                section_format,
                0,
                len(frames) - 1,
                header_length + section_length,
                encoded_frames[0][0],
            )
        )
        animation.write(section_name)
        for duration, payload in encoded_frames:
            animation.write(struct.pack(frame_format, 0, duration, len(payload)))
            animation.write(payload)
