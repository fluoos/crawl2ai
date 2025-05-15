import os
from typing import List, Union, Optional
from pathlib import Path

def join_paths(*paths: Union[str, Path]) -> str:
    """
    连接多个路径为一个路径字符串
    
    Args:
        *paths: 一个或多个路径字符串或Path对象
        
    Returns:
        str: 连接后的路径字符串，使用正斜杠(/)作为分隔符
    """
    joined_path = os.path.join(*paths)
    # 确保路径使用正斜杠，避免Windows和Linux路径表示不一致
    return joined_path.replace('\\', '/')

def ensure_dir(dir_path: Union[str, Path]) -> str:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        dir_path: 目录路径
        
    Returns:
        str: 规范化后的目录路径
    """
    path = join_paths(dir_path)
    os.makedirs(path, exist_ok=True)
    return path

def get_output_path(*paths: Union[str, Path]) -> str:
    """
    获取输出目录下的文件路径
    
    Args:
        *paths: 路径片段，将会被添加到输出根目录后
        
    Returns:
        str: 完整的输出文件路径
    """
    from app.core.config import settings
    return join_paths(settings.OUTPUT_DIR, *paths)

def get_project_output_path(project_id: str, *paths: Union[str, Path]) -> str:
    """
    获取项目特定的输出目录下的文件路径
    
    Args:
        project_id: 项目ID
        *paths: 路径片段，将会被添加到项目输出目录后
        
    Returns:
        str: 完整的项目输出文件路径
    """
    if not project_id:
        return get_output_path(*paths)
    
    from app.core.config import settings
    project_dir = join_paths(settings.OUTPUT_DIR, str(project_id))
    ensure_dir(project_dir)
    return join_paths(project_dir, *paths)

def get_export_path(*paths: Union[str, Path]) -> str:
    """
    获取导出目录下的文件路径
    
    Args:
        *paths: 路径片段，将会被添加到导出根目录后
        
    Returns:
        str: 完整的导出文件路径
    """
    from app.core.config import settings
    return join_paths(settings.EXPORT_DIR, *paths)

def get_upload_path(*paths: Union[str, Path]) -> str:
    """
    获取上传目录下的文件路径
    
    Args:
        *paths: 路径片段，将会被添加到上传根目录后
        
    Returns:
        str: 完整的上传文件路径
    """
    from app.core.config import settings
    return join_paths(settings.UPLOAD_DIR, *paths)

def get_config_path(*paths: Union[str, Path]) -> str:
    """
    获取配置目录下的文件路径
    
    Args:
        *paths: 路径片段，将会被添加到配置根目录后
        
    Returns:
        str: 完整的配置文件路径
    """
    from app.core.config import settings
    return join_paths(settings.SYSTEM_CONFIG_DIR, *paths) 