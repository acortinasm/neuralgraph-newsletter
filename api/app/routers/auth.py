"""Authentication endpoints."""
import secrets
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional

from app.config import settings
from app.auth import (
    create_access_token, get_current_user, generate_api_key, require_admin,
    store_api_key, revoke_api_key, list_api_keys,
    COOKIE_NAME, COOKIE_MAX_AGE,
)
from app.rate_limit import check_rate_limit

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400  # 24 hours in seconds


class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Name to identify this API key")


class ApiKeyResponse(BaseModel):
    api_key: str
    prefix: str
    name: str
    message: str


class ApiKeyInfo(BaseModel):
    prefix: str
    name: str
    created_at: Optional[str]
    revoked: bool


async def rate_limit_login(request: Request):
    """Strict rate limit for login: 5 attempts per 5 minutes."""
    await check_rate_limit(request, max_requests=5, window=300, key_prefix="login")


@router.post("/login")
async def login(
    credentials: LoginRequest,
    _: None = Depends(rate_limit_login)
):
    """
    Authenticate with username/password.

    Sets an httpOnly cookie with the JWT token and returns a success response.
    The token is also returned in the body for programmatic (non-browser) clients.
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

    response = JSONResponse(content={
        "access_token": token,
        "token_type": "bearer",
        "expires_in": COOKIE_MAX_AGE,
    })

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=COOKIE_MAX_AGE,
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
        path="/",
    )

    return response


@router.post("/logout")
async def logout():
    """Clear the session cookie."""
    response = JSONResponse(content={"success": True})
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        secure=not settings.debug,
        samesite="lax",
    )
    return response


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
async def create_api_key_endpoint(
    request: CreateApiKeyRequest,
    admin: dict = Depends(require_admin)
):
    """
    Generate and store a new API key.

    The key is stored securely (hashed) in the database.
    Save the returned key - it cannot be retrieved later.
    """
    new_key = generate_api_key()

    try:
        await store_api_key(new_key, request.name)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to store API key")

    return ApiKeyResponse(
        api_key=new_key,
        prefix=new_key[:11],
        name=request.name,
        message="Save this key securely. It cannot be retrieved later."
    )


@router.get("/api-keys", response_model=list[ApiKeyInfo])
async def list_api_keys_endpoint(admin: dict = Depends(require_admin)):
    """List all API keys (shows prefix and name only, not the full key)."""
    keys = await list_api_keys()
    return [ApiKeyInfo(**k) for k in keys]


@router.delete("/api-key/{key_prefix}")
async def revoke_api_key_endpoint(
    key_prefix: str,
    admin: dict = Depends(require_admin)
):
    """
    Revoke an API key by its prefix.

    The prefix is the first 11 characters of the key (e.g., 'nk_abc12345').
    """
    success = await revoke_api_key(key_prefix)

    if not success:
        raise HTTPException(status_code=404, detail="API key not found or already revoked")

    return {"message": f"API key {key_prefix}... revoked"}


@router.post("/verify")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """Verify that a token or API key is valid."""
    return {"valid": True, "user": current_user}
