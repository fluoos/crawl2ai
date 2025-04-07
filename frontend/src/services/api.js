import request from './request';

// ------------ 原有API功能 ------------

// 基础格式API
export const getFormats = () => {
  return request({
    url: '/api/formats',
    method: 'get'
  });
};

export const getExamples = () => {
  return request({
    url: '/api/examples',
    method: 'get'
  });
};

export const previewData = (params) => {
  console.log('预览数据请求参数:', params);
  
  return request({
    url: '/api/preview',
    method: 'post',
    data: params
  });
};

export const exportData = (options) => {
  return request({
    url: '/api/export',
    method: 'post',
    data: options
  });
};

export const getDownloadUrl = (filename) => {
  return `${request.defaults.baseURL}/api/download/${filename}`;
};

export const getDataStats = () => {
  return request({
    url: '/api/stats',
    method: 'get'
  });
};

export const batchExport = (options) => {
  return request({
    url: '/api/batch-export',
    method: 'post',
    data: options
  });
};

// 爬虫API
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

export const stopCrawl = () => {
  return request({
    url: '/api/crawler/stop-crawl',
    method: 'post'
  });
};

export const deleteUrl = (params) => {
  return request({
    url: '/api/crawler/delete-url',
    method: 'post',
    data: params
  });
};

export const getCrawlStatus = () => {
  return request({
    url: '/api/crawler/status',
    method: 'get'
  });
};

// 转换API
export const convertToMarkdown = (params) => {
  return request({
    url: '/api/crawler/convert',
    method: 'post',
    data: params
  });
};

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

export const getConversionStatus = (outputFile) => {
  return request({
    url: '/api/converter/status',
    method: 'get',
    params: { output_file: outputFile }
  });
};

// 导出API
export const previewDataset = (format, style, inputFile, mapping) => {
  return request({
    url: '/api/export/preview',
    method: 'post',
    data: {
      format,
      style,
      input_file: inputFile,
      mapping
    }
  });
};

export const exportDataset = (format, style, inputFile, outputFile, mapping) => {
  return request({
    url: '/api/export/export',
    method: 'post',
    data: {
      format,
      style,
      input_file: inputFile,
      output_file: outputFile,
      mapping
    }
  });
};

export const getExportFiles = () => {
  return request({
    url: '/api/export/files',
    method: 'get'
  });
};

// 文件管理API
export const getFileList = (page = 1, pageSize = 10) => {
  return request({
    url: '/api/files',
    method: 'get',
    params: { page, pageSize }
  });
};

// 文件管理API-预览 
export const getFilePreview = (path) => {
  return request({
    url: '/api/files/preview',
    method: 'get',
    params: { path }
  });
};

export const uploadFile = (formData) => {
  return request({
    url: '/api/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

// 将convertToDataset重命名为convertFilesToDataset以适应新架构
export const convertFilesToDataset = (files, model, outputFile) => {
  return convertToDataset(files, model, outputFile);
};

// 系统配置API
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

export const updateSystemConfig = (config) => {
  // 暂时模拟保存
  if (config.apiKey) {
    localStorage.setItem('apiKey', config.apiKey);
  }
  return Promise.resolve(true);
};