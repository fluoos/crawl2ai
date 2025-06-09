import os
import shutil
import json
import datetime
from typing import List, Dict, Any, Optional

from app.utils.path_utils import get_project_output_path, ensure_dir, join_paths
from app.core.config import settings
from app.core.markdown_splitter import MarkdownSplitter

class FilesService:
    """文件服务类，处理所有与文件相关的业务逻辑"""
    
    @staticmethod
    def get_file_list(page: int = 1, page_size: int = 10, project_id: Optional[str] = None) -> Dict[str, Any]:
        """获取文件列表"""
        # 读取markdown_manager.json文件
        manager_path = get_project_output_path(project_id, "markdown_manager.json")
        all_files = []
        
        if os.path.exists(manager_path):
            try:
                with open(manager_path, 'r', encoding='utf-8') as f:
                    manager_data = json.load(f)
                
                # 处理每一个记录，添加文件信息
                for item in manager_data:
                    if isinstance(item, dict) and 'filePath' in item:
                        file_path = item['filePath']
                        
                        # 确保文件路径使用系统分隔符
                        file_path = file_path.replace('/', os.sep)
                        
                        # 如果是相对路径，转换为绝对路径
                        if not os.path.isabs(file_path):
                            file_path = os.path.join(".", file_path)
                            
                        # 获取文件信息
                        if os.path.exists(file_path):
                            filename = os.path.basename(file_path)
                            stats = os.stat(file_path)
                            
                            # 创建文件记录
                            file_info = {
                                "filename": filename,
                                "path": file_path,
                                "size": stats.st_size,
                                "modifiedTime": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                                "url": item.get('url', ''),
                                "title": item.get('title', filename),
                                "isDataset": item.get('isDataset', False)
                            }
                            
                            # 添加manager_data中的其他字段
                            for key, value in item.items():
                                if key not in file_info:
                                    file_info[key] = value
                                    
                            all_files.append(file_info)
            except Exception as e:
                print(f"读取markdown_manager.json出错: {str(e)}")
                # 出错时使用空列表继续
                
        # 先按文件名升序排序，再按修改时间降序排序（稳定排序）
        all_files.sort(key=lambda x: x["filename"])
        all_files.sort(key=lambda x: x["modifiedTime"], reverse=True)
        
        # 计算分页
        total = len(all_files)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total)
        
        # 返回分页结果
        return {
            "files": all_files[start_idx:end_idx],
            "total": total,
            "page": page,
            "pageSize": page_size
        }
    
    @staticmethod
    def preview_file(path: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """预览Markdown文件内容"""
        # 安全检查：确保path是有效的，防止目录遍历攻击
        if ".." in path or "~" in path:
            raise ValueError("无效的文件路径")
        
        # 标准化路径，确保使用正确的分隔符
        file_path = path.replace('/', os.sep).replace('\\', os.sep)
        
        # 如果是相对路径且不以"."开头，添加"./"
        if not os.path.isabs(file_path) and not file_path.startswith("."):
            file_path = os.path.join(".", file_path)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise ValueError(f"文件 '{path}' 不存在")
        
        # 检查是否为文件而非目录
        if not os.path.isfile(file_path):
            raise ValueError(f"'{path}' 不是一个文件")
        
        # 检查文件大小，避免加载过大的文件
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB限制
            raise ValueError("文件过大，无法预览")
        
        # 读取文件内容
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            # 获取文件基本信息
            filename = os.path.basename(file_path)
            stats = os.stat(file_path)
            
            return {
                "status": "success",
                "content": content,
                "filename": filename,
                "size": stats.st_size,
                "modifiedTime": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }
        except UnicodeDecodeError:
            raise ValueError("文件编码错误，无法预览")
    
    @staticmethod
    def upload_files(files: List[Any], project_id: Optional[str] = None, smart_split_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """上传文件，非Markdown文件会被自动转换"""
        # 确保目录存在
        upload_dir = get_project_output_path(project_id, "upload")
        markdown_dir = get_project_output_path(project_id, "markdown")
        
        ensure_dir(upload_dir)
        ensure_dir(markdown_dir)
        
        uploaded_files = []
        converted_files = []
        
        for file in files:
            # 原始文件保存路径
            original_path = os.path.join(upload_dir, file.filename)
            
            # 保存原始文件
            with open(original_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            # 检查文件类型
            if file.filename.endswith(".md"):
                # 如果已经是Markdown，直接复制到markdown目录
                markdown_path = os.path.join(markdown_dir, file.filename)
                shutil.copy2(original_path, markdown_path)
                
                # 如果启用智能分段，处理Markdown文件
                if smart_split_config and smart_split_config.get("enableSmartSplit", False):
                    try:
                        split_result = FilesService.apply_smart_split_to_markdown(
                            markdown_path, 
                            smart_split_config,
                            project_id
                        )
                        if split_result["success"]:
                            uploaded_files.extend(split_result["files"])
                        else:
                            # 智能分段失败，使用原文件
                            base_name = os.path.splitext(file.filename)[0]
                            FilesService.update_markdown_registry(original_path, markdown_path, base_name, is_converted=False, project_id=project_id)
                            uploaded_files.append({
                                "filename": file.filename,
                                "path": markdown_path,
                                "size": os.stat(markdown_path).st_size,
                                "converted": False,
                                "error": split_result.get("error")
                            })
                    except Exception as e:
                        # 智能分段出错，使用原文件
                        base_name = os.path.splitext(file.filename)[0]
                        FilesService.update_markdown_registry(original_path, markdown_path, base_name, is_converted=False, project_id=project_id)
                        uploaded_files.append({
                            "filename": file.filename,
                            "path": markdown_path,
                            "size": os.stat(markdown_path).st_size,
                            "converted": False,
                            "error": f"智能分段失败: {str(e)}"
                        })
                else:
                    # 不启用智能分段，直接注册文件
                    base_name = os.path.splitext(file.filename)[0]
                    FilesService.update_markdown_registry(original_path, markdown_path, base_name, is_converted=False, project_id=project_id)
                    uploaded_files.append({
                        "filename": file.filename,
                        "path": markdown_path,
                        "size": os.stat(markdown_path).st_size,
                        "converted": False
                    })
            else:
                # 非Markdown文件，需要转换
                conversion_result = FilesService.convert_to_markdown(
                    original_path=original_path,
                    markdown_dir=markdown_dir,
                    filename=file.filename,
                    project_id=project_id,
                    smart_split_config=smart_split_config
                )
                
                if conversion_result["success"]:
                    if smart_split_config and smart_split_config.get("enableSmartSplit", False):
                        converted_files.extend(conversion_result["files"])
                    else:
                        converted_files.append(conversion_result["file_info"])
                else:
                    uploaded_files.append({
                        "filename": file.filename,
                        "path": original_path,
                        "size": os.stat(original_path).st_size,
                        "converted": False,
                        "error": conversion_result["error"]
                    })
        
        return {
            "status": "success",
            "message": f"成功上传 {len(uploaded_files) + len(converted_files)} 个文件，其中 {len(converted_files)} 个被转换为Markdown",
            "uploaded_files": uploaded_files,
            "converted_files": converted_files
        }
    
    @staticmethod
    def convert_to_markdown(original_path: str, markdown_dir: str, filename: str, project_id: Optional[str] = None, smart_split_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        将非Markdown文件转换为Markdown格式
        
        参数:
        - original_path: 原始文件的完整路径
        - markdown_dir: Markdown文件的存储目录
        - filename: 原始文件名
        - project_id: 项目ID
        
        返回:
        - Dict: 包含以下字段:
          - success: 布尔值，表示转换是否成功
          - file_info: 转换成功时，包含转换后文件信息的字典
          - error: 转换失败时的错误信息
        """
        try:        
            # 引入MarkItDown库
            from markitdown import MarkItDown
            md = MarkItDown()
            # 使用MarkItDown转换
            result = md.convert(original_path)
            
            # 创建新的Markdown文件名
            base_name = os.path.splitext(filename)[0]
            markdown_filename = f"{base_name}.md"
            markdown_path = os.path.join(markdown_dir, markdown_filename)
            
            # 写入转换后的内容
            with open(markdown_path, "w", encoding="utf-8") as f:
                f.write(result.text_content)
            
            # 如果启用智能分段，处理转换后的Markdown文件
            if smart_split_config and smart_split_config.get("enableSmartSplit", False):
                try:
                    split_result = FilesService.apply_smart_split_to_markdown(
                        markdown_path, 
                        smart_split_config,
                        project_id
                    )
                    if split_result["success"]:
                        return {
                            "success": True,
                            "files": split_result["files"],
                            "error": None
                        }
                    else:
                        # 智能分段失败，使用原转换文件
                        FilesService.update_markdown_registry(original_path, markdown_path, base_name, is_converted=True, project_id=project_id)
                        file_info = {
                            "original_filename": filename,
                            "markdown_filename": markdown_filename,
                            "path": markdown_path,
                            "size": os.stat(markdown_path).st_size,
                            "error": f"智能分段失败: {split_result.get('error')}"
                        }
                        return {
                            "success": True,
                            "file_info": file_info,
                            "error": None
                        }
                except Exception as e:
                    # 智能分段出错，使用原转换文件
                    FilesService.update_markdown_registry(original_path, markdown_path, base_name, is_converted=True, project_id=project_id)
                    file_info = {
                        "original_filename": filename,
                        "markdown_filename": markdown_filename,
                        "path": markdown_path,
                        "size": os.stat(markdown_path).st_size,
                        "error": f"智能分段失败: {str(e)}"
                    }
                    return {
                        "success": True,
                        "file_info": file_info,
                        "error": None
                    }
            else:
                # 不启用智能分段，直接返回转换结果
                file_info = {
                    "original_filename": filename,
                    "markdown_filename": markdown_filename,
                    "path": markdown_path,
                    "size": os.stat(markdown_path).st_size
                }
                
                # 更新markdown_manager.json
                FilesService.update_markdown_registry(original_path, markdown_path, base_name, is_converted=True, project_id=project_id)
                
                return {
                    "success": True,
                    "file_info": file_info,
                    "error": None
                }
            
        except Exception as e:
            print(f"转换文件 {filename} 失败: {str(e)}")
            return {
                "success": False,
                "file_info": None,
                "error": str(e)
            }
    
    @staticmethod
    def update_markdown_registry(original_path, markdown_path, title=None, is_converted=True, project_id=None):
        """
        更新markdown_manager.json记录
        
        参数:
        - original_path: 原始文件路径
        - markdown_path: Markdown文件路径
        - title: 文件标题，默认为None
        - is_converted: 是否是转换而来的，还是本来就是markdown文件
        - project_id: 项目ID
        """
        try:
            manager_path = get_project_output_path(project_id, "markdown_manager.json")
            relative_path = markdown_path.replace('\\', '/')
            
            # 创建记录
            file_record = {
                "filePath": relative_path,
                "originalPath": original_path.replace('\\', '/'),
                "timestamp": datetime.datetime.now().isoformat(),
                "isDataset": False,
                "isConverted": is_converted
            }
            
            if title:
                file_record["title"] = title
            
            # 读取或创建manager数据
            manager_data = []
            file_exists = os.path.exists(manager_path)
            
            if file_exists:
                try:
                    with open(manager_path, 'r', encoding='utf-8') as f:
                        manager_data = json.load(f)
                        if not isinstance(manager_data, list):
                            print(f"警告: {manager_path} 格式不正确，重置为空列表")
                            manager_data = []
                except json.JSONDecodeError:
                    print(f"警告: {manager_path} JSON解析错误，重置为空列表")
                    manager_data = []
            else:
                print(f"注意: {manager_path} 不存在，将创建新文件")
            
            # 检查文件是否已存在，避免重复
            found_existing = False
            for i, item in enumerate(manager_data):
                if (isinstance(item, dict) and 
                    item.get('filePath') == relative_path):
                    # 更新现有记录而不是添加新记录
                    manager_data[i] = file_record
                    found_existing = True
                    print(f"发现已存在记录，更新: {relative_path}")
                    break
            
            # 如果没有找到现有记录，添加新记录
            if not found_existing:
                manager_data.append(file_record)
                print(f"添加新记录: {relative_path}")
            
            # 保存更新后的manager数据
            with open(manager_path, 'w', encoding='utf-8') as f:
                json.dump(manager_data, f, ensure_ascii=False, indent=2)
            
            action = "更新" if file_exists else "创建"
            print(f"已{action} {manager_path} 文件")
            return True
        except Exception as e:
            print(f"更新markdown_manager.json时出错: {str(e)}")
            return False
    
    @staticmethod
    def delete_files(data: Dict[str, Any], project_id: Optional[str] = None) -> Dict[str, Any]:
        """删除指定的文件，同时更新markdown_manager.json和crawled_urls.json"""
        files = data.get("files", [])
        if not files:
            return {
                "status": "warning",
                "message": "没有指定要删除的文件"
            }
        
        manager_path = get_project_output_path(project_id, "markdown_manager.json")
        crawled_urls_path = get_project_output_path(project_id, "crawled_urls.json")
        deleted_files = []
        failed_files = []
        
        # 读取markdown_manager.json
        manager_data = []
        if os.path.exists(manager_path):
            try:
                with open(manager_path, 'r', encoding='utf-8') as f:
                    manager_data = json.load(f)
            except Exception as e:
                print(f"读取markdown_manager.json出错: {str(e)}")
                return {
                    "status": "error",
                    "message": f"读取文件记录失败: {str(e)}"
                }
        
        # 处理每个要删除的文件
        for filename in files:
            # 查找文件在manager中的记录
            file_entries = [item for item in manager_data if isinstance(item, dict) 
                           and 'filePath' in item 
                           and os.path.basename(item['filePath']) == filename]
            
            if file_entries:
                for entry in file_entries:
                    file_path = entry['filePath']
                    
                    # 标准化路径
                    if not os.path.isabs(file_path):
                        file_path = os.path.join(".", file_path)
                    
                    # 尝试删除物理文件
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            deleted_files.append(filename)
                        else:
                            # 文件不存在，但仍然从记录中删除
                            deleted_files.append(filename)
                    except Exception as e:
                        print(f"删除文件 {file_path} 失败: {str(e)}")
                        failed_files.append(filename)
            else:
                # 如果在manager中找不到，尝试在markdown目录下查找
                potential_paths = [
                    get_project_output_path(project_id, "markdown", filename),
                    os.path.join(".", get_project_output_path(project_id, "markdown", filename))
                ]
                
                deleted = False
                for path in potential_paths:
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                            deleted_files.append(filename)
                            deleted = True
                            break
                        except Exception as e:
                            print(f"删除文件 {path} 失败: {str(e)}")
                
                if not deleted:
                    failed_files.append(filename)
        
        # 从manager_data中移除已删除文件的记录
        if deleted_files:
            new_manager_data = [item for item in manager_data 
                               if not (isinstance(item, dict) 
                                      and 'filePath' in item 
                                      and os.path.basename(item['filePath']) in deleted_files)]
            
            # 保存更新后的manager_data
            if len(new_manager_data) != len(manager_data):
                with open(manager_path, 'w', encoding='utf-8') as f:
                    json.dump(new_manager_data, f, ensure_ascii=False, indent=2)
        
        # 更新crawled_urls.json中的filePath字段
        if deleted_files and os.path.exists(crawled_urls_path):
            try:
                with open(crawled_urls_path, 'r', encoding='utf-8') as f:
                    crawled_data = json.load(f)
                
                updated = False
                for item in crawled_data:
                    if isinstance(item, dict) and 'filePath' in item:
                        file_name = os.path.basename(item['filePath'])
                        if file_name in deleted_files:
                            # 将filePath设置为空
                            item['filePath'] = ''
                            updated = True
                
                # 只有在有更新时才保存文件
                if updated:
                    with open(crawled_urls_path, 'w', encoding='utf-8') as f:
                        json.dump(crawled_data, f, ensure_ascii=False, indent=2)
                    print(f"已更新 {crawled_urls_path} 中的文件路径")
            except Exception as e:
                print(f"更新crawled_urls.json时出错: {str(e)}")
        
        # 构建响应消息
        if deleted_files and not failed_files:
            return {
                "status": "success",
                "message": f"成功删除 {len(deleted_files)} 个文件",
                "deleted": deleted_files
            }
        elif deleted_files and failed_files:
            return {
                "status": "partial",
                "message": f"成功删除 {len(deleted_files)} 个文件，{len(failed_files)} 个文件删除失败",
                "deleted": deleted_files,
                "failed": failed_files
            }
        else:
            return {
                "status": "error",
                "message": f"所有 {len(failed_files)} 个文件删除失败",
                "failed": failed_files
            }
    
    @staticmethod
    def smart_split_content(content: str, max_tokens: int = 8000, min_tokens: int = 500, strategy: str = "balanced"):
        """
        智能分段功能，使用MarkdownSplitter根据配置将长文本分割成适合的段落
        
        参数:
        - content: 要分割的文本内容
        - max_tokens: 每段最大Token数
        - min_tokens: 每段最小Token数  
        - strategy: 分段策略 ('conservative', 'balanced', 'aggressive')
        
        返回:
        - List[Dict]: 分割后的文本段落对象列表，包含title、content、order等信息
        """
        try:
            # 根据分段策略调整参数
            actual_max_tokens = max_tokens
            actual_min_tokens = min_tokens
            
            if strategy == "conservative":
                actual_max_tokens = int(max_tokens * 1.2)  # 更大的分段
                actual_min_tokens = int(min_tokens * 1.5)
            elif strategy == "aggressive":
                actual_max_tokens = int(max_tokens * 0.8)  # 更小的分段
                actual_min_tokens = int(min_tokens * 0.7)
            
            # 创建智能分段器
            splitter = MarkdownSplitter(
                max_tokens=actual_max_tokens,
                min_tokens=actual_min_tokens
            )
            
            # 执行分段
            chunks = splitter.create_chunks(content)
            
            return chunks if chunks else []
            
        except Exception as e:
            print(f"智能分段失败: {str(e)}")
            # 分段失败时返回原始内容
            return [type('Chunk', (), {
                'order': 1,
                'title': '原始内容',
                'content': content
            })()]
    
    @staticmethod
    def apply_smart_split_to_markdown(markdown_path: str, smart_split_config: Dict[str, Any], project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        对Markdown文件应用智能分段，使用MarkdownSplitter
        
        参数:
        - markdown_path: Markdown文件路径
        - smart_split_config: 智能分段配置
        - project_id: 项目ID
        
        返回:
        - Dict: 包含分段结果的字典
        """
        try:
            # 读取原始文件内容
            with open(markdown_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 获取配置参数
            max_tokens = smart_split_config.get("maxTokens", 8000)
            min_tokens = smart_split_config.get("minTokens", 500)
            strategy = smart_split_config.get("splitStrategy", "balanced")
            
            print(f"对文件 {markdown_path} 启用智能分段 (策略: {strategy}, Token范围: {min_tokens}-{max_tokens})")
            
            # 应用智能分段
            chunks = FilesService.smart_split_content(content, max_tokens, min_tokens, strategy)
            
            if not chunks or len(chunks) <= 1:
                # 如果分段后只有一个块或没有分段，保持原文件
                original_filename = os.path.basename(markdown_path)
                base_name = os.path.splitext(original_filename)[0]
                FilesService.update_markdown_registry(markdown_path, markdown_path, base_name, is_converted=False, project_id=project_id)
                
                print(f"智能分段未产生多个分段，保持原文件: {markdown_path}")
                
                return {
                    "success": True,
                    "files": [{
                        "filename": original_filename,
                        "path": markdown_path,
                        "size": os.stat(markdown_path).st_size,
                        "converted": False,
                        "split_index": 0,
                        "total_splits": 1
                    }]
                }
            
            # 创建分段文件
            files = []
            base_name = os.path.splitext(os.path.basename(markdown_path))[0]
            markdown_dir = os.path.dirname(markdown_path)
            
            for chunk in chunks:
                # 创建分段文件名，与crawler_service保持一致：xxx-1.md, xxx-2.md
                split_filename = f"{base_name}-{chunk.order}.md"
                split_path = os.path.join(markdown_dir, split_filename)
                
                # 写入分段内容，格式与crawler_service保持一致
                chunk_content = f"# {chunk.title}\n\n{chunk.content}"
                with open(split_path, "w", encoding="utf-8") as f:
                    f.write(chunk_content)
                
                # 更新registry
                FilesService.update_markdown_registry(
                    markdown_path, 
                    split_path, 
                    f"{base_name} - 第{chunk.order}部分", 
                    is_converted=False, 
                    project_id=project_id
                )
                
                files.append({
                    "filename": split_filename,
                    "path": split_path,
                    "size": os.stat(split_path).st_size,
                    "converted": False,
                    "split_index": chunk.order,
                    "total_splits": len(chunks)
                })
            
            print(f"已保存智能分段内容: {len(chunks)} 个分段文件到 {markdown_dir}")
            
            # 删除原始文件
            os.remove(markdown_path)
            
            return {
                "success": True,
                "files": files
            }
            
        except Exception as e:
            print(f"智能分段失败 {markdown_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
