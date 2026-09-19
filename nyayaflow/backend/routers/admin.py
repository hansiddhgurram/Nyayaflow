"""Administrator router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Literal

from database.connection import get_db
from database import crud, models
from backend.dependencies import get_current_admin, get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminReviewRequest(BaseModel):
    case_id: int
    decision: Literal["approved", "rejected"]
    notes: Optional[str] = None


class CaseAdminOut(BaseModel):
    id: int
    title: str
    status: str
    dispute_type: Optional[str]
    party_a_name: str
    party_b_name: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/cases", response_model=List[CaseAdminOut])
def list_all_cases(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    cases = db.query(models.Case).order_by(models.Case.created_at.desc()).all()
    result = []
    for c in cases:
        result.append({
            "id": c.id,
            "title": c.title,
            "status": c.status.value,
            "dispute_type": c.dispute_type.value if c.dispute_type else None,
            "party_a_name": c.party_a.full_name,
            "party_b_name": c.party_b.full_name,
            "created_at": c.created_at.isoformat(),
        })
    return result


@router.post("/review")
def admin_review(req: AdminReviewRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    case = crud.get_case(db, req.case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    case.admin_decision = req.decision
    case.admin_notes = req.notes
    case.status = models.CaseStatus.APPROVED if req.decision == "approved" else models.CaseStatus.REJECTED
    db.commit()

    crud.create_audit_log(db, action=f"ADMIN_{req.decision.upper()}", case_id=req.case_id, user_id=current_user.id, details={"notes": req.notes})
    return {"message": f"Case {req.decision}", "case_id": req.case_id}


@router.get("/audit-logs/{case_id}")
def get_audit_logs(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_admin)):
    logs = db.query(models.AuditLog).filter(models.AuditLog.case_id == case_id).order_by(models.AuditLog.created_at.desc()).all()
    return [{"id": l.id, "action": l.action, "details": l.details, "created_at": l.created_at.isoformat()} for l in logs]
