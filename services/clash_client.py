import requests
from requests.exceptions import RequestException, Timeout
import time

class ClashClient:
    def __init__(self, base_url="http://127.0.0.1:9090"):
        self.base_url = base_url
        self.session = requests.Session()
        self.timeout = 5.0

    def safe_request(self, method, endpoint, retries=3, **kwargs):
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault('timeout', self.timeout)
        
        for attempt in range(retries):
            try:
                response = self.session.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json() if response.content else {}
            except Timeout:
                print(f"请求 Clash 核心超时 ({attempt + 1}/{retries}): {url}")
            except RequestException as e:
                print(f"请求 Clash 核心网络异常 ({attempt + 1}/{retries}): {e}")
            
            time.sleep(1.0 * (attempt + 1))
        
        # 返回空回退字典，防止最外层抛错导致主线程断崖崩溃
        print(f"Clash 请求彻底失败，启动回退机制保护主线程: {url}")
        return {}

    def get_proxies(self):
        return self.safe_request("GET", "/proxies")

    def switch_proxy(self, selector_name, proxy_name):
        payload = {"name": proxy_name}
        return self.safe_request("PUT", f"/proxies/{selector_name}", json=payload)
