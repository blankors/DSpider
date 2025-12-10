import os
import time
import logging
import logging.config
from typing import Dict, Any, List

import structlog

from dspider.common.mongodb_client import mongodb_conn
from dspider.common.rabbitmq_client import rabbitmq_client
from dspider.common.load_config import config
from dspider.master.master_config import master_config

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

class MasterNode:
    def __init__(self):
        self.mongo_client = mongodb_conn
        self.rabbitmq_client = rabbitmq_client
        self.send_interval = master_config['sql_select_frenquency']
        self.logger = logging.getLogger(__name__)
        
        self.task_queue = master_config['queue_name']
        self.exchange_name = master_config['exchange_name']
        self.routing_key = master_config['routing_key']
        self.initialize()
        
    
    def initialize(self):
        if self.exchange_name != '':
            # 声明交换机
            self.rabbitmq_client.declare_exchange(
                self.exchange_name, exchange_type='direct'
            )
        
        # 声明任务队列
        if not self.rabbitmq_client.declare_queue(self.task_queue):
            self.logger.error("任务队列声明失败")
            return False
        
        # 绑定队列
        if self.exchange_name != '':
            self.rabbitmq_client.bind_queue(
                self.task_queue, self.exchange_name, self.routing_key
            )
        
        self.logger.info("Master节点初始化成功")
        return True
    
    def run(self):
        self.logger.info("Master节点开始运行")
        while True:
            ds_configs = self.get_ds_configs()
            self.distribute_tasks(ds_configs)
            time.sleep(self.send_interval)
    
    def get_ds_configs(self) -> List[Dict[str, Any]]:
        """从MongoDB加载URL
        
        Returns:
            List[Dict[str, Any]]: URL列表
        """
        try:
            # 从WebsiteConfig表读取未处理的URL
            ds_configs = self.mongo_client.find(
                'recruitment_datasource_config',
                {'state': 0},
                limit=master_config['sql_select_count']
            )
            self.logger.info(f"从MongoDB加载了 {len(ds_configs)} 个URL")
            return ds_configs
        except Exception as e:
            self.logger.error(f"从MongoDB加载URL失败: {str(e)}")
            return []
    
    def distribute_tasks(self, ds_confgs: List[Dict[str, Any]]) -> int:
        """分发URL到RabbitMQ
        
        Args:
            ds_confgs: URL列表
            
        Returns:
            int: 成功分发的URL数
        """
        success_count = 0
        
        for ds_config in ds_confgs:
            ds_config['_id'] = str(ds_config.get('_id', ''))
            ds_config['timestamp'] = time.time()
            
            # 发布到RabbitMQ
            if self.rabbitmq_client.publish_message(
                self.exchange_name,
                self.routing_key,
                ds_config
            ):
                success_count += 1
                # 更新URL状态
                self.mongo_client.update_one(
                    'recruitment_datasource_config',
                    {'_id': ds_config['_id']},
                    {'$set': {'state': 1, 'distributed_at': time.time()}}
                )
        
        self.logger.info(f"成功分发 {success_count}/{len(ds_confgs)} 个URL")
        return success_count
    
    
if __name__ == '__main__':
    master = MasterNode()
    master.run()