from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.exams import router as exams_router
from app.api.routes.health import router as health_router
from app.api.routes.omr import router as omr_router
from app.api.routes.skills import router as skills_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(omr_router, prefix="/omr", tags=["omr"])
router.include_router(exams_router, prefix="/exams", tags=["exams"])
router.include_router(skills_router, prefix="/skills", tags=["skills"])

