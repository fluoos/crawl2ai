import time
import os
import sys
import asyncio
import logging
import json
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urljoin, urlunparse
from typing import List, Optional, Dict, Any, Set
from concurrent.futures import ThreadPoolExecutor
import uuid
import re
from app.core.config import settings
from app.services.system_service import SystemService
from app.utils.path_utils import (
    join_paths, 
    get_output_path,
    get_project_output_path,
    ensure_dir
)

# 替换 crawl4ai 的导入，使用轻量级替代方案
import aiohttp

# 导入智能分段工具
from app.core.markdown_splitter import MarkdownSplitter

# 导入爬虫引擎服务
from app.services.crawler_engine_service import (
    CrawlerEngineService,
    CrawlStrategy,
    BFSCrawlStrategy, 
    DFSCrawlStrategy,
    BeautifulSoupCrawler
)


class CrawlerService:
    """爬虫服务类，提供爬虫相关的业务逻辑"""
    
    # 类变量用于跟踪运行中的任务
    _running_tasks: Dict[str, asyncio.Task] = {}

    @staticmethod
    async def start_crawl_task(
        url: str,
        max_depth: int = settings.DEFAULT_MAX_DEPTH,
        max_pages: int = settings.DEFAULT_MAX_PAGES,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        crawl_strategy: str = settings.DEFAULT_CRAWL_STRATEGY,
        force_refresh: bool = False,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """启动爬虫异步任务，爬取指定URL的链接"""
        try:
            # 生成任务ID
            task_id = f"crawl_{project_id}_{int(time.time())}"
            
            # 创建异步任务
            task = asyncio.create_task(
                CrawlerService.crawl_urls_async(
                    start_url=url,
                    max_depth=max_depth,
                    max_pages=max_pages,
                    include_patterns=include_patterns,
                    exclude_patterns=exclude_patterns,
                    crawl_strategy=crawl_strategy,
                    force_refresh=force_refresh,
                    project_id=project_id
                )
            )
            
            # 保存任务引用
            CrawlerService._running_tasks[task_id] = task
            
            # 将任务信息保存到文件
            with open(get_project_output_path(project_id, "crawler_task.json"), "w") as f:
                json.dump({"task_id": task_id, "start_time": time.time()}, f)
            
            # 设置任务完成回调
            task.add_done_callback(lambda t: CrawlerService._cleanup_task(task_id))
            
            print(f"后台异步任务创建成功，任务ID: {task_id}")
            return {
                "status": "success",
                "message": f"爬虫任务已开始，使用{crawl_strategy}策略，请稍后查看结果"
            }
        except Exception as e:
            logging.error(f"启动爬虫任务失败: {str(e)}")
            raise

    @staticmethod
    def _cleanup_task(task_id: str):
        """清理完成的任务"""
        try:
            if task_id in CrawlerService._running_tasks:
                task = CrawlerService._running_tasks[task_id]
                # 检查任务是否有异常
                if task.done() and not task.cancelled():
                    try:
                        # 获取任务结果，如果有异常会被抛出
                        task.result()
                        print(f"任务 {task_id} 成功完成")
                    except Exception as e:
                        logging.error(f"任务 {task_id} 执行时发生异常: {str(e)}")
                        print(f"任务 {task_id} 执行失败: {str(e)}")
                elif task.cancelled():
                    print(f"任务 {task_id} 已被取消")
                
                del CrawlerService._running_tasks[task_id]
                print(f"已清理任务: {task_id}")
        except Exception as e:
            logging.error(f"清理任务时出错: {str(e)}")

    @staticmethod
    def stop_crawl(project_id: Optional[str] = None) -> Dict[str, Any]:
        """强制停止当前运行的爬虫任务"""
        # 更新爬虫状态
        with open(get_project_output_path(project_id, "crawler_status.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "stopped", "message": "爬虫任务已手动停止"}, f)

        task_info_file = get_project_output_path(project_id, "crawler_task.json")
        # 检查是否有记录的爬虫任务
        if not os.path.exists(task_info_file):
            return {
                "status": "warning",
                "message": "没有找到正在运行的爬虫任务信息",
                "urls": [],
                "count": 0
            }
        
        # 读取任务信息
        with open(task_info_file, "r") as f:
            task_info = json.load(f)
        
        task_id = task_info.get("task_id")
        
        # 检查任务是否存在并且正在运行
        task_found = False
        if task_id and task_id in CrawlerService._running_tasks:
            task = CrawlerService._running_tasks[task_id]
            if not task.done():
                # 取消任务
                task.cancel()
                task_found = True
                print(f"已取消运行中的任务: {task_id}")
            else:
                # 任务已完成，清理引用
                del CrawlerService._running_tasks[task_id]
                print(f"任务已完成: {task_id}")
        
        if not task_found:
            # 删除任务信息文件
            try:
                os.remove(task_info_file)
            except:
                pass
            return {
                "status": "warning",
                "message": "爬虫任务已不存在或已完成",
                "urls": [],
                "count": 0
            }
        
        # 创建停止标志文件
        with open(get_project_output_path(project_id, "stop_crawler.flag"), "w") as f:
            f.write("stop")
        
        # 删除任务信息文件
        try:
            os.remove(task_info_file)
        except:
            pass
        
        return {
            "status": "success",
            "message": "爬虫任务已停止",
            "urls": [],
            "count": 0
        }

    @staticmethod
    def get_crawl_status(project_id: Optional[str] = None) -> Dict[str, Any]:
        """检查爬虫状态并获取爬取的URL"""
        # 文件路径
        status_file = get_project_output_path(project_id, "crawler_status.json")
        urls_file = get_project_output_path(project_id, "crawled_urls.json")
        
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

    @staticmethod
    def delete_url(urls: List[str], project_id: Optional[str] = None) -> Dict[str, Any]:
        """删除指定的URL链接"""
        if not urls:
            return {
                "status": "warning",
                "message": "没有指定要删除的URL",
                "urls": [],
                "count": 0
            }
        
        try:
            # 确保输出目录存在
            if project_id:
                project_dir = join_paths(settings.OUTPUT_DIR, str(project_id))
                ensure_dir(project_dir)
            else:
                ensure_dir(settings.OUTPUT_DIR)
                
            # JSON文件路径
            crawled_urls_path = get_project_output_path(project_id, "crawled_urls.json")
            deleted_count = 0
            
            # 检查文件是否存在
            if os.path.exists(crawled_urls_path):
                try:
                    # 读取现有数据
                    with open(crawled_urls_path, 'r', encoding='utf-8') as f:
                        crawled_data = json.load(f)
                    
                    # 记录原始数量
                    original_count = len(crawled_data)
                    
                    # 过滤掉要删除的URL
                    new_data = [item for item in crawled_data 
                               if not (isinstance(item, dict) and item.get('url') in urls)]
                    
                    # 计算删除的数量
                    deleted_count = original_count - len(new_data)
                    
                    # 保存更新后的文件
                    with open(crawled_urls_path, 'w', encoding='utf-8') as f:
                        json.dump(new_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"已从crawled_urls.json中删除 {deleted_count} 个URL")
                        
                except json.JSONDecodeError:
                    return {
                        "status": "error",
                        "message": "crawled_urls.json文件格式错误",
                        "urls": [],
                        "count": 0
                    }
                except Exception as e:
                    return {
                        "status": "error",
                        "message": f"处理crawled_urls.json时出错: {str(e)}",
                        "urls": [],
                        "count": 0
                    }
            else:
                return {
                    "status": "warning",
                    "message": "crawled_urls.json文件不存在",
                    "urls": [],
                    "count": 0
                }
            
            return {
                "status": "success",
                "message": f"成功删除 {deleted_count} 个URL",
                "urls": [],
                "count": deleted_count
            }
        except Exception as e:
            logging.error(f"删除URL失败: {str(e)}")
            raise

    @staticmethod
    async def start_convert_task(
        urls: List[str],
        included_selector: Optional[str] = None,
        excluded_selector: Optional[str] = None,
        enable_smart_split: bool = False,
        max_tokens: Optional[int] = 8000,
        min_tokens: Optional[int] = 500,
        split_strategy: Optional[str] = "balanced",
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """启动URL转换为Markdown的异步任务"""
        if not urls:
            print("没有需要转换的URL")
            return {
                "status": "success",
                "message": "没有需要转换的URL"
            }
        if not project_id:
            return {
                "status": "error",
                "message": "项目ID错误"
            }
        
        # 设置默认输出目录
        output_dir = join_paths(settings.OUTPUT_DIR, str(project_id), "markdown")
        try:
            # 生成任务ID
            task_id = f"convert_{project_id}_{int(time.time())}"
            
            # 创建异步任务
            task = asyncio.create_task(
                CrawlerService.convert_urls_to_markdown(
                    urls=urls,
                    output_dir=output_dir,
                    included_selector=included_selector,
                    excluded_selector=excluded_selector,
                    enable_smart_split=enable_smart_split,
                    max_tokens=max_tokens,
                    min_tokens=min_tokens,
                    split_strategy=split_strategy,
                    project_id=project_id
                )
            )
            
            # 保存任务引用
            CrawlerService._running_tasks[task_id] = task
            
            # 将任务信息保存到文件
            with open(get_project_output_path(project_id, "convert_task.json"), "w") as f:
                json.dump({"task_id": task_id, "start_time": time.time()}, f)
            
            # 设置任务完成回调
            task.add_done_callback(lambda t: CrawlerService._cleanup_task(task_id))
            
            smart_split_info = f"，智能分段: {'开启' if enable_smart_split else '关闭'}"
            print(f"转换任务已开始，任务ID: {task_id}{smart_split_info}")
            
            return {
                "status": "success",
                "message": f"转换任务已开始，共{len(urls)}个URL{smart_split_info}，请稍后查看结果"
            }
        except Exception as e:
            logging.error(f"启动转换任务失败: {str(e)}")
            raise

    @staticmethod
    def process_url(url):
        """处理URL，确保使用https协议"""
        return CrawlerEngineService.process_url(url)

    @staticmethod
    def url_to_filename(url):
        """将URL转换为文件名"""
        return CrawlerEngineService.url_to_filename(url)

    @staticmethod
    def get_existing_files(output_dir):
        """获取已存在的markdown文件列表"""
        existing_files = set()
        upload_path = Path(output_dir)  # 将字符串转换为Path对象
        if upload_path.exists():
            for file in upload_path.glob("*.md"):  # 使用upload_path而不是output_dir
                existing_files.add(file.name)
        return existing_files

    @staticmethod
    async def crawl_urls_async(
        start_url: str,
        max_depth: int = settings.DEFAULT_MAX_DEPTH,
        max_pages: int = settings.DEFAULT_MAX_PAGES,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        crawl_strategy: str = settings.DEFAULT_CRAWL_STRATEGY,
        force_refresh: bool = False,
        project_id: Optional[str] = None
    ) -> Set[str]:
        """
        使用 BeautifulSoup + aiohttp 异步爬取URL并保存到文件
        
        Args:
            start_url: 起始URL
            max_depth: 最大爬取深度
            max_pages: 最大爬取页面数
            include_patterns: 包含链接规则列表
            exclude_patterns: 排除链接规则列表
            crawl_strategy: 爬取策略，"bfs"(广度优先)或"dfs"(深度优先)
            force_refresh: 是否强制刷新
            project_id: 项目ID
        """
        print(f"准备开始爬取URL: {start_url}")
        # 确保输出目录存在
        if project_id:
            project_dir = join_paths(settings.OUTPUT_DIR, str(project_id))
            ensure_dir(project_dir)
        else:
            ensure_dir(settings.OUTPUT_DIR)
            
        # 设置运行状态
        with open(get_project_output_path(project_id, "crawler_status.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "running", "message": f"爬虫任务正在进行中（{crawl_strategy}策略）..."}, f)
            
        # 保存更详细的JSON格式
        output_json_file = get_project_output_path(project_id, "crawled_urls.json")
        # 初始化空列表用于存储结果
        crawled_data = []
        # 使用集合来跟踪已爬取的URL，便于快速查找
        crawled_urls = set()
        count = 0
        print(f"刷新模式：{force_refresh}, max_pages: {max_pages}, max_depth: {max_depth}")
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
        crawl_strategy_obj = CrawlerEngineService.create_crawl_strategy(
            crawl_strategy, max_depth, max_pages
        )
        
        print(f"开始爬取，策略: {crawl_strategy}")
        # 使用新的 BeautifulSoup 爬虫替代 crawl4ai
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=10)
            ) as session:
                crawler = CrawlerEngineService.create_crawler(session)
                
                # 使用策略模式初始化爬取队列
                crawl_strategy_obj.add_url(start_url, 0, 0)  # 添加起始URL
                visited_urls = set()
                
                while crawl_strategy_obj.has_urls() and len(crawled_urls) < max_pages:
                    # 使用策略获取下一个URL
                    url_info = crawl_strategy_obj.get_next_url()
                    if not url_info:
                        break
                    current_url, depth, score = url_info
                    
                    # 检查是否已访问
                    if current_url in visited_urls:
                        continue
                    
                    visited_urls.add(current_url)
                    
                    # 检查停止标志
                    stop_flag_file = get_project_output_path(project_id, "stop_crawler.flag")
                    if os.path.exists(stop_flag_file):
                        print("检测到停止标志，终止爬取")
                        break
                    
                    # 获取页面内容
                    page_data = await crawler.fetch_page(current_url)
                    
                    if page_data['success']:
                        # 处理URL
                        fix_url = CrawlerService.process_url(current_url)
                        
                        print(f"爬取: 深度={depth} | 得分={score:.2f} | URL={fix_url}")
                        
                        # 去重检查
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
                                "depth": depth,
                                "score": score,
                                "title": page_data['title'],
                                "crawled_at": datetime.now().isoformat()
                            }
                            crawled_data.append(data)
                            
                            # 保存到文件
                            with open(output_json_file, "w", encoding="utf-8") as f:
                                json.dump(crawled_data, f, ensure_ascii=False, indent=2)
                            
                            # 检查是否达到最大页面数
                            if count >= max_pages:
                                print(f"爬取完成，共找到 {count} 个URL")
                                with open(get_project_output_path(project_id, "crawler_status.json"), "w", encoding="utf-8") as f:
                                    json.dump({"status": "completed", "message": "爬虫任务已完成"}, f)
                                break
                        
                        # 如果深度允许，添加子链接到队列
                        if depth < max_depth and crawl_strategy_obj.should_crawl(fix_url, depth, count):
                            for link in page_data['links']:
                                if link not in visited_urls:
                                    # 计算链接得分（简单实现）
                                    link_score = len(link.split('/')) * 0.1  # 根据路径深度计算得分
                                    
                                    # 使用策略对象添加URL
                                    crawl_strategy_obj.add_url(link, depth + 1, link_score)
                    else:
                        print(f"爬取失败: {current_url} - {page_data.get('error', 'Unknown error')}")
                        
            print(f"爬取完成，共找到 {len(crawled_urls)} 个URL")
            # 更新状态
            with open(get_project_output_path(project_id, "crawler_status.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "completed", "message": "爬虫任务已完成"}, f)
                
        except Exception as e:
            error_msg = str(e)
            logging.error(f"爬取过程中发生错误: {error_msg}")
            print(f"爬取过程中发生错误: {error_msg}")
            # 记录错误状态
            with open(get_project_output_path(project_id, "crawler_status.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "failed", "message": f"爬虫任务失败: {error_msg}"}, f)
        
        return crawled_urls

    @staticmethod
    async def convert_urls_to_markdown(
        urls: List[str],
        output_dir: str = None,
        included_selector: Optional[str] = None,
        excluded_selector: Optional[str] = None,
        enable_smart_split: bool = False,
        max_tokens: Optional[int] = 8000,
        min_tokens: Optional[int] = 500,
        split_strategy: Optional[str] = "balanced",
        project_id: Optional[str] = None
    ) -> List[str]:
        """
        将URL列表转换为Markdown文件
        
        Args:
            urls: 要转换的URL列表
            output_dir: 输出目录
            included_selector: 包含的选择器
            excluded_selector: 排除的选择器
            enable_smart_split: 是否启用智能分段
            max_tokens: 最大分段长度
            min_tokens: 最小分段长度
            split_strategy: 分段策略
            project_id: 项目ID
        
        Returns:
            List[str]: 生成的文件路径列表
        """
        ensure_dir(output_dir)
     
        print(f"准备处理{len(urls)}个URL，输出到{output_dir}")
        
        # 设置运行状态
        with open(get_project_output_path(project_id, "convert_status.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "running", "message": f"转换任务正在进行中，共{len(urls)}个URL..."}, f)
        
        # 用于跟踪进度
        total_urls = len(urls)
        processed_urls = 0
        successful_urls = 0
        # 生成任务通知的唯一ID，使用uuid
        task_id = str(uuid.uuid4())
        
        print(f"任务ID: {task_id}, 开始发送WebSocket通知")
        
        # 发送初始进度更新（使用异步方法）
        try:
            await SystemService.send_to_websocket_async({
                "task_id": task_id,
                "type": "html_to_md_convert_progress",
                "status": "started",
                "progress": 0,
                "total": total_urls,
                "processed": 0,
                "successful": 0,
                "message": "开始转换URL为Markdown"
            }, project_id)
            print("异步WebSocket通知发送成功")
        except Exception as e:
            print(f"异步WebSocket通知发送失败: {e}")
            # 继续执行，不因为通知失败而中断

        try:
            print("开始创建aiohttp ClientSession...")
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30, connect=10),  # 减少超时时间
                connector=aiohttp.TCPConnector(limit=3, ttl_dns_cache=300, use_dns_cache=True)
            ) as session:
                print("ClientSession创建成功，初始化爬虫...")
                crawler = CrawlerEngineService.create_crawler(session)
                
                # 并发处理URL，但限制并发数
                semaphore = asyncio.Semaphore(1)  # 降低并发数到1，避免死锁
                print(f"开始处理 {len(urls)} 个URL...")
                
                async def process_single_url(url: str):
                    nonlocal processed_urls, successful_urls
                    
                    async with semaphore:
                        processed_urls += 1
                        progress_percent = int(processed_urls / total_urls * 100)
                        
                        print(f"[{processed_urls}/{total_urls}] 开始转换链接: {url}")
                        
                        try:
                            # 转换URL为Markdown
                            result = await crawler.convert_to_markdown(
                                url, 
                                included_selector=included_selector,
                                excluded_selector=excluded_selector
                            )
                            print(f"转换完成: {url} - 成功: {result['success']}")
                        except Exception as e:
                            print(f"转换URL时发生异常 {url}: {e}")
                            result = {
                                'url': url,
                                'success': False,
                                'error': str(e),
                                'markdown': '',
                                'title': ''
                            }
                        
                        if result['success'] and result['markdown'] and result['markdown'].strip():
                            successful_urls += 1
                            
                            # 根据分段策略调整参数
                            actual_max_tokens = max_tokens
                            actual_min_tokens = min_tokens
                            
                            if split_strategy == "conservative":
                                actual_max_tokens = int(max_tokens * 1.2)  # 更大的分段
                                actual_min_tokens = int(min_tokens * 1.5)
                            elif split_strategy == "aggressive":
                                actual_max_tokens = int(max_tokens * 0.8)  # 更小的分段
                                actual_min_tokens = int(min_tokens * 0.7)
                            
                            if enable_smart_split:
                                # 启用智能分段
                                try:
                                    print(f"对 {result['url']} 启用智能分段 (策略: {split_strategy}, Token范围: {actual_min_tokens}-{actual_max_tokens})")
                                    
                                    # 创建智能分段器
                                    splitter = MarkdownSplitter(
                                        max_tokens=actual_max_tokens,
                                        min_tokens=actual_min_tokens
                                    )
                                    
                                    # 执行分段
                                    chunks = splitter.create_chunks(result['markdown'])
                                    
                                    if chunks and len(chunks) > 1:
                                        # 获取基础文件名（不含扩展名）
                                        base_filename = CrawlerService.url_to_filename(result['url'])
                                        base_name = base_filename.replace('.md', '')
                                        
                                        # 保存每个分段到原目录
                                        for chunk in chunks:
                                            # 简化文件命名：xxx-1.md, xxx-2.md
                                            chunk_filename = f"{base_name}-{chunk.order}.md"
                                            chunk_filepath = join_paths(output_dir, chunk_filename)
                                            
                                            # 直接保存分段内容，不添加复杂的元数据
                                            chunk_content = f"# {chunk.title}\n\n{chunk.content}"
                                            
                                            with open(chunk_filepath, 'w', encoding='utf-8') as f:
                                                f.write(chunk_content)
                                            
                                            # 为每个分段创建注册表条目（基于文件路径）
                                            CrawlerService.update_markdown_registry_for_chunk(result['url'], chunk_filepath, project_id)
                                        
                                        print(f"已保存智能分段内容: {len(chunks)} 个分段文件到 {output_dir}")
                                        
                                        # 更新爬取URL的文件路径（指向第一个分段）
                                        first_chunk_filepath = join_paths(output_dir, f"{base_name}-1.md")
                                        CrawlerService.update_crawled_url_filepath(result['url'], first_chunk_filepath, project_id)
                                        
                                    else:
                                        # 分段结果少于2个，保存原始内容
                                        filename = CrawlerService.url_to_filename(result['url'])
                                        filepath = join_paths(output_dir, filename)
                                        
                                        with open(filepath, 'w', encoding='utf-8') as f:
                                            f.write(result['markdown'])
                                        print(f"智能分段未产生多个分段，保存原始内容到: {filepath}")
                                        
                                        CrawlerService.update_markdown_registry(result['url'], filepath, project_id)
                                        CrawlerService.update_crawled_url_filepath(result['url'], filepath, project_id)
                                        
                                except Exception as e:
                                    print(f"智能分段失败 {result['url']}: {str(e)}，将保存原始内容")
                                    # 分段失败，保存原始内容
                                    filename = CrawlerService.url_to_filename(result['url'])
                                    filepath = join_paths(output_dir, filename)
                                    
                                    with open(filepath, 'w', encoding='utf-8') as f:
                                        f.write(result['markdown'])
                                    print(f"已保存原始内容到: {filepath}")
                                    
                                    CrawlerService.update_markdown_registry(result['url'], filepath, project_id)
                                    CrawlerService.update_crawled_url_filepath(result['url'], filepath, project_id)
                            else:
                                # 未启用智能分段，保存原始内容
                                filename = CrawlerService.url_to_filename(result['url'])
                                filepath = join_paths(output_dir, filename)
                                
                                with open(filepath, 'w', encoding='utf-8') as f:
                                    f.write(result['markdown'])
                                print(f"已保存内容到: {filepath}")
                                
                                CrawlerService.update_markdown_registry(result['url'], filepath, project_id)
                                CrawlerService.update_crawled_url_filepath(result['url'], filepath, project_id)
                            
                            # 发送成功通知
                            success_message = f"已成功转换URL: {result['url']}"
                            if enable_smart_split:
                                success_message += f" (智能分段: {split_strategy})"
                            
                            try:
                                SystemService.send_to_websocket({
                                    "task_id": task_id,
                                    "type": "html_to_md_convert_progress",
                                    "status": "processing",
                                    "progress": progress_percent,
                                    "total": total_urls,
                                    "processed": processed_urls,
                                    "successful": successful_urls,  
                                    "message": success_message,
                                    "url": result['url'],
                                    "success": True
                                }, project_id)
                            except Exception as e:
                                print(f"发送成功通知失败: {e}")
                        elif result.get('status_code') == 403:
                            print(f"跳过 {result['url']} - 被访问限制阻止")
                            try:
                                SystemService.send_to_websocket({
                                    "task_id": task_id,
                                    "type": "html_to_md_convert_progress",
                                    "status": "processing",
                                    "progress": progress_percent,
                                    "total": total_urls,
                                    "processed": processed_urls,
                                    "successful": successful_urls,
                                    "message": f"跳过URL: {result['url']} - 被访问限制阻止",
                                    "url": result['url'],
                                    "success": False,
                                    "error": "被访问限制阻止"
                                }, project_id)
                            except Exception as e:
                                print(f"发送403通知失败: {e}")
                        elif not result.get('markdown') or not result.get('markdown', '').strip():
                            print(f"跳过 {result['url']} - 内容为空")
                            try:
                                SystemService.send_to_websocket({
                                    "task_id": task_id,
                                    "type": "html_to_md_convert_progress",
                                    "status": "processing",
                                    "progress": progress_percent,
                                    "total": total_urls,
                                    "processed": processed_urls,
                                    "successful": successful_urls,
                                    "message": f"跳过URL: {result['url']} - 内容为空",
                                    "url": result['url'],
                                    "success": False,
                                    "error": "内容为空"
                                }, project_id)
                            except Exception as e:
                                print(f"发送内容为空通知失败: {e}")
                        else:
                            error_message = result.get('error', 'Unknown error')
                            print(f"爬取失败 {result['url']}: {error_message}")
                            try:
                                SystemService.send_to_websocket({
                                    "task_id": task_id,
                                    "type": "html_to_md_convert_progress",
                                    "status": "processing",
                                    "progress": progress_percent,
                                    "total": total_urls,
                                    "processed": processed_urls,
                                    "successful": successful_urls,
                                    "message": f"爬取失败: {result['url']}",
                                    "url": result['url'],
                                    "success": False,
                                    "error": error_message
                                }, project_id)
                            except Exception as e:
                                print(f"发送失败通知失败: {e}")
                
                # 并发处理所有URL
                print(f"开始并发处理所有URL...")
                tasks = [process_single_url(url) for url in urls]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                print(f"所有URL处理完成，结果: {len(results)}")

            # 发送完成通知
            print(f"任务完成，发送完成通知...")
            try:
                SystemService.send_to_websocket({
                    "task_id": task_id,
                    "type": "html_to_md_convert_progress", 
                    "status": "completed",
                    "progress": 100,
                    "total": total_urls,
                    "processed": processed_urls,
                    "successful": successful_urls,
                    "message": f"转换完成，共处理{processed_urls}个URL，成功{successful_urls}个"
                }, project_id)
                print("完成通知发送成功")
            except Exception as e:
                print(f"发送完成通知失败: {e}")
            
            # 更新状态为已完成
            with open(get_project_output_path(project_id, "convert_status.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "completed", "message": "转换任务已完成"}, f)
                
        except Exception as e:
            error_msg = str(e)
            logging.error(f"转换任务失败: {error_msg}")
            print(f"转换任务失败: {error_msg}")
            # 记录错误状态
            with open(get_project_output_path(project_id, "convert_status.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "failed", "message": f"转换任务失败: {error_msg}"}, f)
            
            # 发送失败通知
            try:
                SystemService.send_to_websocket({
                    "task_id": task_id,
                    "type": "html_to_md_convert_progress", 
                    "status": "failed",
                    "progress": int(processed_urls / total_urls * 100) if total_urls > 0 else 0,
                    "total": total_urls,
                    "processed": processed_urls,
                    "successful": successful_urls,
                    "message": f"转换任务失败: {error_msg}"
                }, project_id)
            except Exception as e:
                print(f"发送失败通知失败: {e}")

        return urls

    @staticmethod
    def update_crawled_url_filepath(url, filepath, project_id: Optional[str] = None):
        """更新爬取的URL的文件路径"""
        # 文件路径
        crawled_urls_path = get_project_output_path(project_id, "crawled_urls.json")
        updated = False
        if os.path.exists(crawled_urls_path):
            try:
                # 读取数据
                with open(crawled_urls_path, 'r', encoding='utf-8') as f:
                    crawled_data = json.load(f)
                
                # 查找匹配的URL
                for item in crawled_data:
                    if isinstance(item, dict) and item.get('url') == url:
                        item['filePath'] = filepath.replace('\\', '/')  # 确保路径格式一致
                        updated = True
                        break
                
                # 保存更新后的文件
                if updated:
                    with open(crawled_urls_path, 'w', encoding='utf-8') as f:
                        json.dump(crawled_data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"更新crawled_urls.json时出错: {str(e)}")
                return False
        
        return updated

    @staticmethod
    def update_markdown_registry(url, filepath, project_id: Optional[str] = None):
        """
        更新Markdown文件注册表，添加或更新URL对应的文件路径
        
        参数:
        - url: 爬取的原始URL
        - filepath: 保存的Markdown文件路径
        - title: 文档标题（可选）
        
        返回:
        - bool: 是否成功更新
        """
        # 确保目录存在
        registry_path = get_project_output_path(project_id, "markdown_manager.json")
        relative_path = filepath.replace('\\', '/')  # 确保路径格式一致  
        # 创建基本文件记录
        file_record = {
            "url": url,
            "filePath": relative_path,
            "timestamp": datetime.now().isoformat(),
            "isDataset": False
        }
        registry_data = []
        try:
            # 检查文件是否存在
            if os.path.exists(registry_path):
                # 读取现有数据
                with open(registry_path, 'r', encoding='utf-8') as f:
                    try:
                        registry_data = json.load(f)
                        if not isinstance(registry_data, list):
                            registry_data = []
                    except json.JSONDecodeError:
                        # 文件内容不是有效的JSON
                        registry_data = []
            else:
                # 文件不存在，创建新的数组
                registry_data = []
            count = len(registry_data)
            # 检查URL是否已存在
            url_exists = False
            for item in registry_data:
                if isinstance(item, dict) and item.get('url') == url:
                    # 更新现有记录
                    item.update(file_record)
                    url_exists = True
                    break
            
            # 如果URL不存在，添加新记录
            if not url_exists:
                file_record['id'] = count + 1
                registry_data.append(file_record)
            
            # 保存更新后的注册表
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            print(f"更新Markdown注册表时出错: {str(e)}")
            logging.error(f"更新Markdown注册表时出错: {str(e)}")
            return False

    @staticmethod
    def update_markdown_registry_for_chunk(url, filepath, project_id: Optional[str] = None):
        """
        为分段文件更新Markdown文件注册表，基于文件路径进行去重而不是URL
        
        参数:
        - url: 爬取的原始URL
        - filepath: 保存的Markdown文件路径
        - project_id: 项目ID
        
        返回:
        - bool: 是否成功更新
        """
        # 确保目录存在
        registry_path = get_project_output_path(project_id, "markdown_manager.json")
        relative_path = filepath.replace('\\', '/')  # 确保路径格式一致  
        
        # 创建基本文件记录
        file_record = {
            "url": url,
            "filePath": relative_path,
            "timestamp": datetime.now().isoformat(),
            "isDataset": False
        }
        
        registry_data = []
        
        try:
            # 检查文件是否存在
            if os.path.exists(registry_path):
                # 读取现有数据
                with open(registry_path, 'r', encoding='utf-8') as f:
                    try:
                        registry_data = json.load(f)
                        if not isinstance(registry_data, list):
                            registry_data = []
                    except json.JSONDecodeError:
                        # 文件内容不是有效的JSON
                        registry_data = []
            else:
                # 文件不存在，创建新的数组
                registry_data = []
            
            count = len(registry_data)
            
            # 检查文件路径是否已存在（而不是URL）
            filepath_exists = False
            for item in registry_data:
                if isinstance(item, dict) and item.get('filePath') == relative_path:
                    # 更新现有记录
                    item.update(file_record)
                    filepath_exists = True
                    break
            
            # 如果文件路径不存在，添加新记录
            if not filepath_exists:
                file_record['id'] = count + 1
                registry_data.append(file_record)
            
            # 保存更新后的注册表
            with open(registry_path, 'w', encoding='utf-8') as f:
                json.dump(registry_data, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            print(f"更新分段文件注册表时出错: {str(e)}")
            logging.error(f"更新分段文件注册表时出错: {str(e)}")
            return False
