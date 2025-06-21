import os
import json
import uuid
from typing import Dict, Any, List

import requests
from app.core.config import settings
from app.utils.path_utils import join_paths, get_config_path

class SystemService:
    """系统服务类，处理所有与系统配置相关的业务逻辑"""
    
    MODELS_CONFIG_FILE = settings.MODELS_CONFIG_FILE
    PROMPTS_CONFIG_FILE = settings.PROMPTS_CONFIG_FILE
    FILE_STRATEGY_CONFIG_FILE = settings.FILE_STRATEGY_CONFIG_FILE

    @staticmethod
    def _read_json_file(filename, default_value=None):
        """读取JSON文件，如果文件不存在则返回默认值"""
        file_path = get_config_path(filename)
        print(f"尝试读取文件: {file_path}")
        try:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                print(f"文件不存在，返回默认值: {default_value}")
                return default_value
        except Exception as e:
            print(f"读取文件 {file_path} 时出错: {str(e)}")
            return default_value
    
    @staticmethod
    def _write_json_file(filename, data):
        """写入JSON文件"""
        try:
            file_path = get_config_path(filename)
            print(f"尝试写入文件: {file_path}")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"文件 {file_path} 写入成功")
        except Exception as e:
            print(f"写入文件 {file_path} 时出错: {str(e)}")
            raise e
    
    @staticmethod
    def get_default_models():
        """获取默认的模型提供商配置"""
        return [
            {
                "id": "1",
                "name": "Ollama",
                "apiEndpoint": "http://127.0.0.1:11434/api",
                "type": "chat",
                "temperature": 0.7,
                "maxTokens": 4000,
                "isDefault": False,
                "apiKey": "",
                "model": "llama3.1:8b"
            },
            {
                "id": "2",
                "name": "DeepSeek",
                "apiEndpoint": "https://api.deepseek.com/v1/",
                "type": "chat",
                "temperature": 0.7,
                "maxTokens": 4000,
                "isDefault": False,
                "apiKey": "",
                "model": "deepseek-chat"
            },
            {
                "id": "3",
                "name": "OpenAI",
                "apiEndpoint": "https://api.openai.com/v1/",
                "type": "chat",
                "temperature": 0.7,
                "maxTokens": 4000,
                "isDefault": False,
                "apiKey": "",
                "model": "gpt-4o"
            },
            {
                "id": "4",
                "name": "OpenAI",
                "apiEndpoint": "https://api.openai.com/v1/",
                "type": "chat",
                "temperature": 0.7,
                "maxTokens": 4000,
                "isDefault": False,
                "apiKey": "",
                "model": "gpt-4o-mini"
            },
            {
                "id": "5",
                "name": "OpenAI",
                "apiEndpoint": "https://api.openai.com/v1/",
                "type": "chat",
                "temperature": 0.7,
                "maxTokens": 4000,
                "isDefault": False,
                "apiKey": "",
                "model": "o1-mini"
            },
            {
                "id": "6",
                "name": "硅基流动",
                "apiEndpoint": "https://api.siliconflow.cn/v1/",
                "type": "chat",
                "temperature": 0.7,
                "maxTokens": 4000,
                "isDefault": False,
                "apiKey": "",
                "model": "deepseek-ai/DeepSeek-R1"
            },
            {
                "id": "7",
                "name": "智谱AI",
                "apiEndpoint": "https://open.bigmodel.cn/api/paas/v4/",
                "type": "chat",
                "temperature": 0.7,
                "maxTokens": 4000,
                "isDefault": False,
                "apiKey": "",
                "model": "glm-4-flash"
            },
            {
                "id": "8",
                "name": "Groq",
                "apiEndpoint": "https://api.groq.com/openai",
                "type": "chat",
                "temperature": 0.7,
                "maxTokens": 4000,
                "isDefault": False,
                "apiKey": "",
                "model": "Gemma 7B"
            },
            {
                "id": "9",
                "name": "阿里云百炼",
                "apiEndpoint": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                "type": "chat",
                "temperature": 0.7,
                "maxTokens": 4000,
                "isDefault": False,
                "apiKey": "",
                "model": "qwen-max-latest"
            },
            {
                "id": "d7a4b3f3-a8c8-4e51-8a2e-7008321753fd",
                "name": "kimi",
                "model": "moonshot-v1-32k",
                "apiEndpoint": "https://api.moonshot.cn/v1",
                "apiKey": "",
                "type": "chat",
                "temperature": 0.7,
                "maxTokens": 4000,
                "isDefault": False
            }
        ]
    
    @staticmethod
    def get_models() -> Dict[str, Any]:
        """获取所有模型配置"""
        models_list = SystemService._read_json_file(SystemService.MODELS_CONFIG_FILE, [])
        
        # 如果没有模型数据
        if len(models_list) == 0:
            print("如果没有模型数据，写入默认模型")
            models_list = SystemService.get_default_models()
        
        # 确保目录存在并保存更新的配置
        SystemService._write_json_file(SystemService.MODELS_CONFIG_FILE, models_list)
        
        # 遍历所有模型，对API密钥进行掩码处理
        for model in models_list:
            if model.get("apiKey"):
                model["apiKey"] = "******" + model["apiKey"][-4:] if len(model["apiKey"]) > 4 else "******"
        return {
            "data": models_list,
            "total": len(models_list),
        }
    
    @staticmethod
    def add_model(model_data: Dict[str, Any]) -> Dict[str, Any]:
        """添加模型配置"""
        print(f"添加模型配置: {model_data}")
        # 读取现有模型列表
        models_list = SystemService._read_json_file(SystemService.MODELS_CONFIG_FILE, [])

        # 如果没有模型数据
        if len(models_list) == 0:
            print("如果没有模型数据，写入默认模型")
            models_list = SystemService.get_default_models()
        
        # 生成ID
        custom_item = {}
        custom_item["id"] = str(uuid.uuid4())
        
        # 复制模型数据到新对象
        try:
            required_fields = ["name", "apiEndpoint", "apiKey", "model"]
            for field in required_fields:
                if field not in model_data:
                    return {"status": "error", "message": f"缺少必要字段: {field}"}
                custom_item[field] = model_data[field]
            
            # 处理可选字段
            custom_item["isDefault"] = model_data.get("isDefault", False)
        except KeyError as e:
            return {"status": "error", "message": f"缺少必要字段: {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"处理模型数据时出错: {str(e)}"}

        if custom_item.get("isDefault", False):
            # 将其他模型设置为非默认
            for model in models_list:
                model["isDefault"] = False

        models_list.append(custom_item)

        # 保存配置
        SystemService._write_json_file(SystemService.MODELS_CONFIG_FILE, models_list)
        
        return {"status": "success", "message": "模型已添加", "id": custom_item["id"]}
    
    @staticmethod
    def update_model(model_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新模型配置"""
        print(f"更新模型配置: {model_data}")
        # 读取现有模型列表
        models_list = SystemService._read_json_file(SystemService.MODELS_CONFIG_FILE, [])
        
        # 检查必要字段
        try:
            if "id" not in model_data:
                return {"status": "error", "message": "缺少必要字段: id"}
                
            required_fields = ["name", "apiEndpoint", "apiKey", "model"]
            for field in required_fields:
                if field not in model_data:
                    return {"status": "error", "message": f"缺少必要字段: {field}"}
        except Exception as e:
            return {"status": "error", "message": f"处理模型数据时出错: {str(e)}"}
        
        # 查找要更新的模型
        model_found = False
        for i, model in enumerate(models_list):
            if model["id"] == model_data["id"]:
                # 如果API密钥是掩码版本，保留原始API密钥
                if model_data.get("apiKey", "").startswith("******"):
                    model_data["apiKey"] = model["apiKey"]
                
                # 处理可选字段，保留原值如果没有提供
                model_data["type"] = model_data.get("type", model.get("type", "chat"))
                model_data["temperature"] = model_data.get("temperature", model.get("temperature", 0.7))
                model_data["maxTokens"] = model_data.get("maxTokens", model.get("maxTokens", 4000))
                model_data["isDefault"] = model_data.get("isDefault", model.get("isDefault", False))
                
                # 检查是否设置为默认模型
                if model_data.get("isDefault", False) and not model.get("isDefault", False):
                    # 将其他模型设置为非默认
                    for m in models_list:
                        if m["id"] != model_data["id"]:
                            m["isDefault"] = False
                
                # 更新模型信息
                models_list[i] = model_data
                model_found = True
                break
        
        if not model_found:
            return {"status": "error", "message": "找不到指定的模型"}
        
        # 保存配置
        SystemService._write_json_file(SystemService.MODELS_CONFIG_FILE, models_list)
        
        return {"status": "success", "message": "模型已更新"}
    
    @staticmethod
    def delete_model(model_id: str) -> Dict[str, Any]:
        """删除模型配置"""
        print(f"删除模型配置，ID: {model_id}")
        # 读取现有模型列表
        models_list = SystemService._read_json_file(SystemService.MODELS_CONFIG_FILE, [])
        
        # 检查模型ID是否有效
        if not model_id:
            return {"status": "error", "message": "未提供有效的模型ID"}
        
        # 查找要删除的模型
        model_to_delete = None
        for i, model in enumerate(models_list):
            if model["id"] == model_id:
                model_to_delete = model
                models_list.pop(i)
                break
        
        if not model_to_delete:
            return {"status": "error", "message": "找不到指定的模型"}
        
        # 如果删除的是默认模型，且还有其他模型，则将第一个模型设置为默认
        if model_to_delete.get("isDefault", False) and models_list:
            models_list[0]["isDefault"] = True
            print(f"已将模型 {models_list[0]['name']} 设置为新的默认模型")
        
        # 保存配置
        SystemService._write_json_file(SystemService.MODELS_CONFIG_FILE, models_list)
        
        return {"status": "success", "message": "模型已删除"}
    
    @staticmethod
    def set_default_model(model_id: str) -> Dict[str, Any]:
        """设置默认模型"""
        print(f"设置默认模型，ID: {model_id}")
        # 读取现有模型列表
        models_list = SystemService._read_json_file(SystemService.MODELS_CONFIG_FILE, [])
        
        # 检查模型ID是否有效
        if not model_id:
            return {"status": "error", "message": "未提供有效的模型ID"}
        
        # 查找要设置为默认的模型
        model_found = False
        for model in models_list:
            if model["id"] == model_id:
                model["isDefault"] = True
                model_found = True
                print(f"已将模型 {model['name']} 设置为默认")
            else:
                model["isDefault"] = False
        
        if not model_found:
            return {"status": "error", "message": "找不到指定的模型"}
        
        # 保存配置
        SystemService._write_json_file(SystemService.MODELS_CONFIG_FILE, models_list)
        
        return {"status": "success", "message": "已将模型设置为默认"}
    
    @staticmethod
    def get_prompts() -> Dict[str, Any]:
        """获取提示词配置"""
        prompt = SystemService._read_json_file(SystemService.PROMPTS_CONFIG_FILE, {})
        if prompt.get("data", "") == "":
            default_prompts = {
                "data": """
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

    请按照上述JSON格式,注意一定要严格按照JSON格式返回, 返回前先检查是否符合JSON格式。
    """
        }
            SystemService._write_json_file(SystemService.PROMPTS_CONFIG_FILE, default_prompts)
            prompt = default_prompts
        
        return prompt
    
    @staticmethod
    def update_prompts(prompts_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新提示词配置"""
        default_prompts = {
            "data": prompts_data
        }
        print(f"更新提示词配置: {default_prompts}")
        # 保存配置
        SystemService._write_json_file(SystemService.PROMPTS_CONFIG_FILE, default_prompts)
        
        return {"status": "success", "message": "提示词配置已更新"}
    
    @staticmethod
    def reset_prompts() -> Dict[str, Any]:
        """重置提示词配置"""
        default_prompts = {
            "data": ""
        }
        SystemService._write_json_file(SystemService.PROMPTS_CONFIG_FILE, default_prompts)
        return {"status": "success", "message": "提示词配置已重置"}
    
    @staticmethod
    def get_file_strategy() -> Dict[str, Any]:
        """获取文件策略配置"""
        default_strategy = {
            "data": {
                "enableSmartSplit": True,
                "maxTokens": 8000,
                "minTokens": 300,
                "splitStrategy": "balanced"
            }
        }
        strategy = SystemService._read_json_file(SystemService.FILE_STRATEGY_CONFIG_FILE, {})
        if strategy.get("data", "") == "":
            strategy = default_strategy
            SystemService._write_json_file(SystemService.FILE_STRATEGY_CONFIG_FILE, strategy)
        
        return strategy
    
    @staticmethod
    def update_file_strategy(strategy_data: Dict[str, Any]) -> Dict[str, Any]:
        """更新文件策略配置"""
        print(f"更新文件策略配置: {strategy_data}")
        default_strategy = {
            "data": strategy_data
        }
        # 保存配置
        SystemService._write_json_file(SystemService.FILE_STRATEGY_CONFIG_FILE, default_strategy)
        
        return {"status": "success", "message": "文件策略配置已更新"}
    
    @staticmethod
    def reset_file_strategy() -> Dict[str, Any]:
        """重置文件策略配置"""
        default_strategy = {
            "data": {
                "enableSmartSplit": True,
                "maxTokens": 8000,
                "minTokens": 300,
                "splitStrategy": "balanced"
            }
        }
        SystemService._write_json_file(SystemService.FILE_STRATEGY_CONFIG_FILE, default_strategy)
        return {"status": "success", "message": "文件策略配置已重置"}

    # 将模块级函数改为静态方法，直接调用WebSocket manager
    @staticmethod
    def send_to_websocket(data, project_id):
        try:
            from app.core.websocket import manager
            import asyncio
            print(f"直接发送WebSocket消息到项目 {project_id}")
            
            # 如果在异步上下文中，直接调用异步方法
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # 在异步上下文中，创建一个任务
                    asyncio.create_task(manager.send_json(data, project_id))
                else:
                    # 在同步上下文中，运行异步方法
                    loop.run_until_complete(manager.send_json(data, project_id))
            except RuntimeError:
                # 没有事件循环，创建新的
                asyncio.run(manager.send_json(data, project_id))
            
            print(f"WebSocket消息发送成功")
            return True
        except Exception as e:
            print(f"发送WebSocket消息失败: {str(e)}")
            return False

    # 异步版本的WebSocket发送方法
    @staticmethod
    async def send_to_websocket_async(data, project_id):
        """异步发送WebSocket消息，直接调用manager"""
        try:
            from app.core.websocket import manager
            print(f"异步直接发送WebSocket消息到项目 {project_id}")
            await manager.send_json(data, project_id)
            print(f"异步WebSocket消息发送成功")
            return True
        except Exception as e:
            print(f"异步发送WebSocket消息失败: {str(e)}")
            return False