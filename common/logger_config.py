import logging
import logging.config
import os
import json
from typing import Optional, Dict, Any

class LoggerConfig:
    """日志配置管理类"""
    
    @staticmethod
    def setup_logger(config_file: Optional[str] = None, log_level: int = logging.INFO,
                    log_file: Optional[str] = None, name: Optional[str] = None) -> logging.Logger:
        """设置日志配置
        
        Args:
            config_file: 日志配置文件路径
            log_level: 日志级别（当没有配置文件时使用）
            log_file: 日志文件路径（当没有配置文件时使用）
            name: 日志名称
            
        Returns:
            logging.Logger: 配置好的logger实例
        """
        if config_file and os.path.exists(config_file):
            # 从配置文件加载
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logging.config.dictConfig(config)
                logger = logging.getLogger(name) if name else logging.getLogger()
                logger.info(f"日志配置已从 {config_file} 加载")
                return logger
            except Exception as e:
                print(f"加载日志配置文件失败: {str(e)}")
        
        # 默认配置
        logger = logging.getLogger(name) if name else logging.getLogger()
        logger.setLevel(log_level)
        
        # 清除已存在的handler
        if logger.handlers:
            for handler in logger.handlers:
                logger.removeHandler(handler)
        
        # 控制台handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        # 文件handler（如果指定）
        if log_file:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        if log_file:
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        logger.info(f"默认日志配置已设置，级别: {logging.getLevelName(log_level)}")
        return logger
    
    @staticmethod
    def create_default_config(log_file: str = 'logs/app.log') -> Dict[str, Any]:
        """创建默认日志配置
        
        Args:
            log_file: 日志文件路径
            
        Returns:
            Dict[str, Any]: 日志配置字典
        """
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                },
                'detailed': {
                    'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': 'INFO',
                    'formatter': 'detailed',
                    'filename': log_file,
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5,
                    'encoding': 'utf-8'
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console', 'file'],
                    'level': 'INFO',
                    'propagate': True
                },
                'pika': {
                    'handlers': ['console', 'file'],
                    'level': 'WARNING',
                    'propagate': False
                },
                'pymongo': {
                    'handlers': ['console', 'file'],
                    'level': 'WARNING',
                    'propagate': False
                }
            }
        }
    
    @staticmethod
    def save_config(config: Dict[str, Any], file_path: str) -> bool:
        """保存日志配置到文件
        
        Args:
            config: 日志配置字典
            file_path: 保存路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保目录存在
            dir_path = os.path.dirname(file_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存日志配置失败: {str(e)}")
            return False