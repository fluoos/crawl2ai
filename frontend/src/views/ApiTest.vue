<template>
  <div class="api-test">
    <a-card title="API测试工具">
      <div class="health-check">
        <a-button @click="checkApiHealth" :loading="healthCheckLoading">
          检查API健康状态
        </a-button>
        <a-tag v-if="healthStatus === 'online'" color="success">在线</a-tag>
        <a-tag v-if="healthStatus === 'offline'" color="error">离线</a-tag>
      </div>
      
      <a-form layout="vertical">
        <a-form-item label="请求URL">
          <a-input v-model:value="requestUrl" placeholder="/api/crawler/status" />
        </a-form-item>
        
        <a-form-item label="请求方法">
          <a-radio-group v-model:value="requestMethod">
            <a-radio value="get">GET</a-radio>
            <a-radio value="post">POST</a-radio>
            <a-radio value="put">PUT</a-radio>
            <a-radio value="delete">DELETE</a-radio>
          </a-radio-group>
        </a-form-item>
        
        <a-form-item label="请求参数" v-if="requestMethod !== 'get'">
          <a-textarea 
            v-model:value="requestParams" 
            :rows="5" 
            placeholder='{"key": "value"}'
          />
        </a-form-item>
        
        <a-form-item>
          <a-button type="primary" @click="sendRequest" :loading="loading">
            发送请求
          </a-button>
        </a-form-item>
      </a-form>
      
      <div v-if="response" class="response-container">
        <h3>响应结果：</h3>
        <pre>{{ JSON.stringify(response, null, 2) }}</pre>
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { message } from 'ant-design-vue';
import request from '../utils/request';

const requestUrl = ref('');
const requestMethod = ref('get');
const requestParams = ref('');
const response = ref(null);
const loading = ref(false);
const healthCheckLoading = ref(false);
const healthStatus = ref(null);

const sendRequest = async () => {
  if (!requestUrl.value) {
    message.error('请输入请求URL');
    return;
  }
  
  try {
    loading.value = true;
    
    let params = {};
    if (requestMethod.value !== 'get' && requestParams.value) {
      try {
        params = JSON.parse(requestParams.value);
      } catch (e) {
        message.error('请求参数JSON格式错误');
        loading.value = false;
        return;
      }
    }
    
    const config = {
      url: requestUrl.value,
      method: requestMethod.value
    };
    
    if (requestMethod.value === 'get') {
      config.params = params;
    } else {
      config.data = params;
    }
    
    const result = await request(config);
    response.value = result;
    message.success('请求成功');
  } catch (error) {
    console.error('API测试请求失败:', error);
    response.value = {
      error: error.message,
      details: error.response ? error.response.data : '无响应详情'
    };
  } finally {
    loading.value = false;
  }
};

// 检查API健康状态
const checkApiHealth = async () => {
  healthCheckLoading.value = true;
  try {
    await request({
      url: '/',
      method: 'get'
    });
    healthStatus.value = 'online';
    message.success('API服务正常运行');
  } catch (error) {
    healthStatus.value = 'offline';
    message.error('API服务不可用，请检查后端服务');
  } finally {
    healthCheckLoading.value = false;
  }
};
</script>

<style scoped>
.api-test {
  max-width: 800px;
  margin: 20px auto;
}

.response-container {
  margin-top: 20px;
  padding: 16px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

pre {
  white-space: pre-wrap;
  word-break: break-all;
}
</style> 