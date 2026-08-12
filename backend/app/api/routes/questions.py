from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.repositories.question import QuestionRepository
from app.schemas.exam import QuestionCreate, QuestionResponse, QuestionUpdate

router = APIRouter()


@router.get("", response_model=list[QuestionResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def list_questions(
    q: str = "",
    skill_id: UUID | None = None,
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = QuestionRepository(db)
    owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
    questions = repo.get_all(
        query_text=q,
        skill_id=skill_id,
        include_inactive=include_inactive,
        owner_id=owner_id,
        skip=skip,
        limit=limit,
    )
    return [QuestionResponse.model_validate(question).model_dump() for question in questions]


@router.get("/{question_id}", response_model=QuestionResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def get_question(
    question_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = QuestionRepository(db)
    owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
    question = repo.get_by_id(question_id, owner_id=owner_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found.",
        )
    return QuestionResponse.model_validate(question).model_dump()


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def create_question(
    question_in: QuestionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = QuestionRepository(db)
    try:
        question = repo.create(question_in, created_by=current_user.id)
        return QuestionResponse.model_validate(question).model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch("/{question_id}", response_model=QuestionResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def update_question(
    question_id: UUID,
    question_in: QuestionUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = QuestionRepository(db)
    owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
    question = repo.get_by_id(question_id, include_inactive=True, owner_id=owner_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found.",
        )
    try:
        updated = repo.update(question, question_in, updated_by=current_user.id)
        return QuestionResponse.model_validate(updated).model_dump()
    except ValueError as exc:
        detail = str(exc)
        status_code = (
            status.HTTP_404_NOT_FOUND if "not found" in detail.lower() else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=detail)


@router.delete("/{question_id}", response_model=QuestionResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def deactivate_question(
    question_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = QuestionRepository(db)
    owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
    question = repo.get_by_id(question_id, include_inactive=True, owner_id=owner_id)
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found.",
        )
    try:
        updated = repo.deactivate(question)
        return QuestionResponse.model_validate(updated).model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
