<template>
  <div class="system-config">
    <a-page-header title="系统配置" subtitle="配置大模型API和其他系统参数" />
    
    <a-card class="card-wrapper">
      <a-spin :spinning="loading">
        <a-form
          :model="formState"
          :label-col="{ span: 6 }"
          :wrapper-col="{ span: 12 }"
          @finish="handleSubmit"
        >
          <a-divider orientation="left">API设置</a-divider>
          
          <a-form-item 
            label="API密钥" 
            name="apiKey" 
            :rules="[{ required: true, message: '请输入API密钥' }]"
          >
            <a-input-password
              v-model:value="formState.apiKey"
              placeholder="请输入API密钥"
              :visibilityToggle="true"
            />
          </a-form-item>
          
          <a-form-item 
            label="API基础URL" 
            name="baseUrl"
            :rules="[{ required: true, message: '请输入API基础URL' }]"
          >
            <a-input
              v-model:value="formState.baseUrl"
              placeholder="请输入API基础URL，如 https://api.deepseek.com"
            />
          </a-form-item>
          
          <a-divider orientation="left">模型设置</a-divider>
          
          <a-form-item 
            label="默认模型" 
            name="model"
            :rules="[{ required: true, message: '请选择默认模型' }]"
          >
            <a-select
              v-model:value="formState.model"
              placeholder="请选择默认模型"
            >
              <a-select-option value="deepseek-chat">DeepSeek Chat</a-select-option>
              <a-select-option value="deepseek-coder">DeepSeek Coder</a-select-option>
              <a-select-option value="gpt-3.5-turbo">GPT-3.5 Turbo</a-select-option>
              <a-select-option value="gpt-4">GPT-4</a-select-option>
              <a-select-option value="gemma">Gemma</a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item 
            label="温度" 
            name="temperature"
          >
            <a-slider
              v-model:value="formState.temperature"
              :min="0"
              :max="1"
              :step="0.1"
              :tooltip-visible="true"
            />
          </a-form-item>
          
          <a-form-item 
            label="最大token数" 
            name="maxTokens"
          >
            <a-input-number
              v-model:value="formState.maxTokens"
              :min="100"
              :max="8000"
              :step="100"
              style="width: 150px"
            />
          </a-form-item>
          
          <a-divider orientation="left">系统配置</a-divider>
          
          <a-form-item 
            label="日志级别" 
            name="logLevel"
          >
            <a-select
              v-model:value="formState.logLevel"
              placeholder="请选择日志级别"
            >
              <a-select-option value="debug">Debug</a-select-option>
              <a-select-option value="info">Info</a-select-option>
              <a-select-option value="warning">Warning</a-select-option>
              <a-select-option value="error">Error</a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item :wrapper-col="{ offset: 6, span: 12 }">
            <a-button type="primary" html-type="submit" :loading="submitLoading">
              保存配置
            </a-button>
            <a-button style="margin-left: 10px" @click="resetForm">
              重置
            </a-button>
          </a-form-item>
        </a-form>
      </a-spin>
    </a-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import { message } from 'ant-design-vue';
import { useSystemStore } from '../stores/system';

const systemStore = useSystemStore();

// 表单状态
const formState = reactive({
  apiKey: '',
  baseUrl: 'https://api.deepseek.com',
  model: 'deepseek-chat',
  temperature: 0.7,
  maxTokens: 4000,
  logLevel: 'info'
});

// 状态
const loading = ref(false);
const submitLoading = ref(false);

// 初始化
onMounted(async () => {
  await fetchConfig();
});

// 获取配置
const fetchConfig = async () => {
  loading.value = true;
  try {
    await systemStore.fetchConfig();
    // 更新表单状态
    Object.assign(formState, systemStore.config);
  } catch (error) {
    console.error('获取配置失败:', error);
    message.error('获取配置失败');
  } finally {
    loading.value = false;
  }
};

// 提交表单
const handleSubmit = async () => {
  submitLoading.value = true;
  try {
    const success = await systemStore.saveConfig(formState);
    if (success) {
      message.success('配置保存成功');
    } else {
      message.error('配置保存失败');
    }
  } catch (error) {
    console.error('保存配置失败:', error);
    message.error('保存配置失败');
  } finally {
    submitLoading.value = false;
  }
};

// 重置表单
const resetForm = () => {
  Object.assign(formState, systemStore.config);
  message.info('表单已重置');
};
</script>

<style scoped>
.system-config {
  max-width: 1000px;
  margin: 0 auto;
}

.card-wrapper {
  margin-bottom: 24px;
}
</style> 