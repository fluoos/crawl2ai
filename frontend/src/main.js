import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router';
import { setupAntd } from './plugins/antd';

// 导入全局样式
import './assets/styles/main.css';

const app = createApp(App);

// 注册插件
app.use(createPinia());
app.use(router);

// 设置UI组件库
setupAntd(app);

app.mount('#app'); 