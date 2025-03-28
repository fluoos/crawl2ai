// 全量引入方式
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/antd.min.css';

export function setupAntd(app) {
  app.use(Antd);
}

// 如果需要按需引入，可以使用下面的方式（取消注释并注释掉上面的代码）
/*
import {
  Button,
  Table,
  Form,
  Input,
  Select,
  Modal,
  Menu,
  Layout,
  Card,
  Spin,
  Pagination,
  ConfigProvider,
  // 按需添加其他组件
} from 'ant-design-vue';
import 'ant-design-vue/es/button/style/css';
import 'ant-design-vue/es/table/style/css';
// 引入其他组件样式...

export function setupAntd(app) {
  app.use(Button);
  app.use(Table);
  app.use(Form);
  app.use(Input);
  app.use(Select);
  app.use(Modal);
  app.use(Menu);
  app.use(Layout);
  app.use(Card);
  app.use(Spin);
  app.use(Pagination);
  app.use(ConfigProvider);
  // 注册其他组件...
}
*/ 