import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, List, Set
import markdownify
from abc import ABC, abstractmethod
from collections import deque

class CrawlStrategy(ABC):
    """爬取策略抽象基类"""
    def __init__(self, max_depth: int, max_pages: int):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.url_queue = self._init_queue()
        
    @abstractmethod
    def _init_queue(self):
        """初始化队列/栈"""
        pass
    
    @abstractmethod
    def add_url(self, url: str, depth: int, score: float):
        """添加URL到队列"""
        pass
    
    @abstractmethod
    def get_next_url(self) -> tuple:
        """获取下一个要处理的URL"""
        pass
    
    def has_urls(self) -> bool:
        """检查是否还有URL待处理"""
        return len(self.url_queue) > 0
    
    def should_crawl(self, url: str, depth: int, crawled_count: int) -> bool:
        """判断是否应该继续爬取"""
        return depth < self.max_depth and crawled_count < self.max_pages


class BFSCrawlStrategy(CrawlStrategy):
    """广度优先爬取策略 - 使用队列实现"""
    
    def _init_queue(self):
        """BFS使用双端队列"""
        return deque()
    
    def add_url(self, url: str, depth: int, score: float):
        """BFS: 添加到队列尾部"""
        self.url_queue.append((url, depth, score))
    
    def get_next_url(self) -> tuple:
        """BFS: 从队列头部取出（先进先出）"""
        if self.url_queue:
            return self.url_queue.popleft()
        return None


class DFSCrawlStrategy(CrawlStrategy):
    """深度优先爬取策略 - 使用栈实现"""
    
    def _init_queue(self):
        """DFS使用列表作为栈"""
        return []
    
    def add_url(self, url: str, depth: int, score: float):
        """DFS: 添加到栈顶"""
        self.url_queue.append((url, depth, score))
    
    def get_next_url(self) -> tuple:
        """DFS: 从栈顶取出（后进先出）"""
        if self.url_queue:
            return self.url_queue.pop()
        return None


class BeautifulSoupCrawler:
    """基于BeautifulSoup的网页爬虫"""
    
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    async def fetch_page(self, url: str) -> Dict[str, Any]:
        """获取单个页面的内容"""
        try:
            async with self.session.get(url, headers=self.headers, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 提取标题
                    title_tag = soup.find('title')
                    title = title_tag.get_text().strip() if title_tag else ""
                    
                    # 提取链接
                    links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(url, href)
                        if self._is_valid_url(full_url, url):
                            links.append(full_url)
                    
                    return {
                        'url': url,
                        'title': title,
                        'links': links,
                        'html': html,
                        'soup': soup,
                        'success': True,
                        'status_code': response.status
                    }
                else:
                    return {
                        'url': url,
                        'title': "",
                        'links': [],
                        'html': "",
                        'soup': None,
                        'success': False,
                        'status_code': response.status,
                        'error': f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                'url': url,
                'title': "",
                'links': [],
                'html': "",
                'soup': None,
                'success': False,
                'status_code': 0,
                'error': str(e)
            }
    
    def _is_valid_url(self, url: str, base_url: str) -> bool:
        """检查URL是否有效"""
        try:
            parsed = urlparse(url)
            base_parsed = urlparse(base_url)
            
            # 必须是HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # 必须是同一域名（默认不包含外部链接）
            if parsed.netloc != base_parsed.netloc:
                return False
            
            # 排除某些文件类型
            excluded_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                                 '.zip', '.rar', '.tar', '.gz', '.jpg', '.jpeg', '.png', '.gif', 
                                 '.svg', '.ico', '.css', '.js', '.xml', '.json']
            
            path_lower = parsed.path.lower()
            if any(path_lower.endswith(ext) for ext in excluded_extensions):
                return False
            
            return True
        except:
            return False
    
    async def convert_to_markdown(self, url: str, included_selector: str = None, 
                                excluded_selector: str = None) -> Dict[str, Any]:
        """将URL转换为Markdown"""
        try:
            page_data = await self.fetch_page(url)
            
            if not page_data['success']:
                return {
                    'url': url,
                    'markdown': "",
                    'title': "",
                    'success': False,
                    'error': page_data.get('error', 'Failed to fetch page'),
                    'status_code': page_data.get('status_code', 0)
                }
            
            soup = page_data['soup']
            
            # 移除不需要的标签
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            
            # 应用选择器过滤
            content_soup = soup
            if included_selector:
                try:
                    selected_elements = soup.select(included_selector)
                    if selected_elements:
                        # 创建新的 soup 只包含选中的元素
                        content_soup = BeautifulSoup('<div></div>', 'html.parser')
                        for element in selected_elements:
                            content_soup.div.append(element)
                except Exception as e:
                    print(f"应用包含选择器失败 {included_selector}: {e}")
            
            if excluded_selector:
                try:
                    for element in content_soup.select(excluded_selector):
                        element.decompose()
                except Exception as e:
                    print(f"应用排除选择器失败 {excluded_selector}: {e}")
            
            # 转换为Markdown
            markdown = markdownify.markdownify(
                str(content_soup),
                heading_style="ATX",
                bullets="-",
                strip=['script', 'style']
            )
            
            # 清理Markdown内容
            markdown = self._clean_markdown(markdown)
            
            return {
                'url': url,
                'markdown': markdown,
                'title': page_data['title'],
                'success': True,
                'status_code': page_data['status_code']
            }
            
        except Exception as e:
            return {
                'url': url,
                'markdown': "",
                'title': "",
                'success': False,
                'error': str(e),
                'status_code': 0
            }
    
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


class CrawlerEngineService:
    """爬虫引擎服务类"""
    
    @staticmethod
    def create_crawl_strategy(strategy_type: str, max_depth: int, max_pages: int) -> CrawlStrategy:
        """创建爬取策略"""
        if strategy_type == "dfs":
            return DFSCrawlStrategy(max_depth, max_pages)
        else:  # 默认使用BFS
            return BFSCrawlStrategy(max_depth, max_pages)
    
    @staticmethod
    def create_crawler(session: aiohttp.ClientSession) -> BeautifulSoupCrawler:
        """创建爬虫实例"""
        return BeautifulSoupCrawler(session)
    
    @staticmethod
    def process_url(url: str) -> str:
        """处理URL，确保使用https协议"""
        if url.startswith('http://'):
            return url.replace('http://', 'https://', 1)
        return url
    
    @staticmethod
    def url_to_filename(url: str) -> str:
        """将URL转换为文件名"""
        parsed = urlparse(url)
        path = parsed.path.replace('.html', '')
        filename = path.strip('/').replace('/', '_')
        if not filename:
            filename = parsed.netloc
        return f"{filename}.md" 