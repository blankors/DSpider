# spider_signals.py
import asyncio
import uuid
from typing import Optional
from redis_comm import RedisSignalManager
from cookie_signals import SignalMessage, SignalType
 
class SpiderSignalSender:
    def __init__(self, redis_host='localhost', redis_port=6379):
        self.redis_manager = RedisSignalManager(redis_host, redis_port)
    
    async def request_cookie(self, url: str, immediate: bool = False, timeout: float = 10.0) -> Optional[str]:
        """请求特定URL的cookie"""
        signal = SignalMessage(
            signal_type=SignalType.COOKIE_NEEDED,
            request_id=str(uuid.uuid4()),
            url=url,
            immediate=immediate,
            priority='high' if immediate else 'normal',
            timestamp=asyncio.get_event_loop().time()
        )
        
        response = await self.redis_manager.send_request_wait_response(signal, timeout)
        
        if response and response.get('success'):
            return response.get('cookie')
        
        return None
    
    def trigger_batch_update(self):
        """触发批量更新（不等待响应）"""
        signal = SignalMessage(
            signal_type=SignalType.BATCH_UPDATE,
            request_id=str(uuid.uuid4()),
            timestamp=asyncio.get_event_loop().time()
        )
        
        # 异步发送，不等待响应
        asyncio.create_task(self.redis_manager.publish_signal(signal))