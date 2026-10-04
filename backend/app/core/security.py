import uuid
from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import get_settings

hasher = PasswordHasher()
settings = get_settings()

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return hasher.verify(password_hash, password)
    except VerifyMismatchError:
        return False


def _now() -> datetime:
    return datetime.now(UTC)


def create_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    expires_in = settings.access_token_minutes * 60
    payload = {
        "sub": str(user_id),
        "typ": "access",
        "exp": _now() + timedelta(minutes=settings.access_token_minutes),
        "iat": _now(),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM), expires_in


def create_refresh_token(user_id: uuid.UUID, token_id: uuid.UUID) -> str:
    payload = {
        "sub": str(user_id),
        "typ": "refresh",
        "jti": str(token_id),
        "exp": _now() + timedelta(days=settings.refresh_token_days),
        "iat": _now(),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str) -> dict:
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("typ") != expected_type:
        raise jwt.InvalidTokenError("unexpected token type")
    return payload


def hash_token(token: str) -> str:
    return hasher.hash(token)


def verify_token_hash(token: str, token_hash: str) -> bool:
    try:
        return hasher.verify(token_hash, token)
    except VerifyMismatchError:
        return False
