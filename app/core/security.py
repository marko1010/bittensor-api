from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="Authorization", auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header.startswith("Bearer "):
        api_key = api_key_header.replace("Bearer ", "")
    else:
        api_key = api_key_header

    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return api_key 