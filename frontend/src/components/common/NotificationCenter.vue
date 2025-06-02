<template>
  <div class="notification-center">
    <!-- 通知图标 -->
    <a-badge :count="notifications.length" :dot="notifications.length > 0" :offset="[-4, 4]">
      <a-button
        class="notification-icon-btn" 
        type="text" 
        shape="circle" 
        @click="showDrawer"
        :class="{ 'notification-btn-active': drawerVisible }"
      >
        <BellOutlined style="font-size: 18px;" />
      </a-button>
    </a-badge>
    
    <!-- 通知抽屉 -->
    <a-drawer
      title="实时通知"
      :width="420"
      :visible="drawerVisible"
      @close="closeDrawer"
      placement="right"
    >
      <div v-if="notifications.length === 0" class="empty-notification">
        <a-empty description="暂无通知，当前任务通知，刷新会被清空" />
      </div>
      
      <div v-else class="notification-list">
        <!-- 通知分组 -->
        <div v-for="(item, index) in notificationArr" :key="index" class="notification-group">
          <div class="notification-group-header">
            <span class="notification-title">{{ item.title }}</span>
            <a-tag :color="getStatusColor(item.status)">{{ getStatusText(item.status) }}</a-tag>
          </div>
          
          <!-- 进度条 -->
          <a-progress 
            :percent="item.progress" 
            :status="getProgressStatus(item.status)" 
            size="small"
          />
          
          <!-- 统计信息 -->
          <div class="notification-stats">
            <span>总计：{{ item.total }}</span>
            <span>处理：{{ item.processed }}</span>
            <span>成功：{{ item.successful }}</span>
          </div>
          
          <!-- 最新消息 -->
          <div class="notification-message">
            {{ item.latestMessage }}
          </div>
          
          <a-divider v-if="index < notificationArr.length - 1" />
        </div>
      </div>
      
      <div class="notification-actions">
        <a-button @click="clearNotifications" danger>清空通知</a-button>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, h } from 'vue';
