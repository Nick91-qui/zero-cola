from fastapi import APIRouter

from app.api.routes.attempts import router as attempts_router
from app.api.routes.audit_logs import router as audit_logs_router
from app.api.routes.auth import router as auth_router
from app.api.routes.classes import router as classes_router
from app.api.routes.consents import router as consents_router
from app.api.routes.questions import router as questions_router
from app.api.routes.exams import router as exams_router
from app.api.routes.health import router as health_router
from app.api.routes.omr import router as omr_router
from app.api.routes.privacy import router as privacy_router
from app.api.routes.security_events import router as security_events_router
from app.api.routes.skills import router as skills_router
from app.api.routes.users import router as users_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(omr_router, prefix="/omr", tags=["omr"])
router.include_router(attempts_router, prefix="/attempts", tags=["attempts"])
router.include_router(exams_router, prefix="/exams", tags=["exams"])
router.include_router(questions_router, prefix="/questions", tags=["questions"])
router.include_router(skills_router, prefix="/skills", tags=["skills"])
router.include_router(classes_router, tags=["classes"])
router.include_router(users_router, tags=["users"])
router.include_router(audit_logs_router, tags=["audit-logs"])
router.include_router(consents_router, tags=["consents"])
router.include_router(privacy_router, tags=["privacy"])
router.include_router(security_events_router, tags=["security-events"])
