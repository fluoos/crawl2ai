from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import os
import datetime
import shutil
import json

router = APIRouter()

@router.get("")
async def get_file_list(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100)
):
    """获取文件列表"""
    try:
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
        start_idx = (page - 1) * pageSize
        end_idx = min(start_idx + pageSize, total)
        
        # 返回分页结果
        return {
            "files": all_files[start_idx:end_idx],
            "total": total,
            "page": page,
            "pageSize": pageSize
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/preview")
async def preview_file(path: str = Query(...)):
    """预览Markdown文件内容"""
    try:
        # 安全检查：确保path是有效的，防止目录遍历攻击
        if ".." in path or "~" in path:
            raise HTTPException(status_code=400, detail="无效的文件路径")
        
        # 标准化路径，确保使用正确的分隔符
        file_path = path.replace('/', os.sep).replace('\\', os.sep)
        
        # 如果是相对路径且不以"."开头，添加"./"
        if not os.path.isabs(file_path) and not file_path.startswith("."):
            file_path = os.path.join(".", file_path)
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件 '{path}' 不存在")
        
        # 检查是否为文件而非目录
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=400, detail=f"'{path}' 不是一个文件")
        
        # 检查文件大小，避免加载过大的文件
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB限制
            raise HTTPException(status_code=400, detail="文件过大，无法预览")
        
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
            raise HTTPException(status_code=400, detail="文件编码错误，无法预览")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览文件失败: {str(e)}")

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """上传文件"""
    try:
        upload_dir = "upload"
        os.makedirs(upload_dir, exist_ok=True)
        
        uploaded_files = []
        
        for file in files:
            # 确保文件是Markdown格式
            if not file.filename.endswith(".md"):
                return JSONResponse(
                    status_code=400,
                    content={"detail": f"文件 {file.filename} 不是Markdown格式"}
                )
            
            file_path = os.path.join(upload_dir, file.filename)
            
            # 保存文件
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            
            uploaded_files.append({
                "filename": file.filename,
                "path": file_path,
                "size": os.stat(file_path).st_size
            })
        # TODO 将上传的文件转换为markdown文件
        # 使用进程来执行转换任务
        
        return {
            "status": "success",
            "message": f"成功上传 {len(uploaded_files)} 个文件",
            "files": uploaded_files
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 删除文件接口
@router.post("/delete-file")
async def delete_files(data: Dict[str, Any]):
    """删除指定的文件，同时更新markdown_manager.json和crawled_urls.json"""
    try:
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
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}") 