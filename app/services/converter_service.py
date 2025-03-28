import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
import aiohttp

from app.core.config import settings

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
    
    # 添加与原始实现一致的重试机制
    retry_attempts = 3
    retry_delay = 5
    
    async with aiohttp.ClientSession() as session:
        for file_path in files:
            try:
                # 读取文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 检查是否需要分块处理（与原始实现一致）
                max_chunk_size = 9000  # 与原始实现一致
                chunks = [content]
                if len(content) > max_chunk_size:
                    # 实现分块逻辑，可以简化为直接截断
                    chunks = [content[i:i+max_chunk_size] for i in range(0, len(content), max_chunk_size)]
                    logging.info(f"文件内容被分割为 {len(chunks)} 个块")
                
                # 处理每个块
                for chunk in chunks:
                    for attempt in range(retry_attempts):
                        try:
                            # 构建API请求
                            payload = {
                                "model": "deepseek-chat",
                                "messages": [
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": chunk}
                                ],
                                "temperature": 0.7,
                                "response_format": {"type": "json_object"}  # 确保返回JSON
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
                                    if attempt < retry_attempts - 1:
                                        logging.info(f"等待 {retry_delay} 秒后重试...")
                                        await asyncio.sleep(retry_delay)
                                        continue
                                    else:
                                        break
                                
                                response_data = await response.json()
                                generated_text = response_data["choices"][0]["message"]["content"]
                                
                                # 解析JSON响应，更接近原始实现
                                try:
                                    result = json.loads(generated_text)
                                    
                                    # 检查和处理qa_pairs字段（与原始实现一致）
                                    if 'qa_pairs' in result and isinstance(result['qa_pairs'], list):
                                        for qa_pair in result['qa_pairs']:
                                            if isinstance(qa_pair, dict) and "question" in qa_pair and "answer" in qa_pair:
                                                qa_pair["source"] = file_path
                                                results.append(qa_pair)
                                    else:
                                        logging.warning(f"API返回的JSON缺少'qa_pairs'字段或格式不符合预期")
                                    
                                    # 成功处理后跳出重试循环
                                    break
                                    
                                except json.JSONDecodeError as e:
                                    logging.error(f"JSON解析错误: {str(e)}, 内容: {generated_text}")
                                    if attempt < retry_attempts - 1:
                                        logging.info(f"等待 {retry_delay} 秒后重试...")
                                        await asyncio.sleep(retry_delay)
                                        continue
                                    else:
                                        # 尝试基本的问答提取，与原实现类似
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
                                                "source": file_path
                                            })
                        except Exception as e:
                            logging.error(f"调用API时出错: {str(e)}")
                            if attempt < retry_attempts - 1:
                                logging.info(f"等待 {retry_delay} 秒后重试...")
                                await asyncio.sleep(retry_delay)
                            else:
                                logging.error(f"重试次数已用完，放弃处理此块")
                    
                    # 避免API速率限制
                    await asyncio.sleep(1)
                
            except Exception as e:
                logging.error(f"处理文件 {file_path} 时出错: {str(e)}")
    
    # 保存结果到jsonl文件
    with open(output_path, "w", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    return output_path 