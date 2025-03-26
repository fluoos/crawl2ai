import json
import os
import re
from pathlib import Path
import logging
import chardet  # 新增：用于检测文件编码

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("clean_failed.log", encoding='utf-8'),  # 明确指定日志文件编码
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def detect_file_encoding(file_path):
    """检测文件编码"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding']
    except Exception as e:
        logger.error(f"检测文件编码失败: {str(e)}")
        return 'utf-8'  # 默认返回utf-8

def parse_log_file(log_path):
    """分析日志文件，提取失败的文件记录"""
    failed_files = set()
    
    try:
        # 检测文件编码
        encoding = detect_file_encoding(log_path)
        logger.info(f"检测到文件编码: {encoding}")
        
        with open(log_path, 'r', encoding=encoding, errors='replace') as f:
            for line in f:
                # 匹配错误日志中的文件名
                # 调整正则表达式以匹配更多可能的错误模式
                error_patterns = [
                    r'ERROR.*?处理文件失败：(.*?)(?:\s|$)',
                    r'ERROR.*?Failed to process file: (.*?)(?:\s|$)',
                    r'ERROR.*?失败.*?\"(.*?)\"',
                    r'ERROR.*?failed.*?\"(.*?)\"'
                ]
                
                for pattern in error_patterns:
                    error_match = re.search(pattern, line, re.IGNORECASE)
                    if error_match:
                        failed_file = error_match.group(1).strip()
                        # 移除可能的引号
                        failed_file = failed_file.strip('"\'')
                        failed_files.add(failed_file)
                        logger.info(f"发现失败文件: {failed_file}")
                        break
                        
    except Exception as e:
        logger.error(f"读取日志文件失败: {str(e)}")
        logger.error(f"在文件 {log_path} 处理时发生错误")
        return set()
        
    return failed_files

def clean_processed_files(processed_files_path, failed_files):
    """从processed_files.json中移除失败的文件"""
    try:
        # 读取现有的processed_files.json
        if os.path.exists(processed_files_path):
            with open(processed_files_path, 'r', encoding='utf-8') as f:
                processed_files = json.load(f)
        else:
            logger.warning(f"文件不存在: {processed_files_path}")
            return False
            
        # 记录原始文件数量
        original_count = len(processed_files)
        
        # 移除失败的文件
        processed_files = [f for f in processed_files if f not in failed_files]
        
        # 保存更新后的文件
        with open(processed_files_path, 'w', encoding='utf-8') as f:
            json.dump(processed_files, f, ensure_ascii=False, indent=2)
            
        # 记录清理结果
        removed_count = original_count - len(processed_files)
        logger.info(f"已从processed_files.json中移除 {removed_count} 个失败文件")
        logger.info(f"剩余处理文件数量: {len(processed_files)}")
        
        return True
        
    except Exception as e:
        logger.error(f"清理processed_files.json失败: {str(e)}")
        return False

def main():
    """主函数"""
    try:
        # 文件路径配置
        log_file = "file_to_dataset.log"
        processed_files_path = "output/processed_files.json"
        
        # 检查文件是否存在
        if not os.path.exists(log_file):
            logger.error(f"日志文件不存在: {log_file}")
            return
            
        # 分析日志文件
        logger.info("开始分析日志文件...")
        failed_files = parse_log_file(log_file)
        
        if not failed_files:
            logger.info("未发现失败的文件记录")
            return
            
        logger.info(f"发现 {len(failed_files)} 个失败文件")
        
        # 清理processed_files.json
        logger.info("开始清理processed_files.json...")
        if clean_processed_files(processed_files_path, failed_files):
            logger.info("清理完成")
        else:
            logger.error("清理失败")
            
    except Exception as e:
        logger.error(f"执行清理脚本失败: {str(e)}")

if __name__ == "__main__":
    main() 