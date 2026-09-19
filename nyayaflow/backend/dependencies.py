"""FastAPI dependencies."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from database.connection import get_db
from database import crud
from backend.core.security import decode_access_token
from database.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception
    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    try:
        user = crud.get_user(db, int(user_id))
    except (TypeError, ValueError):
        raise credentials_exception
    if user is None or not user.is_active:
        raise credentials_exception
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_mediator_or_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.MEDIATOR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mediator or Admin access required",
        )
    return current_user
