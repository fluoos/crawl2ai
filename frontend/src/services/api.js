import request from './request';

// 数据集管理-导出数据
export const exportDataset = (options) => {
  return request({
    url: '/api/dataset/export',
    method: 'post',
    data: options
  });
};

// 数据集管理-数据列表
export const getDatasetList = (params) => {
  return request({
    url: '/api/dataset/list',
    method: 'post',
    data: params
  });
};

// 数据集管理-删除问答对
export const deleteQAItems = (ids) => {
  return request({
    url: '/api/dataset/delete',
    method: 'post',
    data: { ids }
  });
};

// 数据集管理-获取数据统计
export const getDataStats = () => {
  return request({
    url: '/api/dataset/stats',
    method: 'get'
  });
};

// 链接管理-开始爬取链接
export const crawlLinks = (params) => {
  // 转换参数命名风格为snake_case
  const apiParams = {
    url: params.url,
    max_depth: params.maxDepth,
    max_pages: params.maxPages,
    include_patterns: params.includePatterns,
    exclude_patterns: params.excludePatterns,
    crawl_strategy: params.crawlStrategy,
    force_refresh: params.forceRefresh
  };
  
  return request({
    url: '/api/crawler/crawl',
    method: 'post',
    data: apiParams
  });
};

// 链接管理-停止爬取
export const stopCrawl = () => {
  return request({
    url: '/api/crawler/stop-crawl',
    method: 'post'
  });
};

// 链接管理-删除链接
export const deleteUrls = (params) => {
  return request({
    url: '/api/crawler/delete-url',
    method: 'post',
    data: params
  });
};

// 链接管理-获取状态和链接列表
export const getCrawlStatus = () => {
  return request({
    url: '/api/crawler/status',
    method: 'get'
  });
};

// 链接管理-转换成markdown文件
export const convertToMarkdown = (params) => {
  return request({
    url: '/api/crawler/convert',
    method: 'post',
    data: params
  });
};

// 文件管理-转换文件
export const convertToDataset = (files, model, outputFile) => {
  return request({
    url: '/api/converter/convert',
    method: 'post',
    data: {
      files,
      model,
      output_file: outputFile
    }
  });
};

// 文件管理-列表
export const getFileList = (page = 1, pageSize = 10) => {
  return request({
    url: '/api/files',
    method: 'get',
    params: { page, pageSize }
  });
};

// 文件管理-预览 
export const getFilePreview = (path) => {
  return request({
    url: '/api/files/preview',
    method: 'get',
    params: { path }
  });
};

// 文件管理-删除文件 
export const deleteFiles = (params) => {
  return request({
    url: '/api/files/delete-file',
    method: 'post',
    data: params
  });
};

// 文件管理-上传文件 
export const uploadFile = (formData) => {
  return request({
    url: '/api/files/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

// 系统配置-获取
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

// 系统配置-更新
export const updateSystemConfig = (config) => {
  // 暂时模拟保存
  if (config.apiKey) {
    localStorage.setItem('apiKey', config.apiKey);
  }
  return Promise.resolve(true);
};