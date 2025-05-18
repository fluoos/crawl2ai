from fastapi import APIRouter, HTTPException, Path, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from app.services.system_service import SystemService
from app.core.config import settings
from app.core.deps import get_api_key
from app.core.websocket import manager

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
    chunkSize: int = settings.DEFAULT_CHUNK_SIZE
    overlapSize: int = settings.DEFAULT_OVERLAP_SIZE
    preserveMarkdown: bool = settings.DEFAULT_PRESERVE_MARKDOWN
    smartChunking: bool = settings.DEFAULT_SMART_CHUNKING

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

@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """建立WebSocket连接用于接收实时通知
    
    参数:
    - project_id: 项目ID
    """
    import asyncio
    import time
    print(f"WebSocket连接请求 - 项目ID: {project_id}")
    
    try:
        await manager.connect(websocket, project_id)
        print(f"WebSocket连接已建立 - 项目ID: {project_id}")
        
        try:
            # 发送一个连接成功消息
            await websocket.send_json({
                "type": "connection",
                "status": "connected",
                "project_id": project_id,
                "timestamp": time.time()
            })
            
            # 保持连接活跃
            while True:
                try:
                    # 等待客户端消息，有超时机制
                    data = await asyncio.wait_for(
                        websocket.receive_json(), 
                        timeout=120  # 2分钟超时
                    )
                    
                    # 处理心跳请求
                    if data.get('type') == 'heartbeat':
                        await websocket.send_json({
                            "type": "heartbeat_response",
                            "status": "ok",
                            "timestamp": time.time()
                        })
                        print(f"心跳响应已发送 - 项目ID: {project_id}")
                    
                except asyncio.TimeoutError:
                    # 超时时发送ping消息
                    await websocket.send_json({
                        "type": "ping",
                        "status": "ok",
                        "timestamp": time.time()
                    })
                    print(f"Ping消息已发送 - 项目ID: {project_id}")
                    
        except WebSocketDisconnect:
            print(f"WebSocket连接被客户端断开 - 项目ID: {project_id}")
        except Exception as e:
            print(f"WebSocket处理异常 - 项目ID: {project_id}, 错误: {str(e)}")
    
    except Exception as e:
        print(f"WebSocket连接失败 - 项目ID: {project_id}, 错误: {str(e)}")
    
    finally:
        # 确保连接被清理
        manager.disconnect(websocket, project_id)
        print(f"WebSocket连接已关闭并清理 - 项目ID: {project_id}")


@router.post("/internal/send-ws-message")
async def send_ws_message(data: dict, project_id: str):
    """内部API：从子进程发送WebSocket消息"""
    try:
        await manager.send_json(data, project_id)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}