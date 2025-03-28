from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any, Optional, Literal
import os
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import logging
import json

from app.schemas.crawler import CrawlerRequest, CrawlerResponse, UrlToMarkdownRequest, UrlToMarkdownResponse
from app.services.crawler_service import crawl_urls, convert_urls_to_markdown
from app.api.deps import get_api_key

# 导入crawl4ai库
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, DFSDeepCrawlStrategy

router = APIRouter()

# 在内存中存储爬虫状态
crawler_state = {
    "status": "idle",  # idle, running, completed, failed
    "message": "",
    "urls": [],
    "count": 0
}

@router.post("/crawl", response_model=CrawlerResponse)
async def crawl_links(
    request: CrawlerRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """爬取指定URL的链接"""
    try:
        # 使用后台任务进行爬取
        background_tasks.add_task(
            crawl_urls_task,
            str(request.url),
            max_depth=request.max_depth,
            max_pages=request.max_pages,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns,
            crawl_strategy=request.crawl_strategy,
            use_cache=request.use_cache,
            max_concurrent=request.max_concurrent
        )
        
        return {
            "status": "success",
            "message": f"爬虫任务已开始，使用{request.crawl_strategy}策略，请稍后查看结果"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬虫任务创建失败: {str(e)}")

@router.get("/status", response_model=CrawlerResponse)
async def crawl_status(api_key: str = Depends(get_api_key)):
    """检查爬虫状态并获取爬取的URL"""
    try:
        # 读取JSON文件中的爬虫结果
        output_json_file = os.path.join("output", "crawled_urls.json")
        
        # 先返回内存中的爬虫状态
        if crawler_state["status"] == "running":
            return {
                "status": crawler_state["status"],
                "message": crawler_state["message"],
                "urls": [],
                "count": 0
            }
        
        # 如果爬虫已完成，读取JSON文件中的结果
        if os.path.exists(output_json_file):
            try:
                with open(output_json_file, 'r', encoding='utf-8') as f:
                    crawled_data = json.load(f)
                
                # 更新状态为已完成（除非状态是失败的）
                if crawler_state["status"] != "failed":
                    crawler_state["status"] = "completed"
                    crawler_state["message"] = "爬虫任务已完成"
                    crawler_state["count"] = len(crawled_data)
                
                # 分页处理，默认返回所有结果
                return {
                    "status": crawler_state["status"],
                    "message": crawler_state["message"],
                    "urls": crawled_data,
                    "count": len(crawled_data)
                }
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logging.error(f"读取爬虫结果文件失败: {str(e)}")
        
        # 如果文件不存在且没有运行中的爬虫任务
        if crawler_state["status"] == "idle":
            return {
                "status": "idle",
                "message": "没有正在进行的爬虫任务",
                "urls": [],
                "count": 0
            }
        
        # 否则返回内存中的状态
        return {
            "status": crawler_state["status"],
            "message": crawler_state["message"],
            "urls": crawler_state["urls"],
            "count": crawler_state["count"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取爬虫状态失败: {str(e)}")

@router.post("/convert", response_model=UrlToMarkdownResponse)
async def convert_to_markdown(
    request: UrlToMarkdownRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """将URL列表转换为Markdown文件"""
    try:
        # 使用后台任务进行转换
        background_tasks.add_task(
            convert_urls_to_markdown_task,
            [str(url) for url in request.urls],
            output_dir=request.output_dir
        )
        
        return {
            "status": "success",
            "message": "转换任务已开始，请稍后查看结果"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换任务创建失败: {str(e)}")

@router.post("/simple-crawl")
async def simple_crawl(
    url: str,
    depth: int = 1,
    api_key: str = Depends(get_api_key)
):
    """简单爬虫，只爬取指定URL和直接链接"""
    try:
        urls = await crawl_urls(url, max_depth=depth, max_pages=50)
        return {
            "status": "success",
            "message": f"成功爬取 {len(urls)} 个URL",
            "urls": urls
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬虫失败: {str(e)}")

# 后台任务
async def crawl_urls_task(url, max_depth, max_pages, include_patterns, exclude_patterns, 
                         crawl_strategy="bfs", use_cache=False, max_concurrent=20):
    """爬取URL的后台任务"""
    try:
        # 更新爬虫状态为运行中
        crawler_state["status"] = "running"
        crawler_state["message"] = f"爬虫任务正在进行中（{crawl_strategy}策略）..."
        
        # 执行爬虫
        urls = await crawl_urls(url, max_depth, max_pages, include_patterns, exclude_patterns,
                              crawl_strategy, use_cache, max_concurrent)
        
        # 更新爬虫状态为已完成
        crawler_state["status"] = "completed"
        crawler_state["message"] = "爬虫任务已完成"
        
        # 读取JSON文件中的爬虫结果（包含更详细的数据）
        output_json_file = os.path.join("output", "crawled_urls.json")
        if os.path.exists(output_json_file):
            try:
                with open(output_json_file, 'r', encoding='utf-8') as f:
                    crawled_data = json.load(f)
                crawler_state["urls"] = crawled_data
                crawler_state["count"] = len(crawled_data)
            except Exception as e:
                # 如果读取JSON文件失败，则使用简单的URL列表
                crawler_state["urls"] = [{"id": i+1, "url": url} for i, url in enumerate(urls)]
                crawler_state["count"] = len(urls)
        else:
            # 如果JSON文件不存在，则使用简单的URL列表
            crawler_state["urls"] = [{"id": i+1, "url": url} for i, url in enumerate(urls)]
            crawler_state["count"] = len(urls)
    except Exception as e:
        crawler_state["status"] = "failed"
        crawler_state["message"] = f"爬虫任务失败: {str(e)}"
        logging.error(f"爬虫任务失败: {str(e)}")

async def convert_urls_to_markdown_task(urls, output_dir):
    """转换URL为Markdown的后台任务"""
    try:
        await convert_urls_to_markdown(urls, output_dir)
    except Exception as e:
        logging.error(f"转换任务失败: {str(e)}")

# 修改后的crawl_urls方法，使用crawl4ai库
async def crawl_urls(
    start_url: str,
    max_depth: int = 3,
    max_pages: int = 100,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    crawl_strategy: str = "bfs",
    use_cache: bool = False,
    max_concurrent: int = 20
) -> List[str]:
    """
    爬取URL并保存到文件
    
    Args:
        start_url: 起始URL
        max_depth: 最大爬取深度
        max_pages: 最大爬取页面数
        include_patterns: 包含模式列表
        exclude_patterns: 排除模式列表
        crawl_strategy: 爬取策略，"bfs"(广度优先)或"dfs"(深度优先)
        use_cache: 是否使用缓存
        max_concurrent: 最大并发请求数
    """
    # 确保输出目录存在
    os.makedirs("output", exist_ok=True)
    output_txt_file = os.path.join("output", "crawled_urls.txt")
    
    # 获取域名，用于外部链接过滤
    parsed_url = urlparse(start_url)
    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # 选择爬取策略
    if crawl_strategy == "dfs":
        crawl_strategy_obj = DFSDeepCrawlStrategy(
            max_depth=max_depth,
            include_external=False,  # 默认不包含外部链接
            max_pages=max_pages,
        )
    else:  # 默认使用BFS
        crawl_strategy_obj = BFSDeepCrawlStrategy(
            max_depth=max_depth,
            include_external=False,  # 默认不包含外部链接
            max_pages=max_pages,
        )
    
    # 配置爬虫
    config = CrawlerRunConfig(
        deep_crawl_strategy=crawl_strategy_obj,
        stream=True,  # 使用流式输出
        cache_mode=CacheMode.ENABLED if use_cache else CacheMode.DISABLED,
        max_session_permit=max_concurrent,  # 最大并发数
        memory_threshold_percent=70.0  # 内存使用超过70%时，爬虫将暂停或减速
    )
    
    # 结果集
    found_urls = []
    crawled_urls = set()  # 用于去重
    
    # 使用crawl4ai进行爬取
    async with AsyncWebCrawler() as crawler:
        try:
            # 使用async for获取流式结果
            async for result in await crawler.arun(start_url, config=config):
                url = result.url
                
                # 去重检查
                if url in crawled_urls:
                    continue
                
                # 过滤URL
                should_include = True
                should_exclude = False
                
                if include_patterns:
                    should_include = any(pattern in url for pattern in include_patterns)
                
                if exclude_patterns:
                    should_exclude = any(pattern in url for pattern in exclude_patterns)
                
                if should_include and not should_exclude:
                    crawled_urls.add(url)
                    found_urls.append(url)
                    
                    # 记录爬取信息
                    depth = result.metadata.get("depth", 0)
                    score = result.metadata.get("score", 0)
                    logging.info(f"已爬取: 深度={depth} | 得分={score:.2f} | URL={url}")
                    
        except Exception as e:
            logging.error(f"爬取过程中发生错误: {str(e)}")
    
    # 保存结果到文件
    with open(output_txt_file, "w", encoding="utf-8") as f:
        for url in found_urls:
            f.write(f"{url}\n")
    
    # 如果需要，还可以保存更详细的JSON格式
    output_json_file = os.path.join("output", "crawled_urls.json")
    crawled_data = []
    for i, url in enumerate(found_urls):
        data = {
            "id": i + 1,
            "url": url,
            # 由于我们在流式处理中无法保存所有元数据，这里设置默认值
            "depth": 0,
            "score": 0
        }
        crawled_data.append(data)
    
    with open(output_json_file, "w", encoding="utf-8") as f:
        json.dump(crawled_data, f, ensure_ascii=False, indent=2)
    
    return found_urls

async def convert_urls_to_markdown(
    urls: List[str],
    output_dir: str = "output"
) -> List[str]:
    """将URL列表转换为Markdown文件"""
    os.makedirs(output_dir, exist_ok=True)
    converted_files = []
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                # 生成文件名
                parsed_url = urlparse(url)
                filename = f"{parsed_url.netloc}{parsed_url.path}".replace("/", "_")
                if not filename.endswith(".md"):
                    filename += ".md"
                    
                filepath = os.path.join(output_dir, filename)
                
                # 获取页面内容
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        continue
                        
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # 提取标题和内容
                    title = soup.title.string if soup.title else "无标题"
                    
                    # 移除脚本和样式
                    for script in soup(["script", "style"]):
                        script.extract()
                    
                    # 获取正文内容
                    main_content = soup.find("main") or soup.find("article") or soup.find("div", {"class": ["content", "main"]}) or soup.body
                    
                    # 创建Markdown文件
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(f"# {title}\n\n")
                        f.write(f"原始链接: {url}\n\n")
                        
                        # 提取段落
                        for p in main_content.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "blockquote"]):
                            if p.name.startswith('h'):
                                level = int(p.name[1])
                                f.write(f"{'#' * level} {p.get_text().strip()}\n\n")
                            elif p.name == "ul" or p.name == "ol":
                                for li in p.find_all("li"):
                                    f.write(f"- {li.get_text().strip()}\n")
                                f.write("\n")
                            elif p.name == "blockquote":
                                f.write(f"> {p.get_text().strip()}\n\n")
                            else:
                                f.write(f"{p.get_text().strip()}\n\n")
                
                converted_files.append(filepath)
                logging.info(f"转换完成: {url} -> {filepath}")
                
            except Exception as e:
                logging.error(f"转换 {url} 时出错: {str(e)}")
    
    return converted_files 