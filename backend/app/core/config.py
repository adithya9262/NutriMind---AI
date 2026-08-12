from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

VALID_ENVIRONMENTS: frozenset[str] = frozenset({"development", "test", "production"})

VALID_PASSWORD_HASHING_SCHEMES: frozenset[str] = frozenset({"argon2"})


def validate_secret_strength(
    secret: str, name: str, min_length: int = 32, *, required: bool = False
) -> None:
    if not secret:
        if required:
            raise ValueError(f"{name} must not be empty")
        return
    if len(secret) < min_length:
        raise ValueError(f"{name} must be at least {min_length} characters long")


class Settings(BaseSettings):
    APP_NAME: str = "NutriMind AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = Field(default=8000, ge=1, le=65535)
    CORS_ORIGINS: str = "http://localhost:3000,https://nutrimind-frontend.onrender.com"
    PASSWORD_HASHING_SCHEMES: str = "argon2"

    # Future settings — not used yet; empty defaults let the app start
    DATABASE_URL: str = ""
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15,
        ge=1,
        le=1440,
    )
    JWT_ISSUER: str = "nutrimind-ai"
    JWT_AUDIENCE: str = "nutrimind-ai-api"
    REFRESH_TOKEN_SECRET_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""
    USDA_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENFOODFACTS_BASE_URL: str = "https://world.openfoodfacts.org/api/v2"
    OPENFOODFACTS_USER_AGENT: str = "NutriMindAI/1.0"

    @property
    def cors_origins_list(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for origin in self.CORS_ORIGINS.split(","):
            cleaned = origin.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                result.append(cleaned)
        return result

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        if v not in VALID_ENVIRONMENTS:
            raise ValueError(f"APP_ENV must be one of {sorted(VALID_ENVIRONMENTS)}, got '{v}'")
        return v

    @field_validator("PASSWORD_HASHING_SCHEMES")
    @classmethod
    def validate_hashing_schemes(cls, v: str) -> str:
        if v not in VALID_PASSWORD_HASHING_SCHEMES:
            raise ValueError(
                f"PASSWORD_HASHING_SCHEMES must be one of "
                f"{sorted(VALID_PASSWORD_HASHING_SCHEMES)}, got '{v}'"
            )
        return v

    @field_validator("API_V1_PREFIX")
    @classmethod
    def validate_prefix(cls, v: str) -> str:
        if not v.startswith("/"):
            raise ValueError("API_V1_PREFIX must start with '/'")
        normalized = v.rstrip("/")
        if not normalized:
            raise ValueError("API_V1_PREFIX must not be empty after normalization")
        return normalized

    @field_validator("JWT_ISSUER")
    @classmethod
    def validate_issuer(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("JWT_ISSUER must not be blank")
        return stripped

    @field_validator("JWT_AUDIENCE")
    @classmethod
    def validate_audience(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("JWT_AUDIENCE must not be blank")
        return stripped

    @model_validator(mode="after")
    def validate_production_debug(self):
        if self.APP_ENV == "production" and self.DEBUG:
            self.DEBUG = False
        return self

    @model_validator(mode="after")
    def validate_production_jwt_secrets(self):
        if self.APP_ENV == "production":
            validate_secret_strength(self.JWT_SECRET_KEY, "JWT_SECRET_KEY", required=True)
            validate_secret_strength(
                self.REFRESH_TOKEN_SECRET_KEY,
                "REFRESH_TOKEN_SECRET_KEY",
                required=True,
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the global Settings singleton. Cached after first call."""
    return Settings()
