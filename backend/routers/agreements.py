"""Settlement agreement download router."""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database.connection import get_db
from database import crud, models
from backend.dependencies import get_current_user

router = APIRouter(prefix="/agreements", tags=["Agreements"])


@router.get("/{settlement_id}/pdf")
def download_settlement_pdf(settlement_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    settlement = db.query(models.Settlement).filter(models.Settlement.id == settlement_id).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")

    case = settlement.case
    if current_user.id not in (case.party_a_id, case.party_b_id, case.assigned_mediator_id) and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not settlement.pdf_path or not os.path.exists(settlement.pdf_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(settlement.pdf_path, media_type="application/pdf", filename=f"settlement_case_{case.id}.pdf")
