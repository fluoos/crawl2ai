from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ExportRequest(BaseModel):
    format: str = Field(..., description="导出格式：jsonl或json")
    style: str = Field(..., description="数据集风格：alpaca、sharegpt或custom")
    input_file: str = "qa_dataset.jsonl"
    output_file: str
    mapping: Optional[Dict[str, str]] = None  # 字段映射配置（用于自定义格式）
    
class ExportResponse(BaseModel):
    status: str
    message: str
    output_file: Optional[str] = None
    sample: Optional[List[Dict[str, Any]]] = None

class PreviewRequest(BaseModel):
    format: str
    style: str
    input_file: str = "qa_dataset.jsonl"
    mapping: Optional[Dict[str, str]] = None
    
class PreviewResponse(BaseModel):
    status: str
    message: str
    sample: Optional[List[Dict[str, Any]]] = None 