// frontend/src/services/project.js
import request from './request';

/**
 * 创建新项目
 * @param {Object} projectData 项目数据
 * @returns {Promise}
 */
export const createProject = (projectData) => {
  return request({
    url: '/api/project/create',
    method: 'post',
    data: projectData
  });
};

/**
 * 获取项目列表
 * @returns {Promise}
 */
export const listProjects = () => {
  return request({
    url: '/api/project/list',
    method: 'get'
  });
};

/**
 * 获取项目详情
 * @param {Number} projectId 项目ID
 * @returns {Promise}
 */
export const getProject = (projectId) => {
  return request({
    url: `/api/project/${projectId}`,
    method: 'get'
  });
};

/**
 * 更新项目
 * @param {Number} projectId 项目ID
 * @param {Object} projectData 更新数据
 * @returns {Promise}
 */
export const updateProject = (projectId, projectData) => {
  return request({
    url: `/api/project/${projectId}`,
    method: 'put',
    data: projectData
  });
};

/**
 * 删除项目
 * @param {Number} projectId 项目ID
 * @returns {Promise}
 */
export const deleteProject = (projectId) => {
  return request({
    url: `/api/project/${projectId}`,
    method: 'delete'
  });
};

/**
 * 创建项目数据集
 * @param {Object} data 数据集信息
 * @returns {Promise}
 */
export const createProjectDataset = (data) => {
  return request({
    url: '/api/project/dataset',
    method: 'post',
    data
  });
};