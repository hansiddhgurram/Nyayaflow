"""Authentication router."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from database.connection import get_db
from database import crud, models
from backend.core.security import verify_password, create_access_token, get_password_hash
from backend.config import get_settings

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: models.UserRole
    phone: str | None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, user_in.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(user_in.password)
    user = crud.create_user(
        db,
        email=user_in.email,
        hashed_password=hashed,
        full_name=user_in.full_name,
        # Public registration must never grant privileged roles.
        role=models.UserRole.PARTY,
        phone=user_in.phone,
    )
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, form_data.username)
    if not user or not user.is_active or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "user": user}
