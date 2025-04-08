# 数据集生成、大模型微调工具

这是一个数据集生成的工具，一键爬取指定域名的链接，支持把链接转换成大模型友好的markdown文件，支持将markdown文件通过ChatGPT、deepseek、Gemma等大模型转换成训练大模型可用的数据集。

## 功能特点

- 支持一键爬取指定域名的链接
- 支持把链接转换成大模型友好的markdown文件
- 支持上传.md、.txt、.pdf、.docx、.doc等文件，自动转换成.md文件
- 支持将markdown文件通过ChatGPT、deepseek、Gemma等大模型转换成训练大模型可用的数据集
- 支持导出 JSONL 和 JSON 两种输出格式
- 支持导出 Alpaca、ShareGPT 和自定义格式
- 支持预览转换结果
- 未来支持直接微调大模型

## 项目结构

```
├── app/                    # 后端应用目录
│   ├── api/                # API接口目录
│   │   ├── common.py       # 通用API
│   │   ├── converter.py    # 转换器API
│   │   ├── crawler.py      # 爬虫API
│   │   ├── deps.py         # 依赖项
│   │   ├── export.py       # 导出API
│   │   ├── files.py        # 文件操作API
│   │   └── system.py       # 系统API
│   ├── core/               # 核心功能
│   │   └── config.py       # 配置文件
│   ├── schemas/            # 数据模式
│   │   ├── crawler.py      # 爬虫模式
│   │   ├── converter.py    # 转换器模式
│   │   └── export.py       # 导出模式
│   ├── services/           # 服务层
│   │   ├── crawler_service.py    # 爬虫服务
│   │   ├── converter_service.py  # 转换服务
│   │   └── export_service.py     # 导出服务
│   ├── __init__.py         # 初始化文件
│   └── main.py             # 主程序入口
├── frontend/               # 前端目录
│   ├── src/                # 源代码
│   │   ├── api/            # API调用
│   │   ├── assets/         # 静态资源
│   │   ├── components/     # 组件目录
│   │   │   ├── business/   # 业务组件
│   │   │   ├── common/     # 通用组件
│   │   │   ├── layout/     # 布局组件
│   │   │   └── link/       # 链接组件
│   │   ├── hooks/          # 自定义钩子
│   │   ├── plugins/        # 插件
│   │   ├── router/         # 路由
│   │   ├── services/       # 服务
│   │   ├── stores/         # 状态管理
│   │   ├── utils/          # 工具函数
│   │   ├── views/          # 视图
│   │   ├── App.vue         # 主应用组件
│   │   └── main.js         # 入口文件
│   ├── index.html          # HTML入口
│   ├── package.json        # 依赖配置
│   ├── vite.config.js      # Vite配置
│   └── vue.config.js       # Vue配置
├── config/                 # 配置文件目录
├── export/                 # 导出目录
│   ├── alpaca/             # Alpaca格式导出
│   ├── sharegpt/           # ShareGPT格式导出
│   └── custom/             # 自定义格式导出
├── logs/                   # 日志目录
├── output/                 # 输出目录
│   ├── crawled_urls.json   # 爬取的URL列表(JSON格式)
│   ├── crawled_urls.txt    # 爬取的URL列表(TXT格式)
│   ├── processed_files.json# 处理过的文件
│   └── qa_dataset.jsonl    # 生成的QA数据集
├── tests/                  # 测试目录
├── upload/                 # 上传文件目录
├── venv/                   # Python虚拟环境
├── .env                    # 环境变量
├── .gitignore              # Git忽略文件配置
├── CONTRIBUTING.md         # 贡献指南
├── LICENSE                 # 许可证文件
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
pip install 'markitdown[all]'
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