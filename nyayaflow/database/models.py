"""SQLAlchemy ORM models for NyayaFlow."""
import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey, Enum, Float, Boolean, JSON
)
from sqlalchemy.orm import relationship
from database.connection import Base
import enum


class UserRole(str, enum.Enum):
    PARTY = "party"
    ADMIN = "admin"
    MEDIATOR = "mediator"


class CaseStatus(str, enum.Enum):
    INTAKE = "intake"
    VALIDATION = "validation"
    CLASSIFICATION = "classification"
    LEGAL_RESEARCH = "legal_research"
    MEDIATION = "mediation"
    SETTLEMENT_DRAFT = "settlement_draft"
    ADMIN_REVIEW = "admin_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class DisputeType(str, enum.Enum):
    CONSUMER = "consumer"
    FREELANCE = "freelance"
    MSME = "msme"
    RENTAL = "rental"
    SERVICE = "service"
    OTHER = "other"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PARTY, nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    cases_a = relationship("Case", foreign_keys="Case.party_a_id", back_populates="party_a")
    cases_b = relationship("Case", foreign_keys="Case.party_b_id", back_populates="party_b")
    audit_logs = relationship("AuditLog", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    dispute_type = Column(Enum(DisputeType), nullable=True)
    status = Column(Enum(CaseStatus), default=CaseStatus.INTAKE, nullable=False)
    party_a_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    party_b_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_mediator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    classification_result = Column(JSON, nullable=True)
    legal_research_result = Column(JSON, nullable=True)
    mediation_result = Column(JSON, nullable=True)
    settlement_draft = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    admin_decision = Column(String(50), nullable=True)  # approved / rejected
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    party_a = relationship("User", foreign_keys=[party_a_id], back_populates="cases_a")
    party_b = relationship("User", foreign_keys=[party_b_id], back_populates="cases_b")
    assigned_mediator = relationship("User", foreign_keys=[assigned_mediator_id])
    evidence = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="case", cascade="all, delete-orphan")
    settlements = relationship("Settlement", back_populates="case", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="case", cascade="all, delete-orphan")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, image, txt
    extracted_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    entities = Column(JSON, nullable=True)  # extracted entities
    timeline = Column(JSON, nullable=True)  # extracted timeline events
    validation_score = Column(Float, nullable=True)
    validation_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="evidence")
    uploaded_by = relationship("User")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="chat")  # chat, system, ai_suggestion
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="messages")
    sender = relationship("User")


class LegalSource(Base):
    __tablename__ = "legal_sources"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    act_name = Column(String(500), nullable=False)
    section = Column(String(100), nullable=True)
    content = Column(Text, nullable=False)
    source_url = Column(String(1000), nullable=True)
    embedding_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Settlement(Base):
    __tablename__ = "settlements"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    draft_text = Column(Text, nullable=False)
    payment_schedule = Column(JSON, nullable=True)
    pdf_path = Column(String(1000), nullable=True)
    is_final = Column(Boolean, default=False)
    signed_by_party_a = Column(Boolean, default=False)
    signed_by_party_b = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="settlements")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="audit_logs")
    user = relationship("User", back_populates="audit_logs")
