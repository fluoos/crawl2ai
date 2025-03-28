from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
import os
import json
import aiohttp
import asyncio
import logging
from app.core.config import settings

from app.schemas.converter import ConversionRequest, ConversionResponse
from app.services.converter_service import convert_files_to_dataset
from app.api.deps import get_api_key

router = APIRouter()

# 在内存中存储转换状态
conversion_state = {}

@router.post("/convert")
async def convert_files(
    data: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """将Markdown文件转换为数据集"""
    files = data.get("files", [])
    model = data.get("model", "deepseek")
    output_file = data.get("output_file", "qa_dataset.jsonl")
    
    if not files:
        raise HTTPException(status_code=400, detail="文件列表不能为空")
    
    # 更新转换状态
    conversion_state[output_file] = {
        "status": "running",
        "message": "转换任务正在进行中...",
        "progress": 0,
        "total": len(files)
    }
    
    # 在后台执行转换任务
    background_tasks.add_task(
        convert_files_to_dataset_task, 
        files, 
        model, 
        output_file
    )
    
    return {"status": "success", "message": "转换任务已开始"}

@router.get("/status")
async def get_conversion_status(output_file: str = Query("qa_dataset.jsonl")):
    """获取转换状态和结果"""
    if output_file not in conversion_state:
        # 检查文件是否已存在
        file_path = os.path.join("output", output_file)
        if os.path.exists(file_path):
            # 读取前5行作为示例
            sample_data = []
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f):
                        if i >= 5:
                            break
                        sample_data.append(json.loads(line))
                
                return {
                    "status": "completed",
                    "message": "转换已完成",
                    "output_file": output_file,
                    "sample": sample_data
                }
            except Exception as e:
                logging.error(f"读取样本数据失败: {str(e)}")
        
        return {
            "status": "unknown",
            "message": "未找到转换任务或文件",
            "output_file": output_file
        }
    
    status_info = conversion_state[output_file]
    
    # 如果转换已完成，读取样本数据
    if status_info["status"] == "completed":
        file_path = os.path.join("output", output_file)
        sample_data = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= 5:
                        break
                    sample_data.append(json.loads(line))
            
            status_info["sample"] = sample_data
        except Exception as e:
            logging.error(f"读取样本数据失败: {str(e)}")
    
    return status_info

# 后台任务
async def convert_files_to_dataset_task(files, model, output_file):
    """转换文件到数据集的后台任务"""
    try:
        await convert_files_to_dataset(files, model, output_file)
        conversion_state[output_file]["status"] = "completed"
        conversion_state[output_file]["message"] = "转换任务已完成"
        conversion_state[output_file]["progress"] = conversion_state[output_file]["total"]
    except Exception as e:
        conversion_state[output_file]["status"] = "failed"
        conversion_state[output_file]["message"] = f"转换任务失败: {str(e)}"
        logging.error(f"转换任务失败: {str(e)}")

