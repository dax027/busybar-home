"""State and presets for the local dashboard."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from threading import Lock

from busybar_home.client import DeviceClient
from busybar_home.models import (
    DeviceLog,
    DeviceSnapshot,
    DisplayAnimation,
    DisplayFrame,
    DisplayScene,
    FrontStyle,
)
from busybar_home.ticker import TickerConfig, build_ticker_scene


@dataclass(frozen=True, slots=True)
class ScenePreset:
    """A named, selectable scene with UI metadata."""

    id: str
    label: str
    description: str
    scene: DisplayScene
    front_preview: str | None = None


SCENE_PRESETS = (
    ScenePreset(
        id="focus",
        label="Deep focus",
        description="A pencil works steadily through a focused task list.",
        scene=DisplayScene.from_text(
            "Deep focus",
            "BUSY",
            "DEEP FOCUS",
            "#FF5C35",
            "One task. No inbox.",
            FrontStyle.STATUS,
            DisplayAnimation("busy_checklist_v2_72x16.anim", stock=False),
        ),
        front_preview="/static/animations/busy_checklist_v2_72x16.webp",
    ),
    ScenePreset(
        id="focused",
        label="Focused",
        description="Scattered distractions collapse into a precise focus lock.",
        scene=DisplayScene.from_text(
            "Focused",
            "FOCUSED",
            "FLOW STATE",
            "#3FE7FF",
            "Hold the thread.",
            FrontStyle.STATUS,
            DisplayAnimation("focused_lock_72x16.anim", stock=False),
        ),
        front_preview="/static/animations/focused_lock_72x16.webp",
    ),
    ScenePreset(
        id="concentrating",
        label="Concentrating",
        description="A flashing PET-scan brain fires into a neural text marquee.",
        scene=DisplayScene.from_text(
            "Concentrating",
            "CONCENTRATING",
            "DEEP WORK",
            "#FFC857",
            "Working it through.",
            FrontStyle.STATUS,
            DisplayAnimation("concentrating_neural_72x16.anim", stock=False),
        ),
        front_preview="/static/animations/concentrating_neural_72x16.webp",
    ),
    ScenePreset(
        id="meeting",
        label="In a meeting",
        description="A live microphone and level meter show that a call is active.",
        scene=DisplayScene.from_text(
            "In a meeting",
            "ON A CALL",
            "MEETING MODE",
            "#EF3D77",
            "Capture decisions.",
            FrontStyle.STATUS,
            DisplayAnimation("on_a_call_mic_72x16.anim", stock=False),
        ),
        front_preview="/static/animations/on_a_call_mic_72x16.webp",
    ),
    ScenePreset(
        id="available",
        label="Available",
        description="A mint-green neon FREE sign flickers warmly to life.",
        scene=DisplayScene.from_text(
            "Available",
            "FREE",
            "RESET WINDOW",
            "#47D18C",
            "Clear quick replies.",
            FrontStyle.STATUS,
            DisplayAnimation("available_neon_72x16.anim", stock=False),
        ),
        front_preview="/static/animations/available_neon_72x16.webp",
    ),
    ScenePreset(
        id="wife",
        label="I love my wife",
        description="Use when you're in trouble.",
        scene=DisplayScene.from_text(
            "I love my wife",
            "I ♥ MY WIFE",
            "LUCKY HUSBAND",
            "#FF477E",
            "Tell her. Show her.",
            FrontStyle.STATUS,
            DisplayAnimation("love_my_wife_72x16.anim", stock=False),
        ),
        front_preview="/static/animations/love_my_wife_72x16.webp",
    ),
    ScenePreset(
        id="away",
        label="Stepped away",
        description="A ticking analog clock keeps a bold BRB status moving gently.",
        scene=DisplayScene.from_text(
            "Stepped away",
            "BRB",
            "SHORT BREAK",
            "#FFBF47",
            "Pause. Reset. Return.",
            FrontStyle.STATUS,
            DisplayAnimation("away_brb_clock_72x16.anim", stock=False),
        ),
        front_preview="/static/animations/away_brb_clock_72x16.webp",
    ),
    ScenePreset(
        id="low-social-battery",
        label="Low social battery",
        description="Signal that your people-energy needs time to recharge.",
        scene=DisplayScene.from_text(
            "Low social battery",
            "LOW SOCIAL",
            "SOCIAL BATTERY",
            "#FF4D4D",
            "Quiet mode. Recharge.",
            FrontStyle.LOW_BATTERY,
            DisplayAnimation("low_social_battery_72x16.anim"),
        ),
        front_preview="/static/animations/low_social_battery_72x16.webp",
    ),
    ScenePreset(
        id="coding",
        label="Coding",
        description="Drop into a focused build-and-debug loop.",
        scene=DisplayScene.from_text(
            "Coding",
            "CODING",
            "BUILD MODE",
            "#42FF88",
            "Write. Run. Refine.",
            FrontStyle.TERMINAL,
            DisplayAnimation("coding_72x16.anim"),
        ),
        front_preview="/static/animations/coding_72x16.webp",
    ),
    ScenePreset(
        id="gaming",
        label="Gaming",
        description="A pixel controller powers up into a shifting arcade wordmark.",
        scene=DisplayScene.from_text(
            "Gaming",
            "GAMING",
            "PLAYER ONE",
            "#8B5CF6",
            "Relax. Play. Recharge.",
            FrontStyle.STATUS,
            DisplayAnimation("gaming_arcade_72x16.anim", stock=False),
        ),
        front_preview="/static/animations/gaming_arcade_72x16.webp",
    ),
    ScenePreset(
        id="hacking",
        label="Hacking",
        description="A masked cyberpunk reveal that glitches into a neon wordmark.",
        scene=DisplayScene.from_text(
            "Hacking",
            "HACKING",
            "CYBER OPS",
            "#FF2DB2",
            "Map. Probe. Learn.",
            FrontStyle.CYBERPUNK,
            DisplayAnimation("hacking_fawkes_72x16.anim", stock=False),
        ),
        front_preview="/static/animations/hacking_fawkes_72x16.webp",
    ),
    ScenePreset(
        id="daydreaming",
        label="Daydreaming",
        description="A soft sky-and-cloud signal for letting ideas wander.",
        scene=DisplayScene.from_text(
            "Daydreaming",
            "DAYDREAMING",
            "WANDER MODE",
            "#69C6FF",
            "Let ideas drift.",
            FrontStyle.DAYDREAM,
            DisplayAnimation("daydreaming_72x16.anim", stock=False),
        ),
        front_preview="/static/animations/daydreaming_72x16.webp",
    ),
)


class DashboardController:
    """Thread-safe local state around one device client."""

    def __init__(
        self,
        client: DeviceClient,
        *,
        device_mode: str = "fake",
    ) -> None:
        self._client = client
        self._device_mode = device_mode
        self._dynamic_enabled = False
        self._active_preset: str | None = None
        self._lock = Lock()

    def state(self) -> dict[str, object]:
        with self._lock:
            return self._state_unlocked()

    def activate(self, preset_id: str) -> tuple[dict[str, object], DeviceSnapshot]:
        preset = next((item for item in SCENE_PRESETS if item.id == preset_id), None)
        if preset is None:
            raise KeyError(preset_id)
        with self._lock:
            self._client.show_scene(preset.scene)
            snapshot = self._client.snapshot()
            self._active_preset = preset.id
            return self._state_unlocked(), snapshot

    def device_status(self) -> DeviceSnapshot:
        with self._lock:
            return self._client.snapshot()

    def front_screen_frame(self) -> DisplayFrame:
        with self._lock:
            return self._client.front_screen_frame()

    def stream_front_screen_frames(self) -> AsyncIterator[DisplayFrame]:
        return self._client.stream_front_screen_frames()

    def activate_ticker(self, config: TickerConfig) -> tuple[dict[str, object], DeviceSnapshot]:
        """Render and deploy one user-configured ticker."""
        scene = build_ticker_scene(config)
        with self._lock:
            self._client.show_scene(scene)
            snapshot = self._client.snapshot()
            self._active_preset = "custom-ticker"
            return self._state_unlocked(), snapshot

    def capture_device_logs(self) -> DeviceLog:
        with self._lock:
            return self._client.capture_logs()

    def set_dynamic(self, enabled: bool) -> dict[str, object]:
        with self._lock:
            self._dynamic_enabled = enabled
            return self._state_unlocked()

    def close(self) -> None:
        self._client.close()

    def _state_unlocked(self) -> dict[str, object]:
        return {
            "dynamic_enabled": self._dynamic_enabled,
            "active_preset": self._active_preset,
            "device_mode": self._device_mode,
            "presets": [
                {
                    "id": preset.id,
                    "label": preset.label,
                    "description": preset.description,
                    "front": {
                        "text": preset.scene.front.text,
                        "color": preset.scene.front.color,
                    },
                    "back": {
                        "text": preset.scene.back.text,
                        "color": preset.scene.back.color,
                    },
                    "rear_cue": preset.scene.rear_cue,
                    "front_style": preset.scene.front_style.value,
                    "front_animated": preset.scene.front_animation is not None,
                    "front_preview": preset.front_preview,
                }
                for preset in SCENE_PRESETS
            ],
        }
