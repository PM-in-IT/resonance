from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings

STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> FastAPI:
    application = FastAPI(title="Resonance API", version="0.1.0")
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.get("/", include_in_schema=False)
    def upload_page() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    application.include_router(api_router, prefix=settings.api_v1_prefix)
    return application


app = create_app()
