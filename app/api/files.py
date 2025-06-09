from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Depends
from fastapi.responses import JSONResponse
from typing import List, Dict, Any, Optional
import os
from app.services.files_service import FilesService
from app.core.deps import get_api_key, get_project_id
from app.schemas.files import FileDeleteRequest
router = APIRouter()

@router.get("")
async def get_file_list(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    project_id: Optional[str] = Depends(get_project_id)
):
    """获取文件列表"""
    print(f"获取文件列表: {project_id}")
    try:
        return FilesService.get_file_list(page, pageSize, project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/preview")
async def preview_file(
    path: str = Query(...),
    project_id: Optional[str] = Depends(get_project_id)
):
    """预览Markdown文件内容"""
    try:
        return FilesService.preview_file(path, project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览文件失败: {str(e)}")

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    project_id: Optional[str] = Form(None, alias="projectId"),
    enableSmartSplit: Optional[bool] = Form(False),
    maxTokens: Optional[int] = Form(8000),
    minTokens: Optional[int] = Form(500),
    splitStrategy: Optional[str] = Form("balanced")
):
    """上传文件，非Markdown文件会被自动转换，支持智能分段"""
    try:
        smart_split_config = None
        if enableSmartSplit:
            smart_split_config = {
                "enableSmartSplit": enableSmartSplit,
                "maxTokens": maxTokens,
                "minTokens": minTokens,
                "splitStrategy": splitStrategy
            }
        
        return FilesService.upload_files(files, project_id, smart_split_config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete-file")
async def delete_files(
    request: FileDeleteRequest
):
    """删除指定的文件，同时更新markdown_manager.json和crawled_urls.json"""
    try:
        data = {"files": request.files}
        return FilesService.delete_files(data, request.project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}") 
    
