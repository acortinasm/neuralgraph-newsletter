from fastapi import Header, HTTPException

from config import settings


def require_admin(x_api_key: str = Header()) -> str:
    if x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
