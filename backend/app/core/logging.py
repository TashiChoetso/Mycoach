from contextvars import ContextVar
from typing import Any

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return request_id_ctx.get()


def log_extra(**kwargs: Any) -> dict[str, Any]:
    return {"request_id": get_request_id(), **kwargs}
