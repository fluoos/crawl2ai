import uuid
from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass
from enum import Enum
from app.services.system_service import SystemService


class NotificationType(Enum):
    """通知类型枚举"""
    CONVERT_PROGRESS = "html_to_md_convert_progress"
    CRAWL_PROGRESS = "crawl_progress"
    TASK_STATUS = "task_status"


class NotificationStatus(Enum):
    """通知状态枚举"""
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ConvertProgressData:
    """转换进度通知数据"""
    progress: int
    total: int
    processed: int
    successful: int
    message: str
    url: Optional[str] = None
    success: Optional[bool] = None
    error: Optional[str] = None


@dataclass
class CrawlProgressData:
    """爬取进度通知数据"""
    progress: int
    total: int
    processed: int
    message: str
    current_url: Optional[str] = None
    depth: Optional[int] = None


class NotificationService:
    """统一的通知服务类"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.task_id = str(uuid.uuid4())
    
    async def send_convert_notification(
        self,
        status: NotificationStatus,
        data: ConvertProgressData
    ) -> bool:
        """发送转换进度通知"""
        notification_data = {
            "task_id": self.task_id,
            "type": NotificationType.CONVERT_PROGRESS.value,
            "status": status.value,
            "progress": data.progress,
            "total": data.total,
            "processed": data.processed,
            "successful": data.successful,
            "message": data.message
        }
        
        # 添加可选字段
        if data.url:
            notification_data["url"] = data.url
        if data.success is not None:
            notification_data["success"] = data.success
        if data.error:
            notification_data["error"] = data.error
            
        return await self._send_notification(notification_data)
    
    async def send_crawl_notification(
        self,
        status: NotificationStatus,
        data: CrawlProgressData
    ) -> bool:
        """发送爬取进度通知"""
        notification_data = {
            "task_id": self.task_id,
            "type": NotificationType.CRAWL_PROGRESS.value,
            "status": status.value,
            "progress": data.progress,
            "total": data.total,
            "processed": data.processed,
            "message": data.message
        }
        
        # 添加可选字段
        if data.current_url:
            notification_data["current_url"] = data.current_url
        if data.depth is not None:
            notification_data["depth"] = data.depth
            
        return await self._send_notification(notification_data)
    
    async def send_task_status(
        self,
        status: NotificationStatus,
        message: str,
        **extra_data
    ) -> bool:
        """发送任务状态通知"""
        notification_data = {
            "task_id": self.task_id,
            "type": NotificationType.TASK_STATUS.value,
            "status": status.value,
            "message": message,
            **extra_data
        }
        
        return await self._send_notification(notification_data)
    
    async def _send_notification(self, data: Dict[str, Any]) -> bool:
        """内部方法：发送通知到WebSocket"""
        try:
            print(f"发送通知: {data['type']} - {data['status']}")
            success = await SystemService.send_to_websocket_async(data, self.project_id)
            if not success:
                print(f"通知发送失败: {data}")
            return success
        except Exception as e:
            print(f"发送通知时发生异常: {e}")
            return False
    
    def get_task_id(self) -> str:
        """获取当前任务ID"""
        return self.task_id
    
    def new_task(self) -> str:
        """生成新的任务ID"""
        self.task_id = str(uuid.uuid4())
        return self.task_id


class NotificationManager:
    """通知管理器，管理多个项目的通知服务"""
    
    _instances: Dict[str, NotificationService] = {}
    
    @classmethod
    def get_service(cls, project_id: str) -> NotificationService:
        """获取指定项目的通知服务实例"""
        if project_id not in cls._instances:
            cls._instances[project_id] = NotificationService(project_id)
        return cls._instances[project_id]
    
    @classmethod
    def create_new_task(cls, project_id: str) -> NotificationService:
        """为项目创建新任务的通知服务"""
        service = cls.get_service(project_id)
        service.new_task()
        return service
    
    @classmethod
    def remove_service(cls, project_id: str):
        """移除项目的通知服务"""
        if project_id in cls._instances:
            del cls._instances[project_id]


# 便捷函数
async def send_convert_start(project_id: str, total_urls: int) -> NotificationService:
    """发送转换开始通知"""
    service = NotificationManager.create_new_task(project_id)
    await service.send_convert_notification(
        NotificationStatus.STARTED,
        ConvertProgressData(
            progress=0,
            total=total_urls,
            processed=0,
            successful=0,
            message="开始转换URL为Markdown"
        )
    )
    return service


async def send_convert_progress(
    service: NotificationService,
    processed: int,
    successful: int,
    total: int,
    message: str,
    url: Optional[str] = None,
    success: Optional[bool] = None,
    error: Optional[str] = None
):
    """发送转换进度通知"""
    progress = int(processed / total * 100) if total > 0 else 0
    await service.send_convert_notification(
        NotificationStatus.PROCESSING,
        ConvertProgressData(
            progress=progress,
            total=total,
            processed=processed,
            successful=successful,
            message=message,
            url=url,
            success=success,
            error=error
        )
    )


async def send_convert_complete(
    service: NotificationService,
    processed: int,
    successful: int,
    total: int
):
    """发送转换完成通知"""
    await service.send_convert_notification(
        NotificationStatus.COMPLETED,
        ConvertProgressData(
            progress=100,
            total=total,
            processed=processed,
            successful=successful,
            message=f"转换完成，共处理{processed}个URL，成功{successful}个"
        )
    )


async def send_convert_failed(
    service: NotificationService,
    processed: int,
    successful: int,
    total: int,
    error: str
):
    """发送转换失败通知"""
    progress = int(processed / total * 100) if total > 0 else 0
    await service.send_convert_notification(
        NotificationStatus.FAILED,
        ConvertProgressData(
            progress=progress,
            total=total,
            processed=processed,
            successful=successful,
            message=f"转换任务失败: {error}",
            error=error
        )
    )


# 爬取相关的便捷函数
async def send_crawl_start(project_id: str, start_url: str, strategy: str) -> NotificationService:
    """发送爬取开始通知"""
    service = NotificationManager.create_new_task(project_id)
    await service.send_crawl_notification(
        NotificationStatus.STARTED,
        CrawlProgressData(
            progress=0,
            total=0,  # 开始时不知道总数
            processed=0,
            message=f"开始爬取 {start_url}，使用{strategy}策略"
        )
    )
    return service


async def send_crawl_progress(
    service: NotificationService,
    processed: int,
    total: int,
    message: str,
    current_url: Optional[str] = None,
    depth: Optional[int] = None
):
    """发送爬取进度通知"""
    progress = int(processed / total * 100) if total > 0 else 0
    await service.send_crawl_notification(
        NotificationStatus.PROCESSING,
        CrawlProgressData(
            progress=progress,
            total=total,
            processed=processed,
            message=message,
            current_url=current_url,
            depth=depth
        )
    )


async def send_crawl_complete(
    service: NotificationService,
    processed: int,
    total: int
):
    """发送爬取完成通知"""
    await service.send_crawl_notification(
        NotificationStatus.COMPLETED,
        CrawlProgressData(
            progress=100,
            total=total,
            processed=processed,
            message=f"爬取完成，共发现{total}个URL"
        )
    )


async def send_crawl_failed(
    service: NotificationService,
    processed: int,
    total: int,
    error: str
):
    """发送爬取失败通知"""
    progress = int(processed / total * 100) if total > 0 else 0
    await service.send_crawl_notification(
        NotificationStatus.FAILED,
        CrawlProgressData(
            progress=progress,
            total=total,
            processed=processed,
            message=f"爬取任务失败: {error}"
        )
    ) 