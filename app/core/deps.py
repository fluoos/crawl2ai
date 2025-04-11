from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from app.core.config import settings

async def get_api_key(api_key: Optional[str] = Header(None, alias="Authorization")):
    """
    验证并返回API密钥
    """
    # 如果配置中不需要API密钥验证，则直接返回
    if not settings.API_KEY_REQUIRED:
        return None
    
    # 检查API密钥是否存在
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少API密钥",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Bearer 前缀处理
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    # 验证API密钥是否有效
    if api_key != settings.DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API密钥无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key 