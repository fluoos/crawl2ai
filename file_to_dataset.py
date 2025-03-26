import json
import os
import time
import traceback
import logging
import argparse
from pathlib import Path
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("file_to_dataset.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 默认配置
DEFAULT_CONFIG = {
    "model": "deepseek-chat",
    "max_chunk_size": 9000,  # 文本块最大字符数
    "retry_attempts": 3,     # API调用重试次数
    "retry_delay": 5,        # 重试间隔(秒)
    "base_url": "https://api.deepseek.com"
}

def load_config(config_path: str = "config.json") -> Dict:
    """加载配置文件"""
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                config.update(user_config)
            logger.info(f"已加载配置文件: {config_path}")
        except Exception as e:
            logger.warning(f"加载配置文件失败: {str(e)}，使用默认配置")
    else:
        logger.info(f"配置文件不存在: {config_path}，使用默认配置")
    return config

def load_api_key() -> str:
    """从.env文件加载API key"""
    # 加载.env文件
    load_dotenv()
    
    # 获取API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("请在.env文件中设置 DEEPSEEK_API_KEY")
    return api_key

def split_text_into_chunks(text: str, max_chunk_size: int) -> List[str]:
    """将文本分割成多个块"""
    # 如果文本长度小于最大块大小，直接返回
    if len(text) <= max_chunk_size:
        return [text]
    
    # 按段落分割文本
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # 如果段落本身超过最大块大小，按句子分割
        if len(paragraph) > max_chunk_size:
            sentences = paragraph.replace('\n', ' ').split('. ')
            for sentence in sentences:
                sentence = sentence.strip() + '. ' if not sentence.endswith('.') else sentence.strip()
                if len(current_chunk) + len(sentence) + 1 > max_chunk_size:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += (' ' + sentence if current_chunk else sentence)
        # 否则尝试将整个段落添加到当前块
        elif len(current_chunk) + len(paragraph) + 2 > max_chunk_size:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            current_chunk += ('\n\n' + paragraph if current_chunk else paragraph)
    
    # 添加最后一个块
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def process_text_to_qa(text: str, client: OpenAI, config: Dict) -> Optional[Dict]:
    """处理文本并转换为问答格式"""
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

    # 构建发送给大模型的内容
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text}
    ]

    retry_attempts = config.get("retry_attempts", 3)
    retry_delay = config.get("retry_delay", 5)
    model = config.get("model", "deepseek-chat")
    
    for attempt in range(retry_attempts):
        try:
            # 记录API调用开始
            logger.info(f"正在调用API处理文本，长度: {len(text)} 字符，尝试次数: {attempt+1}/{retry_attempts}")
            
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={
                    'type': 'json_object'
                }
            )
            
            # 记录API调用成功
            logger.info("API调用成功")
            
            # 获取返回内容
            content = response.choices[0].message.content
            logger.info(f"API返回内容长度: {len(content)} 字符")
            
            # 精简输出，只打印前200字符
            print("\nAPI返回的原始内容(前200字符):")
            print(content[:200] + ("..." if len(content) > 200 else ""))
            print("-" * 50)
            
            try:
                result = json.loads(content)
                # 验证返回的JSON结构
                if 'qa_pairs' not in result:
                    logger.warning(f"API返回的JSON缺少'qa_pairs'字段: {result}")
                    return {"qa_pairs": []}
                return result
            except json.JSONDecodeError as je:
                logger.error(f"JSON解析错误: {str(je)}")
                logger.error(f"原始内容前200字符: {content[:200]}")
                if attempt < retry_attempts - 1:
                    logger.info(f"等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    continue
                return {"qa_pairs": []}
                
        except Exception as e:
            logger.error(f"调用API时出错: {str(e)}")
            if attempt < retry_attempts - 1:
                logger.info(f"等待 {retry_delay} 秒后重试...")
                time.sleep(retry_delay)
            else:
                logger.error(traceback.format_exc())
                return {"qa_pairs": []}
    
    return {"qa_pairs": []}

def process_markdown_file(file_path: Path, client: OpenAI, config: Dict) -> List[Dict]:
    """处理单个markdown文件"""
    try:
        logger.info(f"开始处理文件: {file_path}")
        
        # 检查文件是否存在
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return []
        
        # 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"成功读取文件，内容长度: {len(content)} 字符")
            
            # 检查文件内容是否为空
            if not content.strip():
                logger.warning(f"文件内容为空: {file_path}")
                return []
                
        except Exception as e:
            logger.error(f"读取文件失败: {str(e)}")
            logger.error(traceback.format_exc())
            return []
        
        # 判断是否需要分块处理
        max_chunk_size = config.get("max_chunk_size", 4000)
        if len(content) > max_chunk_size:
            logger.info(f"文件内容超过最大块大小({max_chunk_size}字符)，进行分块处理")
            chunks = split_text_into_chunks(content, max_chunk_size)
            logger.info(f"文件被分割成 {len(chunks)} 个块")
            
            all_qa_pairs = []
            for i, chunk in enumerate(chunks):
                logger.info(f"处理块 {i+1}/{len(chunks)}")
                result = process_text_to_qa(chunk, client, config)
                if result and 'qa_pairs' in result and result['qa_pairs']:
                    all_qa_pairs.extend(result['qa_pairs'])
                    logger.info(f"从块 {i+1} 中提取了 {len(result['qa_pairs'])} 个问答对")
            
            logger.info(f"所有块处理完成，共提取了 {len(all_qa_pairs)} 个问答对")
            return all_qa_pairs
        else:
            # 处理文本并获取问答对
            result = process_text_to_qa(content, client, config)
            if result and 'qa_pairs' in result:
                qa_count = len(result['qa_pairs'])
                logger.info(f"从文件中提取了 {qa_count} 个问答对")
                return result['qa_pairs']
        
        logger.warning(f"从文件中未提取到有效问答对: {file_path}")
        return []
        
    except Exception as e:
        logger.error(f"处理文件时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return []

def mark_file_processed(file_path: Path, processed_files: set, processed_files_path: Path) -> bool:
    """标记文件为已处理状态并保存记录"""
    try:
        processed_files.add(str(file_path.absolute()))
        with open(processed_files_path, 'w', encoding='utf-8') as f:
            json.dump(list(processed_files), f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"更新已处理文件记录失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def save_qa_pairs(qa_pairs: List[Dict], output_file: Path) -> bool:
    """保存问答对到输出文件"""
    try:
        with open(output_file, 'a', encoding='utf-8') as f:
            for qa_pair in qa_pairs:
                f.write(json.dumps(qa_pair, ensure_ascii=False) + '\n')
        return True
    except Exception as e:
        logger.error(f"保存结果时出错: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='处理Markdown文件生成问答数据集')
    parser.add_argument('--input', '-i', help='输入目录(默认: upload)', default='upload')
    parser.add_argument('--output', '-o', help='输出目录(默认: output)', default='output')
    parser.add_argument('--config', '-c', help='配置文件(默认: config.json)', default='config.json')
    parser.add_argument('--force', '-f', help='强制重新处理所有文件', action='store_true')
    return parser.parse_args()

def main():
    # 解析命令行参数
    args = parse_arguments()
    
    try:
        logger.info("="*50)
        logger.info("开始处理文件到数据集")
        
        # 加载配置
        config = load_config(args.config)
        logger.info(f"已加载配置: {config}")
        
        # 检查环境变量
        try:
            api_key = load_api_key()
            logger.info("成功加载API密钥")
        except Exception as e:
            logger.error(f"加载API密钥失败: {str(e)}")
            logger.error(traceback.format_exc())
            return
        
        # 初始化OpenAI客户端
        client = OpenAI(
            api_key=api_key,
            base_url=config.get("base_url", "https://api.deepseek.com"),
        )
        
        # 检查目录结构
        upload_dir = Path(args.input)
        if not upload_dir.exists():
            logger.error(f"上传目录不存在: {upload_dir.absolute()}")
            logger.info(f"创建上传目录: {upload_dir.absolute()}")
            upload_dir.mkdir(exist_ok=True)
        
        # 确保输出目录存在
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / "qa_dataset.jsonl"
        
        # 加载已处理文件记录
        processed_files_path = output_dir / "processed_files.json"
        processed_files = set()
        
        if not args.force and processed_files_path.exists():
            try:
                with open(processed_files_path, 'r', encoding='utf-8') as f:
                    processed_files = set(json.load(f))
                logger.info(f"加载已处理文件记录，共 {len(processed_files)} 个文件")
            except Exception as e:
                logger.error(f"加载已处理文件记录失败: {str(e)}")
                processed_files = set()
        elif args.force:
            logger.info("强制重新处理所有文件")
        
        # 获取所有markdown文件
        md_files = list(upload_dir.glob("*.md"))
        if not md_files:
            logger.warning(f"上传目录中没有找到markdown文件: {upload_dir.absolute()}")
            return
            
        logger.info(f"找到 {len(md_files)} 个markdown文件")
        
        # 计算需要处理的文件
        files_to_process = []
        for md_file in md_files:
            file_str = str(md_file.absolute())
            if not args.force and file_str in processed_files:
                logger.info(f"跳过已处理的文件: {md_file}")
            elif "help" not in file_str:
                #files_to_process.append(md_file)
                pass
            else:
                files_to_process.append(md_file)
        logger.info(f"需要处理的文件数量: {len(files_to_process)}")
        if not files_to_process:
            logger.info("没有新文件需要处理")
            return
        
        # 处理文件并实时保存结果
        total_qa_pairs = 0
        success_count = 0
        failed_count = 0
        start_time = time.time()
        
        for i, md_file in enumerate(tqdm(files_to_process, desc="处理文件")):
            logger.info(f"开始处理文件 [{i+1}/{len(files_to_process)}]: {md_file}")
            qa_pairs = process_markdown_file(md_file, client, config)
            
            if qa_pairs:
                # 实时保存结果
                if save_qa_pairs(qa_pairs, output_file):
                    # 更新已处理文件记录
                    if mark_file_processed(md_file, processed_files, processed_files_path):
                        total_qa_pairs += len(qa_pairs)
                        success_count += 1
                        logger.info(f"文件处理完成: {md_file}, 提取了 {len(qa_pairs)} 个问答对，已保存")
                    else:
                        failed_count += 1
                else:
                    failed_count += 1
            else:
                logger.warning(f"文件处理完成，但未提取到有效问答对: {md_file}")
                # 也记录为已处理，避免下次重复处理
                # if mark_file_processed(md_file, processed_files, processed_files_path):
                #     success_count += 1
                # else:
                #     failed_count += 1
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 打印处理统计信息
        logger.info("="*50)
        logger.info("处理完成，统计信息:")
        logger.info(f"总处理文件数: {len(files_to_process)}")
        logger.info(f"成功处理文件数: {success_count}")
        logger.info(f"失败处理文件数: {failed_count}")
        logger.info(f"生成问答对总数: {total_qa_pairs}")
        logger.info(f"处理总耗时: {elapsed_time:.2f} 秒")
        logger.info(f"平均每个文件耗时: {elapsed_time/len(files_to_process):.2f} 秒")
        logger.info(f"结果已保存到: {output_file}")
        
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()