"""Configuración tipada con Pydantic Settings.

Carga variables de entorno y/o archivo .env. Se accede como singleton
mediante `get_settings()` para que sea cacheable y testeable.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "UniNet Connect"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"

    SECRET_KEY: str = Field(min_length=16)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    DATABASE_URL: PostgresDsn
    REDIS_URL: str = "redis://localhost:6379/0"

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    # SMTP opcional para notificaciones por correo (RF005). Si SMTP_HOST
    # está vacío, las notificaciones se entregan sólo in-app y el correo
    # se loggea (mismo patrón que el código MFA en dev).
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "noreply@uninet.escom.ipn.mx"
    SMTP_USE_TLS: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def split_cors(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def smtp_enabled(self) -> bool:
        return bool(self.SMTP_HOST)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
