from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.attempt import (
    OnlineAttemptAnswerInput,
    OnlineAttemptResultResponse,
    OnlineAttemptSessionResponse,
    OnlineAttemptStartRequest,
)
from app.services.attempt import AttemptService

router = APIRouter()


def _map_attempt_error(exc: Exception) -> HTTPException:
    detail = str(exc)
    lowered = detail.lower()
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    if "not found" in lowered:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.post(
    "/start",
    response_model=OnlineAttemptSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_role(UserRole.STUDENT)
async def start_attempt(
    payload: OnlineAttemptStartRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AttemptService(db)
    try:
        return service.start_online_attempt(payload.exam_id, current_user)
    except (PermissionError, ValueError) as exc:
        raise _map_attempt_error(exc)


@router.get("/{attempt_id}/current", response_model=OnlineAttemptSessionResponse)
@require_role(UserRole.STUDENT)
async def get_current_question(
    attempt_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AttemptService(db)
    try:
        return service.get_current_question(attempt_id, current_user)
    except (PermissionError, ValueError) as exc:
        raise _map_attempt_error(exc)


@router.put("/{attempt_id}/answers/{question_number}", response_model=OnlineAttemptSessionResponse)
@require_role(UserRole.STUDENT)
async def save_answer(
    attempt_id: UUID,
    question_number: int,
    payload: OnlineAttemptAnswerInput,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AttemptService(db)
    try:
        return service.save_answer(
            attempt_id,
            question_number,
            payload.selected_option,
            current_user,
        )
    except (PermissionError, ValueError) as exc:
        raise _map_attempt_error(exc)


@router.post("/{attempt_id}/next/{question_number}", response_model=OnlineAttemptSessionResponse)
@require_role(UserRole.STUDENT)
async def next_question(
    attempt_id: UUID,
    question_number: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AttemptService(db)
    try:
        return service.next_question(attempt_id, question_number, current_user)
    except (PermissionError, ValueError) as exc:
        raise _map_attempt_error(exc)


@router.post(
    "/{attempt_id}/previous/{question_number}",
    response_model=OnlineAttemptSessionResponse,
)
@require_role(UserRole.STUDENT)
async def previous_question(
    attempt_id: UUID,
    question_number: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AttemptService(db)
    try:
        return service.previous_question(attempt_id, question_number, current_user)
    except (PermissionError, ValueError) as exc:
        raise _map_attempt_error(exc)


@router.post("/{attempt_id}/submit", response_model=OnlineAttemptResultResponse)
@require_role(UserRole.STUDENT)
async def submit_attempt(
    attempt_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AttemptService(db)
    try:
        return service.submit_attempt(attempt_id, current_user)
    except (PermissionError, ValueError) as exc:
        raise _map_attempt_error(exc)


@router.get("/{attempt_id}/result", response_model=OnlineAttemptResultResponse)
@require_role(UserRole.STUDENT)
async def get_result(
    attempt_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AttemptService(db)
    try:
        return service.get_result(attempt_id, current_user)
    except (PermissionError, ValueError) as exc:
        raise _map_attempt_error(exc)
