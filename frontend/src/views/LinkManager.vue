<template>
  <div class="link-manager">
    <a-page-header title="链接管理" subtitle="爬取和管理网站链接" />
    
    <a-card title="爬取网站链接" class="card-wrapper">
      <a-form layout="vertical">
        <a-row :gutter="24">
          <a-col :span="6">
            <a-form-item label="网站域名" name="url">
              <a-input
                v-model:value="formState.url"
                placeholder="请输入网站域名，如 example.com"
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="爬取策略" name="crawlStrategy">
              <a-select v-model:value="formState.crawlStrategy">
                <a-select-option value="bfs">广度优先 (BFS)</a-select-option>
                <a-select-option value="dfs">深度优先 (DFS)</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="爬取深度" name="maxDepth">
              <a-input-number
                v-model:value="formState.maxDepth"
                :min="1"
                :max="10"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="最大页面数" name="maxPages">
              <a-input-number
                v-model:value="formState.maxPages"
                :min="10"
                :max="5000"
                :step="10"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
          
        </a-row>
        
        <a-row :gutter="24">          
          <a-col :span="6">
            <a-form-item label="包含URL模式（可选，用逗号分隔）" name="includePatterns">
              <a-input
                v-model:value="formState.includePatterns"
                placeholder="例如: blog,/news/"
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="排除URL模式（可选，用逗号分隔）" name="excludePatterns">
              <a-input
                v-model:value="formState.excludePatterns"
                placeholder="例如: admin,/login/"
              />
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label="清空并重新获取" name="forceRefresh">
              <a-switch v-model:checked="formState.forceRefresh" />
              <div class="form-item-hint">启用后将清除所有链接并重新爬取</div>
            </a-form-item>
          </a-col>
          <a-col :span="6">
            <a-form-item label=" ">
              <a-button
                type="primary"
                :loading="crawlLoading"
                @click="startCrawl"
                block
              >
                开始爬取
              </a-button>
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
      <a-row :gutter="24">
        <a-alert
          v-if="crawlStatus"
          :message="crawlStatus"
          :type="crawlStatusType"
          show-icon
          style="flex: 1; margin-right: 10px;"
        >
          <template v-if="crawlStatus.includes('进行中')" #icon>
            <a-spin size="small" style="margin-right: 10px;"/>
          </template>
        </a-alert>
        <a-button v-if="crawlStatus.includes('进行中')" style="height: 40px;" danger type="primary" @click="handleStopCrawl">
          强制停止
        </a-button>
      </a-row>
    </a-card>
    
    <a-card title="已爬取URL列表" class="card-wrapper">
      <template #extra>
        <a-space>
          <a-button @click="fetchCrawlStatus">
            <ReloadOutlined /> 刷新状态
          </a-button>
          <a-button
            type="primary"
            :disabled="!selectedUrls.length"
            @click="showConvertModal"
            :loading="convertLoading"
          >
            转换为Markdown
          </a-button>
        </a-space>
      </template>
      
      <a-table
        :columns="columns"
        :data-source="urlList"
        :pagination="pagination"
        :loading="tableLoading"
        :row-selection="{ selectedRowKeys: selectedKeys, onChange: onSelectChange }"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, text, record }">
          <template v-if="column.dataIndex === 'url'">
            <a :href="text" target="_blank">{{ text }}</a>
          </template>
          <template v-if="column.dataIndex === 'action'">
            <a-space>
              <a-button type="link" size="small" @click="handleSingleConvert(record)">
                {{ record.filePath ? '重新转换' : '转换' }}
              </a-button>
              <a-button type="link" size="small" danger @click="handleDelete(record)">
                删除
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
    
    <!-- 添加转换配置的弹窗 -->
    <a-modal
      v-model:visible="convertModalVisible"
      title="转换设置"
      @ok="handleConvertConfirm"
      okText="开始转换"
      cancelText="取消"
      :confirmLoading="convertLoading"
      width="650px"
    >
      <a-form layout="vertical" :style="{ marginTop: '-8px' }">
        <!-- 选择器设置 -->
        <div class="settings-section">
          <div class="section-header">
            <div class="section-indicator selector-indicator"></div>
            <span class="section-title">内容选择器</span>
          </div>
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="包含选择器" name="includedSelector" :style="{ marginBottom: '16px' }">
                <a-input 
                  v-model:value="convertOptions.includedSelector" 
                  placeholder=".article-content"
                />
                <div class="form-hint">指定要包含的HTML元素</div>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="排除选择器" name="excludedSelector" :style="{ marginBottom: '16px' }">
                <a-input 
                  v-model:value="convertOptions.excludedSelector" 
                  placeholder=".ads, .sidebar"
                />
                <div class="form-hint">指定要排除的HTML元素</div>
              </a-form-item>
            </a-col>
          </a-row>
        </div>
        
        <!-- 智能分段设置 -->
        <div class="settings-section">
          <div class="section-header">
            <div class="section-indicator smart-indicator"></div>
            <span class="section-title">智能分段</span>
          </div>
          
          <div class="smart-split-toggle">
            <a-form-item name="enableSmartSplit" :style="{ marginBottom: '12px' }">
              <a-row justify="space-between" align="middle">
                <a-col>
                  <span class="toggle-label">启用智能分段</span>
                  <div class="form-hint" style="margin-top: 2px;">自动分段，适用于RAG和大模型场景</div>
                </a-col>
                <a-col>
                  <a-switch 
                    v-model:checked="convertOptions.enableSmartSplit"
                    checked-children="开启"
                    un-checked-children="关闭"
                  />
                </a-col>
              </a-row>
            </a-form-item>
          </div>
          
          <!-- 智能分段配置 -->
          <template v-if="convertOptions.enableSmartSplit">
            <div class="smart-config">
              <a-row :gutter="16" :style="{ marginBottom: '16px' }">
                <a-col :span="12">
                  <a-form-item label="最大Token数" name="maxTokens" :style="{ marginBottom: '8px' }">
                    <a-input-number 
                      v-model:value="convertOptions.maxTokens"
                      :min="500"
                      :max="20000"
                      :step="100"
                      style="width: 100%"
                      placeholder="8000"
                    />
                    <div class="form-hint">每段最大Token数</div>
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="最小Token数" name="minTokens" :style="{ marginBottom: '8px' }">
                    <a-input-number 
                      v-model:value="convertOptions.minTokens"
                      :min="100"
                      :max="2000"
                      :step="50"
                      style="width: 100%"
                      placeholder="300"
                    />
                    <div class="form-hint">每段最小Token数</div>
                  </a-form-item>
                </a-col>
              </a-row>
              
              <a-form-item label="分段策略" name="splitStrategy" :style="{ marginBottom: '8px' }">
                <a-select 
                  v-model:value="convertOptions.splitStrategy"
                  placeholder="选择分段策略"
                >
                  <a-select-option value="conservative">保守策略 - 较少分段，保持完整性</a-select-option>
                  <a-select-option value="balanced">平衡策略 - 兼顾完整性和检索效果</a-select-option>
                  <a-select-option value="aggressive">积极策略 - 更多分段，适合精细检索</a-select-option>
                </a-select>
              </a-form-item>
            </div>
          </template>
        </div>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { ReloadOutlined  } from '@ant-design/icons-vue';