# 核心功能实现
async def convert_files_to_dataset(
    files: List[str],
    model: str = "deepseek",
    output_file: str = "qa_dataset.jsonl"
) -> str:
    """将Markdown文件转换为问答数据集"""
    if not files:
        raise ValueError("文件列表不能为空")
    
    output_path = os.path.join("output", output_file)
    results = []
    
    # 根据模型选择不同的API和提示词
    if model == "deepseek":
        api_url = "https://api.deepseek.com/v1/chat/completions"
        api_key = settings.DEEPSEEK_API_KEY
        system_prompt = """
    Role: 微调数据集生成专家
    Description: 你是一名微调数据集生成专家，擅长从给定的内容中生成准确的问题答案，确保答案的准确性和相关性。请将用户提供的文本内容拆分成多个问答对, 并给每个问答对添加一个标签，每个问答对都应该是一个完整的知识点。

    要求：
    1. 答案必须基于给定的内容，保持原文的准确性和专业性
    2. 答案必须准确，不能胡编乱造
    3. 仔细分析文本内容，识别所有可能的问题和答案
    4. 答案必须充分、详细、包含所有必要的信息、适合微调大模型训练使用
    5. 能够根据问题和内容，智能匹配最合适的标签
    6. 如果文本中包含多个知识点，请分别提取
    7. 确保所有重要概念、事实和细节都被纳入问答对中
    8. 必须以JSON格式返回结果

    示例输入：
    地球是太阳系的第三颗行星，距离太阳约1.5亿公里。地球表面71%是海洋，29%是陆地。地球自转一周需要24小时，公转一周需要365天。

    示例JSON输出：
    {
        "qa_pairs": [
            {
                "question": "地球在太阳系中的位置是什么？",
                "answer": "地球是太阳系的第三颗行星",
                "label": "地球"
            },
            {
                "question": "地球距离太阳有多远？",
                "answer": "地球距离太阳约1.5亿公里",
                "label": "地球"
            },
            {
                "question": "地球表面的海洋和陆地比例是多少？",
                "answer": "地球表面71%是海洋，29%是陆地",
                "label": "地球"
            },
            {
                "question": "地球的自转和公转周期分别是多少？",
                "answer": "地球自转一周需要24小时，公转一周需要365天",
                "label": "地球"
            }
        ]
    }

    请按照上述JSON格式，将用户提供的文本内容转换为多个问答对。
    """
    else:
        raise ValueError(f"不支持的模型: {model}")
    
    # 初始化转换状态
    conversion_state[output_file]["progress"] = 0
    
    async with aiohttp.ClientSession() as session:
        for i, file_path in enumerate(files):
            try:
                # 读取文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 构建API请求
                payload = {
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ],
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"}
                }
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                }
                
                # 发送API请求
                async with session.post(api_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logging.error(f"API请求失败: {error_text}")
                        continue
                    
                    response_data = await response.json()
                    generated_text = response_data["choices"][0]["message"]["content"]
                    
                    # 解析JSON响应
                    try:
                        result = json.loads(generated_text)
                        
                        # 检查和处理qa_pairs字段
                        if 'qa_pairs' in result and isinstance(result['qa_pairs'], list):
                            for qa_pair in result['qa_pairs']:
                                if isinstance(qa_pair, dict) and "question" in qa_pair and "answer" in qa_pair:
                                    qa_pair["source"] = file_path
                                    results.append(qa_pair)
                        else:
                            logging.warning(f"API返回的JSON缺少'qa_pairs'字段或格式不符合预期")
                    except json.JSONDecodeError as e:
                        logging.error(f"JSON解析错误: {str(e)}, 内容: {generated_text}")
                        # 尝试基本的问答提取
                        questions = []
                        answers = []
                        current_answer = ""
                        
                        for line in generated_text.split("\n"):
                            if line.startswith("问题") or line.startswith("Q:"):
                                if current_answer and questions:
                                    answers.append(current_answer.strip())
                                    current_answer = ""
                                questions.append(line.split(":", 1)[1].strip())
                            elif line.startswith("答案") or line.startswith("A:"):
                                current_answer = line.split(":", 1)[1].strip()
                            elif current_answer:
                                current_answer += " " + line.strip()
                        
                        if current_answer:
                            answers.append(current_answer.strip())
                        
                        # 将提取的问答对添加到结果中
                        for i in range(min(len(questions), len(answers))):
                            results.append({
                                "question": questions[i],
                                "answer": answers[i],
                                "source": file_path,
                                "label": "未分类"
                            })
                
                # 更新进度
                conversion_state[output_file]["progress"] = i + 1
                
                # 避免API速率限制
                await asyncio.sleep(1)
                
            except Exception as e:
                logging.error(f"处理文件 {file_path} 时出错: {str(e)}")
    
    # 保存结果到jsonl文件
    os.makedirs("output", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    return output_path 