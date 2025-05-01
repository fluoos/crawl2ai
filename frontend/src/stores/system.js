import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useSystemStore = defineStore('system', () => {
  // 系统配置状态
  const config = ref({
    baseUrl: 'https://api.deepseek.com',
    model: 'deepseek-chat',
    apiKey: '',
    temperature: 0.7,
    maxTokens: 4000,
    logLevel: 'info'
  });
  
  return {
    config
  };
}); 