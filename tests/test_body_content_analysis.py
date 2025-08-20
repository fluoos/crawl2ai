#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析body内容的问题
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import markdownify
import json

class BodyContentAnalyzer:
    """Body内容分析器"""
    
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
    
    def analyze_body_content(self, html: str):
        """分析body内容的结构"""
        print("=== Body内容结构分析 ===")
        soup = BeautifulSoup(html, 'html.parser')
        
        # 分析body下的主要元素
        body = soup.find('body')
        if not body:
            print("未找到body标签")
            return
        
        print(f"Body标签下的直接子元素数量: {len(body.find_all(recursive=False))}")
        
        # 统计各种标签的数量
        tag_counts = {}
        for tag in body.find_all():
            tag_name = tag.name
            tag_counts[tag_name] = tag_counts.get(tag_name, 0) + 1
        
        print("\nBody下各标签数量统计:")
        for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"  {tag}: {count}")
        
        # 分析主要内容区域
        main_content = body.find('main')
        if main_content:
            print(f"\nMain标签内容长度: {len(main_content.get_text())} 字符")
            print(f"Main标签下的段落数: {len(main_content.find_all('p'))}")
        
        # 分析导航和页脚
        nav_elements = body.find_all(['nav', 'header', 'footer', 'aside'])
        print(f"\n导航/页脚元素数量: {len(nav_elements)}")
        for elem in nav_elements[:5]:
            print(f"  {elem.name}: {len(elem.get_text())} 字符")
    
    def test_body_vs_main_conversion(self, html: str):
        """测试body和main的转换效果"""
        print("\n=== Body vs Main 转换效果对比 ===")
        soup = BeautifulSoup(html, 'html.parser')
        
        # 方法1: 直接使用body
        body_soup = BeautifulSoup(str(soup), 'html.parser')
        for tag in body_soup(['script', 'style']):
            tag.decompose()
        body_markdown = markdownify.markdownify(str(body_soup), heading_style="ATX", bullets="-")
        
        # 方法2: 只使用main
        main_soup = BeautifulSoup(str(soup), 'html.parser')
        main_element = main_soup.find('main')
        if main_element:
            main_markdown = markdownify.markdownify(str(main_element), heading_style="ATX", bullets="-")
        else:
            main_markdown = ""
        
        # 方法3: body但移除导航等
        body_cleaned_soup = BeautifulSoup(str(soup), 'html.parser')
        for tag in body_cleaned_soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'menu']):
            tag.decompose()
        body_cleaned_markdown = markdownify.markdownify(str(body_cleaned_soup), heading_style="ATX", bullets="-")
        
        print(f"Body方法长度: {len(body_markdown)} 字符")
        print(f"Main方法长度: {len(main_markdown)} 字符")
        print(f"Body+清理方法长度: {len(body_cleaned_markdown)} 字符")
        
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
        for phrase in key_phrases:
            in_body = phrase in body_markdown
            in_main = phrase in main_markdown
            in_body_cleaned = phrase in body_cleaned_markdown
            print(f"{phrase}: Body={in_body}, Main={in_main}, Body+清理={in_body_cleaned}")
        
        # 保存结果
        results = {
            "body_length": len(body_markdown),
            "main_length": len(main_markdown),
            "body_cleaned_length": len(body_cleaned_markdown),
            "body_content": body_markdown[:1000],
            "main_content": main_markdown[:1000],
            "body_cleaned_content": body_cleaned_markdown[:1000]
        }
        
        with open("tests/body_content_analysis.json", "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细结果已保存到: tests/body_content_analysis.json")
    
    async def run_analysis(self):
        """运行分析"""
        print("开始分析body内容问题...")
        print(f"测试URL: {self.test_url}")
        
        html = await self.fetch_page()
        if not html:
            print("获取页面失败")
            return
        
        self.analyze_body_content(html)
        self.test_body_vs_main_conversion(html)
        
        print("\n分析完成！")

async def main():
    """主函数"""
    analyzer = BodyContentAnalyzer()
    await analyzer.run_analysis()

if __name__ == "__main__":
    asyncio.run(main())
