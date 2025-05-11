# app/schemas/project.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    
class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: str = Field(..., description="项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    dataset_count: int = Field(0, description="关联的数据集数量")

class ProjectDatasetRequest(BaseModel):
    project_id: str = Field(..., description="项目ID")
    dataset_name: str = Field(..., description="数据集名称")
    input_file: Optional[str] = Field(None, description="从已有文件创建数据集")