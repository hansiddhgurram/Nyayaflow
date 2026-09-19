"""Evidence upload and processing router."""
import os
from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from database.connection import get_db
from database import crud, models
from backend.dependencies import get_current_user
from backend.config import get_settings
from services.ocr_service import OCRService
from agents.evidence_intake import EvidenceIntakeAgent
from agents.evidence_validation import EvidenceValidationAgent

router = APIRouter(prefix="/evidence", tags=["Evidence"])
settings = get_settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


class EvidenceOut(BaseModel):
    id: int
    case_id: int
    file_name: str
    file_type: str
    extracted_text: str | None
    validation_score: float | None
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/upload/{case_id}", response_model=EvidenceOut, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    case = crud.get_case(db, case_id)
    if not case or current_user.id not in (case.party_a_id, case.party_b_id):
        raise HTTPException(status_code=403, detail="Not authorized to upload evidence for this case")

    # Validate file type
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".txt"}
    original_filename = file.filename or ""
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"File type {ext} not allowed")

    # Save file
    case_dir = os.path.join(settings.UPLOAD_DIR, str(case_id))
    os.makedirs(case_dir, exist_ok=True)
    # Never use a client-controlled filename as a filesystem path.
    file_path = os.path.join(case_dir, f"{uuid4().hex}{ext}")
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    written = 0
    too_large = False
    with open(file_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            written += len(chunk)
            if written > max_bytes:
                too_large = True
                break
            buffer.write(chunk)
    if too_large:
        os.remove(file_path)
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB} MB limit",
        )

    # Determine file type
    file_type = "pdf" if ext == ".pdf" else "image" if ext in {".png", ".jpg", ".jpeg"} else "text"

    # Create evidence record
    evidence = crud.create_evidence(
        db,
        case_id=case_id,
        uploaded_by_id=current_user.id,
        file_name=original_filename,
        file_path=file_path,
        file_type=file_type,
    )

    # Async processing would be better with Celery; here we process inline for simplicity
    try:
        ocr_service = OCRService()
        extracted_text, confidence = ocr_service.extract_text(file_path, file_type)
        evidence.extracted_text = extracted_text
        evidence.ocr_confidence = confidence

        # Run intake agent
        intake_agent = EvidenceIntakeAgent()
        intake_result = intake_agent.process(extracted_text or "")
        evidence.entities = intake_result.get("entities")
        evidence.timeline = intake_result.get("timeline")

        # Run validation agent
        all_evidence = crud.get_evidence_by_case(db, case_id)
        texts = [e.extracted_text for e in all_evidence if e.id != evidence.id and e.extracted_text]
        validator = EvidenceValidationAgent()
        validation = validator.validate(extracted_text or "", texts)
        evidence.validation_score = validation.get("confidence_score", 0.5)
        evidence.validation_notes = validation.get("notes")

        db.commit()
        db.refresh(evidence)

        crud.create_audit_log(db, action="EVIDENCE_UPLOADED", case_id=case_id, user_id=current_user.id, details={"evidence_id": evidence.id})
    except Exception as e:
        # Log but don't fail the upload
        evidence.validation_score = 0.0
        evidence.validation_notes = f"Processing error: {str(e)}"
        db.commit()

    return evidence


@router.get("/case/{case_id}", response_model=List[EvidenceOut])
def list_evidence(case_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    case = crud.get_case(db, case_id)
    if not case or current_user.id not in (case.party_a_id, case.party_b_id, case.assigned_mediator_id) and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_evidence_by_case(db, case_id)
