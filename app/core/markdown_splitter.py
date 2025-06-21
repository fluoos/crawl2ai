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
        """判断两个段落是否可以合并（改进版：更灵活的合并条件）"""
        stack1 = section1['header_stack']
        stack2 = section2['header_stack']
        
        # 如果都没有标题，可以合并
        if not stack1 and not stack2:
            return True
        
        # 如果其中一个没有标题，也可以合并（放宽条件）
        if not stack1 or not stack2:
            return True
        
        # 如果标题层级相同或section2是section1的子章节，可以合并
        if len(stack2) >= len(stack1):
            return stack1 == stack2[:len(stack1)]
        
        # 如果section1是section2的子章节，也可以合并
        if len(stack1) > len(stack2):
            return stack2 == stack1[:len(stack2)]
        
        # 如果都是同一个父级下的子章节，也可以合并
        if len(stack1) == len(stack2) and len(stack1) > 1:
            return stack1[:-1] == stack2[:-1]
        
        return False
    
    def _split_large_sections(self, sections: List[Dict]) -> List[Dict]:
        """分割过大的段落，简化且可靠的算法"""
        result = []
        
        for section in sections:
            tokens = self.estimate_tokens(section['content'])
            
            if tokens <= self.max_tokens:
                result.append(section)
                continue
            
            # 简单但可靠的分割策略：按句子分割
            content = section['content']
            sentences = self._split_into_sentences(content)
            
            current_chunk = ''
            chunk_counter = 0
            
            # 提取标题行（如果有的话）
            lines = content.split('\n')
            header_line = ''
            content_start_idx = 0
            
            for i, line in enumerate(lines):
                if line.strip().startswith('#'):
                    header_line = line + '\n'
                    content_start_idx = i + 1
                    break
            
            for sentence in sentences:
                sentence_tokens = self.estimate_tokens(sentence)
                current_tokens = self.estimate_tokens(current_chunk)
                
                # 如果添加这个句子会超出限制，并且当前chunk不为空
                if (current_tokens + sentence_tokens > self.max_tokens and 
                    current_chunk.strip()):
                    
                    # 保存当前chunk
                    chunk_content = header_line + current_chunk if chunk_counter == 0 else current_chunk
                    if chunk_content.strip():
                        result.append({
                            'content': chunk_content.strip(),
                            'header_stack': section['header_stack'].copy(),
                            'start_line': section['start_line'],
                            'end_line': section['start_line'] + 10  # 简化行号处理
                        })
                    
                    # 开始新chunk
                    current_chunk = sentence
                    chunk_counter += 1
                else:
                    current_chunk += sentence
            
            # 添加最后一个chunk
            if current_chunk.strip():
                chunk_content = header_line + current_chunk if chunk_counter == 0 else current_chunk
                result.append({
                    'content': chunk_content.strip(),
                    'header_stack': section['header_stack'].copy(),
                    'start_line': section['start_line'],
                    'end_line': section['end_line']
                })
        
        return result
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割为句子"""
        # 简单的句子分割，基于标点符号和换行
        import re
        
        # 先按双换行分割段落
        paragraphs = text.split('\n\n')
        sentences = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
                
            # 对于每个段落，按句号、问号、感叹号分割
            para_sentences = re.split(r'[。！？.!?]\s*', paragraph)
            
            for i, sentence in enumerate(para_sentences):
                if sentence.strip():
                    # 恢复标点符号（除了最后一个）
                    if i < len(para_sentences) - 1:
                        # 查找原始标点
                        next_start = paragraph.find(sentence) + len(sentence)
                        if next_start < len(paragraph):
                            punctuation = paragraph[next_start:next_start+1]
                            if punctuation in '。！？.!?':
                                sentence += punctuation
                    
                    sentences.append(sentence + '\n')
            
            # 添加段落分隔
            if sentences:
                sentences.append('\n')
        
        return sentences
    
    def _find_last_header(self, lines: List[str]) -> Optional[str]:
        """在行列表中找到最后一个标题行"""
        for line in reversed(lines):
            is_header, _, _ = self._is_header_line(line)
            if is_header:
                return line
        return None
    
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
        
        # 4. 后处理：再次合并仍然过小的段落
        sections = self._post_process_small_sections(sections)
        
        # 5. 最终安全网：确保没有过小分段
        sections = self._final_cleanup(sections)
        
        # 6. 构建MarkdownChunk对象
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
    
    def _post_process_small_sections(self, sections: List[Dict]) -> List[Dict]:
        """后处理：多轮强力合并过小段落"""
        if not sections:
            return []
        
        result = sections[:]
        max_iterations = 5  # 最多处理5轮
        
        for iteration in range(max_iterations):
            # 检查是否还有过小的段落
            has_small_sections = any(
                self.estimate_tokens(section['content']) < self.min_tokens 
                for section in result
            )
            
            if not has_small_sections:
                break  # 没有过小段落，退出循环
            
            # 执行一轮合并
            result = self._merge_round(result, iteration)
        
        return result
    
    def _merge_round(self, sections: List[Dict], round_num: int) -> List[Dict]:
        """执行一轮合并，每轮的策略越来越激进"""
        if not sections:
            return []
        
        merged = []
        i = 0
        
        while i < len(sections):
            current = sections[i]
            current_tokens = self.estimate_tokens(current['content'])
            
            # 如果当前段落过小，尝试合并
            if current_tokens < self.min_tokens:
                merged_successfully = False
                
                # 策略1：向前合并（与前一个段落合并）
                if merged and not merged_successfully:
                    last_tokens = self.estimate_tokens(merged[-1]['content'])
                    if last_tokens + current_tokens <= self.max_tokens:
                        # 执行向前合并
                        merged[-1]['content'] += '\n\n' + current['content']
                        merged[-1]['end_line'] = current['end_line']
                        if (current['header_stack'] and 
                            len(current['header_stack']) > len(merged[-1]['header_stack'])):
                            merged[-1]['header_stack'] = current['header_stack']
                        merged_successfully = True
                
                # 策略2：向后合并（与后一个段落合并）
                if not merged_successfully and i + 1 < len(sections):
                    next_section = sections[i + 1]
                    next_tokens = self.estimate_tokens(next_section['content'])
                    if current_tokens + next_tokens <= self.max_tokens:
                        # 执行向后合并
                        merged_content = current['content'] + '\n\n' + next_section['content']
                        merged_section = {
                            'content': merged_content,
                            'header_stack': current['header_stack'] if current['header_stack'] else next_section['header_stack'],
                            'start_line': current['start_line'],
                            'end_line': next_section['end_line']
                        }
                        merged.append(merged_section)
                        i += 2  # 跳过下一个段落
                        merged_successfully = True
                
                # 策略3：激进合并（第2轮及以后）
                if not merged_successfully and round_num >= 1:
                    # 更激进的合并策略
                    if merged:
                        # 强制与前一个合并，即使会稍微超限
                        last_tokens = self.estimate_tokens(merged[-1]['content'])
                        if last_tokens + current_tokens <= self.max_tokens * 1.2:  # 允许超限20%
                            merged[-1]['content'] += '\n\n' + current['content']
                            merged[-1]['end_line'] = current['end_line']
                            merged_successfully = True
                    elif i + 1 < len(sections):
                        # 强制与后一个合并
                        next_section = sections[i + 1]
                        merged_content = current['content'] + '\n\n' + next_section['content']
                        merged_section = {
                            'content': merged_content,
                            'header_stack': current['header_stack'] if current['header_stack'] else next_section['header_stack'],
                            'start_line': current['start_line'],
                            'end_line': next_section['end_line']
                        }
                        merged.append(merged_section)
                        i += 2
                        merged_successfully = True
                
                # 如果所有策略都失败，保留原段落（但这种情况应该很少）
                if not merged_successfully:
                    merged.append(current)
                    i += 1
            else:
                # 当前段落正常，直接添加
                merged.append(current)
                i += 1
        
        return merged
    
    def _final_cleanup(self, sections: List[Dict]) -> List[Dict]:
        """最终清理：强制处理所有过小分段"""
        if not sections:
            return []
        
        result = []
        
        for section in sections:
            tokens = self.estimate_tokens(section['content'])
            
            if tokens < self.min_tokens:
                # 过小段落的最终处理策略
                if result:
                    # 强制合并到前一个段落，不管是否超限
                    result[-1]['content'] += '\n\n' + section['content']
                    result[-1]['end_line'] = section['end_line']
                else:
                    # 如果是第一个段落且过小，保留它（总比丢失内容好）
                    result.append(section)
            else:
                result.append(section)
        
        return result
    
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
