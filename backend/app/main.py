import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.router import api_router
from app.core.config import get_settings
from app.core.db import SessionLocal, engine
from app.core.exceptions import AppError
from app.core.logging import request_id_ctx
from app.core.seed import seed_catalog
from app.models import *  # noqa: F401,F403

settings = get_settings()


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        header = dict(scope.get("headers") or [])
        request_id = header.get(b"x-request-id", b"").decode() or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)

        async def send_with_id(message: dict) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers") or [])
                headers.append((b"x-request-id", request_id.encode()))
                message = {**message, "headers": headers}
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        finally:
            request_id_ctx.reset(token)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Schema comes from Alembic (`alembic upgrade head`), not create_all.
    async with SessionLocal() as db:
        await seed_catalog(db)
    yield
    await engine.dispose()


app = FastAPI(title="MyCoach", version="0.1.0", lifespan=lifespan)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _error(status_code: int, code: str, message: str, request_id: str | None) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "request_id": request_id}},
    )


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _error(exc.status_code, exc.code, exc.detail["message"], request.headers.get("X-Request-ID"))


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        return _error(exc.status_code, detail["code"], detail.get("message", "Error"), request.headers.get("X-Request-ID"))
    return _error(exc.status_code, "HTTP_ERROR", str(detail), request.headers.get("X-Request-ID"))


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    message = "; ".join(
        f"{'.'.join(str(part) for part in err.get('loc', []))}: {err.get('msg')}" for err in exc.errors()
    )
    return _error(422, "VALIDATION_ERROR", message, request.headers.get("X-Request-ID"))


@app.get("/health", response_model=None)
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "down"},
        )
    return {"status": "ok", "database": "up"}


app.include_router(api_router)
