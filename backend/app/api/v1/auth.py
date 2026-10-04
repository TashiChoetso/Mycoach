from fastapi import APIRouter, Depends, Request, Response

from app.core.config import get_settings
from app.core.deps import CurrentUser, DbSession
from app.core.exceptions import Unauthorized
from app.core.rate_limit import check_rate_limit, client_key
from app.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()
COOKIE = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure or settings.is_production,
        max_age=settings.refresh_token_days * 24 * 60 * 60,
        path="/api/v1/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE, path="/api/v1/auth")


def _auth_limit(request: Request, action: str) -> None:
    check_rate_limit(
        client_key(request, action),
        limit=settings.auth_rate_limit,
        window_seconds=settings.auth_rate_window_seconds,
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegisterRequest, request: Request, response: Response, db: DbSession) -> TokenResponse:
    _auth_limit(request, "register")
    result = await AuthService(db).register(payload)
    _set_refresh_cookie(response, result.refresh_token)
    return result


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, response: Response, db: DbSession) -> TokenResponse:
    _auth_limit(request, "login")
    result = await AuthService(db).login(payload)
    _set_refresh_cookie(response, result.refresh_token)
    return result


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: DbSession,
    payload: RefreshRequest | None = None,
) -> TokenResponse:
    token = (payload.refresh_token if payload else None) or request.cookies.get(COOKIE)
    if not token:
        raise Unauthorized()
    result = await AuthService(db).refresh(token)
    _set_refresh_cookie(response, result.refresh_token)
    return result


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    response: Response,
    db: DbSession,
    payload: RefreshRequest | None = None,
) -> None:
    token = (payload.refresh_token if payload else None) or request.cookies.get(COOKIE)
    await AuthService(db).logout(token)
    _clear_refresh_cookie(response)


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, request: Request, db: DbSession) -> dict:
    _auth_limit(request, "forgot")
    token = await AuthService(db).request_password_reset(payload.email)
    # Never reveal whether the email exists. In non-production, return the
    # token so local/dev can exercise the flow without an email provider.
    body: dict = {"ok": True}
    if token and not settings.is_production:
        body["reset_token"] = token
    return body


@router.post("/reset-password", status_code=204)
async def reset_password(payload: ResetPasswordRequest, request: Request, db: DbSession) -> None:
    _auth_limit(request, "reset")
    await AuthService(db).reset_password(payload.token, payload.password)


@router.post("/change-password", status_code=204)
async def change_password(payload: ChangePasswordRequest, user: CurrentUser, db: DbSession) -> None:
    await AuthService(db).change_password(user, payload.current_password, payload.new_password)
