from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.exam import (
    ExamCreate,
    ExamDetailResponse,
    ExamResponse,
    ExamStatisticsResponse,
    ExamUpdate,
)
from app.services.exam import ExamService

router = APIRouter()


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def create_exam(
    exam_in: ExamCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ExamService(db)
    return service.create_exam(exam_in, teacher_id=current_user.id)


@router.get("", response_model=List[ExamResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def list_exams(
    class_id: Optional[str] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ExamService(db)
    teacher_id = current_user.id if current_user.role == UserRole.TEACHER else None
    return service.list_exams(teacher_id=teacher_id, class_id=class_id)


@router.get("/{exam_id}", response_model=ExamDetailResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN, UserRole.STUDENT)
async def get_exam(
    exam_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ExamService(db)
    exam = service.get_exam(exam_id)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam {exam_id} not found.",
        )
    return exam


@router.patch("/{exam_id}", response_model=ExamResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def update_exam(
    exam_id: UUID,
    update_in: ExamUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ExamService(db)
    exam = service.update_exam(exam_id, update_in)
    if not exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam {exam_id} not found.",
        )
    return exam


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def delete_exam(
    exam_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ExamService(db)
    success = service.soft_delete_exam(exam_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exam {exam_id} not found.",
        )
    return None


@router.get("/{exam_id}/statistics", response_model=ExamStatisticsResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def get_exam_statistics(
    exam_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ExamService(db)
    try:
        return service.get_exam_statistics(exam_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{exam_id}/export/pdf")
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def export_exam_pdf(
    exam_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ExamService(db)
    try:
        pdf_bytes = service.export_exam_pdf(exam_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="relatorio_avaliacao_{exam_id}.pdf"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/{exam_id}/export/xlsx")
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def export_exam_xlsx(
    exam_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ExamService(db)
    try:
        xlsx_bytes = service.export_exam_xlsx(exam_id)
        return Response(
            content=xlsx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="relatorio_avaliacao_{exam_id}.xlsx"'
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
