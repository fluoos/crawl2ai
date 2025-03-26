# Dataset Generation and Large Model Fine-tuning Tool

This is a tool for generating datasets that can crawl links from specified domains with one click. It supports converting links into markdown files that are friendly for large models and allows these markdown files to be converted into datasets suitable for training large models using ChatGPT, deepseek, Gemma, etc.

## Features

- Supports one-click crawling of links from specified domains
- Supports converting links into markdown files that are friendly for large models
- Supports converting markdown files into datasets suitable for training large models using ChatGPT, deepseek, Gemma, etc.
- Supports exporting in both JSONL and JSON formats
- Supports exporting in Alpaca, ShareGPT, and custom formats
- Supports previewing conversion results

## Project Structure

```
├── frontend/             # Frontend implementation (Vue3 + Ant Design)
│   ├── index.html        # HTML entry file
│   ├── package.json      # Frontend dependency configuration
│   ├── vite.config.js    # Vite configuration file
│   └── src/              # Frontend source code
│       ├── main.js       # Main entry file
│       ├── App.vue       # Main application component
│       ├── components/   # Components directory
│       │   ├── Crawler.vue      # Crawler configuration component
│       │   ├── Converter.vue    # Converter configuration component
│       │   └── Export.vue       # Export configuration component
│       ├── api.js        # API call encapsulation
│       └── style.css     # Global styles
├── src/                  # Source code directory
│   ├── crawl_url.py      # URL crawling implementation
│   ├── crawl_to_file.py  # Crawler to file conversion implementation
│   ├── export_dataset.py # Dataset export API implementation
│   ├── file_to_dataset.py # File to dataset conversion implementation
│   ├── simple_crawler.py # Simple crawler implementation
│   └── clean_failed_files.py # Failed files cleanup tool
├── tests/                # Test directory
│   └── test.py           # Test file
├── output/               # Output directory
│   ├── qa_dataset.jsonl  # Generated QA dataset
│   └── crawled_urls.txt  # Crawled URL list
├── export/               # Export directory
│   ├── alpaca/           # Alpaca format output
│   ├── sharegpt/         # ShareGPT format output
│   └── custom/           # Custom format output
├── upload/               # Upload file directory
├── config/               # Configuration file directory
│   ├── crawler.yaml      # Crawler configuration
│   └── export.yaml       # Export configuration
├── requirements.txt      # Python dependencies file
├── .env                  # Environment variables
├── .gitignore            # Git ignore file configuration
├── LICENSE               # License file
├── README.md             # English documentation
└── README.zh-CN.md       # Chinese documentation
```
## Quick Start

### Install Dependencies

1. **Backend dependencies**:

   ```bash
   pip install flask flask-cors
   ```

2. **Frontend dependencies**:

   ```bash
   cd frontend
   npm install
   ```

### Run the Project

1. Start the backend server:

   ```bash
   python export_dataset.py
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