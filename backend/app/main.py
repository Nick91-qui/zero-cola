from fastapi import FastAPI

from app.api.api import router as api_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": settings.app_name, "status": "ok"}
