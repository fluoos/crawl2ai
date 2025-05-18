<div align="center">

**A powerful Dataset Generation and Large Model Fine-tuning Tool**

[简体中文](./README.md) | [English](./README.en.md)

</div>

# Dataset Generation and Large Model Fine-tuning Tool

A tool for large model dataset generation and fine-tuning, enabling one-click crawling of links from specified domains, converting links into large model-friendly markdown files, and transforming markdown files into datasets suitable for training large models using ChatGPT, Deepseek, Gemma, and other LLMs.

## Features

- Support for deep crawling of all links from specified domains
- Support for converting links into large model-friendly markdown files
- Support for uploading .md, .txt, .pdf, .docx, .doc and other files, with automatic conversion to .md files
- Support for converting markdown files into datasets suitable for training large models using DeepSeek, ChatGPT, Gemma, and other large models
- Support for exporting in both JSONL and JSON formats
- Support for exporting in Alpaca, ShareGPT, and custom formats
- Support for previewing conversion results
- Future support for direct fine-tuning of large models

## Quick Start

### Install Dependencies

1. Backend dependencies:

```bash
# Recommended Python version is python=3.10
# Create virtual environment
python -m venv venv
# Activate environment (in PowerShell)
.\venv\Scripts\Activate.ps1
# Install all dependencies from requirements.txt
pip install -r requirements.txt
```

2. Frontend dependencies:

```bash
cd frontend
npm install
```

### Run the Project

1. Start the backend server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --ws websockets
```

2. Start the frontend development server:

```bash
cd frontend
npm run dev
```

3. Access in browser: `http://localhost:3000`

## Project Structure

```
├── app/                    # Backend application directory
│   ├── api/                # API interface directory
│   │   ├── crawler.py      # Crawler API
│   │   ├── system.py       # System API
│   │   ├── files.py        # File operations API
│   │   ├── dataset.py      # Dataset API
│   │   └── __init__.py     # Initialization file
│   ├── core/               # Core functionality
│   │   └── config.py       # Configuration file
│   ├── schemas/            # Data schemas
│   │   ├── crawler.py      # Crawler schema
│   │   ├── system.py       # System schema
│   │   ├── files.py        # Files schema
│   │   └── dataset.py      # Dataset schema
│   ├── services/           # Service layer
│   │   ├── crawler_service.py    # Crawler service
│   │   ├── system_service.py     # System service
│   │   ├── files_service.py      # Files service
│   │   └── dataset_service.py    # Dataset service
│   ├── utils/              # Utility functions
│   ├── __init__.py         # Initialization file
│   └── main.py             # Main program entry
├── frontend/               # Frontend directory
│   ├── src/                # Source code
│   │   ├── assets/         # Static resources
│   │   ├── components/     # Components directory
│   │   ├── services/       # Services
│   │   │   ├── crawler.js  # Crawler service
│   │   │   └── request.js  # Request service
│   │   ├── views/          # Views
│   │   │   ├── LinkManager.vue   # Link management page
│   │   │   └── ...         # Other view pages
│   │   ├── App.vue         # Main application component
│   │   └── main.js         # Entry file
│   ├── index.html          # HTML entry
│   ├── package.json        # Dependency configuration
│   ├── vite.config.js      # Vite configuration
│   ├── vue.config.js       # Vue configuration
│   ├── .env                # Environment variables
│   ├── .env.production     # Production environment variables
│   └── .prettierrc         # Code formatting configuration
├── config/                 # Configuration file directory
├── export/                 # Export directory
│   ├── alpaca/             # Alpaca format export
│   ├── sharegpt/           # ShareGPT format export
│   └── custom/             # Custom format export
├── logs/                   # Log directory
├── output/                 # Output directory
│   ├── crawled_urls.json   # Crawled URL list (JSON format)
│   ├── crawler_status.json # Crawler status information
│   ├── markdown/           # Converted markdown files
│   └── markdown_manager.json # Markdown file management information
├── upload/                 # Upload file directory
├── .gitignore              # Git ignore file configuration
├── README.md               # English documentation
├── README.zh-CN.md         # Chinese documentation
└── requirements.txt        # Python dependencies file
```

## Input Data Format

The input file `qa_dataset.jsonl` should be in JSONL format, with each line containing a JSON object that must include the following fields:

```json
{
  "question": "Question content",
  "answer": "Answer content",
  "label": "Label (optional)"
}
```

## Supported Output Formats

1. **Alpaca format**: Suitable for instruction fine-tuning
2. **ShareGPT format**: Suitable for dialogue fine-tuning
3. **Custom format**: Customizable field mapping

## Troubleshooting

1. If you encounter the following errors during execution:
   No module named 'markitdown'
   No module named 'onnxruntime'

   You can try installing globally:
   ```bash
   pip install 'markitdown[all]'
   pip install onnxruntime
   ```