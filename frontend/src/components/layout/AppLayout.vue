<template>
  <a-layout class="app-layout">
    <a-layout-header class="header">
      <div class="logo">Crawl To AI</div>
      <a-menu
        v-if="!isProjectPage"
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
      <div v-if="currentProject && !isProjectPage" class="project-info">
        <a-tooltip placement="bottom" title="返回项目管理">
          <a-button 
            type="primary" 
            shape="circle" 
            size="middle" 
            @click="navigateToProject"
            class="back-btn"
          >
            <template #icon><RollbackOutlined /></template>
          </a-button>
        </a-tooltip>
        <div class="project-header">
          <span class="project-label">当前项目:</span>
          <span class="project-name" :title="currentProject.name">
            <ProjectOutlined /> {{ currentProject.name }}
          </span>
        </div>
      </div>
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
import { ref, watch, computed } from 'vue';
import { useRoute } from 'vue-router';
import { useRouter } from 'vue-router';
import { 
  LinkOutlined, 
  FileOutlined, 
  DatabaseOutlined, 
  SettingOutlined, 
  RollbackOutlined,
  ProjectOutlined
} from '@ant-design/icons-vue';

const route = useRoute();
const router = useRouter();
const selectedKeys = ref([route.path.split('/')[1] || 'links']);

const currentProject = ref(null);

const isProjectPage = computed(() => {
  return route.path.startsWith('/projects');
});

const navigateToProject = () => {
  // 删除本地storage中的当前项目信息
  localStorage.removeItem('currentProject');
  router.push('/projects');
};

watch(() => route.path, (newPath) => {
  selectedKeys.value = [newPath.split('/')[1] || 'links'];
  if (!isProjectPage.value) {
    // 判断本地storage中是否存在当前项目信息，如果不存在，则跳转到项目管理页
    const projectStr = localStorage.getItem('currentProject');
    currentProject.value = projectStr ? JSON.parse(projectStr) : null;
  }
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
  z-index: 100;
  width: 100%;
}

.logo {
  color: white;
  font-size: 18px;
  font-weight: bold;
  margin-right: 30px;
  white-space: nowrap;
}

.project-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.back-btn {
  transition: all 0.3s;
}

.back-btn:hover {
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

.project-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 12px;
  border-radius: 16px;
  max-width: 300px;
  height: 32px;
}

.project-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

.project-name {
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}

.dataset-count {
  margin-left: 4px;
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