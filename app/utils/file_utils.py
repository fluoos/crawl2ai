import os
import json
import logging
from typing import Any, Optional, Union
from pathlib import Path

class FileUtils:
    """文件操作工具类，提供统一的文件操作接口"""
    
    @staticmethod
    def read_json(file_path: Union[str, Path], default_value: Any = None) -> Any:
        """
        读取JSON文件，如果文件不存在则返回默认值
        
        Args:
            file_path: 文件路径
            default_value: 如果文件不存在或读取失败时返回的默认值
            
        Returns:
            Any: 解析后的JSON数据或默认值
        """
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                logging.info(f"文件不存在，返回默认值: {file_path}")
                return default_value
        except Exception as e:
            logging.error(f"读取JSON文件失败 {file_path}: {str(e)}")
            return default_value
    
    @staticmethod
    def write_json(file_path: Union[str, Path], data: Any, ensure_ascii: bool = False, indent: int = 2) -> bool:
        """
        写入JSON文件
        
        Args:
            file_path: 文件路径
            data: 要写入的数据
            ensure_ascii: 是否确保ASCII编码
            indent: 缩进空格数
            
        Returns:
            bool: 写入是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
            return True
        except Exception as e:
            logging.error(f"写入JSON文件失败 {file_path}: {str(e)}")
            return False
    
    @staticmethod
    def append_jsonl(file_path: Union[str, Path], data: Any) -> bool:
        """
        追加写入JSONL文件
        
        Args:
            file_path: 文件路径
            data: 要追加的数据
            
        Returns:
            bool: 写入是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            logging.error(f"追加JSONL文件失败 {file_path}: {str(e)}")
            return False
    
    @staticmethod
    def ensure_dir(path: Union[str, Path]) -> bool:
        """
        确保目录存在，如果不存在则创建
        
        Args:
            path: 目录路径
            
        Returns:
            bool: 操作是否成功
        """
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            logging.error(f"创建目录失败 {path}: {str(e)}")
            return False
    
    @staticmethod
    def safe_delete(path: Union[str, Path]) -> bool:
        """
        安全删除文件或目录
        
        Args:
            path: 文件或目录路径
            
        Returns:
            bool: 删除是否成功
        """
        try:
            if os.path.exists(path):
                if os.path.isfile(path):
                    os.remove(path)
                else:
                    import shutil
                    shutil.rmtree(path)
                return True
            return False
        except Exception as e:
            logging.error(f"删除失败 {path}: {str(e)}")
            return False 