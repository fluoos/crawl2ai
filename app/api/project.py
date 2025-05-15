# app/api/project.py
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional

from app.core.deps import get_api_key
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDatasetRequest
from app.services.project_service import ProjectService

router = APIRouter()

@router.post("/create")
async def create_project(
    project: ProjectCreate,
    api_key: str = Depends(get_api_key)
):
    """创建新项目"""
    try:
        return ProjectService.create_project(project)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_projects(
    api_key: str = Depends(get_api_key)
):
    """获取项目列表"""
    try:
        return ProjectService.list_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}")
async def get_project(
    project_id: str,
    api_key: str = Depends(get_api_key)
):
    """获取项目详情"""
    try:
        project = ProjectService.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}")
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    api_key: str = Depends(get_api_key)
):
    """更新项目信息"""
    try:
        project = ProjectService.update_project(project_id, project_update)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    api_key: str = Depends(get_api_key)
):
    """删除项目"""
    try:
        success = ProjectService.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail="项目不存在")
        return {"status": "success", "message": "项目已成功删除"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        