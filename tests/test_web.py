from fastapi.testclient import TestClient

from busybar_home.client import DisplayOwnershipError
from busybar_home.clients.fake import FakeDeviceClient
from busybar_home.models import DisplayScene
from busybar_home.web import create_web_app


def test_dashboard_page_and_state_load_without_hardware() -> None:
    fake = FakeDeviceClient()

    with TestClient(create_web_app(client=fake)) as client:
        page = client.get("/")
        state = client.get("/api/dashboard")

    assert page.status_code == 200
    assert "Set the signal" in page.text
    assert state.status_code == 200
    assert state.json()["device_mode"] == "fake"


def test_scene_activation_uses_injected_fake() -> None:
    fake = FakeDeviceClient()

    with TestClient(create_web_app(client=fake)) as client:
        response = client.post("/api/presets/available/activate")

    assert response.status_code == 200
    assert response.json()["state"]["active_preset"] == "available"
    assert fake.scenes[0].front.text == "FREE"


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
