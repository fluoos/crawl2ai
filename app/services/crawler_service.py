import time
import os
import asyncio
import logging
import json
from multiprocessing import Process
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Optional, Dict, Any, Set
import uuid
from app.core.config import settings
from app.services.system_service import SystemService
from app.utils.path_utils import (
    join_paths, 
    get_output_path,
    get_project_output_path,
    ensure_dir
)

# 导入crawl4ai库
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig, MemoryAdaptiveDispatcher, CrawlerMonitor, DisplayMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy, DFSDeepCrawlStrategy


class CrawlerService:
    """爬虫服务类，提供爬虫相关的业务逻辑"""

    @staticmethod
    def start_crawl_process(
        url: str,
        max_depth: int = settings.DEFAULT_MAX_DEPTH,
        max_pages: int = settings.DEFAULT_MAX_PAGES,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        crawl_strategy: str = settings.DEFAULT_CRAWL_STRATEGY,
        force_refresh: bool = False,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """启动爬虫进程，爬取指定URL的链接"""
        try:
            # 使用进程替代线程，因为Crawl4AI的异步爬取在多线程环境下会有运行问题
            process = Process(
                target=CrawlerService.crawl_urls_process,
                args=(
                    url,
                    max_depth,
                    max_pages,
                    include_patterns,
                    exclude_patterns,
                    crawl_strategy,
                    force_refresh,
                    project_id
                )
            )
            process.daemon = True
            process.start()
            # 将进程ID保存到文件
            with open(get_project_output_path(project_id, "crawler_process.json"), "w") as f:
                json.dump({"pid": process.pid, "start_time": time.time()}, f)
            
            print(f"后台任务创建成功，进程ID: {process.pid}")
            return {
                "status": "success",
                "message": f"爬虫任务已开始，使用{crawl_strategy}策略，请稍后查看结果"
            }
        except Exception as e:
            logging.error(f"启动爬虫进程失败: {str(e)}")
            raise

    @staticmethod
    def stop_crawl(project_id: Optional[str] = None) -> Dict[str, Any]:
        """强制停止当前运行的爬虫任务"""
        # 更新爬虫状态
        with open(get_project_output_path(project_id, "crawler_status.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "stopped", "message": "爬虫任务已手动停止"}, f)

        process_info_file = get_project_output_path(project_id, "crawler_process.json")
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
        with open(get_project_output_path(project_id, "stop_crawler.flag"), "w") as f:
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
    def start_convert_process(
        urls: List[str],
        included_selector: Optional[str] = None,
        excluded_selector: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """启动URL转换为Markdown的进程"""
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
            # 使用进程来执行转换任务
            process = Process(
                target=CrawlerService.convert_urls_to_markdown_process,
                args=(
                    urls,
                    output_dir,
                    included_selector,
                    excluded_selector,
                    project_id
                )
            )
            process.daemon = True
            process.start()
            
            # 将进程ID保存到文件
            with open(get_project_output_path(project_id, "convert_process.json"), "w") as f:
                json.dump({"pid": process.pid, "start_time": time.time()}, f)
            
            print(f"转换任务已开始，进程ID: {process.pid}")
            
            return {
                "status": "success",
                "message": f"转换任务已开始，共{len(urls)}个URL，请稍后查看结果"
            }
        except Exception as e:
            logging.error(f"启动转换进程失败: {str(e)}")
            raise

    @staticmethod
    def crawl_urls_process(
        url, 
        max_depth=settings.DEFAULT_MAX_DEPTH, 
        max_pages=settings.DEFAULT_MAX_PAGES, 
        include_patterns=None, 
        exclude_patterns=None, 
        crawl_strategy=settings.DEFAULT_CRAWL_STRATEGY, 
        force_refresh=False,
        project_id=None
    ):
        """在独立进程中运行爬虫任务"""
        # 多进程环境下需要设置共享状态（使用文件）
        if project_id:
            project_dir = join_paths(settings.OUTPUT_DIR, str(project_id))
            ensure_dir(project_dir)
        else:
            ensure_dir(settings.OUTPUT_DIR)
            
        with open(get_project_output_path(project_id, "crawler_status.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "running", "message": f"爬虫任务正在进行中（{crawl_strategy}策略）..."}, f)
        
        try:
            # 在新进程中，直接使用asyncio.run是安全的
            asyncio.run(CrawlerService.crawl_urls_async(
                start_url=url,
                max_depth=max_depth,
                max_pages=max_pages,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
                crawl_strategy=crawl_strategy,
                force_refresh=force_refresh,
                project_id=project_id
            ))
        except Exception as e:
            # 记录错误
            with open(get_project_output_path(project_id, "crawler_status.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "failed", "message": f"爬虫任务失败: {str(e)}"}, f)
            print(f"爬虫任务失败: {str(e)}")

    @staticmethod
    def convert_urls_to_markdown_process(
        urls, 
        output_dir,
        included_selector=None,
        excluded_selector=None,
        project_id=None
    ):
        """在独立进程中运行URL到Markdown的转换任务"""
        # 记录转换任务开始
        ensure_dir(output_dir)
            
        with open(get_project_output_path(project_id, "convert_status.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "running", "message": f"转换任务正在进行中，共{len(urls)}个URL..."}, f)
        
        try:
            # 在新进程中运行异步函数，使用asyncio.run是安全的
            asyncio.run(CrawlerService.convert_urls_to_markdown(
                urls=urls,
                output_dir=output_dir,
                included_selector=included_selector,
                excluded_selector=excluded_selector,
                project_id=project_id
            ))
            
            # 更新状态为已完成
            with open(get_project_output_path(project_id, "convert_status.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "completed", "message": "转换任务已完成"}, f)
        except Exception as e:
            # 记录错误
            with open(get_project_output_path(project_id, "convert_status.json"), "w", encoding="utf-8") as f:
                json.dump({"status": "failed", "message": f"转换任务失败: {str(e)}"}, f)
            print(f"转换任务失败: {str(e)}")

    @staticmethod
    def process_url(url):
        """处理URL，确保使用https协议"""
        if url.startswith('http://'):
            return url.replace('http://', 'https://', 1)
        return url

    @staticmethod
    def url_to_filename(url):
        """将URL转换为文件名"""
        parsed = urlparse(url)
        path = parsed.path.replace('.html', '')
        filename = path.strip('/').replace('/', '_')
        if not filename:
            filename = parsed.netloc
        return f"{filename}.md"

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
        使用crawl4ai异步爬取URL并保存到文件
        
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
                    fix_url = CrawlerService.process_url(url)
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
                            "title": result.title if hasattr(result, "title") else "",
                            "crawled_at": datetime.now().isoformat()
                        }
                        crawled_data.append(data)
                        with open(output_json_file, "w", encoding="utf-8") as f:
                            json.dump(crawled_data, f, ensure_ascii=False, indent=2)
                        # 如果爬取的URL数量超过max_pages，则停止爬取，强制完成并更新状态
                        if count >= max_pages:
                            print(f"爬取完成，共找到 {count} 个URL")
                            CrawlerService.stop_crawl(project_id)
                            with open(get_project_output_path(project_id, "crawler_status.json"), "w", encoding="utf-8") as f:
                                json.dump({"status": "completed", "message": "爬虫任务已完成"}, f)
                            break
        except Exception as e:
            logging.error(f"爬取过程中发生错误: {str(e)}")
            print(f"爬取过程中发生错误: {str(e)}")

        print(f"爬取完成，共找到 {len(crawled_urls)} 个URL")
        # 更新状态
        with open(get_project_output_path(project_id, "crawler_status.json"), "w", encoding="utf-8") as f:
            json.dump({"status": "completed", "message": "爬虫任务已完成"}, f)
        return crawled_urls

    @staticmethod
    async def convert_urls_to_markdown(
        urls: List[str],
        output_dir: str = None,
        included_selector: Optional[str] = None,
        excluded_selector: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> List[str]:
        """
        将URL列表转换为Markdown文件
        
        Args:
            urls: 要转换的URL列表
            output_dir: 输出目录
            included_selector: 包含的选择器
            excluded_selector: 排除的选择器
            project_id: 项目ID
        
        Returns:
            List[str]: 生成的文件路径列表
        """
        ensure_dir(output_dir)
     
        print(f"准备处理{len(urls)}个URL，输出到{output_dir}")
        
        browser_config = BrowserConfig(verbose=True)
        
        # 配置爬虫
        run_config_dict = {
            # markdown_generator=DefaultMarkdownGenerator(),
            # Content filtering
            # word_count_threshold=10,
            # excluded_tags=['form', 'header'],
            # exclude_external_links=True,

            # Content processing
            # process_iframes=True,
            # remove_overlay_elements=True,
            # css_selector="#article-wrap, .article-title, .article-container",
            # css_selector=".article-title, #article-container-warp",
            # excluded_selector=".article-pagination",
            # target_elements=["#article-wrap"], // 无效
            # Cache control
            # cache_mode=CacheMode.ENABLED,  # Use cache if available
            "stream": True
        }
        
        # 添加选择器配置
        if included_selector:
            run_config_dict["css_selector"] = included_selector
        if excluded_selector:
            run_config_dict["excluded_selector"] = excluded_selector
            
        run_config = CrawlerRunConfig(**run_config_dict)

        # 用于跟踪进度
        total_urls = len(urls)
        processed_urls = 0
        successful_urls = 0
        # 生成任务通知的唯一ID，使用uuid
        task_id = str(uuid.uuid4())
        
        # 发送初始进度更新
        SystemService.send_to_websocket({
            "task_id": task_id,
            "type": "html_to_md_convert_progress",
            "status": "started",
            "progress": 0,
            "total": total_urls,
            "processed": 0,
            "successful": 0,
            "message": "开始转换URL为Markdown"
        }, project_id)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            # 该逻辑不能修改，stream=True模式要使用async for result in await
            async for result in await crawler.arun_many(
                urls=list(urls),
                config=run_config,
            ):
                processed_urls += 1
                progress_percent = int(processed_urls / total_urls * 100)
                
                print(f"已转换链接: {result.url}")
                if result.success and result.markdown and result.markdown.strip():
                    successful_urls += 1
                    
                    # 生成文件名
                    filename = CrawlerService.url_to_filename(result.url)
                    filepath = join_paths(output_dir, filename)
                    
                    # 保存markdown内容
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(result.markdown)
                    print(f"已保存内容到: {filepath}")

                    # 更新markdown_manager.json，添加filePath字段
                    CrawlerService.update_markdown_registry(result.url, filepath, project_id)
                    
                    # 更新crawled_urls.json，添加filePath字段
                    CrawlerService.update_crawled_url_filepath(result.url, filepath, project_id)
                    
                    # 发送成功通知
                    SystemService.send_to_websocket({
                        "task_id": task_id,
                        "type": "html_to_md_convert_progress",
                        "status": "processing",
                        "progress": progress_percent,
                        "total": total_urls,
                        "processed": processed_urls,
                        "successful": successful_urls,  
                        "message": f"已成功转换URL: {result.url}",
                        "url": result.url,
                        "success": True
                    }, project_id)
                elif result.status_code == 403 and "robots.txt" in result.error_message:
                    print(f"跳过 {result.url} - 被robots.txt阻止")
                    SystemService.send_to_websocket({
                        "task_id": task_id,
                        "type": "html_to_md_convert_progress",
                        "status": "processing",
                        "progress": progress_percent,
                        "total": total_urls,
                        "processed": processed_urls,
                        "successful": successful_urls,
                        "message": f"跳过URL: {result.url} - 被robots.txt阻止",
                        "url": result.url,
                        "success": False,
                        "error": "被robots.txt阻止"
                    }, project_id)
                elif not result.markdown or not result.markdown.strip():
                    print(f"跳过 {result.url} - 内容为空")
                    SystemService.send_to_websocket({
                        "task_id": task_id,
                        "type": "html_to_md_convert_progress",
                        "status": "processing",
                        "progress": progress_percent,
                        "total": total_urls,
                        "processed": processed_urls,
                        "successful": successful_urls,
                        "message": f"跳过URL: {result.url} - 内容为空",
                        "url": result.url,
                        "success": False,
                        "error": "内容为空"
                    }, project_id)
                else:
                    print(f"爬取失败 {result.url}: {result.error_message}")
                    SystemService.send_to_websocket({
                        "task_id": task_id,
                        "type": "html_to_md_convert_progress",
                        "status": "processing",
                        "progress": progress_percent,
                        "total": total_urls,
                        "processed": processed_urls,
                        "successful": successful_urls,
                        "message": f"爬取失败: {result.url}",
                        "url": result.url,
                        "success": False,
                        "error": result.error_message
                    }, project_id)

        # 发送完成通知
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
