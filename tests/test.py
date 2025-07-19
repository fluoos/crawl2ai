import asyncio
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

// 测试文件入口
async def main():
    config = CrawlerRunConfig(
        # Target article body and sidebar, but not other content
        target_elements=["#article-wrap"]
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://www.lingxing.com/help/article/purchasingManagement", 
            config=config
        )
        print("Markdown focused on target elements")
        print("Links from entire page still available:", len(result.links.get("internal", [])))

if __name__ == "__main__":
    asyncio.run(main())