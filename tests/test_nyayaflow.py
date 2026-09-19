"""Comprehensive test suite for NyayaFlow API, database, agents, and services."""
import os
import tempfile
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.connection import Base, get_db
from backend.main import app
from backend.core.security import get_password_hash, create_access_token
from database import models, crud
from services.pdf_service import PDFService
from services.ocr_service import OCRService
from agents.evidence_validation import EvidenceValidationAgent
from rag.retriever import LegalRetriever

from sqlalchemy.pool import StaticPool

# Setup in-memory SQLite database for testing with StaticPool
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "NyayaFlow Backend"}


def test_html_pages(client):
    for path in ["/", "/login", "/dashboard", "/case/new", "/admin"]:
        res = client.get(path)
        assert res.status_code == 200
        assert "NyayaFlow" in res.text


def test_user_registration_and_login(client):
    # Register party A
    reg_res = client.post("/auth/register", json={
        "email": "party_a@example.com",
        "password": "Password123!",
        "full_name": "Party A User",
        "phone": "+919876543210"
    })
    assert reg_res.status_code == 201
    data = reg_res.json()
    assert "access_token" in data
    assert data["user"]["email"] == "party_a@example.com"
    assert data["user"]["role"] == "party"

    # Register duplicate email should fail
    dup_res = client.post("/auth/register", json={
        "email": "party_a@example.com",
        "password": "Password123!",
        "full_name": "Duplicate User"
    })
    assert dup_res.status_code == 400

    # Login party A
    login_res = client.post("/auth/login", data={
        "username": "party_a@example.com",
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


def test_case_creation_and_retrieval(client):
    # Register Party A and Party B
    db = TestingSessionLocal()
    user_a = crud.create_user(db, email="user_a@example.com", hashed_password=get_password_hash("pass"), full_name="User A")
    user_b = crud.create_user(db, email="user_b@example.com", hashed_password=get_password_hash("pass"), full_name="User B")

    token_a = create_access_token({"sub": str(user_a.id)})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Create Case
    case_res = client.post("/cases", headers=headers_a, json={
        "title": "Breach of Contract Case",
        "description": "Payment delayed for 90 days",
        "party_b_email": "user_b@example.com"
    })
    assert case_res.status_code == 201
    case_data = case_res.json()
    assert case_data["title"] == "Breach of Contract Case"
    case_id = case_data["id"]

    # List cases for User A
    my_cases_res = client.get("/cases/my", headers=headers_a)
    assert my_cases_res.status_code == 200
    assert len(my_cases_res.json()) == 1

    # Get specific case detail
    get_case_res = client.get(f"/cases/{case_id}", headers=headers_a)
    assert get_case_res.status_code == 200
    assert get_case_res.json()["id"] == case_id


def test_evidence_upload(client):
    db = TestingSessionLocal()
    user_a = crud.create_user(db, email="user_ev_a@example.com", hashed_password=get_password_hash("pass"), full_name="User Ev A")
    user_b = crud.create_user(db, email="user_ev_b@example.com", hashed_password=get_password_hash("pass"), full_name="User Ev B")
    case = crud.create_case(db, title="Evidence Case", description="Desc", party_a_id=user_a.id, party_b_id=user_b.id)

    token_a = create_access_token({"sub": str(user_a.id)})
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Upload text evidence file
    content = b"Invoice #101 for INR 50,000 issued on 2026-01-15."
    files = {"file": ("invoice.txt", content, "text/plain")}

    upload_res = client.post(f"/evidence/upload/{case.id}", headers=headers_a, files=files)
    assert upload_res.status_code == 201
    ev_data = upload_res.json()
    assert ev_data["file_name"] == "invoice.txt"
    assert "Invoice #101" in ev_data["extracted_text"]

    # List evidence
    list_ev_res = client.get(f"/evidence/case/{case.id}", headers=headers_a)
    assert list_ev_res.status_code == 200
    assert len(list_ev_res.json()) == 1


def test_pdf_service():
    with tempfile.TemporaryDirectory() as tmpdir:
        draft = "# Mediated Settlement Agreement\n\n**Party A** agrees to pay **Party B** INR 25,000."
        file_path = PDFService.generate_settlement_pdf(draft, case_id=99, output_dir=tmpdir)
        assert os.path.exists(file_path)
        assert file_path.endswith(".pdf")


def test_ocr_service_text_file():
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Sample Legal Document Text")
        tmp_path = f.name

    try:
        ocr = OCRService()
        text, conf = ocr.extract_text(tmp_path, "text")
        assert text == "Sample Legal Document Text"
        assert conf == 1.0
    finally:
        os.remove(tmp_path)


def test_evidence_validation_agent_null_handling():
    agent = EvidenceValidationAgent()
    res_none = agent.validate(None, [])
    assert res_none["confidence_score"] == 0.0
    assert "readable evidence text" in res_none["missing_evidence"]

    res_valid = agent.validate("Agreement signed on 2026-01-01", [])
    assert res_valid["confidence_score"] == 0.5


def test_admin_review_endpoint(client):
    db = TestingSessionLocal()
    admin_user = crud.create_user(db, email="admin@example.com", hashed_password=get_password_hash("pass"), full_name="Admin", role=models.UserRole.ADMIN)
    user_a = crud.create_user(db, email="u_a@example.com", hashed_password=get_password_hash("pass"), full_name="U A")
    user_b = crud.create_user(db, email="u_b@example.com", hashed_password=get_password_hash("pass"), full_name="U B")
    case = crud.create_case(db, title="Admin Case", description="Desc", party_a_id=user_a.id, party_b_id=user_b.id)

    token_admin = create_access_token({"sub": str(admin_user.id)})
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # List admin cases
    admin_cases_res = client.get("/admin/cases", headers=headers_admin)
    assert admin_cases_res.status_code == 200
    assert len(admin_cases_res.json()) == 1

    # Review case
    review_res = client.post("/admin/review", headers=headers_admin, json={
        "case_id": case.id,
        "decision": "approved",
        "notes": "Settlement terms approved by admin."
    })
    assert review_res.status_code == 200
    assert review_res.json()["message"] == "Case approved"
