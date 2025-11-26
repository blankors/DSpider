import time
import threading
from typing import List, Dict, Callable
from pydispatch import dispatcher
import requests
from datetime import datetime, timedelta
from typing import Any, Dict
import platform
import asyncio

from playwright.sync_api import sync_playwright

from common.rabbitmq_client import rabbitmq_client
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
        
        # 注册信号处理器
        dispatcher.connect(self.handle_spider_signal, signal="NEED_COOKIE", sender=dispatcher.Any)
    
    def start_v1(self):
        """启动定时更新线程"""
        # if not self.running:
        #     self.running = True
        #     self.thread = threading.Thread(target=self._periodic_update)
        #     self.thread.daemon = True
        #     self.thread.start()
        #     print("CookieUpdater started")
    
    def stop(self):
        """停止定时更新"""
        self.running = False
        if self.thread:
            self.thread.join()
        self.playwright.stop()
        print("CookieUpdater stopped")
    
    def start(self):
        """定时批量更新cookie"""
        self.rabbitmq_client.consume_messages(
            queue_name='sql2mq',
            callback=self._update_single_cookie
        )
        # while self.running:
        #     try:
        #         # 从数据库获取URL列表（这里用模拟数据）
        #         urls = self._get_urls_from_db()
        #         print(f"Updating cookies for {len(urls)} URLs")
                
        #         for url in urls:
        #             self._update_single_cookie(url)
                
        #         print(f"Batch update completed at {datetime.now()}")
        #         time.sleep(self.update_interval)
        #     except Exception as e:
        #         print(f"Error during periodic update: {e}")
        #         time.sleep(60)  # 出错后等待1分钟再继续
    
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
            from .cookie_updater import process_url_task
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

from common.celery_config import celery_app
from playwright.async_api import async_playwright

class CookieBrowser:
    """
    使用 Celery 和 Playwright 异步打开网页的浏览器类
    """
    def __init__(self):
        """初始化 CookieBrowser"""
        self.playwright = None
        self.browser = None
    
    async def initialize(self):
        """初始化 Playwright"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
    
    async def close(self):
        """关闭 Playwright"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def process_url(self, url):
        """
        处理单个 URL，异步打开网页并获取 cookie
        
        Args:
            url: 要处理的 URL
            
        Returns:
            Dict: 包含 URL 和 cookie 的字典
        """
        logger.info(f"Processing URL: {url}")
        if not self.browser:
            await self.initialize()
        
        page = await self.browser.new_page()
        try:
            await page.goto(url)
            await page.wait_for_timeout(5000)  # 等待页面加载
            
            # 获取 cookie
            cookies = await page.context.cookies()
            cookie_str = '; '.join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
            
            # Windows兼容的时间戳获取方式
            try:
                timestamp = asyncio.get_event_loop().time()
            except Exception:
                import time
                timestamp = time.time()
            
            return {
                'url': url,
                'cookie': cookie_str,
                'timestamp': timestamp
            }
        finally:
            await page.close()

# 创建 CookieBrowser 实例
cookie_browser = CookieBrowser()

# 定义 Celery 任务
@celery_app.task
def process_url_task(url):
    """
    Celery 任务，处理单个 URL
    
    Args:
        url: 要处理的 URL
        
    Returns:
        Dict: 包含 URL 和 cookie 的字典
    """
    logger.info(f"Celery task processing URL: {url}")
    
    # Windows兼容的事件循环处理
    if platform.system() == 'Windows':
        # Windows下使用新的事件循环
        try:
            # 尝试关闭现有的事件循环（如果存在）
            old_loop = asyncio.get_event_loop()
            if not old_loop.is_closed():
                old_loop.close()
        except RuntimeError:
            pass
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    else:
        # Unix系统使用标准方式
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        result = loop.run_until_complete(cookie_browser.process_url(url))
        return result
    except Exception as e:
        # Windows兼容的时间戳获取方式
        try:
            timestamp = loop.time()
        except Exception:
            import time
            timestamp = time.time()
        
        return {
            'url': url,
            'error': str(e),
            'timestamp': timestamp
        }
    finally:
        # 确保关闭事件循环
        try:
            if not loop.is_closed():
                loop.close()
        except Exception:
            pass

if __name__ == "__main__":
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并启动工作进程
    worker = CookieUpdater()
    worker.start()