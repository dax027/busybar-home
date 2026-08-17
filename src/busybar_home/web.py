"""Local web dashboard for choosing BUSY Bar display scenes."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from pydantic import BaseModel, Field

from busybar_home.client import DeviceClient, DisplayOwnershipError
from busybar_home.config import Settings
from busybar_home.dashboard import DashboardController
from busybar_home.factory import create_client
from busybar_home.ticker import (
    MAX_MESSAGE_LENGTH,
    MAX_SPEED,
    MIN_SPEED,
    TickerConfig,
    TickerEffect,
    build_ticker_assets,
)

STATIC_DIR = Path(__file__).with_name("static")


class DynamicUpdate(BaseModel):
    """Request body for the automatic-update switch."""

    enabled: bool


class TickerRequest(BaseModel):
    """Bounded custom ticker controls accepted from the local dashboard."""

    message: str = Field(min_length=1, max_length=MAX_MESSAGE_LENGTH)
    font_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    speed: int = Field(ge=MIN_SPEED, le=MAX_SPEED)
    effect: TickerEffect

    def to_config(self) -> TickerConfig:
        """Convert transport validation into the application-owned model."""
        return TickerConfig(**self.model_dump())


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

    @app.get("/logs", include_in_schema=False)
    def logs_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "logs.html")

    @app.get("/api/dashboard")
    def dashboard_state() -> dict[str, object]:
        return controller.state()

    @app.get("/api/device/status")
    def device_status() -> dict[str, object]:
        try:
            return asdict(controller.device_status())
        except Exception as error:
            raise HTTPException(status_code=502, detail="Device status unavailable") from error

    @app.get("/api/device/screen/front")
    def front_screen() -> Response:
        try:
            frame = controller.front_screen_frame()
            output = BytesIO()
            Image.frombytes("RGB", (frame.width, frame.height), frame.rgb).save(
                output,
                format="PNG",
                optimize=True,
            )
        except Exception as error:
            raise HTTPException(status_code=502, detail="Device screen unavailable") from error
        return Response(
            content=output.getvalue(),
            media_type="image/png",
            headers={"Cache-Control": "no-store"},
        )

    @app.websocket("/ws/device/screen/front")
    async def stream_front_screen(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            async for frame in controller.stream_front_screen_frames():
                await websocket.send_bytes(frame.rgb)
        except WebSocketDisconnect:
            return
        except Exception:
            try:
                await websocket.close(code=1011, reason="Device screen unavailable")
            except RuntimeError:
                return

    @app.post("/api/device/logs/capture")
    def capture_device_logs() -> dict[str, object]:
        try:
            return asdict(controller.capture_device_logs())
        except Exception as error:
            raise HTTPException(status_code=502, detail="Device log capture failed") from error

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

    @app.post("/api/ticker/preview")
    def preview_ticker(request: TickerRequest) -> Response:
        try:
            assets = build_ticker_assets(request.to_config())
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return Response(
            content=assets.preview,
            media_type="image/webp",
            headers={"Cache-Control": "no-store"},
        )

    @app.post("/api/ticker/deploy")
    def deploy_ticker(request: TickerRequest) -> dict[str, object]:
        try:
            state, snapshot = controller.activate_ticker(request.to_config())
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except DisplayOwnershipError as error:
            raise HTTPException(
                status_code=409,
                detail="Another BUSY app owns the display. Close it and try again.",
            ) from error
        except Exception as error:
            raise HTTPException(status_code=502, detail="Ticker deployment failed") from error
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
