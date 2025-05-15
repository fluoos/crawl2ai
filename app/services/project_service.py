# app/services/project_service.py
import os
import json
import logging
import uuid
import base64
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.dataset_service import DatasetService

# 项目数据存储路径
PROJECTS_FILE = os.path.join(settings.OUTPUT_DIR, "projects.json")

class ProjectService:
    """项目服务类，处理所有与项目相关的业务逻辑"""
    @staticmethod
    def ensure_project_structure():
        """确保项目结构存在"""        
        if not os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False)

    @staticmethod
    def generate_short_id(length=12):
        """生成短ID"""
        # 生成UUID并移除短横线
        uid = uuid.uuid4().hex
        # 返回前N位字符
        return uid[:length]

    @staticmethod
    def create_project(project: ProjectCreate) -> Dict[str, Any]:
        """创建新项目"""   
        ProjectService.ensure_project_structure()     
        # 读取现有项目列表
        projects = []
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            try:
                projects = json.load(f)
            except json.JSONDecodeError:
                projects = []
        
        # 检查项目名称是否已存在
        for existing_project in projects:
            if existing_project.get("name") == project.name:
                return {"status": "error", "message": "项目名称已存在，请使用其他名称", "data": None}
        
        # 生成新项目ID - 使用短ID
        project_id = ProjectService.generate_short_id()
        
        # 确保ID不重复
        existing_ids = set(p.get("id") for p in projects if p.get("id"))
        while project_id in existing_ids:
            project_id = ProjectService.generate_short_id()
        
        # 创建项目目录，后续项目相关的文件都存储在这个目录下
        project_dir = os.path.join(settings.OUTPUT_DIR, str(project_id))
        os.makedirs(project_dir, exist_ok=True)
        
        # 添加新项目
        now = datetime.now().isoformat()
        new_project = {
            "id": project_id,
            "name": project.name,
            "description": project.description,
            "created_at": now,
            "updated_at": now,
            "dataset_count": 0
        }
        
        projects.append(new_project)
        
        # 保存项目列表
        with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
        
        return {"status": "success", "message": "项目创建成功", "data": ProjectResponse(**new_project) }
    
    @staticmethod
    def list_projects() -> List[ProjectResponse]:
        """获取项目列表"""
        ProjectService.ensure_project_structure()
        
        # 读取项目列表
        projects = []
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            try:
                projects = json.load(f)
            except json.JSONDecodeError:
                projects = []
        
        for project in projects:
            project["dataset_count"] = DatasetService.get_project_dataset_count(project["id"])
        
        return {"status": "success", "message": "项目创建成功", "data": [ProjectResponse(**p) for p in projects] }
    
    @staticmethod
    def get_project(project_id: int) -> Optional[ProjectResponse]:
        """获取项目详情"""
        ProjectService.ensure_project_structure()
        
        # 读取项目列表
        projects = []
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            try:
                projects = json.load(f)
            except json.JSONDecodeError:
                projects = []
        
        # 查找项目
        for project in projects:
            if project.get("id") == project_id:
                return {"status": "success", "message": "项目详情", "data": ProjectResponse(**project) }
        
        return {"status": "success", "message": "项目详情", "data": {} }
    
    @staticmethod
    def update_project(project_id: str, project_update: ProjectUpdate) -> Optional[ProjectResponse]:
        """更新项目信息"""
        ProjectService.ensure_project_structure()
        
        # 读取项目列表
        projects = []
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            try:
                projects = json.load(f)
            except json.JSONDecodeError:
                projects = []
        
        # 检查新名称是否与其他项目重复
        for existing_project in projects:
            if (existing_project.get("id") != project_id and 
                existing_project.get("name") == project_update.name):
                return {"status": "error", "message": "项目名称已存在，请使用其他名称", "data": None}
        
        # 查找并更新项目
        for i, project in enumerate(projects):
            if project.get("id") == project_id:
                projects[i]["name"] = project_update.name
                projects[i]["description"] = project_update.description
                projects[i]["updated_at"] = datetime.now().isoformat()
                
                # 保存项目列表
                with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
                    json.dump(projects, f, ensure_ascii=False, indent=2)
                
                return {"status": "success", "message": "项目更新成功", "data": ProjectResponse(**projects[i]) }
        
        return {"status": "error", "message": "该项目不存在", "data": {} }
    
    @staticmethod
    def delete_project(project_id: str) -> Dict[str, Any]:
        """删除项目"""
        ProjectService.ensure_project_structure()
        
        # 读取项目列表
        projects = []
        with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
            try:
                projects = json.load(f)
            except json.JSONDecodeError:
                projects = []
        
        # 查找项目
        found = False
        for i, project in enumerate(projects):
            if project.get("id") == project_id:
                projects.pop(i)
                found = True
                break
        
        if not found:
            return {"status": "error", "message": "该项目不存在", "data": {} }
        
        # 保存项目列表
        with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
            json.dump(projects, f, ensure_ascii=False, indent=2)
        
        # 删除项目目录及其数据集
        project_dir = os.path.join(settings.OUTPUT_DIR, str(project_id))
        if os.path.exists(project_dir):
            import shutil
            shutil.rmtree(project_dir)
        
        return {"status": "success", "message": "项目删除成功", "data": {} }
    