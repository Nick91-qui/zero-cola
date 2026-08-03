from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.omr import (
    GradeResponse,
    OMRBatchUploadResponse,
    OMRScanResponse,
    OMRScanUpdate,
    OMRTemplateCreate,
    OMRTemplateResponse,
)
from app.services.omr import OMRService

router = APIRouter()


@router.post("/templates", response_model=OMRTemplateResponse, status_code=status.HTTP_201_CREATED)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def create_template(
    template_in: OMRTemplateCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Creates a new OMR answer sheet template."""
    service = OMRService(db)
    return service.create_template(template_in, teacher_id=current_user.id)


@router.get("/templates", response_model=list[OMRTemplateResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def list_templates(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists OMR templates."""
    service = OMRService(db)
    owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
    return service.list_templates(owner_id=owner_id)


@router.get("/templates/{template_id}", response_model=OMRTemplateResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def get_template(
    template_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Gets a single OMR template."""
    service = OMRService(db)
    owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
    template = service.get_template(template_id, owner_id=owner_id)
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OMR Template with ID {template_id} not found.",
        )
    return template


@router.get("/templates/{template_id}/pdf")
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def get_template_pdf(
    template_id: UUID,
    student_code: str = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generates the PDF for a specific OMR template, with optional pre-filled student code."""
    service = OMRService(db)
    try:
        owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
        pdf_bytes = service.get_template_pdf(template_id, student_code, owner_id=owner_id)
        headers = {"Content-Disposition": f'attachment; filename="omr_template_{template_id}.pdf"'}
        return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/templates/{template_id}/preview.png")
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def get_template_preview_png(
    template_id: UUID,
    student_code: str = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """PNG preview in the same coordinate space used by the OMR engine (calibration aid)."""
    service = OMRService(db)
    try:
        owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
        png_bytes = service.get_template_preview_png(
            template_id,
            student_code,
            owner_id=owner_id,
        )
        headers = {
            "Content-Disposition": f'inline; filename="omr_preview_{template_id}.png"'
        }
        return Response(content=png_bytes, media_type="image/png", headers=headers)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/scans/upload", response_model=OMRScanResponse, status_code=status.HTTP_201_CREATED)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def upload_scan(
    omr_template_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Uploads a scanned answer sheet image (JPG, JPEG, PNG) and processes it."""
    service = OMRService(db)

    # Validate extension
    filename = file.filename or "scan.png"
    ext = filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only JPG, JPEG and PNG are allowed.",
        )

    # Read bytes
    file_bytes = await file.read()

    try:
        owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
        scan = service.process_scan_upload(
            omr_template_id,
            file_bytes,
            filename,
            owner_id=owner_id,
        )
        return scan
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post(
    "/scans/upload-batch",
    response_model=OMRBatchUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def upload_scan_batch(
    omr_template_id: UUID = Form(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Uploads a multipage PDF or single image and processes one scan per page."""
    service = OMRService(db)

    filename = file.filename or "batch.pdf"
    ext = filename.split(".")[-1].lower()
    if ext not in ["pdf", "jpg", "jpeg", "png"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF, JPG, JPEG and PNG are allowed.",
        )

    file_bytes = await file.read()

    try:
        owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
        scans = service.process_scan_upload_batch(
            omr_template_id,
            file_bytes,
            filename,
            owner_id=owner_id,
        )
        serialized_scans = [
            {
                "id": scan.id,
                "omr_template_id": scan.omr_template_id,
                "student_code": scan.student_code,
                "student_id": scan.student_id,
                "status": scan.status,
                "image_url": scan.image_url,
                "detected_answers": scan.detected_answers,
                "raw_confidence": scan.raw_confidence,
                "score": scan.score,
                "error_message": scan.error_message,
                "processed_at": scan.processed_at,
                "created_at": scan.created_at,
                "updated_at": scan.updated_at,
            }
            for scan in scans
        ]
        return {
            "omr_template_id": omr_template_id,
            "source_filename": filename,
            "total_pages": len(scans),
            "scans": serialized_scans,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/scans/{scan_id}", response_model=OMRScanResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def get_scan(
    scan_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieves the details and results of an OMR scan."""
    service = OMRService(db)
    owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
    scan = service.get_scan(scan_id, owner_id=owner_id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"OMR Scan with ID {scan_id} not found."
        )
    return scan


@router.patch("/scans/{scan_id}", response_model=OMRScanResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def update_scan_manual(
    scan_id: UUID,
    update_in: OMRScanUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Allows manual adjustment of student code and answers by the teacher."""
    service = OMRService(db)
    try:
        owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
        updated = service.update_scan_manual(scan_id, update_in, owner_id=owner_id)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/scans/{scan_id}/confirm", response_model=GradeResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def confirm_scan(
    scan_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirms OMR correction and publishes the grade to the unified grades table."""
    service = OMRService(db)
    try:
        owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
        grade = service.confirm_scan(scan_id, current_user.id, owner_id=owner_id)
        return grade
    except ValueError as e:
        detail = str(e)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in detail.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=status_code, detail=detail)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def delete_template(
    template_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft-deletes an OMR template and preserves historical scans and grades."""
    service = OMRService(db)
    owner_id = current_user.id if current_user.role == UserRole.TEACHER else None
    success = service.delete_template(template_id, owner_id=owner_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"OMR Template {template_id} not found.",
        )
    return None
