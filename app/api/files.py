from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import datetime
import shutil

router = APIRouter()

@router.get("")
async def get_file_list(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100)
):
    """获取文件列表"""
    try:
        output_dir = "output/markdown"
        
        # 确保目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        all_files = []
        
        # 获取输出目录中的Markdown文件
        for filename in os.listdir(output_dir):
            if filename.endswith(".md"):
                file_path = os.path.join(output_dir, filename)
                stats = os.stat(file_path)
                all_files.append({
                    "filename": filename,
                    "path": file_path,
                    "size": stats.st_size,
                    "modifiedTime": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "directory": "output"
                })
        
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