import time
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
import os
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import logging
import json
from multiprocessing import Process

from app.schemas.crawler import CrawlerRequest, CrawlerResponse, UrlToMarkdownRequest, UrlToMarkdownResponse
from app.services.crawler_service import convert_urls_to_markdown
from app.api.deps import get_api_key

# 导入crawl4ai库
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, DFSDeepCrawlStrategy

router = APIRouter()

@router.post("/crawl", response_model=CrawlerResponse)
async def crawl_links(
    request: CrawlerRequest,
    api_key: str = Depends(get_api_key)
):
    """爬取指定URL的链接"""
    try:
        # 使用进程替代线程，因为Crawl4AI的异步爬取在多线程环境下会有运行问题
        process = Process(
            target=crawl_urls_process,
            args=(
                str(request.url),
                request.max_depth,
                request.max_pages,
                request.include_patterns,
                request.exclude_patterns,
                request.crawl_strategy,
                request.force_refresh
            )
        )
        process.daemon = True
        process.start()
        # 将进程ID保存到文件
        with open(os.path.join("output", "crawler_process.json"), "w") as f:
            json.dump({"pid": process.pid, "start_time": time.time()}, f)
        
        print(f"后台任务创建成功，进程ID: {process.pid}")
        return {
            "status": "success",
            "message": f"爬虫任务已开始，使用{request.crawl_strategy}策略，请稍后查看结果"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬虫任务创建失败: {str(e)}")

@router.post("/stop-crawl", response_model=CrawlerResponse)
async def stop_crawl(api_key: str = Depends(get_api_key)):
    """强制停止当前运行的爬虫任务"""
    try:
        process_info_file = os.path.join("output", "crawler_process.json")
        
        # 检查是否有记录的爬虫进程
        if not os.path.exists(process_info_file):
            return {
                "status": "warning",
                "message": "没有找到正在运行的爬虫任务信息",
                "urls": [],
                "count": 0
            }
        
        # 读取进程信息
        with open(process_info_file, "r") as f:
            process_info = json.load(f)
        
        pid = process_info.get("pid")
        
        # 检查进程是否存在
        import psutil
        process_exists = False
        try:
            process = psutil.Process(pid)
            process_exists = process.is_running()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            process_exists = False
        
        if not process_exists:
            # 删除进程信息文件
            os.remove(process_info_file)
            return {
                "status": "warning",
                "message": "爬虫进程已不存在",
                "urls": [],
                "count": 0
            }
        
        # 创建停止标志文件
        with open(os.path.join("output", "stop_crawler.flag"), "w") as f:
            f.write("stop")
        
        # 尝试终止进程
        try:
            process.terminate()
            gone, alive = psutil.wait_procs([process], timeout=3)
            
            # 如果进程仍然活着，强制杀死
            if process in alive:
                process.kill()
        except Exception as e:
            logging.error(f"终止进程时出错: {str(e)}")
        
        # 更新爬虫状态
        with open(os.path.join("output", "crawler_status.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "stopped", "message": "爬虫任务已手动停止"}, f)
        
        # 删除进程信息文件
        try:
            os.remove(process_info_file)
        except:
            pass
        
        return {
            "status": "success",
            "message": "爬虫任务已停止",
            "urls": [],
            "count": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止爬虫任务失败: {str(e)}")

@router.get("/status", response_model=CrawlerResponse)
async def crawl_status(api_key: str = Depends(get_api_key)):
    """检查爬虫状态并获取爬取的URL"""
    try:
        # 文件路径
        status_file = os.path.join("output", "crawler_status.json")
        urls_file = os.path.join("output", "crawled_urls.json")
        
        # 默认状态
        status = "idle"
        message = "没有正在进行的爬虫任务"
        crawled_data = []
        count = 0
        
        # 从状态文件读取爬虫状态
        if os.path.exists(status_file):
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
                    status = status_data.get("status", "idle")
                    message = status_data.get("message", "未知状态")
            except json.JSONDecodeError:
                status = "error"
                message = "状态文件格式错误"
            except Exception as e:
                logging.error(f"读取状态文件失败: {str(e)}")
                status = "error"
                message = f"读取状态文件失败: {str(e)}"
        
        # 如果状态是"running"，也应该返回当前已爬取的URL
        if status == "running":
            # 读取当前已爬取的URL
            if os.path.exists(urls_file):
                try:
                    with open(urls_file, 'r', encoding='utf-8') as f:
                        crawled_data = json.load(f)
                        count = len(crawled_data)
                except Exception as e:
                    logging.error(f"读取URL文件失败: {str(e)}")
        
        # 返回组合的结果
        return {
            "status": status,
            "message": message,
            "urls": crawled_data,
            "count": count
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

@router.post("/single-crawl")
async def simple_crawl(
    url: str,
    depth: int = 1,
    api_key: str = Depends(get_api_key)
):
    """简单爬虫，只爬取指定URL和直接链接"""
    try:
        # 使用同步版本
        urls = crawl_urls_sync(url, max_depth=depth, max_pages=50)
        return {
            "status": "success",
            "message": f"成功爬取 {len(urls)} 个URL",
            "urls": urls
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"爬虫失败: {str(e)}")

# 进程中运行爬虫任务
def crawl_urls_process(url, max_depth, max_pages, include_patterns, exclude_patterns, crawl_strategy="bfs", force_refresh=False):
    """在独立进程中运行爬虫任务"""
    # 多进程环境下需要设置共享状态（使用文件）
    with open(os.path.join("output", "crawler_status.json"), "w", encoding="utf-8") as f:
        json.dump({"status": "running", "message": f"爬虫任务正在进行中（{crawl_strategy}策略）..."}, f)
    
    try:
        # 在新进程中，直接使用asyncio.run是安全的
        asyncio.run(crawl_urls_async(
            start_url=url,
            max_depth=max_depth,
            max_pages=max_pages,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            crawl_strategy=crawl_strategy,
            force_refresh=force_refresh
        ))
    except Exception as e:
        # 记录错误
        with open(os.path.join("output", "crawler_status.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "failed", "message": f"爬虫任务失败: {str(e)}"}, f)
        print(f"爬虫任务失败: {str(e)}")

async def convert_urls_to_markdown_task(urls, output_dir):
    """转换URL为Markdown的后台任务"""
    try:
        await convert_urls_to_markdown(urls, output_dir)
    except Exception as e:
        logging.error(f"转换任务失败: {str(e)}")

def process_url(url):
    """处理URL，确保使用https协议"""
    if url.startswith('http://'):
        return url.replace('http://', 'https://', 1)
    return url

# 异步爬取URL
async def crawl_urls_async(
    start_url: str,
    max_depth: int = 3,
    max_pages: int = 100,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    crawl_strategy: str = "bfs",
    force_refresh: bool = False
) -> List[str]:
    """
    使用crawl4ai异步爬取URL并保存到文件
    
    Args:
        start_url: 起始URL
        max_depth: 最大爬取深度
        max_pages: 最大爬取页面数
        include_patterns: 包含链接规则列表
        exclude_patterns: 排除链接规则列表
        crawl_strategy: 爬取策略，"bfs"(广度优先)或"dfs"(深度优先)
        force_refresh: 是否强制刷新
    """
    print(f"准备开始爬取URL: {start_url}")
    # 确保输出目录存在
    os.makedirs("output", exist_ok=True)
    # 保存更详细的JSON格式
    output_json_file = os.path.join("output", "crawled_urls.json")
    # 初始化空列表用于存储结果
    crawled_data = []
    # 使用集合来跟踪已爬取的URL，便于快速查找
    crawled_urls = set()
    count = 0
    print(f"刷新模式：{force_refresh}")
    # 处理force_refresh参数
    if force_refresh:
        # 如果强制刷新，清空已有数据
        print("强制刷新模式：清空已有爬取结果")
        crawled_data = []
        crawled_urls = set()
        # 立即更新文件为空
        with open(output_json_file, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    elif os.path.exists(output_json_file):
        # 否则加载已有数据
        with open(output_json_file, 'r', encoding='utf-8') as f:
            try:
                crawled_data = json.load(f)
                # 从已有数据中提取URL到集合中，用于去重
                crawled_urls = {item["url"] for item in crawled_data}
                # 更新计数器
                count = len(crawled_data)
                print(f"已加载{count}个现有URL")
            except json.JSONDecodeError:
                crawled_data = []
                crawled_urls = set()
                count = 0

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
    )

    print(f"开始爬取，策略: {crawl_strategy}")
    # 使用crawl4ai进行爬取
    try:
        async with AsyncWebCrawler() as crawler:
            # 使用async for获取流式结果
            async for result in await crawler.arun(start_url, config=config):
                url = result.url
                # 获取元数据
                depth = result.metadata.get("depth", 0) if hasattr(result, "metadata") else 0
                score = result.metadata.get("score", 0) if hasattr(result, "metadata") else 0
                
                print(f"爬取: 深度={depth} | 得分={score:.2f} | URL={url}")
                
                # 去重检查，不同协议的相当于同一个URL
                fix_url = process_url(url)
                if fix_url in crawled_urls:
                    continue
                
                # 过滤URL
                should_include = True
                should_exclude = False
                
                if include_patterns:
                    should_include = any(pattern in fix_url for pattern in include_patterns)
                
                if exclude_patterns:
                    should_exclude = any(pattern in fix_url for pattern in exclude_patterns)
                
                if should_include and not should_exclude:
                    crawled_urls.add(fix_url)
                    count = count + 1
                    data = {
                        "id": count,
                        "url": fix_url,
                        # 由于我们无法保存所有元数据，这里设置默认值
                        "depth": depth,
                        "score": score
                    }
                    crawled_data.append(data)
                    with open(output_json_file, "w", encoding="utf-8") as f:
                        json.dump(crawled_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"爬取过程中发生错误: {str(e)}")
        print(f"爬取过程中发生错误: {str(e)}")
    
    print(f"爬取完成，共找到 {len(crawled_urls)} 个URL")
    # 更新状态
    with open(os.path.join("output", "crawler_status.json"), "w", encoding="utf-8") as f:
        json.dump({"status": "completed", "message": "爬虫任务已完成"}, f)
    return crawled_urls

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
                    if response.status != 200:  # 注意：应该是status而不是status_code
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

# 创建一个同步版本的爬虫函数，内部使用事件循环
def crawl_urls_sync(
    start_url: str,
    max_depth: int = 3,
    max_pages: int = 100,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    crawl_strategy: str = "bfs"
) -> List[str]:
    """同步接口，使用asyncio.run()执行异步函数"""
    try:
        # 使用asyncio.run执行异步函数
        result = asyncio.run(
            crawl_urls_async(
                start_url=start_url,
                max_depth=max_depth,
                max_pages=max_pages,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                crawl_strategy=crawl_strategy
            )
        )
        return result
    except Exception as e:
        print(f"爬虫任务执行失败: {str(e)}")
        logging.error(f"爬虫任务执行失败: {str(e)}")
        return [] 