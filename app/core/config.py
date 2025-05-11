import os
from pydantic_settings import BaseSettings
from typing import List, Dict, Any

class Settings(BaseSettings):
    # API密钥配置
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    API_KEY_REQUIRED: bool = False  # 设置为True时将要求API请求提供有效的密钥
    
    # 路径配置
    OUTPUT_DIR: str = "output"
    EXPORT_DIR: str = "export"
    UPLOAD_DIR: str = "upload"
    
    # 导出配置
    SUPPORTED_FORMATS: List[str] = ["jsonl", "json"]
    SUPPORTED_STYLES: List[str] = ["Alpaca", "ShareGPT", "Custom"]
    
    # 爬虫配置
    DEFAULT_MAX_DEPTH: int = 3
    DEFAULT_MAX_PAGES: int = 100
    DEFAULT_CRAWL_STRATEGY: str = "bfs"
    
    # 系统服务配置
    SYSTEM_CONFIG_DIR: str = "output/config"
    SYSTEM_CONFIG_FILE: str = "system.json"
    MODELS_CONFIG_FILE: str = "models.json"
    PROMPTS_CONFIG_FILE: str = "prompts.json"
    FILE_STRATEGY_CONFIG_FILE: str = "file_strategy.json"
    
    # 文件处理默认配置
    DEFAULT_CHUNK_SIZE: int = 2000
    DEFAULT_OVERLAP_SIZE: int = 200
    DEFAULT_PRESERVE_MARKDOWN: bool = True
    DEFAULT_SMART_CHUNKING: bool = True
    
    # 使用Pydantic v2配置语法
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # 忽略额外字段
    }

# 生成设置实例
settings = Settings()

# 确保必要的目录存在
for dir_path in [settings.OUTPUT_DIR, settings.EXPORT_DIR, settings.UPLOAD_DIR]:
    os.makedirs(dir_path, exist_ok=True)

# 确保导出子目录存在
for style in [s.lower() for s in settings.SUPPORTED_STYLES]:
    os.makedirs(os.path.join(settings.EXPORT_DIR, style), exist_ok=True)

# 确保系统配置目录存在
os.makedirs(settings.SYSTEM_CONFIG_DIR, exist_ok=True) 