import request from '../utils/request';

/**
 * 获取链接列表
 * @returns {Promise<Array>} - 链接列表
 */
export async function fetchLinks() {
  return request({
    url: '/api/crawler/links',
    method: 'get'
  });
}

/**
 * 爬取链接
 * @param {Object} params - 爬取参数
 * @param {string} params.url - 待爬取的URL
 * @param {number} params.depth - 爬取深度
 * @param {string} params.strategy - 爬取策略 (dfs/bfs)
 * @param {number} params.max_concurrency - 最大并发数
 * @param {boolean} params.force_refresh - 是否重新获取内容
 * @returns {Promise<Object>} - 爬取任务结果
 */
export async function crawlLink(params) {
  return request({
    url: '/api/crawler/crawl',
    method: 'post',
    data: params
  });
}

/**
 * 重新获取指定链接
 * @param {string|number} linkId - 链接ID
 * @param {boolean} forceRefresh - 是否重新获取内容
 * @returns {Promise<Object>} - 重新获取结果
 */
export async function refreshLink(linkId, forceRefresh = true) {
  return request({
    url: `/api/crawler/refresh/${linkId}`,
    method: 'post',
    data: { force_refresh: forceRefresh }
  });
}

/**
 * 重新获取所有链接
 * @param {boolean} forceRefresh - 是否重新获取内容
 * @returns {Promise<Object>} - 重新获取结果
 */
export async function refreshAllLinks(forceRefresh = true) {
  return request({
    url: '/api/crawler/refresh-all',
    method: 'post',
    data: { force_refresh: forceRefresh }
  });
} 