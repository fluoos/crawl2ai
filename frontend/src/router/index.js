import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    redirect: '/links'
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
  next();
});

export default router; 