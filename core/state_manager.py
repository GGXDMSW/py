import threading


class StateManager:
    _instance = None
    _init_lock = threading.Lock()

    def __new__(cls):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        # 采用 RLock 允许重入，避免同一线程内多次请求产生的死锁
        self._global_lock = threading.RLock()
        self._thread_stop_events = {}

        # 核心业务状态容器（预置默认容器初值，彻底杜绝 AttributeError）
        self.all_nodes = []
        self.node_details = {}
        self.active_profile = ""
        self.favorites = set()
        self.local_blacklist = set()
        self.speed_blacklist = set()
        self.blacklist_reasons = {}
        self.fav_reasons = {}
        self.verified_nodes = {}
        self.stars_nodes = []
        self.auto_endpoints = {}
        self.cloud_endpoints = {}
        self.node_delays = {}
        self.node_speeds = {}
        self.node_colo = {}
        self.node_history = {}
        self.node_speed_history = {}
        self.node_delay_history = {}
        self.node_colo_history = {}
        self.blacklist_timestamps = {}

    @property
    def lock(self):
        return self._global_lock

    def get_stop_event(self, thread_name: str) -> threading.Event:
        with self._global_lock:
            if thread_name not in self._thread_stop_events:
                self._thread_stop_events[thread_name] = threading.Event()
            return self._thread_stop_events[thread_name]

    def request_stop(self, thread_name: str):
        # 优雅发出终止信号，替代系统级暴力 kill 线程
        with self._global_lock:
            if thread_name in self._thread_stop_events:
                self._thread_stop_events[thread_name].set()

    def clear_stop_request(self, thread_name: str):
        with self._global_lock:
            if thread_name in self._thread_stop_events:
                self._thread_stop_events[thread_name].clear()

    def safe_execute(self, func, *args, **kwargs):
        # 提供上下文环境安全执行，采用 timeout 拦截永久死锁，异常时绝对保证释放锁
        acquired = self._global_lock.acquire(timeout=5.0)
        if not acquired:
            raise TimeoutError("无法获取全局状态互斥锁，检测到潜在死锁残留。")
        try:
            return func(*args, **kwargs)
        finally:
            try:
                self._global_lock.release()
            except RuntimeError:
                pass

    def get_snapshot(self):
        """
        线程安全导出状态机全局快照
        """
        with self._global_lock:
            return {
                "favorites": list(self.favorites),
                "local_blacklist": list(self.local_blacklist),
                "speed_blacklist": list(self.speed_blacklist),
                "blacklist_reasons": dict(self.blacklist_reasons),
                "fav_reasons": dict(self.fav_reasons),
                "verified_nodes": dict(self.verified_nodes),
                "stars_nodes": list(self.stars_nodes),
                "node_delays": dict(self.node_delays),
                "node_speeds": dict(self.node_speeds),
                "node_colo": dict(self.node_colo),
                "node_history": dict(self.node_history),
                "node_speed_history": dict(self.node_speed_history),
                "node_delay_history": dict(self.node_delay_history),
                "node_colo_history": dict(self.node_colo_history),
                "blacklist_timestamps": dict(self.blacklist_timestamps),
                "cloud_endpoints": dict(self.cloud_endpoints),
                "all_nodes": list(self.all_nodes),
                "active_profile": str(self.active_profile),
            }
