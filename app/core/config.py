import os
from pydantic_settings import BaseSettings
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class Settings(BaseSettings):
    # API密钥配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    API_KEY_REQUIRED: bool = False  # 设置为True时将要求API请求提供有效的密钥
    
    # 路径配置
    OUTPUT_DIR: str = "output"
    EXPORT_DIR: str = "export"
    UPLOAD_DIR: str = "upload"
    CONFIG_DIR: str = "config"
    
    # 导出配置
    SUPPORTED_FORMATS: List[str] = ["jsonl", "json"]
    SUPPORTED_STYLES: List[str] = ["Alpaca", "ShareGPT", "Custom"]
    
    # 爬虫配置
    DEFAULT_CRAWLER_CONFIG: Dict[str, Any] = {
        "max_depth": 3,
        "max_pages": 100,
        "timeout": 30,
        "user_agent": "Mozilla/5.0 (compatible; DatasetCrawlerBot/1.0;)",
    }
    
    # 转换配置
    DEFAULT_CONVERTER_CONFIG: Dict[str, Any] = {
        "model": "deepseek-chat",
        "temperature": 0.7,
        "max_tokens": 4000,
    }
    
    # 前端环境变量 - 可以保留但非必需
    VITE_API_BASE_URL: str = "http://localhost:8000"
    
    # 使用旧版配置
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # 添加此行以忽略额外字段

# 生成设置实例
settings = Settings()

# 确保必要的目录存在
for dir_path in [settings.OUTPUT_DIR, settings.EXPORT_DIR, settings.UPLOAD_DIR, settings.CONFIG_DIR]:
    os.makedirs(dir_path, exist_ok=True) 