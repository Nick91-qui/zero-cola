from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.class_ import ClassStudent
from app.models.enums import UserRole
from app.schemas.class_ import (
    ClassCreate,
    ClassStudentBulkTransferCreate,
    ClassDetailResponse,
    ClassResponse,
    ClassStudentCreate,
    ClassStudentResponse,
    ClassStudentTransferCreate,
    ClassStudentBulkTransferResponse,
    ClassStudentTransferResponse,
    ClassTeacherCreate,
    ClassTeacherResponse,
    ClassUpdate,
)
from app.services.class_service import ClassService

router = APIRouter()


def _class_response_payload(db: Session, class_obj):
    student_count = (
        db.query(ClassStudent)
        .filter(
            ClassStudent.class_id == class_obj.id,
            ClassStudent.is_active.is_(True),
        )
        .count()
    )
    return {
        "id": class_obj.id,
        "teacher_id": class_obj.teacher_id,
        "name": class_obj.name,
        "academic_period": class_obj.academic_period,
        "description": class_obj.description,
        "is_active": class_obj.is_active,
        "archived_at": class_obj.archived_at,
        "student_count": student_count,
        "created_at": class_obj.created_at,
        "updated_at": class_obj.updated_at,
    }


@router.post("/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
@require_role(UserRole.ADMIN)
async def create_class(
    class_in: ClassCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        class_obj = service.create_class(
            current_user=current_user,
            name=class_in.name,
            description=class_in.description,
            academic_period=class_in.academic_period,
            teacher_id=class_in.teacher_id,
        )
        return _class_response_payload(db, class_obj)
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
    classes = service.list_classes(current_user=current_user, include_archived=include_archived)
    return [_class_response_payload(db, class_obj) for class_obj in classes]


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
    teachers = service.list_teachers(
        class_id=class_obj.id,
        current_user=current_user,
        include_archived=True,
    )
    payload = _class_response_payload(db, class_obj)
    payload["memberships"] = [
        ClassStudentResponse.model_validate(m).model_dump() for m in memberships
    ]
    payload["teachers"] = [ClassTeacherResponse.model_validate(t).model_dump() for t in teachers]
    return ClassDetailResponse.model_validate(payload)


@router.patch("/classes/{class_id}", response_model=ClassResponse)
@require_role(UserRole.ADMIN)
async def update_class(
    class_id: UUID,
    class_in: ClassUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        class_obj = service.update_class(
            class_id=class_id,
            current_user=current_user,
            name=class_in.name,
            description=class_in.description,
        )
        return _class_response_payload(db, class_obj)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/classes/{class_id}/archive", response_model=ClassResponse)
@require_role(UserRole.ADMIN)
async def archive_class(
    class_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        class_obj = service.archive_class(class_id=class_id, current_user=current_user)
        return _class_response_payload(db, class_obj)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/classes/{class_id}/students",
    response_model=list[ClassStudentResponse],
    status_code=status.HTTP_201_CREATED,
)
@require_role(UserRole.ADMIN)
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
            status.HTTP_409_CONFLICT
            if "already a member" in message or "already has an active class" in message
            else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(status_code=status_code, detail=message)


@router.post(
    "/classes/{class_id}/teachers",
    response_model=list[ClassTeacherResponse],
    status_code=status.HTTP_201_CREATED,
)
@require_role(UserRole.ADMIN)
async def add_teachers(
    class_id: UUID,
    payload: ClassTeacherCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        return service.add_teachers(
            class_id=class_id,
            current_user=current_user,
            teacher_ids=payload.teacher_ids,
        )
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_409_CONFLICT
        if "already associated" not in message:
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=message)


@router.get("/classes/{class_id}/teachers", response_model=list[ClassTeacherResponse])
@require_role(UserRole.ADMIN)
async def list_teachers(
    class_id: UUID,
    include_archived: bool = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        return service.list_teachers(
            class_id=class_id,
            current_user=current_user,
            include_archived=include_archived,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/classes/{class_id}/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_role(UserRole.ADMIN)
async def remove_teacher(
    class_id: UUID,
    teacher_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        service.remove_teacher(class_id=class_id, teacher_id=teacher_id, current_user=current_user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return None


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
@require_role(UserRole.ADMIN)
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


@router.post(
    "/classes/{class_id}/students/{student_id}/transfer",
    response_model=ClassStudentTransferResponse,
)
@require_role(UserRole.ADMIN)
async def transfer_student(
    class_id: UUID,
    student_id: UUID,
    payload: ClassStudentTransferCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        result = service.transfer_student(
            source_class_id=class_id,
            target_class_id=payload.target_class_id,
            student_id=student_id,
            current_user=current_user,
        )
        return ClassStudentTransferResponse.model_validate(result)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_409_CONFLICT
        if "not found" in message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "archived" in message.lower() or "differ" in message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message)


@router.post(
    "/classes/{class_id}/students/transfer-all",
    response_model=ClassStudentBulkTransferResponse,
)
@require_role(UserRole.ADMIN)
async def transfer_all_students(
    class_id: UUID,
    payload: ClassStudentBulkTransferCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    try:
        result = service.transfer_students(
            source_class_id=class_id,
            target_class_id=payload.target_class_id,
            current_user=current_user,
        )
        return ClassStudentBulkTransferResponse.model_validate(result)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_409_CONFLICT
        if "not found" in message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        elif "archived" in message.lower() or "differ" in message.lower():
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=message)


@router.get("/me/classes", response_model=list[ClassResponse])
async def my_classes(
    include_archived: bool = False,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ClassService(db)
    classes = service.list_my_classes(current_user=current_user, include_archived=include_archived)
    return [_class_response_payload(db, class_obj) for class_obj in classes]
