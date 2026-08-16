import pytest

from busybar_home.config import ClientKind, Settings


def test_settings_default_to_fake_and_disallow_hardware() -> None:
    settings = Settings.from_env({})

    assert settings.client_kind is ClientKind.FAKE
    assert settings.allow_hardware is False


def test_settings_load_official_client_values() -> None:
    settings = Settings.from_env(
        {
            "BUSYBAR_CLIENT": "official",
            "BUSYBAR_DEVICE_ADDRESS": "192.0.2.10",
            "BUSYBAR_ACCESS_TOKEN": "secret",
            "BUSYBAR_ALLOW_HARDWARE": "yes",
        }
    )

    assert settings == Settings(
        client_kind=ClientKind.OFFICIAL,
        device_address="192.0.2.10",
        access_token="secret",
        allow_hardware=True,
    )


def test_settings_reject_invalid_boolean() -> None:
    with pytest.raises(ValueError, match="BUSYBAR_ALLOW_HARDWARE"):
        Settings.from_env({"BUSYBAR_ALLOW_HARDWARE": "sometimes"})
