"""JWT Authentication for admin endpoints."""
import secrets
import hashlib
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


def hash_api_key(api_key: str) -> str:
    """Hash an API key for storage."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str) -> bool:
    """Verify an API key against env var (legacy support)."""
    if not settings.admin_api_key:
        return False
    return secrets.compare_digest(api_key, settings.admin_api_key)


async def verify_api_key_from_db(api_key: str) -> Optional[dict]:
    """Verify an API key against database."""
    from app.database import db

    key_hash = hash_api_key(api_key)
    result = await db.execute(
        """
        MATCH (k:ApiKey {key_hash: $key_hash})
        WHERE k.revoked_at IS NULL
        RETURN k.name, k.created_at
        """,
        {"key_hash": key_hash}
    )

    if result:
        return {"name": result[0].get("k.name"), "created_at": result[0].get("k.created_at")}
    return None


async def store_api_key(api_key: str, name: str) -> None:
    """Store a hashed API key in the database."""
    from app.database import db
    from datetime import datetime

    key_hash = hash_api_key(api_key)
    # Store only first 8 chars as prefix for identification
    key_prefix = api_key[:11]  # "nk_" + 8 chars
    now = datetime.utcnow().isoformat() + "Z"

    await db.execute(
        """
        CREATE (k:ApiKey {
            key_hash: $key_hash,
            key_prefix: $key_prefix,
            name: $name,
            created_at: $now,
            revoked_at: null
        })
        """,
        {"key_hash": key_hash, "key_prefix": key_prefix, "name": name, "now": now}
    )


async def revoke_api_key(key_prefix: str) -> bool:
    """Revoke an API key by its prefix."""
    from app.database import db
    from datetime import datetime

    now = datetime.utcnow().isoformat() + "Z"

    result = await db.execute(
        """
        MATCH (k:ApiKey {key_prefix: $key_prefix})
        WHERE k.revoked_at IS NULL
        SET k.revoked_at = $now
        RETURN k.name
        """,
        {"key_prefix": key_prefix, "now": now}
    )

    return len(result) > 0


async def list_api_keys() -> list[dict]:
    """List all API keys (without the actual keys)."""
    from app.database import db

    result = await db.execute(
        """
        MATCH (k:ApiKey)
        RETURN k.key_prefix, k.name, k.created_at, k.revoked_at
        ORDER BY k.created_at DESC
        """
    )

    return [
        {
            "prefix": r.get("k.key_prefix"),
            "name": r.get("k.name"),
            "created_at": r.get("k.created_at"),
            "revoked": r.get("k.revoked_at") is not None
        }
        for r in result
    ]


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
        # First check database
        db_key = await verify_api_key_from_db(token)
        if db_key:
            return {"type": "api_key", "sub": "admin", "key_name": db_key.get("name")}

        # Fall back to env var (legacy support)
        if settings.admin_api_key and verify_api_key(token):
            return {"type": "api_key", "sub": "admin"}

        raise AuthError("Invalid API key")

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
