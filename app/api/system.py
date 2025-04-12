from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from app.services.system_service import SystemService

router = APIRouter()

class SystemConfig(BaseModel):
    baseUrl: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    apiKey: str = ""
    temperature: float = 0.7
    maxTokens: int = 4000
    logLevel: str = "info"

@router.get("/config")
async def get_system_config():
    """获取系统配置"""
    try:
        return SystemService.get_system_config()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def update_system_config(config: SystemConfig):
    """更新系统配置"""
    try:
        return SystemService.update_system_config(config.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 