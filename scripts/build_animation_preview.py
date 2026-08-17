"""Build a browser preview from an official BUSY Bar animation source directory."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from PIL import Image


def frame_number(path: Path) -> int:
    """Return the numeric suffix from a BUSY Bar frame filename."""
    match = re.fullmatch(r".+_(\d+)\.png", path.name)
    if match is None:
        raise ValueError(f"unexpected animation frame name: {path.name}")
    return int(match.group(1))


def build_preview(source: Path, output: Path) -> None:
    """Convert numbered PNG frames and metadata to a lossless animated WebP."""
    metadata = json.loads((source / "meta.json").read_text(encoding="utf-8"))
    fps = int(metadata["fps"])
    if fps <= 0:
        raise ValueError("animation fps must be positive")

    frame_paths = sorted(source.glob("*.png"), key=frame_number)
    if not frame_paths:
        raise ValueError("animation must contain at least one frame")
    if [frame_number(path) for path in frame_paths] != list(range(len(frame_paths))):
        raise ValueError("animation frames must be numbered consecutively from zero")

    frames = [Image.open(path).convert("RGB") for path in frame_paths]
    try:
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
    finally:
        for frame in frames:
            frame.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build_preview(args.source, args.output)


if __name__ == "__main__":
    main()
