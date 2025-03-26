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
├── export_dataset.py # Backend implementation (Flask API)
├── frontend/ # Frontend implementation (Vue3 + Ant Design)
│ ├── index.html
│ ├── package.json
│ ├── vite.config.js
│ └── src/
│ ├── main.js
│ ├── App.vue
│ ├── api.js
│ └── style.css
├── output/ # Input file directory
│ └── qa_dataset.jsonl # Original QA data
└── export/ # Output file directory
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