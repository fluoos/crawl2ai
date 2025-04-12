from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.schemas.crawler import CrawlerRequest, CrawlerResponse, UrlToMarkdownRequest, UrlToMarkdownResponse
from app.core.deps import get_api_key
from app.services.crawler_service import CrawlerService

router = APIRouter()

@router.post("/crawl", response_model=CrawlerResponse)
async def crawl_links(
    request: CrawlerRequest,
    api_key: str = Depends(get_api_key)
):
    """爬取指定URL的链接"""
    try:
        result = CrawlerService.start_crawl_process(
            url=str(request.url),
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns,
            crawl_strategy=request.crawl_strategy,
            force_refresh=request.force_refresh
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬虫任务创建失败: {str(e)}")

@router.post("/stop-crawl", response_model=CrawlerResponse)
async def stop_crawl(api_key: str = Depends(get_api_key)):
    """强制停止当前运行的爬虫任务"""
    try:
        return CrawlerService.stop_crawl()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止爬虫任务失败: {str(e)}")

@router.get("/status", response_model=CrawlerResponse)
async def crawl_status(api_key: str = Depends(get_api_key)):
    """检查爬虫状态并获取爬取的URL"""
    try:
        return CrawlerService.get_crawl_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取爬虫状态失败: {str(e)}")

@router.post("/delete-url", response_model=CrawlerResponse)
async def delete_url(
    request: UrlToMarkdownRequest,
    api_key: str = Depends(get_api_key)
):
    """删除指定的URL链接"""
    urls = [str(url) for url in request.urls]
    try:
        return CrawlerService.delete_url(urls)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除URL失败: {str(e)}")

@router.post("/convert", response_model=UrlToMarkdownResponse)
async def convert_to_markdown(
    request: UrlToMarkdownRequest,
    api_key: str = Depends(get_api_key)
):
    """将URL列表转换为Markdown文件"""
    urls = [str(url) for url in request.urls]
    try:
        return CrawlerService.start_convert_process(urls, request.output_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换任务创建失败: {str(e)}")
