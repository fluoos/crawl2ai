<template>
  <a-layout class="app-layout">
    <a-layout-header class="header">
      <div class="logo">Crawl To AI</div>
      <a-menu
        v-model:selectedKeys="selectedKeys"
        theme="dark"
        mode="horizontal"
        :style="{ lineHeight: '64px', flex: 1 }"
      >
        <a-menu-item key="links">
          <router-link to="/links">
            <LinkOutlined /> 链接管理
          </router-link>
        </a-menu-item>
        <a-menu-item key="files">
          <router-link to="/files">
            <FileOutlined /> 文件管理
          </router-link>
        </a-menu-item>
        <a-menu-item key="datasets">
          <router-link to="/datasets">
            <DatabaseOutlined /> 数据集管理
          </router-link>
        </a-menu-item>
        <a-menu-item key="config">
          <router-link to="/config">
            <SettingOutlined /> 系统配置
          </router-link>
        </a-menu-item>
      </a-menu>
    </a-layout-header>
    
    <a-layout-content class="content">
      <div class="content-container">
        <slot></slot>
      </div>
    </a-layout-content>
    
    <a-layout-footer class="footer">
      数据集生成与大模型微调工具 ©2025
    </a-layout-footer>
  </a-layout>
</template>

<script setup>
import { ref, watch } from 'vue';
import { useRoute } from 'vue-router';
import { LinkOutlined, FileOutlined, DatabaseOutlined, SettingOutlined } from '@ant-design/icons-vue';

const route = useRoute();
const selectedKeys = ref([route.path.split('/')[1] || 'links']);

watch(() => route.path, (newPath) => {
  selectedKeys.value = [newPath.split('/')[1] || 'links'];
});
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  padding: 0 24px;
  position: fixed;
  z-index: 1;
  width: 100%;
}

.logo {
  color: white;
  font-size: 18px;
  font-weight: bold;
  margin-right: 30px;
  white-space: nowrap;
}

.content {
  margin-top: 64px;
  padding: 24px;
  background: #f0f2f5;
}

.content-container {
  background: #fff;
  padding: 24px;
  min-height: calc(100vh - 64px - 70px - 48px);
  border-radius: 2px;
}

.footer {
  text-align: center;
  padding: 24px 50px;
}
</style> 