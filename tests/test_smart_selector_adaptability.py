#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试智能选择器方案对不同网页的适应性
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import markdownify
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.crawler_engine_service import BeautifulSoupCrawler

class SmartSelectorAdaptabilityTester:
    """智能选择器适应性测试器"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # 测试不同类型的网页
        self.test_urls = [
            "https://www.lingxing.com/article/233.html",  # 有main标签的网页
            "https://www.baidu.com",  # 没有main标签的网页
            "https://www.github.com",  # 复杂的现代网页
        ]
    
    async def test_single_url(self, url: str):
        """测试单个URL的转换效果"""
        print(f"\n=== 测试URL: {url} ===")
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                crawler = BeautifulSoupCrawler(session)
                
                # 测试智能选择器
                result = await crawler.convert_to_markdown(url)
                
                if result['success']:
                    print(f"转换成功！")
                    print(f"标题: {result['title']}")
                    print(f"Markdown长度: {len(result['markdown'])} 字符")
                    
                    # 分析HTML结构
                    page_data = await crawler.fetch_page(url)
                    if page_data['success']:
                        soup = page_data['soup']
                        
                        # 检查各种选择器
                        selectors = ['main', '.main-content', '.content', '#content', 'article']
                        found_selectors = []
                        
                        for selector in selectors:
                            elements = soup.select(selector)
                            if elements:
                                found_selectors.append(f"{selector}({len(elements)})")
                        
                        print(f"找到的选择器: {', '.join(found_selectors) if found_selectors else '无'}")
                        
                        # 检查是否有导航等元素
                        nav_elements = soup.find_all(['nav', 'header', 'footer', 'aside'])
                        print(f"导航/页脚元素: {len(nav_elements)} 个")
                        
                        return {
                            'url': url,
                            'success': True,
                            'title': result['title'],
                            'length': len(result['markdown']),
                            'found_selectors': found_selectors,
                            'nav_elements': len(nav_elements),
                            'content_preview': result['markdown'][:200] + "..." if len(result['markdown']) > 200 else result['markdown']
                        }
                    else:
                        print(f"获取页面失败: {page_data.get('error', 'Unknown error')}")
                        return {'url': url, 'success': False, 'error': page_data.get('error', 'Unknown error')}
                else:
                    print(f"转换失败: {result.get('error', 'Unknown error')}")
                    return {'url': url, 'success': False, 'error': result.get('error', 'Unknown error')}
                    
        except Exception as e:
            print(f"测试异常: {e}")
            return {'url': url, 'success': False, 'error': str(e)}
    
    async def test_all_urls(self):
        """测试所有URL"""
        print("开始测试智能选择器方案对不同网页的适应性...")
        
        results = []
        for url in self.test_urls:
            result = await self.test_single_url(url)
            results.append(result)
        
        # 保存结果
        with open("tests/smart_selector_adaptability_results.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n=== 测试总结 ===")
        successful_tests = [r for r in results if r['success']]
        failed_tests = [r for r in results if not r['success']]
        
        print(f"成功测试: {len(successful_tests)}/{len(results)}")
        print(f"失败测试: {len(failed_tests)}/{len(results)}")
        
        if successful_tests:
            print(f"\n成功案例详情:")
            for result in successful_tests:
                print(f"  {result['url']}")
                print(f"    标题: {result['title']}")
                print(f"    长度: {result['length']} 字符")
                print(f"    选择器: {', '.join(result['found_selectors']) if result['found_selectors'] else '无'}")
                print(f"    导航元素: {result['nav_elements']} 个")
        
        if failed_tests:
            print(f"\n失败案例详情:")
            for result in failed_tests:
                print(f"  {result['url']}: {result['error']}")
        
        print(f"\n详细结果已保存到: tests/smart_selector_adaptability_results.json")
        
        return results
    
    def analyze_adaptability(self, results):
        """分析适应性"""
        print(f"\n=== 适应性分析 ===")
        
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            print("没有成功的测试结果")
            return
        
        # 分析选择器使用情况
        selector_usage = {}
        for result in successful_results:
            for selector in result['found_selectors']:
                selector_name = selector.split('(')[0]
                selector_usage[selector_name] = selector_usage.get(selector_name, 0) + 1
        
        print("选择器使用统计:")
        for selector, count in sorted(selector_usage.items(), key=lambda x: x[1], reverse=True):
            print(f"  {selector}: {count} 次")
        
        # 分析内容长度分布
        lengths = [r['length'] for r in successful_results]
        avg_length = sum(lengths) / len(lengths)
        min_length = min(lengths)
        max_length = max(lengths)
        
        print(f"\n内容长度统计:")
        print(f"  平均长度: {avg_length:.0f} 字符")
        print(f"  最小长度: {min_length} 字符")
        print(f"  最大长度: {max_length} 字符")
        
        # 分析导航元素情况
        nav_counts = [r['nav_elements'] for r in successful_results]
        avg_nav = sum(nav_counts) / len(nav_counts)
        
        print(f"\n导航元素统计:")
        print(f"  平均导航元素: {avg_nav:.1f} 个")
        
        # 评估适应性
        print(f"\n适应性评估:")
        if len(successful_results) == len(results):
            print("  ✅ 完美适应: 所有测试网页都成功转换")
        elif len(successful_results) >= len(results) * 0.8:
            print("  ✅ 良好适应: 大部分测试网页成功转换")
        elif len(successful_results) >= len(results) * 0.5:
            print("  ⚠️ 一般适应: 约一半测试网页成功转换")
        else:
            print("  ❌ 适应性差: 大部分测试网页转换失败")
    
    async def run_adaptability_test(self):
        """运行适应性测试"""
        results = await self.test_all_urls()
        self.analyze_adaptability(results)
        print("\n适应性测试完成！")

async def main():
    """主函数"""
    tester = SmartSelectorAdaptabilityTester()
    await tester.run_adaptability_test()

if __name__ == "__main__":
    asyncio.run(main())
