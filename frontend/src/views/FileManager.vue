<template>
  <div class="file-manager">
    <a-page-header title="文件管理" subtitle="管理和处理文件" />
    
    <a-card title="上传文件" class="card-wrapper">
      <template #extra>
        <a-space>
          <span class="smart-split-label">智能分段:</span>
          <a-switch 
            v-model:checked="smartSplitEnabled"
            checked-children="开启"
            un-checked-children="关闭"
          />
          <a-button 
            type="text" 
            size="small"
            @click="showSmartSplitConfig"
            :disabled="!smartSplitEnabled"
          >
            <SettingOutlined />
          </a-button>
        </a-space>
      </template>
      <FileUploader 
        @upload-success="handleUploadSuccess" 
        :smart-split-config="smartSplitEnabled ? smartSplitConfig : null"
      />
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
          <a-tooltip :title="record.filename">
            <a @click="handlePreviewFile(record)">{{ record.filename }}</a>
          </a-tooltip>
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
            <a-button type="link" size="small" @click="handlePreviewFile(record)">
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
    <FilePreviewModal
      v-model="previewModalVisible"
      :content="previewContent"
      :file-name="previewFile?.filename"
    />
    
    <!-- 智能分段配置弹窗 -->
    <a-modal
      v-model:visible="smartSplitConfigVisible"
      title="智能分段配置 (系统级配置)"
      @ok="saveSmartSplitConfig"
      okText="保存到系统配置"
      cancelText="取消"
      width="600px"
    >
      <a-form layout="vertical" :style="{ marginTop: '-8px' }">
        <a-alert 
          message="系统级配置" 
          description="此配置将应用于所有文件的智能分段处理，包括文件上传和链接转换。配置保存后立即生效。" 
          type="info" 
          show-icon 
          :style="{ marginBottom: '16px' }"
        />
        
        <!-- 智能分段设置 -->
        <div class="settings-section">
          <div class="section-header">
            <div class="section-indicator smart-indicator"></div>
            <span class="section-title">智能分段配置</span>
          </div>
          
          <div class="smart-split-toggle">
            <a-form-item name="enableSmartSplit" :style="{ marginBottom: '12px' }">
              <a-row justify="space-between" align="middle">
                <a-col>
                  <span class="toggle-label">启用智能分段</span>
                  <div class="form-hint" style="margin-top: 2px;">自动分段，适用于调用大模型Token有限制的场景</div>
                </a-col>
                <a-col>
                  <a-switch 
                    v-model:checked="smartSplitConfig.enableSmartSplit"
                    checked-children="开启"
                    un-checked-children="关闭"
                  />
                </a-col>
              </a-row>
            </a-form-item>
          </div>
          
          <!-- 智能分段配置 -->
          <template v-if="smartSplitConfig.enableSmartSplit">
            <div class="smart-config">
              <a-row :gutter="16" :style="{ marginBottom: '16px' }">
                <a-col :span="12">
                  <a-form-item label="最大Token数" name="maxTokens" :style="{ marginBottom: '8px' }">
                    <a-input-number 
                      v-model:value="smartSplitConfig.maxTokens"
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
                      v-model:value="smartSplitConfig.minTokens"
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
                  v-model:value="smartSplitConfig.splitStrategy"
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
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue';
import { message, Modal } from 'ant-design-vue';
import { ReloadOutlined, SettingOutlined } from '@ant-design/icons-vue';
import DataTable from '../components/common/DataTable.vue';
import FileUploader from '../components/common/FileUploader.vue';
import FilePreviewModal from '../components/common/FilePreviewModal.vue';
import { getFileList, convertToDataset, getFilePreview, deleteFiles } from '../services/files';
import { getFileStrategy, updateFileStrategy } from '../services/system';
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
const previewFile = ref(null); // 新增：用于存储当前预览文件的完整记录

// 转换相关
const convertModalVisible = ref(false);
const convertForm = reactive({
  outputFile: 'qa_dataset.jsonl',
  files: []
});

// 智能分段相关
const smartSplitEnabled = ref(true);
const smartSplitConfigVisible = ref(false);
const smartSplitConfig = reactive({
  enableSmartSplit: true,
  maxTokens: 8000,
  minTokens: 300,
  splitStrategy: 'balanced'
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
  fetchSmartSplitConfig();
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
const handlePreviewFile = async (record) => {
  previewFile.value = record; // 更新预览文件记录
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
    const requestData = {
      files: convertForm.files,
      outputFile: convertForm.outputFile
    };

    // 如果启用智能分段，添加相关参数
    if (smartSplitEnabled.value && smartSplitConfig.enableSmartSplit) {
      requestData.enableSmartSplit = true;
      requestData.maxTokens = smartSplitConfig.maxTokens;
      requestData.minTokens = smartSplitConfig.minTokens;
      requestData.splitStrategy = smartSplitConfig.splitStrategy;
    }

    const response = await convertToDataset(
      requestData.files,
      "default",  // model参数
      requestData.outputFile
    );
    
    if (response && response.status === 'success') {
      message.success('转换任务已提交，稍后更新进度结果');
      convertModalVisible.value = false;
    } else {
      message.error(response?.message || '转换失败');
    }
  } catch (error) {
    console.error('转换失败:', error);
    // message.error('转换失败');
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

// 显示智能分段配置弹窗
const showSmartSplitConfig = () => {
  smartSplitConfigVisible.value = true;
};

// 获取智能分段配置
const fetchSmartSplitConfig = async () => {
  try {
    const response = await getFileStrategy();
    if (response && response.data) {
      const data = response.data;
      // 更新智能分段配置
      smartSplitConfig.enableSmartSplit = data.enableSmartSplit !== false;
      smartSplitConfig.maxTokens = data.maxTokens || 8000;
      smartSplitConfig.minTokens = data.minTokens || 300;
      smartSplitConfig.splitStrategy = data.splitStrategy || 'balanced';
      // 同步主开关状态
      smartSplitEnabled.value = smartSplitConfig.enableSmartSplit;
    }
  } catch (error) {
    console.error('获取智能分段配置失败:', error);
  }
};

// 保存智能分段配置
const saveSmartSplitConfig = async () => {
  try {
    const configData = {
      enableSmartSplit: smartSplitConfig.enableSmartSplit,
      maxTokens: smartSplitConfig.maxTokens,
      minTokens: smartSplitConfig.minTokens,
      splitStrategy: smartSplitConfig.splitStrategy
    };
    
    const response = await updateFileStrategy(configData);
    if (response && response.status === 'success') {
      message.success('智能分段配置已保存到系统配置');
    } else {
      message.error('保存智能分段配置失败');
    }
    
    smartSplitConfigVisible.value = false;
    // 同步主开关状态
    smartSplitEnabled.value = smartSplitConfig.enableSmartSplit;
  } catch (error) {
    console.error('保存智能分段配置失败:', error);
    message.error('保存智能分段配置失败');
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

.source-link {
  color: rgba(0, 0, 0, 0.85);
  text-decoration: none;
}

.source-link:hover {
  color: #1890ff;
  text-decoration: underline;
}

/* 移除原有的file-preview样式，因为已经移到组件中了 */

.smart-split-label {
  font-size: 13px;
  color: #666;
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
  margin-right: 8px;
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