from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.omr import (
    GradeResponse,
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
    return service.create_template(template_in)


@router.get("/templates", response_model=list[OMRTemplateResponse])
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def list_templates(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lists OMR templates."""
    service = OMRService(db)
    return service.list_templates()


@router.get("/templates/{template_id}", response_model=OMRTemplateResponse)
@require_role(UserRole.TEACHER, UserRole.ADMIN)
async def get_template(
    template_id: UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Gets a single OMR template."""
    service = OMRService(db)
    template = service.get_template(template_id)
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
        pdf_bytes = service.get_template_pdf(template_id, student_code)
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
        png_bytes = service.get_template_preview_png(template_id, student_code)
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
        scan = service.process_scan_upload(omr_template_id, file_bytes, filename)
        return scan
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
    scan = service.scan_repo.get_by_id(scan_id)
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
        updated = service.update_scan_manual(scan_id, update_in)
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
        grade = service.confirm_scan(scan_id, current_user.id)
        return grade
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
