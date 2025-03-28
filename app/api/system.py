from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
import os
import json
from app.core.config import settings

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
        # 检查配置文件是否存在
        config_file = os.path.join("config", "system.json")
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 使用默认配置填充缺失的字段
            default_config = SystemConfig().dict()
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            
            # 不返回API密钥完整内容，仅返回是否已设置
            if config.get("apiKey"):
                config["apiKey"] = "******" + config["apiKey"][-4:]
            
            return config
        else:
            # 返回默认配置
            config = SystemConfig().dict()
            config["apiKey"] = settings.DEEPSEEK_API_KEY if settings.DEEPSEEK_API_KEY else ""
            return config
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def update_system_config(config: SystemConfig):
    """更新系统配置"""
    try:
        # 确保配置目录存在
        os.makedirs("config", exist_ok=True)
        
        # 读取现有配置（如果存在）
        config_file = os.path.join("config", "system.json")
        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        
        # 更新配置
        config_dict = config.dict()
        
        # 如果apiKey字段是掩码版本，保留原始的apiKey
        if config_dict["apiKey"].startswith("******") and "apiKey" in existing_config:
            config_dict["apiKey"] = existing_config["apiKey"]
        
        # 保存配置
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
        
        # 更新环境变量中的API密钥
        if config_dict["apiKey"] and not config_dict["apiKey"].startswith("******"):
            settings.DEEPSEEK_API_KEY = config_dict["apiKey"]
        
        return {"status": "success", "message": "配置已更新"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 