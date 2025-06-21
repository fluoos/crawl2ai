from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional

from app.schemas.crawler import CrawlerRequest, CrawlerResponse, UrlToMarkdownRequest, UrlToMarkdownResponse, ExportLinksResponse
from app.core.deps import get_api_key, get_project_id
from app.services.crawler_service import CrawlerService
from app.core.config import settings

router = APIRouter()

@router.post("/crawl", response_model=CrawlerResponse)
async def crawl_links(
    request: CrawlerRequest,
    api_key: str = Depends(get_api_key)
):
    """爬取指定URL的链接"""
    project_id = request.projectId
    print(f"爬取链接，使用项目ID: {project_id}")
    
    try:
        result = await CrawlerService.start_crawl_task(
            url=str(request.url),
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns,
            crawl_strategy=request.crawl_strategy,
            force_refresh=request.force_refresh,
            project_id=project_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬虫任务创建失败: {str(e)}")

@router.post("/stop-crawl", response_model=CrawlerResponse)
async def stop_crawl(
    api_key: str = Depends(get_api_key),
    project_id: Optional[str] = Depends(get_project_id)
):
    """强制停止当前运行的爬虫任务"""
    try:
        return CrawlerService.stop_crawl(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止爬虫任务失败: {str(e)}")

@router.get("/status", response_model=CrawlerResponse)
async def crawl_status(
    api_key: str = Depends(get_api_key),
    project_id: Optional[str] = Depends(get_project_id)
):
    """检查爬虫状态并获取爬取的URL"""
    try:
        return CrawlerService.get_crawl_status(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取爬虫状态失败: {str(e)}")

@router.post("/delete-url", response_model=CrawlerResponse)
async def delete_url(
    request: UrlToMarkdownRequest,
    api_key: str = Depends(get_api_key)
):
    """删除指定的URL链接"""
    project_id = request.projectId
    urls = [str(url) for url in request.urls]
    try:
        return CrawlerService.delete_url(urls, project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除URL失败: {str(e)}")

@router.post("/convert", response_model=UrlToMarkdownResponse)
async def convert_to_markdown(
    request: UrlToMarkdownRequest,
    api_key: str = Depends(get_api_key)
):
    """将URL列表转换为Markdown文件"""
    project_id = request.projectId
    urls = [str(url) for url in request.urls]
    try:
        return await CrawlerService.start_convert_task(
            urls=urls, 
            included_selector=request.included_selector,
            excluded_selector=request.excluded_selector,
            enable_smart_split=request.enable_smart_split,
            max_tokens=request.max_tokens,
            min_tokens=request.min_tokens,
            split_strategy=request.split_strategy,
            project_id=project_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换任务创建失败: {str(e)}")

@router.post("/export-excel", response_model=ExportLinksResponse)
async def export_links_excel(
    api_key: str = Depends(get_api_key),
    project_id: Optional[str] = Depends(get_project_id)
):
    """导出所有链接到Excel文件"""
    try:
        result = CrawlerService.export_links_to_excel(project_id=project_id)
        return ExportLinksResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出Excel失败: {str(e)}")

@router.get("/download")
async def download_file(
    filename: str,
    api_key: str = Depends(get_api_key),
    project_id: Optional[str] = Depends(get_project_id)
):
    """下载导出的文件"""
    try:
        file_path = CrawlerService.get_download_file_path(filename, project_id)
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))