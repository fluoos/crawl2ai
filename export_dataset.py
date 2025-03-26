# 用Vue3和ant-design组件库实现一个可运行的数据集导出工具，当前文件为后端，导出工具为前端
# 将本地output目录下的文件qa_dataset.jsonl根据网页配置，按配置根式导出为指定数据集文件
# 数据集文件名：根据网页配置，按配置根式导出为指定数据集文件
# 导出的文件格式可选：jsonl、json
# 数据集风格可选：Alpaca、ShareGPT、自定义格式
# 网页可根据选择的文件格式、数据集风格，显示格式内容示例

# 后端实现：
# 1. 读取本地output目录下的文件qa_dataset.jsonl
# 2. 根据网页配置，按配置根式导出为指定数据集文件
# 3. 返回数据集文件内容
# 4. 可以实现数据集导出

import json
import os
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import logging
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("export_dataset.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 常量定义
INPUT_FILE = "output/qa_dataset.jsonl"
OUTPUT_DIR = "export"
EXPORT_FORMATS = ["jsonl", "json"]
DATASET_STYLES = ["Alpaca", "ShareGPT", "Custom"]

# 确保导出目录存在
os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_jsonl_file(file_path):
    """读取JSONL文件并返回数据列表"""
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line)
                        data.append(item)
                    except json.JSONDecodeError as e:
                        logger.error(f"解析行失败: {line[:100]}... - {str(e)}")
        logger.info(f"成功读取 {len(data)} 条数据")
        return data
    except Exception as e:
        logger.error(f"读取文件失败: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def convert_to_alpaca_format(data):
    """转换为Alpaca格式数据"""
    alpaca_data = []
    for item in data:
        if "question" in item and "answer" in item:
            alpaca_item = {
                "instruction": item["question"],
                "input": "",
                "output": item["answer"]
            }
            # 如果有标签，添加到元数据中
            if "label" in item:
                alpaca_item["metadata"] = {"label": item["label"]}
            alpaca_data.append(alpaca_item)
    return alpaca_data

def convert_to_sharegpt_format(data):
    """转换为ShareGPT格式数据"""
    sharegpt_data = []
    for item in data:
        if "question" in item and "answer" in item:
            conversation = {
                "conversations": [
                    {
                        "role": "human",
                        "content": item["question"]
                    },
                    {
                        "role": "assistant",
                        "content": item["answer"]
                    }
                ]
            }
            # 如果有标签，添加到元数据中
            if "label" in item:
                conversation["metadata"] = {"label": item["label"]}
            sharegpt_data.append(conversation)
    return sharegpt_data

def convert_to_custom_format(data, template):
    """根据自定义模板转换数据"""
    custom_data = []
    try:
        for item in data:
            # 使用模板进行格式转换
            custom_item = {}
            for key, value in template.items():
                if isinstance(value, dict) and "field" in value:
                    field_name = value["field"]
                    if field_name in item:
                        custom_item[key] = item[field_name]
                    else:
                        custom_item[key] = value.get("default", "")
                else:
                    custom_item[key] = value
            custom_data.append(custom_item)
        return custom_data
    except Exception as e:
        logger.error(f"自定义格式转换失败: {str(e)}")
        return []

def save_as_jsonl(data, file_path):
    """保存为JSONL格式"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        return True
    except Exception as e:
        logger.error(f"保存JSONL文件失败: {str(e)}")
        return False

def save_as_json(data, file_path):
    """保存为JSON格式"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"保存JSON文件失败: {str(e)}")
        return False

@app.route('/api/formats', methods=['GET'])
def get_formats():
    """获取支持的文件格式和数据集风格"""
    return jsonify({
        "formats": EXPORT_FORMATS,
        "styles": DATASET_STYLES
    })

@app.route('/api/preview', methods=['POST'])
def preview_data():
    """预览数据转换结果"""
    try:
        # 获取请求参数
        params = request.json
        format_type = params.get('format', 'jsonl')
        style = params.get('style', 'Alpaca')
        custom_template = params.get('template', {})
        
        # 新增：获取分页参数
        page = int(params.get('page', 1))
        page_size = int(params.get('pageSize', 20))
        
        if format_type not in EXPORT_FORMATS:
            return jsonify({"error": f"不支持的文件格式: {format_type}"}), 400
        
        if style not in DATASET_STYLES:
            return jsonify({"error": f"不支持的数据集风格: {style}"}), 400
        
        # 读取原始数据
        data = read_jsonl_file(INPUT_FILE)
        if not data:
            return jsonify({"error": "未找到有效数据或数据为空"}), 404
        
        # 根据选择的风格转换数据
        converted_data = []
        if style == "Alpaca":
            converted_data = convert_to_alpaca_format(data)
        elif style == "ShareGPT":
            converted_data = convert_to_sharegpt_format(data)
        elif style == "Custom":
            converted_data = convert_to_custom_format(data, custom_template)
        
        # 计算分页索引
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        # 返回分页数据，而不是固定的前5条
        preview_data = converted_data[start_idx:end_idx] if converted_data else []
        
        logger.info(f"预览请求: 格式={format_type}, 风格={style}, 页码={page}, 页大小={page_size}, 返回数据条数={len(preview_data)}")
        
        return jsonify({
            "preview": preview_data,
            "totalCount": len(data),
            "convertedCount": len(converted_data),
            "page": page,
            "pageSize": page_size
        })
        
    except Exception as e:
        logger.error(f"预览数据失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/export', methods=['POST'])
def export_data():
    """导出数据集"""
    try:
        # 获取请求参数
        params = request.json
        format_type = params.get('format', 'jsonl')
        style = params.get('style', 'Alpaca')
        filename = params.get('filename', f'dataset_{int(time.time())}')
        custom_template = params.get('template', {})
        
        if not filename:
            filename = f'dataset_{int(time.time())}'
        
        if format_type not in EXPORT_FORMATS:
            return jsonify({"error": f"不支持的文件格式: {format_type}"}), 400
        
        if style not in DATASET_STYLES:
            return jsonify({"error": f"不支持的数据集风格: {style}"}), 400
        
        # 读取原始数据
        data = read_jsonl_file(INPUT_FILE)
        if not data:
            return jsonify({"error": "未找到有效数据或数据为空"}), 404
        
        # 根据选择的风格转换数据
        converted_data = []
        if style == "Alpaca":
            converted_data = convert_to_alpaca_format(data)
        elif style == "ShareGPT":
            converted_data = convert_to_sharegpt_format(data)
        elif style == "Custom":
            converted_data = convert_to_custom_format(data, custom_template)
        
        if not converted_data:
            return jsonify({"error": "数据转换后为空"}), 400
        
        # 生成完整的文件名
        file_extension = format_type
        full_filename = f"{filename}.{file_extension}"
        output_path = os.path.join(OUTPUT_DIR, full_filename)
        
        # 根据格式保存文件
        success = False
        if format_type == "jsonl":
            success = save_as_jsonl(converted_data, output_path)
        elif format_type == "json":
            success = save_as_json(converted_data, output_path)
        
        if not success:
            return jsonify({"error": "保存文件失败"}), 500
        
        # 返回文件信息
        return jsonify({
            "success": True,
            "filename": full_filename,
            "path": output_path,
            "count": len(converted_data),
            "downloadUrl": f"/api/download/{full_filename}"
        })
        
    except Exception as e:
        logger.error(f"导出数据失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """下载导出的文件"""
    try:
        file_path = os.path.join(OUTPUT_DIR, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "文件不存在"}), 404
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@app.route('/api/examples', methods=['GET'])
def get_format_examples():
    """获取各种格式的示例"""
    examples = {
        "Alpaca": {
            "description": "Alpaca格式是一种常用的指令微调数据集格式",
            "example": {
                "instruction": "问题内容",
                "input": "",
                "output": "答案内容",
                "metadata": {"label": "标签"}
            }
        },
        "ShareGPT": {
            "description": "ShareGPT格式用于对话式模型的微调",
            "example": {
                "conversations": [
                    {
                        "role": "human",
                        "content": "问题内容"
                    },
                    {
                        "role": "assistant",
                        "content": "答案内容"
                    }
                ],
                "metadata": {"label": "标签"}
            }
        },
        "Custom": {
            "description": "自定义格式允许您定义自己的数据结构",
            "example": {
                "query": {"field": "question", "default": ""},
                "response": {"field": "answer", "default": ""},
                "category": {"field": "label", "default": "general"}
            }
        }
    }
    
    return jsonify(examples)

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取数据集统计信息"""
    try:
        # 读取原始数据
        data = read_jsonl_file(INPUT_FILE)
        
        if not data:
            return jsonify({
                "totalCount": 0,
                "validCount": 0,
                "avgLength": 0
            })
            
        # 计算统计信息
        total_count = len(data)
        valid_count = sum(1 for item in data if "question" in item and "answer" in item)
        total_length = sum(len(str(item.get("question", ""))) + len(str(item.get("answer", ""))) for item in data)
        avg_length = total_length / total_count if total_count > 0 else 0
        
        return jsonify({
            "totalCount": total_count,
            "validCount": valid_count,
            "avgLength": avg_length
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

# 主入口
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
