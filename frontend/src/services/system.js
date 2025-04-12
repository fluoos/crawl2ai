import request from './request';

/**
 * 获取系统配置
 * @returns {Promise}
 */
export const getSystemConfig = () => {
  // 暂时模拟返回结果
  return Promise.resolve({
    baseUrl: 'https://api.deepseek.com',
    model: 'deepseek-chat',
    apiKey: localStorage.getItem('apiKey') || '',
    temperature: 0.7,
    maxTokens: 4000,
    logLevel: 'info'
  });
};

/**
 * 更新系统配置
 * @param {Object} config 配置对象
 * @returns {Promise}
 */
export const updateSystemConfig = (config) => {
  // 暂时模拟保存
  if (config.apiKey) {
    localStorage.setItem('apiKey', config.apiKey);
  }
  return Promise.resolve(true);
}; 