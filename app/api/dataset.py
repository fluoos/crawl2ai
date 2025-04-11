from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse, JSONResponse
import os
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.core.deps import get_api_key
from app.schemas.dataset import DeleteItemsRequest, DatasetListRequest, DatasetExportRequest
from app.services.dataset_service import DatasetService, EXPORT_FORMATS, DATASET_STYLES, INPUT_FILE

router = APIRouter()

# 确保数据目录和初始文件存在
DatasetService.ensure_output_file_exists()

@router.get("/formats")
async def get_formats(api_key: str = Depends(get_api_key)):
    """获取支持的文件格式和数据集风格"""
    try:
        return DatasetService.get_formats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/examples")
async def get_format_examples(api_key: str = Depends(get_api_key)):
    """获取各种格式的示例"""
    try:
        return DatasetService.get_format_examples()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(api_key: str = Depends(get_api_key)):
    """获取数据集统计信息"""
    try:
        return DatasetService.get_stats()
    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/list")
async def list_data(
    params: DatasetListRequest,
    api_key: str = Depends(get_api_key)
):
    """预览数据转换结果"""
    try:
        return DatasetService.list_data(
            format_type=params.format,
            style=params.style,
            input_file=params.inputFile,
            template=params.template,
            page=params.page,
            page_size=params.pageSize
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"预览数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_data(
    options: DatasetExportRequest,
    api_key: str = Depends(get_api_key)
):
    """导出数据集"""
    try:
        return DatasetService.export_data(
            format_type=options.format,
            style=options.style,
            input_file=options.inputFile,
            output_file=options.outputFile,
            template=options.template
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"导出数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{style}/{filename}")
async def download_file(style: str, filename: str):
    """下载导出的文件"""
    try:
        file_path = DatasetService.get_download_file_path(style, filename)
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete", response_model=Dict[str, Any])
async def delete_items(
    request: DeleteItemsRequest,
    api_key: str = Depends(get_api_key)
):
    """删除指定的问答对"""
    try:
        return DatasetService.delete_items(request.ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 