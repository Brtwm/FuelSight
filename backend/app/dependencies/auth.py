from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db_session
from app.core.security import decode_token
from app.services.auth_service import AuthenticatedUser, AuthService

http_bearer = HTTPBearer(auto_error=False)


def get_auth_service(session: Session = Depends(get_db_session)) -> AuthService:
    return AuthService(session)


def unauthorized_exception(
    message: str = "Требуется аутентификация",
    code: str = "http_error",
) -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": code, "message": message},
    )


def forbidden_exception(message: str = "Недостаточно прав") -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": "http_error", "message": message},
    )


def _extract_bearer_token(
    credentials: HTTPAuthorizationCredentials | None,
) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise unauthorized_exception()
    return credentials.credentials


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    token = _extract_bearer_token(credentials)
    try:
        payload = decode_token(
            token=token,
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expected_type="access",
        )
    except InvalidTokenError as exc:
        raise unauthorized_exception("Недействительный access token") from exc

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise unauthorized_exception("Некорректный payload access token")

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise unauthorized_exception("Некорректный payload access token") from exc

    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise unauthorized_exception("Пользователь не найден")
    return user


def require_roles(*allowed_roles: str):
    def dependency(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        if current_user.role not in allowed_roles:
            raise forbidden_exception()
        return current_user

    return dependency
