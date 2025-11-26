from typing import List, Optional
import random
import time
import json
import traceback
import logging

import requests

NET = 'in'
PROXY_INFO = {}
PROXY_INFO['free'] = 'http://10.17.206.1:2235/api/proxy/get/0'
PROXY_INFO['pay'] = 'http://10.17.206.1:2235/api/proxy/get/1'

class ProxyConnectionError(Exception):
    pass
class ProxyAcquisitionError(Exception):
    pass


class EnhancedRequests:
    def __init__(self, 
                 max_retries: int = 1,
                 retry_delay: float = 1.0,
                 expect_status_code: int = 200,
                 need_proxy: bool = False,
                 proxy_type: str = 'free',
                 logger = None
                 ):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.expect_status_code = expect_status_code
        self.need_proxy = need_proxy
        self.proxy_type = proxy_type
        self.logger = logger or logging.getLogger(__name__)
        self.statistic = {
            'retry_times': 0,
        }
    
    def _get_proxy_ip(self, proxy_api_url: str) -> Optional[str]:
        max_retries = 5
        while max_retries:
            try:
                response = requests.get(proxy_api_url, timeout=(3, 5))
            except Exception as e:
                max_retries -= 1
                time.sleep(1)
                continue
            
            if response.status_code == 200:
                proxy_api_resp_data = json.loads(response.text) # 异常发生概率较小，不需要try except
                if type(proxy_api_resp_data) is dict:
                    return proxy_api_resp_data['ip']
                else:
                    return proxy_api_resp_data[0]
            else:
                max_retries -= 1
                time.sleep(1)
        
        self.logger.debug(f'尝试5次，请求代理服务器，获取代理IP失败')
        raise ProxyConnectionError('尝试5次，请求代理服务器，获取代理IP失败')
    
    def _get_proxy(self, type: str = 'free') -> Optional[dict]:
        """获取代理
        在_get_proxy中处理异常，而非在request中处理异常
        异常处理位置的选择应遵循‘职责分离原则’、‘错误上下文相关性’、‘错误上下文完整性’

        Args:
            type (str, optional): _description_. Defaults to 'free'.

        Raises:
            ProxyConnectionError: _description_
            ProxyAuthError: _description_

        Returns:
            Optional[dict]: _description_
        """
        ip_with_port: str = None
        try:
            if NET == 'in' and type == 'free':
                ip_with_port = random.choice(PROXY_INFO[type])
            else:
                proxy_api_url = PROXY_INFO[type]
                ip_with_port = self._get_proxy_ip(proxy_api_url)
        except (ProxyConnectionError) as e:
            raise # 已知异常直接抛出
        except Exception as e:
            # 未知异常，记录日志
            self.logger.debug(f'获取代理失败：{e}')
            raise ProxyAcquisitionError(f"代理获取失败: {e}") from e
        
        proxy_dict = {"http": f"http://{ip_with_port}", "https": f"http://{ip_with_port}"}
        return proxy_dict
    
    
    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        start = time.time()
        last_exception = None
        
        if self.need_proxy:
            try:
                proxy = self._get_proxy(type=self.proxy_type)
            except Exception as e:
                self.logger.debug(f'获取代理失败：{e}')
                raise
            kwargs['proxies'] = proxy

        for attempt in range(self.max_retries):
            self.statistic['retry_times'] += 1
            try:
                response = requests.request(method, url, **kwargs)
                if response.status_code == self.expect_status_code:
                    self.statistic['request_time'] = time.time() - start
                    return response
                
                raise requests.exceptions.RequestException(
                    f"Request failed with status code {response.status_code}"
                )
            
            except requests.exceptions.RequestException as e:
                last_exception = e
            except Exception as e:
                last_exception = e
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        self.statistic['request_time'] += (time.time() - start)
        raise last_exception or requests.exceptions.RequestException("Request failed")
    
    def get_statistic(self) -> dict:
        return self.statistic
    
    def get(self, url: str, **kwargs) -> requests.Response:
        try:
            return self.request('GET', url, **kwargs)
        except Exception as e:
            self.logger.exception(f'GET请求失败: {url}') # 自动包含完整栈信息，且日志级别为ERROR，无需手动调用traceback.format_exc()
            raise
    
    def post(self, url: str, **kwargs) -> requests.Response:
        # return self.request('POST', url, **kwargs)
        try:
            return self.request('POST', url, **kwargs)
        except Exception as e:
            self.logger.exception(f'POST请求失败: {url}')
            raise
    
if __name__ == "__main__":
    client = EnhancedRequests(need_proxy=False)
    # client._get_proxy()
    try:
        resp = client.get('https://baidu.com')
        print(resp.text)
    except ProxyConnectionError as e:
        pass

    # 或者使用固定代理
    # fixed_client = EnhancedRequests(
    #     proxy_strategy=FixedProxyStrategy("http://my-fixed-proxy.com")
    # )

    # 运行时切换策略
    # client.proxy_strategy = RoundRobinProxyStrategy()