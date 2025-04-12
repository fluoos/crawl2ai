import request from './request';

/**
 * 将文件转换为数据集
 * @param {Array<string>} files 文件路径列表
 * @param {string} model 使用的模型
 * @param {string} outputFile 输出文件名
 * @returns {Promise}
 */
export const convertToDataset = (files, model, outputFile) => {
  return request({
    url: '/api/dataset/convert',
    method: 'post',
    data: {
      files,
      model,
      output_file: outputFile
    }
  });
};

/**
 * 获取文件列表
 * @param {number} page 页码
 * @param {number} pageSize 每页数量
 * @returns {Promise}
 */
export const getFileList = (page = 1, pageSize = 10) => {
  return request({
    url: '/api/files',
    method: 'get',
    params: { page, pageSize }
  });
};

/**
 * 预览文件内容
 * @param {string} path 文件路径
 * @returns {Promise}
 */
export const getFilePreview = (path) => {
  return request({
    url: '/api/files/preview',
    method: 'get',
    params: { path }
  });
};

/**
 * 删除文件
 * @param {Object} params 删除参数
 * @returns {Promise}
 */
export const deleteFiles = (params) => {
  return request({
    url: '/api/files/delete-file',
    method: 'post',
    data: params
  });
};

/**
 * 上传文件
 * @param {FormData} formData 表单数据
 * @returns {Promise}
 */
export const uploadFile = (formData) => {
  return request({
    url: '/api/files/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}; 