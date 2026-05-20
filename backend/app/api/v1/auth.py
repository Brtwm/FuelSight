from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from jwt import InvalidTokenError

from app.core.config import Settings, get_settings
from app.core.responses import envelope, request_meta
from app.core.roles import ALL_AUTHENTICATED_ROLES, preferred_landing_route_for_role
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.dependencies.auth import get_auth_service, require_roles, unauthorized_exception
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    UserProfile,
)
from app.services.auth_service import AuthenticatedUser, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _resolve_preferred_landing_route(*, role: str) -> str | None:
    return preferred_landing_route_for_role(role)


def _build_user_profile(user: AuthenticatedUser) -> UserProfile:
    return UserProfile(
        id=user.id,
        email=user.email,
        role=user.role,
        display_name=user.display_name,
        preferred_landing_route=_resolve_preferred_landing_route(role=user.role),
    )


def _create_access_token(*, settings: Settings, user: AuthenticatedUser) -> str:
    return create_access_token(
        sub=str(user.id),
        role=user.role,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        ttl_minutes=settings.jwt_access_ttl_min,
    )


def _create_refresh_token(*, settings: Settings, user: AuthenticatedUser) -> str:
    return create_refresh_token(
        sub=str(user.id),
        role=user.role,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        ttl_days=settings.jwt_refresh_ttl_days,
    )


def _set_refresh_cookie(*, response: JSONResponse, settings: Settings, refresh_token: str) -> None:
    max_age = settings.jwt_refresh_ttl_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.auth_refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.app_env not in {"local", "test"},
        samesite="lax",
        path=settings.auth_refresh_cookie_path,
        max_age=max_age,
    )


def _delete_refresh_cookie(*, response: JSONResponse, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.auth_refresh_cookie_name,
        path=settings.auth_refresh_cookie_path,
        secure=settings.app_env not in {"local", "test"},
        httponly=True,
        samesite="lax",
    )


def _resolve_user_from_refresh(
    *,
    request: Request,
    settings: Settings,
    auth_service: AuthService,
) -> AuthenticatedUser:
    refresh_token = request.cookies.get(settings.auth_refresh_cookie_name)
    if not refresh_token:
        raise unauthorized_exception("Refresh token не найден", code="invalid_refresh_token")

    try:
        payload = decode_token(
            token=refresh_token,
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            expected_type="refresh",
        )
    except InvalidTokenError as exc:
        raise unauthorized_exception(
            "Недействительный refresh token",
            code="invalid_refresh_token",
        ) from exc

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise unauthorized_exception(
            "Некорректный payload refresh token",
            code="invalid_refresh_token",
        )

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise unauthorized_exception(
            "Некорректный payload refresh token",
            code="invalid_refresh_token",
        ) from exc

    user = auth_service.get_user_by_id(user_id=user_id)
    if user is None:
        raise unauthorized_exception("Пользователь не найден", code="invalid_refresh_token")
    return user


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
):
    user = auth_service.authenticate(email=payload.email, password=payload.password)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_credentials", "message": "Неверный email или пароль"},
        )

    response_payload = LoginResponse(
        access_token=_create_access_token(settings=settings, user=user),
        token_type="bearer",
        expires_in=settings.jwt_access_ttl_min * 60,
        user=_build_user_profile(user),
    )
    refresh_token = _create_refresh_token(settings=settings, user=user)

    response = JSONResponse(
        status_code=200,
        content=envelope(
            data=response_payload.model_dump(mode="json"),
            error=None,
            meta=request_meta(request),
        ),
    )
    _set_refresh_cookie(response=response, settings=settings, refresh_token=refresh_token)
    return response


@router.post("/refresh")
def refresh(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
):
    user = _resolve_user_from_refresh(request=request, settings=settings, auth_service=auth_service)
    new_access_token = _create_access_token(settings=settings, user=user)
    new_refresh_token = _create_refresh_token(settings=settings, user=user)
    response_payload = RefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_ttl_min * 60,
    )
    response = JSONResponse(
        status_code=200,
        content=envelope(
            data=response_payload.model_dump(mode="json"),
            error=None,
            meta=request_meta(request),
        ),
    )
    _set_refresh_cookie(response=response, settings=settings, refresh_token=new_refresh_token)
    return response


@router.get("/me")
def me(
    request: Request,
    current_user: AuthenticatedUser = Depends(require_roles(*ALL_AUTHENTICATED_ROLES)),
):
    return envelope(
        data=_build_user_profile(current_user).model_dump(mode="json"),
        error=None,
        meta=request_meta(request),
    )


@router.post("/logout")
def logout(
    request: Request,
    _: AuthenticatedUser = Depends(require_roles(*ALL_AUTHENTICATED_ROLES)),
    settings: Settings = Depends(get_settings),
):
    payload = LogoutResponse(ok=True)
    response = JSONResponse(
        status_code=200,
        content=envelope(
            data=payload.model_dump(mode="json"),
            error=None,
            meta=request_meta(request),
        ),
    )
    _delete_refresh_cookie(response=response, settings=settings)
    return response
