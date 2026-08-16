"""State and presets for the local dashboard."""

from dataclasses import dataclass
from threading import Lock

from busybar_home.client import DeviceClient
from busybar_home.models import DeviceLog, DeviceSnapshot, DisplayScene, FrontStyle


@dataclass(frozen=True, slots=True)
class ScenePreset:
    """A named, selectable scene with UI metadata."""

    id: str
    label: str
    description: str
    scene: DisplayScene


SCENE_PRESETS = (
    ScenePreset(
        id="focus",
        label="Deep focus",
        description="Protect a block of uninterrupted work.",
        scene=DisplayScene.from_text(
            "Deep focus",
            "BUSY",
            "DEEP FOCUS",
            "#FF5C35",
            "One task. No inbox.",
        ),
    ),
    ScenePreset(
        id="meeting",
        label="In a meeting",
        description="Let people know you are on a call.",
        scene=DisplayScene.from_text(
            "In a meeting",
            "ON A CALL",
            "MEETING MODE",
            "#EF3D77",
            "Capture decisions.",
        ),
    ),
    ScenePreset(
        id="available",
        label="Available",
        description="Make it clear that interruptions are welcome.",
        scene=DisplayScene.from_text(
            "Available",
            "FREE",
            "RESET WINDOW",
            "#47D18C",
            "Clear quick replies.",
        ),
    ),
    ScenePreset(
        id="away",
        label="Stepped away",
        description="Show a calm, temporary away state.",
        scene=DisplayScene.from_text(
            "Stepped away",
            "AWAY",
            "PAUSE",
            "#FFBF47",
            "Reset when I return.",
        ),
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
        ),
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
        ),
    ),
    ScenePreset(
        id="hacking",
        label="Hacking",
        description="A neon cyber-ops signal with a chromatic glitch edge.",
        scene=DisplayScene.from_text(
            "Hacking",
            "HACKING",
            "CYBER OPS",
            "#FF2DB2",
            "Map. Probe. Learn.",
            FrontStyle.CYBERPUNK,
        ),
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
        ),
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
                }
                for preset in SCENE_PRESETS
            ],
        }
