"""Core application configuration and environment settings for NIRMAYA."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field
from typing import List, Literal
from datetime import datetime, timezone


class Settings(BaseSettings):
    """NIRMAYA platform settings with environment validation."""

    # Project Metadata
    PROJECT_NAME: str = "NIRMAYA"
    PROJECT_FULL_NAME: str = (
        "Networked Interoperable Records Medical Assets & Your Archives"
    )
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # Environment & Debugging
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # Security & Tokens
    SECRET_KEY: str = Field(
        default="nirmaya-super-secret-dev-key-change-in-production-2026",
        description="Core JWT signing secret",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT signature verification algorithm",
    )
    JWT_AUDIENCE: str = Field(
        default="authenticated",
        description="Expected JWT audience claim for Supabase Auth",
    )

    # CORS Allowed Origins
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Database Configuration (PostgreSQL 16)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/nirmaya",
        description="Async PostgreSQL connection string",
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600
    DATABASE_ECHO: bool = False

    # Supabase Auth & Storage
    SUPABASE_URL: str = Field(default="", description="Supabase project endpoint URL")
    SUPABASE_KEY: str = Field(default="", description="Supabase publishable anon key")
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        default="", description="Supabase service role administrative key"
    )
    SUPABASE_JWT_SECRET: str = Field(
        default="supabase-jwt-secret-placeholder",
        description="JWT secret for validating Supabase access tokens",
    )

    # Healthcare Interoperability Flags
    FHIR_VERSION: str = "R4"
    ABDM_SANDBOX_ENABLED: bool = True

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @computed_field
    @property
    def sync_database_url(self) -> str:
        """Derive synchronous database URL for Alembic and migration tools."""
        url = self.DATABASE_URL
        if url.startswith("postgresql+asyncpg://"):
            return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if url.startswith("sqlite+aiosqlite://"):
            return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
        return url


settings = Settings()
