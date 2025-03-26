import asyncio
import os
from pathlib import Path
from urllib.parse import urlparse
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, DisplayMode, BrowserConfig, MemoryAdaptiveDispatcher, CrawlerMonitor

def process_url(url):
    """处理URL，确保使用https协议"""
    if url.startswith('http://'):
        return url.replace('http://', 'https://', 1)
    return url

def url_to_filename(url):
    """将URL转换为文件名"""
    parsed = urlparse(url)
    path = parsed.path.replace('.html', '')
    filename = path.strip('/').replace('/', '_')
    if not filename:
        filename = parsed.netloc
    return f"{filename}.md"

def get_existing_files(upload_dir):
    """获取已存在的markdown文件列表"""
    existing_files = set()
    if upload_dir.exists():
        for file in upload_dir.glob("*.md"):
            existing_files.add(file.name)
    return existing_files

async def main():
    # 创建upload目录
    upload_dir = Path("upload")
    upload_dir.mkdir(exist_ok=True)
    
    # 获取已存在的文件列表
    existing_files = get_existing_files(upload_dir)
    print(f"发现 {len(existing_files)} 个已存在的markdown文件")
    
    # 读取URL文件
    urls = set()
    url_file = Path("output/crawled_urls.txt")
    if url_file.exists():
        with open(url_file, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url:
                    # 处理URL并添加到集合中（自动去重）
                    processed_url = process_url(url)
                    # 检查对应的markdown文件是否已存在
                    filename = url_to_filename(processed_url)
                    if filename not in existing_files:
                        urls.add(processed_url)
                    else:
                        print(f"跳过已存在的URL: {url} -> {filename}")
    
    print(f"读取到 {len(urls)} 个需要爬取的新URL")
    
    if not urls:
        print("没有新的URL需要爬取")
        return
    
    browser_config = BrowserConfig(verbose=True)
    run_config = CrawlerRunConfig(
        # markdown_generator=DefaultMarkdownGenerator(),
        # Content filtering
        # word_count_threshold=10,
        # excluded_tags=['form', 'header'],
        # exclude_external_links=True,

        # Content processing
        # process_iframes=True,
        # remove_overlay_elements=True,
        css_selector="#article-wrap, .article-title, .article-container",
        # css_selector=".article-title, #article-container-warp",
        excluded_selector=".article-pagination",
        # target_elements=["#article-wrap"], // 无效
        # Cache control
        # cache_mode=CacheMode.ENABLED,  # Use cache if available
        stream=True
    )
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=70.0,
        check_interval=1.0,
        max_session_permit=10,
        monitor=CrawlerMonitor(
            display_mode=DisplayMode.DETAILED
        )
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # 该逻辑不能修改，stream=True模式要使用async for result in await
        async for result in await crawler.arun_many(
            urls=list(urls),
            config=run_config,
            dispatcher=dispatcher
        ):
            if result.success and result.markdown and result.markdown.strip():
                # 生成文件名
                filename = url_to_filename(result.url)
                filepath = upload_dir / filename
                
                # 保存markdown内容
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(result.markdown)
                print(f"已保存内容到: {filepath}")
            elif result.status_code == 403 and "robots.txt" in result.error_message:
                print(f"跳过 {result.url} - 被robots.txt阻止")
            elif not result.markdown or not result.markdown.strip():
                print(f"跳过 {result.url} - 内容为空")
            else:
                print(f"爬取失败 {result.url}: {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main())