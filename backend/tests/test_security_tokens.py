import pytest
from jwt import InvalidTokenError

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

TEST_SECRET = "phase9-test-secret-with-32-plus-chars"


def test_hash_and_verify_password_roundtrip() -> None:
    password = "admin12345"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-pass", password_hash) is False


def test_decode_access_token_success() -> None:
    token = create_access_token(
        sub="f6b2c204-94ba-4bc4-8cbf-9f59f73995b1",
        role="admin",
        secret_key=TEST_SECRET,
        algorithm="HS256",
        ttl_minutes=30,
    )

    payload = decode_token(
        token=token,
        secret_key=TEST_SECRET,
        algorithm="HS256",
        expected_type="access",
    )

    assert payload["sub"] == "f6b2c204-94ba-4bc4-8cbf-9f59f73995b1"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"


def test_decode_token_rejects_wrong_type() -> None:
    token = create_refresh_token(
        sub="f6b2c204-94ba-4bc4-8cbf-9f59f73995b1",
        role="analyst",
        secret_key=TEST_SECRET,
        algorithm="HS256",
        ttl_days=7,
    )

    with pytest.raises(InvalidTokenError):
        decode_token(
            token=token,
            secret_key=TEST_SECRET,
            algorithm="HS256",
            expected_type="access",
        )
