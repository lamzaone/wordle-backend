from __future__ import annotations

from functools import lru_cache
from typing import Any, Literal
from urllib.parse import urlparse
from uuid import UUID

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _split_csv(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        enable_decoding=False,
    )

    app_name: str = "Wordle Backend"
    environment: Literal["local", "development", "staging", "production", "test"] = "development"
    debug: bool = False
    api_v1_prefix: str = ""

    database_url: str

    supabase_url: str
    supabase_anon_key: SecretStr
    supabase_jwks_url: str | None = None
    supabase_jwt_issuer: str | None = None
    supabase_jwt_audience: str = "authenticated"
    supabase_jwt_algorithms: list[str] = Field(default_factory=lambda: ["RS256", "ES256"])
    supabase_jwt_secret: SecretStr | None = None

    allowed_word_lengths: list[int] = Field(default_factory=lambda: [4, 5, 6, 7])
    default_max_attempts: int = 6
    enforce_dictionary_guesses: bool = True
    one_active_classic_game_per_length: bool = True
    daily_challenge_timezone: str = "UTC"

    admin_user_ids: list[UUID] = Field(default_factory=list)
    cors_origins: list[str] = Field(default_factory=list)
    guesses_rate_limit_per_minute: int = 30
    jwks_cache_ttl_seconds: int = 3600

    score_base_by_length: dict[int, int] = Field(default_factory=lambda: {4: 80, 5: 100, 6: 130, 7: 160})
    score_win_bonus: int = 25
    score_remaining_attempt_bonus: int = 10
    score_daily_bonus: int = 20

    @field_validator("allowed_word_lengths", mode="before")
    @classmethod
    def parse_allowed_word_lengths(cls, value: Any) -> list[int]:
        if isinstance(value, list):
            return [int(item) for item in value]
        return [int(item) for item in _split_csv(value)]

    @field_validator("supabase_jwt_algorithms", mode="before")
    @classmethod
    def parse_jwt_algorithms(cls, value: Any) -> list[str]:
        return _split_csv(value) or ["RS256", "ES256"]

    @field_validator("admin_user_ids", mode="before")
    @classmethod
    def parse_admin_user_ids(cls, value: Any) -> list[UUID]:
        return [UUID(item) for item in _split_csv(value)]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        return _split_csv(value)

    @field_validator("score_base_by_length", mode="before")
    @classmethod
    def parse_score_base_by_length(cls, value: Any) -> dict[int, int]:
        if isinstance(value, dict):
            return {int(key): int(score) for key, score in value.items()}
        if value is None or value == "":
            return {4: 80, 5: 100, 6: 130, 7: 160}
        parsed: dict[int, int] = {}
        for item in _split_csv(value):
            length, score = item.split(":", maxsplit=1)
            parsed[int(length)] = int(score)
        return parsed

    @model_validator(mode="after")
    def validate_database_url(self) -> "Settings":
        lowered = self.database_url.lower()
        if "sqlite" in lowered:
            raise ValueError("SQLite is not allowed. DATABASE_URL must point to Supabase Cloud Postgres.")
        parsed = urlparse(self.database_url.replace("postgresql+asyncpg://", "postgresql://", 1))
        local_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
        if parsed.hostname in local_hosts:
            raise ValueError("Local databases are not allowed. DATABASE_URL must point to Supabase Cloud Postgres.")
        if not (lowered.startswith("postgresql://") or lowered.startswith("postgresql+asyncpg://") or lowered.startswith("postgres://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection URL for Supabase Cloud.")
        return self

    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        if self.database_url.startswith("postgres://"):
            return self.database_url.replace("postgres://", "postgresql+asyncpg://", 1)
        return self.database_url

    @property
    def jwt_issuer(self) -> str:
        if self.supabase_jwt_issuer:
            return self.supabase_jwt_issuer.rstrip("/")
        return f"{self.supabase_url.rstrip('/')}/auth/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
