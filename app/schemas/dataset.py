from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class DeleteItemsRequest(BaseModel):
    ids: List[int] = Field(..., description="要删除的问答对ID列表")

class DatasetListRequest(BaseModel):
    format: str = Field("jsonl", description="数据格式")
    style: str = Field("Alpaca", description="数据集风格")
    inputFile: str = Field("qa_dataset.jsonl", description="输入文件名")
    template: Optional[Dict[str, Any]] = Field(None, description="自定义模板")
    page: int = Field(1, description="页码")
    pageSize: int = Field(20, description="每页数量")

class DatasetExportRequest(BaseModel):
    format: str = Field("jsonl", description="导出格式")
    style: str = Field("Alpaca", description="数据集风格")
    inputFile: str = Field("qa_dataset.jsonl", description="输入文件名")
    outputFile: Optional[str] = Field(None, description="输出文件名")
    template: Optional[Dict[str, Any]] = Field(None, description="自定义模板")

class AddQAItemRequest(BaseModel):
    question: str = Field(..., description="问题内容")
    answer: str = Field(..., description="答案内容")
    chainOfThought: Optional[str] = Field(None, description="思考链，记录解答过程")
    label: Optional[str] = Field(None, description="问答对的标签分类")