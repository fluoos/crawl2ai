from fastapi import Depends, HTTPException, status, Header, Query, Body
from typing import Optional, Union
from app.core.config import settings

async def get_api_key(api_key: Optional[str] = Header(None, alias="Authorization")):
    """
    验证并返回API密钥
    """
    # 如果配置中不需要API密钥验证，则直接返回
    if not settings.API_KEY_REQUIRED:
        return None
    
    # 检查API密钥是否存在
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少API密钥",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Bearer 前缀处理
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    # 验证API密钥是否有效
    if api_key != settings.DEEPSEEK_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API密钥无效",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key

async def get_project_id(
    project_id_query: Optional[str] = Query(None, alias="projectId"),
    body: Optional[dict] = Body(None)
) -> Optional[str]:
    """
    统一获取请求中的项目ID
    
    优先从查询参数中获取，其次从请求体中获取
    """
    # 首先从查询参数获取
    if project_id_query:
        return project_id_query
    
    # 然后从请求体获取
    if body and "projectId" in body:
        return body["projectId"]
    
    # 可选：如果项目ID是必需的，可以在这里抛出异常
    # 如果不是必需的，可以返回None
    # raise HTTPException(
    #     status_code=status.HTTP_400_BAD_REQUEST,
    #     detail="缺少项目ID参数",
    # )
    
    return None 