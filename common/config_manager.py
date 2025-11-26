import os
import json
import yaml
from typing import Dict, Any, Optional


class ConfigManager:
    """配置管理类，支持多环境配置
    
    支持从不同环境的配置文件加载配置，并使用环境变量切换环境。
    环境优先级：环境变量 > 指定环境 > 默认环境(development)
    """
    
    # 支持的环境列表
    SUPPORTED_ENVIRONMENTS = ['dev', 'test', 'prod']
    
    # 默认环境
    DEFAULT_ENVIRONMENT = 'dev'
    
    # 环境变量名称，用于指定当前环境 (dev/test/prod)
    ENV_VAR_NAME = 'DSPIDER_ENV'
    
    def __init__(self, config_dir: str = '../config'):
        """初始化配置管理器
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = os.path.abspath(config_dir)
        self._config: Optional[Dict[str, Any]] = None
        self._environment: Optional[str] = None
    
    def get_environment(self) -> str:
        """获取当前环境
        
        优先级：
        1. 已设置的环境
        2. 环境变量 DSPIDER_ENV
        3. 默认环境
        
        Returns:
            str: 当前环境名称
        """
        if self._environment is not None:
            return self._environment
        
        # 从环境变量获取
        env = os.environ.get(self.ENV_VAR_NAME, '').lower()
        if env in self.SUPPORTED_ENVIRONMENTS:
            return env
        
        # 返回默认环境
        return self.DEFAULT_ENVIRONMENT
    
    def set_environment(self, environment: str) -> None:
        """设置当前环境
        
        Args:
            environment: 环境名称
            
        Raises:
            ValueError: 当环境名称不在支持列表中时
        """
        if environment not in self.SUPPORTED_ENVIRONMENTS:
            raise ValueError(f"不支持的环境: {environment}，支持的环境有: {', '.join(self.SUPPORTED_ENVIRONMENTS)}")
        
        self._environment = environment
        # 清除缓存，下次获取配置时重新加载
        self._config = None
    
    def get_config(self, environment: Optional[str] = None) -> Dict[str, Any]:
        """获取配置
        
        Args:
            environment: 指定环境名称，如果为None则使用当前环境
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        # 如果指定了环境，先切换环境
        if environment is not None:
            self.set_environment(environment)
        
        # 如果配置已缓存，直接返回
        if self._config is not None:
            return self._config
        
        # 获取当前环境
        current_env = self.get_environment()
        
        # 尝试从环境配置文件加载（优先YAML格式）
        yaml_config_file = os.path.join(self.config_dir, f'{current_env}.yaml')
        json_config_file = os.path.join(self.config_dir, f'{current_env}.json')
        
        if os.path.exists(yaml_config_file):
            self._config = self._load_config_file(yaml_config_file)
        elif os.path.exists(json_config_file):
            self._config = self._load_config_file(json_config_file)
        else:
            # 如果环境配置文件不存在，尝试加载默认配置文件
            default_yaml_file = os.path.join(self.config_dir, 'config.yaml')
            default_json_file = os.path.join(self.config_dir, 'config.json')
            
            if os.path.exists(default_yaml_file):
                self._config = self._load_config_file(default_yaml_file)
            elif os.path.exists(default_json_file):
                self._config = self._load_config_file(default_json_file)
            else:
                # 如果所有配置文件都不存在，返回默认配置
                self._config = self._get_default_config(current_env)
        
        return self._config
    
    def _load_config_file(self, file_path: str) -> Dict[str, Any]:
        """加载配置文件（支持YAML和JSON格式）
        
        Args:
            file_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            print(f"加载配置文件失败 {file_path}: {str(e)}")
            # 返回默认配置
            return self._get_default_config()
    
    def _get_default_config(self, environment: str = 'dev') -> Dict[str, Any]:
        """获取默认配置
        
        Args:
            environment: 环境名称
            
        Returns:
            Dict[str, Any]: 默认配置字典
        """
        # 基础配置
        base_config = {
            'mongodb': {
                'username': 'dspider',
                'password': 'dspider_password',
                'db_name': 'spider_db'
            },
            'rabbitmq': {
                'username': 'dspider',
                'password': 'dspider_password',
                'virtual_host': '/'
            },
            'master': {
                'task_queue': 'spider_tasks',
                'exchange_name': 'spider_exchange',
                'routing_key': 'task',
                'task_batch_size': 100,
                'polling_interval': 5
            },
            'worker': {
                'worker_id': 'worker_1',
                'task_queue': 'spider_tasks',
                'result_queue': 'spider_results',
                'max_concurrent_tasks': 5,
                'heartbeat_interval': 30
            },
            'processor': {
                'result_queue': 'spider_results',
                'batch_size': 50,
                'processing_interval': 10
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/app.log'
            }
        }
        
        # 根据环境设置不同的连接信息
        if environment == 'dev':
            base_config['mongodb']['host'] = 'localhost'
            base_config['mongodb']['port'] = 27017
            base_config['rabbitmq']['host'] = 'localhost'
            base_config['rabbitmq']['port'] = 5672
        elif environment == 'test':
            # 测试环境连接Docker容器
            base_config['mongodb']['host'] = 'mongodb'
            base_config['mongodb']['port'] = 27017
            base_config['rabbitmq']['host'] = 'rabbitmq'
            base_config['rabbitmq']['port'] = 5672
        elif environment == 'prod':
            # 生产环境连接Docker容器
            base_config['mongodb']['host'] = 'mongodb'
            base_config['mongodb']['port'] = 27017
            base_config['rabbitmq']['host'] = 'rabbitmq'
            base_config['rabbitmq']['port'] = 5672
        
        return base_config
    
    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """向后兼容方法，用于替换现有的_load_config方法
        
        Args:
            config_path: 配置文件路径（可选）
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        # 如果指定了配置文件路径，优先使用
        if config_path and os.path.exists(config_path):
            return self._load_config_file(config_path)
        
        # 否则使用配置管理器的方式
        return self.get_config()


# 创建全局配置管理器实例
config_manager = ConfigManager()


def get_config(environment: Optional[str] = None) -> Dict[str, Any]:
    """获取配置的便捷函数
    
    Args:
        environment: 指定环境名称
        
    Returns:
        Dict[str, Any]: 配置字典
    """
    return config_manager.get_config(environment)


def set_environment(environment: str) -> None:
    """设置环境的便捷函数
    
    Args:
        environment: 环境名称
    """
    config_manager.set_environment(environment)


def load_config(config_path: str = None) -> Dict[str, Any]:
    """加载配置的便捷函数，向后兼容
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Dict[str, Any]: 配置字典
    """
    return config_manager.load_config(config_path)