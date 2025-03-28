import os
import aiohttp
import asyncio
from typing import List, Optional
from bs4 import BeautifulSoup
import re
import logging
from urllib.parse import urljoin, urlparse

# 这里我们保留原来爬虫的核心逻辑，但改为异步实现
async def crawl_urls(
    start_url: str,
    max_depth: int = 6,
    max_pages: int = 5000,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> List[str]:
    """爬取URL并保存到文件"""
    # 初始化变量
    visited_urls = set()
    to_visit = [(start_url, 0)]  # (url, depth)
    found_urls = []
    
    # 获取域名，我们只爬取同一域名下的链接
    parsed_url = urlparse(start_url)
    domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # 如果没有提供过滤模式，使用默认模式匹配同域名
    if not include_patterns:
        include_patterns = [f"^{re.escape(domain)}"]
    
    async with aiohttp.ClientSession() as session:
        while to_visit and len(found_urls) < max_pages:
            url, depth = to_visit.pop(0)
            
            if url in visited_urls:
                continue
                
            visited_urls.add(url)
            
            # 检查深度
            if depth > max_depth:
                continue
            
            try:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        continue
                        
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    
                    # 添加到发现的URL列表
                    found_urls.append(url)
                    logging.info(f"已爬取: {url}")
                    
                    # 提取页面中的链接
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        full_url = urljoin(url, href)
                        
                        # 检查URL是否符合包含模式且不符合排除模式
                        should_include = any(re.search(pattern, full_url) for pattern in include_patterns) if include_patterns else True
                        should_exclude = any(re.search(pattern, full_url) for pattern in exclude_patterns) if exclude_patterns else False
                        
                        if should_include and not should_exclude and full_url not in visited_urls:
                            to_visit.append((full_url, depth + 1))
            
            except Exception as e:
                logging.error(f"爬取 {url} 时出错: {str(e)}")
    
    # 保存结果到文件
    os.makedirs("output", exist_ok=True)
    with open("output/crawled_urls.txt", "w", encoding="utf-8") as f:
        for url in found_urls:
            f.write(f"{url}\n")
    
    return found_urls

def url_to_filename(url):
    """将URL转换为文件名，与原始实现一致"""
    parsed = urlparse(url)
    path = parsed.path.replace('.html', '')
    filename = path.strip('/').replace('/', '_')
    if not filename:
        filename = parsed.netloc
    return f"{filename}.md"

async def convert_urls_to_markdown(
    urls: List[str],
    output_dir: str = "upload"  # 与原始实现一致
) -> List[str]:
    """将URL列表转换为Markdown文件"""
    os.makedirs(output_dir, exist_ok=True)
    converted_files = []
    
    # 获取已存在的文件，避免重复处理
    existing_files = set()
    for file in os.listdir(output_dir):
        if file.endswith(".md"):
            existing_files.add(file)
    
    async with aiohttp.ClientSession() as session:
        for url in urls:
            try:
                # 生成文件名，与原始实现一致
                filename = url_to_filename(url)
                filepath = os.path.join(output_dir, filename)
                
                # 如果文件已存在，跳过
                if filename in existing_files:
                    logging.info(f"跳过已存在的URL: {url} -> {filename}")
                    continue
                
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