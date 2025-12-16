import os
import time
import logging
import requests
from typing import Dict, Any, Optional
import uuid
import json
import importlib

import requests

from dspider.common.rabbitmq_client import RabbitMQClient, rabbitmq_client
from dspider.common.mongodb_client import mongodb_conn
from dspider.common.logger_config import LoggerConfig
from dspider.common.load_config import config
from dspider.common.minio_client import minio_client
from dspider.worker.spider.list_spider import ListSpider

# 配置日志系统
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(process)d - %(thread)d - %(filename)s - %(lineno)d - %(funcName)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

logging.config.dictConfig(logging_config)

class WorkerNodeByLLM:
    """爬虫Worker节点"""
    
    def __init__(self, worker_id: Optional[str] = None):
        """初始化Worker节点
        
        Args:
            worker_id: 工作节点ID
        """
        # 先设置worker_id
        self.worker_id = worker_id or f'worker_{os.getpid()}'
        
        # 使用common中的配置
        self.config = config
        
        # 设置日志
        # 尝试加载YAML格式的日志配置
        log_config_yaml = 'config/logging.yaml'
        log_config_json = 'config/logging.json'
        
        if os.path.exists(log_config_yaml):
            self.logger = LoggerConfig.setup_logger(
                log_config_yaml, 
                name=f'worker_{self.worker_id}'
            )
        elif os.path.exists(log_config_json):
            self.logger = LoggerConfig.setup_logger(
                log_config_json, 
                name=f'worker_{self.worker_id}'
            )
        else:
            self.logger = LoggerConfig.setup_logger(
                name=f'worker_{self.worker_id}'
            )
        
        # 初始化RabbitMQ连接
        self.rabbitmq_client = rabbitmq_client
        
        # 任务配置
        self.task_queue = self.config['worker']['task_queue']
        self.result_exchange = self.config['worker']['result_exchange']
        self.result_routing_key = self.config['worker']['result_routing_key']
        self.prefetch_count = self.config['worker']['prefetch_count']
        self.timeout = self.config['worker']['timeout']
    

    
    def initialize(self) -> bool:
        """初始化连接和资源
        
        Returns:
            bool: 是否初始化成功
        """
        self.logger.info(f"[{self.worker_id}] 开始初始化Worker节点...")
        
        # 连接RabbitMQ
        if not self.rabbitmq_client.connect():
            self.logger.error(f"[{self.worker_id}] RabbitMQ连接失败")
            return False
        
        # 声明交换机
        if not self.rabbitmq_client.declare_exchange(self.result_exchange):
            self.logger.error(f"[{self.worker_id}] 交换机声明失败")
            return False
        
        # 声明任务队列
        if not self.rabbitmq_client.declare_queue(self.task_queue):
            self.logger.error(f"[{self.worker_id}] 任务队列声明失败")
            return False
        
        # 绑定任务队列
        if not self.rabbitmq_client.bind_queue(
            self.task_queue, self.result_exchange, self.result_routing_key
        ):
            self.logger.error(f"[{self.worker_id}] 任务队列绑定失败")
            return False
        
        # 声明结果队列
        result_queue = f"spider_results_{self.worker_id}"
        if not self.rabbitmq_client.declare_queue(result_queue):
            self.logger.error(f"[{self.worker_id}] 结果队列声明失败")
            return False
        
        # 绑定结果队列
        if not self.rabbitmq_client.bind_queue(
            result_queue, self.result_exchange, self.result_routing_key
        ):
            self.logger.error(f"[{self.worker_id}] 结果队列绑定失败")
            return False
        
        self.logger.info(f"[{self.worker_id}] Worker节点初始化成功")
        return True
    
    def fetch_url(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """执行网页抓取
        
        Args:
            task: 任务配置
            
        Returns:
            Dict[str, Any]: 抓取结果
        """
        result = {
            'task_id': task.get('_id', ''),
            'worker_id': self.worker_id,
            'timestamp': time.time(),
            'success': False,
            'error': None
        }
        
        try:
            # 获取请求参数
            request_params = task.get('request_params', {})
            api_url = request_params.get('api_url', '')
            data = request_params.get('data', {})
            need_headers = task.get('need_headers', False)
            
            if not api_url:
                raise ValueError("任务中缺少API URL")
            
            # 准备请求头
            headers = {}
            if need_headers:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json, text/plain, */*'
                }
            
            # 执行请求
            self.logger.info(f"[{self.worker_id}] 开始抓取: {api_url}")
            start_time = time.time()
            
            # 根据任务类型执行不同的请求
            if isinstance(data, dict) and data:
                response = requests.post(
                    api_url, 
                    json=data, 
                    headers=headers,
                    timeout=self.timeout
                )
            else:
                response = requests.get(
                    api_url,
                    headers=headers,
                    timeout=self.timeout
                )
            
            response.raise_for_status()
            
            # 尝试解析JSON响应
            try:
                content = response.json()
                result['data'] = content
            except json.JSONDecodeError:
                content = response.text
                result['data'] = content
            
            result['success'] = True
            result['status_code'] = response.status_code
            result['response_time'] = time.time() - start_time
            
            self.logger.info(f"[{self.worker_id}] 抓取成功: {api_url}, 耗时: {result['response_time']:.2f}s")
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"[{self.worker_id}] 抓取失败: {str(e)}")
        
        return result
    
    def parse_response(self, task: Dict[str, Any], fetch_result: Dict[str, Any]) -> Dict[str, Any]:
        """解析响应结果
        
        Args:
            task: 任务配置
            fetch_result: 抓取结果
            
        Returns:
            Dict[str, Any]: 解析后的结果
        """
        parse_result = fetch_result.copy()
        
        if not fetch_result.get('success', False):
            return parse_result
        
        try:
            parse_rule = task.get('parse_rule', {})
            if parse_rule:
                # 这里可以根据parse_rule实现更复杂的解析逻辑
                # 目前只是简单示例
                data = fetch_result.get('data', {})
                if isinstance(data, dict):
                    # 提取需要的字段
                    parsed_data = {}
                    for key, selector in parse_rule.items():
                        if isinstance(selector, str) and selector in data:
                            parsed_data[key] = data[selector]
                    if parsed_data:
                        parse_result['parsed_data'] = parsed_data
            
        except Exception as e:
            parse_result['parse_error'] = str(e)
            self.logger.error(f"[{self.worker_id}] 解析失败: {str(e)}")
        
        return parse_result
    
    def process_task(self, task: Dict[str, Any], properties: Dict[str, Any]) -> bool:
        """处理单个任务
        
        Args:
            task: 任务数据
            properties: 消息属性
            
        Returns:
            bool: 是否成功处理
        """
        self.logger.info(f"[{self.worker_id}] 收到任务: {task.get('_id', 'unknown')}")
        
        try:
            # 执行抓取
            fetch_result = self.fetch_url(task)
            
            # 解析结果
            final_result = self.parse_response(task, fetch_result)
            
            # 发送结果到RabbitMQ
            if self.rabbitmq_client.publish_message(
                self.result_exchange,
                self.result_routing_key,
                final_result
            ):
                self.logger.info(f"[{self.worker_id}] 结果已发送: {task.get('_id', 'unknown')}")
                return True
            else:
                self.logger.error(f"[{self.worker_id}] 结果发送失败: {task.get('_id', 'unknown')}")
                return False
                
        except Exception as e:
            self.logger.error(f"[{self.worker_id}] 处理任务时出错: {str(e)}")
            return False
    
    def run(self):
        """运行Worker节点主循环"""
        try:
            if not self.initialize():
                self.logger.error(f"[{self.worker_id}] 初始化失败，退出程序")
                return
            
            self.logger.info(f"[{self.worker_id}] Worker节点开始运行")
            
            # 开始消费消息
            self.rabbitmq_client.consume_messages(
                self.task_queue,
                callback=self.process_task,
                auto_ack=False,
                prefetch_count=self.prefetch_count
            )
            
        except KeyboardInterrupt:
            self.logger.info(f"[{self.worker_id}] 用户中断，准备退出")
        except Exception as e:
            self.logger.error(f"[{self.worker_id}] 运行时错误: {str(e)}")
        finally:
            self.logger.info(f"[{self.worker_id}] 清理资源...")
            self.rabbitmq_client.disconnect()
            self.logger.info(f"[{self.worker_id}] Worker节点已停止")

import importlib
from importlib import import_module
from pkgutil import iter_modules
from types import ModuleType

def walk_modules(path: str) -> list[ModuleType]:
    """Loads a module and all its submodules from the given module path and
    returns them. If *any* module throws an exception while importing, that
    exception is thrown back.

    For example: walk_modules('scrapy.utils')
    """

    mods: list[ModuleType] = []
    mod = import_module(path)
    mods.append(mod)
    if hasattr(mod, "__path__"):
        for _, subpath, ispkg in iter_modules(mod.__path__):
            fullpath = path + "." + subpath
            if ispkg:
                mods += walk_modules(fullpath)
            else:
                submod = import_module(fullpath)
                mods.append(submod)
    return mods

class Executor:
    def __init__(self, task_config):
        self.task_config = task_config
        self.spider_name = self.task_config['spider_name']
        
        self.rabbitmq_client = rabbitmq_client
        self.mongodb_service = mongodb_conn
        self.minio_client = minio_client
        
        self.logger = logging.getLogger(f"Executor")
        
        # self.spider_module = importlib.import_module(f"dspider.worker.{spider_name}")
        # import dspider.worker.spider as worker_module
        # self.spider_class = getattr(worker_module, spider_name)
        worker_modules = walk_modules('dspider.worker.spider')
        for mod in worker_modules:
            if hasattr(mod, self.spider_name):
                self.spider_class = getattr(mod, self.spider_name)
                self.spider = self.spider_class(self)
                break
        else:
            raise ImportError(f"Spider {self.spider_name} not found in any module")
        
        self.worker_id = str(uuid.uuid4())[:8]
    
    def run(self):
        self.rabbitmq_client.consume_messages(
            self.queue_name,
            callback=self.process_task,
            auto_ack=False,
            prefetch_count=self.prefetch_count
        )
    
    def process_task(self, task: Dict[str, Any], properties: Dict[str, Any]) -> bool:
        """处理单个任务
        
        Args:
            task: 任务数据
            properties: 消息属性
            
        Returns:
            bool: 是否成功处理
        """
        self.logger.info(f"[{self.worker_id}] 收到任务: {task.get('_id', 'unknown')}")
        self.spider.start(task)
        
class WorkerNode:
    def __init__(self):
        self.worker_id = str(uuid.uuid4())[:8]
        self.rabbitmq_client = rabbitmq_client
        self.mongodb_service = mongodb_conn
        self.minio_client = minio_client
        # self.queue_name = config['worker']['task_queue']
        self.queue_name = 'sql2mq'
        self.prefetch_count = config['worker'].get('prefetch_count', 1)  # 默认值为1
        self.logger = logging.getLogger(f"WorkerNode-{self.worker_id}")
        self.spider = ListSpider(self)
    
    def run(self):
        self.rabbitmq_client.consume_messages(
            self.queue_name,
            callback=self.process_task,
            auto_ack=False,
            prefetch_count=self.prefetch_count
        )

    def process_task(self, task: Dict[str, Any], properties: Dict[str, Any]) -> bool:
        """处理单个任务
        
        Args:
            task: 任务数据
            properties: 消息属性
            
        Returns:
            bool: 是否成功处理
        """
        task_id = task.get('_id', str(uuid.uuid4()))
        self.logger.info(f"[{self.worker_id}] 收到任务: {task_id}")
        self.spider.start(task)
        time.sleep(100)
        return False

if __name__ == '__main__':
    worker = WorkerNode()
    worker.run()