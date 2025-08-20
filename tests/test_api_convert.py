#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试API接口的convert功能修复效果
"""

import asyncio
import aiohttp
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class APIConvertTester:
    """API转换测试器"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.test_url = "https://www.lingxing.com/article/233.html"
        self.api_key = "test-api-key"  # 测试用的API密钥
    
    async def test_convert_api(self):
        """测试convert API接口"""
        print("=== 测试API接口convert功能 ===")
        
        # 准备请求数据
        request_data = {
            "urls": [self.test_url],
            "projectId": "test-project-lingxing",
            "included_selector": None,  # 让系统自动选择
            "excluded_selector": None,
            "enable_smart_split": False,
            "max_tokens": 8000,
            "min_tokens": 500,
            "split_strategy": "balanced"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # 发送转换请求
                async with session.post(
                    f"{self.base_url}/api/crawler/convert",
                    json=request_data,
                    headers=headers
                ) as response:
                    print(f"API响应状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("API调用成功！")
                        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"API调用失败: {error_text}")
                        return None
                        
        except Exception as e:
            print(f"API测试异常: {e}")
            return None
    
    async def test_convert_with_selector(self):
        """测试使用特定选择器的convert API"""
        print("\n=== 测试使用main选择器的convert API ===")
        
        request_data = {
            "urls": [self.test_url],
            "projectId": "test-project-lingxing-selector",
            "included_selector": "main",  # 指定使用main选择器
            "excluded_selector": None,
            "enable_smart_split": False,
            "max_tokens": 8000,
            "min_tokens": 500,
            "split_strategy": "balanced"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/crawler/convert",
                    json=request_data,
                    headers=headers
                ) as response:
                    print(f"API响应状态码: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        print("使用选择器的API调用成功！")
                        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"API调用失败: {error_text}")
                        return None
                        
        except Exception as e:
            print(f"API测试异常: {e}")
            return None
    
    def check_conversion_status(self, project_id):
        """检查转换状态"""
        print(f"\n=== 检查转换状态 (项目ID: {project_id}) ===")
        
        # 检查生成的文件
        output_dir = f"output/{project_id}/markdown"
        if os.path.exists(output_dir):
            files = os.listdir(output_dir)
            print(f"生成的Markdown文件: {files}")
            
            # 读取第一个文件的内容
            if files:
                first_file = files[0]
                file_path = os.path.join(output_dir, first_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"文件 {first_file} 长度: {len(content)} 字符")
                    print("文件内容预览:")
                    print("-" * 50)
                    print(content[:500] + "..." if len(content) > 500 else content)
                    print("-" * 50)
                except Exception as e:
                    print(f"读取文件失败: {e}")
        else:
            print(f"输出目录不存在: {output_dir}")
    
    async def run_api_tests(self):
        """运行所有API测试"""
        print("开始API接口测试...")
        print(f"测试URL: {self.test_url}")
        print(f"API地址: {self.base_url}")
        
        # 测试基本convert功能
        result1 = await self.test_convert_api()
        if result1:
            self.check_conversion_status("test-project-lingxing")
        
        # 测试使用选择器的convert功能
        result2 = await self.test_convert_with_selector()
        if result2:
            self.check_conversion_status("test-project-lingxing-selector")
        
        print("\nAPI测试完成！")

async def main():
    """主函数"""
    # 检查是否有命令行参数指定API地址
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    tester = APIConvertTester(base_url)
    await tester.run_api_tests()

if __name__ == "__main__":
    asyncio.run(main())
