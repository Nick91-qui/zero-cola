from fastapi import APIRouter, Depends, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas import PrivacyRequestResponse
from app.schemas.privacy import DataExportResponse, PrivacyPolicyResponse
from app.services.audit_log import AuditLogService
from app.services.privacy import PrivacyService

router = APIRouter()


@router.get("/privacy-policy", response_model=PrivacyPolicyResponse)
async def get_privacy_policy():
    return PrivacyService.get_privacy_policy()


@router.get("/me/data-export", response_model=DataExportResponse)
async def export_my_data(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PrivacyService(db)
    payload = service.export_user_data(user_id=current_user.id)
    AuditLogService(db).record(
        event_type="lgpd.data_export_requested",
        user_id=current_user.id,
        resource_type="user",
        resource_id=current_user.id,
    )
    db.commit()
    return {"data": jsonable_encoder(payload)}


@router.post("/me/request-anonymization", response_model=PrivacyRequestResponse, status_code=status.HTTP_202_ACCEPTED)
async def request_anonymization(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PrivacyService(db)
    request = service.request_anonymization(user_id=current_user.id, requested_by_id=current_user.id)
    return PrivacyRequestResponse.model_validate(request)


@router.get("/me/privacy-request", response_model=PrivacyRequestResponse | None)
async def get_my_privacy_request(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PrivacyService(db)
    request = service.get_my_privacy_request(user_id=current_user.id)
    if request is None:
        return None
    return PrivacyRequestResponse.model_validate(request)
