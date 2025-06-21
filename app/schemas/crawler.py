from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Literal, Dict, Any, Union
from app.core.config import settings
from app.utils.path_utils import join_paths

class CrawlerRequest(BaseModel):
    url: str
    max_depth: int = Field(settings.DEFAULT_MAX_DEPTH, ge=1, le=10)
    max_pages: int = Field(settings.DEFAULT_MAX_PAGES, ge=1, le=5000)
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    crawl_strategy: Literal["bfs", "dfs"] = settings.DEFAULT_CRAWL_STRATEGY
    force_refresh: bool = False
    projectId: Optional[str] = None
    
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
    output_dir: Optional[str] = settings.OUTPUT_DIR
    included_selector: Optional[str] = None
    excluded_selector: Optional[str] = None
    projectId: Optional[str] = None
    
    # 智能分段参数
    enable_smart_split: bool = False
    max_tokens: Optional[int] = 8000
    min_tokens: Optional[int] = 500
    split_strategy: Optional[str] = "balanced"  # conservative, aggressive, balanced

class UrlToMarkdownResponse(BaseModel):
    status: str
    message: str
    files: Optional[List[str]] = None
    count: Optional[int] = None

class ExportLinksResponse(BaseModel):
    status: str
    message: str
    file_path: Optional[str] = None
    download_url: Optional[str] = None 