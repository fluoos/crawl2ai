<template>
  <div class="file-manager">
    <a-page-header title="文件管理" subtitle="管理和处理文件" />
    
    <a-card title="上传文件" class="card-wrapper">
      <FileUploader @upload-success="handleUploadSuccess" />
    </a-card>
    
    <a-card title="Markdown文件列表" class="card-wrapper">
      <template #extra>
        <a-space>
          <a-button @click="fetchFileList">
            <ReloadOutlined /> 刷新列表
          </a-button>
          <a-button
            type="primary"
            :disabled="!selectedFiles.length"
            @click="handleConvertFiles"
            :loading="convertLoading"
          >
            转换为数据集
          </a-button>
        </a-space>
      </template>
      
      <DataTable
        :columns="columns"
        :data-source="fileList"
        :pagination="pagination"
        :loading="tableLoading"
        :row-selection="{ selectedRowKeys: selectedKeys, onChange: onSelectChange }"
        @change="handleTableChange"
      >
        <template #body-filename="{ record }">
          <a @click="previewFile(record)">{{ record.filename }}</a>
        </template>
        <template #body-size="{ record }">
          {{ formatFileSize(record.size) }}
        </template>
        <template #body-source="{ record }">
          <a-tooltip v-if="record.url" :title="record.url">
            <a 
              :href="record.url" 
              target="_blank"
              class="source-link"
            >
              网页链接
            </a>
          </a-tooltip>
          <span v-else>本地上传</span>
        </template>
        <template #body-action="{ record }">
          <a-space>
            <a-button type="link" size="small" @click="previewFile(record)">
              预览
            </a-button>
            <a-button type="link" size="small" @click="handleSingleConvert(record)">
              {{ record.isDataset ? '重新转换' : '转换'}}
            </a-button>
            <a-button type="link" size="small" danger @click="handleDelete(record)">
              删除
            </a-button>
          </a-space>
        </template>
      </DataTable>
    </a-card>
    
    <!-- 文件转换对话框 -->
    <a-modal
      v-model:visible="convertModalVisible"
      title="转换为数据集"
      @ok="confirmConvert"
      :confirm-loading="convertLoading"
    >
      <a-form :model="convertForm" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
        <a-form-item label="输出文件名">
          <a-input disabled v-model:value="convertForm.outputFile" placeholder="qa_dataset.jsonl" />
        </a-form-item>
      </a-form>
    </a-modal>
    
    <!-- 文件预览对话框 -->
    <a-modal
      v-model:visible="previewModalVisible"
      title="文件预览"
      width="800px"
      :footer="null"
    >
      <div class="file-preview">
        <pre v-if="previewContent">{{ previewContent }}</pre>
        <a-empty v-else description="文件内容为空" />
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { ReloadOutlined } from '@ant-design/icons-vue';
import DataTable from '../components/common/DataTable.vue';
import FileUploader from '../components/common/FileUploader.vue';
import { getFileList, convertToDataset, getFilePreview, deleteFiles } from '../services/files';
import wsService from '../services/websocket';

// 表格数据
const fileList = ref([]);
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showTotal: (total) => `共 ${total} 条`
});

// 状态
const tableLoading = ref(false);
const convertLoading = ref(false);
const selectedKeys = ref([]);
const selectedFiles = ref([]);

// 预览相关
const previewModalVisible = ref(false);
const previewContent = ref('');

// 转换相关
const convertModalVisible = ref(false);
const convertForm = reactive({
  outputFile: 'qa_dataset.jsonl',
  files: []
});

// 表格列定义
const columns = [
  {
    title: '文件名',
    dataIndex: 'filename',
    ellipsis: true
  },
  {
    title: '大小',
    dataIndex: 'size',
    width: 120
  },
  {
    title: '来源',
    dataIndex: 'source',
    width: 120
  },
  {
    title: '修改时间',
    dataIndex: 'modifiedTime',
    width: 180
  },
  {
    title: '操作',
    dataIndex: 'action',
    width: 210,
    fixed: 'right'
  }
];

