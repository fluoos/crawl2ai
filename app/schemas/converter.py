from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class ConversionRequest(BaseModel):
    files: List[str]
    model: str = "deepseek"  # 默认使用deepseek
    output_file: str = "qa_dataset.jsonl"
    
class ConversionResponse(BaseModel):
    status: str
    message: str
    output_file: Optional[str] = None
    sample: Optional[List[Dict[str, Any]]] = None 