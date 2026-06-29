from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import verify_password
from app.models import Role, User
from app.scripts.create_reviewer import upsert_reviewer


@pytest.fixture()
def session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def register_uuid_function(dbapi_connection, _connection_record):  # noqa: ANN001
        dbapi_connection.create_function("gen_random_uuid", 0, lambda: str(uuid4()))

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug VARCHAR(32) UNIQUE NOT NULL,
                    name VARCHAR(64) NOT NULL
                )
                """
            )
        )
        connection.execute(
            text(
                """
                CREATE TABLE users (
                    id TEXT PRIMARY KEY DEFAULT (gen_random_uuid()),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    display_name VARCHAR(128) NOT NULL,
                    role_id SMALLINT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
    with SessionLocal() as db_session:
        db_session.add_all(
            [
                Role(slug="analyst", name="Аналитик"),
                Role(slug="director", name="Директор"),
                Role(slug="admin", name="Администратор"),
            ]
        )
        db_session.commit()
        yield db_session


def test_upsert_reviewer_creates_analyst_with_hashed_password(session: Session) -> None:
    created = upsert_reviewer(
        session,
        email="commission@example.com",
        password="strong-reviewer-password",
        display_name="Приемная комиссия",
        role_slug="analyst",
    )
    session.commit()

    user = session.scalar(select(User).where(User.email == "commission@example.com"))
    assert created is True
    assert user is not None
    assert user.role.slug == "analyst"
    assert verify_password("strong-reviewer-password", user.password_hash)


def test_upsert_reviewer_rejects_admin_role(session: Session) -> None:
    with pytest.raises(ValueError, match="reviewer_role_not_allowed"):
        upsert_reviewer(
            session,
            email="admin@example.com",
            password="strong-reviewer-password",
            display_name="Admin",
            role_slug="admin",
        )


def test_upsert_reviewer_rejects_password_over_bcrypt_limit(session: Session) -> None:
    with pytest.raises(ValueError, match="password_too_long"):
        upsert_reviewer(
            session,
            email="commission@example.com",
            password="x" * 73,
            display_name="Приемная комиссия",
            role_slug="director",
        )
