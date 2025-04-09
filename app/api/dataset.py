from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import json
from typing import Dict, Any
from datetime import datetime

from app.core.config import settings

router = APIRouter()

# 常量定义
EXPORT_FORMATS = ["jsonl", "json"]
DATASET_STYLES = ["Alpaca", "ShareGPT", "Custom"]
INPUT_FILE = os.path.join("output", "qa_dataset.jsonl")

# 确保输出目录和文件存在
def ensure_output_file_exists():
    os.makedirs("output", exist_ok=True)
    
    # 检查qa_dataset.jsonl是否存在，如果不存在则创建一个示例文件
    qa_file = os.path.join("output", "qa_dataset.jsonl")
    if not os.path.exists(qa_file):
        with open(qa_file, "w", encoding="utf-8") as f:
            # 写入几条示例数据
            f.write('{"question": "什么是大模型?", "answer": "大模型是指参数量巨大的人工智能模型，如GPT等。", "label": "AI"}\n')
            f.write('{"question": "如何训练大模型?", "answer": "训练大模型需要大量数据和计算资源，通常采用分布式训练方法。", "label": "训练"}\n')
            f.write('{"question": "数据集如何准备?", "answer": "数据集准备需要收集、清洗、标注和验证数据，确保数据质量和多样性。", "label": "数据"}\n')

# 在路由定义前调用此函数
ensure_output_file_exists()

@router.get("/formats")
async def get_formats():
    """获取支持的文件格式和数据集风格"""
    return {
        "formats": EXPORT_FORMATS,
        "styles": DATASET_STYLES
    }

@router.get("/examples")
async def get_format_examples():
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
    
    return examples

@router.get("/stats")
async def get_stats():
    """获取数据集统计信息"""
    try:
        # 读取原始数据
        data = read_jsonl_file(INPUT_FILE)
        
        if not data:
            return {
                "totalCount": 0,
                "validCount": 0,
                "avgLength": 0
            }
            
        # 计算统计信息
        total_count = len(data)
        valid_count = sum(1 for item in data if "question" in item and "answer" in item)
        total_length = sum(len(str(item.get("question", ""))) + len(str(item.get("answer", ""))) for item in data)
        avg_length = total_length / total_count if total_count > 0 else 0
        
        return {
            "totalCount": total_count,
            "validCount": valid_count,
            "avgLength": avg_length
        }
        
    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/list")
async def list_data(params: Dict[str, Any]):
    """预览数据转换结果"""
    try:
        # 解析请求参数
        format_type = params.get('format', 'jsonl')
        style = params.get('style', 'Alpaca')
        input_file = params.get('inputFile', 'qa_dataset.jsonl')
        template = params.get('template', None)
        
        # 分页参数
        page = int(params.get('page', 1))
        page_size = int(params.get('pageSize', 20))
        
        if format_type not in EXPORT_FORMATS:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {format_type}")
        
        if style not in DATASET_STYLES:
            raise HTTPException(status_code=400, detail=f"不支持的数据集风格: {style}")
        
        # 读取原始数据
        file_path = os.path.join("output", input_file)
        data = read_jsonl_file(file_path)
        if not data:
            return {"data": [], "total": 0, "page": page, "pageSize": page_size}
        
        # 根据选择的风格转换数据
        converted_data = []
        if style == "Alpaca":
            converted_data = convert_to_alpaca_format(data)
        elif style == "ShareGPT":
            converted_data = convert_to_sharegpt_format(data)
        elif style == "Custom":
            converted_data = convert_to_custom_format(data, template)
        
        # 计算分页
        total = len(converted_data)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total)
        page_data = converted_data[start_idx:end_idx] if start_idx < total else []
        
        return {
            "data": page_data,
            "total": total,
            "page": page,
            "pageSize": page_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"预览数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_data(options: Dict[str, Any]):
    """导出数据集"""
    try:
        # 解析请求参数
        format_type = options.get('format', 'jsonl')
        style = options.get('style', 'Alpaca')
        input_file = options.get('inputFile', 'qa_dataset.jsonl')
        output_file = options.get('outputFile', f'dataset_{int(datetime.now().timestamp())}')
        template = options.get('template', None)
        
        if format_type not in EXPORT_FORMATS:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {format_type}")
        
        if style not in DATASET_STYLES:
            raise HTTPException(status_code=400, detail=f"不支持的数据集风格: {style}")
        
        # 读取原始数据
        file_path = os.path.join("output", input_file)
        data = read_jsonl_file(file_path)
        if not data:
            raise HTTPException(status_code=404, detail=f"文件 {input_file} 为空或不存在")
        
        # 根据选择的风格转换数据
        converted_data = []
        if style == "Alpaca":
            converted_data = convert_to_alpaca_format(data)
        elif style == "ShareGPT":
            converted_data = convert_to_sharegpt_format(data)
        elif style == "Custom":
            converted_data = convert_to_custom_format(data, template)
        
        # 生成完整的文件名
        if not output_file.endswith(f".{format_type}"):
            output_file += f".{format_type}"
        
        # 确保导出目录存在
        style_dir = os.path.join("export", style.lower())
        os.makedirs(style_dir, exist_ok=True)
        output_path = os.path.join(style_dir, output_file)
        
        # 根据格式保存文件
        if format_type == "jsonl":
            save_as_jsonl(converted_data, output_path)
        elif format_type == "json":
            save_as_json(converted_data, output_path)
        
        # 返回文件信息
        return {
            "success": True,
            "message": "导出成功",
            "filename": output_file,
            "path": output_path,
            "downloadUrl": f"/api/download/{style.lower()}/{output_file}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"导出数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{style}/{filename}")
async def download_file(style: str, filename: str):
    """下载导出的文件"""
    try:
        file_path = os.path.join("export", style, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="文件不存在")
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 辅助函数
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
                    except json.JSONDecodeError:
                        continue
        return data
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"读取文件失败: {str(e)}")
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
    if not template:
        # 默认模板
        template = {
            "query": {"field": "question", "default": ""},
            "response": {"field": "answer", "default": ""},
            "category": {"field": "label", "default": ""}
        }
    
    custom_data = []
    for item in data:
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

def save_as_jsonl(data, file_path):
    """保存为JSONL格式"""
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    return True

def save_as_json(data, file_path):
    """保存为JSON格式"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True 