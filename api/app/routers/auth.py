"""Authentication endpoints."""
import secrets
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from app.config import settings
from app.auth import create_access_token, get_current_user, generate_api_key, require_admin
from app.rate_limit import check_rate_limit

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours in seconds


class ApiKeyResponse(BaseModel):
    api_key: str
    message: str


async def rate_limit_login(request: Request):
    """Strict rate limit for login: 5 attempts per 5 minutes."""
    await check_rate_limit(request, max_requests=5, window=300, key_prefix="login")


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: LoginRequest,
    _: None = Depends(rate_limit_login)
):
    """
    Authenticate with username/password to get a JWT token.

    Default admin credentials must be configured via environment variables:
    - ADMIN_USERNAME (default: admin)
    - ADMIN_PASSWORD (required)
    """
    if not settings.admin_password:
        raise HTTPException(
            status_code=500,
            detail="Admin authentication not configured. Set ADMIN_PASSWORD env var."
        )

    # Constant-time comparison to prevent timing attacks
    username_valid = secrets.compare_digest(credentials.username, settings.admin_username)
    password_valid = secrets.compare_digest(credentials.password, settings.admin_password)

    if not (username_valid and password_valid):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    token = create_access_token({"sub": credentials.username, "role": "admin"})

    return TokenResponse(access_token=token)


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user info."""
    return {
        "authenticated": True,
        "type": current_user.get("type"),
        "subject": current_user.get("sub"),
        "role": current_user.get("role", "admin" if current_user.get("type") == "api_key" else "user")
    }


@router.post("/api-key", response_model=ApiKeyResponse)
async def create_api_key(admin: dict = Depends(require_admin)):
    """
    Generate a new API key.

    Note: This generates the key but doesn't store it.
    You must save it to ADMIN_API_KEY env var to use it.
    """
    new_key = generate_api_key()

    return ApiKeyResponse(
        api_key=new_key,
        message="Save this key securely. Set it as ADMIN_API_KEY env var to use it."
    )


@router.post("/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify that a token or API key is valid."""
    return {"valid": True, "user": current_user}
