from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import os
from typing import Dict, Any, List, Optional

import os
import json
import aiohttp
import asyncio
import logging
from app.core.config import settings
from app.core.deps import get_api_key
from app.schemas.dataset import DeleteItemsRequest, DatasetListRequest, DatasetExportRequest
from app.services.dataset_service import DatasetService, EXPORT_FORMATS, DATASET_STYLES, INPUT_FILE

router = APIRouter()

# 确保数据目录和初始文件存在
DatasetService.ensure_output_file_exists()

@router.get("/formats")
async def get_formats(api_key: str = Depends(get_api_key)):
    """获取支持的文件格式和数据集风格"""
    try:
        return DatasetService.get_formats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/examples")
async def get_format_examples(api_key: str = Depends(get_api_key)):
    """获取各种格式的示例"""
    try:
        return DatasetService.get_format_examples()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_stats(api_key: str = Depends(get_api_key)):
    """获取数据集统计信息"""
    try:
        return DatasetService.get_stats()
    except Exception as e:
        print(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/list")
async def list_data(
    params: DatasetListRequest,
    api_key: str = Depends(get_api_key)
):
    """预览数据转换结果"""
    try:
        return DatasetService.list_data(
            format_type=params.format,
            style=params.style,
            input_file=params.inputFile,
            template=params.template,
            page=params.page,
            page_size=params.pageSize
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"预览数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_data(
    options: DatasetExportRequest,
    api_key: str = Depends(get_api_key)
):
    """导出数据集"""
    try:
        return DatasetService.export_data(
            format_type=options.format,
            style=options.style,
            input_file=options.inputFile,
            output_file=options.outputFile,
            template=options.template
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"导出数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{style}/{filename}")
async def download_file(style: str, filename: str):
    """下载导出的文件"""
    try:
        file_path = DatasetService.get_download_file_path(style, filename)
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/delete", response_model=Dict[str, Any])
async def delete_items(
    request: DeleteItemsRequest,
    api_key: str = Depends(get_api_key)
):
    """删除指定的问答对"""
    try:
        return DatasetService.delete_items(request.ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

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

# 后台任务
async def convert_files_to_dataset_task(files, model, output_file):
    """转换文件到数据集的后台任务"""
    print(f"正在转换 {len(files)} 个文件")
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
    print(f"开始转换 {len(files)} 个文件")
    
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
    
    # 关键修改：使用追加模式写入文件
    os.makedirs("output", exist_ok=True)
    
    # 使用追加模式打开文件
    with open(output_path, "a", encoding="utf-8") as f:
        for item in results:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    
    # 更新markdown_manager.json中相应文件的isDataset状态
    update_markdown_dataset_status(files)
    
    print(f"提取了 {len(results)} 个问答对")
    return output_path

def update_markdown_dataset_status(files: List[str]) -> bool:
    """
    更新markdown_manager.json中文件的isDataset状态为True
    
    参数:
    - files: 需要更新的文件路径列表
    
    返回:
    - bool: 是否成功更新了文件
    """
    try:
        manager_path = os.path.join("output", "markdown_manager.json")
        if os.path.exists(manager_path):
            # 读取文件内容
            with open(manager_path, 'r', encoding='utf-8') as f:
                try:
                    manager_data = json.load(f)
                    
                    # 创建已处理文件的集合，便于快速查找
                    processed_files = set(files)
                    updated = False
                    
                    # 更新匹配的文件记录
                    for item in manager_data:
                        if isinstance(item, dict) and 'filePath' in item:
                            file_path = item['filePath']
                            
                            # 标准化路径比较 - 统一转换为正斜杠格式并去掉前导的./
                            norm_item_path = file_path.replace('\\', '/')
                            if norm_item_path.startswith('./'):
                                norm_item_path = norm_item_path[2:]
                            
                            # 检查是否匹配任何处理过的文件
                            for proc_file in processed_files:
                                norm_proc_file = proc_file.replace('\\', '/')
                                if norm_proc_file.startswith('./'):
                                    norm_proc_file = norm_proc_file[2:]
                                    
                                print(f"比较: {norm_item_path} vs {norm_proc_file}")
                                if norm_item_path == norm_proc_file:
                                    item['isDataset'] = True
                                    updated = True
                                    print(f"匹配成功: {norm_item_path} = {norm_proc_file}")
                                    break
                    
                    # 只有在有更新时才写入文件
                    if updated:
                        with open(manager_path, 'w', encoding='utf-8') as f:
                            json.dump(manager_data, f, ensure_ascii=False, indent=2)
                        print(f"已更新 {manager_path} 中的文件状态")
                        return True
                    return False
                except json.JSONDecodeError:
                    logging.error(f"markdown_manager.json 格式错误，无法更新")
                    return False
                except Exception as e:
                    logging.error(f"更新 markdown_manager.json 时出错: {str(e)}")
                    return False
        return False
    except Exception as e:
        logging.error(f"处理 markdown_manager.json 时出错: {str(e)}")
        return False 