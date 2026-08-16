"""Environment-backed application settings."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class ClientKind(StrEnum):
    FAKE = "fake"
    OFFICIAL = "official"


def _parse_bool(value: str, *, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuration loaded only from explicit values or environment variables."""

    client_kind: ClientKind = ClientKind.FAKE
    device_address: str = "10.0.4.20"
    access_token: str | None = None
    allow_hardware: bool = False
    display_priority: int = 100
    web_host: str = "127.0.0.1"
    web_port: int = 8765

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> "Settings":
        values = os.environ if environ is None else environ
        raw_kind = values.get("BUSYBAR_CLIENT", ClientKind.FAKE.value).strip().lower()
        try:
            client_kind = ClientKind(raw_kind)
        except ValueError as error:
            choices = ", ".join(kind.value for kind in ClientKind)
            raise ValueError(f"BUSYBAR_CLIENT must be one of: {choices}") from error

        address = values.get("BUSYBAR_DEVICE_ADDRESS", "10.0.4.20").strip()
        if not address:
            raise ValueError("BUSYBAR_DEVICE_ADDRESS must not be empty")

        token = values.get("BUSYBAR_ACCESS_TOKEN", "").strip() or None
        allow_hardware = _parse_bool(
            values.get("BUSYBAR_ALLOW_HARDWARE", "false"),
            name="BUSYBAR_ALLOW_HARDWARE",
        )
        web_host = values.get("BUSYBAR_WEB_HOST", "127.0.0.1").strip()
        if not web_host:
            raise ValueError("BUSYBAR_WEB_HOST must not be empty")
        try:
            web_port = int(values.get("BUSYBAR_WEB_PORT", "8765"))
        except ValueError as error:
            raise ValueError("BUSYBAR_WEB_PORT must be an integer") from error
        if not 1 <= web_port <= 65535:
            raise ValueError("BUSYBAR_WEB_PORT must be between 1 and 65535")
        try:
            display_priority = int(values.get("BUSYBAR_DISPLAY_PRIORITY", "100"))
        except ValueError as error:
            raise ValueError("BUSYBAR_DISPLAY_PRIORITY must be an integer") from error
        if not 1 <= display_priority <= 100:
            raise ValueError("BUSYBAR_DISPLAY_PRIORITY must be between 1 and 100")
        return cls(
            client_kind=client_kind,
            device_address=address,
            access_token=token,
            allow_hardware=allow_hardware,
            display_priority=display_priority,
            web_host=web_host,
            web_port=web_port,
        )
