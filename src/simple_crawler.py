import os
import json
import asyncio
import logging
import time
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import LLMExtractionStrategy, ExtractionStrategy

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# -----------------------------
# 简单的HTML提取策略类
# -----------------------------
class SimpleHTMLExtractionStrategy(ExtractionStrategy):
    """简单的HTML提取策略，仅返回原始HTML"""
    
    def extract(self, html_content, url=None):
        return html_content
    
    def show_usage(self):
        return None

# -----------------------------
# Async scraping function
# -----------------------------
async def run_scrape(url: str, instruction: str, input_format: str, provider: str, api_key: str, schema: dict, use_llm=True):
    print(f"开始爬取URL: {url}")
    print(f"使用模型: {provider if use_llm else '不使用LLM，仅提取HTML'}")
    
    try:
        if use_llm and api_key:
            try:
                # 使用LLM提取策略
                extraction_strategy = LLMExtractionStrategy(
                    provider=provider,
                    api_token=api_key,
                    schema=schema,
                    extraction_type="schema",
                    instruction=instruction,
                    chunk_token_threshold=1000,
                    overlap_rate=0.0,
                    apply_chunking=True,
                    input_format=input_format,
                    extra_args={"temperature": 0.0, "max_tokens": 800}
                )
            except Exception as e:
                logger.error(f"创建LLM提取策略时出错: {str(e)}")
                print(f"创建LLM提取策略时出错: {str(e)}")
                print("切换到简单HTML提取策略")
                use_llm = False
                extraction_strategy = SimpleHTMLExtractionStrategy()
        
        if not use_llm:
            # 使用简单HTML提取策略
            print("使用简单HTML提取策略（不使用LLM）")
            extraction_strategy = SimpleHTMLExtractionStrategy()

        crawl_config = CrawlerRunConfig(
            extraction_strategy=extraction_strategy,
            cache_mode=CacheMode.BYPASS
        )

        browser_cfg = BrowserConfig(headless=True)
        
        print("正在创建浏览器实例...")
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            print("开始爬取网页...")
            result = await crawler.arun(
                url=url,
                config=crawl_config
            )
            print("网页爬取完成")

        return result, extraction_strategy, use_llm
    
    except Exception as e:
        logger.error(f"爬取过程中出错: {str(e)}", exc_info=True)
        raise

# -----------------------------
# Helper to run async function
# -----------------------------
def scrape(url: str, instruction: str, input_format: str, model_choice: str, api_key: str, schema: dict, use_llm=True):
    provider_mapping = {
        "deepseek-v3": "deepseek/deepseek-chat",
        "deepseek-coder": "deepseek/deepseek-coder"
    }
    provider = provider_mapping.get(model_choice, "deepseek/deepseek-chat")
    
    # 设置重试次数
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            return asyncio.run(run_scrape(url, instruction, input_format, provider, api_key, schema, use_llm))
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                wait_time = 2 ** retry_count  # 指数退避
                print(f"爬取失败，{wait_time}秒后重试 ({retry_count}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print(f"达到最大重试次数，放弃爬取: {e}")
                raise

def main():
    # 配置参数
    print("=== 网页爬虫与DeepSeek提取策略 ===")
    
    # 默认参数
    model_choice = "deepseek-v3"
    api_key = input("请输入DeepSeek API密钥 (留空则使用默认值): ") or "sk-3087f6e95b244897968460c66ed86819"
    use_llm = bool(api_key)
    
    schema_str = input("请输入提取模式JSON (直接回车使用默认值): ") or '{"name": "str", "price": "str"}'
    try:
        schema_dict = json.loads(schema_str)
    except json.JSONDecodeError:
        print("JSON格式错误，使用默认模式")
        schema_dict = {"name": "str", "price": "str"}
    
    instruction = input("请输入提取指令 (直接回车使用默认值): ") or "Extract all product objects with 'name' and 'price' from the content."
    input_format = input("请输入输入格式 (直接回车使用默认值): ") or "html"
    url = input("请输入要爬取的URL (直接回车使用默认值): ") or "https://www.trendyol.com/cep-telefonu-x-c103498"
    
    print("\n开始爬取...")
    try:
        result, extraction_strategy, use_llm_final = scrape(url, instruction, input_format, model_choice, api_key, schema_dict, use_llm)
        
        if result.success:
            try:
                # 创建输出目录
                output_dir = "output"
                os.makedirs(output_dir, exist_ok=True)
                
                # 打印结果对象的属性，帮助调试
                print("\n结果对象的属性:")
                for attr in dir(result):
                    if not attr.startswith('_'):
                        print(f"- {attr}")
                
                # 尝试获取HTML内容
                html_content = None
                if hasattr(result, 'html'):
                    html_content = result.html
                elif hasattr(result, 'content'):
                    html_content = result.content
                elif hasattr(result, 'raw_html'):
                    html_content = result.raw_html
                
                if html_content:
                    # 保存原始HTML内容
                    html_file = os.path.join(output_dir, f"{url.replace('://', '_').replace('/', '_')}.html")
                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    print(f"\nHTML内容已保存到: {html_file}")
                else:
                    print("\n无法获取HTML内容，没有找到相应的属性")
                
                if use_llm_final and hasattr(result, 'extracted_content'):
                    try:
                        # 尝试解析JSON
                        try:
                            data = json.loads(result.extracted_content)
                            print("\n爬取成功!")
                            print("\n提取的数据:")
                            print(json.dumps(data, indent=2, ensure_ascii=False))
                            
                            # 显示使用信息
                            if hasattr(extraction_strategy, 'show_usage'):
                                usage_info = extraction_strategy.show_usage()
                                if usage_info:
                                    print("\nDeepSeek模型使用信息:")
                                    print(usage_info)
                            
                            # 保存JSON结果
                            json_file = os.path.join(output_dir, f"{url.replace('://', '_').replace('/', '_')}.json")
                            with open(json_file, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2, ensure_ascii=False)
                            print(f"\nJSON结果已保存到: {json_file}")
                        except json.JSONDecodeError:
                            # 如果不是JSON格式，则保存为文本
                            print("\n提取的内容不是JSON格式，保存为文本文件")
                            text_file = os.path.join(output_dir, f"{url.replace('://', '_').replace('/', '_')}.txt")
                            with open(text_file, 'w', encoding='utf-8') as f:
                                f.write(result.extracted_content)
                            print(f"\n文本内容已保存到: {text_file}")
                    except Exception as e:
                        print(f"解析提取内容时出错: {e}")
                        print("原始提取内容:")
                        print(result.extracted_content)
                else:
                    print("\n仅HTML爬取成功!")
                    if html_content:
                        print(f"HTML内容长度: {len(html_content)} 字符")
            except Exception as e:
                print(f"处理结果时出错: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"爬取失败: {result.error_message}")
    
    except Exception as e:
        print(f"执行过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 