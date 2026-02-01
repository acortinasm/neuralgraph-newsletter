"""JWT Authentication for admin endpoints."""
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from app.config import settings

# Security scheme
bearer_scheme = HTTPBearer(auto_error=False)

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


class AuthError(HTTPException):
    """Authentication error."""

    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")


def verify_api_key(api_key: str) -> bool:
    """Verify an API key against stored keys."""
    # Compare using constant-time comparison to prevent timing attacks
    return secrets.compare_digest(api_key, settings.admin_api_key)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> dict:
    """
    Dependency to get current authenticated user.
    Supports both JWT tokens and API keys.
    """
    if credentials is None:
        raise AuthError("Authentication required")

    token = credentials.credentials

    # Check if it's an API key (starts with 'nk_')
    if token.startswith("nk_"):
        if not settings.admin_api_key:
            raise AuthError("API key authentication not configured")
        if not verify_api_key(token):
            raise AuthError("Invalid API key")
        return {"type": "api_key", "sub": "admin"}

    # Otherwise treat as JWT
    payload = decode_token(token)
    return {"type": "jwt", "sub": payload.get("sub"), "role": payload.get("role", "user")}


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """Dependency to require admin role."""
    if user.get("type") == "api_key":
        return user  # API keys are always admin
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return user


def generate_api_key() -> str:
    """Generate a new API key."""
    return f"nk_{secrets.token_urlsafe(32)}"
