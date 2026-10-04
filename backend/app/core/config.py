from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Placeholders that must never ship — even in local .env copies of .env.example.
_INSECURE_SECRETS = frozenset(
    {
        "dev-only-change-me",
        "change-me-to-a-long-random-string",
        "secret",
        "changeme",
    }
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+asyncpg://mycoach:mycoach@localhost:5433/mycoach"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = Field(min_length=32)
    access_token_minutes: int = 15
    refresh_token_days: int = 14
    cors_origins: str = (
        "http://localhost:3000,http://localhost:3001,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001"
    )
    environment: str = "development"
    cookie_secure: bool = False
    # How far back a user may complete/skip practices (no future dates).
    log_date_max_past_days: int = 14
    auth_rate_limit: int = 10
    auth_rate_window_seconds: int = 60

    @field_validator("database_url", mode="before")
    @classmethod
    def use_asyncpg_driver(cls, value: object) -> object:
        """Render supplies postgres:// or postgresql://. SQLAlchemy async needs asyncpg."""
        if not isinstance(value, str):
            return value
        url = value.strip()
        if url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]
        scheme, sep, rest = url.partition("://")
        if sep and scheme == "postgresql":
            url = "postgresql+asyncpg://" + rest
        # asyncpg does not accept libpq's sslmode query parameter.
        return (
            url.replace("sslmode=require", "ssl=require")
            .replace("sslmode=prefer", "ssl=prefer")
            .replace("sslmode=disable", "ssl=disable")
        )

    @field_validator("secret_key")
    @classmethod
    def secret_must_be_real(cls, value: str) -> str:
        if value.strip().lower() in _INSECURE_SECRETS:
            raise ValueError(
                "SECRET_KEY is a known placeholder. Generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return value

    @model_validator(mode="after")
    def harden_production(self) -> "Settings":
        if self.is_production:
            object.__setattr__(self, "cookie_secure", True)
            if not self.cors_origin_list:
                raise ValueError("CORS_ORIGINS must be set in production")
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        if self.is_production:
            return None
        # Next.js prints a LAN URL (http://192.168.x.x:3001). Browsers treat that as
        # a different origin than localhost, so signup/login fail without this.
        return (
            r"https?://(localhost|127\.0\.0\.1|"
            r"192\.168\.\d{1,3}\.\d{1,3}|"
            r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
            r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})"
            r"(:\d+)?$"
        )

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
