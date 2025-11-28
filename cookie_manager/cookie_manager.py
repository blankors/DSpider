import time
import threading
from typing import List, Dict, Callable
from pydispatch import dispatcher
import requests
from datetime import datetime, timedelta
from typing import Any, Dict
import asyncio

from playwright_worker.worker import process_url_task
from common.rabbitmq_client import rabbitmq_client
from common.mongodb_client import mongodb_conn
import logging

logger = logging.getLogger(__name__)

class CookieUpdater:
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
        self.cookies: Dict[str, str] = {}
        self.url_timestamps: Dict[str, datetime] = {}
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        
        self.rabbitmq_client = rabbitmq_client
        self.mongodb_conn = mongodb_conn
    
    def stop(self):
        """停止定时更新"""
        self.running = False
        if self.thread:
            self.thread.join()
        self.playwright.stop()
        print("CookieUpdater stopped")
    
    def start(self):
        """定时批量更新cookie"""
        # 定期扫描数据库，通过celery任务更新cookie
        self.running = True
        while self.running:
            # 扫描数据库，获取所有需要更新的URL
            urls = self.mongodb_conn.get_collection('cookies').find()
            
            for url_data in urls:
                self._update_single_cookie(url_data, url_data)
            
            # 等待下一个更新周期
            time.sleep(self.update_interval)
    
    def _update_single_cookie(self, data, properties: Dict[str, Any]):
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
            process_url_task.delay(url)
            logger.info(f"Submitted Celery task for URL: {url}")
            
            return True  # 确认消息
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            return False  # 拒绝消息
        # time.sleep(10)
        # self._update_single_cookie1(url)
        
    def handle_spider_signal(self, signal_url: str):
        """
        处理Spider信号，立即更新指定URL的cookie
        
        Args:
            signal_url: 需要立即更新cookie的URL
        """
        print(f"Received signal for URL: {signal_url}")
        self._update_single_cookie(signal_url)
        
        # 发送cookie已更新的信号
        dispatcher.send(signal="COOKIE_UPDATED", sender=self, url=signal_url, cookie=self.cookies.get(signal_url))
    
    def _update_single_cookie1(self, url: str):
        """
        更新单个URL的cookie
        
        Args:
            url: 目标URL
        """
        try:
            # 模拟获取cookie的逻辑（实际项目中替换为真实请求）
            response = requests.get(url, timeout=10)
            cookie = self._extract_cookie_from_response(response)
            
            with self.lock:
                self.cookies[url] = cookie
                self.url_timestamps[url] = datetime.now()
            
            print(f"Updated cookie for {url}")
        except Exception as e:
            print(f"Failed to update cookie for {url}: {e}")
    
    def _extract_cookie_from_response(self, response) -> str:
        """
        从响应中提取cookie（模拟实现）
        
        Args:
            response: HTTP响应对象
            
        Returns:
            cookie字符串
        """
        # 实际项目中根据需要实现真正的cookie提取逻辑
        # 这里只是示例
        return f"sessionid={int(time.time())}; path=/"
    
    def _get_urls_from_db(self) -> List[str]:
        """
        从数据库获取需要更新cookie的URL列表（模拟实现）
        
        Returns:
            URL列表
        """
        # 实际项目中替换为真实的数据库查询
        time.sleep(3)
        return [
            "https://example.com/api1",
            "https://example.com/api2", 
            "https://example.com/api3"
        ]
    
    def get_cookie(self, url: str) -> str:
        """
        获取指定URL的cookie
        
        Args:
            url: 目标URL
            
        Returns:
            cookie字符串，如果不存在返回None
        """
        with self.lock:
            return self.cookies.get(url)
    
    def get_all_cookies(self) -> Dict[str, str]:
        """
        获取所有cookie
        
        Returns:
            所有cookie的字典
        """
        with self.lock:
            return self.cookies.copy()



if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并启动工作进程
    worker = CookieUpdater()
    worker.start()