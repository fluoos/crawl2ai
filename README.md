<div align="center">

**A powerful tool for Dataset Generation and Large Model Fine-tuning**

[简体中文](./README.zh-CN.md) | [English](./README.md)

</div>

# Dataset Generation and Large Model Fine-tuning Tool

This is a tool for generating datasets that can crawl links from specified domains with one click. It supports converting links into markdown files that are friendly for large models and allows these markdown files to be converted into datasets suitable for training large models using ChatGPT, deepseek, Gemma, etc.

## Features

- Supports one-click crawling of links from specified domains
- Supports converting links into markdown files that are friendly for large models
- Supports uploading .md, .txt, .pdf, .docx, .doc and other files, automatically converting them to .md files
- Supports converting markdown files into datasets suitable for training large models using ChatGPT, deepseek, Gemma, etc.
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
│   │   ├── api/            # API calls
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

## Usage

1. Select the export format (JSONL or JSON) in the interface.
2. Choose the dataset style (Alpaca, ShareGPT, or custom).
3. If you choose a custom format, configure the field mapping.
4. Enter the output file name.
5. Click the "Preview" button to view the conversion results.
6. Click the "Export" button to generate the file.
7. After exporting is complete, click the "Download" button to obtain the file.

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

1. **Alpaca format**: Suitable for instruction fine-tuning.
2. **ShareGPT format**: Suitable for dialogue fine-tuning.
3. **Custom format**: Customizable field mapping.