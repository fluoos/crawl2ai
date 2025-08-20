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
                        # 深拷贝标题栈，确保每个分段独立
                        section_copy = current_section.copy()
                        section_copy['header_stack'] = current_section['header_stack'].copy()
                        sections.append(section_copy)
                    
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
            # 深拷贝标题栈，确保每个分段独立
            section_copy = current_section.copy()
            section_copy['header_stack'] = current_section['header_stack'].copy()
            sections.append(section_copy)
        
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
                # 智能合并标题栈
                merged[-1]['header_stack'] = self._merge_header_stacks(
                    merged[-1]['header_stack'], current['header_stack']
                )
            else:
                merged.append(current)
        
        return merged
    
    def _smart_merge_sections(self, sections: List[Dict], adaptive_params: Dict[str, int]) -> List[Dict]:
        """智能合并策略，在保持结构完整性的同时优化Token分布"""
        if not sections:
            return []
        
        # 获取自适应参数
        merge_threshold = adaptive_params.get('merge_threshold', 0.5)
        target_min_tokens = adaptive_params.get('min_tokens', self.min_tokens)
        target_max_tokens = adaptive_params.get('max_tokens', self.max_tokens)
        
        # 计算目标Token数
        total_tokens = sum(self.estimate_tokens(section['content']) for section in sections)
        target_avg_tokens = total_tokens // len(sections) if sections else 0
        
        merged = []
        
        for current in sections:
            current_tokens = self.estimate_tokens(current['content'])
            
            # 如果合并列表为空，直接添加
            if not merged:
                merged.append(current)
                continue
            
            last_tokens = self.estimate_tokens(merged[-1]['content'])
            
            # 智能合并决策
            should_merge = self._should_merge_smartly(
                merged[-1], current, 
                current_tokens, last_tokens,
                target_avg_tokens, target_min_tokens, target_max_tokens,
                merge_threshold
            )
            
            if should_merge:
                # 执行智能合并
                merged[-1] = self._merge_sections_smartly(merged[-1], current)
            else:
                merged.append(current)
        
        return merged
    
    def _should_merge_smartly(self, section1: Dict, section2: Dict, 
                             tokens1: int, tokens2: int,
                             target_avg: int, target_min: int, target_max: int,
                             merge_threshold: float) -> bool:
        """智能判断是否应该合并两个段落"""
        
        # 基础条件检查
        if tokens2 >= target_max:
            return False  # 当前段落已经足够大
        
        combined_tokens = tokens1 + tokens2
        
        # 1. 层级兼容性检查
        if not self._can_merge_sections(section1, section2):
            return False
        
        # 2. Token限制检查
        if combined_tokens > target_max:
            return False
        
        # 3. 智能合并评分
        score = 0.0
        
        # 3.1 Token分布优化评分
        if combined_tokens <= target_avg:
            score += 0.3  # 合并后接近目标平均值
        elif combined_tokens <= target_avg * 1.2:
            score += 0.2  # 合并后略高于目标平均值
        elif combined_tokens <= target_avg * 1.5:
            score += 0.1  # 合并后明显高于目标平均值
        
        # 3.2 过小段落处理评分
        if tokens2 < target_min:
            score += 0.4  # 当前段落过小，强烈建议合并
        elif tokens2 < target_min * 1.5:
            score += 0.2  # 当前段落较小，建议合并
        
        # 3.3 语义相关性评分
        semantic_score = self._calculate_semantic_similarity(section1, section2)
        score += semantic_score * 0.3
        
        # 3.4 结构完整性评分
        structure_score = self._calculate_structure_compatibility(section1, section2)
        score += structure_score * 0.2
        
        return score >= merge_threshold
    
    def _calculate_semantic_similarity(self, section1: Dict, section2: Dict) -> float:
        """计算两个段落的语义相似度"""
        # 基于标题栈的相似度计算
        stack1 = section1['header_stack']
        stack2 = section2['header_stack']
        
        if not stack1 or not stack2:
            return 0.5  # 没有标题信息，给中等相似度
        
        # 计算标题栈的相似度
        common_prefix_len = 0
        min_len = min(len(stack1), len(stack2))
        
        for i in range(min_len):
            if stack1[i] == stack2[i]:
                common_prefix_len += 1
            else:
                break
        
        # 相似度 = 公共前缀长度 / 最大栈长度
        max_len = max(len(stack1), len(stack2))
        similarity = common_prefix_len / max_len if max_len > 0 else 0
        
        return similarity
    
    def _calculate_structure_compatibility(self, section1: Dict, section2: Dict) -> float:
        """计算结构兼容性"""
        stack1 = section1['header_stack']
        stack2 = section2['header_stack']
        
        # 父子关系
        if len(stack1) < len(stack2) and stack1 == stack2[:len(stack1)]:
            return 0.9  # 父子关系，高度兼容
        elif len(stack2) < len(stack1) and stack2 == stack1[:len(stack2)]:
            return 0.9  # 父子关系，高度兼容
        
        # 同级关系
        if len(stack1) == len(stack2) and len(stack1) > 1:
            if stack1[:-1] == stack2[:-1]:
                return 0.7  # 同级关系，中等兼容
        
        # 无标题段落
        if not stack1 and not stack2:
            return 0.6  # 都无标题，中等兼容
        
        return 0.3  # 其他情况，低兼容性
    
    def _merge_sections_smartly(self, section1: Dict, section2: Dict) -> Dict:
        """智能合并两个段落"""
        # 合并内容
        merged_content = section1['content'] + '\n\n' + section2['content']
        
        # 智能合并标题栈
        merged_header_stack = self._merge_header_stacks(
            section1['header_stack'], section2['header_stack']
        )
        
        return {
            'content': merged_content,
            'header_stack': merged_header_stack,
            'start_line': section1['start_line'],
            'end_line': section2['end_line']
        }
    
    def _can_merge_sections(self, section1: Dict, section2: Dict) -> bool:
        """判断两个段落是否可以合并（改进版：更完善的层级兼容性检查）"""
        stack1 = section1['header_stack']
        stack2 = section2['header_stack']
        
        # 如果都没有标题，可以合并
        if not stack1 and not stack2:
            return True
        
        # 如果其中一个没有标题，也可以合并（放宽条件）
        if not stack1 or not stack2:
            return True
        
        # 检查标题层级兼容性
        return self._are_headers_compatible(stack1, stack2)
    
    def _are_headers_compatible(self, stack1: List[Tuple[int, str]], stack2: List[Tuple[int, str]]) -> bool:
        """检查两个标题栈是否兼容"""
        if not stack1 or not stack2:
            return True
        
        # 情况1：父子关系 - section2是section1的子章节
        if len(stack2) > len(stack1):
            return stack1 == stack2[:len(stack1)]
        
        # 情况2：父子关系 - section1是section2的子章节  
        if len(stack1) > len(stack2):
            return stack2 == stack1[:len(stack2)]
        
        # 情况3：同级关系 - 相同层级的标题
        if len(stack1) == len(stack2):
            # 如果是根级标题（只有一级），检查是否为相邻的同级标题
            if len(stack1) == 1:
                return self._are_sibling_headers(stack1[0], stack2[0])
            # 如果是子级标题，检查是否有相同的父级
            else:
                return stack1[:-1] == stack2[:-1]
        
        return False
    
    def _are_sibling_headers(self, header1: Tuple[int, str], header2: Tuple[int, str]) -> bool:
        """检查两个标题是否为同级标题（允许合并）"""
        level1, text1 = header1
        level2, text2 = header2
        
        # 必须是相同级别
        if level1 != level2:
            return False
        
        # 对于一级标题，通常不合并（章节级别）
        if level1 == 1:
            return False
        
        # 对于其他级别，允许合并
        return True
    
    def _merge_header_stacks(self, stack1: List[Tuple[int, str]], stack2: List[Tuple[int, str]]) -> List[Tuple[int, str]]:
        """智能合并两个标题栈"""
        if not stack1:
            return stack2
        if not stack2:
            return stack1
        
        # 如果stack2更深，使用stack2
        if len(stack2) > len(stack1):
            return stack2
        
        # 如果stack1更深，使用stack1
        if len(stack1) > len(stack2):
            return stack1
        
        # 如果深度相同，选择更具体的标题栈
        if len(stack1) == len(stack2):
            # 比较最后一个标题的级别，选择更高级别的
            if stack1[-1][0] < stack2[-1][0]:
                return stack1
            elif stack2[-1][0] < stack1[-1][0]:
                return stack2
            else:
                # 级别相同，选择第一个（保持原有逻辑）
                return stack1
        
        return stack1
    
    def _split_large_sections(self, sections: List[Dict]) -> List[Dict]:
        """改进的大段落分割算法，优先保持语义完整性"""
        result = []
        
        for section in sections:
            tokens = self.estimate_tokens(section['content'])
            
            if tokens <= self.max_tokens:
                result.append(section)
                continue
            
            # 使用多级分割策略
            split_chunks = self._split_section_multilevel(section)
            result.extend(split_chunks)
        
        return result
    
    def _split_section_multilevel(self, section: Dict) -> List[Dict]:
        """多级分割策略：段落→句子→词语"""
        content = section['content']
        tokens = self.estimate_tokens(content)
        
        # 策略1：按段落分割
        paragraph_chunks = self._split_by_paragraphs(section)
        if len(paragraph_chunks) > 1:
            return paragraph_chunks
        
        # 策略2：按句子分割
        sentence_chunks = self._split_by_sentences(section)
        if len(sentence_chunks) > 1:
            return sentence_chunks
        
        # 策略3：按词语分割（最后手段）
        word_chunks = self._split_by_words(section)
        return word_chunks
    
    def _split_by_paragraphs(self, section: Dict) -> List[Dict]:
        """按段落分割，保持语义完整性"""
        content = section['content']
        paragraphs = content.split('\n\n')
        
        if len(paragraphs) <= 1:
            return [section]  # 只有一个段落，无法分割
        
        chunks = []
        current_chunk = ''
        chunk_counter = 0
        
        # 提取标题行
        lines = content.split('\n')
        header_line = ''
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                header_line = line + '\n'
                break
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            paragraph_tokens = self.estimate_tokens(paragraph)
            current_tokens = self.estimate_tokens(current_chunk)
            
            # 如果添加这个段落会超出限制，并且当前chunk不为空
            if (current_tokens + paragraph_tokens > self.max_tokens and 
                current_chunk.strip()):
                
                # 保存当前chunk
                chunk_content = header_line + current_chunk if chunk_counter == 0 else current_chunk
                if chunk_content.strip():
                    chunks.append({
                        'content': chunk_content.strip(),
                        'header_stack': section['header_stack'].copy(),
                        'start_line': section['start_line'],
                        'end_line': section['start_line'] + 10
                    })
                
                # 开始新chunk
                current_chunk = paragraph + '\n\n'
                chunk_counter += 1
            else:
                current_chunk += paragraph + '\n\n'
        
        # 添加最后一个chunk
        if current_chunk.strip():
            chunk_content = header_line + current_chunk if chunk_counter == 0 else current_chunk
            chunks.append({
                'content': chunk_content.strip(),
                'header_stack': section['header_stack'].copy(),
                'start_line': section['start_line'],
                'end_line': section['end_line']
            })
        
        return chunks if len(chunks) > 1 else [section]
    
    def _split_by_sentences(self, section: Dict) -> List[Dict]:
        """按句子分割，改进的句子分割算法"""
        content = section['content']
        sentences = self._split_into_sentences_improved(content)
        
        if len(sentences) <= 1:
            return [section]  # 只有一个句子，无法分割
        
        chunks = []
        current_chunk = ''
        chunk_counter = 0
        
        # 提取标题行
        lines = content.split('\n')
        header_line = ''
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                header_line = line + '\n'
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
                    chunks.append({
                        'content': chunk_content.strip(),
                        'header_stack': section['header_stack'].copy(),
                        'start_line': section['start_line'],
                        'end_line': section['start_line'] + 10
                    })
                
                # 开始新chunk
                current_chunk = sentence
                chunk_counter += 1
            else:
                current_chunk += sentence
        
        # 添加最后一个chunk
        if current_chunk.strip():
            chunk_content = header_line + current_chunk if chunk_counter == 0 else current_chunk
            chunks.append({
                'content': chunk_content.strip(),
                'header_stack': section['header_stack'].copy(),
                'start_line': section['start_line'],
                'end_line': section['end_line']
            })
        
        return chunks if len(chunks) > 1 else [section]
    
    def _split_by_words(self, section: Dict) -> List[Dict]:
        """按词语分割（最后手段）"""
        content = section['content']
        words = content.split()
        
        if len(words) <= 100:  # 如果词语太少，不分割
            return [section]
        
        chunks = []
        current_chunk = ''
        chunk_counter = 0
        word_count = 0
        
        # 提取标题行
        lines = content.split('\n')
        header_line = ''
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                header_line = line + '\n'
                break
        
        for word in words:
            word_tokens = self.estimate_tokens(word + ' ')
            current_tokens = self.estimate_tokens(current_chunk)
            
            # 如果添加这个词语会超出限制，并且当前chunk不为空
            if (current_tokens + word_tokens > self.max_tokens and 
                current_chunk.strip() and word_count > 50):  # 确保每个chunk至少有50个词
                
                # 保存当前chunk
                chunk_content = header_line + current_chunk if chunk_counter == 0 else current_chunk
                if chunk_content.strip():
                    chunks.append({
                        'content': chunk_content.strip(),
                        'header_stack': section['header_stack'].copy(),
                        'start_line': section['start_line'],
                        'end_line': section['start_line'] + 10
                    })
                
                # 开始新chunk
                current_chunk = word + ' '
                chunk_counter += 1
                word_count = 1
            else:
                current_chunk += word + ' '
                word_count += 1
        
        # 添加最后一个chunk
        if current_chunk.strip():
            chunk_content = header_line + current_chunk if chunk_counter == 0 else current_chunk
            chunks.append({
                'content': chunk_content.strip(),
                'header_stack': section['header_stack'].copy(),
                'start_line': section['start_line'],
                'end_line': section['end_line']
            })
        
        return chunks if len(chunks) > 1 else [section]
    
    def _split_into_sentences_improved(self, text: str) -> List[str]:
        """改进的句子分割算法"""
        # 先按双换行分割段落
        paragraphs = text.split('\n\n')
        sentences = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            # 改进的句子分割正则表达式
            # 考虑更多的句子结束标记和特殊情况
            para_sentences = re.split(r'([。！？.!?]+\s*)', paragraph)
            
            current_sentence = ''
            for i in range(0, len(para_sentences), 2):
                if i < len(para_sentences):
                    current_sentence += para_sentences[i]
                    if i + 1 < len(para_sentences):
                        current_sentence += para_sentences[i + 1]
                    
                    if current_sentence.strip():
                        sentences.append(current_sentence + '\n')
                        current_sentence = ''
            
            # 处理最后一个句子（如果没有标点符号）
            if current_sentence.strip():
                sentences.append(current_sentence + '\n')
            
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
        创建分段（优化版）
        
        Args:
            content: Markdown内容
            
        Returns:
            List[MarkdownChunk]: 分段列表
        """
        if not content.strip():
            return []
        
        # 1. 分析文档结构
        structure_info = self._analyze_document_structure(content)
        adaptive_params = self._get_adaptive_parameters(structure_info)
        
        # 2. 基于标题分割
        sections = self._split_by_headers(content)
        
        # 3. 智能合并过小段落
        sections = self._smart_merge_sections(sections, adaptive_params)
        
        # 4. 改进的大段落分割
        sections = self._split_large_sections(sections)
        
        # 5. 后处理：再次智能合并
        sections = self._post_process_small_sections(sections)
        
        # 6. 最终清理：确保没有过小分段
        sections = self._final_cleanup(sections)
        
        # 7. 构建MarkdownChunk对象
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
                    'split_method': 'intelligent_adaptive',
                    'structure_type': structure_info['structure_type'],
                    'adaptive_params': adaptive_params
                }
            )
            chunks.append(chunk)
        
        # 8. Token分布监控和优化
        distribution_info = self._check_token_distribution(chunks)
        if distribution_info['quality'] in ['poor', 'fair']:
            # 如果分布质量不佳，尝试重新优化
            chunks = self._optimize_token_distribution(chunks, adaptive_params)
        
        return chunks
    
    def _optimize_token_distribution(self, chunks: List[MarkdownChunk], 
                                   adaptive_params: Dict[str, int]) -> List[MarkdownChunk]:
        """优化Token分布"""
        if len(chunks) <= 1:
            return chunks
        
        # 计算目标Token数
        total_tokens = sum(chunk.estimated_tokens for chunk in chunks)
        target_avg = total_tokens // len(chunks)
        target_min = adaptive_params.get('min_tokens', self.min_tokens)
        target_max = adaptive_params.get('max_tokens', self.max_tokens)
        
        # 找出过小和过大的分段
        small_chunks = [i for i, chunk in enumerate(chunks) if chunk.estimated_tokens < target_min]
        large_chunks = [i for i, chunk in enumerate(chunks) if chunk.estimated_tokens > target_max]
        
        # 如果问题不严重，直接返回
        if len(small_chunks) <= 1 and len(large_chunks) <= 1:
            return chunks
        
        # 尝试重新合并过小的分段
        optimized_chunks = []
        i = 0
        
        while i < len(chunks):
            current_chunk = chunks[i]
            current_tokens = current_chunk.estimated_tokens
            
            # 如果当前分段过小，尝试与下一个分段合并
            if (current_tokens < target_min and 
                i + 1 < len(chunks) and
                current_tokens + chunks[i + 1].estimated_tokens <= target_max):
                
                # 合并分段
                merged_content = current_chunk.content + '\n\n' + chunks[i + 1].content
                merged_title = current_chunk.title if current_chunk.title != "未分类内容" else chunks[i + 1].title
                
                merged_chunk = MarkdownChunk(
                    content=merged_content,
                    title=merged_title,
                    order=len(optimized_chunks) + 1,
                    estimated_tokens=current_tokens + chunks[i + 1].estimated_tokens,
                    start_line=current_chunk.start_line,
                    end_line=chunks[i + 1].end_line,
                    metadata=current_chunk.metadata
                )
                
                optimized_chunks.append(merged_chunk)
                i += 2  # 跳过下一个分段
            else:
                # 更新序号
                current_chunk.order = len(optimized_chunks) + 1
                optimized_chunks.append(current_chunk)
                i += 1
        
        return optimized_chunks
    
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
                        # 智能合并标题栈
                        merged[-1]['header_stack'] = self._merge_header_stacks(
                            merged[-1]['header_stack'], current['header_stack']
                        )
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
                            'header_stack': self._merge_header_stacks(
                                current['header_stack'], next_section['header_stack']
                            ),
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
                            'header_stack': self._merge_header_stacks(
                                current['header_stack'], next_section['header_stack']
                            ),
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
    
    def get_optimized_split_summary(self, chunks: List[MarkdownChunk]) -> Dict[str, Any]:
        """获取优化后的分段摘要信息"""
        basic_summary = self.get_split_summary(chunks)
        distribution_info = self._check_token_distribution(chunks)
        
        # 合并信息
        summary = {
            **basic_summary,
            'distribution_quality': distribution_info['quality'],
            'distribution_score': distribution_info['quality_score'],
            'distribution_issues': distribution_info['issues'],
            'token_ratio': distribution_info['ratio'],
            'coefficient_of_variation': distribution_info['cv']
        }
        
        # 添加优化建议
        suggestions = []
        if distribution_info['quality'] == 'poor':
            suggestions.append('考虑调整max_tokens和min_tokens参数')
            suggestions.append('检查文档结构是否适合当前分割策略')
        elif distribution_info['quality'] == 'fair':
            suggestions.append('可以考虑微调分割参数以获得更好的分布')
        
        summary['optimization_suggestions'] = suggestions
        
        return summary
    
    def _check_token_distribution(self, chunks: List[MarkdownChunk]) -> Dict[str, Any]:
        """检查Token分布情况"""
        if not chunks:
            return {'quality': 'unknown', 'issues': []}
        
        token_counts = [chunk.estimated_tokens for chunk in chunks]
        max_tokens = max(token_counts)
        min_tokens = min(token_counts)
        avg_tokens = sum(token_counts) // len(token_counts)
        
        # 计算分布指标
        ratio = max_tokens / min_tokens if min_tokens > 0 else float('inf')
        std_dev = self._calculate_std(token_counts)
        cv = std_dev / avg_tokens if avg_tokens > 0 else 0  # 变异系数
        
        # 评估分布质量
        quality_score = 0
        issues = []
        
        # 检查Token比例
        if ratio > 5:
            quality_score += 1
            issues.append(f'Token分布不均匀，最大/最小比例: {ratio:.2f}')
        elif ratio > 3:
            quality_score += 0.5
            issues.append(f'Token分布略不均匀，最大/最小比例: {ratio:.2f}')
        
        # 检查变异系数
        if cv > 0.5:
            quality_score += 1
            issues.append(f'Token变异系数过高: {cv:.2f}')
        elif cv > 0.3:
            quality_score += 0.5
            issues.append(f'Token变异系数较高: {cv:.2f}')
        
        # 检查超限和过小分段
        over_limit = len([t for t in token_counts if t > self.max_tokens])
        under_limit = len([t for t in token_counts if t < self.min_tokens])
        
        if over_limit > 0:
            quality_score += 1
            issues.append(f'存在{over_limit}个超限分段')
        
        if under_limit > 0:
            quality_score += 0.5
            issues.append(f'存在{under_limit}个过小分段')
        
        # 确定质量等级
        if quality_score == 0:
            quality = 'excellent'
        elif quality_score <= 1:
            quality = 'good'
        elif quality_score <= 2:
            quality = 'fair'
        else:
            quality = 'poor'
        
        return {
            'quality': quality,
            'quality_score': quality_score,
            'issues': issues,
            'ratio': ratio,
            'cv': cv,
            'std_dev': std_dev,
            'over_limit_count': over_limit,
            'under_limit_count': under_limit
        }
    
    def _calculate_std(self, numbers: List[int]) -> float:
        """计算标准差"""
        if not numbers:
            return 0
        mean = sum(numbers) / len(numbers)
        variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
        return variance ** 0.5
    
    def _analyze_document_structure(self, content: str) -> Dict[str, Any]:
        """分析文档结构特征"""
        lines = content.split('\n')
        header_count = 0
        header_levels = []
        content_lines = 0
        code_blocks = 0
        tables = 0
        
        in_code_block = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 统计标题
            if line.startswith('#'):
                header_count += 1
                level = len(line.split()[0])
                header_levels.append(level)
            elif line.startswith('```'):
                in_code_block = not in_code_block
                if in_code_block:
                    code_blocks += 1
            elif '|' in line and not in_code_block:
                tables += 1
            else:
                content_lines += 1
        
        # 分析结构特征
        avg_header_level = sum(header_levels) / len(header_levels) if header_levels else 0
        max_header_level = max(header_levels) if header_levels else 0
        header_density = header_count / len(lines) if lines else 0
        
        return {
            'total_lines': len(lines),
            'header_count': header_count,
            'content_lines': content_lines,
            'code_blocks': code_blocks,
            'tables': tables,
            'avg_header_level': avg_header_level,
            'max_header_level': max_header_level,
            'header_density': header_density,
            'structure_type': self._classify_structure(header_count, header_density, max_header_level)
        }
    
    def _classify_structure(self, header_count: int, header_density: float, max_level: int) -> str:
        """分类文档结构类型"""
        if header_count == 0:
            return 'no_headers'
        elif header_density > 0.1:
            return 'header_dense'
        elif max_level >= 5:
            return 'deep_nested'
        elif header_count > 20:
            return 'many_sections'
        else:
            return 'normal'
    
    def _get_adaptive_parameters(self, structure_info: Dict[str, Any]) -> Dict[str, int]:
        """根据文档结构自适应调整参数"""
        structure_type = structure_info['structure_type']
        header_density = structure_info['header_density']
        
        # 基础参数
        base_max_tokens = self.max_tokens
        base_min_tokens = self.min_tokens
        
        # 根据结构类型调整
        if structure_type == 'no_headers':
            # 无标题文档，需要更激进的分割
            return {
                'max_tokens': int(base_max_tokens * 0.8),
                'min_tokens': int(base_min_tokens * 0.6),
                'merge_threshold': 0.7
            }
        elif structure_type == 'header_dense':
            # 标题密集，需要更保守的合并
            return {
                'max_tokens': int(base_max_tokens * 1.2),
                'min_tokens': int(base_min_tokens * 1.5),
                'merge_threshold': 0.3
            }
        elif structure_type == 'deep_nested':
            # 深度嵌套，需要更智能的合并
            return {
                'max_tokens': base_max_tokens,
                'min_tokens': int(base_min_tokens * 0.8),
                'merge_threshold': 0.5
            }
        elif structure_type == 'many_sections':
            # 章节众多，需要平衡合并
            return {
                'max_tokens': int(base_max_tokens * 1.1),
                'min_tokens': int(base_min_tokens * 1.2),
                'merge_threshold': 0.4
            }
        else:
            # 正常结构
            return {
                'max_tokens': base_max_tokens,
                'min_tokens': base_min_tokens,
                'merge_threshold': 0.5
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
