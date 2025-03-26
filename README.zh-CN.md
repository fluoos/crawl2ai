# 数据集生成、大模型微调工具

这是一个数据集生成的工具，一键爬取指定域名的链接，支持把链接转换成大模型友好的markdown文件，支持将markdown文件通过ChatGPT、deepseek、Gemma等大模型转换成训练大模型可用的数据集。

## 功能特点

- 支持一键爬取指定域名的链接
- 支持把链接转换成大模型友好的markdown文件
- 支持将markdown文件通过ChatGPT、deepseek、Gemma等大模型转换成训练大模型可用的数据集
- 支持导出 JSONL 和 JSON 两种输出格式
- 支持导出 Alpaca、ShareGPT 和自定义格式
- 支持预览转换结果

## 项目结构

```
├── export_dataset.py     # 后端实现（Flask API）
├── frontend/             # 前端实现（Vue3 + Ant Design）
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── api.js
│       └── style.css
├── output/               # 输入文件目录
│   └── qa_dataset.jsonl  # 原始QA数据
└── export/               # 输出文件目录
```

## 快速开始

### 安装依赖

1. 后端依赖：

```bash
pip install flask flask-cors
```

2. 前端依赖：

```bash
cd frontend
npm install
```

### 运行项目

1. 启动后端服务器：

```bash
python export_dataset.py
```

2. 启动前端开发服务器：

```bash
cd frontend
npm run dev
```

3. 在浏览器中访问：`http://localhost:3000`

## 使用方法

1. 在界面中选择导出格式（JSONL或JSON）
2. 选择数据集风格（Alpaca、ShareGPT或自定义）
3. 如果选择自定义格式，配置字段映射
4. 输入输出文件名
5. 点击"预览"按钮查看转换结果
6. 点击"导出"按钮生成文件
7. 导出完成后，点击"下载"按钮获取文件

## 输入数据格式

输入文件 `output/qa_dataset.jsonl` 应为JSONL格式，每行包含一个JSON对象，要求包含以下字段：

```json
{
  "question": "问题内容",
  "answer": "答案内容",
  "label": "标签（可选）"
}
```

## 支持的输出格式

1. **Alpaca格式**：适用于指令微调
2. **ShareGPT格式**：适用于对话微调
3. **自定义格式**：可自定义字段映射