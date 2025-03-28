from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Literal, Dict, Any, Union

class CrawlerRequest(BaseModel):
    url: str
    max_depth: int = Field(3, ge=1, le=10)
    max_pages: int = Field(100, ge=1, le=5000)
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    crawl_strategy: Literal["bfs", "dfs"] = "bfs"
    use_cache: bool = False
    max_concurrent: int = Field(20, ge=1, le=50)
    
class UrlItem(BaseModel):
    id: int
    url: str
    depth: Optional[int] = 0
    score: Optional[float] = 0.0

class CrawlerResponse(BaseModel):
    status: str
    message: str
    urls: Optional[List[Union[str, Dict[str, Any], UrlItem]]] = None
    count: Optional[int] = None
    
class UrlToMarkdownRequest(BaseModel):
    urls: List[str]
    output_dir: Optional[str] = "output"
    
class UrlToMarkdownResponse(BaseModel):
    status: str
    message: str
    files: Optional[List[str]] = None
    count: Optional[int] = None 