import { BellOutlined, LoadingOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons-vue';
import { notification } from 'ant-design-vue';
import wsService from '../../services/websocket';

// 抽屉可见性
const drawerVisible = ref(false);
// 通知列表
const notifications = ref([]);
// 通知分组
const notificationArr = computed(() => {
  return notifications.value.map(notification => {
    // 计算正确的百分比进度
    const progressPercent = notification.total > 0 ? Math.round((notification.processed / notification.total) * 100) : 0;
    
    return {
      task_id: notification.task_id,
      type: notification.type,
      title: getNotificationTitle(notification),
      status: notification.status,
      progress: progressPercent, // 使用计算后的百分比
      total: notification.total || 0,
      processed: notification.processed || 0,
      successful: notification.successful || 0,
      latestMessage: notification.message || '',
      timestamp: notification.timestamp
    }
  }).sort((a, b) => b.timestamp - a.timestamp)
});

// 用于跟踪活动的通知
const activeNotifications = ref({});

// 获取通知标题
const getNotificationTitle = (notification) => {
  if (notification.type === 'html_to_md_convert_progress') {
    return 'URL转换为Markdown';
  }
  if (notification.type === 'md_to_dataset_convert_progress') {
    return 'Markdown转换为数据集';
  }
  return '系统通知';
};

// 获取状态颜色
const getStatusColor = (status) => {
  switch (status) {
    case 'started':
      return 'blue';
    case 'processing':
      return 'processing';
    case 'completed':
      return 'success';
    case 'failed':
      return 'error';
    default:
      return 'default';
  }
};

// 获取状态文本
const getStatusText = (status) => {
  switch (status) {
    case 'started':
      return '开始';
    case 'processing':
      return '进行中';
    case 'completed':
      return '已完成';
    case 'failed':
      return '失败';
    default:
      return '未知';
  }
};

// 获取进度条状态
const getProgressStatus = (status) => {
  switch (status) {
    case 'completed':
      return 'success';
    case 'failed':
      return 'exception';
    default:
      return 'active';
  }
};

// 显示抽屉
const showDrawer = () => {
  drawerVisible.value = true;
};

// 关闭抽屉
const closeDrawer = () => {
  drawerVisible.value = false;
};

// 清空通知
const clearNotifications = () => {
  notifications.value = [];
  closeDrawer();
};

// 显示进度通知
const showProgressNotification = (task_id, data) => {
  const percent = Math.round((data.processed / data.total) * 100);
  const status = data.status;
  const processed = data.processed;
  const total = data.total;
  const successful = data.successful;
  
  // 任务标题
  const title = getNotificationTitle(data);
  
  // 状态颜色映射
  const statusColors = {
    completed: '#52c41a',
    failed: '#f5222d',
    processing: '#1890ff',
    started: '#722ed1'
  };
  
  // 获取当前状态颜色
  const statusColor = statusColors[status] || statusColors.processing;
  
  // 通知配置
  let notificationConfig = {
    key: `task-${task_id}`,
    message: h('div', { 
      style: {
        fontWeight: '500',
        fontSize: '15px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      } 
    }, [
      status === 'completed' ? '✅ 转换任务完成' : 
      status === 'failed' ? '❌ 转换任务失败' :
      status === 'started' ? '🚀 转换任务开始' :
      `🔄 ${title}：${percent}%`
    ]),
    description: h('div', {
      style: {
        marginTop: '8px'
      }
    }, [
      // 进度信息
      h('div', {
        style: {
          fontSize: '14px',
          marginBottom: status !== 'completed' && status !== 'failed' ? '12px' : '0',
          color: '#595959'
        }
      }, status === 'completed' ? data.message :
          status === 'failed' ? data.message || '转换过程中出现错误' :
          status === 'started' ? data.message || '任务准备中，即将开始...' :
          [
            h('span', {
              style: {
                color: statusColor,
                fontWeight: 'bold'
              }
            }, `${processed}/${total} `),
            '项已处理，',
            h('span', {
              style: {
                color: '#52c41a', 
                fontWeight: 'bold'
              }
            }, `${successful} `),
            '项成功'
          ]),
      
      // 进度条
      status !== 'completed' && status !== 'failed' ? 
        h('div', {
          style: {
            marginTop: '8px',
            padding: '4px',
            background: 'rgba(0,0,0,0.02)',
            borderRadius: '4px'
          }
        }, [
          h('a-progress', {
            percent: percent,
            status: getProgressStatus(status),
            size: 'small',
            strokeColor: statusColor,
            trailColor: 'rgba(0,0,0,0.06)',
            style: 'margin: 0;'
          })
        ]) : null,
        
      // 完成和失败时显示的时间提示
      (status === 'completed' || status === 'failed') ?
        h('div', {
          style: {
            fontSize: '12px',
            color: '#8c8c8c',
            marginTop: '8px',
            fontStyle: 'italic'
          }
        }, '此消息将在6秒后自动关闭') : null
    ]),
    duration: status === 'completed' || status === 'failed' ? 6 : 0, // 完成或失败后6秒关闭
    icon: () => h('div', {
      style: {
        width: '24px',
        height: '24px',
        borderRadius: '50%',
        background: statusColor,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#ffffff',
        fontSize: '12px',
        boxShadow: `0 0 8px ${statusColor}66`
      }
    }, [
      status === 'completed' ? h(CheckCircleOutlined) :
      status === 'failed' ? h(CloseCircleOutlined) :
      h(LoadingOutlined, { style: 'animation: spin 1.2s infinite linear;' })
    ]),
    style: {
      borderLeft: `4px solid ${statusColor}`,
      boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      backgroundColor: 'white'
    },
    class: 'custom-notification',
    placement: 'topRight'
  };
  
  // 开启或更新通知
  if (!activeNotifications.value[task_id]) {
    // 首次显示
    notification.open(notificationConfig);
    // 记录通知
    activeNotifications.value[task_id] = true;
    
    // 如果是完成或失败状态，6秒后删除记录
    if (status === 'completed' || status === 'failed') {
      setTimeout(() => {
        delete activeNotifications.value[task_id];
      }, 6000);
    }
  } else {
    // 更新已有通知
    notification.open(notificationConfig);
    
    // 如果是完成或失败状态，6秒后删除记录
    if (status === 'completed' || status === 'failed') {
      setTimeout(() => {
        delete activeNotifications.value[task_id];
      }, 6000);
    }
  }
};

// 处理WebSocket转换进度通知
const handleConvertProgress = (data) => {
  // 添加时间戳
  const notificationData = { ...data, timestamp: Date.now() };
  const task_id = notificationData.task_id || `${data.type}-${data.total}`;
  // 设置task_id
  notificationData.task_id = task_id;
  
  // 更新通知列表（用于抽屉显示）
  const index = notifications.value.findIndex(n => n.task_id === task_id);
  if (index !== -1) {
    notifications.value[index] = notificationData;
  } else {
    // 添加到通知列表
    notifications.value.unshift(notificationData);
  }
  
  // 限制最大通知数量
  if (notifications.value.length > 100) {
    notifications.value = notifications.value.slice(0, 100);
  }
  
  // 显示或更新系统通知 - 统一使用showProgressNotification方法
  // 处理所有状态：started, processing, completed, failed
  showProgressNotification(task_id, notificationData);
};

onMounted(() => {
  // 订阅WebSocket消息
  wsService.on('ws:html_to_md_convert_progress', handleConvertProgress);
  wsService.on('ws:md_to_dataset_convert_progress', handleConvertProgress);
});

onUnmounted(() => {
  // 取消订阅
  wsService.off('ws:html_to_md_convert_progress');
  wsService.off('ws:md_to_dataset_convert_progress');
});
</script>

<style scoped>
.notification-center {
  display: inline-block;
}

.notification-icon-btn {
  background-color: rgba(255, 255, 255, 0.15);
  color: white;
  border: none;
}

.notification-icon-btn:hover {
  background-color: rgba(255, 255, 255, 0.3);
  color: white;
}

.notification-list {
  max-height: calc(100vh - 200px);
  overflow-y: auto;
  overflow-x: hidden;
}

.notification-group {
  margin-bottom: 16px;
  padding-right: 8px;
}

.notification-group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.notification-title {
  font-weight: bold;
}

.notification-stats {
  display: flex;
  justify-content: space-between;
  margin: 8px 0;
  color: #666;
  font-size: 12px;
}

.notification-message {
  padding: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
  margin-top: 8px;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
}

.notification-actions {
  position: absolute;
  bottom: 20px;
  right: 20px;
}

.empty-notification {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}
</style>

<style>
/* 全局样式，用于通知动画 */
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.custom-notification {
  overflow: hidden;
  border-radius: 4px;
  transition: all 0.3s cubic-bezier(0.645, 0.045, 0.355, 1);
  animation: notificationFadeIn 0.3s ease;
}

@keyframes notificationFadeIn {
  from { 
    opacity: 0;
    transform: translateY(-10px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

/* 优化Ant Design通知样式 */
.ant-notification-notice-message {
  margin-bottom: 0 !important;
}

.ant-notification-notice-description {
  margin-left: 0 !important;  
}

.ant-notification-notice-with-icon .ant-notification-notice-message {
  margin-left: 36px !important;
}

.ant-notification-notice-with-icon .ant-notification-notice-description {
  margin-left: 36px !important;
}
</style> 