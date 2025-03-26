<template>
  <div class="container">
    <a-page-header
      title="数据集导出工具"
      sub-title="将QA数据转换为多种格式的数据集"
    />
    
    <a-card class="card">
      <a-form :model="formState" :rules="rules" :label-col="{ span: 4 }" :wrapper-col="{ span: 20 }">
        <a-form-item label="文件格式" name="fileFormat">
          <a-radio-group 
            v-model:value="formState.fileFormat" 
            button-style="solid"
            @change="handleFormatChange"
          >
            <a-radio-button v-for="format in formats" :key="format" :value="format">
              {{ format }}
            </a-radio-button>
          </a-radio-group>
        </a-form-item>
        
        <a-form-item label="数据集类型" name="datasetType">
          <a-radio-group 
            v-model:value="formState.datasetType" 
            button-style="solid"
            @change="handleTypeChange"
          >
            <a-radio-button v-for="style in styles" :key="style" :value="style">
              {{ style }}
            </a-radio-button>
          </a-radio-group>
        </a-form-item>
        
        <a-form-item label="文件名">
          <a-input 
            v-model:value="formState.filename" 
            placeholder="输入文件名（不含扩展名）"
            :addon-after="fileExtension"
          />
        </a-form-item>
        
        <!-- 自定义模板配置 -->
        <template v-if="formState.datasetType === 'Custom'">
          <a-form-item label="自定义模板">
            <a-card size="small">
              <template #extra>
                <a-button type="link" @click="addCustomField">添加字段</a-button>
              </template>
              
              <div v-for="(field, index) in formState.customFields" :key="index" class="custom-template-field">
                <a-input 
                  v-model:value="field.key" 
                  placeholder="字段名" 
                  style="width: 150px"
                />
                <a-select 
                  v-model:value="field.sourceField" 
                  style="width: 150px"
                  placeholder="来源字段"
                >
                  <a-select-option value="question">问题 (question)</a-select-option>
                  <a-select-option value="answer">答案 (answer)</a-select-option>
                  <a-select-option value="label">标签 (label)</a-select-option>
                </a-select>
                <a-input 
                  v-model:value="field.defaultValue" 
                  placeholder="默认值" 
                  style="width: 150px"
                />
                <a-button danger type="text" @click="removeCustomField(index)">
                  <template #icon><delete-outlined /></template>
                </a-button>
              </div>
            </a-card>
          </a-form-item>
        </template>
      </a-form>
      
      <!-- 格式示例 -->
      <a-divider orientation="left">格式示例</a-divider>
      <div v-if="examples && currentStyleExample">
        <a-typography-paragraph>
          {{ examples[formState.datasetType]?.description || '自定义模板配置' }}
        </a-typography-paragraph>
        
        <!-- 自定义模板显示模板结构和示例数据 -->
        <template v-if="formState.datasetType === 'Custom'">
          <a-divider>模板结构</a-divider>
          <pre>{{ JSON.stringify(currentStyleExample.template, null, 2) }}</pre>
          <a-divider>数据示例</a-divider>
          <pre>{{ JSON.stringify(currentStyleExample.example, null, 2) }}</pre>
        </template>
        <template v-else>
          <pre>{{ JSON.stringify(currentStyleExample, null, 2) }}</pre>
        </template>
      </div>
      
      <!-- 操作按钮 -->
      <div class="action-buttons">
        <a-space>
          <a-button @click="resetForm">重置</a-button>
          <a-button type="primary" @click="handlePreview" :loading="previewLoading" :disabled="!canPreview">预览</a-button>
          <a-button type="primary" @click="handleExport" :loading="exportLoading" :disabled="!canExport">导出</a-button>
          <a-button @click="openBatchExport">批量导出</a-button>
        </a-space>
      </div>
    </a-card>
    
    <!-- 预览结果 -->
    <a-card v-if="previewData.length > 0" title="预览结果" class="card table-card">
      <a-table
        :dataSource="previewData"
        :columns="previewColumns"
        :loading="previewLoading"
        :pagination="{
          total: totalCount,
          current: previewCurrentPage,
          pageSize: previewPageSize,
          showSizeChanger: true,
          showQuickJumper: true,
          pageSizeOptions: ['10', '20', '50', '100'],
          showTotal: total => `共 ${total} 条数据`,
          onChange: handlePageChange,
          onShowSizeChange: handlePageSizeChange
        }"
        size="middle"
        :scroll="{ x: 800 }"
      >
        <template #bodyCell="{ column, record }">
          <!-- Alpaca 格式特定列渲染 -->
          <template v-if="column.dataIndex === 'instruction' || column.dataIndex === 'output' || column.dataIndex === 'input'">
            <a-tooltip :title="record[column.dataIndex]" :mouseEnterDelay="0.5">
              <div class="cell-content truncated">{{ record[column.dataIndex] }}</div>
            </a-tooltip>
          </template>
          
          <!-- 标签列渲染 -->
          <template v-else-if="column.key === 'label'">
            <a-tag v-if="record.label" color="blue">{{ record.label }}</a-tag>
            <a-tag v-else-if="record.metadata && record.metadata.label" color="blue">
              {{ record.metadata.label }}
            </a-tag>
          </template>
          
          <!-- ShareGPT 格式特定列渲染 -->
          <template v-else-if="column.key === 'human_content'">
            <a-tooltip :title="record.human_content" :mouseEnterDelay="0.5">
              <div class="cell-content truncated">{{ record.human_content }}</div>
            </a-tooltip>
          </template>
          
          <template v-else-if="column.key === 'assistant_content'">
            <a-tooltip :title="record.assistant_content" :mouseEnterDelay="0.5">
              <div class="cell-content truncated">{{ record.assistant_content }}</div>
            </a-tooltip>
          </template>
          
          <!-- 默认内容渲染 (用于未识别的列或通用内容列) -->
          <template v-else-if="column.key === 'content'">
            <a-tooltip :title="JSON.stringify(omitId(record), null, 2)" :mouseEnterDelay="0.5">
              <pre class="preview-content truncated">{{ JSON.stringify(omitId(record), null, 2) }}</pre>
            </a-tooltip>
          </template>
          
          <!-- 自定义类型的动态字段渲染 -->
          <template v-else-if="formState.datasetType === 'Custom' && record[column.dataIndex] !== undefined">
            <a-tooltip :title="record[column.dataIndex]" :mouseEnterDelay="0.5">
              <div class="cell-content truncated">{{ record[column.dataIndex] }}</div>
            </a-tooltip>
          </template>
        </template>
      </a-table>
    </a-card>
    
    <!-- 导出结果 -->
    <a-card v-if="exportResult" title="导出结果" class="card">
      <a-result 
        status="success" 
        title="数据集导出成功"
        :sub-title="`共导出 ${exportResult.count} 条数据`"
      >
        <template #extra>
          <a-button type="primary" @click="handleDownload">
            下载文件
          </a-button>
        </template>
        
        <div class="result-info">
          <a-descriptions :column="1" bordered>
            <a-descriptions-item label="文件名">
              {{ exportResult.filename }}
            </a-descriptions-item>
            <a-descriptions-item label="文件路径">
              {{ exportResult.path }}
            </a-descriptions-item>
          </a-descriptions>
        </div>
      </a-result>
    </a-card>
    
    <!-- 全局消息提示 -->
    <a-modal v-model:visible="errorVisible" title="错误" @ok="errorVisible = false">
      <p>{{ errorMessage }}</p>
    </a-modal>
    
    <!-- 新增功能: 数据统计面板 -->
    <a-card v-if="dataStats" title="数据统计" class="card">
      <a-row :gutter="16">
        <a-col :span="8">
          <a-statistic title="总数据条数" :value="dataStats.totalCount" />
        </a-col>
        <a-col :span="8">
          <a-statistic title="有效数据条数" :value="dataStats.validCount" />
        </a-col>
        <a-col :span="8">
          <a-statistic title="平均字符长度" :value="dataStats.avgLength" :precision="2" />
        </a-col>
      </a-row>
    </a-card>
    
    <!-- 新增功能: 批量导出 -->
    <a-modal v-model:visible="batchExportVisible" title="批量导出" @ok="handleBatchExport">
      <a-form layout="vertical">
        <a-form-item label="选择格式">
          <a-checkbox-group v-model:value="batchExportFormats">
            <a-checkbox v-for="format in formats" :key="format" :value="format">
              {{ format }}
            </a-checkbox>
          </a-checkbox-group>
        </a-form-item>
        
        <a-form-item label="选择风格">
          <a-checkbox-group v-model:value="batchExportStyles">
            <a-checkbox v-for="style in styles" :key="style" :value="style">
              {{ style }}
            </a-checkbox>
          </a-checkbox-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, reactive } from 'vue';
