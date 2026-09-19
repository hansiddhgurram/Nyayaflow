# NyayaFlow (SulabhODR)

> **AI-Assisted Online Dispute Resolution (ODR) Platform for India** Grounded in Local LLMs, RAG-Enhanced Legal Research, and the Mediation Act, 2023.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Workflow-FF6F00?style=flat-square)](https://langchain.com)
[![Ollama](https://img.shields.io/badge/Ollama-Gemma%202B-000000?style=flat-square)](https://ollama.com)
[![License](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)

---

## 📌 Executive Summary

**NyayaFlow** is an open-source, enterprise-ready Online Dispute Resolution platform engineered to facilitate out-of-court civil, commercial, freelance, and consumer dispute resolution in India. By combining local, privacy-preserving LLMs (**Gemma 2B** via **Ollama**) with Retrieval-Augmented Generation (**RAG**) over authoritative Indian legal statutes, NyayaFlow empowers parties and human mediators to reach amicable settlements faster, with transparency and full legal compliance.

---

## ✨ Key Features

- 📑 **Multi-Format Evidence Intake**: Upload contracts, invoices, receipts, or chat logs (`PDF`, `PNG`, `JPG`, `TXT`). Native text extraction with automatic **Tesseract OCR fallback** for scanned documents.
- 🔍 **RAG Legal Retrieval**: Semantic search powered by ChromaDB and vector embeddings over verified Indian acts (Mediation Act 2023, Consumer Protection Act 2019, IT Act 2000, etc.).
- 🏷️ **AI Dispute Classification**: Automated categorization into *Consumer*, *Freelance*, *MSME*, *Rental*, or *Service* disputes with confidence scoring and reasoning.
- 🤝 **Neutral AI Mediation**: Summarizes opposing positions, extracts common ground, and proposes constructive, non-binding settlement pathways.
- 📜 **Automated Settlement Drafting**: Generates structured Mediated Settlement Agreements including customized payment schedules, penalty clauses, and confidentiality covenants per **Section 22 of the Mediation Act, 2023**.
- 📄 **Legal PDF Export**: Compiles settlement drafts into execution-ready PDF documents featuring formal recitals, terms, and signature blocks.
- 🛡️ **Administrator Console**: Human-in-the-loop governance interface to review AI outputs, manage case status (`APPROVED` / `REJECTED`), and inspect full audit logs.


---

## 🤖 Multi-Agent System

NyayaFlow employs 7 specialized AI agents orchestrated via **LangGraph**:

| Agent | Module | Function |
|---|---|---|
| **1. Evidence Intake** | `agents/evidence_intake.py` | Extracts structured entities (amounts, dates, orgs) and chronological timelines from evidence. |
| **2. Evidence Validation** | `agents/evidence_validation.py` | Cross-checks new evidence against past submissions to flag contradictions or missing documents. |
| **3. Dispute Classifier** | `agents/dispute_classification.py` | Categorizes the dispute and assigns confidence scores. |
| **4. Legal Research** | `agents/legal_research.py` | Connects retrieved statute chunks to case facts and summarizes relevant sections. |
| **5. Mediation Facilitator**| `agents/mediation.py` | Synthesizes positions, identifies common ground, and presents neutral settlement suggestions. |
| **6. Settlement Drafter** | `agents/settlement_drafting.py` | Generates Mediated Settlement Agreements and payment schedules. |
| **7. Administrator Review** | `agents/administrator.py` | Checks draft agreements for compliance gaps and flags high-risk terms for human review. |

---

## ⚖️ Indian Legal Framework

All legal research and RAG retrieval vectors are built from official text sourced from **[India Code](https://www.indiacode.nic.in)**:

1. **The Mediation Act, 2023** (Act No. 32 of 2023) - Institutionalized online mediation, confidentiality standards (§22), and settlement enforcement (§27).
2. **Consumer Protection Act, 2019** (Act No. 35 of 2019) - Consumer rights, product liability, and dispute resolution mechanisms.
3. **Indian Contract Act, 1872** (Act No. 9 of 1872) - Essential elements of valid contracts, breach, and damages.
4. **Information Technology Act, 2000** (Act No. 21 of 2000) - Electronic records, digital signatures, and legal recognition of e-communications.
5. **Micro, Small and Medium Enterprises Development (MSMED) Act, 2006** (Act No. 27 of 2006) - Delayed payment remedies and statutory interest terms (§16).

---

## 🛠️ Installation & Setup

### 1. Prerequisites

- **Python**: Version `3.11+`
- **Ollama**: For local LLM inference ([Download Ollama](https://ollama.com))
- **Tesseract OCR**: For image/scanned document text extraction

#### OS Dependencies Setup

- **Ubuntu / Debian**:
  ```bash
  sudo apt update
  sudo apt install -y tesseract-ocr tesseract-ocr-hin libtesseract-dev libgl1-mesa-glx libglib2.0-0
  ```

- **macOS**:
  ```bash
  brew install tesseract tesseract-lang
  ```

- **Windows**:
  1. Download Tesseract installer from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
  2. Install and ensure `C:\Program Files\Tesseract-OCR` (or your installation path) is added to your **System PATH**.

---

### 2. Environment Setup

Clone the repository and create a virtual environment:

```bash
git clone https://github.com/your-username/nyayaflow.git
cd nyayaflow/nyayaflow

# Create & activate virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Environment Configuration

Copy the sample environment file:

```bash
# Windows PowerShell:
Copy-Item .env.example .env
# Linux/macOS:
cp .env.example .env
```

Ensure `.env` contains your desired settings:
```ini
SECRET_KEY=generate-a-secure-random-secret-key-here
DATABASE_URL=sqlite:///./nyayaflow.db
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma:2b
CORS_ORIGINS=http://localhost:8000
```

---

### 4. Local LLM Setup (Ollama)

Start Ollama and pull the Gemma model:

```bash
# Pull the lightweight Gemma 2B model
ollama pull gemma:2b

# Verify model installation
ollama list
```

---

### 5. Ingest Legal Documents into ChromaDB

Run the ingestion script to chunk, embed, and store Indian statutes in ChromaDB:

```bash
python -m rag.ingest
```

*Output:*
```text
Ingested 11 chunks from Mediation Act, 2023
Ingested 10 chunks from Information Technology Act, 2000
Ingested 12 chunks from Indian Contract Act, 1872
Ingested 14 chunks from Consumer Protection Act, 2019
Ingested 9 chunks from MSMED Act, 2006
```

---

## 🚀 Running the Application

Launch the FastAPI application:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Access the application in your browser:
- **Web UI Application**: [http://localhost:8000](http://localhost:8000)
- **Interactive OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🔑 Admin User Setup

To grant a registered user administrator privileges:

```python
from database.connection import SessionLocal
from database import crud, models

db = SessionLocal()
user = crud.get_user_by_email(db, "admin@example.com")
if user:
    user.role = models.UserRole.ADMIN
    db.commit()
    print("User updated to Admin successfully!")
```

---

## 🧪 Testing & Verification

Run the automated test suite with `pytest`:

```bash
python -m pytest -v
```

*Expected output:*
```text
tests/test_nyayaflow.py::test_health_check PASSED                        [ 11%]
tests/test_nyayaflow.py::test_html_pages PASSED                          [ 22%]
tests/test_nyayaflow.py::test_user_registration_and_login PASSED         [ 33%]
tests/test_nyayaflow.py::test_case_creation_and_retrieval PASSED         [ 44%]
tests/test_nyayaflow.py::test_evidence_upload PASSED                     [ 55%]
tests/test_nyayaflow.py::test_pdf_service PASSED                         [ 66%]
tests/test_nyayaflow.py::test_ocr_service_text_file PASSED               [ 77%]
tests/test_nyayaflow.py::test_evidence_validation_agent_null_handling PASSED [ 88%]
tests/test_nyayaflow.py::test_admin_review_endpoint PASSED               [100%]

======================= 9 passed in 21.00s =======================
```

---

## 🌐 API Endpoint Matrix

| Method | Endpoint | Description | Access |
|---|---|---|---|
| `GET` | `/health` | Application health check | Public |
| `POST` | `/auth/register` | User registration (Party role) | Public |
| `POST` | `/auth/login` | User login (OAuth2 Password / JWT) | Public |
| `POST` | `/cases` | File a new dispute case | Authenticated |
| `GET` | `/cases/my` | List current user's cases | Authenticated |
| `GET` | `/cases/{id}` | Get case details | Party/Mediator/Admin |
| `POST` | `/evidence/upload/{case_id}` | Upload & process evidence file | Case Party |
| `GET` | `/evidence/case/{case_id}` | List evidence files for case | Party/Mediator/Admin |
| `POST` | `/mediate/classify` | Trigger dispute classification | Party/Mediator/Admin |
| `POST` | `/mediate/legal-research` | Retrieve & summarize legal statutes | Party/Mediator/Admin |
| `POST` | `/mediate/suggest` | Generate AI mediation suggestions | Party/Mediator/Admin |
| `POST` | `/mediate/settlement` | Draft settlement agreement | Party/Mediator/Admin |
| `GET` | `/agreements/{settlement_id}/pdf` | Download settlement PDF | Party/Mediator/Admin |
| `GET` | `/admin/cases` | List all system cases | Admin |
| `POST` | `/admin/review` | Approve or reject settlement draft | Admin |
| `GET` | `/admin/audit-logs/{case_id}` | Retrieve case audit logs | Admin |

---

## ⚠️ Legal Disclaimer

> **IMPORTANT**: NyayaFlow (SulabhODR) is an AI-assisted facilitation platform designed to aid voluntary dispute resolution, legal information retrieval, and draft agreement generation. **It does NOT render judicial decisions, issue binding arbitral awards, or make civil/criminal liability determinations.**
>
> All generated settlement agreements become legally binding only when voluntarily executed by both parties in accordance with the provisions of **The Mediation Act, 2023 (India)**. Parties are strongly encouraged to seek independent legal counsel prior to executing any settlement agreement.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for details.
