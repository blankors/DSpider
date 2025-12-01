import os
import time
import logging
from typing import Dict, Any, List
from dspider.common.mongodb_client import MongoDBConnection
from dspider.common.rabbitmq_client import RabbitMQClient
from dspider.common.logger_config import LoggerConfig
from dspider.common.load_config import config

class MasterNode:
    """爬虫Master节点"""
    
    def __init__(self):
        """初始化Master节点
        """
        # 使用common中的配置
        self.config = config
        
        # 设置日志
        # 尝试加载YAML格式的日志配置
        log_config_yaml = 'config/logging.yaml'
        log_config_json = 'config/logging.json'
        
        if os.path.exists(log_config_yaml):
            self.logger = LoggerConfig.setup_logger(log_config_yaml, name='master')
        elif os.path.exists(log_config_json):
            self.logger = LoggerConfig.setup_logger(log_config_json, name='master')
        else:
            self.logger = LoggerConfig.setup_logger(name='master')
        
        # 初始化MongoDB连接
        self.mongo_client = MongoDBConnection(
            host=self.config['mongodb']['host'],
            port=self.config['mongodb']['port'],
            username=self.config['mongodb']['username'],
            password=self.config['mongodb']['password'],
            db_name=self.config['mongodb']['db_name']
        )
        
        # 初始化RabbitMQ连接
        self.rabbitmq_client = RabbitMQClient(
            host=self.config['rabbitmq']['host'],
            port=self.config['rabbitmq']['port'],
            username=self.config['rabbitmq']['username'],
            password=self.config['rabbitmq']['password'],
            virtual_host=self.config['rabbitmq']['virtual_host']
        )
        
        # 任务配置
        self.task_queue = self.config['master']['task_queue']
        self.exchange_name = self.config['master']['exchange_name']
        self.routing_key = self.config['master']['routing_key']
        self.task_batch_size = self.config['master']['task_batch_size']
        self.polling_interval = self.config['master']['polling_interval']
    
    def initialize(self) -> bool:
        """初始化连接和资源
        
        Returns:
            bool: 是否初始化成功
        """
        self.logger.info("开始初始化Master节点...")
        
        # 连接MongoDB
        if not self.mongo_client.connect():
            self.logger.error("MongoDB连接失败")
            return False
        
        # 连接RabbitMQ
        if not self.rabbitmq_client.connect():
            self.logger.error("RabbitMQ连接失败")
            return False
        
        # 声明交换机
        if not self.rabbitmq_client.declare_exchange(self.exchange_name):
            self.logger.error("交换机声明失败")
            return False
        
        # 声明任务队列
        if not self.rabbitmq_client.declare_queue(self.task_queue):
            self.logger.error("任务队列声明失败")
            return False
        
        # 绑定队列
        if not self.rabbitmq_client.bind_queue(
            self.task_queue, self.exchange_name, self.routing_key
        ):
            self.logger.error("队列绑定失败")
            return False
        
        self.logger.info("Master节点初始化成功")
        return True
    
    def load_tasks_from_mongodb(self) -> List[Dict[str, Any]]:
        """从MongoDB加载任务配置
        
        Returns:
            List[Dict[str, Any]]: 任务配置列表
        """
        try:
            # 从WebsiteConfig表读取未处理的任务
            tasks = self.mongo_client.find(
                'WebsiteConfig',
                {'status': {'$ne': 'completed'}},
                limit=self.task_batch_size
            )
            self.logger.info(f"从MongoDB加载了 {len(tasks)} 个任务")
            return tasks
        except Exception as e:
            self.logger.error(f"从MongoDB加载任务失败: {str(e)}")
            return []
    
    def distribute_tasks(self, tasks: List[Dict[str, Any]]) -> int:
        """分发任务到RabbitMQ
        
        Args:
            tasks: 任务列表
            
        Returns:
            int: 成功分发的任务数
        """
        success_count = 0
        
        for task in tasks:
            # 添加任务ID和时间戳
            if '_id' not in task:
                task['_id'] = str(task.get('id', ''))
            task['timestamp'] = time.time()
            
            # 发布到RabbitMQ
            if self.rabbitmq_client.publish_message(
                self.exchange_name,
                self.routing_key,
                task
            ):
                success_count += 1
                # 更新任务状态
                self.mongo_client.update_one(
                    'WebsiteConfig',
                    {'_id': task['_id']},
                    {'$set': {'status': 'distributed', 'distributed_at': time.time()}}
                )
        
        self.logger.info(f"成功分发 {success_count}/{len(tasks)} 个任务")
        return success_count
    
    def run(self):
        """运行Master节点主循环"""
        try:
            if not self.initialize():
                self.logger.error("初始化失败，退出程序")
                return
            
            self.logger.info("Master节点开始运行")
            self.logger.info("热更新测试：Master节点成功启动")
            
            while True:
                try:
                    # 加载任务
                    tasks = self.load_tasks_from_mongodb()
                    
                    # 分发任务
                    if tasks:
                        self.distribute_tasks(tasks)
                    else:
                        self.logger.info(f"没有可分发的任务，{self.polling_interval}秒后重试")
                    
                    # 休眠一段时间
                    time.sleep(self.polling_interval)
                
                except KeyboardInterrupt:
                    self.logger.info("用户中断，准备退出")
                    break
                except Exception as e:
                    self.logger.error(f"运行时错误: {str(e)}")
                    # 重新连接资源
                    self.mongo_client.disconnect()
                    self.rabbitmq_client.disconnect()
                    self.initialize()
                    
        finally:
            self.logger.info("清理资源...")
            self.mongo_client.disconnect()
            self.rabbitmq_client.disconnect()
            self.logger.info("Master节点已停止")

if __name__ == '__main__':
    master = MasterNode()
    master.run()