import { DeleteOutlined } from '@ant-design/icons-vue';
import * as api from './api';
import { message } from 'ant-design-vue';

// 将状态按功能分组
// 基础状态
const formats = ref([]);
const styles = ref([]);
const examples = ref({});
const errorVisible = ref(false);
const errorMessage = ref('');

// 表单状态 - 使用 reactive 更合适
const formState = reactive({
  fileFormat: 'jsonl',
  datasetType: 'Alpaca',
  filename: '',
  template: {},
  customFields: []
});

// 预览状态
const previewData = ref([]);
const previewLoading = ref(false);
const previewPageSize = ref(20);
const previewCurrentPage = ref(1);
const totalCount = ref(0);
const convertedCount = ref(0);

// 导出状态
const exportLoading = ref(false);
const exportResult = ref(null);

// 统计数据
const dataStats = ref(null);

// 批量导出状态
const batchExportVisible = ref(false);
const batchExportFormats = ref([]);
const batchExportStyles = ref([]);

// 添加计算属性处理文件后缀
const fileExtension = computed(() => {
  return formState.fileFormat || 'jsonl';
});

// 是否可以预览
const canPreview = computed(() => {
  return !!formState.fileFormat && !!formState.datasetType;
});

// 是否可以导出
const canExport = computed(() => {
  return !!formState.fileFormat && !!formState.datasetType;
});

