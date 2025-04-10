import os
import json
import logging
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.core.config import settings

# 常量定义 - 使用settings中的配置
EXPORT_FORMATS = settings.SUPPORTED_FORMATS
DATASET_STYLES = settings.SUPPORTED_STYLES
INPUT_FILE = os.path.join(settings.OUTPUT_DIR, "qa_dataset.jsonl")

class DatasetService:
    """数据集服务类，处理所有与数据集相关的业务逻辑"""
    
    @staticmethod
    def ensure_output_file_exists():
        """确保输出目录和文件存在"""
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        
        # 检查qa_dataset.jsonl是否存在，如果不存在则创建一个示例文件
        qa_file = os.path.join(settings.OUTPUT_DIR, "qa_dataset.jsonl")
        if not os.path.exists(qa_file):
            with open(qa_file, "w", encoding="utf-8") as f:
                # 写入几条示例数据
                f.write('{"question": "什么是大模型?", "answer": "大模型是指参数量巨大的人工智能模型，如GPT等。", "label": "AI"}\n')
                f.write('{"question": "如何训练大模型?", "answer": "训练大模型需要大量数据和计算资源，通常采用分布式训练方法。", "label": "训练"}\n')
                f.write('{"question": "数据集如何准备?", "answer": "数据集准备需要收集、清洗、标注和验证数据，确保数据质量和多样性。", "label": "数据"}\n')
        
        # 确保导出目录存在
        for style in DATASET_STYLES:
            os.makedirs(os.path.join(settings.EXPORT_DIR, style.lower()), exist_ok=True)
    
    @staticmethod
    def get_formats():
        """获取支持的文件格式和数据集风格"""
        return {
            "formats": EXPORT_FORMATS,
            "styles": DATASET_STYLES
        }
    
    @staticmethod
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
        
        return examples
    
    @staticmethod
    def get_stats(input_file: str = INPUT_FILE) -> Dict[str, Any]:
        """获取数据集统计信息"""
        # 读取原始数据
        data = DatasetService.read_jsonl_file(input_file)
        
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
    
    @staticmethod
    def list_data(
        format_type: str = "jsonl", 
        style: str = "Alpaca", 
        input_file: str = "qa_dataset.jsonl", 
        template: Optional[Dict] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """预览数据转换结果"""
        if format_type not in EXPORT_FORMATS:
            raise ValueError(f"不支持的文件格式: {format_type}")
        
        if style not in DATASET_STYLES:
            raise ValueError(f"不支持的数据集风格: {style}")
        
        # 读取原始数据
        file_path = os.path.join(settings.OUTPUT_DIR, input_file)
        data = DatasetService.read_jsonl_file(file_path)
        if not data:
            return {"data": [], "total": 0, "page": page, "pageSize": page_size}
        
        # 根据选择的风格转换数据
        converted_data = []
        if style == "Alpaca":
            converted_data = DatasetService.convert_to_alpaca_format(data)
        elif style == "ShareGPT":
            converted_data = DatasetService.convert_to_sharegpt_format(data)
        elif style == "Custom":
            converted_data = DatasetService.convert_to_custom_format(data, template)
        
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
    
    @staticmethod
    def export_data(
        format_type: str = "jsonl",
        style: str = "Alpaca",
        input_file: str = "qa_dataset.jsonl",
        output_file: Optional[str] = None,
        template: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """导出数据集"""
        if format_type not in EXPORT_FORMATS:
            raise ValueError(f"不支持的文件格式: {format_type}")
        
        if style not in DATASET_STYLES:
            raise ValueError(f"不支持的数据集风格: {style}")
        
        # 读取原始数据
        file_path = os.path.join(settings.OUTPUT_DIR, input_file)
        data = DatasetService.read_jsonl_file(file_path)
        if not data:
            raise ValueError(f"文件 {input_file} 为空或不存在")
        
        # 根据选择的风格转换数据
        converted_data = []
        if style == "Alpaca":
            converted_data = DatasetService.convert_to_alpaca_format(data)
        elif style == "ShareGPT":
            converted_data = DatasetService.convert_to_sharegpt_format(data)
        elif style == "Custom":
            converted_data = DatasetService.convert_to_custom_format(data, template)
        
        # 生成完整的文件名
        if not output_file:
            output_file = f'dataset_{int(datetime.now().timestamp())}'
            
        if not output_file.endswith(f".{format_type}"):
            output_file += f".{format_type}"
        
        # 确保导出目录存在
        style_dir = os.path.join(settings.EXPORT_DIR, style.lower())
        os.makedirs(style_dir, exist_ok=True)
        output_path = os.path.join(style_dir, output_file)
        
        # 根据格式保存文件
        if format_type == "jsonl":
            DatasetService.save_as_jsonl(converted_data, output_path)
        elif format_type == "json":
            DatasetService.save_as_json(converted_data, output_path)
        
        # 返回文件信息
        return {
            "success": True,
            "message": "导出成功",
            "filename": output_file,
            "path": output_path,
            "downloadUrl": f"/api/dataset/download/{style.lower()}/{output_file}"
        }
    
    @staticmethod
    def delete_items(ids: List[int]) -> Dict[str, Any]:
        """删除指定的问答对"""
        if not ids:
            raise ValueError("请提供要删除的问答对ID")
        
        dataset_path = os.path.join(settings.OUTPUT_DIR, "qa_dataset.jsonl")
        
        if not os.path.exists(dataset_path):
            raise ValueError("数据集文件不存在")
        
        # 读取现有数据集
        items = []
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        items.append(json.loads(line))
        except Exception as e:
            raise ValueError(f"读取数据集文件失败: {str(e)}")
        
        # 检查ID是否有效
        max_id = len(items) - 1
        invalid_ids = [id for id in ids if id < 0 or id > max_id]
        if invalid_ids:
            raise ValueError(f"无效的ID: {invalid_ids}，有效范围: 0-{max_id}")
        
        # 备份原始文件
        backup_path = os.path.join(settings.OUTPUT_DIR, f"qa_dataset.jsonl.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        try:
            shutil.copy2(dataset_path, backup_path)
        except Exception as e:
            logging.warning(f"备份原始文件失败: {str(e)}")
        
        # 删除指定ID的项
        to_delete = set(ids)
        remaining_items = []
        deleted_count = 0
        
        for i, item in enumerate(items):
            if i in to_delete:
                deleted_count += 1
            else:
                remaining_items.append(item)
        
        # 将剩余项写回文件
        try:
            with open(dataset_path, "w", encoding="utf-8") as f:
                for item in remaining_items:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        except Exception as e:
            raise ValueError(f"写入更新后的数据集失败: {str(e)}")
        
        return {
            "status": "success",
            "message": f"成功删除 {deleted_count} 个问答对，剩余 {len(remaining_items)} 个",
            "deleted_count": deleted_count,
            "remaining_count": len(remaining_items)
        }
    
    @staticmethod
    def get_download_file_path(style: str, filename: str) -> str:
        """获取下载文件的路径"""
        file_path = os.path.join(settings.EXPORT_DIR, style, filename)
        if not os.path.exists(file_path):
            raise ValueError("文件不存在")
        return file_path
    
    # 辅助方法
    
    @staticmethod
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
    
    @staticmethod
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
    
    @staticmethod
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
    
    @staticmethod
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
    
    @staticmethod
    def save_as_jsonl(data, file_path):
        """保存为JSONL格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        return True
    
    @staticmethod
    def save_as_json(data, file_path):
        """保存为JSON格式"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
