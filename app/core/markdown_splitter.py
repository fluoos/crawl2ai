import re
import os
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class MarkdownChunk:
    """Markdown分段结果对象"""
    content: str           # 分段内容
    title: str            # 分段标题
    order: int            # 分段序号
    estimated_tokens: int # 估算Token数
    start_line: int       # 起始行号
    end_line: int         # 结束行号
    metadata: Dict        # 元数据信息


class MarkdownSplitter:
    """
    Markdown智能分段工具
    
    参考LlamaIndex的MarkdownNodeParser实现，支持：
    - 基于标题层级的智能分段
    - Token估算和控制
    - 特殊块保护（代码块、表格等）
    - 保持文档结构完整性
    """
    
    def __init__(self, max_tokens: int = 8000, min_tokens: int = 1000, header_path_separator: str = "/"):
        """
        初始化分段器
        
        Args:
            max_tokens: 最大Token数限制
            min_tokens: 最小Token数限制
            header_path_separator: 标题路径分隔符
        """
        self.max_tokens = max_tokens
        self.min_tokens = min_tokens
        self.header_path_separator = header_path_separator
    
    def estimate_tokens(self, text: str) -> int:
        """
        估算文本的Token数量
        
        Token估算规则：
        - 英文单词数 × 1.3
        - 中文字符数 × 1.6  
        - 代码字符数 × 1.8
        - 特殊符号数 × 0.5
        """
        if not text:
            return 0
        
        # 分离代码块
        code_blocks = re.findall(r'```[\s\S]*?```', text)
        text_without_code = re.sub(r'```[\s\S]*?```', '', text)
        
        # 计算代码块Token
        code_tokens = 0
        for code_block in code_blocks:
            code_tokens += len(code_block) * 1.8
        
        # 计算中文字符数
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text_without_code))
        chinese_tokens = chinese_chars * 1.6
        
        # 计算英文单词数
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text_without_code))
        english_tokens = english_words * 1.3
        
        # 计算特殊符号数
        special_chars = len(re.findall(r'[^\u4e00-\u9fff\w\s]', text_without_code))
        special_tokens = special_chars * 0.5
        
        total_tokens = code_tokens + chinese_tokens + english_tokens + special_tokens
        return int(total_tokens)
    
    def _is_header_line(self, line: str) -> Tuple[bool, int, str]:
        """检查是否为标题行，返回(是否为标题, 标题级别, 标题文本)"""
        header_match = re.match(r'^(#{1,6})\s+(.+)', line.strip())
        if header_match:
            level = len(header_match.group(1))
            text = header_match.group(2).strip()
            return True, level, text
        return False, 0, ""
    
    def _split_by_headers(self, text: str) -> List[Dict]:
        """基于标题分割文档，保持结构完整性"""
        lines = text.split('\n')
        sections = []
        current_section = {
            'content': '',
            'header_stack': [],
            'start_line': 0,
            'end_line': 0
        }
        
        in_code_block = False
        in_table = False
        
        for i, line in enumerate(lines):
            # 追踪代码块状态
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                current_section['content'] += line + '\n'
                continue
            
            # 追踪表格状态
            if '|' in line and not in_code_block:
                in_table = True
            elif in_table and line.strip() == '':
                in_table = False
            
            # 只在非代码块和非表格中解析标题
            if not in_code_block and not in_table:
                is_header, level, header_text = self._is_header_line(line)
                
                if is_header:
                    # 保存当前段落
                    if current_section['content'].strip():
                        current_section['end_line'] = i - 1
                        sections.append(current_section.copy())
                    
                    # 更新标题栈 - 保持正确的层级结构
                    # 移除同级或更高级的标题
                    while (current_section['header_stack'] and 
                           current_section['header_stack'][-1][0] >= level):
                        current_section['header_stack'].pop()
                    
                    # 添加新标题
                    current_section['header_stack'].append((level, header_text))
                    
                    # 开始新段落
                    current_section['content'] = line + '\n'
                    current_section['start_line'] = i
                    continue
            
            current_section['content'] += line + '\n'
        
        # 添加最后一个段落
        if current_section['content'].strip():
            current_section['end_line'] = len(lines) - 1
            sections.append(current_section)
        
        return sections
    
    def _merge_small_sections(self, sections: List[Dict]) -> List[Dict]:
        """合并过小的段落，改进合并逻辑"""
        if not sections:
            return []
        
        merged = []
        
        for current in sections:
            current_tokens = self.estimate_tokens(current['content'])
            
            # 如果合并列表为空，直接添加
            if not merged:
                merged.append(current)
                continue
            
            last_tokens = self.estimate_tokens(merged[-1]['content'])
            
            # 检查是否应该合并
            should_merge = (
                current_tokens < self.min_tokens and 
                last_tokens + current_tokens <= self.max_tokens and
                # 只有在标题层级兼容时才合并
                self._can_merge_sections(merged[-1], current)
            )
            
            if should_merge:
                merged[-1]['content'] += '\n' + current['content']
                merged[-1]['end_line'] = current['end_line']
                # 如果当前段落有更深层的标题，更新标题栈
                if (current['header_stack'] and 
                    len(current['header_stack']) > len(merged[-1]['header_stack'])):
                    merged[-1]['header_stack'] = current['header_stack']
            else:
                merged.append(current)
        
        return merged
    
    def _can_merge_sections(self, section1: Dict, section2: Dict) -> bool:
        """判断两个段落是否可以合并"""
        stack1 = section1['header_stack']
        stack2 = section2['header_stack']
        
        # 如果都没有标题，可以合并
        if not stack1 and not stack2:
            return True
        
        # 如果其中一个没有标题，不合并
        if not stack1 or not stack2:
            return False
        
        # 如果标题层级相同或section2是section1的子章节，可以合并
        if len(stack2) >= len(stack1):
            return stack1 == stack2[:len(stack1)]
        
        return False
    
    def _split_large_sections(self, sections: List[Dict]) -> List[Dict]:
        """分割过大的段落"""
        result = []
        
        for section in sections:
            tokens = self.estimate_tokens(section['content'])
            
            if tokens <= self.max_tokens:
                result.append(section)
                continue
            
            # 按段落强制分割
            paragraphs = section['content'].split('\n\n')
            current_chunk = ''
            current_start = section['start_line']
            line_offset = 0
            
            for paragraph in paragraphs:
                paragraph_tokens = self.estimate_tokens(paragraph)
                current_tokens = self.estimate_tokens(current_chunk)
                
                if current_tokens + paragraph_tokens > self.max_tokens and current_chunk:
                    # 保存当前块
                    result.append({
                        'content': current_chunk.strip(),
                        'header_stack': section['header_stack'].copy(),
                        'start_line': current_start,
                        'end_line': current_start + line_offset - 1
                    })
                    current_chunk = paragraph + '\n\n'
                    current_start = current_start + line_offset
                    line_offset = paragraph.count('\n') + 2
                else:
                    current_chunk += paragraph + '\n\n'
                    line_offset += paragraph.count('\n') + 2
            
            # 添加最后一块
            if current_chunk.strip():
                result.append({
                    'content': current_chunk.strip(),
                    'header_stack': section['header_stack'].copy(),
                    'start_line': current_start,
                    'end_line': section['end_line']
                })
        
        return result
    
    def _build_header_path(self, header_stack: List[Tuple[int, str]]) -> str:
        """构建标题路径"""
        if not header_stack:
            return ""
        return self.header_path_separator.join([h[1] for h in header_stack])
    
    def _get_chunk_title(self, header_stack: List[Tuple[int, str]]) -> str:
        """获取分段标题"""
        if not header_stack:
            return "未分类内容"
        # 返回当前分段的主标题（最后一个标题）
        return header_stack[-1][1]
    
    def _get_section_title_from_content(self, content: str) -> str:
        """从内容中提取第一个标题作为分段标题"""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                is_header, level, header_text = self._is_header_line(line)
                if is_header:
                    return header_text
        return "未分类内容"
    
    def create_chunks(self, content: str) -> List[MarkdownChunk]:
        """
        创建分段
        
        Args:
            content: Markdown内容
            
        Returns:
            List[MarkdownChunk]: 分段列表
        """
        if not content.strip():
            return []
        
        # 1. 基于标题分割
        sections = self._split_by_headers(content)
        
        # 2. 合并过小段落
        sections = self._merge_small_sections(sections)
        
        # 3. 分割过大段落
        sections = self._split_large_sections(sections)
        
        # 4. 构建MarkdownChunk对象
        chunks = []
        for i, section in enumerate(sections):
            # 从内容中提取实际的标题
            actual_title = self._get_section_title_from_content(section['content'])
            
            chunk = MarkdownChunk(
                content=section['content'].strip(),
                title=actual_title,
                order=i + 1,
                estimated_tokens=self.estimate_tokens(section['content']),
                start_line=section['start_line'],
                end_line=section['end_line'],
                metadata={
                    'header_path': self._build_header_path(section['header_stack']),
                    'header_stack': section['header_stack'],
                    'split_method': 'intelligent'
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def get_split_summary(self, chunks: List[MarkdownChunk]) -> Dict[str, Any]:
        """获取分段摘要信息"""
        if not chunks:
            return {
                'total_chunks': 0,
                'total_tokens': 0,
                'avg_tokens_per_chunk': 0,
                'max_tokens': 0,
                'min_tokens': 0
            }
        
        total_tokens = sum(chunk.estimated_tokens for chunk in chunks)
        token_counts = [chunk.estimated_tokens for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'total_tokens': total_tokens,
            'avg_tokens_per_chunk': total_tokens // len(chunks),
            'max_tokens': max(token_counts),
            'min_tokens': min(token_counts),
            'chunks_over_limit': len([t for t in token_counts if t > self.max_tokens]),
            'chunks_under_limit': len([t for t in token_counts if t < self.min_tokens])
        }


def split_markdown_file(input_path: str, output_dir: str, max_tokens: int = 8000, 
                       min_tokens: int = 1000) -> List[str]:
    """
    分割Markdown文件并保存为多个文件
    
    Args:
        input_path: 输入文件路径
        output_dir: 输出目录
        max_tokens: 最大Token数
        min_tokens: 最小Token数
        
    Returns:
        List[str]: 生成的文件路径列表
    """
    # 读取文件
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 创建分段器
    splitter = MarkdownSplitter(max_tokens=max_tokens, min_tokens=min_tokens)
    chunks = splitter.create_chunks(content)
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 获取原文件信息
    input_file = Path(input_path)
    base_name = input_file.stem
    
    # 保存分段文件
    output_files = []
    for chunk in chunks:
        # 生成文件名
        safe_title = re.sub(r'[^\w\s-]', '', chunk.title)[:50]
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        filename = f"{base_name}_part_{chunk.order:03d}_{safe_title}.md"
        file_path = output_path / filename
        
        # 构建文件内容，包含元数据
        file_content = f"""---
original_file: {input_path}
chunk_order: {chunk.order}
chunk_title: {chunk.title}
estimated_tokens: {chunk.estimated_tokens}
split_method: {chunk.metadata.get('split_method', 'intelligent')}
header_path: {chunk.metadata.get('header_path', '')}
start_line: {chunk.start_line}
end_line: {chunk.end_line}
---

{chunk.content}
"""
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        output_files.append(str(file_path))
    
    return output_files


def split_markdown_content(content: str, max_tokens: int = 8000, 
                          min_tokens: int = 1000) -> List[str]:
    """
    分割Markdown内容字符串
    
    Args:
        content: Markdown内容
        max_tokens: 最大Token数
        min_tokens: 最小Token数
        
    Returns:
        List[str]: 分段内容列表
    """
    splitter = MarkdownSplitter(max_tokens=max_tokens, min_tokens=min_tokens)
    chunks = splitter.create_chunks(content)
    return [chunk.content for chunk in chunks]


# 示例用法和测试函数
def example_usage():
    """示例用法"""
    
    # 示例Markdown内容
    sample_content = """
# 主标题

这是一个介绍段落。

## 第一章

这是第一章的内容。包含一些基本信息。

### 1.1 子章节

这是子章节的内容。

```python
def hello_world():
    print("Hello, World!")
```

### 1.2 另一个子章节

更多内容...

## 第二章

第二章的内容开始。

| 表格列1 | 表格列2 |
|---------|---------|
| 数据1   | 数据2   |

这是表格后的内容。

### 2.1 重要概念

重要概念的解释...

## 第三章

最后一章的内容。
"""
    
    # 创建分段器
    splitter = MarkdownSplitter(max_tokens=500, min_tokens=100)
    
    # 获取分段
    chunks = splitter.create_chunks(sample_content)
    
    # 显示结果
    print("=== 分段结果 ===")
    for chunk in chunks:
        print(f"\n分段 {chunk.order}: {chunk.title}")
        print(f"Token数: {chunk.estimated_tokens}")
        print(f"标题路径: {chunk.metadata['header_path']}")
        print(f"内容预览: {chunk.content[:100]}...")
        print("-" * 50)
    
    # 显示摘要
    summary = splitter.get_split_summary(chunks)
    print(f"\n=== 分段摘要 ===")
    print(f"总分段数: {summary['total_chunks']}")
    print(f"总Token数: {summary['total_tokens']}")
    print(f"平均Token数: {summary['avg_tokens_per_chunk']}")
    print(f"超限分段数: {summary['chunks_over_limit']}")
    print(f"过小分段数: {summary['chunks_under_limit']}")


if __name__ == "__main__":
    example_usage()
