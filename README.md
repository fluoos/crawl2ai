<div align="center">

**一个强大的数据集生成和大模型微调工具**

[简体中文](./README.md) | [English](./README.en.md)

</div>

# 数据集生成、大模型微调工具

大模型数据集生成和微调工具，一键爬取指定域名的链接，支持把链接转换成大模型友好的markdown文件，支持将markdown文件通过ChatGPT、deepseek、Gemma等大模型转换成训练大模型可用的数据集。

## 功能特点

- 支持深度爬取指定域名的所有链接
- 支持将链接转换成大模型友好的markdown文件
- 支持上传.md、.txt、.pdf、.docx、.doc等文件，自动转换成.md文件
- 支持通过DeepSeek、ChatGPT、Gemma等大模型将markdown转换成训练大模型可用的数据集
- 支持导出 JSONL 和 JSON 两种输出格式
- 支持导出 Alpaca、ShareGPT 和自定义格式
- 支持预览转换结果
- 未来支持直接微调大模型

## 项目结构

```
├── app/                    # 后端应用目录
│   ├── api/                # API接口目录
│   │   ├── crawler.py      # 爬虫API
│   │   ├── system.py       # 系统API
│   │   ├── files.py        # 文件操作API
│   │   ├── dataset.py      # 数据集API
│   │   └── __init__.py     # 初始化文件
│   ├── core/               # 核心功能
│   │   └── config.py       # 配置文件
│   ├── schemas/            # 数据模式
│   │   ├── crawler.py      # 爬虫模式
│   │   ├── system.py       # 系统模式
│   │   ├── files.py        # 文件模式
│   │   └── dataset.py      # 数据集模式
│   ├── services/           # 服务层
│   │   ├── crawler_service.py    # 爬虫服务
│   │   ├── system_service.py     # 系统服务
│   │   ├── files_service.py      # 文件服务
│   │   └── dataset_service.py    # 数据集服务
│   ├── utils/              # 工具函数
│   ├── __init__.py         # 初始化文件
│   └── main.py             # 主程序入口
├── frontend/               # 前端目录
│   ├── src/                # 源代码
│   │   ├── assets/         # 静态资源
│   │   ├── components/     # 组件目录
│   │   ├── services/       # 服务
│   │   │   ├── crawler.js  # 爬虫服务
│   │   │   └── request.js  # 请求服务
│   │   ├── views/          # 视图
│   │   │   ├── LinkManager.vue   # 链接管理页面
│   │   │   └── ...         # 其他视图页面
│   │   ├── App.vue         # 主应用组件
│   │   └── main.js         # 入口文件
│   ├── index.html          # HTML入口
│   ├── package.json        # 依赖配置
│   ├── vite.config.js      # Vite配置
│   ├── vue.config.js       # Vue配置
│   ├── .env                # 环境变量
│   ├── .env.production     # 生产环境变量
│   └── .prettierrc         # 代码格式配置
├── config/                 # 配置文件目录
├── export/                 # 导出目录
│   ├── alpaca/             # Alpaca格式导出
│   ├── sharegpt/           # ShareGPT格式导出
│   └── custom/             # 自定义格式导出
├── logs/                   # 日志目录
├── output/                 # 输出目录
│   ├── crawled_urls.json   # 爬取的URL列表(JSON格式)
│   ├── crawler_status.json # 爬虫状态信息
│   ├── markdown/           # 转换后的Markdown文件
│   └── markdown_manager.json # Markdown文件管理信息
├── upload/                 # 上传文件目录
├── .gitignore              # Git忽略文件配置
├── README.md               # 英文说明文档
├── README.zh-CN.md         # 中文说明文档
└── requirements.txt        # Python依赖文件
```

## 快速开始

### 安装依赖

1. 后端依赖：

```bash
# 建议运行python的版本python=3.10
# 创建虚拟环境
python -m venv venv
# 激活环境（在PowerShell中）
.\venv\Scripts\Activate.ps1
# 从requirements.txt安装所有依赖
pip install -r requirements.txt
```

2. 前端依赖：

```bash
cd frontend
npm install
```

### 运行项目

1. 启动后端服务器：

```bash
uvicorn app.main:app --reload
```

2. 启动前端开发服务器：

```bash
cd frontend
npm run dev
```

3. 在浏览器中访问：`http://localhost:3000`

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

## 常见问题处理

1. 运行过程如果提示下面报错
No module named 'markitdown'
No module named 'onnxruntime'

可以尝试在全局安装
```bash
pip install 'markitdown[all]'
pip install onnxruntime
```