import { crawlLinks, getCrawlStatus, convertToMarkdown, stopCrawl, deleteUrls } from '../services/crawler';
import { getFileStrategy } from '../services/system';
import wsService from '../services/websocket';

// 表单状态
const formState = reactive({
  url: '',
  maxDepth: 3,
  maxPages: 100,
  includePatterns: '',
  excludePatterns: '',
  crawlStrategy: 'bfs',
  forceRefresh: false
});

// 转换选项状态
const convertOptions = reactive({
  includedSelector: '',
  excludedSelector: '',
  enableSmartSplit: true,
  maxTokens: 8000,
  minTokens: 300,
  splitStrategy: 'balanced'
});

// 转换弹窗状态
const convertModalVisible = ref(false);
// 当前选中的URL列表（用于转换）
const urlsToConvert = ref([]);

// 爬取状态
const crawlLoading = ref(false);
const crawlStatus = ref('');
const crawlStatusType = ref('info');
const tableLoading = ref(false);
const convertLoading = ref(false);

// 表格数据
const urlList = ref([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条`
});

// 选择状态
const selectedKeys = ref([]);
const selectedUrls = ref([]);

// 表格列定义
const columns = [
  {
    title: 'ID',
    dataIndex: 'id',
    width: 80
  },
  {
    title: 'URL',
    dataIndex: 'url',
    ellipsis: true
  },
  {
    title: '深度',
    dataIndex: 'depth',
    width: 80
  },
  {
    title: '得分',
    dataIndex: 'score',
    width: 80
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 150,
    fixed: 'right'
  }
];

// 初始化
onMounted(() => {
  fetchCrawlStatus();
  fetchSmartSplitConfig();
  
  // 订阅WebSocket消息，监听URL转换为Markdown的进度
  wsService.on('ws:html_to_md_convert_progress', handleConvertProgress);
});

// 组件卸载时移除事件监听
onUnmounted(() => {
  // 移除WebSocket监听
  wsService.off('ws:html_to_md_convert_progress');
});

// 处理转换进度消息
const handleConvertProgress = (data) => {
  console.log('收到转换进度消息:', data);
  
  // 如果状态是completed或processing，自动刷新列表数据
  if (data.status === 'completed' || (data.status === 'processing' && data.processed % 5 === 0)) {
    fetchCrawlStatus();
  }
};

// 获取智能分段配置
const fetchSmartSplitConfig = async () => {
  try {
    const response = await getFileStrategy();
    if (response && response.data) {
      const data = response.data;
      // 更新智能分段配置
      convertOptions.enableSmartSplit = data.enableSmartSplit !== false;
      convertOptions.maxTokens = data.maxTokens || 8000;
      convertOptions.minTokens = data.minTokens || 300;
      convertOptions.splitStrategy = data.splitStrategy || 'balanced';
    }
  } catch (error) {
    console.error('获取智能分段配置失败:', error);
  }
};

// 开始爬取
const startCrawl = async () => {
  if (!formState.url) {
    message.error('请输入网站域名');
    return;
  }
  
  try {
    crawlLoading.value = true;
    crawlStatus.value = '爬取任务已提交，请稍候...';
    crawlStatusType.value = 'info';
    
    let url = formState.url;
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }
    
    // 处理包含和排除模式
    const includePatterns = formState.includePatterns ? 
      formState.includePatterns.split(',').map(p => p.trim()) : 
      null;
      
    const excludePatterns = formState.excludePatterns ? 
      formState.excludePatterns.split(',').map(p => p.trim()) : 
      null;
    
    const response = await crawlLinks({
      url: url,
      maxDepth: formState.maxDepth,
      maxPages: formState.maxPages,
      includePatterns: includePatterns,
      excludePatterns: excludePatterns,
      crawlStrategy: formState.crawlStrategy,
      forceRefresh: formState.forceRefresh
    });
    
    if (response.status === 'success') {
      message.success('爬取任务已开始');
      crawlStatus.value = `爬取任务正在进行（${formState.crawlStrategy}策略），稍后将自动刷新结果`;
      crawlStatusType.value = 'info';
      
      // 5秒后自动刷新状态
      setTimeout(fetchCrawlStatus, 3000);
    } else {
      message.error(response.message || '爬取任务启动失败');
      crawlStatus.value = '爬取任务启动失败';
      crawlStatusType.value = 'error';
    }
  } catch (error) {
    console.error('爬取失败:', error);
    message.error('爬取失败');
    crawlStatus.value = '爬取任务启动失败';
    crawlStatusType.value = 'error';
  } finally {
    crawlLoading.value = false;
  }
};

// 添加停止爬取的方法
const handleStopCrawl = async () => {
  try {
    const response = await stopCrawl();
    
    if (response.status === 'success') {
      message.success('已成功停止爬取任务');
      crawlStatus.value = '爬取任务已手动停止';
      crawlStatusType.value = 'warning';
    } else {
      message.error(response.message || '停止爬取任务失败');
    }
    
    // 刷新状态
    setTimeout(fetchCrawlStatus, 100);
  } catch (error) {
    console.error('停止爬取任务失败:', error);
    message.error('停止爬取任务失败');
  } finally {
  }
};

// 获取爬虫状态
const fetchCrawlStatus = async () => {
  tableLoading.value = true;
  try {
    const response = await getCrawlStatus();
    
    if (response.status === 'completed') {
      crawlStatus.value = '爬取完成';
      crawlStatusType.value = 'success';
    } else if (response.status === 'running') {
      crawlStatus.value = '爬取任务正在进行中...' + (response.urls && response.urls.length > 0 ? `已爬取${response.urls.length}个URL` : 0);
      crawlStatusType.value = 'info';
      
      // 继续轮询
      setTimeout(fetchCrawlStatus, 8000);
    } else if (response.status === 'failed') {
      crawlStatus.value = response.message || '爬取任务失败';
      crawlStatusType.value = 'error';
    } else {
      crawlStatus.value = response.message || '获取爬虫状态';
      crawlStatusType.value = 'info';
    }
    if (response.urls && response.urls.length > 0) {
      // 更新URL列表
      urlList.value = response.urls;
      pagination.total = response.count || response.urls.length;
    }
  } catch (error) {
    console.error('获取爬虫状态失败:', error);
    crawlStatus.value = '获取爬虫状态失败';
    crawlStatusType.value = 'error';
  } finally {
    tableLoading.value = false;
  }
};

// 删除指定链接
const handleDelete = async (record) => {
  // 添加确认弹窗
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除 "${record.url}" 吗？此操作无法撤销。`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        const response = await deleteUrls({
          urls: [record.url]
        });
        
        if (response.status === 'success') {
          message.success('链接已成功删除');
          // 删除成功后，刷新状态
          fetchCrawlStatus();
        } else {
          message.error(response.message || '删除链接失败');
        }
      } catch (error) {
        console.error('删除链接失败:', error);
        message.error('删除链接失败');
      }
    }
  });
};

