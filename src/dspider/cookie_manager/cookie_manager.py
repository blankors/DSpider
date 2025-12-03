import time
import threading
from typing import List, Dict, Callable
from pydispatch import dispatcher
import requests
from datetime import datetime, timedelta
from typing import Any, Dict
import asyncio

from dspider.celery_worker.tasks import process_url_task
from dspider.common.rabbitmq_client import rabbitmq_client
from dspider.common.mongodb_client import mongodb_conn
import logging

logger = logging.getLogger(__name__)

class CookieManager:
    """
    Cookie更新管理类，支持定时批量更新和实时信号更新
    """
    def __init__(self, update_interval: int = 3600):
        """
        初始化Cookie更新器
        
        Args:
            update_interval: 批量更新间隔时间（秒）
        """
        self.update_interval = update_interval
        self.running = False
        
        self.rabbitmq_client = rabbitmq_client
        self.mongodb_conn = mongodb_conn
    
    def stop(self):
        """停止定时更新"""
        self.running = False
        logger.info("CookieManager stopped")
    
    def start(self):
        """定时批量更新cookie"""
        # 定期扫描数据库，通过celery任务更新cookie
        self.running = True
        while self.running:
            # 扫描数据库，获取所有需要更新的URL
            datasource_configs = self.mongodb_conn.get_collection('recruitment_datasource_config').find()
            
            for datasource_config in datasource_configs:
                self._update_single_cookie(datasource_config)
            
            # 等待下一个更新周期
            logger.info(f"Waiting for next update cycle ({self.update_interval} seconds)")
            time.sleep(self.update_interval)
    
    def _update_single_cookie(self, data: dict):
        """
        更新单个URL的cookie
        
        Args:
            data: 包含URL的消息数据
        """
        try:
            # 解析 URL
            url = data['url']
            logger.info(f"Received URL: {url}")
            
            # 调用 Celery 任务处理 URL
            serializable_data = data.copy()
            # 移除或转换MongoDB的ObjectId类型字段
            if '_id' in serializable_data:
                # 移除_id字段或转换为字符串
                serializable_data.pop('_id', None)
                
            process_url_task.delay(serializable_data)
            logger.info(f"Submitted Celery task for URL: {url}")
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")


if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并启动工作进程
    worker = CookieManager(update_interval=10)
    worker.start()