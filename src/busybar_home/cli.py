"""Command-line entry point."""

import argparse
from collections.abc import Sequence

from busybar_home.config import Settings
from busybar_home.factory import HardwareAccessDisabledError, create_client
from busybar_home.models import DisplayMessage, DisplayScene
from busybar_home.service import BusyBarService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Control a BUSY Bar safely")
    parser.add_argument(
        "message",
        nargs="?",
        default="HELLO",
        help="message to show (recorded in memory when using the default fake client)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        client = create_client(Settings.from_env())
    except (HardwareAccessDisabledError, ValueError) as error:
        print(f"Configuration error: {error}")
        return 2

    try:
        message = DisplayMessage(args.message)
        scene = DisplayScene(name="Command line", front=message, back=message)
        snapshot = BusyBarService(client).apply_scene(scene)
        mode = "fake" if client.__class__.__name__ == "FakeDeviceClient" else "official"
        print(
            f"Client: {mode}; connected: {snapshot.connected}; "
            f"firmware: {snapshot.firmware_version}"
        )
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