// 表格选择变化
const onSelectChange = (keys, rows) => {
  selectedKeys.value = keys;
  selectedUrls.value = rows.map(row => row.url);
};

// 表格分页变化
const handleTableChange = (pag) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
};

// 显示转换配置弹窗 - 单个URL
const handleSingleConvert = (record) => {
  urlsToConvert.value = [record.url];
  convertModalVisible.value = true;
};

// 显示转换配置弹窗 - 多个URL
const showConvertModal = () => {
  if (selectedUrls.value.length === 0) {
    message.warning('请先选择要转换的URL');
    return;
  }
  
  urlsToConvert.value = selectedUrls.value;
  convertModalVisible.value = true;
};

// 确认转换
const handleConvertConfirm = async () => {
  convertLoading.value = true;
  try {
    const requestData = {
      urls: urlsToConvert.value,
      included_selector: convertOptions.includedSelector || null,
      excluded_selector: convertOptions.excludedSelector || null
    };

    // 如果启用智能分段，添加相关参数
    if (convertOptions.enableSmartSplit) {
      requestData.enable_smart_split = true;
      requestData.max_tokens = convertOptions.maxTokens;
      requestData.min_tokens = convertOptions.minTokens;
      requestData.split_strategy = convertOptions.splitStrategy;
    }

    const response = await convertToMarkdown(requestData);
    
    if (response.status === 'success') {
      message.success('转换任务已提交，稍后更新进度结果');
      convertModalVisible.value = false;
      
      // 转换开始后，会通过WebSocket接收进度消息
    } else {
      message.error(response.message || '转换失败');
    }
  } catch (error) {
    console.error('转换失败:', error);
    message.error('转换失败');
  } finally {
    convertLoading.value = false;
  }
};
</script>

<style scoped>
.link-manager {
  max-width: 1200px;
  margin: 0 auto;
}

.card-wrapper {
  margin-bottom: 24px;
}

.form-item-hint {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.form-hint {
  font-size: 11px;
  color: #8c8c8c;
  margin-top: 2px;
  line-height: 1.4;
}

.settings-section {
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.section-indicator {
  width: 2px;
  height: 13px;
  border-radius: 0;
  margin-right:8px;
}

.selector-indicator {
  background-color: #1890ff;
}

.smart-indicator {
  background-color: #52c41a;
}

.section-title {
  font-weight: 500;
  font-size: 14px;
}

.smart-split-toggle {
  margin-bottom: 16px;
}

.toggle-label {
  font-weight: 500;
}

.smart-config {
  margin-bottom: 16px;
}
</style> 