// 表格列配置，添加 ellipsis 和 tooltip 配置
const previewColumns = computed(() => {
  const baseColumns = [
    {
      title: '序号',
      dataIndex: 'index',
      width: 80,
      fixed: 'left',
      align: 'center'
    }
  ];

  // 根据不同的数据集类型添加对应的列
  if (formState.datasetType === 'Alpaca') {
    return [
      ...baseColumns,
      {
        title: '问题',
        dataIndex: 'instruction',
        width: '35%',
        ellipsis: true,
        customCell: () => ({ class: 'limited-height-cell' })
      },
      {
        title: '输入',
        dataIndex: 'input',
        width: '10%',
        ellipsis: true,
        customCell: () => ({ class: 'limited-height-cell' })
      },
      {
        title: '回答',
        dataIndex: 'output',
        width: '40%',
        ellipsis: true,
        customCell: () => ({ class: 'limited-height-cell' })
      },
      {
        title: '标签',
        key: 'label',
        width: '15%',
        ellipsis: true
      }
    ];
  } else if (formState.datasetType === 'ShareGPT') {
    return [
      ...baseColumns,
      {
        title: '问题',
        key: 'human_content',
        width: '40%',
        ellipsis: true,
        customCell: () => ({ class: 'limited-height-cell' })
      },
      {
        title: '回答',
        key: 'assistant_content',
        width: '45%',
        ellipsis: true,
        customCell: () => ({ class: 'limited-height-cell' })
      },
      {
        title: '标签',
        key: 'label',
        width: '15%',
        ellipsis: true
      }
    ];
  } else if (formState.datasetType === 'Custom') {
    // 为自定义格式生成动态列
    const customColumns = Object.keys(formState.template).map(key => ({
      title: key,
      dataIndex: key,
      ellipsis: true,
      customCell: () => ({ class: 'limited-height-cell' })
    }));
    
    return [...baseColumns, ...customColumns];
  }
  
  // 默认情况下返回通用列
  return [
    ...baseColumns,
    {
      title: '内容',
      key: 'content',
      width: '100%',
      ellipsis: true,
      customCell: () => ({ class: 'limited-height-cell' })
    }
  ];
});

// 计算当前风格的示例数据
const currentStyleExample = computed(() => {
  if (!examples.value) return null;
  
  if (formState.datasetType === 'Custom') {
    // 为自定义模板生成示例
    const template = {};
    const exampleData = {
      question: "示例问题",
      answer: "示例答案",
      label: "示例标签"
    };
    
    formState.customFields.forEach(field => {
      if (field.key) {
        template[field.key] = {
          field: field.sourceField,
          default: field.defaultValue
        };
      }
    });
    
    // 生成示例数据
    const example = {};
    Object.entries(template).forEach(([key, config]) => {
      example[key] = exampleData[config.field] || config.default;
    });
    
    // 更新 formState 中的 template
    formState.template = template;
    return {
      template: template,
      example: example
    };
  }
  
  return examples.value[formState.datasetType]?.example || null;
});

