"""Simple in-memory rate limiting."""
import time
from collections import defaultdict
from fastapi import Request, HTTPException

from app.config import settings


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)

    def _clean_old_requests(self, key: str, window: int):
        """Remove requests outside the current window."""
        cutoff = time.time() - window
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]

    def is_allowed(self, key: str, max_requests: int = None, window: int = None) -> bool:
        """Check if request is allowed under rate limit."""
        max_requests = max_requests or settings.rate_limit_requests
        window = window or settings.rate_limit_window

        self._clean_old_requests(key, window)

        if len(self.requests[key]) >= max_requests:
            return False

        self.requests[key].append(time.time())
        return True

    def get_retry_after(self, key: str, window: int = None) -> int:
        """Get seconds until rate limit resets."""
        window = window or settings.rate_limit_window
        if not self.requests[key]:
            return 0
        oldest = min(self.requests[key])
        return max(0, int(window - (time.time() - oldest)))


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(
    request: Request,
    max_requests: int = None,
    window: int = None,
    key_prefix: str = ""
):
    """
    Rate limit dependency for FastAPI endpoints.

    Usage:
        @router.post("/subscribe")
        async def subscribe(
            request: Request,
            _: None = Depends(lambda r: check_rate_limit(r, max_requests=5))
        ):
            ...
    """
    client_ip = get_client_ip(request)
    key = f"{key_prefix}:{client_ip}" if key_prefix else client_ip

    if not rate_limiter.is_allowed(key, max_requests, window):
        retry_after = rate_limiter.get_retry_after(key, window)
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)}
        )
