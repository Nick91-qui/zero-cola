from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.class_ import (
    ClassCreate,
    ClassDetailResponse,
    ClassResponse,
    ClassStudentCreate,
    ClassStudentResponse,
    ClassUpdate,
)
from app.services.class_service import ClassService

router = APIRouter()


@router.post("/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def create_class(
    class_in: ClassCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        return service.create_class(
            current_user=current_user,
            name=class_in.name,
            description=class_in.description,
            teacher_id=class_in.teacher_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/classes", response_model=list[ClassResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def list_classes(
    include_archived: bool = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    return service.list_classes(current_user=current_user, include_archived=include_archived)


@router.get("/classes/{class_id}", response_model=ClassDetailResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def get_class(
    class_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        class_obj = service.get_class(class_id=class_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    memberships = service.list_students(
        class_id=class_obj.id,
        current_user=current_user,
        include_archived=True,
    )
    payload = ClassResponse.model_validate(class_obj).model_dump()
    payload["memberships"] = [
        ClassStudentResponse.model_validate(m).model_dump() for m in memberships
    ]
    return ClassDetailResponse.model_validate(payload)


@router.patch("/classes/{class_id}", response_model=ClassResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def update_class(
    class_id: UUID,
    class_in: ClassUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        return service.update_class(
            class_id=class_id,
            current_user=current_user,
            name=class_in.name,
            description=class_in.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/classes/{class_id}/archive", response_model=ClassResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def archive_class(
    class_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        return service.archive_class(class_id=class_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/classes/{class_id}/students",
    response_model=list[ClassStudentResponse],
    status_code=status.HTTP_201_CREATED,
)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def add_students(
    class_id: UUID,
    payload: ClassStudentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        return service.add_students(
            class_id=class_id, current_user=current_user, student_ids=payload.student_ids
        )
    except ValueError as exc:
        message = str(exc)
        status_code = (
            status.HTTP_409_CONFLICT if "already a member" in message else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(status_code=status_code, detail=message)


@router.get("/classes/{class_id}/students", response_model=list[ClassStudentResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def list_students(
    class_id: UUID,
    include_archived: bool = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        return service.list_students(
            class_id=class_id,
            current_user=current_user,
            include_archived=include_archived,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/classes/{class_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def remove_student(
    class_id: UUID,
    student_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        service.remove_student(class_id=class_id, student_id=student_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return None


@router.get("/me/classes", response_model=list[ClassResponse])
async def my_classes(
    include_archived: bool = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    return service.list_my_classes(current_user=current_user, include_archived=include_archived)
