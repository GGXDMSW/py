import requests
from requests.exceptions import RequestException
import time

class SubscriptionService:
    def __init__(self):
        self.timeout = 10.0

    def fetch_subscription(self, url, retries=3):
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except RequestException as e:
                print(f"拉取订阅节点网络波动或超时 ({attempt + 1}/{retries}): {e}")
                time.sleep(2.0 * (attempt + 1))
        
        print(f"订阅拉取彻底失败，已拦截异常，保护主线程不死: {url}")
        return ""
        
    def update_all_subscriptions(self, urls):
        results = {}
        for url in urls:
            results[url] = self.fetch_subscription(url)
        return results
