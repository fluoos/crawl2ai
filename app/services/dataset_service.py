import os
import json
import logging
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import aiohttp
import asyncio
from openai import OpenAI

from app.core.config import settings
from app.services.system_service import SystemService
from app.core.websocket import manager

# 常量定义 - 使用settings中的配置
EXPORT_FORMATS = settings.SUPPORTED_FORMATS
DATASET_STYLES = settings.SUPPORTED_STYLES
INPUT_FILE = os.path.join(settings.OUTPUT_DIR, "qa_dataset.jsonl")

# 在内存中存储转换状态
conversion_state = {}

class DatasetService:
    """数据集服务类，处理所有与数据集相关的业务逻辑"""
    
    @staticmethod
    def get_project_dataset_path(project_id: Optional[str] = None) -> str:
        """
        获取数据集文件路径
        如果提供了项目ID，则返回项目下的数据集路径
        否则返回默认数据集路径
        """
        if project_id:
            # 项目目录路径 - 修改路径结构
            project_dir = os.path.join(settings.OUTPUT_DIR, str(project_id))
            # 确保项目目录存在
            os.makedirs(project_dir, exist_ok=True)
            # 项目数据集文件路径
            project_dataset_path = os.path.join(project_dir, "qa_dataset.jsonl")
            # 如果项目数据集文件不存在，创建空文件
            if not os.path.exists(project_dataset_path):
                with open(project_dataset_path, "w", encoding="utf-8") as f:
                    pass
            return project_dataset_path
        else:
            # 返回默认数据集路径
            return INPUT_FILE
    
    @staticmethod
    def get_project_export_path(style: str, project_id: Optional[str] = None) -> str:
        """
        获取项目导出目录路径
        如果提供了项目ID，则返回项目下的导出目录
        否则返回默认导出目录
        """
        if project_id:
            # 项目导出目录 - 修改路径结构
            project_export_dir = os.path.join(settings.OUTPUT_DIR, str(project_id), "export", style.lower())
            # 确保目录存在
            os.makedirs(project_export_dir, exist_ok=True)
            return project_export_dir
        else:
            # 返回默认导出目录
            export_dir = os.path.join(settings.EXPORT_DIR, style.lower())
            os.makedirs(export_dir, exist_ok=True)
            return export_dir
    
    @staticmethod
    def get_formats(project_id: Optional[str] = None):
        """获取支持的文件格式和数据集风格"""
        return {
            "formats": EXPORT_FORMATS,
            "styles": DATASET_STYLES
        }
    
    @staticmethod
    def get_format_examples(project_id: Optional[str] = None):
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
    def get_project_dataset_count(project_id: Optional[str] = None) -> int:
        """获取项目数据集数量"""
        input_file = DatasetService.get_project_dataset_path(project_id)
        return len(DatasetService.read_jsonl_file(input_file))
    
    @staticmethod
    def get_stats(project_id: Optional[str] = None) -> Dict[str, Any]:
        """获取数据集统计信息"""
        # 根据project_id获取数据集路径
        input_file = DatasetService.get_project_dataset_path(project_id)
        
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
        input_file: str = "qa_dataset.jsonl", 
        page: int = 1,
        page_size: int = 20,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """预览数据转换结果"""
        # 根据project_id获取数据集路径
        file_path = input_file
        if project_id:
            file_path = DatasetService.get_project_dataset_path(project_id)
        else:
            file_path = os.path.join(settings.OUTPUT_DIR, input_file)
            
        # 读取原始数据
        data = DatasetService.read_jsonl_file(file_path)
        if not data:
            return {"data": [], "total": 0, "page": page, "pageSize": page_size}
        
        # 根据选择的风格转换数据
        converted_data = []
    
        for item in data:
            custom_item = {}
            custom_item["id"] = item.get("id", None)
            custom_item["question"] = item.get("question", "")
            custom_item["answer"] = item.get("answer", "")
            custom_item["label"] = item.get("label", "")
            custom_item["source"] = item.get("source", "")
            custom_item["chain_of_thought"] = item.get("chainOfThought", "")
            converted_data.append(custom_item)
            
        # 将数据倒序排列
        converted_data.reverse()
        
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
        template: Optional[Dict] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """导出数据集"""
        if format_type not in EXPORT_FORMATS:
            raise ValueError(f"不支持的文件格式: {format_type}")
        
        if style not in DATASET_STYLES:
            raise ValueError(f"不支持的数据集风格: {style}")
        
        # 读取原始数据
        file_path = input_file
        if project_id:
            file_path = DatasetService.get_project_dataset_path(project_id)
        else:
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
        
        # 确保导出目录存在，并根据项目ID选择正确的路径
        style_dir = DatasetService.get_project_export_path(style, project_id)
        output_path = os.path.join(style_dir, output_file)
        
        # 根据格式保存文件
        if format_type == "jsonl":
            DatasetService.save_as_jsonl(converted_data, output_path)
        elif format_type == "json":
            DatasetService.save_as_json(converted_data, output_path)
        
        # 构建下载URL
        download_url = f"/api/dataset/download/{style.lower()}/{output_file}"
        if project_id:
            download_url += f"?projectId={project_id}"
        
        # 返回文件信息
        return {
            "success": True,
            "message": "导出成功",
            "filename": output_file,
            "path": output_path,
            "downloadUrl": download_url
        }
    
    @staticmethod
    def delete_items(ids: List[int], project_id: Optional[str] = None) -> Dict[str, Any]:
        """删除指定的问答对"""
        if not ids:
            raise ValueError("请提供要删除的问答对ID")
        
        # 根据项目ID获取数据集路径
        dataset_path = DatasetService.get_project_dataset_path(project_id)
        
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
        existing_ids = {item.get("id") for item in items if "id" in item}
        invalid_ids = [id for id in ids if id not in existing_ids]
        if invalid_ids:
            raise ValueError(f"无效的ID: {invalid_ids}")
        
        # 删除指定ID的项
        to_delete = set(ids)
        remaining_items = []
        deleted_count = 0
        
        for item in items:
            if "id" in item and item["id"] in to_delete:
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
    def get_download_file_path(style: str, filename: str, project_id: Optional[str] = None) -> str:
        """获取下载文件的路径"""
        # 根据项目ID选择正确的导出目录
        style_dir = DatasetService.get_project_export_path(style, project_id)
        file_path = os.path.join(style_dir, filename)
        
        if not os.path.exists(file_path):
            raise ValueError("文件不存在")
        return file_path
    
    # Markdown转换相关功能
    
    @staticmethod
    def save_conversion_task_status(files: List[str], output_file: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """启动文件转换任务"""
        # 用项目ID作为状态的key，以支持不同项目的并行转换
        task_key = output_file
        if project_id:
            task_key = f"{project_id}_{output_file}"
            
        # 更新转换状态
        conversion_state[task_key] = {
            "status": "running",
            "message": "转换任务正在进行中...",
            "progress": 0,
            "total": len(files),
            "project_id": project_id
        }
        
        return {"status": "success", "message": "转换任务已开始"}
    
    @staticmethod
    async def convert_files_to_dataset_task(files: List[str], output_file: str, project_id: Optional[str] = None):
        """转换文件到数据集的后台任务"""
        # 用项目ID作为状态的key
        task_key = output_file
        if project_id:
            task_key = f"{project_id}_{output_file}"
            
        print(f"正在转换 {len(files)} 个文件, 项目ID: {project_id}")
        try:
            await DatasetService.convert_files_to_dataset(files, output_file, project_id)
            conversion_state[task_key]["status"] = "completed"
            conversion_state[task_key]["message"] = "转换任务已完成"
            conversion_state[task_key]["progress"] = conversion_state[task_key]["total"]
        except Exception as e:
            conversion_state[task_key]["status"] = "failed"
            conversion_state[task_key]["message"] = f"转换任务失败: {str(e)}"
            logging.error(f"转换任务失败: {str(e)}")
            # 发送失败通知
            try:
                await manager.send_json({
                    "type": "md_to_dataset_convert_failed",
                    "status": "failed",
                    "message": f"转换任务失败: {error_msg}",
                    "total": len(files),
                    "processed": conversion_state[task_key].get("progress", 0),
                    "successful": conversion_state[task_key].get("successful", 0)
                }, project_id)
            except Exception as notify_error:
                logging.error(f"发送失败通知时出错: {str(notify_error)}")
    
    @staticmethod
    def check_available_api_key() -> Dict[str, Any]:
        """检查是否有可用的API密钥"""
        try:
            # 获取模型配置
            models_list = SystemService._read_json_file(SystemService.MODELS_CONFIG_FILE, [])
            
            # 查找默认模型
            default_model = None
            for model_config in models_list:
                if model_config.get("isDefault", False):
                    default_model = model_config
                    break
            
            # 如果没有默认模型，查找第一个有API密钥的模型
            if not default_model:
                for model_config in models_list:
                    if model_config.get("apiKey") and model_config.get("apiKey").strip():
                        default_model = model_config
                        break
            
            if not default_model:
                return {
                    "available": False,
                    "message": "未找到可用的模型配置，请在系统设置中配置模型API密钥"
                }
            
            api_key = default_model.get("apiKey", "").strip()
            if not api_key:
                return {
                    "available": False,
                    "message": f"模型 '{default_model.get('name', 'Unknown')}' 的API密钥未配置，请在系统设置中配置"
                }
            
            return {
                "available": True,
                "model_name": default_model.get("name", "Unknown"),
                "model": default_model.get("model", "Unknown"),
                "api_endpoint": default_model.get("apiEndpoint", ""),
                "message": f"找到可用模型: {default_model.get('name', 'Unknown')} ({default_model.get('model', 'Unknown')})"
            }
            
        except Exception as e:
            return {
                "available": False,
                "message": f"检查API密钥时发生错误: {str(e)}"
            }
    
    @staticmethod
    async def convert_files_to_dataset(
        files: List[str],
        output_file: str = "qa_dataset.jsonl",
        project_id: Optional[str] = None
    ) -> str:
        """将Markdown文件转换为问答数据集"""
        if not files:
            raise ValueError("文件列表不能为空")
        
        # 根据项目ID确定输出路径 - 修改路径结构
        if project_id:
            project_dir = os.path.join(settings.OUTPUT_DIR, str(project_id))
            os.makedirs(project_dir, exist_ok=True)
            output_path = os.path.join(project_dir, output_file)
        else:
            output_path = os.path.join("output", output_file)
            
        results = []
        print(f"开始转换 {len(files)} 个文件, 项目ID: {project_id}")
        
        # 获取默认模型配置
        models_list = SystemService._read_json_file(SystemService.MODELS_CONFIG_FILE, [])
        default_model = {}
        for model_config in models_list:
            if model_config.get("isDefault", False):
                default_model = model_config
                break
                
        # 如果找到默认模型，使用其配置
        model_name = default_model.get("model", "deepseek-chat")
        base_url = default_model.get("apiEndpoint", "https://api.deepseek.com")
        api_key = default_model.get("apiKey", settings.DEEPSEEK_API_KEY)
        print(f"model_name: {model_name}, base_url: {base_url}, api_key: {api_key}", {settings.DEEPSEEK_API_KEY})
        # 如果API密钥仍为空，返回错误
        if not api_key:
            raise ValueError("未配置API密钥，请在系统设置中配置默认模型API密钥或在函数调用时提供API密钥")
        
        # 获取提示词
        prompt = SystemService.get_prompts()
        system_prompt = prompt.get("data", "") + '\n确保JSON结构完整，所有括号和引号都正确闭合。如果内容过长，请分段但保持JSON结构完整性。'
        
        # 初始化转换状态
        task_key = output_file
        if project_id:
            task_key = f"{project_id}_{output_file}"
        conversion_state[task_key]["progress"] = 0
        # 生成任务ID
        task_id = str(uuid.uuid4())
        # 发送初始进度更新
        await manager.send_json({
            "task_id": task_id,
            "type": "md_to_dataset_convert_progress",
            "status": "started",
            "progress": 0,
            "total": len(files),
            "processed": 0,
            "successful": 0,
            "message": "开始调用大模型转换md文件为数据集, 转换速度取决于大模型的响应速度"
        }, project_id)
        print(f"开始调用大模型转换md文件为数据集, 项目ID: {project_id}")
        
        for i, file_path in enumerate(files):
            try:
                # 读取文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 调用API
                client = OpenAI(api_key=api_key, base_url=base_url)
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ],
                    stream=False
                )
                print(f"response ok: {file_path}")
                generated_text = response.choices[0].message.content
                finish_reason = response.choices[0].finish_reason
                print(f"获取到大模型的第 {i + 1} 个文件结果，长度为: {len(generated_text)}")
                # 如果该值为 length，则表明当前模型生成内容所包含的 Tokens 数量超过请求中的 max_tokens 参数
                print(f"finish_reason: {finish_reason}")
                # 检查返回结果是否完整
                if not generated_text:
                    logging.warning(f"大模型返回空内容，跳过文件: {file_path}")
                    continue

                # 解析JSON响应，先简单处理返回的格式问题，如果返回的JSON格式不正确，则尝试多次修复
                try:
                    # 去除可能的Markdown代码块标记
                    if generated_text.startswith("```"):
                        # 查找第一个和最后一个```
                        first_ticks = generated_text.find("\n", generated_text.find("```"))
                        last_ticks = generated_text.rfind("```")
                        if first_ticks != -1 and last_ticks != -1:
                            # 提取```之间的内容
                            generated_text = generated_text[first_ticks+1:last_ticks].strip()

                    # 检查返回结果是否被截断
                    is_truncated = not generated_text.strip().endswith('}') and '{' in generated_text
                    if is_truncated:
                        print(f"检测到第 {i + 1} 个文件的返回结果可能被截断，尝试修复...")
                        logging.warning(f"大模型返回结果可能被截断: 文件 {file_path}")
                        generated_text = DatasetService.fix_truncated_json(generated_text)
                    result = json.loads(generated_text)
                    
                    # 处理qa_pairs字段
                    if 'qa_pairs' in result and isinstance(result['qa_pairs'], list):
                        for qa_pair in result['qa_pairs']:
                            if isinstance(qa_pair, dict) and "question" in qa_pair and "answer" in qa_pair:
                                # 标准化处理QA对字段
                                standardized_qa_pair = DatasetService.standardize_qa_pair(qa_pair)
                                standardized_qa_pair["source"] = file_path
                                results.append(standardized_qa_pair)
                        # 更新进度
                        print(f"成功处理第 {i + 1} 个文件，生成 {len(results)} 个数据")
                        await manager.send_json({
                            "task_id": task_id,
                            "type": "md_to_dataset_convert_progress",
                            "status": "processing",
                            "progress": i + 1,
                            "total": len(files),
                            "processed": i + 1,
                            "successful": i + 1,
                            "message": f"成功处理第 {i + 1} 个文件，生成 {len(results)} 个数据"
                        }, project_id)
                    else:
                        logging.warning(f"API返回的JSON缺少'qa_pairs'字段或格式不符合预期")
                        # 更新进度
                        await manager.send_json({
                            "task_id": task_id,
                            "type": "md_to_dataset_convert_progress",
                            "status": "processing",
                            "progress": i + 1,
                            "total": len(files),
                            "processed": i + 1,
                            "successful": i + 1,
                            "message": f"第{i + 1} 个文件，大模型返回的字段或格式不符合预期"
                        }, project_id)
                except json.JSONDecodeError as e:
                    logging.error(f"JSON解析错误: {str(e)}")
                    
                    # 尝试更高级的JSON修复
                    try:
                        print(f"成功修复并处理第 {i + 1} 个文件：{generated_text}")
                        fixed_json = DatasetService.fix_complex_json_format(generated_text)
                        result = json.loads(fixed_json)
                        # print(f"成功修复并处理第 {i + 1} 个文件：{result}")
                        
                        # 处理qa_pairs字段
                        if 'qa_pairs' in result and isinstance(result['qa_pairs'], list):
                            for qa_pair in result['qa_pairs']:
                                if isinstance(qa_pair, dict) and "question" in qa_pair and "answer" in qa_pair:
                                    # 标准化处理QA对字段
                                    standardized_qa_pair = DatasetService.standardize_qa_pair(qa_pair)
                                    standardized_qa_pair["source"] = file_path
                                    results.append(standardized_qa_pair)
                            # 更新进度
                            print(f"成功修复并处理第 {i + 1} 个文件，生成 {len(results)} 个数据")
                            await manager.send_json({
                                "task_id": task_id,
                                "type": "md_to_dataset_convert_progress",
                                "status": "processing",
                                "progress": i + 1,
                                "total": len(files),
                                "processed": i + 1,
                                "successful": i + 1,
                                "message": f"成功修复并处理第 {i + 1} 个文件，生成 {len(results)} 个数据"
                            }, project_id)
                            continue
                    except Exception:
                        pass
                    
                    # 如果JSON修复失败，回退到基本的问答提取
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
                        qa_pair = {
                            "question": questions[i],
                            "answer": answers[i],
                            "source": file_path,
                            "label": "未分类"
                        }
                        # 标准化处理QA对字段
                        standardized_qa_pair = DatasetService.standardize_qa_pair(qa_pair)
                        results.append(standardized_qa_pair)
                        # 更新进度
                        await manager.send_json({
                            "task_id": task_id,
                            "type": "md_to_dataset_convert_progress",
                            "status": "processing",
                            "progress": i + 1,
                            "total": len(files),
                            "processed": i + 1,
                            "successful": i + 1,
                            "message": f"成功处理 {i + 1} 个文件，生成 {len(results)} 个数据"
                        }, project_id)
                
                # 更新进度
                conversion_state[task_key]["progress"] = i + 1
                
                # 避免API速率限制
                await asyncio.sleep(1)
                
            except Exception as e:
                logging.error(f"处理文件 {file_path} 时出错: {str(e)}")
                # 更新进度
                await manager.send_json({
                    "task_id": task_id,
                    "type": "md_to_dataset_convert_progress",
                    "status": "processing",
                    "progress": i + 1,
                    "total": len(files),
                    "processed": i + 1,
                    "successful": i + 1,
                    "message": f"处理文件第{i + 1} 个文件时出错"
                }, project_id)
        
        # 确保输出目录存在并以追加模式写入文件
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "a", encoding="utf-8") as f:
            for item in results:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        # 更新markdown_manager.json中相应文件的isDataset状态
        DatasetService.update_markdown_dataset_status(files, project_id)

        # 为没有id的数据行添加自增id
        DatasetService.add_missing_ids(output_file, project_id)
        
        print(f"提取了 {len(results)} 个问答对")
        # 更新进度
        await manager.send_json({
            "task_id": task_id,
            "type": "md_to_dataset_convert_progress",
            "status": "completed",
            "progress": len(files),
            "total": len(files),
            "processed": len(files),
            "successful": len(files),
            "message": f"成功提取 {len(results)} 数据"
        }, project_id)
        return output_path
    
    @staticmethod
    def update_markdown_dataset_status(files: List[str], project_id: Optional[str] = None) -> bool:
        """
        更新markdown_manager.json中文件的isDataset状态为True
        
        参数:
        - files: 需要更新的文件路径列表
        - project_id: 可选的项目ID
        
        返回:
        - bool: 是否成功更新了文件
        """
        try:
            # 根据项目ID确定manager文件路径
            if project_id:
                manager_dir = os.path.join(settings.OUTPUT_DIR, str(project_id))
                manager_path = os.path.join(manager_dir, "markdown_manager.json")
            else:
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
    
    @staticmethod
    def get_conversion_state(output_file: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """获取转换任务的状态"""
        # 用项目ID作为状态的key
        task_key = output_file
        if project_id:
            task_key = f"{project_id}_{output_file}"
            
        if task_key not in conversion_state:
            return {
                "status": "not_found",
                "message": "没有找到对应的转换任务",
                "progress": 0,
                "total": 0
            }
        
        return conversion_state[task_key]
    
    @staticmethod
    def add_qa_item(
        question: str,
        answer: str,
        chain_of_thought: Optional[str] = None,
        label: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """添加问答对到数据集"""
        if not question.strip() or not answer.strip():
            raise ValueError("问题和答案不能为空")
        
        # 根据项目ID获取数据集路径
        dataset_path = DatasetService.get_project_dataset_path(project_id)
        
        # 读取现有数据
        items = []
        if os.path.exists(dataset_path):
            try:
                with open(dataset_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            items.append(json.loads(line))
            except Exception as e:
                raise ValueError(f"读取数据集文件失败: {str(e)}")
        
        # 确定新ID
        new_id = 1
        if items:
            existing_ids = [item.get("id", 0) for item in items if "id" in item]
            if existing_ids:
                new_id = max(existing_ids) + 1
        
        # 创建新项
        now = datetime.now().isoformat()
        new_item = {
            "id": new_id,
            "question": question,
            "answer": answer,
            "chainOfThought": chain_of_thought if chain_of_thought else "",
            "label": label if label else "",
            "timestamp": now
        }
        
        # 添加到文件
        try:
            with open(dataset_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(new_item, ensure_ascii=False) + "\n")
        except Exception as e:
            raise ValueError(f"添加数据失败: {str(e)}")
        
        return {
            "status": "success",
            "message": "添加问答对成功",
            "data": new_item
        }
    
    @staticmethod
    def update_qa_item(
        id: int,
        question: str,
        answer: str,
        chain_of_thought: Optional[str] = None,
        label: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """更新问答对"""
        if not question.strip() or not answer.strip():
            raise ValueError("问题和答案不能为空")
        
        # 根据项目ID获取数据集路径
        dataset_path = DatasetService.get_project_dataset_path(project_id)
        
        if not os.path.exists(dataset_path):
            raise ValueError(f"数据集文件不存在")
        
        # 读取现有数据
        items = []
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        items.append(json.loads(line))
        except Exception as e:
            raise ValueError(f"读取数据集文件失败: {str(e)}")
        
        # 查找并更新项
        found = False
        for i, item in enumerate(items):
            if "id" in item and item["id"] == id:
                # 更新内容
                items[i]["question"] = question
                items[i]["answer"] = answer
                items[i]["chainOfThought"] = chain_of_thought if chain_of_thought else ""
                items[i]["label"] = label if label else ""
                items[i]["timestamp"] = datetime.now().isoformat()
                found = True
                updated_item = items[i]
                break
        
        if not found:
            raise ValueError(f"未找到ID为{id}的问答对")
        
        # 写回文件
        try:
            with open(dataset_path, "w", encoding="utf-8") as f:
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        except Exception as e:
            raise ValueError(f"更新数据失败: {str(e)}")
        
        return {
            "status": "success",
            "message": "更新问答对成功",
            "data": updated_item
        }
    
    @staticmethod
    def add_missing_ids(input_file: str = INPUT_FILE, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        为数据集中没有id的数据行添加自增id
        
        参数:
        - input_file: 输入文件路径，默认为qa_dataset.jsonl
        
        返回:
        - Dict[str, Any]: 包含操作状态信息的字典
        """
        file_path = DatasetService.get_project_dataset_path(project_id)
        if not os.path.exists(file_path):
            raise ValueError(f"文件 {file_path} 不存在")
        
        # 读取原始数据
        data = DatasetService.read_jsonl_file(file_path)
        if not data:
            return {
                "status": "warning",
                "message": "文件为空，无需处理",
                "total": 0,
                "updated": 0
            }
        
        # 备份原始文件
        # backup_path = os.path.join(settings.OUTPUT_DIR, f"{input_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        # try:
        #     shutil.copy2(file_path, backup_path)
        # except Exception as e:
        #     logging.warning(f"备份原始文件失败: {str(e)}")
        
        # 为没有id的数据项添加id
        current_id = 1
        updated_count = 0
        
        for item in data:
            if "id" not in item:
                item["id"] = current_id
                updated_count += 1
            else:
                # 如果已有id且为数字，更新当前id以保持递增
                try:
                    if isinstance(item["id"], (int, float)):
                        current_id = max(current_id, int(item["id"]) + 1)
                except (ValueError, TypeError):
                    pass
            current_id += 1
        
        # 将更新后的数据写回文件
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        except Exception as e:
            raise ValueError(f"写入更新后的数据集失败: {str(e)}")
        
        return {
            "status": "success",
            "message": f"成功为 {updated_count} 条数据添加id",
            "total": len(data),
            "updated": updated_count
        }
    
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
                    "messages": [
                        {
                            "role": "user",
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
    
    @staticmethod
    def fix_json_format(json_text):
        """修复常见的JSON格式问题"""
        import re
        
        # 如果输入为空，返回有效的空JSON对象
        if not json_text or not json_text.strip():
            return "{}"
            
        # 1. 替换单引号为双引号
        result = json_text.replace("'", "\"")
        
        # 2. 确保属性名使用双引号
        result = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', result)
        
        # 3. 修复尾部逗号问题
        result = re.sub(r',\s*}', '}', result)
        result = re.sub(r',\s*]', ']', result)
        
        # 4. 删除注释
        result = re.sub(r'//.*?\n', '\n', result)
        result = re.sub(r'/\*.*?\*/', '', result, flags=re.DOTALL)
        
        # 5. 全面处理无效的控制字符（包括不可见控制字符和无效Unicode）
        # 仅保留合法的字符：可打印字符、换行、回车、制表符
        result = ''.join(ch for ch in result if (ch >= ' ' and ord(ch) < 127) or ch in ['\n', '\r', '\t'])
        
        # 6. 替换不规范的转义序列
        result = re.sub(r'\\([^"\\/bfnrtu])', r'\1', result)
        
        # 7. 修复常见编码问题，替换非ASCII字符
        result = re.sub(r'[\x80-\xff]', ' ', result)
        
        # 8. 修复缺少逗号的问题 - 在任何一个右括号或右引号后面跟着左引号的地方插入逗号
        result = re.sub(r'([\}\]])\s*(\")', r'\1,\2', result)
        result = re.sub(r'(\")(\s*\"[^\"]*\":\s*)', r'\1,\2', result)  # "key": "value" "key2": "value2" => "key": "value", "key2": "value2"
        
        return result
    
    @staticmethod
    def fix_truncated_json(json_text):
        """修复被截断的JSON字符串"""
        import re
        
        if not json_text:
            return json_text
        
        # 移除首尾空白
        json_text = json_text.strip()
        
        # 如果JSON以{开始但没有以}结束，说明可能被截断
        if json_text.startswith('{') and not json_text.endswith('}'):
            # 尝试找到最后一个完整的对象或数组
            
            # 1. 找到最后一个完整的键值对
            last_complete_pair_pos = -1
            brace_count = 0
            in_string = False
            escape_next = False
            
            for i, char in enumerate(json_text):
                if escape_next:
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                    
                if in_string:
                    continue
                    
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 1:  # 回到主对象层级
                        last_complete_pair_pos = i
                elif char == ',' and brace_count == 1:
                    last_complete_pair_pos = i
            
            # 2. 如果找到了最后完整的位置，截断到那里
            if last_complete_pair_pos > 0:
                # 检查最后是否是逗号，如果是则移除它
                truncated = json_text[:last_complete_pair_pos].rstrip()
                if truncated.endswith(','):
                    truncated = truncated[:-1]
                json_text = truncated
            
            # 3. 处理未闭合的字符串
            quote_count = json_text.count('"')
            # 计算转义字符的影响
            escaped_quotes = len(re.findall(r'\\"', json_text))
            actual_quotes = quote_count - escaped_quotes
            
            if actual_quotes % 2 != 0:
                # 有未闭合的字符串，在适当位置添加闭合引号
                json_text += '"'
            
            # 4. 添加缺失的右花括号和方括号
            open_braces = json_text.count('{') - json_text.count('}')
            open_brackets = json_text.count('[') - json_text.count(']')
            
            # 先闭合数组，再闭合对象
            json_text += ']' * open_brackets
            json_text += '}' * open_braces
            
        return json_text
    
    @staticmethod
    def fix_complex_json_format(json_text):
        """处理更复杂的JSON格式问题"""
        print(f"仍然解析失败，尝试提取文本中的问答对")
        import re
        
        # 0. 尝试保存原始输入，以便在所有修复尝试失败时使用基本文本提取
        original_text = json_text

        # 1. 首先应用基本修复
        result = DatasetService.fix_json_format(json_text)
        
        # 2. 尝试从文本中提取JSON部分
        # 查找 { 开始到最后一个 } 的内容
        json_match = re.search(r'({.*})', result, re.DOTALL)
        if json_match:
            result = json_match.group(1)
        
        # 3. 检查并补全缺失的引号
        # 查找可能缺少引号的键
        result = re.sub(r'([{,])\s*([a-zA-Z0-9_]+)\s*:', r'\1"\2":', result)
        
        # 4. 修复未终止的字符串（如果引号数量为奇数）
        # 计算双引号出现次数
        quote_count = result.count('"')
        if quote_count % 2 != 0:
            # 找到最后一个未闭合的引号位置
            open_quotes = []
            for i, char in enumerate(result):
                if char == '"' and (i == 0 or result[i-1] != '\\'):
                    if len(open_quotes) == 0:
                        open_quotes.append(i)
                    else:
                        open_quotes.pop()
            
            # 如果存在未闭合的引号，在其后添加一个闭合引号
            if open_quotes:
                last_open = open_quotes[-1]
                next_comma = result.find(',', last_open)
                next_closing = result.find('}', last_open)
                next_bracket = result.find(']', last_open)
                
                insertion_point = len(result)
                if next_comma > 0:
                    insertion_point = min(insertion_point, next_comma)
                if next_closing > 0:
                    insertion_point = min(insertion_point, next_closing)
                if next_bracket > 0:
                    insertion_point = min(insertion_point, next_bracket)
                
                result = result[:insertion_point] + '"' + result[insertion_point:]
        
        # 5. 添加缺失的逗号
        # 更复杂的逗号修复 - 使用正则表达式查找缺失逗号的模式
        # 在右括号或引号后面跟着左引号的地方添加逗号
        result = re.sub(r'(["\d}])\s*(")', r'\1,\2', result)
        # 修复JSON对象中键值对之间缺少的逗号
        result = re.sub(r'(:\s*["\w\d.\[\]{}]+)\s+(")', r'\1,\2', result)
        
        # 5.5 修复缺少冒号分隔符的情况 - 处理 "Expecting ':' delimiter" 错误
        # 查找键名后面缺少冒号的模式
        result = re.sub(r'(["]\s*[a-zA-Z0-9_]+\s*["]\s*)(\s*["{[])', r'\1:\2', result)
        # 查找键值对中间缺少冒号的模式 - 引号内的键名与引号值之间
        result = re.sub(r'(["]\s*[a-zA-Z0-9_]+\s*["]\s*)([^:{\[])', r'\1:\2', result)
        # 处理无引号的键名和值之间缺少冒号的情况
        result = re.sub(r'([a-zA-Z0-9_"]+)\s+([a-zA-Z0-9_"{[])', r'\1:\2', result)
        
        # 6. 修复嵌套结构中的错误
        # 添加缺失的右括号
        # 计算左右括号数量
        left_braces = result.count('{')
        right_braces = result.count('}')
        if left_braces > right_braces:
            result += '}' * (left_braces - right_braces)
        
        # 计算左右方括号数量
        left_brackets = result.count('[')
        right_brackets = result.count(']')
        if left_brackets > right_brackets:
            result += ']' * (left_brackets - right_brackets)
        
        # 7. 如果JSON格式仍有问题，尝试提取问答对
        try:
            # 尝试解析修复后的结果
            json.loads(result)
        except Exception:
            # 如果仍然解析失败，尝试提取文本中的问答对
            try:
                # 清除之前的修复尝试，从原始文本中提取问答对
                qa_pairs = DatasetService.extract_qa_pairs_from_text(original_text)
                if qa_pairs:
                    return json.dumps({"qa_pairs": qa_pairs}, ensure_ascii=False)
            except Exception:
                pass
        
        # 8. 最后，尝试一次自动修复 - 将结果解析为Python对象然后重新序列化为JSON
        try:
            # 尝试解析修复后的结果
            parsed_data = json.loads(result)
            # 然后重新序列化为标准JSON，确保格式正确
            result = json.dumps(parsed_data, ensure_ascii=False)
        except Exception:
            # 如果仍然解析失败，保留现有的修复结果
            pass
        
        return result

    @staticmethod
    def extract_qa_pairs_from_text(text):
        """从非JSON文本中提取问答对"""
        import re
        
        # 如果文本为空，返回空列表
        if not text or not text.strip():
            return []
        
        qa_pairs = []
        
        # 首先尝试使用常见问答格式（问题：答案：）
        questions = []
        answers = []
        current_answer = ""
        current_question = None
        
        # 处理中文冒号和英文冒号
        for line in text.split('\n'):
            # 去除首尾空白
            line = line.strip()
            if not line:
                continue
                
            # 检查是否是问题行
            q_match = re.search(r'^(问题|Q|Question)[:：]?\s*(.*)', line, re.IGNORECASE)
            if q_match:
                # 如果已有问题和答案，保存前一对
                if current_question and current_answer:
                    qa_pairs.append({
                        "question": current_question.strip(),
                        "answer": current_answer.strip()
                    })
                
                # 开始新的问答对
                current_question = q_match.group(2).strip()
                current_answer = ""
                continue
                
            # 检查是否是答案行
            a_match = re.search(r'^(答案|A|Answer)[:：]?\s*(.*)', line, re.IGNORECASE)
            if a_match:
                # 如果已有问题，设置答案
                if current_question:
                    current_answer = a_match.group(2).strip()
                continue
                
            # 如果不是问题或答案开头，添加到当前答案
            if current_question and line:
                if current_answer:
                    current_answer += " " + line
                else:
                    current_answer = line
        
        # 添加最后一对问答
        if current_question and current_answer:
            qa_pairs.append({
                "question": current_question.strip(),
                "answer": current_answer.strip()
            })
        
        # 如果没有找到问答对，尝试其他提取方法
        if not qa_pairs:
            # 寻找可能的问题-答案模式
            pairs = re.findall(r'["《]([^"》]+)["》][：:]\s*["《]([^"》]+)["》]', text)
            for q, a in pairs:
                qa_pairs.append({
                    "question": q.strip(),
                    "answer": a.strip()
                })
        
        return qa_pairs

    # 添加新的静态方法用于标准化问答对字段
    @staticmethod
    def standardize_qa_pair(qa_pair: Dict) -> Dict:
        """
        标准化处理问答对字段，确保字段名称正确映射
        
        参数:
        - qa_pair: 原始问答对字典
        
        返回:
        - 标准化后的问答对字典
        """
        # 创建一个新的字典用于存储标准化字段
        result = {}
        
        # 1. 处理问题字段 - 尝试多种可能的键名
        question_key = None
        for key in ["question", "prompt", "instruction", "query", "问题", "q", "Q"]:
            if key in qa_pair:
                question_key = key
                break
        
        if question_key:
            result["question"] = qa_pair[question_key]
        else:
            # 如果找不到问题字段，使用空字符串
            result["question"] = ""
        
        # 2. 处理答案字段 - 尝试多种可能的键名
        answer_key = None
        for key in ["answer", "response", "output", "completion", "答案", "a", "A"]:
            if key in qa_pair:
                answer_key = key
                break
        
        if answer_key:
            result["answer"] = qa_pair[answer_key]
        else:
            # 如果找不到答案字段，使用空字符串
            result["answer"] = ""
        
        # 3. 处理标签字段 - 尝试多种可能的键名
        label_key = None
        for key in ["label", "category", "tag", "type", "标签", "分类"]:
            if key in qa_pair:
                label_key = key
                break
        
        if label_key:
            result["label"] = qa_pair[label_key]
        elif "metadata" in qa_pair and isinstance(qa_pair["metadata"], dict) and "label" in qa_pair["metadata"]:
            # 检查元数据中是否有标签
            result["label"] = qa_pair["metadata"]["label"]
        else:
            # 如果找不到标签字段，设为未分类
            result["label"] = "未分类"
        
        # 4. 处理思维链字段
        cot_key = None
        for key in ["chainOfThought", "chain_of_thought", "reasoning", "思考过程", "分析"]:
            if key in qa_pair:
                cot_key = key
                break
        
        if cot_key:
            result["chainOfThought"] = qa_pair[cot_key]
        else:
            result["chainOfThought"] = ""
        
        # 5. 保留源文件信息
        if "source" in qa_pair:
            result["source"] = qa_pair["source"]
        
        # 6. 保留ID (如果存在)
        if "id" in qa_pair:
            result["id"] = qa_pair["id"]
        
        # 7. 添加时间戳 (如果不存在)
        if "timestamp" not in qa_pair:
            result["timestamp"] = datetime.now().isoformat()
        else:
            result["timestamp"] = qa_pair["timestamp"]
        return result
