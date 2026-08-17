import pytest

from busybar_home.ticker import (
    MAX_FRAMES,
    TickerConfig,
    TickerEffect,
    build_ticker_assets,
    render_ticker_frames,
)


def test_ticker_config_normalizes_safe_user_controls() -> None:
    config = TickerConfig(
        "  Build   complete  ",
        font_color="#aabbcc",
        background_color="#010203",
        speed=40,
        effect="letter_flash",
    )

    assert config.message == "Build complete"
    assert config.font_color == "#AABBCC"
    assert config.background_color == "#010203"
    assert config.effect is TickerEffect.LETTER_FLASH


@pytest.mark.parametrize(
    ("message", "speed"),
    [
        ("", 32),
        ("not supported: ♥", 32),
        ("x" * 49, 32),
        ("hello", 8),
        ("hello", 80),
    ],
)
def test_ticker_config_rejects_unbounded_or_unsupported_values(message: str, speed: int) -> None:
    with pytest.raises(ValueError):
        TickerConfig(message, speed=speed)


def test_ticker_builds_matching_bounded_device_and_browser_assets() -> None:
    assets = build_ticker_assets(
        TickerConfig("Lunch in five", speed=72, effect=TickerEffect.COLOR_WAVE)
    )

    assert assets.animation.startswith(b"bicycle0")
    assert assets.preview.startswith(b"RIFF")
    assert 24 <= assets.frame_count <= MAX_FRAMES


def test_invert_effect_changes_background_during_the_loop() -> None:
    frames = render_ticker_frames(
        TickerConfig(
            "Test",
            font_color="#FFFFFF",
            background_color="#000000",
            speed=72,
            effect=TickerEffect.INVERT,
        )
    )
    try:
        backgrounds = {frame.getpixel((0, 0)) for frame in frames}
    finally:
        for frame in frames:
            frame.close()

    assert backgrounds == {(0, 0, 0), (255, 255, 255)}
