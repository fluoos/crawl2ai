<template>
  <div class="link-manager">
    <a-page-header title="链接管理" subtitle="爬取和管理网站链接" />
    
    <a-card title="爬取网站链接" class="card-wrapper">
      <a-form layout="vertical">
        <a-row :gutter="24">
          <a-col :span="12">
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
            <a-form-item label="最大并发数" name="maxConcurrent">
              <a-input-number
                v-model:value="formState.maxConcurrent"
                :min="1"
                :max="50"
                style="width: 100%"
              />
            </a-form-item>
          </a-col>
        </a-row>
        
        <a-row :gutter="24">
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
          <a-col :span="6">
            <a-form-item label="重新获取内容" name="forceRefresh">
              <a-switch v-model:checked="formState.forceRefresh" />
              <div class="form-item-hint">启用后将忽略缓存重新爬取</div>
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
        
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="包含URL模式（可选，用逗号分隔）" name="includePatterns">
              <a-input
                v-model:value="formState.includePatterns"
                placeholder="例如: blog,/news/"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="排除URL模式（可选，用逗号分隔）" name="excludePatterns">
              <a-input
                v-model:value="formState.excludePatterns"
                placeholder="例如: admin,/login/"
              />
            </a-form-item>
          </a-col>
        </a-row>
      </a-form>
      
      <a-alert
        v-if="crawlStatus"
        :message="crawlStatus"
        :type="crawlStatusType"
        show-icon
        style="margin-top: 16px"
      />
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
            @click="handleConvert"
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
                转换
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { ReloadOutlined } from '@ant-design/icons-vue';
import { crawlLinks, getCrawlStatus, convertToMarkdown } from '../services/api';

// 表单状态
const formState = reactive({
  url: '',
  maxDepth: 3,
  maxPages: 100,
  includePatterns: '',
  excludePatterns: '',
  crawlStrategy: 'bfs',
  forceRefresh: false,
  maxConcurrent: 20
});

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
});

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
      max_depth: formState.maxDepth,
      max_pages: formState.maxPages,
      include_patterns: includePatterns,
      exclude_patterns: excludePatterns,
      crawl_strategy: formState.crawlStrategy,
      force_refresh: formState.forceRefresh,
      max_concurrent: formState.maxConcurrent
    });
    
    if (response.status === 'success') {
      message.success('爬取任务已开始');
      crawlStatus.value = `爬取任务正在进行（${formState.crawlStrategy}策略），稍后将自动刷新结果`;
      crawlStatusType.value = 'info';
      
      // 5秒后自动刷新状态
      setTimeout(fetchCrawlStatus, 5000);
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

// 获取爬虫状态
const fetchCrawlStatus = async () => {
  tableLoading.value = true;
  try {
    const response = await getCrawlStatus();
    
    if (response.status === 'completed') {
      crawlStatus.value = '爬取完成';
      crawlStatusType.value = 'success';
      
      if (response.urls && response.urls.length > 0) {
        // 更新URL列表
        urlList.value = response.urls;
        pagination.total = response.count || response.urls.length;
      } else {
        urlList.value = [];
        pagination.total = 0;
      }
    } else if (response.status === 'running') {
      crawlStatus.value = '爬取任务正在进行中...';
      crawlStatusType.value = 'info';
      
      // 继续轮询
      setTimeout(fetchCrawlStatus, 5000);
    } else if (response.status === 'failed') {
      crawlStatus.value = response.message || '爬取任务失败';
      crawlStatusType.value = 'error';
    } else {
      crawlStatus.value = response.message || '获取爬虫状态';
      crawlStatusType.value = 'info';
    }
  } catch (error) {
    console.error('获取爬虫状态失败:', error);
    crawlStatus.value = '获取爬虫状态失败';
    crawlStatusType.value = 'error';
  } finally {
    tableLoading.value = false;
  }
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

// 转换单个URL
const handleSingleConvert = async (record) => {
  await handleConvertUrls([record.url]);
};

// 转换选中的URLs
const handleConvert = async () => {
  if (selectedUrls.value.length === 0) {
    message.warning('请先选择要转换的URL');
    return;
  }
  
  await handleConvertUrls(selectedUrls.value);
};

// 转换URLs
const handleConvertUrls = async (urls) => {
  convertLoading.value = true;
  try {
    const response = await convertToMarkdown({
      urls: urls,
      output_dir: "output"
    });
    
    if (response.status === 'success') {
      message.success('转换任务已提交，请在文件管理中查看结果');
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
</style> 