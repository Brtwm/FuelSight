from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.security import hash_password, verify_password
from app.models import Role, User
from app.scripts import seed_core


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
        yield db_session


def test_seed_demo_users_flag_defaults_to_enabled() -> None:
    assert seed_core.should_seed_demo_users(Settings()) is True


def test_seed_demo_users_flag_can_disable_demo_accounts() -> None:
    assert seed_core.should_seed_demo_users(Settings(fuelsight_seed_demo_users=False)) is False


def test_upsert_roles_creates_target_roles(session: Session) -> None:
    created, updated = seed_core.upsert_roles(session)
    session.flush()

    roles = {role.slug: role.name for role in session.scalars(select(Role))}

    assert created == 5
    assert updated == 0
    assert roles == {
        "admin": "Системный администратор",
        "sales": "Отдел продаж",
        "accounting": "Бухгалтерия",
        "analyst": "Аналитический отдел",
        "director": "Генеральный директор",
    }


def test_upsert_users_creates_demo_users_with_hashed_passwords(session: Session) -> None:
    seed_core.upsert_roles(session)
    session.flush()

    created, updated = seed_core.upsert_users(session)
    session.flush()

    users = {
        user.email: user
        for user in session.scalars(
            select(User).join(Role).where(User.email.like("%@fuelsight.local"))
        )
    }

    assert created == 5
    assert updated == 0
    assert set(users) == {
        "admin@fuelsight.local",
        "sales@fuelsight.local",
        "accounting@fuelsight.local",
        "analyst@fuelsight.local",
        "director@fuelsight.local",
    }
    for item in seed_core.USER_SEEDS:
        user = users[item.email]
        assert user.password_hash != item.password
        assert verify_password(item.password, user.password_hash)
        assert user.role.slug == item.role_slug


def test_upsert_seed_data_is_idempotent(session: Session) -> None:
    assert seed_core.upsert_roles(session) == (5, 0)
    session.flush()
    assert seed_core.upsert_users(session) == (5, 0)
    session.flush()

    assert seed_core.upsert_roles(session) == (0, 0)
    assert seed_core.upsert_users(session) == (0, 0)
    session.flush()

    admin_role = session.scalar(select(Role).where(Role.slug == "admin"))
    analyst_role = session.scalar(select(Role).where(Role.slug == "analyst"))

    assert admin_role.name == "Системный администратор"
    assert analyst_role.name == "Аналитический отдел"
    assert len(session.scalars(select(Role)).all()) == 5
    assert len(session.scalars(select(User)).all()) == 5


def test_upsert_users_corrects_only_demo_accounts(session: Session) -> None:
    seed_core.upsert_roles(session)
    session.flush()

    roles = {role.slug: role for role in session.scalars(select(Role))}
    session.add_all(
        [
            User(
                id=uuid4(),
                email="sales@fuelsight.local",
                password_hash=hash_password("old-password"),
                display_name="Old Sales",
                role_id=roles["analyst"].id,
                is_active=False,
            ),
            User(
                id=uuid4(),
                email="employee@example.com",
                password_hash=hash_password("employee-password"),
                display_name="Employee",
                role_id=roles["analyst"].id,
                is_active=False,
            ),
        ]
    )
    session.flush()

    created, updated = seed_core.upsert_users(session)
    session.flush()

    demo_user = session.scalar(select(User).where(User.email == "sales@fuelsight.local"))
    unrelated_user = session.scalar(select(User).where(User.email == "employee@example.com"))

    assert created == 4
    assert updated == 1
    assert demo_user.display_name == "FuelSight Sales"
    assert demo_user.role.slug == "sales"
    assert demo_user.is_active is True
    assert verify_password("sales12345", demo_user.password_hash)
    assert unrelated_user.display_name == "Employee"
    assert unrelated_user.role.slug == "analyst"
    assert unrelated_user.is_active is False
    assert verify_password("employee-password", unrelated_user.password_hash)
