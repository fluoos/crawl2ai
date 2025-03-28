import axios from 'axios';
import { message } from 'ant-design-vue';

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',  // 从环境变量读取基础URL
  timeout: 30000  // 请求超时时间
});

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 在发送请求前做些什么，比如加入token
    console.log('请求URL:', config.url);
    console.log('请求方法:', config.method);
    console.log('请求参数:', config.data || config.params);
    return config;
  },
  error => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  response => {
    // 记录成功响应的数据结构，有助于调试
    console.log('API响应成功:', response.config.url, response.data);
    return response.data;
  },
  error => {
    // 详细记录错误信息
    if (error.response) {
      // 服务器返回了错误状态码
      console.error('API响应错误:', {
        url: error.config.url,
        method: error.config.method,
        status: error.response.status,
        data: error.response.data,
        headers: error.config.headers
      });
      
      // 基于状态码给出更详细的错误信息
      if (error.response.status === 404) {
        message.error(`API接口不存在: ${error.config.url}`);
      } else if (error.response.status === 400) {
        message.error(`请求参数错误: ${error.response.data.detail || '参数格式有误'}`);
      } else if (error.response.status === 500) {
        message.error(`服务器内部错误: ${error.response.data.detail || '请联系管理员'}`);
      } else {
        message.error(`请求失败: ${error.response.data.detail || error.message}`);
      }
    } else if (error.request) {
      // 请求发出但没有收到响应
      console.error('API无响应:', {
        url: error.config.url,
        method: error.config.method
      });
      message.error('服务器无响应，请检查后端服务是否启动');
    } else {
      // 请求配置出错
      console.error('API请求配置错误:', error.message);
      message.error(`请求配置错误: ${error.message}`);
    }
    return Promise.reject(error);
  }
);

export default request; 