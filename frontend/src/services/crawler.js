import request from './request';

/**
 * 开始爬取链接
 * @param {Object} params 爬取参数
 * @returns {Promise}
 */
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

/**
 * 停止爬取
 * @returns {Promise}
 */
export const stopCrawl = () => {
  return request({
    url: '/api/crawler/stop-crawl',
    method: 'post'
  });
};

/**
 * 删除链接
 * @param {Object} params 删除参数
 * @returns {Promise}
 */
export const deleteUrls = (params) => {
  return request({
    url: '/api/crawler/delete-url',
    method: 'post',
    data: params
  });
};

/**
 * 获取爬取状态和链接列表
 * @returns {Promise}
 */
export const getCrawlStatus = () => {
  return request({
    url: '/api/crawler/status',
    method: 'get'
  });
};

/**
 * 将URL列表转换为Markdown
 * @param {Object} data 
 * @param {Array<string>} data.urls URL列表
 * @param {string} data.included_selector 包含选择器（可选）
 * @param {string} data.excluded_selector 排除选择器（可选）
 * @returns {Promise<Object>}
 */
export async function convertToMarkdown(data) {
  try {
    return await request.post('/api/crawler/convert', data);
  } catch (error) {
    console.error('转换为Markdown失败:', error);
    throw error;
  }
}

/**
 * 导出所有链接到Excel文件
 * @returns {Promise<Object>}
 */
export const exportLinksToExcel = () => {
  return request({
    url: '/api/crawler/export-excel',
    method: 'post'
  });
}; 