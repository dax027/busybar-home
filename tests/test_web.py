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


def test_device_status_uses_injected_fake() -> None:
    fake = FakeDeviceClient(battery_percent=61, power_state="discharging")

    with TestClient(create_web_app(client=fake)) as client:
        status = client.get("/api/device/status")

    assert status.status_code == 200
    assert status.json()["battery_percent"] == 61
    assert status.json()["power_state"] == "discharging"


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
