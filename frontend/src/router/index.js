import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    redirect: '/projects'
  },
  {
    path: '/projects',
    name: 'projectManagement',
    component: () => import('../views/ProjectManager.vue'),
    meta: { title: '项目管理' }
  },
  {
    path: '/links',
    name: 'linkManagement',
    component: () => import('../views/LinkManager.vue'),
    meta: { title: '链接管理' }
  },
  {
    path: '/files',
    name: 'fileManagement',
    component: () => import('../views/FileManager.vue'),
    meta: { title: '文件管理' }
  },
  {
    path: '/datasets',
    name: 'datasetManagement',
    component: () => import('../views/DatasetManager.vue'),
    meta: { title: '数据集管理' }
  },
  {
    path: '/config',
    name: 'systemConfigManagement',
    component: () => import('../views/SystemConfig.vue'),
    meta: { title: '系统配置' }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - Crawl To AI` : 'Crawl To AI';
  // 在路由切换时，判断如果不是project管理页面，则判断本地storage中是否存在当前项目信息，如果不存在，则跳转到project管理页面
  if (to.path !== '/projects') {
    const currentProject = localStorage.getItem('currentProject');
    if (!currentProject) {
      router.push('/projects');
    }
  }
  next();
});

export default router; 