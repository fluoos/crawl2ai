/**
 * 下载工具函数
 */

/**
 * 通过URL直接下载文件
 * @param {string} url - 文件URL
 * @param {string} filename - 保存的文件名，可选
 */
export const downloadFile = (url, filename = null) => {
  if (!url) return;
  
  // 创建一个隐藏的a标签
  const link = document.createElement('a');
  link.href = url;
  
  // 设置下载文件名（如果提供）
  if (filename) {
    link.download = filename;
  }
  
  // 将链接添加到文档中
  document.body.appendChild(link);
  
  // 触发点击事件
  link.click();
  
  // 移除链接
  document.body.removeChild(link);
};

/**
 * 通过Blob下载文件
 * @param {Blob} blob - 文件Blob对象
 * @param {string} filename - 下载的文件名
 */
export const downloadBlob = (blob, filename) => {
  if (!blob || !filename) return;
  
  // 创建Blob URL
  const url = window.URL.createObjectURL(blob);
  
  // 下载文件
  downloadFile(url, filename);
  
  // 释放Blob URL
  setTimeout(() => {
    window.URL.revokeObjectURL(url);
  }, 100);
}; 