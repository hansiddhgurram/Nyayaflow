"""CRUD operations for NyayaFlow."""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from database import models


# ---------- Users ----------
def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.email == email).first()


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, email: str, hashed_password: str, full_name: str, role: models.UserRole = models.UserRole.PARTY, phone: Optional[str] = None) -> models.User:
    user = models.User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        phone=phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------- Cases ----------
def get_case(db: Session, case_id: int) -> Optional[models.Case]:
    return db.query(models.Case).filter(models.Case.id == case_id).first()


def get_cases_for_user(db: Session, user_id: int) -> List[models.Case]:
    return (
        db.query(models.Case)
        .filter(
            (models.Case.party_a_id == user_id) | (models.Case.party_b_id == user_id)
        )
        .order_by(desc(models.Case.created_at))
        .all()
    )


def create_case(db: Session, title: str, description: Optional[str], party_a_id: int, party_b_id: int) -> models.Case:
    case = models.Case(
        title=title,
        description=description,
        party_a_id=party_a_id,
        party_b_id=party_b_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def update_case_status(db: Session, case_id: int, status: models.CaseStatus) -> models.Case:
    case = get_case(db, case_id)
    if case:
        case.status = status
        db.commit()
        db.refresh(case)
    return case


def update_case_field(db: Session, case_id: int, **kwargs) -> models.Case:
    case = get_case(db, case_id)
    if case:
        for key, value in kwargs.items():
            setattr(case, key, value)
        db.commit()
        db.refresh(case)
    return case


# ---------- Evidence ----------
def create_evidence(db: Session, **kwargs) -> models.Evidence:
    evidence = models.Evidence(**kwargs)
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def get_evidence_by_case(db: Session, case_id: int) -> List[models.Evidence]:
    return db.query(models.Evidence).filter(models.Evidence.case_id == case_id).all()


# ---------- Settlements ----------
def create_settlement(db: Session, **kwargs) -> models.Settlement:
    settlement = models.Settlement(**kwargs)
    db.add(settlement)
    db.commit()
    db.refresh(settlement)
    return settlement


# ---------- Messages ----------
def create_message(db: Session, case_id: int, sender_id: int, content: str, message_type: str = "chat") -> models.Message:
    msg = models.Message(
        case_id=case_id,
        sender_id=sender_id,
        content=content,
        message_type=message_type,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def get_messages_by_case(db: Session, case_id: int) -> List[models.Message]:
    return (
        db.query(models.Message)
        .filter(models.Message.case_id == case_id)
        .order_by(models.Message.created_at)
        .all()
    )


# ---------- Audit Logs ----------
def create_audit_log(db: Session, action: str, case_id: Optional[int] = None, user_id: Optional[int] = None, details: Optional[dict] = None) -> models.AuditLog:
    log = models.AuditLog(
        action=action,
        case_id=case_id,
        user_id=user_id,
        details=details,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# ---------- Legal Sources ----------
def create_legal_source(db: Session, **kwargs) -> models.LegalSource:
    source = models.LegalSource(**kwargs)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def get_legal_sources(db: Session, skip: int = 0, limit: int = 100) -> List[models.LegalSource]:
    return db.query(models.LegalSource).offset(skip).limit(limit).all()
