"""Local web dashboard for choosing BUSY Bar display scenes."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from busybar_home.client import DeviceClient, DisplayOwnershipError
from busybar_home.config import Settings
from busybar_home.dashboard import DashboardController
from busybar_home.factory import create_client

STATIC_DIR = Path(__file__).with_name("static")


class DynamicUpdate(BaseModel):
    """Request body for the automatic-update switch."""

    enabled: bool


def create_web_app(
    settings: Settings | None = None,
    *,
    client: DeviceClient | None = None,
) -> FastAPI:
    """Create the dashboard app with an injectable, hardware-free client boundary."""
    resolved_settings = settings or Settings.from_env()
    device_client = client or create_client(resolved_settings)
    device_mode = "fake" if client is not None else resolved_settings.client_kind.value
    controller = DashboardController(device_client, device_mode=device_mode)

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        controller.close()

    app = FastAPI(
        title="BUSY Bar Home",
        description="A local-only visual control surface for BUSY Bar scenes.",
        lifespan=lifespan,
    )
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/dashboard")
    def dashboard_state() -> dict[str, object]:
        return controller.state()

    @app.post("/api/presets/{preset_id}/activate")
    def activate_preset(preset_id: str) -> dict[str, object]:
        try:
            state, snapshot = controller.activate(preset_id)
        except KeyError as error:
            raise HTTPException(status_code=404, detail="Unknown scene preset") from error
        except DisplayOwnershipError as error:
            raise HTTPException(
                status_code=409,
                detail="Another BUSY app owns the display. Close it and try again.",
            ) from error
        except Exception as error:
            raise HTTPException(status_code=502, detail="Device command failed") from error
        return {"state": state, "device": asdict(snapshot)}

    @app.put("/api/dynamic")
    def update_dynamic(update: DynamicUpdate) -> dict[str, object]:
        return controller.set_dynamic(update.enabled)

    return app


def main() -> None:
    """Run the dashboard on the configured local interface."""
    import uvicorn

    settings = Settings.from_env()
    uvicorn.run(
        create_web_app(settings),
        host=settings.web_host,
        port=settings.web_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
