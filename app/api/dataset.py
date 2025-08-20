from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import FileResponse
import os
from typing import Dict, Any, List, Optional

import os
import logging
from app.core.config import settings
from app.core.deps import get_api_key, get_project_id
from app.schemas.dataset import DeleteItemsRequest, DatasetListRequest, DatasetExportRequest, AddQAItemRequest, UpdateQAItemRequest
from app.services.dataset_service import DatasetService, EXPORT_FORMATS, DATASET_STYLES, INPUT_FILE

router = APIRouter()

@router.get("/formats")
async def get_formats(
    api_key: str = Depends(get_api_key),
    project_id: Optional[str] = Depends(get_project_id)
):
    """获取支持的文件格式和数据集风格"""
    try:
        return DatasetService.get_formats(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/examples")
async def get_format_examples(
    api_key: str = Depends(get_api_key),
    project_id: Optional[str] = Depends(get_project_id)
):
    """获取各种格式的示例"""
    try:
        return DatasetService.get_format_examples(project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(
    api_key: str = Depends(get_api_key),
    project_id: Optional[str] = Depends(get_project_id)
):
    """获取数据集统计信息"""
    try:
        return DatasetService.get_stats(project_id=project_id)
    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_data(
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    api_key: str = Depends(get_api_key),
    project_id: Optional[str] = Depends(get_project_id)
):
    """预览数据转换结果"""
    try:
        return DatasetService.list_data(
            page=page,
            page_size=pageSize,
            project_id=project_id
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
    project_id = options.projectId
    
    try:
        return DatasetService.export_data(
            format_type=options.format,
            style=options.style,
            input_file=options.inputFile,
            output_file=options.outputFile,
            template=options.template,
            project_id=project_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"导出数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{style}/{filename}")
async def download_file(
    style: str, 
    filename: str,
    api_key: str = Depends(get_api_key),
    project_id: Optional[str] = Depends(get_project_id)
):
    """下载导出的文件"""
    try:
        file_path = DatasetService.get_download_file_path(style, filename, project_id)
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
    project_id = request.projectId
    
    try:
        return DatasetService.delete_items(request.ids, project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
async def add_qa_item(
    params: AddQAItemRequest,
    api_key: str = Depends(get_api_key)
):
    """添加问答对到数据集"""
    project_id = params.projectId
    
    print(f"添加问答对: {params}")
    try:
        return DatasetService.add_qa_item(
            question=params.question,
            answer=params.answer,
            chain_of_thought=params.chainOfThought,
            label=params.label,
            project_id=project_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"添加问答对失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update")
async def update_qa_item(
    params: UpdateQAItemRequest,
    api_key: str = Depends(get_api_key)
):
    """编辑数据集中的问答对"""
    project_id = params.projectId
    
    print(f"编辑问答对: {params}")
    try:
        return DatasetService.update_qa_item(
            id=params.id,
            question=params.question,
            answer=params.answer,
            chain_of_thought=params.chainOfThought,
            label=params.label,
            project_id=project_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"编辑问答对失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/convert")
async def convert_to_dataset(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key)
):
    """将Markdown文件转换为数据集"""
    # 从请求体中获取 projectId
    project_id = data.get("projectId")
    print(f"project_id: {project_id}")
    
    files = data.get("files", [])
    output_file = data.get("output_file", "qa_dataset.jsonl")
    
    if not files:
        raise HTTPException(status_code=400, detail="文件列表不能为空")
    
    # 先检查是否有可用的API密钥
    api_key_check = DatasetService.check_available_api_key()
    if not api_key_check["available"]:
        raise HTTPException(
            status_code=400, 
            detail=api_key_check["message"]
        )
    
    try:
        # 启动转换任务
        result = DatasetService.save_conversion_task_status(files, output_file, project_id)
        # 在后台执行转换任务，传入 api_key
        background_tasks.add_task(
            DatasetService.convert_files_to_dataset_task, 
            files, 
            output_file,
            project_id
        )
        
        # 在返回结果中包含API密钥检查信息
        result["api_key_info"] = api_key_check
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"启动转换任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/convert/status/{output_file}")
async def get_conversion_status(
    output_file: str,
    project_id: Optional[str] = Depends(get_project_id)
):
    """获取转换任务的状态"""
    try:
        return DatasetService.get_conversion_state(output_file, project_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 