// 初始化
onMounted(() => {
  fetchFileList();
  wsService.on('ws:md_to_dataset_convert_progress', handleConvertProgress);
});

// 组件卸载时移除事件监听
onUnmounted(() => {
  wsService.off('ws:md_to_dataset_convert_progress');
});

// 处理转换进度消息
const handleConvertProgress = (data) => {
  // 如果状态是completed或processing，自动刷新列表数据
  if (data.status === 'completed' || (data.status === 'processing' && data.processed % 5 === 0)) {
    fetchFileList();
  }
};

// 获取文件列表
const fetchFileList = async () => {
  tableLoading.value = true;
  try {
    const response = await getFileList(pagination.current, pagination.pageSize);
    
    if (response && response.files) {
      const files = response.files.map(file => ({
        ...file,
        id: file.id || file.url || file.filename
      }));
      fileList.value = []
      nextTick(() => {
        fileList.value = files;
      })
      pagination.total = response.total || files.length;
    } else {
      fileList.value = [];
      pagination.total = 0;
    }
  } catch (error) {
    console.error('获取文件列表失败:', error);
    message.error('获取文件列表失败');
  } finally {
    tableLoading.value = false;
  }
};

// 文件上传成功处理
const handleUploadSuccess = () => {
  fetchFileList();
};

// 表格选择变化
const onSelectChange = (keys, rows) => {
  selectedKeys.value = keys;
  selectedFiles.value = rows.map(row => row.path || row.filename);
};

// 表格分页变化
const handleTableChange = (pag) => {
  pagination.current = pag.current;
  pagination.pageSize = pag.pageSize;
  fetchFileList();
};

// 预览文件
const previewFile = async (record) => {
  try {
    // 真实环境应该通过API获取文件内容
    const response = await getFilePreview(record.path);
    if (response && response.content) {
      previewContent.value = response.content;
    } else {
      message.error('获取文件内容失败');
    }
    previewModalVisible.value = true;
  } catch (error) {
    message.error('获取文件内容失败');
  }
};

// 转换单个文件
const handleSingleConvert = (record) => {
  convertForm.files = [record.path || record.filename];
  convertModalVisible.value = true;
};

// 转换选中的文件
const handleConvertFiles = () => {
  if (selectedFiles.value.length === 0) {
    message.warning('请先选择要转换的文件');
    return;
  }
  
  convertForm.files = selectedFiles.value;
  convertModalVisible.value = true;
};

// 确认转换
const confirmConvert = async () => {
  if (!convertForm.outputFile) {
    message.error('请输入输出文件名');
    return;
  }
  
  convertLoading.value = true;
  try {
    const response = await convertToDataset(
      convertForm.files,
      convertForm.outputFile
    );
    
    if (response && response.status === 'success') {
      message.success('转换任务已提交，稍后更新进度结果');
      convertModalVisible.value = false;
    } else {
      message.error(response?.message || '转换失败');
    }
  } catch (error) {
    console.error('转换失败:', error);
    message.error('转换失败');
  } finally {
    convertLoading.value = false;
  }
};

// 删除指定文件
const handleDelete = async (record) => {
  // 添加确认弹窗
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除 "${record.filename}" 吗？此操作无法撤销。`,
    okText: '确认删除',
    okType: 'danger',
    cancelText: '取消',
    async onOk() {
      try {
        const response = await deleteFiles({
          files: [record.filename]
        });
        
        if (response.status === 'success') {
          message.success('文件已成功删除');
          // 删除成功后，刷新列表
          fetchFileList();
        } else {
          message.error(response.message || '删除文件失败');
        }
      } catch (error) {
        console.error('删除文件失败:', error);
        message.error('删除文件失败');
      }
    }
  });
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B';
  
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
};
</script>

<style scoped>
.file-manager {
  max-width: 1200px;
  margin: 0 auto;
}

.card-wrapper {
  margin-bottom: 24px;
}

.source-link {
  color: rgba(0, 0, 0, 0.85);
  text-decoration: none;
}

.source-link:hover {
  color: #1890ff;
  text-decoration: underline;
}

.file-preview {
  max-height: 500px;
  overflow-y: auto;
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
}
</style> 