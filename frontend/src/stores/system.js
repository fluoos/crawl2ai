import { defineStore } from 'pinia';
import { getSystemConfig, updateSystemConfig } from '../services/system';

export const useSystemStore = defineStore('system', {
  state: () => ({
    config: {
      baseUrl: 'https://api.deepseek.com',
      model: 'deepseek-chat',
      apiKey: '',
      temperature: 0.7,
      maxTokens: 4000,
      logLevel: 'info'
    },
    loading: false
  }),
  
  actions: {
    async fetchConfig() {
      this.loading = true;
      try {
        const response = await getSystemConfig();
        if (response) {
          this.config = { ...this.config, ...response };
        }
        return response;
      } catch (error) {
        console.error('获取系统配置失败:', error);
      } finally {
        this.loading = false;
      }
    },
    
    async saveConfig(config) {
      this.loading = true;
      try {
        await updateSystemConfig(config);
        this.config = { ...this.config, ...config };
        return true;
      } catch (error) {
        console.error('保存系统配置失败:', error);
        return false;
      } finally {
        this.loading = false;
      }
    }
  }
}); 