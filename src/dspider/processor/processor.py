import os
import time
import logging
from typing import Dict, Any, List
from dspider.common.mongodb_client import MongoDBConnection
from dspider.common.rabbitmq_client import RabbitMQClient
from dspider.common.logger_config import LoggerConfig
from dspider.common.load_config import config

class ProcessorNode:
    """数据处理节点"""
    
    def __init__(self):
        """初始化Processor节点
        """
        # 使用common中的配置
        self.config = config
        
        # 设置日志
        # 尝试加载YAML格式的日志配置
        log_config_yaml = 'config/logging.yaml'
        log_config_json = 'config/logging.json'
        
        if os.path.exists(log_config_yaml):
            self.logger = LoggerConfig.setup_logger(log_config_yaml, name='processor')
        elif os.path.exists(log_config_json):
            self.logger = LoggerConfig.setup_logger(log_config_json, name='processor')
        else:
            self.logger = LoggerConfig.setup_logger(name='processor')
        
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
        
        # 配置信息
        self.result_queue = self.config['processor']['result_queue']
        self.exchange_name = self.config['processor']['exchange_name']
        self.routing_key = self.config['processor']['routing_key']
        self.collection_name = self.config['processor']['collection_name']
        self.batch_size = self.config['processor']['batch_size']
        
        # 批量处理缓存
        self.batch_cache: List[Dict[str, Any]] = []
    

    
    def initialize(self) -> bool:
        """初始化连接和资源
        
        Returns:
            bool: 是否初始化成功
        """
        self.logger.info("开始初始化Processor节点...")
        
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
        
        # 声明结果队列
        if not self.rabbitmq_client.declare_queue(self.result_queue):
            self.logger.error("结果队列声明失败")
            return False
        
        # 绑定队列
        if not self.rabbitmq_client.bind_queue(
            self.result_queue, self.exchange_name, self.routing_key
        ):
            self.logger.error("队列绑定失败")
            return False
        
        self.logger.info("Processor节点初始化成功")
        return True
    
    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清洗数据
        
        Args:
            data: 原始数据
            
        Returns:
            Dict[str, Any]: 清洗后的数据
        """
        cleaned_data = data.copy()
        
        try:
            # 处理空值
            for key, value in cleaned_data.items():
                if value == '':
                    cleaned_data[key] = None
                elif isinstance(value, dict):
                    # 递归清洗嵌套字典
                    cleaned_data[key] = self.clean_data(value)
            
            # 添加处理时间
            cleaned_data['processed_at'] = time.time()
            
            # 如果有parsed_data，将其合并到主数据中
            if 'parsed_data' in cleaned_data:
                for key, value in cleaned_data['parsed_data'].items():
                    cleaned_data[key] = value
            
            # 添加元数据
            cleaned_data['metadata'] = {
                'processing_version': '1.0',
                'processor_host': os.uname().nodename if hasattr(os, 'uname') else 'unknown',
                'processing_duration': cleaned_data.get('response_time', 0)
            }
            
        except Exception as e:
            self.logger.error(f"数据清洗失败: {str(e)}")
        
        return cleaned_data
    
    def save_to_mongodb(self, data_list: List[Dict[str, Any]]) -> bool:
        """保存数据到MongoDB
        
        Args:
            data_list: 数据列表
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if not data_list:
                return True
            
            # 批量插入
            result_ids = self.mongo_client.insert_many(self.collection_name, data_list)
            
            if result_ids:
                self.logger.info(f"成功保存 {len(result_ids)} 条数据到MongoDB")
                # 更新任务状态
                for data in data_list:
                    if data.get('task_id'):
                        self.mongo_client.update_one(
                            'WebsiteConfig',
                            {'_id': data['task_id']},
                            {'$set': {'status': 'completed', 'completed_at': time.time()}}
                        )
                return True
            else:
                self.logger.error("保存数据到MongoDB失败")
                return False
                
        except Exception as e:
            self.logger.error(f"保存数据到MongoDB时出错: {str(e)}")
            return False
    
    def process_result(self, result: Dict[str, Any], properties: Dict[str, Any]) -> bool:
        """处理单个结果
        
        Args:
            result: 结果数据
            properties: 消息属性
            
        Returns:
            bool: 是否成功处理
        """
        try:
            # 清洗数据
            cleaned_data = self.clean_data(result)
            
            # 添加到批处理缓存
            self.batch_cache.append(cleaned_data)
            
            # 当缓存达到批处理大小时进行保存
            if len(self.batch_cache) >= self.batch_size:
                if self.save_to_mongodb(self.batch_cache):
                    self.batch_cache = []  # 清空缓存
                else:
                    self.logger.error("批量保存失败，保留缓存")
                    return False
            
            self.logger.info(f"处理结果: 任务ID={result.get('task_id', 'unknown')}, 来源={result.get('worker_id', 'unknown')}")
            return True
            
        except Exception as e:
            self.logger.error(f"处理结果时出错: {str(e)}")
            return False
    
    def flush_cache(self):
        """刷新缓存，保存剩余数据"""
        if self.batch_cache:
            self.logger.info(f"刷新剩余 {len(self.batch_cache)} 条数据")
            self.save_to_mongodb(self.batch_cache)
            self.batch_cache = []
    
    def run(self):
        """运行Processor节点主循环"""
        try:
            if not self.initialize():
                self.logger.error("初始化失败，退出程序")
                return
            
            self.logger.info("Processor节点开始运行")
            
            # 开始消费消息
            self.rabbitmq_client.consume_messages(
                self.result_queue,
                callback=self.process_result,
                auto_ack=False,
                prefetch_count=self.batch_size
            )
            
        except KeyboardInterrupt:
            self.logger.info("用户中断，准备退出")
        except Exception as e:
            self.logger.error(f"运行时错误: {str(e)}")
        finally:
            self.logger.info("清理资源...")
            # 刷新缓存
            self.flush_cache()
            # 断开连接
            self.mongo_client.disconnect()
            self.rabbitmq_client.disconnect()
            self.logger.info("Processor节点已停止")

if __name__ == '__main__':
    processor = ProcessorNode()
    processor.run()