from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import UserCreate, UserLogin
from app.db.session import get_db
from app.services.auth import AuthService

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        user = service.register_user(user_in)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(data: UserLogin, db: Session = Depends(get_db)):
    service = AuthService(db)
    auth = service.authenticate_user(data)
    if not auth:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return auth


@router.post("/refresh")
def refresh(body: dict, db: Session = Depends(get_db)):
    token = body.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    service = AuthService(db)
    new = service.refresh_access_token(token)
    if not new:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return new
