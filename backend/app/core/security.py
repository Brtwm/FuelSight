"""Security primitives: password hashing and JWT token lifecycle."""

from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt
from jwt import InvalidTokenError

TokenType = Literal["access", "refresh"]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(
    *,
    sub: str,
    role: str,
    token_type: TokenType,
    secret_key: str,
    algorithm: str,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": sub,
        "role": role,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_access_token(
    *,
    sub: str,
    role: str,
    secret_key: str,
    algorithm: str,
    ttl_minutes: int,
) -> str:
    return create_token(
        sub=sub,
        role=role,
        token_type="access",
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=timedelta(minutes=ttl_minutes),
    )


def create_refresh_token(
    *,
    sub: str,
    role: str,
    secret_key: str,
    algorithm: str,
    ttl_days: int,
) -> str:
    return create_token(
        sub=sub,
        role=role,
        token_type="refresh",
        secret_key=secret_key,
        algorithm=algorithm,
        expires_delta=timedelta(days=ttl_days),
    )


def decode_token(
    *,
    token: str,
    secret_key: str,
    algorithm: str,
    expected_type: TokenType,
) -> dict[str, Any]:
    payload = jwt.decode(
        token,
        secret_key,
        algorithms=[algorithm],
        options={"require": ["sub", "type", "exp"]},
    )
    if payload.get("type") != expected_type:
        raise InvalidTokenError(f"Unexpected token type: {payload.get('type')}")
    return payload
