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