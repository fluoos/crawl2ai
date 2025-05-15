import axios from 'axios';
import { message } from 'ant-design-vue';

// 创建axios实例
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 60000
});

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 检查本地存储中是否有当前项目信息
    const projectStr = localStorage.getItem('currentProject');
    if (projectStr) {
      try {
        const currentProject = JSON.parse(projectStr);
        if (currentProject && currentProject.id) {
          // 根据请求方法类型，添加projectId参数
          if (config.method === 'get') {
            // GET请求：添加到params
            config.params = { 
              ...config.params, 
              projectId: currentProject.id 
            };
          } else {
            // POST/PUT/DELETE等请求：添加到data
            if (!config.data) {
              config.data = {};
            }
            
            // 检查data类型，如果是FormData，则直接添加字段
            if (config.data instanceof FormData) {
              config.data.append('projectId', currentProject.id);
            } else if (typeof config.data === 'string') {
              // 如果data是JSON字符串，则解析后添加
              try {
                const data = JSON.parse(config.data);
                data.projectId = currentProject.id;
                config.data = JSON.stringify(data);
              } catch (e) {
                // 如果解析失败，则不修改data
                console.warn('无法在JSON字符串中添加projectId');
              }
            } else {
              // 如果是普通对象，直接添加
              config.data.projectId = currentProject.id;
            }
          }
        }
      } catch (e) {
        console.warn('解析本地项目信息失败', e);
      }
    }
    return config;
  },
  error => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
service.interceptors.response.use(
  response => {
    return response.data;
  },
  error => {
    console.error('Response error:', error);
    const errorMsg = error.response?.data?.error || error.response?.data?.message || '请求失败';
    message.error(errorMsg);
    return Promise.reject(error);
  }
);

export default service; 