import re
from functools import lru_cache
from urllib.parse import quote, unquote, urlsplit, urlunsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import URL, make_url
from sqlalchemy.exc import ArgumentError

# Placeholders that must never ship — even in local .env copies of .env.example.
_INSECURE_SECRETS = frozenset(
    {
        "dev-only-change-me",
        "change-me-to-a-long-random-string",
        "secret",
        "changeme",
    }
)

_POSTGRES_URL = re.compile(r"postgres(?:ql)?(?:\+[A-Za-z0-9_]+)?://\S+")
_PSQL_COMMAND = re.compile(
    r"PGPASSWORD=(?P<password>\S+)\s+psql\s+"
    r"(?:-p\s+(?P<port>\d+)\s+)?"
    r"-h\s+(?P<host>\S+)\s+"
    r"(?:-p\s+(?P<port2>\d+)\s+)?"
    r"-U\s+(?P<user>\S+)\s+"
    r"(?P<database>\S+)"
)


def _clean_database_url(value: str) -> str:
    return value.strip().strip("'\"").replace("\ufeff", "").replace("\u200b", "").strip()


def _postgres_url(value: str) -> str | None:
    match = _POSTGRES_URL.search(value)
    if match is None:
        return None
    return match.group(0).rstrip("'\".,)")


def _psql_command(value: str) -> URL | None:
    match = _PSQL_COMMAND.search(value)
    if match is None:
        return None
    port = match.group("port") or match.group("port2")
    return URL.create(
        drivername="postgresql+asyncpg",
        username=match.group("user"),
        password=match.group("password"),
        host=match.group("host"),
        port=int(port) if port else 5432,
        database=match.group("database"),
    )


def _asyncpg_url(value: str) -> str:
    command = _psql_command(value)
    if command is not None:
        return command.render_as_string(hide_password=False)

    found = _postgres_url(value)
    if found is None:
        return value
    # The last @ separates userinfo from the host. Passwords may contain @ / # ?.
    scheme, _sep, rest = found.partition("://")
    if "@" in rest:
        userinfo, hostpart = rest.rsplit("@", 1)
        if ":" in userinfo:
            user, password = userinfo.split(":", 1)
            userinfo = f"{quote(unquote(user), safe='')}:{quote(unquote(password), safe='')}"
        else:
            userinfo = quote(unquote(userinfo), safe="")
    else:
        userinfo = ""
        hostpart = rest
    if "?" in hostpart:
        hostpart, query = hostpart.split("?", 1)
    else:
        query = ""
    found = f"{scheme}://{userinfo + '@' if userinfo else ''}{hostpart}"
    if query:
        found = f"{found}?{query}"
    parts = urlsplit(found)
    query_text = (
        parts.query.replace("sslmode=require", "ssl=require")
        .replace("sslmode=prefer", "ssl=prefer")
        .replace("sslmode=allow", "ssl=require")
        .replace("sslmode=disable", "ssl=disable")
    )
    driver = "postgresql+asyncpg"
    return urlunsplit((driver, parts.netloc, parts.path, query_text, ""))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+asyncpg://mycoach:mycoach@localhost:5433/mycoach"
    # Set from the Render database when DATABASE_URL itself is not a usable URL.
    db_host: str | None = None
    db_port: str | None = None
    db_user: str | None = None
    db_password: str | None = None
    db_name: str | None = None
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
        cleaned = _clean_database_url(value)
        if _postgres_url(cleaned) is None and _psql_command(cleaned) is None:
            # Leave non-URL values for the model validator, which can build the
            # URL from DB_HOST / DB_USER / DB_PASSWORD / DB_NAME instead.
            return cleaned
        return _asyncpg_url(cleaned)

    @model_validator(mode="after")
    def assemble_database_url(self) -> "Settings":
        if self.db_host and self.db_user and self.db_password is not None and self.db_name:
            port = int(self.db_port) if self.db_port else 5432
            built = URL.create(
                drivername="postgresql+asyncpg",
                username=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=port,
                database=self.db_name,
            )
            object.__setattr__(
                self, "database_url", built.render_as_string(hide_password=False)
            )
        try:
            make_url(self.database_url)
        except (ArgumentError, ValueError) as exc:
            raise ValueError(
                "DATABASE_URL is not a Postgres connection URL. "
                "It must look like postgresql://USER:PASSWORD@HOST:PORT/DATABASE."
            ) from exc
        return self

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
