from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import UserRole
from app.schemas.consent import ConsentCreate, ConsentResponse, MonitoringConsentCreate
from app.services.consent import ConsentService

router = APIRouter()


@router.post("/consents", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def upsert_consent(
    consent_in: ConsentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ConsentService(db)
    consent = service.upsert_consent(
        user_id=current_user.id,
        consent_type=consent_in.consent_type,
        purpose=consent_in.purpose,
        granted=consent_in.granted,
        policy_version=consent_in.policy_version,
        metadata=consent_in.metadata,
    )
    db.commit()
    return consent


@router.post(
    "/consents/monitoring", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED
)
async def upsert_monitoring_consent(
    consent_in: MonitoringConsentCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ConsentService(db)
    consent = service.upsert_consent(
        user_id=current_user.id,
        consent_type="monitoring",
        purpose=consent_in.purpose,
        granted=consent_in.granted,
        policy_version=consent_in.policy_version,
        metadata=consent_in.metadata,
    )
    db.commit()
    return consent


@router.delete("/consents/{consent_type}", response_model=ConsentResponse)
async def revoke_consent(
    consent_type: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ConsentService(db)
    try:
        consent = service.revoke_consent(user_id=current_user.id, consent_type=consent_type)
        db.commit()
        return consent
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/me/consents", response_model=list[ConsentResponse])
async def list_my_consents(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ConsentService(db)
    return service.get_consents(user_id=current_user.id)


@router.get("/admin/consents", response_model=list[ConsentResponse])
@require_role(UserRole.ADMIN)
async def list_all_consents(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[UUID] = None,
    consent_type: Optional[str] = None,
    granted: Optional[bool] = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ConsentService(db)
    return service.list_consents(
        skip=skip,
        limit=limit,
        user_id=user_id,
        consent_type=consent_type,
        granted=granted,
    )
