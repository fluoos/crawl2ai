from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any
import os

from app.schemas.export import ExportRequest, ExportResponse, PreviewRequest, PreviewResponse
from app.services.export_service import export_dataset, preview_dataset
from app.api.deps import get_api_key

router = APIRouter()

@router.post("/preview", response_model=PreviewResponse)
async def preview_export(
    request: PreviewRequest,
    api_key: str = Depends(get_api_key)
):
    """预览导出结果"""
    try:
        sample_data = preview_dataset(
            format=request.format,
            style=request.style,
            input_file=request.input_file,
            mapping=request.mapping
        )
        
        return {
            "status": "success",
            "message": "预览生成成功",
            "sample": sample_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览生成失败: {str(e)}")

@router.post("/export", response_model=ExportResponse)
async def export_to_file(
    request: ExportRequest,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """导出数据集到文件"""
    try:
        # 检查格式和风格是否支持
        if request.format not in ["jsonl", "json"]:
            raise HTTPException(status_code=400, detail="不支持的导出格式，请使用jsonl或json")
            
        if request.style not in ["alpaca", "sharegpt", "custom"]:
            raise HTTPException(status_code=400, detail="不支持的数据集风格，请使用alpaca、sharegpt或custom")
            
        # 如果是自定义格式，检查mapping是否提供
        if request.style == "custom" and not request.mapping:
            raise HTTPException(status_code=400, detail="自定义风格需要提供字段映射")
        
        # 使用后台任务进行导出
        background_tasks.add_task(
            export_dataset,
            format=request.format,
            style=request.style,
            input_file=request.input_file,
            output_file=request.output_file,
            mapping=request.mapping
        )
        
        return {
            "status": "success",
            "message": "导出任务已开始，请稍后下载",
            "output_file": request.output_file
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出任务创建失败: {str(e)}")

@router.get("/files", response_model=Dict[str, List[str]])
async def list_export_files(api_key: str = Depends(get_api_key)):
    """列出所有导出文件"""
    try:
        export_files = {}
        
        # 列出各个导出目录中的文件
        for style in ["alpaca", "sharegpt", "custom"]:
            dir_path = f"export/{style}"
            if os.path.exists(dir_path):
                export_files[style] = [
                    f for f in os.listdir(dir_path) 
                    if os.path.isfile(os.path.join(dir_path, f))
                ]
            else:
                export_files[style] = []
                
        return export_files
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取导出文件列表失败: {str(e)}") 