#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较直接使用body内容和智能选择器的效果
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

class BodyVsSmartSelectorTester:
    """比较body和智能选择器的测试器"""
    
    def __init__(self):
        self.test_url = "https://www.lingxing.com/article/233.html"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    async def fetch_page(self):
        """获取页面内容"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.get(self.test_url, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    print(f"获取页面失败: {response.status}")
                    return None
    
    def convert_with_body_only(self, html: str):
        """直接使用body内容转换"""
        print("=== 方法1: 直接使用body内容 ===")
        soup = BeautifulSoup(html, 'html.parser')
        
        # 只移除script和style标签，保留其他内容
        for tag in soup(['script', 'style']):
            tag.decompose()
        
        # 转换为Markdown
        markdown = markdownify.markdownify(
            str(soup),
            heading_style="ATX",
            bullets="-",
            strip=['script', 'style']
        )
        
        # 清理Markdown内容
        markdown = self._clean_markdown(markdown)
        
        print(f"Body方法转换长度: {len(markdown)} 字符")
        print("转换结果预览:")
        print("-" * 50)
        print(markdown[:500] + "..." if len(markdown) > 500 else markdown)
        print("-" * 50)
        
        return markdown
    
    def convert_with_smart_selector(self, html: str):
        """使用智能选择器转换"""
        print("\n=== 方法2: 智能选择器 ===")
        soup = BeautifulSoup(html, 'html.parser')
        
        # 智能选择器逻辑
        content_selectors = [
            'main',
            '.main-content',
            '.content',
            '.article-content',
            '.post-content',
            '#content',
            '#main',
            '.container',
            'article',
            '.article',
            '.post'
        ]
        
        content_soup = soup
        used_selector = None
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                largest_element = max(elements, key=lambda x: len(x.get_text()))
                if len(largest_element.get_text().strip()) > 100:
                    content_soup = largest_element
                    used_selector = selector
                    print(f"使用智能选择器: {selector}")
                    break
        
        if used_selector is None:
            print("未找到合适的选择器，使用整个页面")
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'menu']):
                tag.decompose()
            content_soup = soup
        
        # 转换为Markdown
        markdown = markdownify.markdownify(
            str(content_soup),
            heading_style="ATX",
            bullets="-",
            strip=['script', 'style']
        )
        
        # 清理Markdown内容
        markdown = self._clean_markdown(markdown)
        
        print(f"智能选择器转换长度: {len(markdown)} 字符")
        print("转换结果预览:")
        print("-" * 50)
        print(markdown[:500] + "..." if len(markdown) > 500 else markdown)
        print("-" * 50)
        
        return markdown
    
    def convert_with_body_cleaned(self, html: str):
        """使用body内容但清理不需要的标签"""
        print("\n=== 方法3: Body内容 + 清理不需要标签 ===")
        soup = BeautifulSoup(html, 'html.parser')
        
        # 移除不需要的标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'menu']):
            tag.decompose()
        
        # 转换为Markdown
        markdown = markdownify.markdownify(
            str(soup),
            heading_style="ATX",
            bullets="-",
            strip=['script', 'style']
        )
        
        # 清理Markdown内容
        markdown = self._clean_markdown(markdown)
        
        print(f"Body+清理方法转换长度: {len(markdown)} 字符")
        print("转换结果预览:")
        print("-" * 50)
        print(markdown[:500] + "..." if len(markdown) > 500 else markdown)
        print("-" * 50)
        
        return markdown
    
    def _clean_markdown(self, markdown: str) -> str:
        """清理Markdown内容"""
        if not markdown:
            return ""
        
        # 移除多余的空行
        lines = markdown.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append("")
                prev_empty = True
        
        # 移除开头和结尾的空行
        while cleaned_lines and not cleaned_lines[0]:
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)
    
    def compare_results(self, body_only: str, smart_selector: str, body_cleaned: str):
        """比较三种方法的结果"""
        print("\n=== 结果比较 ===")
        
        results = {
            "body_only": {
                "length": len(body_only),
                "content": body_only
            },
            "smart_selector": {
                "length": len(smart_selector),
                "content": smart_selector
            },
            "body_cleaned": {
                "length": len(body_cleaned),
                "content": body_cleaned
            }
        }
        
        print(f"Body方法长度: {results['body_only']['length']} 字符")
        print(f"智能选择器长度: {results['smart_selector']['length']} 字符")
        print(f"Body+清理长度: {results['body_cleaned']['length']} 字符")
        
        # 检查关键内容
        key_phrases = [
            "领星ERP",
            "ASINKING",
            "深圳市领星网络科技有限公司",
            "2017年成立",
            "服务网络",
            "发展历程",
            "产品及服务",
            "核心功能"
        ]
        
        print("\n关键内容检查:")
        for method, data in results.items():
            print(f"\n{method}:")
            for phrase in key_phrases:
                if phrase in data['content']:
                    print(f"  ✓ {phrase}")
                else:
                    print(f"  ✗ {phrase}")
        
        # 保存结果
        with open("tests/body_vs_smart_comparison.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细结果已保存到: tests/body_vs_smart_comparison.json")
        
        # 推荐最佳方法
        print("\n=== 推荐方案 ===")
        if results['body_cleaned']['length'] >= results['smart_selector']['length']:
            print("推荐使用: Body内容 + 清理不需要标签")
            print("原因: 更简单直接，内容完整性好")
        else:
            print("推荐使用: 智能选择器")
            print("原因: 内容更精准，噪音更少")
    
    async def run_comparison(self):
        """运行比较测试"""
        print("开始比较Body内容和智能选择器的效果...")
        print(f"测试URL: {self.test_url}")
        
        # 获取页面内容
        html = await self.fetch_page()
        if not html:
            print("获取页面失败，无法继续测试")
            return
        
        # 测试三种方法
        body_only = self.convert_with_body_only(html)
        smart_selector = self.convert_with_smart_selector(html)
        body_cleaned = self.convert_with_body_cleaned(html)
        
        # 比较结果
        self.compare_results(body_only, smart_selector, body_cleaned)
        
        print("\n比较测试完成！")

async def main():
    """主函数"""
    tester = BodyVsSmartSelectorTester()
    await tester.run_comparison()

if __name__ == "__main__":
    asyncio.run(main())
