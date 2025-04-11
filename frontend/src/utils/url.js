/**
 * URL处理工具函数
 */

/**
 * 获取API基础URL
 * @returns {string} API基础URL
 */
export const getApiBaseUrl = () => {
  return import.meta.env.VITE_API_BASE_URL || '';
};

/**
 * 将相对路径转换为完整的API URL
 * @param {string} path - 相对路径
 * @returns {string} 完整的API URL
 */
export const getFullApiUrl = (path) => {
  if (!path) return '';
  if (path.startsWith('http')) return path;
  
  const baseUrl = getApiBaseUrl();
  // 确保baseUrl和path之间只有一个斜杠
  const separator = baseUrl.endsWith('/') || path.startsWith('/') ? '' : '/';
  return `${baseUrl}${separator}${path}`;
};

/**
 * 将API返回的下载URL转换为可访问的完整URL
 * @param {object} response - API响应对象
 * @param {string} urlField - 包含URL的字段名，默认为'downloadUrl'
 * @returns {object} 处理后的响应对象
 */
export const processApiDownloadUrl = (response, urlField = 'downloadUrl') => {
  if (response && response[urlField]) {
    response[urlField] = getFullApiUrl(response[urlField]);
  }
  return response;
}; 