// 获取支持的格式和风格
const fetchFormats = async () => {
  try {
    const data = await api.getFormats();
    formats.value = data.formats;
    styles.value = data.styles;
  } catch (error) {
    showError(error.message);
  }
};

// 获取格式示例
const fetchExamples = async () => {
  try {
    examples.value = await api.getExamples();
  } catch (error) {
    showError(error.message);
  }
};

// 获取数据统计
const fetchDataStats = async () => {
  try {
    const data = await api.getDataStats();
    if (data) {
      dataStats.value = data;
    }
  } catch (error) {
    console.warn('获取数据统计失败:', error);
    // 不显示错误提示，因为这是非核心功能
    dataStats.value = null;
  }
};

// 修改预览方法
const handlePreview = async () => {
  if (!canPreview.value) {
    showError('请选择导出格式和数据集类型');
    return;
  }

  // 重置状态
  previewLoading.value = true;
  previewCurrentPage.value = 1;
  previewData.value = [];
  
  try {
    // 添加分页参数请求数据
    await fetchPageData(1, previewPageSize.value);
    message.success(`预览成功，共 ${totalCount.value} 条数据，已转换 ${convertedCount.value} 条`);
  } catch (error) {
    console.error('预览数据失败:', error);
    showError(typeof error === 'string' ? error : error.message);
  } finally {
    previewLoading.value = false;
  }
};

// 新增：从后端获取指定页面的数据
const fetchPageData = async (page, pageSize) => {
  console.log(`请求第 ${page} 页数据，每页 ${pageSize} 条`);
  
  try {
    // 明确指定分页参数
    const data = await api.previewData({
      format: formState.fileFormat,
      style: formState.datasetType,
      template: formState.template,
      page: page,
      pageSize: pageSize
    });
    
    // 验证数据
    if (!data || !data.preview || !Array.isArray(data.preview)) {
      throw new Error('返回数据格式不正确');
    }
    
    console.log(`获取到 ${data.preview.length} 条预览数据`);
    
    // 更新总数据计数
    totalCount.value = data.totalCount || 0;
    convertedCount.value = data.convertedCount || 0;
    
    // 处理当前页数据，格式化为表格适用的结构
    previewData.value = formatPreviewData(data.preview, formState.datasetType);
    
    return data;
  } catch (error) {
    console.error('获取页面数据失败:', error);
    throw error;
  }
};

// 修改分页处理方法
const handlePageChange = async (page, pageSize) => {
  console.log(`页码变更: page=${page}, pageSize=${pageSize}`);
  
  previewCurrentPage.value = page;
  
  // 检查页面大小是否变化
  if (previewPageSize.value !== pageSize) {
    previewPageSize.value = pageSize;
  }
  
  previewLoading.value = true;
  
  try {
    // 请求新页面的数据
    const result = await fetchPageData(page, pageSize);
    console.log(`成功获取第 ${page} 页数据，共 ${result.preview.length} 条记录`);
  } catch (error) {
    console.error('分页处理错误:', error);
    showError(`分页处理出错: ${error.message}`);
  } finally {
    previewLoading.value = false;
  }
};

// 处理每页条数变化
const handlePageSizeChange = (current, size) => {
  console.log(`每页条数变更: current=${current}, size=${size}`);
  previewPageSize.value = size;
  handlePageChange(1, size);  // 切换每页条数时返回第一页
};

// 导出数据
const handleExport = async () => {
  if (!canExport.value) {
    showError('请选择导出格式和数据集类型');
    return;
  }

  // 处理文件名
  const filename = formState.filename.trim() || `dataset_${Date.now()}`;
  
  exportLoading.value = true;
  try {
    const data = await api.exportData({
      format: formState.fileFormat,
      style: formState.datasetType,
      filename: filename, // 不包含扩展名的文件名
      template: formState.template
    });
    
    if (!data || !data.filename) {
      throw new Error('导出结果格式不正确');
    }
    
    exportResult.value = data;
    message.success(`导出成功！共导出 ${data.count || 0} 条数据`);
  } catch (error) {
    handleGlobalError(error);
  } finally {
    exportLoading.value = false;
  }
};

