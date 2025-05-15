import request from './request';

/**
 * 获取数据集列表
 * @param {Object} params 查询参数
 * @returns {Promise}
 */
export const getDatasetList = (params) => {
  return request({
    url: '/api/dataset/list',
    method: 'get',
    params: params
  });
};

/**
 * 导出数据集
 * @param {Object} options 导出选项
 * @returns {Promise}
 */
export const exportDataset = (options) => {
  return request({
    url: '/api/dataset/export',
    method: 'post',
    data: options
  });
};

/**
 * 删除问答对
 * @param {Array<number>} ids 问答对ID列表
 * @returns {Promise}
 */
export const deleteQAItems = (ids) => {
  return request({
    url: '/api/dataset/delete',
    method: 'post',
    data: { ids }
  });
};

/**
 * 获取数据统计信息
 * @returns {Promise}
 */
export const getDataStats = () => {
  return request({
    url: '/api/dataset/stats',
    method: 'get'
  });
}; 

/**
 * 添加问答对
 * @param {Object} data 问答对数据，包含question、answer、chainOfThought和label字段
 * @returns {Promise}
 */
export const addQAItem = (data) => {
  return request({
    url: '/api/dataset/add',
    method: 'post',
    data
  });
};

/**
 * 更新问答对
 * @param {Object} data 问答对数据，包含question、answer、chainOfThought和label字段
 * @returns {Promise}
 */
export const updateQAItem = (data) => {
  return request({
    url: '/api/dataset/update',
    method: 'post',
    data
  });
};