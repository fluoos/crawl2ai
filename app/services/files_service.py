import os
import shutil
import json
import datetime
from typing import List, Dict, Any

class FilesService:
    """文件服务类，处理所有与文件相关的业务逻辑"""
    
    @staticmethod
    def get_file_list(page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """获取文件列表"""
        # 读取markdown_manager.json文件
        manager_path = os.path.join("output", "markdown_manager.json")
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
                
        # 按修改时间降序排序
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
    def preview_file(path: str) -> Dict[str, Any]:
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
    def upload_files(files: List[Any]) -> Dict[str, Any]:
        """上传文件，非Markdown文件会被自动转换"""
        # 确保目录存在
        upload_dir = "upload"
        markdown_dir = os.path.join("output", "markdown")
        os.makedirs(upload_dir, exist_ok=True)
        os.makedirs(markdown_dir, exist_ok=True)
        
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
                
                # 更新markdown_manager.json
                base_name = os.path.splitext(file.filename)[0]
                FilesService.update_markdown_registry(original_path, markdown_path, base_name, is_converted=False)
                
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
                    filename=file.filename
                )
                
                if conversion_result["success"]:
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
    def convert_to_markdown(original_path: str, markdown_dir: str, filename: str) -> Dict[str, Any]:
        """
        将非Markdown文件转换为Markdown格式
        
        参数:
        - original_path: 原始文件的完整路径
        - markdown_dir: Markdown文件的存储目录
        - filename: 原始文件名
        
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
            
            # 构建文件信息
            file_info = {
                "original_filename": filename,
                "markdown_filename": markdown_filename,
                "path": markdown_path,
                "size": os.stat(markdown_path).st_size
            }
            
            # 更新markdown_manager.json
            FilesService.update_markdown_registry(original_path, markdown_path, base_name, is_converted=True)
            
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
    def update_markdown_registry(original_path, markdown_path, title=None, is_converted=True):
        """
        更新markdown_manager.json记录
        
        参数:
        - original_path: 原始文件路径
        - markdown_path: Markdown文件路径
        - title: 文件标题，默认为None
        - is_converted: 是否是转换而来的，还是本来就是markdown文件
        """
        try:
            manager_path = os.path.join("output", "markdown_manager.json")
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
            
            # 确保目录存在
            os.makedirs("output", exist_ok=True)
            
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
    def delete_files(data: Dict[str, Any]) -> Dict[str, Any]:
        """删除指定的文件，同时更新markdown_manager.json和crawled_urls.json"""
        files = data.get("files", [])
        if not files:
            return {
                "status": "warning",
                "message": "没有指定要删除的文件"
            }
        
        manager_path = os.path.join("output", "markdown_manager.json")
        crawled_urls_path = os.path.join("output", "crawled_urls.json")
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
                    os.path.join("output", "markdown", filename),
                    os.path.join(".", "output", "markdown", filename)
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
