from fastapi import APIRouter, HTTPException, Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.services.system_service import SystemService

router = APIRouter()

class SystemConfig(BaseModel):
    baseUrl: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    apiKey: str = ""
    temperature: float = 0.7
    maxTokens: int = 4000
    logLevel: str = "info"

class ModelConfig(BaseModel):
    id: Optional[str] = None
    name: str
    model: str
    apiEndpoint: str
    apiKey: str
    type: str = "chat"
    temperature: float = 0.7
    maxTokens: int = 4000
    isDefault: bool = False

class PromptsConfig(BaseModel):
    data: str = ""

class FileStrategyConfig(BaseModel):
    chunkSize: int = 2000
    overlapSize: int = 200
    preserveMarkdown: bool = True
    smartChunking: bool = True

@router.get("/config/models")
async def get_models():
    """获取所有模型配置"""
    try:
        return SystemService.get_models()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/models/add")
async def add_model(model: ModelConfig):
    """添加模型配置"""
    try:
        return SystemService.add_model(model.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/models/{model_id}")
async def update_model(
    model: ModelConfig,
    model_id: str = Path(..., description="模型ID")
):
    """更新模型配置"""
    try:
        model_dict = model.dict()
        model_dict["id"] = model_id
        return SystemService.update_model(model_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/models/{model_id}/delete")
async def delete_model(model_id: str = Path(..., description="模型ID")):
    """删除模型配置"""
    try:
        return SystemService.delete_model(model_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/models/{model_id}/default")
async def set_default_model(model_id: str = Path(..., description="模型ID")):
    """设置默认模型"""
    try:
        return SystemService.set_default_model(model_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/prompts")
async def get_prompts():
    """获取提示词配置"""
    try:
        return SystemService.get_prompts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/prompts")
async def update_prompts(prompts: PromptsConfig):
    """更新提示词配置"""
    try:
        return SystemService.update_prompts(prompts.data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/config/prompts/reset")
async def reset_prompts():
    """重置提示词配置"""
    try:
        return SystemService.reset_prompts()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/file-strategy")
async def get_file_strategy():
    """获取文件策略配置"""
    try:
        return SystemService.get_file_strategy()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/file-strategy")
async def update_file_strategy(strategy: FileStrategyConfig):
    """更新文件策略配置"""
    try:
        return SystemService.update_file_strategy({
            "chunkSize": strategy.chunkSize,
            "overlapSize": strategy.overlapSize,
            "preserveMarkdown": strategy.preserveMarkdown,
            "smartChunking": strategy.smartChunking
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/file-strategy/reset")
async def reset_file_strategy():
    """重置文件策略配置"""
    try:
        return SystemService.reset_file_strategy()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
