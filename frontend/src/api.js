import axios from 'axios';

// API服务
const API_BASE_URL = 'http://localhost:5000/api';

// 改为命名导出
export const getFormats = async () => {
  const response = await axios.get(`${API_BASE_URL}/formats`);
  return response.data;
};

export const getExamples = async () => {
  const response = await axios.get(`${API_BASE_URL}/examples`);
  return response.data;
};

export const previewData = async (params) => {
  console.log('预览数据请求参数:', params); // 添加日志
  
  try {
    const response = await axios.post(`${API_BASE_URL}/preview`, params);
    console.log('预览数据响应:', response.data); // 添加日志
    return response.data;
  } catch (error) {
    console.error('预览数据请求失败:', error.response || error);
    if (error.response && error.response.data) {
      throw new Error(error.response.data.error || '预览数据失败');
    }
    throw error;
  }
};

export const exportData = async (options) => {
  const response = await axios.post(`${API_BASE_URL}/export`, options);
  return response.data;
};

export const getDownloadUrl = (filename) => {
  return `${API_BASE_URL}/download/${filename}`;
};

export const getDataStats = async () => {
  const response = await axios.get(`${API_BASE_URL}/stats`);
  return response.data;
};

export const batchExport = async (options) => {
  const response = await axios.post(`${API_BASE_URL}/batch-export`, options);
  return response.data;
}; 