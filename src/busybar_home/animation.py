"""In-memory encoders for BUSY Bar animations and browser previews."""

from __future__ import annotations

import struct
from io import BytesIO

from PIL import Image


def encode_webp(frames: list[Image.Image], *, fps: int) -> bytes:
    """Encode a lossless looping browser preview."""
    _validate_frames(frames, fps)
    output = BytesIO()
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
    return output.getvalue()


def encode_anim(frames: list[Image.Image], *, fps: int) -> bytes:
    """Encode an uncompressed BUSY Bar animation container."""
    width, height = _validate_frames(frames, fps)
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
    output = BytesIO()
    output.write(
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
    output.write(
        struct.pack(
            section_format,
            0,
            len(frames) - 1,
            header_length + section_length,
            encoded_frames[0][0],
        )
    )
    output.write(section_name)
    for duration, payload in encoded_frames:
        output.write(struct.pack(frame_format, 0, duration, len(payload)))
        output.write(payload)
    return output.getvalue()


def _validate_frames(frames: list[Image.Image], fps: int) -> tuple[int, int]:
    if not frames:
        raise ValueError("at least one animation frame is required")
    if not 1 <= fps <= 255:
        raise ValueError("fps must be between 1 and 255")
    width, height = frames[0].size
    if any(frame.size != (width, height) for frame in frames):
        raise ValueError("all animation frames must have the same dimensions")
    return width, height
