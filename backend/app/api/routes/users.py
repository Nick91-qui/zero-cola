from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_role
from app.db.session import get_db
from app.models.enums import PrivacyRequestStatus, UserRole
from app.repositories.user import UserRepository
from app.schemas import PrivacyRequestResponse, UserCreate, UserResponse
from app.services.audit_log import AuditLogService
from app.services.auth import AuthService
from app.services.privacy import PrivacyService

router = APIRouter()


@router.post("/users", response_model=UserResponse, status_code=201)
@require_role(UserRole.ADMIN)
async def create_user(
    user_in: UserCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    try:
        created = service.register_user(user_in)
        AuditLogService(db).record(
            event_type="admin.user_create",
            user_id=current_user.id,
            metadata={"email": user_in.email, "role": user_in.role.value},
        )
        db.commit()
        return created
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/users", response_model=list[UserResponse])
@require_role(UserRole.ADMIN)
async def list_users(
    q: str = "",
    role: UserRole | None = None,
    include_inactive: bool = True,
    limit: int = 100,
    skip: int = 0,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    return repo.list_users(
        query=q,
        role=role,
        include_inactive=include_inactive,
        limit=limit,
        skip=skip,
    )


@router.get("/users/search", response_model=list[UserResponse])
@require_role(UserRole.ADMIN)
async def search_users(
    q: str = "",
    role: UserRole | None = None,
    limit: int = 10,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    return repo.search(query=q, role=role, limit=limit)


@router.get("/privacy-requests", response_model=list[PrivacyRequestResponse])
@require_role(UserRole.ADMIN)
async def list_privacy_requests(
    status: PrivacyRequestStatus | None = PrivacyRequestStatus.PENDING,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PrivacyService(db)
    requests = service.list_privacy_requests(status=status)
    return [PrivacyRequestResponse.model_validate(request) for request in requests]


@router.post("/privacy-requests/{request_id}/approve", response_model=PrivacyRequestResponse)
@require_role(UserRole.ADMIN)
async def approve_privacy_request(
    request_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PrivacyService(db)
    try:
        request = service.approve_privacy_request(request_id=request_id, reviewer=current_user)
        return PrivacyRequestResponse.model_validate(request)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_409_CONFLICT
        if "not found" in message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=message)


@router.post("/privacy-requests/{request_id}/reject", response_model=PrivacyRequestResponse)
@require_role(UserRole.ADMIN)
async def reject_privacy_request(
    request_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PrivacyService(db)
    try:
        request = service.reject_privacy_request(request_id=request_id, reviewer=current_user)
        return PrivacyRequestResponse.model_validate(request)
    except ValueError as exc:
        message = str(exc)
        status_code = status.HTTP_409_CONFLICT
        if "not found" in message.lower():
            status_code = status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code=status_code, detail=message)


@router.post("/users/{user_id}/archive", response_model=UserResponse)
@require_role(UserRole.ADMIN)
async def archive_user(
    user_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.anonymized_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Anonymized users cannot be archived.",
        )

    if not user.is_active:
        return user

    AuditLogService(db).record(
        event_type="admin.user_archive_requested",
        user_id=current_user.id,
        resource_type="user",
        resource_id=user.id,
        metadata={
            "email": user.email,
            "role": user.role.value,
            "previous_is_active": user.is_active,
            "requested_is_active": False,
        },
    )
    user.is_active = False
    AuditLogService(db).record(
        event_type="admin.user_archived",
        user_id=current_user.id,
        resource_type="user",
        resource_id=user.id,
        metadata={
            "email": user.email,
            "role": user.role.value,
            "previous_is_active": True,
            "current_is_active": False,
        },
    )
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", response_model=UserResponse)
@require_role(UserRole.ADMIN)
async def delete_user(
    user_id: str,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = PrivacyService(db)
    try:
        existing = UserRepository(db).get_by_id(user_id)
        if existing is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        AuditLogService(db).record(
            event_type="admin.user_delete_requested",
            user_id=current_user.id,
            resource_type="user",
            resource_id=existing.id,
            metadata={
                "email": existing.email,
                "role": existing.role.value,
                "previous_is_active": existing.is_active,
                "anonymized": existing.anonymized_at is not None,
            },
        )
        deleted = service.anonymize_user(user_id=user_id)
        AuditLogService(db).record(
            event_type="admin.user_deleted",
            user_id=current_user.id,
            resource_type="user",
            resource_id=deleted.id,
            metadata={
                "email": deleted.email,
                "role": deleted.role.value,
                "is_active": deleted.is_active,
                "anonymized_at": deleted.anonymized_at.isoformat()
                if deleted.anonymized_at
                else None,
            },
        )
        db.commit()
        return deleted
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
