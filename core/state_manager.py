import threading
import time

class StateManager:
    """
    线程安全的状态容器与多池数据管理器：
    使用 RLock 保证后台测速/调度流水线与前台 UI 表格渲染并发访问时绝对安全，
    彻底消除 'RuntimeError: dictionary/set changed size during iteration' 崩溃。
    """

    def __init__(self):
        self.lock = threading.RLock()

        # 核心集合与列表
        self.all_nodes = []
        self.favorites = set()
        self.local_blacklist = set()
        self.speed_blacklist = set()
        self.blacklist_reasons = {}
        self.fav_reasons = {}

        self.verified_nodes = {}
        self.stars_nodes = []

        # 实时测试数据与历史记录
        self.node_delays = {}
        self.node_speeds = {}
        self.node_colo = {}
        self.node_colo_history = {}
        self.node_history = {}
        self.node_speed_history = {}
        self.node_delay_history = {}
        self.node_details = {}
        self.auto_endpoints = set()

    def get_snapshot(self):
        """
        获取当前核心数据池的线程安全只读快照，供 UI 渲染使用
        """
        with self.lock:
            return {
                "all_nodes": list(self.all_nodes),
                "favorites": set(self.favorites),
                "local_blacklist": set(self.local_blacklist),
                "speed_blacklist": set(self.speed_blacklist),
                "blacklist_reasons": dict(self.blacklist_reasons),
                "fav_reasons": dict(self.fav_reasons),
                "verified_nodes": dict(self.verified_nodes),
                "stars_nodes": [dict(s) for s in self.stars_nodes],
                "node_delays": dict(self.node_delays),
                "node_speeds": dict(self.node_speeds),
                "node_colo": dict(self.node_colo),
                "node_colo_history": {k: list(v) for k, v in self.node_colo_history.items()},
                "node_history": {k: list(v) for k, v in self.node_history.items()},
                "node_speed_history": {k: list(v) for k, v in self.node_speed_history.items()},
                "node_delay_history": {k: list(v) for k, v in self.node_delay_history.items()},
                "node_details": dict(self.node_details),
                "auto_endpoints": set(self.auto_endpoints),
            }

    def add_favorite(self, node_name, reason=None):
        with self.lock:
            self.favorites.add(node_name)
            self.local_blacklist.discard(node_name)
            self.speed_blacklist.discard(node_name)
            if reason:
                self.fav_reasons[node_name] = str(reason)

    def discard_favorite(self, node_name):
        with self.lock:
            self.favorites.discard(node_name)

    def add_blacklist(self, key, reason="", bl_type="local"):
        with self.lock:
            if bl_type == "speed":
                self.speed_blacklist.add(key)
            else:
                self.local_blacklist.add(key)
            self.favorites.discard(key)
            if reason:
                self.blacklist_reasons[key] = str(reason)

    def remove_blacklist(self, key):
        with self.lock:
            self.local_blacklist.discard(key)
            self.speed_blacklist.discard(key)
            self.blacklist_reasons.pop(key, None)

    def record_delay(self, node_name, delay_val, rounds=4):
        with self.lock:
            self.node_delays[node_name] = delay_val
            if node_name not in self.node_history:
                self.node_history[node_name] = []
            self.node_history[node_name].append(delay_val)
            self.node_history[node_name] = self.node_history[node_name][-rounds:]

    def record_speed(self, node_name, speed_val):
        with self.lock:
            self.node_speeds[node_name] = speed_val
            if node_name not in self.node_speed_history:
                self.node_speed_history[node_name] = []
            self.node_speed_history[node_name].append(max(0.0, speed_val))
            self.node_speed_history[node_name] = self.node_speed_history[node_name][-4:]
