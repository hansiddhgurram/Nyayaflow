"""Case management router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database.connection import get_db
from database import crud, models
from backend.dependencies import get_current_user

router = APIRouter(prefix="/cases", tags=["Cases"])


class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    party_b_email: str


class CaseOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    dispute_type: Optional[str]
    party_a_id: int
    party_b_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    party_b = crud.get_user_by_email(db, case_in.party_b_email)
    if not party_b:
        raise HTTPException(status_code=404, detail="Party B not found")
    if party_b.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot create case with yourself")

    case = crud.create_case(
        db,
        title=case_in.title,
        description=case_in.description,
        party_a_id=current_user.id,
        party_b_id=party_b.id,
    )
    crud.create_audit_log(db, action="CASE_CREATED", case_id=case.id, user_id=current_user.id)
    return case


@router.get("/my", response_model=List[CaseOut])
def list_my_cases(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return crud.get_cases_for_user(db, current_user.id)


@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    case = crud.get_case(db, case_id)
    if not case or (current_user.id not in (case.party_a_id, case.party_b_id, case.assigned_mediator_id) and current_user.role != models.UserRole.ADMIN):
        raise HTTPException(status_code=404, detail="Case not found")
    return case
