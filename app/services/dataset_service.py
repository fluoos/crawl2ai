import os
import json
import logging
import shutil
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import asyncio
from openai import OpenAI

from app.core.config import settings
from app.services.system_service import SystemService

# 常量定义 - 使用settings中的配置
EXPORT_FORMATS = settings.SUPPORTED_FORMATS
DATASET_STYLES = settings.SUPPORTED_STYLES
INPUT_FILE = os.path.join(settings.OUTPUT_DIR, "qa_dataset.jsonl")

# 在内存中存储转换状态
conversion_state = {}

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
        input_file: str = "qa_dataset.jsonl", 
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """预览数据转换结果"""
        # 读取原始数据
        file_path = os.path.join(settings.OUTPUT_DIR, input_file)
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
        existing_ids = {item.get("id") for item in items if "id" in item}
        invalid_ids = [id for id in ids if id not in existing_ids]
        if invalid_ids:
            raise ValueError(f"无效的ID: {invalid_ids}")
        
        # 备份原始文件
        # backup_path = os.path.join(settings.OUTPUT_DIR, f"qa_dataset.jsonl.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        # try:
        #     shutil.copy2(dataset_path, backup_path)
        # except Exception as e:
        #     logging.warning(f"备份原始文件失败: {str(e)}")
        
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
    def get_download_file_path(style: str, filename: str) -> str:
        """获取下载文件的路径"""
        file_path = os.path.join(settings.EXPORT_DIR, style, filename)
        if not os.path.exists(file_path):
            raise ValueError("文件不存在")
        return file_path
    
    # Markdown转换相关功能
    
    @staticmethod
    def save_conversion_task_status(files: List[str], model: str, output_file: str) -> Dict[str, Any]:
        """启动文件转换任务"""
        
        # 更新转换状态
        conversion_state[output_file] = {
            "status": "running",
            "message": "转换任务正在进行中...",
            "progress": 0,
            "total": len(files)
        }
        
        return {"status": "success", "message": "转换任务已开始"}
    
    @staticmethod
    async def convert_files_to_dataset_task(files: List[str], model: str, output_file: str, api_key: str = None):
        """转换文件到数据集的后台任务"""
        print(f"正在转换 {len(files)} 个文件")
        try:
            await DatasetService.convert_files_to_dataset(files, model, output_file, api_key)
            conversion_state[output_file]["status"] = "completed"
            conversion_state[output_file]["message"] = "转换任务已完成"
            conversion_state[output_file]["progress"] = conversion_state[output_file]["total"]
        except Exception as e:
            conversion_state[output_file]["status"] = "failed"
            conversion_state[output_file]["message"] = f"转换任务失败: {str(e)}"
            logging.error(f"转换任务失败: {str(e)}")
    
    @staticmethod
    async def convert_files_to_dataset(
        files: List[str],
        model: str = "deepseek",
        output_file: str = "qa_dataset.jsonl",
        api_key: str = None
    ) -> str:
        """将Markdown文件转换为问答数据集"""
        if not files:
            raise ValueError("文件列表不能为空")
        
        output_path = os.path.join("output", output_file)
        results = []
        print(f"开始转换 {len(files)} 个文件")
        
        # 使用默认配置
        if api_key is None:
            api_key = settings.DEEPSEEK_API_KEY
        
        # 获取提示词
        prompt = SystemService.get_prompts()
        system_prompt = prompt.get("data", "")
        
        # 初始化转换状态
        conversion_state[output_file]["progress"] = 0
        
        # 根据model参数选择实际的API模型名称
        model_name = "deepseek-chat"  # DeepSeek API使用的实际模型名称
        
        for i, file_path in enumerate(files):
            try:
                # 读取文件内容
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # 调用API
                client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
                response = client.chat.completions.create(
                    model=model_name,  # 使用正确的模型名称
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": content}
                    ],
                    stream=False
                )
                generated_text = response.choices[0].message.content
                
                # 解析JSON响应
                try:
                    # 去除可能的Markdown代码块标记
                    if generated_text.startswith("```"):
                        # 查找第一个和最后一个```
                        first_ticks = generated_text.find("\n", generated_text.find("```"))
                        last_ticks = generated_text.rfind("```")
                        if first_ticks != -1 and last_ticks != -1:
                            # 提取```之间的内容
                            generated_text = generated_text[first_ticks+1:last_ticks].strip()
                        
                    result = json.loads(generated_text)
                    
                    # 处理qa_pairs字段
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
        
        # 确保输出目录存在并以追加模式写入文件
        os.makedirs("output", exist_ok=True)
        with open(output_path, "a", encoding="utf-8") as f:
            for item in results:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        # 更新markdown_manager.json中相应文件的isDataset状态
        DatasetService.update_markdown_dataset_status(files)

        # 为没有id的数据行添加自增id
        DatasetService.add_missing_ids(output_file)
        
        print(f"提取了 {len(results)} 个问答对")
        return output_path
    
    @staticmethod
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
    def get_conversion_state(output_file: str) -> Dict[str, Any]:
        """获取转换任务的状态"""
        if output_file in conversion_state:
            return conversion_state[output_file]
        return {
            "status": "not_found",
            "message": "转换任务不存在",
            "progress": 0,
            "total": 0
        }
    
    @staticmethod
    def add_qa_item(
        question: str,
        answer: str,
        chain_of_thought: Optional[str] = None,
        label: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        向数据集中添加一个新的问答对
        
        参数:
        - question: 问题内容
        - answer: 答案内容
        - chain_of_thought: 思考链，可选
        - label: 分类标签，可选
        
        返回:
        - Dict[str, Any]: 包含操作状态信息的字典
        """
        if not question or not answer:
            raise ValueError("问题和答案不能为空")
        
        # 确保输出目录存在
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        
        # 读取现有数据以找到最大id
        dataset_path = os.path.join(settings.OUTPUT_DIR, "qa_dataset.jsonl")
        max_id = 0
        
        if os.path.exists(dataset_path):
            try:
                data = DatasetService.read_jsonl_file(dataset_path)
                for item in data:
                    if "id" in item and isinstance(item["id"], (int, float)):
                        max_id = max(max_id, int(item["id"]))
            except Exception as e:
                logging.warning(f"读取数据集获取最大id时出错: {str(e)}")
        
        # 构建问答对数据
        qa_item = {
            "id": max_id + 1,
            "question": question,
            "answer": answer
        }
        
        # 添加可选字段
        if chain_of_thought:
            qa_item["chainOfThought"] = chain_of_thought
            
        if label:
            qa_item["label"] = label
            
        # 写入数据
        try:
            with open(dataset_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(qa_item, ensure_ascii=False) + "\n")
            
            # 获取更新后的统计信息
            stats = DatasetService.get_stats()
            
            return {
                "status": "success",
                "message": "问答对添加成功",
                "qa_item": qa_item,
                "stats": stats
            }
        except Exception as e:
            logging.error(f"添加问答对失败: {str(e)}")
            raise ValueError(f"添加问答对失败: {str(e)}")
    
    @staticmethod
    def add_missing_ids(input_file: str = INPUT_FILE) -> Dict[str, Any]:
        """
        为数据集中没有id的数据行添加自增id
        
        参数:
        - input_file: 输入文件路径，默认为qa_dataset.jsonl
        
        返回:
        - Dict[str, Any]: 包含操作状态信息的字典
        """
        file_path = os.path.join(settings.OUTPUT_DIR, input_file)
        if not os.path.exists(file_path):
            raise ValueError(f"文件 {input_file} 不存在")
        
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
        backup_path = os.path.join(settings.OUTPUT_DIR, f"{input_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")
        try:
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            logging.warning(f"备份原始文件失败: {str(e)}")
        
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
    
    @staticmethod
    def update_qa_item(
        id: int,
        question: str,
        answer: str,
        chain_of_thought: Optional[str] = None,
        label: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        编辑数据集中的问答对
        
        参数:
        - id: 要编辑的问答对ID
        - question: 更新后的问题内容
        - answer: 更新后的答案内容
        - chain_of_thought: 更新后的思考链，可选
        - label: 更新后的分类标签，可选
        
        返回:
        - Dict[str, Any]: 包含操作状态信息的字典
        """
        if not question or not answer:
            raise ValueError("问题和答案不能为空")
            
        dataset_path = os.path.join(settings.OUTPUT_DIR, "qa_dataset.jsonl")
        
        if not os.path.exists(dataset_path):
            raise ValueError("数据集文件不存在")
        
        # 读取所有数据
        items = []
        try:
            with open(dataset_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        items.append(json.loads(line))
        except Exception as e:
            raise ValueError(f"读取数据集文件失败: {str(e)}")
            
        # 查找并更新指定ID的项
        found = False
        for item in items:
            if "id" in item and item["id"] == id:
                item["question"] = question
                item["answer"] = answer
                
                # 更新可选字段
                if chain_of_thought is not None:
                    item["chainOfThought"] = chain_of_thought
                elif "chainOfThought" in item:
                    # 如果前端没有提供该字段且原数据有该字段，保留原值
                    pass
                    
                if label is not None:
                    item["label"] = label
                elif "label" in item:
                    # 如果前端没有提供该字段且原数据有该字段，保留原值
                    pass
                    
                found = True
                break
                
        if not found:
            raise ValueError(f"未找到ID为 {id} 的问答对")
            
        # 将更新后的数据写回文件
        try:
            with open(dataset_path, "w", encoding="utf-8") as f:
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        except Exception as e:
            raise ValueError(f"写入更新后的数据集失败: {str(e)}")
            
        # 获取更新后的统计信息
        stats = DatasetService.get_stats()
        
        return {
            "status": "success",
            "message": f"成功更新ID为 {id} 的问答对",
            "updated_item": {
                "id": id,
                "question": question,
                "answer": answer,
                "chainOfThought": chain_of_thought,
                "label": label
            },
            "stats": stats
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
