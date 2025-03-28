import os
import json
from typing import List, Dict, Any, Optional

def preview_dataset(
    format: str,
    style: str,
    input_file: str = "qa_dataset.jsonl",
    mapping: Optional[Dict[str, str]] = None,
    page: int = 1,
    page_size: int = 20  # 添加分页参数，与原始实现一致
) -> Dict[str, Any]:
    """预览数据集导出结果，返回分页结果"""
    # 检查输入文件存在
    input_path = os.path.join("output", input_file)
    if not os.path.exists(input_path):
        # 如果文件不存在，返回空列表而不是抛出异常
        print(f"警告: 找不到输入文件: {input_path}")
        return {"preview": [], "totalCount": 0, "convertedCount": 0, "page": page, "pageSize": page_size}
    
    # 读取所有数据，而不仅仅是前几条
    data = []
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        item = json.loads(line.strip())
                        data.append(item)
                    except json.JSONDecodeError as e:
                        print(f"警告: JSON解析错误: {str(e)}, 行: {line}")
                        continue
    except Exception as e:
        print(f"读取文件错误: {str(e)}")
        return {"preview": [], "totalCount": 0, "convertedCount": 0, "page": page, "pageSize": page_size}
    
    # 检查是否有数据
    if not data:
        print(f"警告: 文件 {input_path} 中没有有效数据")
        return {"preview": [], "totalCount": 0, "convertedCount": 0, "page": page, "pageSize": page_size}
    
    # 转换为目标格式
    result = []
    
    try:
        # 规范化style名称 (保证大小写一致性)
        style = style.lower() if isinstance(style, str) else "alpaca"
        
        if style == "alpaca":
            for item in data:
                # Alpaca格式
                alpaca_item = {
                    "instruction": item.get("question", ""),
                    "input": "",
                    "output": item.get("answer", "")
                }
                if "label" in item:
                    alpaca_item["metadata"] = {"label": item["label"]}
                result.append(alpaca_item)
        
        elif style == "sharegpt":
            for item in data:
                # ShareGPT格式
                sharegpt_item = {
                    "conversations": [
                        {"role": "human", "content": item.get("question", "")},
                        {"role": "assistant", "content": item.get("answer", "")}
                    ]
                }
                if "label" in item:
                    sharegpt_item["metadata"] = {"label": item["label"]}
                result.append(sharegpt_item)
        
        elif style == "custom":
            if not mapping:
                # 默认映射
                mapping = {
                    "query": "question",
                    "response": "answer",
                    "category": "label"
                }
            
            for item in data:
                # 自定义格式，根据映射转换字段
                custom_item = {}
                for target_key, source_key in mapping.items():
                    if source_key in item:
                        custom_item[target_key] = item[source_key]
                    else:
                        custom_item[target_key] = ""  # 默认值
                result.append(custom_item)
        
        else:
            # 不支持的格式，返回原始数据
            result = data
    
    except Exception as e:
        print(f"转换数据错误: {str(e)}")
        # 返回原始数据作为后备
        return {"preview": [], "totalCount": 0, "convertedCount": 0, "page": page, "pageSize": page_size}
    
    # 添加分页处理，与原始实现一致
    total_count = len(data)
    total_converted = len(result)
    
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_converted)
    
    # 返回分页结果和元数据
    return {
        "preview": result[start_idx:end_idx] if result and start_idx < len(result) else [],
        "totalCount": total_count,
        "convertedCount": total_converted,
        "page": page,
        "pageSize": page_size
    }

def export_dataset(
    format: str,
    style: str,
    input_file: str = "qa_dataset.jsonl",
    output_file: str = "dataset.jsonl",
    mapping: Optional[Dict[str, str]] = None
) -> str:
    """导出数据集到指定格式"""
    # 读取输入文件
    input_path = os.path.join("output", input_file)
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"找不到输入文件: {input_path}")
    
    # 准备输出目录 - 规范化style名称为小写
    style_lower = style.lower() if isinstance(style, str) else "alpaca"
    output_dir = os.path.join("export", style_lower)
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置输出路径
    if not output_file.endswith(f".{format}"):
        output_file += f".{format}"
    output_path = os.path.join(output_dir, output_file)
    
    # 读取所有数据
    data = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    item = json.loads(line)
                    data.append(item)
                except json.JSONDecodeError:
                    continue
    
    # 转换数据为目标格式
    result = preview_dataset(format, style, input_file, mapping, page=1, page_size=9999)
    
    # 写入输出文件
    if format.lower() == "jsonl":
        with open(output_path, "w", encoding="utf-8") as f:
            for item in result["preview"]:  # 仍使用"preview"，因为这是preview_dataset返回的格式
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    elif format.lower() == "json":
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result["preview"], f, ensure_ascii=False, indent=2)
    
    else:
        raise ValueError(f"不支持的导出格式: {format}")
    
    return output_path 