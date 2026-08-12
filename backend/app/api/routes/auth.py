from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas import UserLogin, UserResponse, UserUpdate
from app.services.audit_log import AuditLogService
from app.services.auth import AuthService

router = APIRouter()

ACCESS_TOKEN_MAX_AGE = 15 * 60
REFRESH_TOKEN_MAX_AGE = 7 * 24 * 60 * 60
COOKIE_SECURE = settings.app_env.lower() == "production"


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=ACCESS_TOKEN_MAX_AGE,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=REFRESH_TOKEN_MAX_AGE,
        path="/",
    )


@router.post("/login", response_model=dict)
async def login(data: UserLogin, response: Response, db: Session = Depends(get_db)):
    """Authenticate user and return tokens."""
    service = AuthService(db)
    auth = service.authenticate_user(data)
    if not auth:
        AuditLogService(db).record(
            event_type="auth.login_failure",
            metadata={"email": data.email},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    _set_auth_cookies(response, auth["access_token"], auth["refresh_token"])
    AuditLogService(db).record(
        event_type="auth.login_success",
        user_id=UUID(auth["user"]["id"]),
        metadata={"email": data.email},
    )
    db.commit()
    return auth


@router.post("/refresh", response_model=dict)
async def refresh(
    body: dict,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Refresh access token using refresh token."""
    token = body.get("refresh_token") or request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token required",
        )
    service = AuthService(db)
    new = service.refresh_access_token(token)
    if not new:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    response.set_cookie(
        key="access_token",
        value=new["access_token"],
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=ACCESS_TOKEN_MAX_AGE,
        path="/",
    )
    return new


@router.post("/logout")
async def logout(response: Response, current_user=Depends(get_current_user)):
    """Logout user (client-side token deletion)."""
    # Logged as a sensitive action for audit purposes.
    # The current authenticated user is already validated by the dependency.
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_in: UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current authenticated user profile (e.g. student_code)."""
    service = AuthService(db)
    try:
        updated = service.update_user(current_user.id, user_in)
        AuditLogService(db).record(
            event_type="user.profile_update",
            user_id=current_user.id,
            metadata={"fields": list(user_in.model_dump(exclude_unset=True).keys())},
        )
        db.commit()
        return updated
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
