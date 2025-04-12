import os
import json
from typing import Dict, Any
from app.core.config import settings

class SystemService:
    """系统服务类，处理所有与系统配置相关的业务逻辑"""
    
    @staticmethod
    def get_system_config() -> Dict[str, Any]:
        """获取系统配置"""
        # 默认配置，与API层的SystemConfig保持一致
        default_config = {
            "baseUrl": "https://api.deepseek.com",
            "model": "deepseek-chat",
            "apiKey": "",
            "temperature": 0.7,
            "maxTokens": 4000,
            "logLevel": "info"
        }
        
        # 检查配置文件是否存在
        config_file = os.path.join("config", "system.json")
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 使用默认配置填充缺失的字段
            for key in default_config:
                if key not in config:
                    config[key] = default_config[key]
            
            # 不返回API密钥完整内容，仅返回是否已设置
            if config.get("apiKey"):
                config["apiKey"] = "******" + config["apiKey"][-4:]
            
            return config
        else:
            # 返回默认配置
            config = default_config.copy()
            config["apiKey"] = settings.DEEPSEEK_API_KEY if settings.DEEPSEEK_API_KEY else ""
            return config
    
    @staticmethod
    def update_system_config(config_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新系统配置"""
        # 确保配置目录存在
        os.makedirs("config", exist_ok=True)
        
        # 读取现有配置（如果存在）
        config_file = os.path.join("config", "system.json")
        existing_config = {}
        if os.path.exists(config_file):
            with open(config_file, "r", encoding="utf-8") as f:
                existing_config = json.load(f)
        
        # 如果apiKey字段是掩码版本，保留原始的apiKey
        if config_data["apiKey"].startswith("******") and "apiKey" in existing_config:
            config_data["apiKey"] = existing_config["apiKey"]
        
        # 保存配置
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        # 更新环境变量中的API密钥
        if config_data["apiKey"] and not config_data["apiKey"].startswith("******"):
            settings.DEEPSEEK_API_KEY = config_data["apiKey"]
        
        return {"status": "success", "message": "配置已更新"}
