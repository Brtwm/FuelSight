from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import verify_password
from app.models import User


@dataclass(frozen=True)
class AuthenticatedUser:
    id: UUID
    email: str
    role: str
    display_name: str
    is_active: bool


class AuthService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def authenticate(self, email: str, password: str) -> AuthenticatedUser | None:
        user = self._find_user_by_email(email=email)
        if user is None or user.role is None:
            return None
        if not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return self._to_authenticated_user(user)

    def get_user_by_id(self, user_id: UUID) -> AuthenticatedUser | None:
        user = self._session.scalar(
            select(User).options(joinedload(User.role)).where(User.id == user_id)
        )
        if user is None or user.role is None:
            return None
        if not user.is_active:
            return None
        return self._to_authenticated_user(user)

    def _find_user_by_email(self, *, email: str) -> User | None:
        return self._session.scalar(
            select(User).options(joinedload(User.role)).where(User.email == email)
        )

    @staticmethod
    def _to_authenticated_user(user: User) -> AuthenticatedUser:
        return AuthenticatedUser(
            id=user.id,
            email=user.email,
            role=user.role.slug,
            display_name=user.display_name,
            is_active=user.is_active,
        )
