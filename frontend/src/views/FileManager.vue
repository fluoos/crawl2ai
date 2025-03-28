<template>
  <div class="file-manager">
    <a-page-header title="文件管理" subtitle="管理和处理Markdown文件" />
    
    <a-card title="上传Markdown文件" class="card-wrapper">
      <FileUploader @upload-success="handleUploadSuccess" />
    </a-card>
    
    <a-card title="Markdown文件列表" class="card-wrapper">
      <template #extra>
        <a-button
          type="primary"
          :disabled="!selectedFiles.length"
          @click="handleConvertFiles"
          :loading="convertLoading"
        >
          转换为数据集
        </a-button>
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
        <template #body-action="{ record }">
          <a-space>
            <a-button type="link" size="small" @click="previewFile(record)">
              预览
            </a-button>
            <a-button type="link" size="small" @click="handleSingleConvert(record)">
              转换
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
        <a-form-item label="使用模型">
          <a-select v-model:value="convertForm.model">
            <a-select-option value="deepseek">Deepseek</a-select-option>
            <a-select-option value="gpt-3.5-turbo">GPT-3.5</a-select-option>
            <a-select-option value="gemma">Gemma</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="输出文件名">
          <a-input v-model:value="convertForm.outputFile" placeholder="qa_dataset.jsonl" />
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
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import DataTable from '../components/common/DataTable.vue';
import FileUploader from '../components/common/FileUploader.vue';
import { getFileList, convertFilesToDataset } from '../services/api';

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
  model: 'deepseek',
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
    title: '修改时间',
    dataIndex: 'modifiedTime',
    width: 180
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
  fetchFileList();
});

// 获取文件列表
const fetchFileList = async () => {
  tableLoading.value = true;
  try {
    const response = await getFileList(pagination.current, pagination.pageSize);
    
    if (response && response.files) {
      fileList.value = response.files;
      pagination.total = response.total || response.files.length;
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
  message.success('文件上传成功');
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
    previewContent.value = `# ${record.filename}\n\n文件内容预览...\n\n这是一个示例内容，实际应用中应该通过API获取文件内容。`;
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
    const response = await convertFilesToDataset(
      convertForm.files,
      convertForm.model,
      convertForm.outputFile
    );
    
    if (response && response.status === 'success') {
      message.success('转换任务已提交，请在数据集管理中查看结果');
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

.file-preview {
  max-height: 500px;
  overflow-y: auto;
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
}
</style> 