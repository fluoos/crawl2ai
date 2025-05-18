import { ref } from 'vue';

// 全局事件发射器，用于跨组件传递WebSocket消息
const eventEmitter = {
  callbacks: {},
  on(event, callback) {
    if (!this.callbacks[event]) {
      this.callbacks[event] = [];
    }
    this.callbacks[event].push(callback);
  },
  off(event, callback) {
    if (!this.callbacks[event]) return;
    if (!callback) {
      delete this.callbacks[event];
    } else {
      this.callbacks[event] = this.callbacks[event].filter(cb => cb !== callback);
    }
  },
  emit(event, data) {
    if (!this.callbacks[event]) return;
    this.callbacks[event].forEach(callback => callback(data));
  }
};

class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 3000; // 重连间隔，毫秒
    this.projectId = null;
    this.heartbeatInterval = null;
  }

  // 连接到WebSocket服务器
  connect(projectId) {
    if (!projectId) {
      console.error('WebSocket连接失败: 未提供项目ID');
      return;
    }

    // 如果已经连接到相同的项目ID，且连接状态正常，则不重新连接
    if (this.socket && 
        this.socket.readyState === WebSocket.OPEN && 
        this.projectId === projectId) {
      console.log(`WebSocket已连接到项目 ${projectId}，不重复连接`);
      return;
    }

    this.projectId = projectId;
    // 确保之前的连接已关闭
    this.disconnect();

    // 确定WebSocket URL，根据当前环境
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = process.env.NODE_ENV === 'development' 
     ? `ws://127.0.0.1:8000/api/system/ws/${projectId}`
     : `${protocol}//${window.location.host}/api/system/ws/${projectId}`;
    
    console.log(`正在连接WebSocket: ${wsUrl}`);
    
    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = () => {
        console.log('WebSocket连接已建立');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        // 发射连接事件
        eventEmitter.emit('ws:connected', { projectId });
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          // 根据消息类型发射不同的事件
          if (data.type) {
            eventEmitter.emit(`ws:${data.type}`, data);
          }
          if (data.type === 'heartbeat_response') {
            console.log('收到心跳响应');
          }
          // 同时发射所有消息的事件
          eventEmitter.emit('ws:message', data);
        } catch (error) {
          console.error('处理WebSocket消息出错:', error);
        }
      };

      this.socket.onclose = (event) => {
        this.isConnected = false;
        console.log(`WebSocket连接已关闭，代码: ${event.code}`);
        
        // 清除心跳定时器
        if (this.heartbeatInterval) {
          clearInterval(this.heartbeatInterval);
        }
        
        // 尝试重连
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`尝试重新连接 (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
          setTimeout(() => this.connect(this.projectId), this.reconnectInterval);
        } else {
          console.log('达到最大重连次数，停止重连');
          eventEmitter.emit('ws:reconnect_failed');
        }
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket连接错误:', error);
        eventEmitter.emit('ws:error', error);
      };

      // 设置心跳定时器
      this.heartbeatInterval = setInterval(() => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          // 发送简单的心跳消息
          this.socket.send(JSON.stringify({type: "heartbeat"}));
        }
      }, 30000); // 每10秒发送一次
    } catch (error) {
      console.error('建立WebSocket连接失败:', error);
      eventEmitter.emit('ws:error', error);
    }
  }

  // 断开WebSocket连接
  disconnect() {
    if (this.socket) {
      // 重置连接状态
      this.isConnected = false;
      // 关闭连接
      if (this.socket.readyState === WebSocket.OPEN || 
          this.socket.readyState === WebSocket.CONNECTING) {
        this.socket.close();
      }
      this.socket = null;
    }

    // 清除心跳定时器
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
  }

  // 发送消息到服务器
  sendMessage(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(typeof message === 'string' ? message : JSON.stringify(message));
      return true;
    }
    return false;
  }

  // 注册事件监听器
  on(event, callback) {
    eventEmitter.on(event, callback);
  }

  // 移除事件监听器
  off(event, callback) {
    eventEmitter.off(event, callback);
  }
}

// 创建单例实例
const wsService = new WebSocketService();

export default wsService; 