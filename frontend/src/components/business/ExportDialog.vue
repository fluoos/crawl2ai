<template>
  <a-modal
    :visible="visible"
    title="导出配置"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
    width="600px"
  >
    <a-form :model="formState" :label-col="{ span: 6 }" :wrapper-col="{ span: 16 }">
      <a-form-item label="导出格式">
        <a-radio-group v-model:value="formState.format">
          <a-radio value="jsonl">JSONL</a-radio>
          <a-radio value="json">JSON</a-radio>
        </a-radio-group>
      </a-form-item>
      
      <a-form-item label="数据集风格">
        <a-radio-group v-model:value="formState.style">
          <a-radio value="Alpaca">Alpaca</a-radio>
          <a-radio value="ShareGPT">ShareGPT</a-radio>
          <a-radio value="Custom">自定义</a-radio>
        </a-radio-group>
      </a-form-item>
      
      <template v-if="formState.style === 'Custom'">
        <a-form-item label="自定义字段映射">
          <a-collapse>
            <a-collapse-panel key="1" header="配置字段映射">
              <a-form-item label="问题字段" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
                <a-input v-model:value="formState.template.query.field" placeholder="question" />
              </a-form-item>
              <a-form-item label="答案字段" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
                <a-input v-model:value="formState.template.response.field" placeholder="answer" />
              </a-form-item>
              <a-form-item label="类别字段" :label-col="{ span: 8 }" :wrapper-col="{ span: 14 }">
                <a-input v-model:value="formState.template.category.field" placeholder="label" />
              </a-form-item>
            </a-collapse-panel>
          </a-collapse>
        </a-form-item>
      </template>
      
      <a-form-item label="输出文件名">
        <a-input 
          v-model:value="formState.outputFile" 
          placeholder="请输入文件名" 
          :suffix="`.${formState.format}`" 
        />
      </a-form-item>
    </a-form>
    
    <template #footer>
      <a-button key="preview" type="dashed" @click="handlePreview" :loading="previewLoading">
        预览
      </a-button>
      <a-button key="cancel" @click="handleCancel">
        取消
      </a-button>
      <a-button key="submit" type="primary" @click="handleOk" :loading="loading">
        导出
      </a-button>
    </template>
    
    <a-divider v-if="previewData.length > 0" />
    
    <div v-if="previewData.length > 0" class="preview-section">
      <h3>预览数据</h3>
      <a-card>
        <pre>{{ JSON.stringify(previewData[0], null, 2) }}</pre>
      </a-card>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { message } from 'ant-design-vue';
import { previewData as fetchPreviewData, exportData } from '../../services/api';

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:visible', 'export-success']);

const formState = reactive({
  format: 'jsonl',
  style: 'Alpaca',
  inputFile: 'qa_dataset.jsonl',
  outputFile: `export_${Date.now()}`,
  template: {
    query: { field: 'question', default: '' },
    response: { field: 'answer', default: '' },
    category: { field: 'label', default: 'general' }
  }
});

const loading = ref(false);
const previewLoading = ref(false);
const previewData = ref([]);

const handlePreview = async () => {
  previewLoading.value = true;
  try {
    const response = await fetchPreviewData({
      format: formState.format,
      style: formState.style,
      inputFile: formState.inputFile,
      template: formState.style === 'Custom' ? formState.template : undefined
    });
    
    if (response && response.data && response.data.length > 0) {
      previewData.value = response.data.slice(0, 1);
      message.success('预览成功');
    } else {
      message.warning('没有可以预览的数据');
      previewData.value = [];
    }
  } catch (error) {
    message.error('预览失败');
    previewData.value = [];
  } finally {
    previewLoading.value = false;
  }
};

const handleOk = async () => {
  if (!formState.outputFile) {
    message.error('请输入输出文件名');
    return;
  }
  
  loading.value = true;
  try {
    const response = await exportData({
      format: formState.format,
      style: formState.style,
      inputFile: formState.inputFile,
      outputFile: formState.outputFile,
      template: formState.style === 'Custom' ? formState.template : undefined
    });
    
    message.success('导出成功');
    emit('export-success', response);
    emit('update:visible', false);
  } catch (error) {
    message.error('导出失败');
  } finally {
    loading.value = false;
  }
};

const handleCancel = () => {
  emit('update:visible', false);
};
</script>

<style scoped>
.preview-section {
  margin-top: 16px;
}
</style> 