import asyncio
import logging

from dspider.celery_worker.celery_app import celery_app
from playwright.async_api import async_playwright
import platform

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        logger.info("Initializing Playwright...???")
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