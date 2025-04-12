from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import os
from app.services.files_service import FilesService

router = APIRouter()

@router.get("")
async def get_file_list(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100)
):
    """获取文件列表"""
    try:
        return FilesService.get_file_list(page, pageSize)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/preview")
async def preview_file(path: str = Query(...)):
    """预览Markdown文件内容"""
    try:
        return FilesService.preview_file(path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览文件失败: {str(e)}")

@router.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """上传文件，非Markdown文件会被自动转换"""
    try:
        return FilesService.upload_files(files)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete-file")
async def delete_files(data: Dict[str, Any]):
    """删除指定的文件，同时更新markdown_manager.json和crawled_urls.json"""
    try:
        return FilesService.delete_files(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}") 
    
