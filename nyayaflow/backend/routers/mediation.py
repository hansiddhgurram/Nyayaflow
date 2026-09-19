"""Mediation and classification router."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional

from database.connection import get_db
from database import crud, models
from backend.dependencies import get_current_user
from agents.dispute_classification import DisputeClassificationAgent
from agents.legal_research import LegalResearchAgent
from agents.mediation import MediationAgent
from agents.settlement_drafting import SettlementDraftingAgent
from rag.retriever import LegalRetriever

router = APIRouter(prefix="/mediate", tags=["Mediation"])


class ClassificationRequest(BaseModel):
    case_id: int


class ClassificationResponse(BaseModel):
    dispute_type: str
    confidence: float
    reasoning: str


class LegalResearchResponse(BaseModel):
    relevant_statutes: List[dict]
    summary: str


class MediationRequest(BaseModel):
    case_id: int
    party_position: Optional[str] = None  # If party wants to add new position


class MediationResponse(BaseModel):
    party_a_position: str = "Could not be determined automatically."
    party_b_position: str = "Could not be determined automatically."
    common_ground: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    risks_assessment: str = "Unable to assess risks automatically. Consider legal counsel."


class SettlementRequest(BaseModel):
    case_id: int
    terms: Optional[str] = None  # Override terms if needed


class SettlementResponse(BaseModel):
    draft_text: str
    payment_schedule: Optional[dict]
    pdf_url: Optional[str]


@router.post("/classify", response_model=ClassificationResponse)
def classify_dispute(req: ClassificationRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    case = crud.get_case(db, req.case_id)
    if not case or current_user.id not in (case.party_a_id, case.party_b_id, case.assigned_mediator_id) and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    evidence_list = crud.get_evidence_by_case(db, req.case_id)
    all_text = "\n\n".join([e.extracted_text or "" for e in evidence_list])

    agent = DisputeClassificationAgent()
    result = agent.classify(all_text)

    dt_str = result.get("dispute_type", "other")
    try:
        case.dispute_type = models.DisputeType(dt_str)
    except ValueError:
        case.dispute_type = models.DisputeType.OTHER
    case.classification_result = result
    case.status = models.CaseStatus.CLASSIFICATION
    db.commit()

    crud.create_audit_log(db, action="DISPUTE_CLASSIFIED", case_id=req.case_id, user_id=current_user.id, details=result)
    return ClassificationResponse(
        dispute_type=case.dispute_type.value if hasattr(case.dispute_type, 'value') else str(case.dispute_type),
        confidence=float(result.get("confidence", 0.0)),
        reasoning=str(result.get("reasoning", "")),
    )


@router.post("/legal-research", response_model=LegalResearchResponse)
def legal_research(req: ClassificationRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    case = crud.get_case(db, req.case_id)
    if not case or current_user.id not in (case.party_a_id, case.party_b_id, case.assigned_mediator_id) and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    evidence_list = crud.get_evidence_by_case(db, req.case_id)
    all_text = "\n\n".join([e.extracted_text or "" for e in evidence_list])

    retriever = LegalRetriever()
    statutes = retriever.retrieve(all_text, top_k=5)

    dt_val = getattr(case.dispute_type, 'value', str(case.dispute_type)) if case.dispute_type else "general"
    agent = LegalResearchAgent()
    summary = agent.summarize_relevance(dt_val, statutes)

    case.legal_research_result = {"statutes": statutes, "summary": summary}
    case.status = models.CaseStatus.LEGAL_RESEARCH
    db.commit()

    crud.create_audit_log(db, action="LEGAL_RESEARCH", case_id=req.case_id, user_id=current_user.id)
    return LegalResearchResponse(relevant_statutes=statutes, summary=summary)


@router.post("/suggest", response_model=MediationResponse)
def mediation_suggest(req: MediationRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    case = crud.get_case(db, req.case_id)
    if not case or current_user.id not in (case.party_a_id, case.party_b_id, case.assigned_mediator_id) and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    evidence_list = crud.get_evidence_by_case(db, req.case_id)
    all_text = "\n\n".join([e.extracted_text or "" for e in evidence_list])
    messages = crud.get_messages_by_case(db, req.case_id)
    chat_history = "\n".join([f"{m.sender.full_name}: {m.content}" for m in messages])

    dt_val = getattr(case.dispute_type, 'value', str(case.dispute_type)) if case.dispute_type else "general"
    agent = MediationAgent()
    result = agent.mediate(all_text, chat_history, dt_val)

    case.mediation_result = result
    case.status = models.CaseStatus.MEDIATION
    db.commit()

    crud.create_audit_log(db, action="MEDIATION_SUGGESTED", case_id=req.case_id, user_id=current_user.id)
    return MediationResponse(
        party_a_position=result.get("party_a_position", "Could not be determined automatically."),
        party_b_position=result.get("party_b_position", "Could not be determined automatically."),
        common_ground=result.get("common_ground") or [],
        suggestions=result.get("suggestions") or [],
        risks_assessment=result.get("risks_assessment", "Unable to assess risks automatically. Consider legal counsel."),
    )


@router.post("/settlement", response_model=SettlementResponse)
def generate_settlement(req: SettlementRequest, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    case = crud.get_case(db, req.case_id)
    if not case or current_user.id not in (case.party_a_id, case.party_b_id, case.assigned_mediator_id) and current_user.role != models.UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized")

    evidence_list = crud.get_evidence_by_case(db, req.case_id)
    all_text = "\n\n".join([e.extracted_text or "" for e in evidence_list])
    mediation_result = case.mediation_result or {}

    dt_val = getattr(case.dispute_type, 'value', str(case.dispute_type)) if case.dispute_type else "general"
    agent = SettlementDraftingAgent()
    result = agent.draft(
        dispute_type=dt_val,
        facts=all_text,
        common_ground=mediation_result.get("common_ground", []),
        suggestions=mediation_result.get("suggestions", []),
        terms_override=req.terms,
    )

    case.settlement_draft = result["draft_text"]
    case.status = models.CaseStatus.SETTLEMENT_DRAFT
    db.commit()

    # Generate PDF
    from services.pdf_service import PDFService
    pdf_path = PDFService.generate_settlement_pdf(result["draft_text"], req.case_id)

    settlement = crud.create_settlement(
        db,
        case_id=req.case_id,
        draft_text=result["draft_text"],
        payment_schedule=result.get("payment_schedule"),
        pdf_path=pdf_path,
    )

    crud.create_audit_log(db, action="SETTLEMENT_DRAFTED", case_id=req.case_id, user_id=current_user.id)
    return SettlementResponse(
        draft_text=result["draft_text"],
        payment_schedule=result.get("payment_schedule"),
        pdf_url=f"/agreements/{settlement.id}/pdf" if pdf_path else None,
    )
