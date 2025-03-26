import { createApp } from 'vue';
import Antd from 'ant-design-vue';
import App from './App.vue';
import './style.css';
import 'ant-design-vue/dist/antd.css';  // 添加 antd 样式
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css';

const app = createApp(App);

// 使用 Ant Design Vue
app.use(Antd);

app.mount('#app'); 