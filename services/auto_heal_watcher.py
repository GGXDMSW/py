"""
services/auto_heal_watcher.py
Mihomo 实时链路感知与秒级无感自愈守护服务 (多策略组与非香港业务隔离增强版)
"""
import datetime
import re
import threading
import time
import urllib.parse
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
    ):
        self.client = client or ClashClient()
        self.get_candidates_fn = get_candidates_fn
        self.on_heal_event = on_heal_event
        self.on_status_update = on_status_update
        self.log_fn = log_fn

        # 核心超高速敏捷参数配置
        self.enabled: bool = True
        self.check_interval: float = 1.0           # 轮询探测心跳提升至 1.0 秒 (毫秒级敏捷响应)
        self.blackhole_timeout: float = 2.0        # 单向黑洞判定时长缩短至 2.0 秒 (超敏捷捕获)
        self.min_blackhole_hosts: int = 2          # 触发判定所需的最少并发异构域名数
        self.probe_timeout_ms: int = 1200          # 哨兵微探针超时对齐客户端 (1200ms 容纳 VLESS TLS 冷启动与首包重传，彻底消除假超时)
        self.cooldown_duration: float = 900.0      # 坏死节点临时熔断冷冻时长 (秒, 默认15分钟)
        self.min_switch_interval: float = 8.0      # 连续自愈最小时间间隔 (防雪崩/防抖动)
        self.probe_url: str = "http://www.gstatic.com/generate_204"  # 对齐客户端明文探测 URL，无多余 TLS 开销
        
        # Cloudflare 专属平滑自愈与防抽风参数
        self.degrade_rtt_ms: int = 280            # 哨兵探针严重劣化判定门禁 (毫秒)
        self.strike_min_interval: float = 10.0    # 两次黄牌认定的最小观察间隔 (秒, 避免1秒内连出两牌)
        self.strike_window: float = 60.0          # 黄牌累积计分窗口 (秒)
        self.yellow_cards: Dict[str, float] = {}  # {node_name: last_strike_timestamp}
        self.soft_stall_bytes_limit: int = 3072   # 软失速下行速率下限 (字节/秒, 约3KB/s)
        
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
        return {
            "enabled": self.enabled,
            "running": self.is_running(),
            "active_node": self.current_active_node,
            "active_nohk_node": self.current_active_nohk_node,
            "status_summary": self.current_status_summary,
            "healed_count": self.healed_count,
            "last_heal_time": self.last_heal_timestamp,
            "last_heal_info": self.last_heal_info,
            "cooldown_nodes_count": len(active_cooldowns),
            "cooldown_nodes": active_cooldowns,
            "yellow_cards_count": len(active_yellow_cards),
            "yellow_cards": active_yellow_cards,
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
            "antigravity-unleash.goog",
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
        while self._running:
            try:
                time.sleep(self.check_interval)
                if not self.enabled:
                    self.current_status_summary = "已暂停守护"
                    continue

                self._check_and_heal()
            except Exception:
                pass

    def _check_and_heal(self):
        now = time.time()
        proxies_map = self.client.get_proxies()
        if not proxies_map:
            return

        # 1. 抓取被监控策略组当前正在使用的物理节点
        group_current_nodes: Dict[str, str] = {}
        for grp in self.monitored_groups:
            g_data = proxies_map.get(grp, {})
            c_node = g_data.get("now", "")
            if c_node:
                group_current_nodes[grp] = c_node

        self.current_active_node = group_current_nodes.get("⚡ 自动选择", "未知出口")
        self.current_active_nohk_node = group_current_nodes.get("⚡ 自动选择 (非香港)", "未知非港出口")

        # 2. 读取当前活跃连接快照
        conns_data = self.client.get_connections(timeout=1.8)
        if not conns_data or not isinstance(conns_data, dict):
            return

        connections = conns_data.get("connections", [])
        if not connections:
            self.current_status_summary = f"空闲就绪 (全量: {self.current_active_node} | 非港: {self.current_active_nohk_node})"
            self._notify_status()
            return

        # 3. 分析单向发包黑洞与软失速假死，按 (所属策略组, 物理节点) 聚类统计
        # blackhole_hosts: {(group_name, node_name): set(host1, host2, ...)}
        blackhole_hosts: Dict[Tuple[str, str], Set[str]] = {}
        blackhole_conn_ids: Dict[Tuple[str, str], List[str]] = {}
        blackhole_stall_types: Dict[Tuple[str, str], Set[str]] = {}

        for conn in connections:
            chains = conn.get("chains", [])
            if not chains:
                continue

            node_name = chains[0]
            metadata = conn.get("metadata", {})
            host = metadata.get("host") or metadata.get("destinationIP") or ""
            if not self._is_external_host(host):
                continue

            upload = conn.get("upload", 0)
            download = conn.get("download", 0)
            start_ts = self._parse_start_time(conn.get("start", ""))
            duration = now - start_ts

            # 物理硬断流检测 (单向发包黑洞)：持续多秒有上传无下载 (upload > 0, download == 0)
            # 只有当且仅当向外发出了请求 (如 TCP SYN / HTTP Request)，但在超时窗口内没有任何数据返回，才是真实物理断流
            # 凡是 download > 0 的连接，说明握手和下行响应均已成功，绝大部分为空闲长连接 (Keep-Alive)，严禁误判为断流！
            is_hard_stall = (duration >= self.blackhole_timeout and upload > 0 and download == 0)

            if is_hard_stall:
                # 定位该连接属于哪个受监控的策略组 (血统溯源)
                matched_grp = None
                for grp in self.monitored_groups:
                    if grp in chains:
                        matched_grp = grp
                        break

                # 若链条中无直接显式名称，则根据该节点当前被哪个组选用推断
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
                root_domain = self._get_root_domain(host)
                blackhole_hosts[pair_key].add(root_domain or host)
                blackhole_conn_ids[pair_key].append(conn.get("id"))
                blackhole_stall_types[pair_key].add("硬断流")

        # 4. 逐一巡检受监控策略组中的在用节点是否集体暴毙或严重抽风 (同时预先刷新内存热备就绪池)
        self._refresh_standby_cache(proxies_map)
        healed_any = False
        for grp, curr_n in group_current_nodes.items():
            pair_key = (grp, curr_n)
            if pair_key in blackhole_hosts:
                distinct_hosts = blackhole_hosts[pair_key]
                if len(distinct_hosts) >= self.min_blackhole_hosts:
                    stall_types = blackhole_stall_types.get(pair_key, set())
                    stall_desc = "/".join(sorted(list(stall_types))) if stall_types else "断流"
                    hosts_preview = ", ".join(sorted(list(distinct_hosts))[:3])
                    is_non_hk = ("非香港" in grp)

                    # 触发嫌疑，发射质量哨兵微探针 (对齐客户端 1200ms HTTP 探针)
                    probe_delay = self.client.query_proxy_delay(curr_n, self.probe_url, timeout_ms=self.probe_timeout_ms)

                    # 分支 A：探针初次超时 (>= 99999ms) —— 启动防抖复测，避免因瞬时并发高吞吐丢包导致误杀！
                    if probe_delay >= 99999:
                        time.sleep(0.4)
                        retry_delay = self.client.query_proxy_delay(curr_n, self.probe_url, timeout_ms=self.probe_timeout_ms)
                        if retry_delay >= 99999:
                            dead_reason = (
                                f"【{grp}】并发 {len(distinct_hosts)} 个独立主域名{stall_desc}且复测探针连续超时暴毙 "
                                f"(目标: {hosts_preview})"
                            )
                            self.yellow_cards.pop(curr_n, None)
                            self._execute_auto_heal(
                                target_group=grp,
                                dead_node=curr_n,
                                reason=dead_reason,
                                dead_conn_ids=blackhole_conn_ids.get(pair_key, []),
                                is_non_hk=is_non_hk,
                            )
                            healed_any = True
                        else:
                            self.log(f"⚠️ [探针防抖生效] 节点 【{curr_n}】 初次探测超时，但复测成功 ({retry_delay}ms)，避免误杀")
                            probe_delay = retry_delay

                    # 分支 B：探针自身也严重劣化 (>= degrade_rtt_ms 且 < 99999) —— 启动观察缓冲与双黄牌机制
                    # 【核心法则】：若探针极速通畅 (< 280ms，如 37ms)，拥有一票否决权，绝对判定为物理健康，绝不发牌误杀！
                    elif probe_delay >= self.degrade_rtt_ms:
                        last_card_ts = self.yellow_cards.get(curr_n, 0.0)
                        time_since_last_card = now - last_card_ts

                        if self.strike_min_interval <= time_since_last_card <= self.strike_window:
                            # 满足在 [10s, 60s] 观察缓冲期后二次抽风，两黄变一红！强制退位顺移
                            dead_reason = (
                                f"【{grp}】经观察缓冲期后二次抽风/延迟严重劣化 ({probe_delay}ms >= {self.degrade_rtt_ms}ms, {stall_desc}) "
                                f"(目标: {hosts_preview})"
                            )
                            self.yellow_cards.pop(curr_n, None)
                            self.log(f"🚨 [两黄变一红] 节点 【{curr_n}】 经 {int(time_since_last_card)}s 观察期后持续抽风劣化 ({probe_delay}ms)，出示红牌强制退位顺移！")
                            self._execute_auto_heal(
                                target_group=grp,
                                dead_node=curr_n,
                                reason=dead_reason,
                                dead_conn_ids=blackhole_conn_ids.get(pair_key, []),
                                is_non_hk=is_non_hk,
                            )
                            healed_any = True
                        elif time_since_last_card < self.strike_min_interval:
                            # 还在 10 秒观察缓冲期内，保持观察，绝不连出两牌
                            self.current_status_summary = f"🟨 黄牌观察中 ({curr_n} 延迟 {probe_delay}ms)"
                            self._notify_status()
                        else:
                            # 首次抽风 (或距离上次已超过 60s 重置)，出示新黄牌并开始观察期
                            self.yellow_cards[curr_n] = now
                            self.log(f"🟨 [自愈黄牌] 节点 【{curr_n}】 延迟飙升劣化 ({probe_delay}ms >= {self.degrade_rtt_ms}ms, {stall_desc})，出示黄牌进入观察期...")
                            self.current_status_summary = f"🟨 黄牌警告 ({curr_n} 延迟 {probe_delay}ms) | 观察中"
                            self._notify_status()
                    else:
                        # 探针通畅 (< degrade_rtt_ms，如 37ms)，一票否决证明当前节点健康！
                        if curr_n in self.yellow_cards and (now - self.yellow_cards[curr_n]) > self.strike_window:
                            self.yellow_cards.pop(curr_n, None)

        if not healed_any:
            active_count = len(connections)
            yc_count = len([k for k, v in self.yellow_cards.items() if (now - v) <= self.strike_window])
            yc_str = f" | 🟨黄牌节点: {yc_count}" if yc_count > 0 else ""
            self.current_status_summary = (
                f"🟢 双通道畅通 (全量: {self.current_active_node} | 非港: {self.current_active_nohk_node} | 活跃: {active_count}{yc_str})"
            )
            self._notify_status()

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
            # 步骤 3：坏死节点冷冻熔断 15 分钟
            self.cooldown_nodes[dead_node] = now + self.cooldown_duration
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

            # 步骤 4：异步平滑清退 —— 仅定点清理真正坏死的僵尸连接，绝不滥杀活跃的正常数据流！
            def _delayed_drain():
                time.sleep(0.5)
                evicted_count = 0
                for cid in dead_conn_ids:
                    if cid and self.client.close_connection(cid, timeout=0.5):
                        evicted_count += 1
                if evicted_count > 0:
                    self.log(f"🔪 [定点扫尾] 已精准清理旧节点 【{dead_node}】 遗留的 {evicted_count} 条死锁僵尸连接")

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

    def _refresh_standby_cache(self, proxies_map: dict):
        """
        在后台心跳中预先计算并缓存各策略组的顺位热备节点 (Pre-warmed Standby)，
        发生断流瞬间 0 延迟直接取用，无需临时排序与过滤。
        """
        now = time.time()
        for grp in self.monitored_groups:
            is_non_hk = ("非香港" in grp)
            candidates: List[str] = []
            if callable(self.get_candidates_fn):
                try:
                    candidates = self.get_candidates_fn(is_non_hk=is_non_hk) or []
                except TypeError:
                    candidates = self.get_candidates_fn() or []
            if not candidates:
                candidates = list(proxies_map.get(grp, {}).get("all", []))
            if is_non_hk:
                candidates = [c for c in candidates if c and not EXCLUDE_HK_REGEX.search(c)]
            # 过滤掉当前处于 15 分钟熔断期的节点
            ready_cands = [c for c in candidates if c and (c not in self.cooldown_nodes or self.cooldown_nodes[c] <= now)]
            self.standby_cache[grp] = ready_cands

    def _pick_backup_node(
        self,
        target_group: str,
        exclude_node: str,
        is_non_hk: bool = False,
    ) -> Optional[str]:
        # 1. 优先直接从内存热备队列中瞬时取出首个非死节点 (0 毫秒开销)
        cached = self.standby_cache.get(target_group, [])
        for cand in cached:
            if cand and cand != exclude_node:
                return cand

        # 2. 若热备缓存恰好为空，回退执行全量提取
        candidates: List[str] = []
        if callable(self.get_candidates_fn):
            try:
                candidates = self.get_candidates_fn(is_non_hk=is_non_hk) or []
            except TypeError:
                candidates = self.get_candidates_fn() or []

        if not candidates:
            proxies_map = self.client.get_proxies()
            candidates = list(proxies_map.get(target_group, {}).get("all", []))

        if is_non_hk:
            candidates = [c for c in candidates if c and not EXCLUDE_HK_REGEX.search(c)]

        now = time.time()
        for cand in candidates:
            if not cand or cand == exclude_node:
                continue
            if cand in self.cooldown_nodes and self.cooldown_nodes[cand] > now:
                continue
            return cand

        # 若都在冷却期，选择任一不同的健康候选兜底
        for cand in candidates:
            if cand and cand != exclude_node:
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
        proxies_map = self.client.get_proxies()
        auto_now = proxies_map.get("⚡ 自动选择", {}).get("now", "")
        nohk_now = proxies_map.get("⚡ 自动选择 (非香港)", {}).get("now", "")

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
