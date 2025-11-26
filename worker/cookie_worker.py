import asyncio
from common.rabbitmq_client import rabbitmq_client
from worker.cookie_updater import process_url_task
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class CookieWorker:
    """
    从 RabbitMQ 获取 URL 并调用 Celery 任务处理的工作类
    """
    def __init__(self):
        """初始化 CookieWorker"""
        self.rabbitmq_client = rabbitmq_client
    
    def start(self):
        """启动工作进程"""
        # 连接 RabbitMQ
        if not self.rabbitmq_client.connect():
            logger.error("Failed to connect to RabbitMQ")
            return
        
        # 声明队列
        self.rabbitmq_client.declare_queue('sql2mq', durable=True)
        
        # 开始消费消息
        logger.info("CookieWorker started, waiting for messages...")
        self.rabbitmq_client.consume_messages(
            queue_name='sql2mq',
            callback=self._handle_message
        )
    
    def _handle_message(self, data: Dict[str, Any], properties: Dict[str, Any]) -> bool:
        """
        处理 RabbitMQ 消息
        
        Args:
            data: 消息数据
            properties: 消息属性
            
        Returns:
            bool: 是否确认消息
        """
        try:
            # 解析 URL
            url = data['url']
            logger.info(f"Received URL: {url}")
            
            # 调用 Celery 任务处理 URL
            process_url_task.delay(url)
            logger.info(f"Submitted Celery task for URL: {url}")
            
            return True  # 确认消息
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return False  # 拒绝消息

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并启动工作进程
    worker = CookieWorker()
    worker.start()
