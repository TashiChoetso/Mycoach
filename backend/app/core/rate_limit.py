"""Simple sliding-window rate limiter (in-memory).

Fine for a single uvicorn worker / friends beta. Multi-worker production
should put a reverse-proxy or Redis limiter in front.
"""

from __future__ import annotations

import time
from collections import defaultdict

from app.core.exceptions import RateLimited

_buckets: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(key: str, *, limit: int, window_seconds: int) -> None:
    now = time.monotonic()
    cutoff = now - window_seconds
    hits = [stamp for stamp in _buckets[key] if stamp > cutoff]
    if len(hits) >= limit:
        _buckets[key] = hits
        raise RateLimited("Too many attempts. Wait a minute and try again.")
    hits.append(now)
    _buckets[key] = hits


def reset_rate_limits() -> None:
    """Test helper."""
    _buckets.clear()


def client_key(request, suffix: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{suffix}:{host}"
