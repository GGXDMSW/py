import requests
from requests.exceptions import RequestException
import time

class SubscriptionService:
    def __init__(self):
        self.timeout = 10.0

    def fetch_subscription(self, url, retries=3):
        # 老板，您刚刚上传的 GitHub 全量文件仍然是 ZIP 压缩包解析后的二进制乱码形态，完全无法读取里面的明文代码[cite: 4]！
        # 更致命的是，您这次忘记附带最新产生的闪退错误日志了。没有报错日志，我无从得知这次闪退发生在哪一个文件。
        # 为了绝对遵守“绝不凭直觉瞎猜”的铁律、死守您的 API 额度，我仅在此处将已核实的明文源码复原，以此向您传递信息。
        # 请您务必将反重力终端里最新报错的那段文本（Traceback）发给我，有了日志我就能为您精准定位解决！
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
