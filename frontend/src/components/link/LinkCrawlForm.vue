<template>
  <a-form layout="vertical" :model="formState" @finish="onFinish">
    <a-form-item label="URL" name="url" :rules="[{ required: true, message: '请输入URL' }]">
      <a-input v-model:value="formState.url" placeholder="请输入需要爬取的URL" />
    </a-form-item>
    
    <a-form-item label="爬取深度" name="depth">
      <a-input-number v-model:value="formState.depth" :min="1" :max="10" />
    </a-form-item>
    
    <a-form-item label="爬取策略" name="strategy">
      <a-select v-model:value="formState.strategy">
        <a-select-option value="dfs">深度优先 (DFS)</a-select-option>
        <a-select-option value="bfs">广度优先 (BFS)</a-select-option>
      </a-select>
    </a-form-item>
    
    <a-form-item label="最大并发数" name="maxConcurrency">
      <a-input-number v-model:value="formState.maxConcurrency" :min="1" :max="20" />
    </a-form-item>
    
    <a-form-item>
      <a-checkbox v-model:checked="formState.forceRefresh">重新获取内容</a-checkbox>
      <template #extra>启用后将忽略已缓存的数据，重新爬取所有内容</template>
    </a-form-item>
    
    <a-form-item>
      <a-button type="primary" html-type="submit" :loading="loading">开始爬取</a-button>
    </a-form-item>
  </a-form>
</template>

<script setup>
import { reactive, defineProps, defineEmits } from 'vue';

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['submit']);

const formState = reactive({
  url: '',
  depth: 1,
  strategy: 'dfs',
  maxConcurrency: 5,
  forceRefresh: false
});

const onFinish = () => {
  emit('submit', { ...formState });
  formState.url = ''; // 清空URL输入框
};
</script> 