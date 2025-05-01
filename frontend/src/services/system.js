import request from './request';

/**
 * 获取系统配置
 * @param {string} path 配置路径，可选
 * @returns {Promise<Object>} 配置信息
 */
export const getModelList = async () => {
  return request.get('/api/system/config/models');
};

export const addModel = async (model) => {
  return request.post('/api/system/config/models/add', model);
};

export const updateModel = async (model) => {
  return request.post(`/api/system/config/models/${model.id}`, model);
};

export const deleteModel = async (modelId) => {
  return request.post(`/api/system/config/models/${modelId}/delete`);
};

export const setDefaultModel = async (modelId) => {
  return request.post(`/api/system/config/models/${modelId}/default`);
};

export const getPrompts = async () => {
  return request.get('/api/system/config/prompts');
};

export const updatePrompts = async (prompts) => {
  return request.post('/api/system/config/prompts', prompts);
};

export const resetPrompts = async () => {
  return request.post('/api/system/config/prompts/reset');
};

export const getFileStrategy = async () => {
  return request.get('/api/system/config/file-strategy');
};

export const updateFileStrategy = async (strategy) => {
  return request.post('/api/system/config/file-strategy', strategy);
};

