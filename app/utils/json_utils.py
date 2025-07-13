import re
import json
from typing import Any, Optional

class JsonUtils:
    """JSON工具类，提供JSON格式化和处理功能"""
    
    @staticmethod
    def fix_json_format(json_text: str) -> str:
        """
        修复常见的JSON格式问题
        
        Args:
            json_text: 需要修复的JSON文本
            
        Returns:
            str: 修复后的JSON文本
        """
        if not json_text or not json_text.strip():
            return "{}"
            
        # 1. 替换单引号为双引号
        result = json_text.replace("'", "\"")
        
        # 2. 确保属性名使用双引号
        result = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', result)
        
        # 3. 修复尾部逗号问题
        result = re.sub(r',\s*}', '}', result)
        result = re.sub(r',\s*]', ']', result)
        
        # 4. 删除注释
        result = re.sub(r'//.*?\n', '\n', result)
        result = re.sub(r'/\*.*?\*/', '', result, flags=re.DOTALL)
        
        # 5. 处理无效的控制字符
        result = ''.join(ch for ch in result if (ch >= ' ' and ord(ch) < 127) or ch in ['\n', '\r', '\t'])
        
        # 6. 替换不规范的转义序列
        result = re.sub(r'\\([^"\\/bfnrtu])', r'\1', result)
        
        # 7. 修复缺少逗号的问题
        result = re.sub(r'([\}\]])\s*(\")', r'\1,\2', result)
        
        return result
    
    @staticmethod
    def safe_loads(json_text: str, default_value: Any = None) -> Any:
        """
        安全地解析JSON文本，出错时返回默认值
        
        Args:
            json_text: JSON文本
            default_value: 解析失败时返回的默认值
            
        Returns:
            Any: 解析后的数据或默认值
        """
        try:
            if not json_text or not json_text.strip():
                return default_value
            return json.loads(json_text)
        except json.JSONDecodeError:
            try:
                # 尝试修复并重新解析
                fixed_text = JsonUtils.fix_json_format(json_text)
                return json.loads(fixed_text)
            except:
                return default_value
    
    @staticmethod
    def safe_dumps(data: Any, ensure_ascii: bool = False, indent: Optional[int] = None) -> str:
        """
        安全地序列化数据为JSON文本
        
        Args:
            data: 要序列化的数据
            ensure_ascii: 是否确保ASCII编码
            indent: 缩进空格数，None表示不缩进
            
        Returns:
            str: JSON文本
        """
        try:
            return json.dumps(data, ensure_ascii=ensure_ascii, indent=indent)
        except:
            return "{}" if isinstance(data, dict) else "[]" if isinstance(data, list) else '""' 