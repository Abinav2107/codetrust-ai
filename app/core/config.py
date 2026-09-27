import sys
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "IBM Bob 2.0 - AI Debugging & Testing Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security
    API_KEY: str = "ibm-bob-secret-key-change-in-production"
    REQUIRE_API_KEY: bool = False

    # Rate Limiting
    RATE_LIMIT_ANALYZE: str = "30/minute"
    RATE_LIMIT_DEFAULT: str = "120/minute"

    # CORS
    # In production, override this with the deployed frontend origin(s).
    # Example: CORS_ORIGINS="https://app.your-domain.com"
    # Multiple origins: CORS_ORIGINS="https://app.your-domain.com,https://www.your-domain.com"
    CORS_ORIGINS: Union[str, List[str]] = (
        "http://localhost:3000,"
        "http://localhost:5173,"
        "http://localhost:5180,"
        "http://127.0.0.1:3000,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:5180"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # AI Agent Integration (Abinav's service)
    MOCK_AI_AGENT: bool = True
    AI_AGENT_SERVICE_URL: str = "http://localhost:8001/agent/analyze"
    AI_AGENT_TIMEOUT_SECONDS: float = 30.0

    # Persistence
    # Local default: SQLite (zero dependencies for local dev).
    # PRODUCTION: Render's filesystem is ephemeral — SQLite data is lost on every
    # redeploy/restart. Set DATABASE_URL to a PostgreSQL connection string:
    #   postgresql+asyncpg://user:password@host:5432/dbname
    DATABASE_URL: str = "sqlite+aiosqlite:///./ibm_bob.db"

    # Safety & Limits
    MAX_CODE_SIZE_BYTES: int = 65536  # 64 KB limit
    SANDBOX_EXECUTION_TIMEOUT: float = 5.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def warn_sqlite_in_production(self) -> "Settings":
        """Emit a loud warning (and exit in production) if SQLite is used outside dev."""
        if self.APP_ENV == "production" and self.DATABASE_URL.startswith("sqlite"):
            msg = (
                "FATAL: SQLite is not suitable for production on Render. "
                "Render's filesystem is ephemeral — all SQLite data is lost on restart. "
                "Set DATABASE_URL to a PostgreSQL connection string and redeploy."
            )
            print(f"\n{'='*70}\n{msg}\n{'='*70}\n", file=sys.stderr)
            sys.exit(1)
        return self


settings = Settings()
