from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FileDeleteRequest(BaseModel):
    files: List[str] = Field(..., description="要删除的文件名列表")
    project_id: Optional[str] = Field(None, alias="projectId")

