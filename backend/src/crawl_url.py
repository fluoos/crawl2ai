import asyncio
import json
import os
from pathlib import Path
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.content_scraping_strategy import LXMLWebScrapingStrategy

# 获取项目根目录
BASE_DIR = Path(__file__).parent.parent.parent

# 确保输出目录存在
output_dir = BASE_DIR / "output"
output_dir.mkdir(exist_ok=True)
output_file = output_dir / "crawled_urls.json"
output_txt_file = output_dir / "crawled_urls.txt"

# 初始化空列表用于存储结果
crawled_data = []
# 使用集合来跟踪已爬取的URL，便于快速查找
crawled_urls = set()

if output_file.exists():
    with open(output_file, 'r', encoding='utf-8') as f:
        try:
            crawled_data = json.load(f)
            # 从已有数据中提取URL到集合中，用于去重
            crawled_urls = {item["url"] for item in crawled_data}
        except json.JSONDecodeError:
            crawled_data = []
            crawled_urls = set()

# 将去重后的URL保存到txt文件中
def save_urls_to_txt():
    with open(output_txt_file, 'w', encoding='utf-8') as f:
        for url in sorted(crawled_urls):
            f.write(f"{url}\n")
    print(f"已保存 {len(crawled_urls)} 个去重URL到 {output_txt_file}")

# 处理爬虫结果并保存到JSON文件，添加去重逻辑
def process_result(result):
    url = result.url
    
    # 去重检查：如果URL已经存在于集合中，直接返回，不重复添加
    if url in crawled_urls:
        print(f"跳过重复URL: {url}")
        return
        
    # 将新URL添加到去重集合中
    crawled_urls.add(url)
    
    # 继续处理新的URL数据
    data = {
        "depth": result.metadata.get("depth", 0),
        "score": result.metadata.get("score", 0),
        "url": url
    }
    crawled_data.append(data)
    print(f"Current {len(crawled_data)} pages")
    # 将更新后的数据写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(crawled_data, f, ensure_ascii=False, indent=2)
    
    # 移除每次处理结果时更新txt文件的操作，只在爬虫完成后更新一次
    # save_urls_to_txt()

async def main():
    # Configure a 2-level deep crawl
    config = CrawlerRunConfig(
        deep_crawl_strategy=BFSDeepCrawlStrategy(
            max_depth=6, 
            include_external=False,
            max_pages=5000,              # Maximum number of pages to crawl
        ),
        stream=True, # 流式输出, 配置了stream=True后，爬虫会以流式输出结果，而不是一次性返回所有结果
        # cache_mode=CacheMode.ENABLED, # 使用缓存
        max_session_permit=10, # 最大并发数,默认20
        memory_threshold_percent=60.0 # 内存使用超过60%时，爬虫将暂停或减速，默认70%
    )

    # results = []
    async with AsyncWebCrawler() as crawler:
        # results = await crawler.arun("https://www.lingxing.com", config=config)
        # for result in results:
        async for result in await crawler.arun("https://www.lingxing.com", config=config):
            # Process each result as it becomes available
            depth = result.metadata.get("depth", 0)
            score = result.metadata.get("score", 0)
            url = result.url
            print(f"Depth: {depth} | Score: {score:.2f} | {url}")
            process_result(result)
            # results.append(result)
        # print(f"Crawled {len(results)} high-value pages")
        
        # 爬虫完成后，确保所有URL都已保存到txt文件
        save_urls_to_txt()

if __name__ == "__main__":
    asyncio.run(main())