// 下载文件
const handleDownload = () => {
  if (!exportResult.value || !exportResult.value.downloadUrl) {
    showError('下载地址不可用');
    return;
  }
  
  window.open(exportResult.value.downloadUrl, '_blank');
  message.info('正在下载文件...');
};

// 修改重置表单方法
const resetForm = () => {
  // 重置表单状态
  Object.assign(formState, {
    fileFormat: 'jsonl',
    datasetType: 'Alpaca',
    filename: '',
    template: {},
    customFields: []
  });
  
  // 重置预览数据
  previewData.value = [];
  previewCurrentPage.value = 1;
  totalCount.value = 0;
  convertedCount.value = 0;
  
  // 重置导出结果
  exportResult.value = null;
  
  message.info('已重置表单');
};

// 显示错误
const showError = (msg) => {
  console.error('错误:', msg);
  errorMessage.value = msg || '发生未知错误';
  errorVisible.value = true;
};

// 全局错误处理
const handleGlobalError = (error) => {
  console.error('全局错误:', error);
  if (error?.response?.data) {
    showError(`服务器错误: ${error.response.data}`);
  } else if (error.message) {
    showError(error.message);
  } else {
    showError('发生未知错误');
  }
};

// 格式变更处理
const handleFormatChange = () => {
  console.log(`文件格式变更为: ${formState.fileFormat}`);
  // 清除预览和导出结果
  previewData.value = [];
  exportResult.value = null;
};

// 风格变更处理
const handleTypeChange = () => {
  console.log(`数据集类型变更为: ${formState.datasetType}`);
  // 清除预览和导出结果
  previewData.value = [];
  exportResult.value = null;
  
  // 对于自定义类型，重置模板
  if (formState.datasetType === 'Custom') {
    formState.template = {};
    formState.customFields = [];
  }
};

// 添加自定义字段
const addCustomField = () => {
  formState.customFields.push({
    key: '',
    sourceField: 'question',
    defaultValue: ''
  });
};

// 移除自定义字段
const removeCustomField = (index) => {
  if (index >= 0 && index < formState.customFields.length) {
    formState.customFields.splice(index, 1);
    // 更新模板
    updateCustomTemplate();
  }
};

// 更新自定义模板
const updateCustomTemplate = () => {
  const template = {};
  const validFields = formState.customFields.filter(field => field.key.trim());
  
  validFields.forEach(field => {
    template[field.key] = {
      field: field.sourceField,
      default: field.defaultValue
    };
  });
  
  formState.template = template;
};

// 打开批量导出对话框
const openBatchExport = () => {
  batchExportFormats.value = [formState.fileFormat];
  batchExportStyles.value = [formState.datasetType];
  batchExportVisible.value = true;
};

// 批量导出处理
const handleBatchExport = async () => {
  if (batchExportFormats.value.length === 0 || batchExportStyles.value.length === 0) {
    showError('请至少选择一种格式和类型');
    return;
  }

  const filename = formState.filename.trim() || `dataset_${Date.now()}`;
  exportLoading.value = true;
  
  try {
    const result = await api.batchExport({
      formats: batchExportFormats.value,
      styles: batchExportStyles.value,
      filename: filename
    });
    
    message.success('批量导出成功！');
    batchExportVisible.value = false;
    
    // 可以进一步处理结果，例如显示下载链接列表
    if (result && result.files && Array.isArray(result.files)) {
      // 处理下载链接...
    }
  } catch (error) {
    handleGlobalError(error);
  } finally {
    exportLoading.value = false;
  }
};

// 添加表单验证规则
const rules = {
  fileFormat: [{ required: true, message: '请选择文件格式' }],
  datasetType: [{ required: true, message: '请选择数据集类型' }]
};

// 添加一个工具函数来移除 id 字段
const omitId = (item) => {
  const { id, ...rest } = item;
  return rest;
};

