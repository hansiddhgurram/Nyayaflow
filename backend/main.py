"""NyayaFlow FastAPI application entry point."""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from database.connection import init_db
from backend.routers import auth, cases, evidence, mediation, admin, agreements
from backend.config import get_settings

settings = get_settings()

app = FastAPI(
    title="NyayaFlow API",
    description="AI-assisted Online Dispute Resolution Platform for India",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(evidence.router)
app.include_router(mediation.router)
app.include_router(admin.router)
app.include_router(agreements.router)


@app.on_event("startup")
def on_startup():
    os.makedirs("./uploads", exist_ok=True)
    os.makedirs("./chroma_db", exist_ok=True)
    init_db()


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "NyayaFlow Backend"}


@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/case/new", response_class=HTMLResponse)
def new_case_page(request: Request):
    return templates.TemplateResponse("new_case.html", {"request": request})


@app.get("/case/{case_id}", response_class=HTMLResponse)
def case_page(request: Request, case_id: int):
    return templates.TemplateResponse("case_detail.html", {"request": request, "case_id": case_id})


@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})
