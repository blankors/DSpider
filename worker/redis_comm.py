# redis_comm.py
import redis
import json
import uuid
import asyncio
from typing import Callable, Dict, Optional, Any
from cookie_signals import SignalMessage, SignalType
 
class RedisSignalManager:
    def __init__(self, redis_host='localhost', redis_port=6379, db=0):
        self.redis = redis.Redis(host=redis_host, port=redis_port, db=db, decode_responses=True)
        self.pubsub = self.redis.pubsub()
        self.response_callbacks: Dict[str, Callable] = {}
        self.running = False
        
    async def publish_signal(self, signal: SignalMessage) -> None:
        """发布信号到Redis"""
        channel = f"cookie_signals:{signal.signal_type.value}"
        await asyncio.get_event_loop().run_in_executor(
            None, self.redis.publish, channel, signal.to_json()
        )
    
    async def send_request_wait_response(self, signal: SignalMessage, timeout: float = 10.0) -> Optional[Any]:
        """发送请求并等待响应"""
        request_id = signal.request_id
        
        # 创建响应Future
        future = asyncio.Future()
        self.response_callbacks[request_id] = future
        
        try:
            # 发布请求
            await self.publish_signal(signal)
            
            # 等待响应
            response = await asyncio.wait_for(future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            self.response_callbacks.pop(request_id, None)
            return None
        finally:
            self.response_callbacks.pop(request_id, None)
    
    async def subscribe_to_signals(self, signal_types: list[SignalType]) -> None:
        """订阅特定类型的信号"""
        channels = [f"cookie_signals:{signal_type.value}" for signal_type in signal_types]
        await asyncio.get_event_loop().run_in_executor(
            None, self.pubsub.subscribe, *channels
        )
    
    async def listen_for_signals(self) -> None:
        """监听信号消息"""
        self.running = True
        while self.running:
            try:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, self.pubsub.get_message, timeout=1.0
                )
                
                if message and message['type'] == 'message':
                    signal = SignalMessage.from_json(message['data'])
                    await self._handle_signal(signal)
                    
            except Exception as e:
                print(f"Error listening for signals: {e}")
    
    async def _handle_signal(self, signal: SignalMessage) -> None:
        """处理接收到的信号"""
        if signal.signal_type == SignalType.COOKIE_RESPONSE:
            # 处理响应消息
            callback = self.response_callbacks.get(signal.request_id)
            if callback and not callback.done():
                callback.set_result(signal.data)
    
    def send_response(self, original_request_id: str, data: Any) -> None:
        """发送响应消息"""
        response = SignalMessage(
            signal_type=SignalType.COOKIE_RESPONSE,
            request_id=original_request_id,
            data=data
        )
        self.redis.publish(
            f"cookie_signals:{SignalType.COOKIE_RESPONSE.value}",
            response.to_json()
        )
    
    def stop(self):
        """停止监听"""
        self.running = False
        self.pubsub.close()