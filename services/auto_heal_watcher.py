"""
services/auto_heal_watcher.py
Mihomo 实时链路感知与秒级无感自愈守护服务 (多策略组与非香港业务隔离增强版)
"""
import datetime
import re
import threading
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional, Set, Tuple

from config.settings import EXCLUDE_HK_REGEX
from services.clash_client import ClashClient


class AutoHealWatcher:
    """
    后台常驻链路守护引擎：
    1. 并发监听多个核心策略组 (⚡ 自动选择 / ⚡ 自动选择 (非香港))
    2. 监听 Mihomo /connections API 抓取当前真实出口连接表 (CPU < 0.05%, 0额外外网流量)
    3. 检测单向发包黑洞 (Upload > 0, Download == 0 且持续多秒)
    4. 外科手术式斩断坏死连接 (DELETE /connections/{id}) 迫使客户端瞬间 TCP RST 重连
    5. 严格业务与区域隔离：
       - 【⚡ 自动选择 (非香港)】坏死时：严格在纯净非香港池（新加坡、日本、美国等）顺位补位，绝不切入香港！
       - 【⚡ 自动选择】坏死时：在全量精选池中挑选最优低延迟节点补位
    6. 熔断隔离坏死节点 15 分钟，防止反复横跳
    """

    def __init__(
        self,
        client: Optional[ClashClient] = None,
        get_candidates_fn: Optional[Callable[..., List[str]]] = None,
        on_heal_event: Optional[Callable[[str, str, dict], None]] = None,
        on_status_update: Optional[Callable[[dict], None]] = None,
        log_fn: Optional[Callable[[str], None]] = None,
        check_interval: float = 1.0,
        idle_timeout_seconds: float = 5.0,
        cooldown_duration: float = 900.0,
        min_switch_interval: float = 8.0,
        probe_timeout_ms: int = 1500,
        probe_url: str = "https://www.google.com/generate_204",
        min_blackhole_hosts: int = 2,
        is_pipeline_running_fn: Optional[Callable[[], bool]] = None,
    ):
        self.client = client or ClashClient()
        self.get_candidates_fn = get_candidates_fn
        self.on_heal_event = on_heal_event
        self.on_status_update = on_status_update
        self.log_fn = log_fn
        self.is_pipeline_running_fn = is_pipeline_running_fn

        # 核心探测参数
        self.enabled: bool = True
        self.check_interval: float = max(0.5, float(check_interval))
        self.idle_timeout_seconds: float = float(idle_timeout_seconds)
        self.min_blackhole_hosts: int = max(1, int(min_blackhole_hosts))
        self.probe_timeout_ms: int = max(500, int(probe_timeout_ms))
        self.cooldown_duration: float = 900.0      # 坏死节点临时熔断冷冻时长 (秒, 默认15分钟)
        self.min_switch_interval: float = 8.0      # 连续自愈最小时间间隔 (防雪崩/防抖动)
        self.conn_snapshots: Dict[str, dict] = {}  # {conn_id: {"up": int, "down": int, "ts": float, "stall_since": float}}
        self.probe_urls: List[str] = [
            "https://www.google.com/generate_204",
            "https://www.gstatic.com/generate_204",
        ]
        self.probe_url: str = probe_url

        # 【主循环彻底解耦与防抖核心】
        self._heal_lock = threading.Lock()
        self._healing_groups: Set[str] = set()     # 正在执行异步自愈流水线的策略组集合
        self._heal_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="AutoHealWorker")

        # 主动心跳巡检双保险配置 (Proactive Heartbeat)
        self.heartbeat_interval: float = 4.0       # 每 4 秒主动轮询一次当前在用节点
        self.last_heartbeat_time: float = 0.0
        self._heartbeat_lock = threading.Lock()
        self._heartbeat_running: bool = False
        
        # Cloudflare 专属平滑自愈与防抽风参数
        self.degrade_rtt_ms: int = 280            # 哨兵探针严重劣化判定门禁 (毫秒)
        self.strike_min_interval: float = 10.0    # 两次黄牌认定的最小观察间隔 (秒, 避免1秒内连出两牌)
        self.strike_window: float = 60.0          # 黄牌累积计分窗口 (秒)
        self.yellow_cards: Dict[str, float] = {}  # {node_name: last_strike_timestamp}
        self.soft_stall_bytes_limit: int = 3072   # 软失速下行速率下限 (字节/秒, 约3KB/s)

        # Google 送中感知冷冻黑名单与探针防御 (防香港 Anycast 导致 Gemini / IDE 报 403)
        self.google_hk_nodes: Dict[str, float] = {
            "东京 NRT 11.40 MB/s 3": time.time() + 86400,
            "东京 NRT 5.94 MB/s": time.time() + 86400,
            "东京 NRT 9.41 MB/s": time.time() + 86400,
        }
        self._last_google_check: Dict[str, float] = {}  # {node_name: last_check_ts}
        
        # 守护的核心策略组清单
        self.monitored_groups: List[str] = [
            "⚡ 自动选择",
            "⚡ 自动选择 (非香港)",
        ]

        # 内存热备候选队列缓存 (Pre-warmed Standby Cache, 0 延迟切换)
        self.standby_cache: Dict[str, List[str]] = {}

        # 运行时状态
        self._thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._lock = threading.Lock()
        
        self.cooldown_nodes: Dict[str, float] = {}  # {node_name: expire_timestamp}
        self.healed_count: int = 0
        self.last_heal_timestamp: float = 0.0
        self.last_heal_info: Optional[dict] = None
        
        self.current_active_node: str = ""         # 全量出口当前在用
        self.current_active_nohk_node: str = ""    # 非港出口当前在用
        self.current_status_summary: str = "守护就绪"

    def log(self, message: str):
        if callable(self.log_fn):
            try:
                self.log_fn(message)
            except Exception:
                pass

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._running = True
            self._thread = threading.Thread(
                target=self._loop,
                daemon=True,
                name="AutoHealWatcherThread"
            )
            self._thread.start()
            self.log("🛡️ [自愈引擎] 后台秒级链路守卫服务已启动 (双通道智能感知中)")

    def stop(self):
        with self._lock:
            self._running = False
        try:
            self._heal_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass

    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    def update_config(self, **kwargs):
        with self._lock:
            if "enabled" in kwargs:
                self.enabled = bool(kwargs["enabled"])
            if "check_interval" in kwargs:
                try:
                    self.check_interval = max(1.0, float(kwargs["check_interval"]))
                except (ValueError, TypeError):
                    pass
            if "blackhole_timeout" in kwargs:
                try:
                    self.blackhole_timeout = max(1.5, float(kwargs["blackhole_timeout"]))
                except (ValueError, TypeError):
                    pass
            if "cooldown_duration" in kwargs:
                try:
                    self.cooldown_duration = max(60.0, float(kwargs["cooldown_duration"]))
                except (ValueError, TypeError):
                    pass
            if "degrade_rtt_ms" in kwargs:
                try:
                    self.degrade_rtt_ms = max(100, int(kwargs["degrade_rtt_ms"]))
                except (ValueError, TypeError):
                    pass
            if "strike_min_interval" in kwargs:
                try:
                    self.strike_min_interval = max(5.0, float(kwargs["strike_min_interval"]))
                except (ValueError, TypeError):
                    pass
            if "strike_window" in kwargs:
                try:
                    self.strike_window = max(10.0, float(kwargs["strike_window"]))
                except (ValueError, TypeError):
                    pass
            if "probe_timeout_ms" in kwargs:
                try:
                    self.probe_timeout_ms = max(500, int(kwargs["probe_timeout_ms"]))
                except (ValueError, TypeError):
                    pass
            if "probe_url" in kwargs and kwargs["probe_url"]:
                self.probe_url = str(kwargs["probe_url"]).strip()
            if "min_blackhole_hosts" in kwargs:
                try:
                    self.min_blackhole_hosts = max(1, int(kwargs["min_blackhole_hosts"]))
                except (ValueError, TypeError):
                    pass

    def get_status_dict(self) -> dict:
        now = time.time()
        active_cooldowns = {k: int(v - now) for k, v in self.cooldown_nodes.items() if v > now}
        active_yellow_cards = {k: int(v + self.strike_window - now) for k, v in self.yellow_cards.items() if (v + self.strike_window) > now}
        active_google_hk = {k: int(v - now) for k, v in self.google_hk_nodes.items() if v > now}
        status_summary = self.current_status_summary
        if callable(self.is_pipeline_running_fn) and self.is_pipeline_running_fn():
            status_summary = "⏸️ 优选测速中 (心跳探针自动避让)"
        return {
            "enabled": self.enabled,
            "running": self.is_running(),
            "active_node": self.current_active_node,
            "active_nohk_node": self.current_active_nohk_node,
            "status_summary": status_summary,
            "healed_count": self.healed_count,
            "last_heal_time": self.last_heal_timestamp,
            "last_heal_info": self.last_heal_info,
            "cooldown_nodes_count": len(active_cooldowns),
            "cooldown_nodes": active_cooldowns,
            "yellow_cards_count": len(active_yellow_cards),
            "yellow_cards": active_yellow_cards,
            "google_hk_nodes_count": len(active_google_hk),
            "google_hk_nodes": active_google_hk,
        }

    def _parse_start_time(self, start_str: str) -> float:
        if not start_str:
            return 0.0
        try:
            clean_str = start_str
            if "+" in clean_str:
                dt_part, tz_part = clean_str.split("+", 1)
                if "." in dt_part:
                    base, micro = dt_part.split(".", 1)
                    clean_str = f"{base}.{micro[:6]}+{tz_part}"
                dt = datetime.datetime.fromisoformat(clean_str)
                return dt.timestamp()
            elif "Z" in clean_str:
                clean_str = clean_str.replace("Z", "+00:00")
                dt = datetime.datetime.fromisoformat(clean_str)
                return dt.timestamp()
        except Exception:
            pass
        return time.time()

    def _is_ignorable_background_host(self, host: str) -> bool:
        """
        判断是否为系统后台静默长轮询、推送通道或遥测连接 (如 Google FCM / Meet Signaler / Apple APNs)。
        这些连接由客户端发起后长期挂起等待服务端下发事件，期间无下行数据属于完全正常的预期行为，
        必须从断流与软失速检测中白名单排除，避免误判为物理黑洞。
        """
        if not host:
            return True
        h = host.lower().strip()
        ignorable_keywords = (
            "mtalk.google.com",
            "signaler-pa.clients6.google.com",
            "chat-pa.clients6.google.com",
            "push.apple.com",
            "pipe.aria.microsoft.com",
            "gateway.facebook.com",
        )
        for kw in ignorable_keywords:
            if kw in h:
                return True
        return False

    def _is_external_host(self, host: str) -> bool:
        if not host:
            return False
        h = host.lower().strip()
        if h in ("localhost", "127.0.0.1", "::1"):
            return False
        if h.endswith(".local") or h.endswith(".internal"):
            return False
        if h.startswith("192.168.") or h.startswith("10.") or h.startswith("172."):
            return False
        if self._is_ignorable_background_host(h):
            return False
        return True

    def _get_root_domain(self, host: str) -> str:
        """
        提取根域名 (Apex Domain)，将同厂不同子域名 (如 www.bing.com 与 cn.bing.com，
        或 YouTube 的不同 googlevideo.com CDN 节点) 聚类为同一个根域名，
        防止因访问单个网站时多个子域名并发请求误触发多域名断流判定。
        """
        if not host:
            return ""
        h = host.strip().lower()
        if ":" in h and not h.startswith("["):
            h = h.split(":")[0]

        parts = h.split(".")
        if len(parts) == 4 and all(p.isdigit() for p in parts):
            return h

        if len(parts) <= 2:
            return h

        second_level_tlds = {
            "com.cn", "net.cn", "org.cn", "gov.cn", "edu.cn",
            "co.uk", "org.uk", "me.uk",
            "com.hk", "org.hk", "net.hk", "edu.hk",
            "com.tw", "org.tw", "net.tw",
            "com.jp", "co.jp", "ne.jp",
            "com.sg", "edu.sg",
        }
        two_tail = f"{parts[-2]}.{parts[-1]}"
        if two_tail in second_level_tlds and len(parts) >= 3:
            return f"{parts[-3]}.{two_tail}"
        return f"{parts[-2]}.{parts[-1]}"

    def _loop(self):
        prev_loop_ts = time.time()
        while self._running:
            try:
                time.sleep(self.check_interval)
                if not self.enabled:
                    self.current_status_summary = "已暂停守护"
                    prev_loop_ts = time.time()
                    continue

                now = time.time()
                # 检测系统休眠/挂起唤醒或时间大跳变 (实际间隔严重超出预期步长 8.0 秒以上)
                if (now - prev_loop_ts) > 8.0:
                    prev_loop_ts = now
                    self.conn_snapshots.clear()
                    self.last_heartbeat_time = now + 2.0  # 延后主动心跳，给予网卡 Wi-Fi 2~3 秒握手缓冲
                    self.log("💤 [休眠唤醒保护] 检测到系统唤醒或时间跳变，已重置监控快照并给予网卡 3 秒重连缓冲")
                    continue
                prev_loop_ts = now

                self._check_and_heal()
            except Exception:
                pass

    def _check_and_heal(self):
        if callable(self.is_pipeline_running_fn) and self.is_pipeline_running_fn():
            self.current_status_summary = "⏸️ 优选测速中 (心跳探针自动避让)"
            self._notify_status()
            return

        now = time.time()

        # 1. 轻量拉取各组当前在用节点（调用 self.client.get_proxy(grp)）
        group_current_nodes: Dict[str, str] = {}
        for grp in self.monitored_groups:
            g_data = self.client.get_proxy(grp, timeout=0.8)
            c_node = g_data.get("now", "")
            if c_node:
                group_current_nodes[grp] = c_node

        self.current_active_node = group_current_nodes.get("⚡ 自动选择", "未知出口")
        self.current_active_nohk_node = group_current_nodes.get("⚡ 自动选择 (非香港)", "未知非港出口")

        # 2. 读取当前活跃连接快照
        conns_data = self.client.get_connections(timeout=1.5)
        if not conns_data or not isinstance(conns_data, dict):
            return

        connections = conns_data.get("connections", [])
        if not connections:
            self.conn_snapshots.clear()
            self.current_status_summary = f"空闲就绪 (全量: {self.current_active_node} | 非港: {self.current_active_nohk_node})"
            self._notify_status()
            return

        # 3. 严格协议过滤与 Delta Rate 增量计算
        blackhole_hosts: Dict[Tuple[str, str], Set[str]] = {}
        blackhole_conn_ids: Dict[Tuple[str, str], List[str]] = {}
        blackhole_stall_types: Dict[Tuple[str, str], Set[str]] = {}
        blackhole_max_durations: Dict[Tuple[str, str], float] = {}
        active_cids: Set[str] = set()

        for conn in connections:
            cid = conn.get("id")
            if not cid:
                continue
            active_cids.add(cid)

            # 严格协议过滤：仅分析 net_type == "tcp" 的外部连接，非 TCP 协议（UDP/ICMP）直接 continue 跳过
            metadata = conn.get("metadata", {})
            net_type = str(metadata.get("network", "") or conn.get("network", "")).lower()
            if net_type != "tcp":
                continue

            host = metadata.get("host") or metadata.get("destinationIP") or ""
            if not self._is_external_host(host):
                continue

            chains = conn.get("chains", [])
            node_name = chains[0] if chains else ""
            if not node_name:
                continue

            upload = conn.get("upload", 0)
            download = conn.get("download", 0)
            start_ts = self._parse_start_time(conn.get("start", ""))
            duration = now - start_ts

            is_stalled = False
            stall_type = ""
            stall_duration = 0.0

            # 4. Delta Rate 增量计算与严格四态状态机
            if cid not in self.conn_snapshots:
                # 若 conn_id 首次出现：初始化 snapshot
                if upload > 0 and download == 0:
                    stall_since = (now - duration) if duration > 0 else now
                    if duration >= self.blackhole_timeout:
                        is_stalled = True
                        stall_type = "硬断流"
                        stall_duration = duration
                elif upload > 0:
                    stall_since = now
                else:
                    stall_since = 0.0

                self.conn_snapshots[cid] = {
                    "up": upload,
                    "down": download,
                    "ts": now,
                    "stall_since": stall_since,
                }
            else:
                prev = self.conn_snapshots[cid]
                delta_up = upload - prev["up"]
                delta_down = download - prev["down"]
                prev["up"], prev["down"], prev["ts"] = upload, download, now

                # 严格四态状态转移：
                # (a) 若 delta_down > 0: 说明真正接收到了服务端回包，链路健康畅通，解除计时
                if delta_down > 0:
                    prev["stall_since"] = 0.0
                # (b) 若 delta_up > 0: 客户端产生新上传，若此前未处于挂起状态，则置 stall_since = now
                elif delta_up > 0:
                    if prev["stall_since"] == 0.0:
                        prev["stall_since"] = now
                # (c) 若 upload > 0 and download == 0: 纯物理发包黑洞，若未挂起则置 stall_since = now
                elif upload > 0 and download == 0:
                    if prev["stall_since"] == 0.0:
                        prev["stall_since"] = now
                # (d) 若 delta_up == 0 and delta_down == 0: 客户端处于等待服务端响应的挂起状态 (In-Flight)
                # 【关键红线】：若此时 prev["stall_since"] > 0.0，绝对禁止重置为 0.0！必须保持原有时间戳继续累加！
                else:
                    pass

                # 判定是否超时卡死
                if prev["stall_since"] > 0.0 and (now - prev["stall_since"]) >= self.blackhole_timeout:
                    is_stalled = True
                    stall_type = "在途软失速" if download > 0 else "硬断流"
                    stall_duration = now - prev["stall_since"]

            if is_stalled:
                matched_grp = None
                for grp in self.monitored_groups:
                    if grp in chains:
                        matched_grp = grp
                        break

                if not matched_grp:
                    for grp, curr_n in group_current_nodes.items():
                        if curr_n == node_name:
                            matched_grp = grp
                            break

                if not matched_grp:
                    matched_grp = "⚡ 自动选择"

                pair_key = (matched_grp, node_name)
                if pair_key not in blackhole_hosts:
                    blackhole_hosts[pair_key] = set()
                    blackhole_conn_ids[pair_key] = []
                    blackhole_stall_types[pair_key] = set()
                    blackhole_max_durations[pair_key] = 0.0

                root_domain = self._get_root_domain(host)
                blackhole_hosts[pair_key].add(root_domain or host)
                blackhole_conn_ids[pair_key].append(cid)
                blackhole_stall_types[pair_key].add(stall_type)
                if stall_duration > blackhole_max_durations[pair_key]:
                    blackhole_max_durations[pair_key] = stall_duration

        # 5. 清理已断开连接的 snapshot 字典，防止内存泄漏
        dead_keys = [k for k in self.conn_snapshots if k not in active_cids]
        for k in dead_keys:
            self.conn_snapshots.pop(k, None)

        # 6. 复合触发判定与异步分发（0ms 阻塞）
        self._refresh_standby_cache()

        for grp, curr_n in group_current_nodes.items():
            pair_key = (grp, curr_n)
            distinct_hosts = blackhole_hosts.get(pair_key, set())
            stalled_conns = blackhole_conn_ids.get(pair_key, [])
            max_stall_duration = blackhole_max_durations.get(pair_key, 0.0)

            # 多阶自愈触发门禁：适配单应用 IDE (如反重力) 与流式大模型长连接
            is_suspicious = (
                (len(distinct_hosts) >= self.min_blackhole_hosts) or
                (len(distinct_hosts) >= 1 and len(stalled_conns) >= 2) or
                (len(stalled_conns) >= 1 and max_stall_duration >= max(3.0, self.blackhole_timeout * 1.5))
            )

            if is_suspicious:
                # 【防抖防重入门禁检查】
                with self._heal_lock:
                    if grp in self._healing_groups:
                        continue  # 该策略组已有后台自愈任务在执行，跳过，绝不重复触发！
                    if (now - self.last_heal_timestamp) < self.min_switch_interval:
                        continue  # 处于避震窗口内，跳过
                    # 成功获取自愈任务令牌
                    self._healing_groups.add(grp)

                # 【Fire-and-Forget 瞬间分发到独立线程池，主循环 0 毫秒放行，绝不等待任何结果】
                stall_desc = "/".join(sorted(list(blackhole_stall_types.get(pair_key, set())))) or "断流"
                is_non_hk = ("非香港" in grp)
                self._heal_executor.submit(
                    self._async_heal_worker,
                    grp,
                    curr_n,
                    list(distinct_hosts),
                    list(stalled_conns),
                    is_non_hk,
                    stall_desc,
                )

        with self._heal_lock:
            currently_healing = list(self._healing_groups)

        if currently_healing:
            self.current_status_summary = (
                f"🔄 深度自愈探查中 (目标组: {', '.join(currently_healing)})"
            )
            self._notify_status()
        else:
            active_count = len(connections)
            yc_count = len([k for k, v in self.yellow_cards.items() if (now - v) <= self.strike_window])
            yc_str = f" | 🟨黄牌节点: {yc_count}" if yc_count > 0 else ""
            self.current_status_summary = (
                f"🟢 双通道畅通 (全量: {self.current_active_node} | 非港: {self.current_active_nohk_node} | 活跃: {active_count}{yc_str})"
            )
            self._notify_status()

        # 7. 主动心跳巡检双保险 (Proactive Heartbeat - 0ms 异步分发)
        if (now - self.last_heartbeat_time) >= self.heartbeat_interval:
            with self._heartbeat_lock:
                if not self._heartbeat_running:
                    self._heartbeat_running = True
                    self.last_heartbeat_time = now
                    self._heal_executor.submit(self._proactive_heartbeat_worker)

    def _async_heal_worker(
        self,
        grp: str,
        curr_n: str,
        distinct_hosts: list,
        dead_conn_ids: list,
        is_non_hk: bool,
        stall_desc: str,
    ):
        """
        独立线程池中执行的自愈工作流水线：
        双通道 HTTPS 竞速探针 -> 裁决判定 -> 顺位切换 -> 并发清理僵尸连接
        """
        try:
            # 1. 双通道 HTTPS 并发竞速探针（验证 443 端口与 TLS 握手）
            probe_delay = 99999
            for u in self.probe_urls:
                d = self.client.query_proxy_delay(curr_n, u, timeout_ms=self.probe_timeout_ms)
                if d < probe_delay:
                    probe_delay = d
                if probe_delay < self.degrade_rtt_ms:
                    break  # 极速响应直接短路返回，无需重复探测

            # 2. 探针裁决逻辑
            now = time.time()
            hosts_preview = ", ".join(sorted(distinct_hosts)[:3])
            if probe_delay >= 99999:
                # 确认物理暴毙，立即下发自愈顺移
                dead_reason = (
                    f"【{grp}】并发 {len(distinct_hosts)} 个主域名{stall_desc}且 HTTPS 探针超时暴毙 (目标: {hosts_preview})"
                )
                self.yellow_cards.pop(curr_n, None)
                self._execute_auto_heal(
                    target_group=grp,
                    dead_node=curr_n,
                    reason=dead_reason,
                    dead_conn_ids=dead_conn_ids,
                    is_non_hk=is_non_hk,
                )
            elif probe_delay >= self.degrade_rtt_ms:
                # 黄牌观察与两黄变一红机制
                last_card_ts = self.yellow_cards.get(curr_n, 0.0)
                time_since_last_card = now - last_card_ts
                if self.strike_min_interval <= time_since_last_card <= self.strike_window:
                    dead_reason = (
                        f"【{grp}】二次抽风/延迟严重劣化 ({probe_delay}ms >= {self.degrade_rtt_ms}ms, {stall_desc}) (目标: {hosts_preview})"
                    )
                    self.yellow_cards.pop(curr_n, None)
                    self._execute_auto_heal(
                        target_group=grp,
                        dead_node=curr_n,
                        reason=dead_reason,
                        dead_conn_ids=dead_conn_ids,
                        is_non_hk=is_non_hk,
                    )
                elif time_since_last_card > self.strike_window or last_card_ts == 0.0:
                    self.yellow_cards[curr_n] = now
                    self.log(f"🟨 [自愈黄牌] 节点 【{curr_n}】 延迟飙升 ({probe_delay}ms)，出示黄牌进入观察期...")
                    self.current_status_summary = f"🟨 黄牌警告 ({curr_n} 延迟 {probe_delay}ms) | 观察中"
                    self._notify_status()
            else:
                # 探针极速通畅，一票否决证明健康
                if curr_n in self.yellow_cards and (now - self.yellow_cards[curr_n]) > self.strike_window:
                    self.yellow_cards.pop(curr_n, None)
        except Exception as e:
            self.log(f"⚠️ [自愈流水线异常] {grp} 自愈处理过程发生异常: {e}")
        finally:
            # 【防抖锁释放】：流水线结束（无论成功或异常），必须在锁内移出 grp
            with self._heal_lock:
                self._healing_groups.discard(grp)

    def _proactive_heartbeat_worker(self):
        """
        后台异步主动心跳巡检双保险流水线：
        周期性轻量化双探针竞速探测各受监控策略组当前在用节点的可用性，
        若检测到物理暴毙（超时 >= 99999ms）或非港出口触发 Google 送中，抓取坏死连接并立即触发自愈切换。
        """
        if callable(self.is_pipeline_running_fn) and self.is_pipeline_running_fn():
            self.current_status_summary = "⏸️ 优选测速中 (心跳探针自动避让)"
            self._notify_status()
            return

        try:
            now = time.time()
            for grp in self.monitored_groups:
                g_data = self.client.get_proxy(grp, timeout=0.8)
                c_node = g_data.get("now", "")
                if not c_node:
                    continue

                is_non_hk = ("非香港" in grp)

                # (0) 非香港策略组专属：Google 送中洁净度感知防御双保险
                if is_non_hk:
                    is_google_hk = False
                    if c_node in self.google_hk_nodes and self.google_hk_nodes[c_node] > now:
                        is_google_hk = True
                    elif (now - self._last_google_check.get(c_node, 0.0)) >= 30.0:
                        self._last_google_check[c_node] = now
                        try:
                            mix_port = self.client.get_mixed_port(default=7897)
                            proxy_handler = urllib.request.ProxyHandler({
                                "http": f"http://127.0.0.1:{mix_port}",
                                "https": f"http://127.0.0.1:{mix_port}",
                            })
                            opener = urllib.request.build_opener(proxy_handler)
                            g_req = urllib.request.Request("https://www.google.com", headers={"User-Agent": "Mozilla/5.0"})
                            with opener.open(g_req, timeout=2.0) as g_resp:
                                final_u = g_resp.geturl()
                                if "google.com.hk" in final_u:
                                    is_google_hk = True
                                    self.google_hk_nodes[c_node] = now + 43200
                                    self.log(f"🚨 [Google送中感知] 节点 【{c_node}】 访问 google.com 被重定向至 {final_u}，触发非港自愈冷冻！")
                        except Exception:
                            pass

                    if is_google_hk:
                        with self._heal_lock:
                            if grp in self._healing_groups:
                                continue
                            if (now - self.last_heal_timestamp) < self.min_switch_interval:
                                continue
                            self._healing_groups.add(grp)

                        try:
                            dead_cids = []
                            try:
                                conns_data = self.client.get_connections(timeout=1.2)
                                if conns_data and isinstance(conns_data, dict):
                                    for conn in conns_data.get("connections", []):
                                        chains = conn.get("chains", [])
                                        if c_node in chains or (chains and chains[0] == c_node):
                                            cid = conn.get("id")
                                            if cid:
                                                dead_cids.append(cid)
                            except Exception:
                                dead_cids = []

                            self._execute_auto_heal(
                                target_group=grp,
                                dead_node=c_node,
                                reason=f"【{grp}】节点触发 Google 送中 (.hk) 违规熔断，保护 Gemini / IDE 会话",
                                dead_conn_ids=dead_cids,
                                is_non_hk=True,
                            )
                        finally:
                            with self._heal_lock:
                                self._healing_groups.discard(grp)
                        continue

                # (a) 双探针竞速探测
                d = 99999
                for u in self.probe_urls:
                    cur_d = self.client.query_proxy_delay(c_node, u, timeout_ms=self.probe_timeout_ms)
                    if cur_d < d:
                        d = cur_d
                    if d < self.degrade_rtt_ms:
                        break

                if d >= 99999:
                    # 二次复验防抖机制：首次超时后等待 500ms 重试确认，两次均超时方判定为暴毙
                    time.sleep(0.5)
                    d2 = 99999
                    for u in self.probe_urls:
                        cur_d2 = self.client.query_proxy_delay(c_node, u, timeout_ms=self.probe_timeout_ms)
                        if cur_d2 < d2:
                            d2 = cur_d2
                        if d2 < self.degrade_rtt_ms:
                            break
                    if d2 < 99999:
                        # 二次复验恢复健康，安全放行
                        continue

                    with self._heal_lock:
                        if grp in self._healing_groups:
                            continue  # 被动异步工作线程已在处理该组自愈，主动心跳主动让行，杜绝重复触发
                        if (now - self.last_heal_timestamp) < self.min_switch_interval:
                            continue  # 处于避震窗口期，跳过
                        self._healing_groups.add(grp)

                    try:
                        # (b) 确认物理暴毙，主动从内核抓取当前所有活跃连接，提取挂在该坏死节点上的连接 ID
                        dead_cids = []
                        try:
                            conns_data = self.client.get_connections(timeout=1.2)
                            if conns_data and isinstance(conns_data, dict):
                                for conn in conns_data.get("connections", []):
                                    chains = conn.get("chains", [])
                                    if c_node in chains or (chains and chains[0] == c_node):
                                        cid = conn.get("id")
                                        if cid:
                                            dead_cids.append(cid)
                        except Exception:
                            dead_cids = []

                        # (c) 传入 dead_conn_ids 立即并发清退，触发客户端瞬间重连
                        self._execute_auto_heal(
                            target_group=grp,
                            dead_node=c_node,
                            reason=f"【{grp}】主动心跳探针探测超时(>{self.probe_timeout_ms}ms物理断流)",
                            dead_conn_ids=dead_cids,
                            is_non_hk=is_non_hk,
                        )
                    finally:
                        with self._heal_lock:
                            self._healing_groups.discard(grp)
        except Exception as e:
            self.log(f"⚠️ [主动心跳探针异常] 巡检过程发生错误: {e}")
        finally:
            with self._heartbeat_lock:
                self._heartbeat_running = False

    def _execute_auto_heal(
        self,
        target_group: str,
        dead_node: str,
        reason: str,
        dead_conn_ids: List[str],
        is_non_hk: bool = False,
    ):
        now = time.time()
        if now - self.last_heal_timestamp < self.min_switch_interval:
            self.log(f"⚠️ [自愈避震] 策略组 【{target_group}】 节点 {dead_node} 异常，但距离上次切换不足 {int(self.min_switch_interval)}s，暂缓动作")
            return

        tag_prefix = "🛡️ [非港AI自愈]" if is_non_hk else "🚨 [全量出口自愈]"
        self.log(f"{tag_prefix} 检测到策略组 【{target_group}】 当前在用节点 【{dead_node}】 触发自愈！原因: {reason}")

        # 步骤 1：挑选次优顺位备选节点 (若为非港组，绝对排除香港)
        backup_node = self._pick_backup_node(
            target_group=target_group,
            exclude_node=dead_node,
            is_non_hk=is_non_hk,
        )
        if not backup_node:
            self.log(f"❌ [自愈失败] 策略组 【{target_group}】 中未找到可用的健康备选节点！")
            return

        # 步骤 2：毫秒级优雅引流 —— 0ms 瞬间把出口切换至热备节点 (所有新请求/重发秒走新路)
        t0 = time.perf_counter()
        switched = self.client.switch_proxy(target_group, backup_node, timeout=1.5)
        switch_cost_ms = (time.perf_counter() - t0) * 1000

        if switched:
            # 步骤 3：坏死节点冷冻熔断 15 分钟 (若触发 Google 送中则冷冻 12 小时)
            self.cooldown_nodes[dead_node] = now + self.cooldown_duration
            if is_non_hk and ("Google 送中" in reason or dead_node in self.google_hk_nodes):
                self.google_hk_nodes[dead_node] = max(self.google_hk_nodes.get(dead_node, 0.0), now + 43200)
            self.healed_count += 1
            self.last_heal_timestamp = now

            if is_non_hk:
                self.current_active_nohk_node = backup_node
            else:
                self.current_active_node = backup_node

            self.last_heal_info = {
                "group": target_group,
                "dead_node": dead_node,
                "backup_node": backup_node,
                "is_non_hk": is_non_hk,
                "cost_ms": round(switch_cost_ms, 1),
                "evicted": len(dead_conn_ids),
                "reason": reason,
                "time": time.strftime("%H:%M:%S", time.localtime(now))
            }

            non_hk_tip = " (已严格继承非港限制，Gemini/反重力保持畅通)" if is_non_hk else ""
            log_msg = f"✨ [优雅引流完成] 策略组 【{target_group}】 耗时 {switch_cost_ms:.1f}ms 顺移至备选节点 【{backup_node}】！{non_hk_tip}"
            self.log(log_msg)

            # 步骤 4：异步平滑并发清退 —— 双保险真空吸尘器
            def _delayed_drain():
                evicted_count = 0
                # 1. 优先并发斩断预先抓取到的指定死连接 ID
                valid_cids = [cid for cid in dead_conn_ids if cid]
                if valid_cids:
                    try:
                        with ThreadPoolExecutor(max_workers=8) as pool:
                            results = list(pool.map(lambda cid: self.client.close_connection(cid, timeout=0.8), valid_cids))
                            evicted_count += sum(1 for r in results if r)
                    except Exception:
                        pass

                # 2. 毫秒级二次真空扫尾：调用底层 close_connections_by_proxy 切断任何残留或刚产生的孤儿连接
                try:
                    time.sleep(0.1)  # 给予 100ms 裕量让策略组路由完全生效
                    extra_closed = self.client.close_connections_by_proxy(dead_node, timeout=1.2)
                    evicted_count += extra_closed
                except Exception:
                    pass

                if evicted_count > 0:
                    self.log(f"🔪 [定点扫尾] 已双重并发精准清理旧节点 【{dead_node}】 遗留的 {evicted_count} 条死锁僵尸连接")

            threading.Thread(target=_delayed_drain, daemon=True, name="HealDrainThread").start()

            self.current_status_summary = f"⚡ 刚刚自愈: 【{target_group}】已顺移至 {backup_node}"

            if callable(self.on_heal_event):
                try:
                    self.on_heal_event(dead_node, backup_node, self.last_heal_info)
                except Exception:
                    pass
        else:
            self.log(f"❌ [自愈切换失败] 向策略组 【{target_group}】 推送目标节点失败！")

        self._notify_status()

    def _refresh_standby_cache(self, proxies_map: Optional[dict] = None):
        """
        在后台心跳中预先计算并缓存各策略组的顺位热备节点 (Pre-warmed Standby)，
        100% 以内核策略组真实 all 成员为唯一权威事实源，彻底消灭 HTTP 400 切换脱节。
        """
        now = time.time()
        for grp in self.monitored_groups:
            is_non_hk = ("非香港" in grp)

            # (a) 100% 以内核该策略组的真实成员为权威基准
            all_members: List[str] = []
            if proxies_map and grp in proxies_map:
                all_members = list(proxies_map.get(grp, {}).get("all", []))
            if not all_members:
                g_data = self.client.get_proxy(grp, timeout=0.8)
                all_members = list(g_data.get("all", []))

            if not all_members:
                continue

            # (b) 区域合规过滤 (非港组剔除香港节点及被 Google 送中冷冻的节点)
            if is_non_hk:
                valid_members = [
                    c for c in all_members
                    if c and not EXCLUDE_HK_REGEX.search(c)
                    and (c not in self.google_hk_nodes or self.google_hk_nodes[c] <= now)
                ]
            else:
                valid_members = [c for c in all_members if c]

            if not valid_members:
                continue

            # (d) 智能排序算法：从节点名正则提取速度，结合 get_candidates_fn 建立权重映射
            fav_cands: List[str] = []
            if callable(self.get_candidates_fn):
                try:
                    fav_cands = self.get_candidates_fn(is_non_hk=is_non_hk) or []
                except TypeError:
                    fav_cands = self.get_candidates_fn() or []
                except Exception:
                    fav_cands = []

            fav_rank = {name: idx for idx, name in enumerate(fav_cands)}

            def _sort_key(name: str):
                m = re.search(r"([\d.]+)\s*MB/s", name, re.IGNORECASE)
                sp = float(m.group(1)) if m else 0.0
                rank = fav_rank.get(name, 9999)
                return (-sp, rank, name)

            sorted_members = sorted(valid_members, key=_sort_key)

            # (e) 过滤掉当前处于 15 分钟熔断冷冻期的节点，若全在冷却期则保留有效成员兜底
            ready_cands = [c for c in sorted_members if (c not in self.cooldown_nodes or self.cooldown_nodes[c] <= now)]
            self.standby_cache[grp] = ready_cands or sorted_members

    def _pick_backup_node(
        self,
        target_group: str,
        exclude_node: str,
        is_non_hk: bool = False,
    ) -> Optional[str]:
        """
        以内核当前策略组的真实成员为唯一事实基准，挑选最佳顺位备选节点 (消灭 400 脱节)
        """
        now = time.time()

        # 1. 优先直接从内存热备队列中取出首个非死且真实存在的未冷冻节点 (0 毫秒开销)
        cached = self.standby_cache.get(target_group, [])
        for cand in cached:
            if is_non_hk and cand in self.google_hk_nodes and self.google_hk_nodes[cand] > now:
                continue
            if cand and cand != exclude_node and (cand not in self.cooldown_nodes or self.cooldown_nodes[cand] <= now):
                return cand

        # 2. 若热备缓存未命中，实时以内核该策略组真实成员为权威基准提取
        g_data = self.client.get_proxy(target_group, timeout=1.0)
        all_members = list(g_data.get("all", []))
        if not all_members:
            return None

        # (b) 区域合规过滤 (非港组剔除香港节点及被 Google 送中冷冻的节点)
        if is_non_hk:
            valid_members = [
                c for c in all_members
                if c and not EXCLUDE_HK_REGEX.search(c)
                and (c not in self.google_hk_nodes or self.google_hk_nodes[c] <= now)
            ]
        else:
            valid_members = [c for c in all_members if c]

        # (c) 排除当前坏死节点
        candidates = [c for c in valid_members if c != exclude_node]
        if not candidates:
            return None

        # (d) 智能排序算法：正则提取下行速度并结合 get_candidates_fn 排序
        fav_cands: List[str] = []
        if callable(self.get_candidates_fn):
            try:
                fav_cands = self.get_candidates_fn(is_non_hk=is_non_hk) or []
            except TypeError:
                fav_cands = self.get_candidates_fn() or []
            except Exception:
                fav_cands = []

        fav_rank = {name: idx for idx, name in enumerate(fav_cands)}

        def _sort_key(name: str):
            m = re.search(r"([\d.]+)\s*MB/s", name, re.IGNORECASE)
            sp = float(m.group(1)) if m else 0.0
            rank = fav_rank.get(name, 9999)
            return (-sp, rank, name)

        candidates.sort(key=_sort_key)

        # (e) 优先返回未在 15 分钟熔断冷冻期的顶级节点
        for cand in candidates:
            if cand not in self.cooldown_nodes or self.cooldown_nodes[cand] <= now:
                return cand

        # (e 兜底) 若全部处于冷却期，返回除 exclude_node 之外评分最高的有效成员兜底
        for cand in candidates:
            return cand

        return None

    def _notify_status(self):
        if callable(self.on_status_update):
            try:
                self.on_status_update(self.get_status_dict())
            except Exception:
                pass

    def diagnose_current_link(self) -> dict:
        """
        一键手动双通道链路深度诊断
        """
        g_auto = self.client.get_proxy("⚡ 自动选择", timeout=1.2)
        g_nohk = self.client.get_proxy("⚡ 自动选择 (非香港)", timeout=1.2)
        auto_now = g_auto.get("now", "")
        nohk_now = g_nohk.get("now", "")

        delay_auto = self.client.query_proxy_delay(auto_now, self.probe_url, timeout_ms=1500) if auto_now else 99999
        delay_nohk = self.client.query_proxy_delay(nohk_now, self.probe_url, timeout_ms=1500) if nohk_now else 99999

        conns_data = self.client.get_connections(timeout=2.0)
        total_conns = len(conns_data.get("connections", []))

        is_healthy = (delay_auto < 99999 and delay_nohk < 99999)
        return {
            "active_node": auto_now or "未获取到",
            "active_nohk_node": nohk_now or "未获取到",
            "delay_ms": delay_auto if delay_auto < 99999 else "超时(断流)",
            "delay_nohk_ms": delay_nohk if delay_nohk < 99999 else "超时(断流)",
            "is_healthy": is_healthy,
            "total_connections": total_conns,
            "healed_count": self.healed_count,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
