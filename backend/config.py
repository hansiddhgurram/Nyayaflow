"""Backend configuration."""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "NyayaFlow"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-assisted Online Dispute Resolution Platform for India"

    DATABASE_URL: str = "sqlite:///./nyayaflow.db"
    # Required: a predictable default would allow forged access tokens.
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day

    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "gemma:2b"

    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "indian_legal_docs"

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    CORS_ORIGINS: str = "http://localhost:8000"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
