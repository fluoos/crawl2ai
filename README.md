<div align="center">

**A powerful tool for Dataset Generation and Large Model Fine-tuning**

[简体中文](./README.zh-CN.md) | [English](./README.md)

</div>

# Dataset Generation and Large Model Fine-tuning Tool

A large model dataset generation and fine-tuning tool that can crawl links from specified domains with one click, convert links into markdown files friendly for large models, and support converting markdown files into datasets suitable for training large models using ChatGPT, deepseek, Gemma, and other large models.

## Features

- Supports deep crawling of all links from specified domains
- Supports converting links into markdown files friendly for large models
- Supports uploading .md, .txt, .pdf, .docx, .doc and other files, automatically converting them to .md files
- Supports converting markdown files into datasets suitable for training large models using ChatGPT, deepseek, Gemma, and other large models
- Supports exporting in both JSONL and JSON formats
- Supports exporting in Alpaca, ShareGPT, and custom formats
- Supports previewing conversion results
- Future support for direct fine-tuning of large models

## Project Structure

```
├── app/                    # Backend application directory
│   ├── api/                # API interface directory
│   │   ├── common.py       # Common API
│   │   ├── converter.py    # Converter API
│   │   ├── crawler.py      # Crawler API
│   │   ├── deps.py         # Dependencies
│   │   ├── export.py       # Export API
│   │   ├── files.py        # File operations API
│   │   └── system.py       # System API
│   ├── core/               # Core functionality
│   │   └── config.py       # Configuration file
│   ├── schemas/            # Data schemas
│   │   ├── crawler.py      # Crawler schema
│   │   ├── converter.py    # Converter schema
│   │   └── export.py       # Export schema
│   ├── services/           # Service layer
│   │   ├── crawler_service.py    # Crawler service
│   │   ├── converter_service.py  # Converter service
│   │   └── export_service.py     # Export service
│   ├── __init__.py         # Initialization file
│   └── main.py             # Main program entry
├── frontend/               # Frontend directory
│   ├── src/                # Source code
│   │   ├── assets/         # Static resources
│   │   ├── components/     # Components directory
│   │   │   ├── business/   # Business components
│   │   │   ├── common/     # Common components
│   │   │   ├── layout/     # Layout components
│   │   │   └── link/       # Link components
│   │   ├── hooks/          # Custom hooks
│   │   ├── plugins/        # Plugins
│   │   ├── router/         # Router
│   │   ├── services/       # Services
│   │   ├── stores/         # State management
│   │   ├── utils/          # Utility functions
│   │   ├── views/          # Views
│   │   ├── App.vue         # Main application component
│   │   └── main.js         # Entry file
│   ├── index.html          # HTML entry
│   ├── package.json        # Dependency configuration
│   ├── vite.config.js      # Vite configuration
│   └── vue.config.js       # Vue configuration
├── config/                 # Configuration file directory
├── export/                 # Export directory
│   ├── alpaca/             # Alpaca format export
│   ├── sharegpt/           # ShareGPT format export
│   └── custom/             # Custom format export
├── logs/                   # Log directory
├── output/                 # Output directory
│   ├── crawled_urls.json   # Crawled URL list (JSON format)
│   ├── crawled_urls.txt    # Crawled URL list (TXT format)
│   ├── processed_files.json# Processed files
│   └── qa_dataset.jsonl    # Generated QA dataset
├── tests/                  # Test directory
├── upload/                 # Upload file directory
├── venv/                   # Python virtual environment
├── .env                    # Environment variables
├── .gitignore              # Git ignore file configuration
├── CONTRIBUTING.md         # Contribution guide
├── LICENSE                 # License file
├── README.md               # English documentation
├── README.zh-CN.md         # Chinese documentation
└── requirements.txt        # Python dependencies file
```

## Quick Start

### Install Dependencies

1. Backend dependencies:

```bash
# Recommended Python version is 3.10
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
uvicorn app.main:app --reload
```

2. Start the frontend development server:

```bash
cd frontend
npm run dev
```

3. Access in the browser: `http://localhost:3000`

## Input Data Format

The input file `output/qa_dataset.jsonl` should be in JSONL format, with each line containing a JSON object that must include the following fields:

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