from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.core.config import settings

async def get_api_key(x_api_key: Optional[str] = Header(None)):
    """验证API密钥（如需要）"""
    if settings.API_KEY_REQUIRED and x_api_key != settings.DEEPSEEK_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key 