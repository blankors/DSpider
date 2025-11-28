# cookie_manager_process.py
import asyncio
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from redis_comm import RedisSignalManager
from cookie_signals import SignalMessage, SignalType
 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
class CookieManagerProcess:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_manager = RedisSignalManager(redis_host, redis_port)
        self.cookie_cache: Dict[str, Dict] = {}
        self.db_client = None  # 你的数据库客户端
        self.running = True
        self.batch_update_task = None
        
    async def start(self):
        """启动CookieManager进程"""
        logger.info("Starting CookieManager process...")
        
        # 连接数据库
        await self._connect_database()
        
        # 订阅信号
        await self.redis_manager.subscribe_to_signals([
            SignalType.COOKIE_NEEDED,
            SignalType.BATCH_UPDATE
        ])
        
        # 启动批量更新任务
        self.batch_update_task = asyncio.create_task(self._batch_update_loop())
        
        # 启动信号监听
        await self._signal_handling_loop()
    
    async def _signal_handling_loop(self):
        """信号处理主循环"""
        await self.redis_manager.listen_for_signals()
    
    async def _handle_cookie_needed(self, signal: SignalMessage):
        """处理cookie需求信号"""
        logger.info(f"Received cookie request for URL: {signal.url}, immediate: {signal.immediate}")
        
        try:
            # 尝试从缓存获取
            cookie = await self._get_cached_cookie(signal.url)
            
            if not cookie or signal.immediate:
                # 立即获取cookie
                cookie = await self._fetch_cookie_immediate(signal.url)
                
                if cookie:
                    # 更新缓存
                    self._update_cache(signal.url, cookie)
            
            # 发送响应
            response_data = {
                'url': signal.url,
                'cookie': cookie,
                'success': cookie is not None,
                'timestamp': datetime.now().isoformat()
            }
            
            self.redis_manager.send_response(signal.request_id, response_data)
            logger.info(f"Sent cookie response for {signal.url}")
            
        except Exception as e:
            logger.error(f"Error handling cookie request: {e}")
            # 发送错误响应
            error_response = {
                'url': signal.url,
                'error': str(e),
                'success': False
            }
            self.redis_manager.send_response(signal.request_id, error_response)
    
    async def _handle_batch_update(self, signal: SignalMessage):
        """处理批量更新信号"""
        logger.info("Starting batch cookie update...")
        
        try:
            await self._perform_batch_update()
            logger.info("Batch update completed successfully")
        except Exception as e:
            logger.error(f"Batch update failed: {e}")
    
    async def _signal_listener(self):
        """监听Redis信号的协程"""
        while self.running:
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_manager.pubsub.get_message, timeout=1.0
                )
                
                if message and message['type'] == 'message':
                    signal = SignalMessage.from_json(message['data'])
                    
                    if signal.signal_type == SignalType.COOKIE_NEEDED:
                        await self._handle_cookie_needed(signal)
                    elif signal.signal_type == SignalType.BATCH_UPDATE:
                        await self._handle_batch_update(signal)
                        
            except Exception as e:
                logger.error(f"Error in signal listener: {e}")
    
    async def _batch_update_loop(self):
        """定期批量更新循环"""
        while self.running:
            try:
                await asyncio.sleep(300)  # 每5分钟更新一次
                await self._perform_batch_update()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch update loop: {e}")
    
    async def _perform_batch_update(self):
        """执行批量更新"""
        logger.info("Performing batch cookie update...")
        
        try:
            # 从数据库批量获取cookies
            cookies = await self._fetch_cookies_batch()
            
            # 更新缓存
            updated_count = 0
            for url, cookie in cookies.items():
                if cookie:
                    self._update_cache(url, cookie)
                    updated_count += 1
            
            logger.info(f"Batch update completed: {updated_count} cookies updated")
            
        except Exception as e:
            logger.error(f"Batch update failed: {e}")
    
    async def _get_cached_cookie(self, url: str) -> Optional[str]:
        """从缓存获取cookie"""
        cached = self.cookie_cache.get(url)
        if cached:
            # 检查是否过期（假设5分钟过期）
            age = datetime.now() - datetime.fromisoformat(cached['updated_at'])
            if age < timedelta(minutes=5):
                return cached['cookie']
        return None
    
    def _update_cache(self, url: str, cookie: str):
        """更新缓存"""
        self.cookie_cache[url] = {
            'cookie': cookie,
            'updated_at': datetime.now().isoformat()
        }
    
    async def _fetch_cookie_immediate(self, url: str) -> Optional[str]:
        """立即获取单个URL的cookie"""
        # 实现你的数据库查询逻辑
        if self.db_client:
            try:
                return await self.db_client.get_cookie_for_url(url)
            except Exception as e:
                logger.error(f"Error fetching cookie for {url}: {e}")
        return None
    
    async def _fetch_cookies_batch(self) -> Dict[str, str]:
        """批量获取cookies"""
        if self.db_client:
            try:
                return await self.db_client.get_cookies_batch()
            except Exception as e:
                logger.error(f"Error in batch fetch: {e}")
        return {}
    
    async def _connect_database(self):
        """连接数据库"""
        # 实现你的数据库连接逻辑
        # self.db_client = await create_database_client()
        logger.info("Database connected")
    
    def stop(self):
        """停止进程"""
        logger.info("Stopping CookieManager process...")
        self.running = False
        if self.batch_update_task:
            self.batch_update_task.cancel()
        self.redis_manager.stop()
 
async def main():
    """主函数"""
    cookie_manager = CookieManagerProcess()
    
    def signal_handler(signum, frame):
        cookie_manager.stop()
        sys.exit(0)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        await cookie_manager.start()
    except Exception as e:
        logger.error(f"CookieManager process error: {e}")
    finally:
        cookie_manager.stop()
 
if __name__ == "__main__":
    asyncio.run(main())