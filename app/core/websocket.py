from fastapi import WebSocket
from typing import Dict, List, Optional

class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 按项目ID存储活跃连接
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, project_id: str):
        """添加新的WebSocket连接"""
        await websocket.accept()
        if project_id not in self.active_connections:
            self.active_connections[project_id] = []
        self.active_connections[project_id].append(websocket)
        print(f"WebSocket连接已建立 - 项目ID: {project_id}, 当前连接数: {len(self.active_connections[project_id])}")
        
    def disconnect(self, websocket: WebSocket, project_id: str):
        """移除WebSocket连接"""
        if project_id in self.active_connections:
            try:
                self.active_connections[project_id].remove(websocket)
                print(f"WebSocket连接已断开 - 项目ID: {project_id}, 剩余连接数: {len(self.active_connections[project_id])}")
            except ValueError:
                pass
            
    async def send_json(self, message: dict, project_id: str):
        """向特定项目的所有连接发送JSON消息"""
        if project_id not in self.active_connections:
            print(f"WebSocket连接不存在 - 项目ID: {project_id}")
            # 打印一下self.active_connections内的所有项目ID
            print(f"当前连接的项目ID: {self.active_connections.keys()}")
            return
            
        disconnected_websockets = []
        for websocket in self.active_connections[project_id]:
            try:
                await websocket.send_json(message)
                print(f"发送WebSocket消息成功 - 项目ID: {project_id}")
            except Exception as e:
                print(f"发送WebSocket消息失败: {str(e)}")
                disconnected_websockets.append(websocket)
                
        # 移除断开的连接
        for websocket in disconnected_websockets:
            self.disconnect(websocket, project_id)
            
    async def broadcast_json(self, message: dict):
        """向所有连接发送广播消息"""
        for project_id in self.active_connections:
            await self.send_json(message, project_id)

# 全局连接管理器实例
manager = ConnectionManager() 