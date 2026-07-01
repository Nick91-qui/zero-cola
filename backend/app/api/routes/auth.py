from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.repositories.user import UserRepository
from app.schemas import UserCreate, UserLogin, UserResponse
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=dict)
async def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    service = AuthService(db)
    try:
        user = service.register_user(user_in)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=dict)
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return tokens."""
    service = AuthService(db)
    auth = service.authenticate_user(data)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return auth


@router.post("/refresh", response_model=dict)
async def refresh(body: dict, db: Session = Depends(get_db)):
    """Refresh access token using refresh token."""
    token = body.get("refresh_token")
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
    return new


@router.post("/logout")
async def logout(current_user=Depends(get_current_user)):
    """Logout user (client-side token deletion)."""
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """Get current authenticated user info."""
    return current_user
