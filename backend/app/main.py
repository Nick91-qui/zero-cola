from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.api import router as api_router
from app.core.config import settings


def configure_omr_upload_mount(
    application: FastAPI,
    *,
    backend: str,
    local_dir: str,
) -> None:
    """Expose local OMR uploads only when the configured backend stores files on disk."""
    if backend.lower().strip() not in {"", "local"}:
        return

    upload_root = Path(local_dir).expanduser().resolve().parent
    upload_root.mkdir(parents=True, exist_ok=True)
    application.mount("/uploads", StaticFiles(directory=str(upload_root)), name="uploads")


app = FastAPI(title=settings.app_name)
configure_omr_upload_mount(
    app,
    backend=settings.omr_storage_backend,
    local_dir=settings.omr_storage_local_dir,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "ok"}
