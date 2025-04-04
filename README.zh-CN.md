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
├── frontend/             # 前端实现（Vue3 + Ant Design）
│   ├── index.html        # HTML入口文件
│   ├── package.json      # 前端依赖配置
│   ├── vite.config.js    # Vite配置文件
│   └── src/              # 前端源代码
│       ├── main.js       # 主入口文件
│       ├── App.vue       # 主应用组件
│       ├── components/   # 组件目录
│       │   ├── Crawler.vue      # 爬虫配置组件
│       │   ├── Converter.vue    # 转换配置组件
│       │   └── Export.vue       # 导出配置组件
│       ├── api.js        # API调用封装
│       └── style.css     # 全局样式
├── src/                  # 源代码目录
│   ├── crawl_url.py      # URL爬取实现
│   ├── crawl_to_file.py  # 爬虫到文件转换实现
│   ├── export_dataset.py # 数据集导出API实现
│   ├── file_to_dataset.py # 文件到数据集转换实现
│   ├── simple_crawler.py # 简单爬虫实现
│   └── clean_failed_files.py # 清理失败文件工具
├── tests/                # 测试目录
│   └── test.py           # 测试文件
├── output/               # 输出目录
│   ├── qa_dataset.jsonl  # 生成的QA数据集
│   └── crawled_urls.txt  # 爬取的URL列表
├── export/               # 导出目录
│   ├── alpaca/           # Alpaca格式输出
│   ├── sharegpt/         # ShareGPT格式输出
│   └── custom/           # 自定义格式输出
├── upload/               # 上传文件目录
├── config/               # 配置文件目录
│   ├── crawler.yaml      # 爬虫配置
│   └── export.yaml       # 导出配置
├── requirements.txt      # Python依赖文件
├── .env                  # 环境变量
├── .gitignore            # Git忽略文件配置
├── LICENSE               # 许可证文件
├── README.md             # 英文说明文档
└── README.zh-CN.md       # 中文说明文档
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