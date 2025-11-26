import time
import asyncio
from pydispatch import dispatcher

from context import worker
from worker.cookie_updater import CookieUpdater

class SpiderSimulator:
    """
    模拟Spider类，用于测试信号发送
    """
    def __init__(self, cookie_updater: CookieUpdater):
        self.cookie_updater = cookie_updater
    
    def request_cookie(self, url: str):
        """
        模拟Spider请求立即获取cookie
        
        Args:
            url: 需要cookie的URL
        """
        print(f"Spider requesting cookie for: {url}")
        dispatcher.send(signal="NEED_COOKIE", sender=self, signal_url=url)
    
    def wait_for_cookie_update(self, url: str, timeout: int = 10) -> bool:
        """
        等待cookie更新完成
        
        Args:
            url: 目标URL
            timeout: 超时时间（秒）
            
        Returns:
            是否在超时前获取到cookie
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.cookie_updater.get_cookie(url):
                return True
            time.sleep(0.1)
        return False


# 使用示例
if __name__ == "__main__":
    # 创建Cookie更新器实例
    updater = CookieUpdater(update_interval=30)  # 30秒更新一次
    
    # 创建Spider模拟器
    spider = SpiderSimulator(updater)
    
    # 启动更新器
    updater.start()
    
    # 等待一段时间让批量更新运行
    time.sleep(5)
    
    # 模拟Spider发送信号请求cookie
    spider.request_cookie("https://example.com/urgent")
    
    # 等待cookie更新完成
    if spider.wait_for_cookie_update("https://example.com/urgent"):
        cookie = updater.get_cookie("https://example.com/urgent")
        print(f"Got cookie: {cookie}")
    else:
        print("Failed to get cookie in time")
    
    # 运行一段时间后停止
    time.sleep(10)
    updater.stop()