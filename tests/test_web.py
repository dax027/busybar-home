from fastapi.testclient import TestClient

from busybar_home.client import DisplayOwnershipError
from busybar_home.clients.fake import FakeDeviceClient
from busybar_home.models import DeviceLog, DisplayScene
from busybar_home.web import create_web_app


def test_dashboard_page_and_state_load_without_hardware() -> None:
    fake = FakeDeviceClient()

    with TestClient(create_web_app(client=fake)) as client:
        page = client.get("/")
        logs_page = client.get("/logs")
        state = client.get("/api/dashboard")

    assert page.status_code == 200
    assert "Set the signal" in page.text
    assert logs_page.status_code == 200
    assert "Device" in logs_page.text
    assert state.status_code == 200
    assert state.json()["device_mode"] == "fake"


def test_scene_activation_uses_injected_fake() -> None:
    fake = FakeDeviceClient()

    with TestClient(create_web_app(client=fake)) as client:
        response = client.post("/api/presets/available/activate")

    assert response.status_code == 200
    assert response.json()["state"]["active_preset"] == "available"
    assert fake.scenes[0].front.text == "FREE"


def test_ticker_preview_is_generated_without_device_command() -> None:
    fake = FakeDeviceClient()
    request = {
        "message": "Back in ten",
        "font_color": "#FFFFFF",
        "background_color": "#111111",
        "speed": 48,
        "effect": "letter_flash",
    }

    with TestClient(create_web_app(client=fake)) as client:
        response = client.post("/api/ticker/preview", json=request)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert response.content.startswith(b"RIFF")
    assert fake.scenes == []


def test_ticker_deploy_uses_injected_fake_with_in_memory_animation() -> None:
    fake = FakeDeviceClient()
    request = {
        "message": "Build complete",
        "font_color": "#42FF88",
        "background_color": "#000000",
        "speed": 72,
        "effect": "clean",
    }

    with TestClient(create_web_app(client=fake)) as client:
        response = client.post("/api/ticker/deploy", json=request)

    assert response.status_code == 200
    assert response.json()["state"]["active_preset"] == "custom-ticker"
    assert len(fake.scenes) == 1
    animation = fake.scenes[0].front_animation
    assert animation is not None
    assert animation.path == "custom_ticker.anim"
    assert animation.stock is False
    assert animation.payload is not None
    assert animation.payload.startswith(b"bicycle0")


def test_ticker_rejects_invalid_color_without_device_command() -> None:
    fake = FakeDeviceClient()

    with TestClient(create_web_app(client=fake)) as client:
        response = client.post(
            "/api/ticker/deploy",
            json={
                "message": "Hello",
                "font_color": "red",
                "background_color": "#000000",
                "speed": 32,
                "effect": "clean",
            },
        )

    assert response.status_code == 422
    assert fake.scenes == []


def test_device_status_uses_injected_fake() -> None:
    fake = FakeDeviceClient(battery_percent=61, power_state="discharging")

    with TestClient(create_web_app(client=fake)) as client:
        status = client.get("/api/device/status")

    assert status.status_code == 200
    assert status.json()["battery_percent"] == 61
    assert status.json()["power_state"] == "discharging"


def test_front_screen_preview_uses_injected_fake_and_returns_png() -> None:
    fake = FakeDeviceClient()

    with TestClient(create_web_app(client=fake)) as client:
        response = client.get("/api/device/screen/front")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.headers["cache-control"] == "no-store"
    assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
    assert fake.screen_capture_count == 1


def test_front_screen_stream_uses_injected_fake_and_returns_raw_rgb() -> None:
    fake = FakeDeviceClient()

    with (
        TestClient(create_web_app(client=fake)) as client,
        client.websocket_connect("/ws/device/screen/front") as websocket,
    ):
        frame = websocket.receive_bytes()

    assert frame == bytes((17, 17, 17)) * (72 * 16)
    assert fake.screen_capture_count == 1


def test_device_log_capture_uses_injected_fake_only_when_requested() -> None:
    fake = FakeDeviceClient(log_content="device log\n")

    with TestClient(create_web_app(client=fake)) as client:
        assert fake.log_capture_count == 0
        response = client.post("/api/device/logs/capture")

    assert response.status_code == 200
    assert response.json() == {
        "path": "/ext/log.txt",
        "content": "device log\n",
        "size_bytes": 11,
        "truncated": False,
    }
    assert fake.log_capture_count == 1


class UnavailableStatusClient(FakeDeviceClient):
    def snapshot(self):
        raise RuntimeError("secret device detail")


def test_device_status_failure_is_sanitized() -> None:
    with TestClient(create_web_app(client=UnavailableStatusClient())) as client:
        status = client.get("/api/device/status")

    assert status.status_code == 502
    assert status.json()["detail"] == "Device status unavailable"
    assert "secret" not in status.text


class UnavailableLogsClient(FakeDeviceClient):
    def capture_logs(self) -> DeviceLog:
        raise RuntimeError("secret device detail")


def test_device_log_failure_is_sanitized() -> None:
    with TestClient(create_web_app(client=UnavailableLogsClient())) as client:
        response = client.post("/api/device/logs/capture")

    assert response.status_code == 502
    assert response.json()["detail"] == "Device log capture failed"
    assert "secret" not in response.text


class UnavailableScreenClient(FakeDeviceClient):
    def front_screen_frame(self):
        raise RuntimeError("secret device detail")


def test_front_screen_failure_is_sanitized() -> None:
    with TestClient(create_web_app(client=UnavailableScreenClient())) as client:
        response = client.get("/api/device/screen/front")

    assert response.status_code == 502
    assert response.json()["detail"] == "Device screen unavailable"
    assert "secret" not in response.text


def test_dynamic_toggle_does_not_send_device_command() -> None:
    fake = FakeDeviceClient()

    with TestClient(create_web_app(client=fake)) as client:
        response = client.put("/api/dynamic", json={"enabled": True})

    assert response.status_code == 200
    assert response.json()["dynamic_enabled"] is True
    assert fake.scenes == []


class OwnedDisplayClient(FakeDeviceClient):
    def show_scene(self, scene: DisplayScene) -> None:
        raise DisplayOwnershipError("owned")


def test_display_owner_conflict_returns_actionable_message() -> None:
    with TestClient(create_web_app(client=OwnedDisplayClient())) as client:
        response = client.post("/api/presets/focus/activate")

    assert response.status_code == 409
    assert "Close it" in response.json()["detail"]