// 添加数据格式化函数处理不同类型的数据
const formatPreviewData = (data, type) => {
  if (!Array.isArray(data)) return [];
  
  return data.map((item, index) => {
    // 基础字段，所有记录都有
    const formattedItem = {
      key: `item-${index}`,
      index: index + 1
    };
    
    if (type === 'Alpaca') {
      // 处理 Alpaca 格式
      formattedItem.instruction = item.instruction || '';
      formattedItem.input = item.input || '';
      formattedItem.output = item.output || '';
      
      // 处理标签，可能在 metadata 中
      if (item.metadata && item.metadata.label) {
        formattedItem.label = item.metadata.label;
      }
    } else if (type === 'ShareGPT') {
      // 处理 ShareGPT 格式
      if (item.conversations && Array.isArray(item.conversations)) {
        const humanMsg = item.conversations.find(msg => msg.role === 'human');
        const assistantMsg = item.conversations.find(msg => msg.role === 'assistant');
        
        formattedItem.human_content = humanMsg ? humanMsg.content : '';
        formattedItem.assistant_content = assistantMsg ? assistantMsg.content : '';
      }
      
      // 处理标签，可能在 metadata 中
      if (item.metadata && item.metadata.label) {
        formattedItem.label = item.metadata.label;
      }
    } else if (type === 'Custom') {
      // 处理自定义格式，直接合并所有字段
      Object.assign(formattedItem, item);
    } else {
      // 未知格式，保留原始数据
      formattedItem.originalData = item;
    }
    
    return formattedItem;
  });
};

// 组件挂载时初始化
onMounted(() => {
  console.log('组件已挂载，开始初始化');
  Promise.all([
    fetchFormats(),
    fetchExamples(),
    fetchDataStats()
  ]).then(() => {
    console.log('初始化完成');
  }).catch(error => {
    console.error('初始化出错:', error);
  });
});
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.card {
  margin-bottom: 20px;
}

.table-card ::v-deep(.ant-card-body){
  padding: 0;
}

pre {
  background-color: #f5f5f5;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
}

.statistics {
  margin-bottom: 20px;
  display: flex;
  gap: 20px;
}

.statistic-card {
  flex: 1;
  padding: 16px;
  background: #fafafa;
  border-radius: 4px;
}

/* 添加自定义模板字段的样式 */
.custom-template-field {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  align-items: center;
}

.custom-template-field:last-child {
  margin-bottom: 0;
}

/* 添加操作按钮样式 */
.action-buttons {
  margin-top: 24px;
  text-align: right;
}

/* 修改预览内容样式 */
.preview-content {
  margin: 0;
  padding: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  line-height: 1.4;
  white-space: pre-wrap;
  word-wrap: break-word;
  min-height: 36px;
}

/* 添加响应式样式 */
@media (max-width: 768px) {
  .container {
    padding: 10px;
  }
  
  .custom-template-field {
    flex-direction: column;
    align-items: stretch;
  }
  
  .custom-template-field > * {
    width: 100% !important;
    margin-bottom: 8px;
  }
}

/* 添加错误高亮 */
.error {
  border-color: #ff4d4f;
  background-color: #fff2f0;
}

/* 改进加载状态 */
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

/* 修改单元格内容样式，适应更小的行高 */
.cell-content {
  white-space: pre-line;
  word-break: break-word;
  background-color: #f9f9f9;
  border-radius: 4px;
  line-height: 1.4;
  min-height: 36px;
}

/* 调整表格单元格高度为固定的52px */
::v-deep(.ant-table-cell) {
  vertical-align: top;
  padding: 6px 12px !important;
  height: 52px !important;
  max-height: 52px;
  box-sizing: border-box;
}

/* 两行显示截断的样式，调整行高 */
.truncated {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 18px;
}

/* 针对自定义cell类添加样式 */
::v-deep(.limited-height-cell) {
  vertical-align: top;
  padding: 6px 12px;
  height: 52px;
}

/* 确保表格整体行间距一致 */
::v-deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid #f0f0f0;
  height: 52px;
}

/* 修改tooltip最大宽度 */
::v-deep(.ant-tooltip-inner) {
  max-width: 500px;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
}

/* 移除表格行的默认悬停背景效果 */
::v-deep(.ant-table-tbody > tr.ant-table-row:hover > td) {
  background: unset;
}

/* 移除单元格内容的悬停效果 */
::v-deep(.ant-table-row:hover) .cell-content {
  background-color: #f9f9f9;
}
</style> 