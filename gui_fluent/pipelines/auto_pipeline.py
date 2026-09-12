"""
全自动优选流水线工作线程 (AutoPipelineWorker)
基于 QThread 运行，完全解耦 UI 渲染，1:1 接入真实测速、Colo校准、漂移过滤与 Script.js 生成逻辑
"""
import json
import ssl
import sys
import time
import threading
import traceback
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import QThread, pyqtSignal
else:
    from PyQt6.QtCore import QThread, pyqtSignal

from services.subscription_service import get_node_endpoint, choose_canonical_node_name
from services.colo_service import is_asian_node, analyze_colo_stats, record_colo_sample
from services.probe_service import get_cf_colo_raw
from services.clash_client import ClashClient, ClashModeGuard, find_cf_donor_node, fission_clean_ips
from services.script_generator import build_script_js, write_script_js
from services.pool_service import (
    purge_invalid_and_blacklisted_from_all_pools,
    get_pool_endpoint_sets,
    deduplicate_favorites_by_endpoint,
    process_verified_lifecycle,
)
from services.filter_service import (
    compute_delay_stats,
    check_node_jitter_blacklisted,
    auto_filter_and_blacklist_non_asia_nodes,
)
from utils.win32_utils import trigger_verge_reactivate_hotkey


def _record_delay_sample(node_delay_history, key_or_name, delay, ep=None, now_ts=None):
    """
    记录时延样本至 7 天时序桶中
    """
    if not delay or delay >= 99999 or delay <= 0:
        return
    if now_ts is None:
        now_ts = time.time()
    keys_to_update = {key_or_name}
    if ep and ep != "127.0.0.1:443":
        keys_to_update.add(ep)
    cutoff = now_ts - 7 * 86400
    for k in keys_to_update:
        if not k:
            continue
        hist = node_delay_history.setdefault(k, [])
        hist.append({"ts": now_ts, "d": int(delay)})
        node_delay_history[k] = [
            x for x in hist if isinstance(x, dict) and x.get("ts", 0) >= cutoff
        ][-30:]


class AutoPipelineWorker(QThread):
    """
    全自动优选后台工作线程：
    提取当前订阅待测节点，执行多轮并发测延、Colo时序探测、防漂移审查、下行带宽实测与策略组热重载
    """

    status_signal = pyqtSignal(str)           # 进度状态更新 (如 "延迟初筛: 第1/4轮 (10/50)")
    log_signal = pyqtSignal(str)              # 日志文本输出
    rows_updated = pyqtSignal(list)           # 表格行实时全量刷新
    finished_signal = pyqtSignal(bool, str)   # (是否成功, 结果描述)

    def __init__(self, controller, config: dict, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.config = dict(config)
        self.thread = self

    def log(self, msg: str):
        """发射日志信号的统一快捷方法"""
        self.log_signal.emit(msg)

    def stop(self):
        # 将原有的 self.thread.terminate() 精准替换为以下平滑退出机制：
        if self.thread and self.thread.isRunning():
            self.thread.requestInterruption()
            self.thread.quit()
            if not self.thread.wait(2000):
                self.thread.terminate()
                self.thread.wait()

    def run(self):
        self.log_signal.emit("🚀 启动一整套全自动大优选流程 (Fluent 后台线程)...")
        try:
            # 0. 解析配置参数（严格依据 UI 面板设置决定初筛轮数与超时，严禁硬编码与截断）
            max_delay = int(self.config.get("max_delay", 100)) if str(self.config.get("max_delay", "")).isdigit() else 100
            try:
                min_speed = float(self.config.get("min_speed", 5.0))
            except Exception:
                min_speed = 5.0

            # 严格恢复按 UI 设置的轮数与超时（不再硬编码 rounds=2 与 500ms 超时）
            rounds = max(1, int(self.config.get("test_rounds", 4))) if str(self.config.get("test_rounds", "")).isdigit() else 4
            timeout_ms = max(200, int(self.config.get("test_timeout", 1500))) if str(self.config.get("test_timeout", "")).isdigit() else 1500
            try:
                duration = max(0.5, float(self.config.get("speed_duration", 3.0)))
            except Exception:
                duration = 3.0

            bl_delay_threshold = int(self.config.get("blacklist_threshold", 130)) if str(self.config.get("blacklist_threshold", "")).isdigit() else 130
            try:
                speed_bl_threshold = float(self.config.get("speed_bl_threshold", 1.0))
            except Exception:
                speed_bl_threshold = 1.0
            speed_bl_rounds = max(1, int(self.config.get("speed_bl_rounds", 4))) if str(self.config.get("speed_bl_rounds", "")).isdigit() else 4
            jitter_min_d = int(self.config.get("jitter_min_delay", 80)) if str(self.config.get("jitter_min_delay", "")).isdigit() else 80
            jitter_up_th = int(self.config.get("jitter_up_threshold", 20)) if str(self.config.get("jitter_up_threshold", "")).isdigit() else 20

            test_url = str(self.config.get("test_url", "")).strip() or "http://www.msftconnecttest.com/connecttest.txt"
            speed_url = str(self.config.get("speed_url", "")).strip() or "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip"

            target_cnt_str = str(self.config.get("target_count", "")).strip()
            target_node_limit = int(target_cnt_str) if (target_cnt_str.isdigit() and int(target_cnt_str) > 0) else 0

            group_interval = str(self.config.get("group_interval", "300")).strip()
            group_tolerance = str(self.config.get("group_tolerance", "20")).strip()
            star_group_interval = str(self.config.get("star_group_interval", "300")).strip()
            star_group_tolerance = str(self.config.get("star_group_tolerance", "20")).strip()

            # 校验并同步内核凭据
            clash_port_cfg = self.config.get("clash_port", "")
            clash_secret_cfg = self.config.get("clash_secret", "")
            if clash_port_cfg or clash_secret_cfg:
                self.controller.clash_client.update_credentials(
                    port=clash_port_cfg if str(clash_port_cfg).isdigit() else None,
                    secret=clash_secret_cfg if clash_secret_cfg is not None else None,
                )

            is_conn, ver_info = self.controller.clash_client.test_connection()
            if not is_conn:
                auto_p, auto_s = ClashClient.auto_detect_credentials()
                if auto_p:
                    self.controller.clash_client.update_credentials(port=auto_p, secret=auto_s)
                    is_conn, ver_info = self.controller.clash_client.test_connection()

            if not is_conn:
                self.log_signal.emit("❌ 无法连接 Clash 内核，请检查端口与密钥设置！")
                self.finished_signal.emit(False, "无法连接 Clash 内核！")
                return

            # 前置准备 1：强制更新远程订阅
            self.log_signal.emit("🔄 [前置准备] 正在强制更新远程订阅...")
            ok_sub, msg_sub = self.controller.update_remote_subscription_sync()
            self.log_signal.emit(f"🔄 [前置准备] 远程订阅更新结果: {msg_sub}")

            # 前置准备 2：拉取云端 auto.txt 专属节点名称与 pending.txt 待测清单
            self.log_signal.emit("☁️ [前置准备] 正在拉取云端 auto.txt 与 pending.txt 待测清单...")
            cloud_endpoints = self.controller.fetch_cloud_endpoints_sync()
            pending_endpoints = self.controller.fetch_pending_endpoints_sync()
            self.log_signal.emit(f"☁️ [前置准备] 云端同步完毕：精选端点 {len(cloud_endpoints)} 个，待测端点 {len(pending_endpoints)} 个")

            # 前置准备 3：重载本地内存与界面数据 (按云端专属名称霸占并严格绝对去重)
            self.log_signal.emit("📦 [前置准备] 正在重载本地内存与界面数据...")
            active_sub = getattr(self.controller.state, "active_profile", "") or self.config.get("profile_yaml", "") or "Rw0nNFlVIbnA.yaml"
            self.controller.load_nodes_from_profile(active_sub, cloud_endpoints=cloud_endpoints)
            # 触发一次强刷新，让 UI 的“活跃待测”立刻显示新抓取的节点
            self.controller.data_changed.emit()

            # 前置准备 4：热更激活 Clash 核心加载新节点
            self.log_signal.emit("⚡ [前置准备] 正在热更激活 Clash 核心加载新节点...")
            self.controller.generate_script_and_reload()

            # 延长休眠时间，确保 Clash 核心完全解析数百个节点并开放 RESTful API
            self.log_signal.emit("⏳ 等待内核重载完毕 (5秒)...")
            time.sleep(5)

            def _get_ep(n):
                return get_node_endpoint(
                    n,
                    node_details=self.controller.state.node_details,
                    all_nodes=self.controller.state.all_nodes,
                    verified_nodes=self.controller.state.verified_nodes,
                    clash_client=self.controller.clash_client,
                )

            # 1. 节点排查、去重与分组
            with self.controller.state.lock:
                auto_filter_and_blacklist_non_asia_nodes(
                    self.controller.state.all_nodes,
                    self.controller.state.local_blacklist,
                    self.controller.state.favorites,
                    self.controller.state.blacklist_reasons,
                    _get_ep,
                    is_asian_node,
                    node_colo_dict=self.controller.state.node_colo,
                )

                fav_eps, bl_eps, sbl_eps, star_eps = get_pool_endpoint_sets(
                    self.controller.state.favorites,
                    self.controller.state.local_blacklist,
                    self.controller.state.speed_blacklist,
                    self.controller.state.auto_endpoints,
                    self.controller.state.verified_nodes,
                    self.controller.state.stars_nodes,
                    _get_ep,
                )

                ep_to_untested = {}
                fav_sk = 0
                d_sk = 0
                s_sk = 0
                ver_sk = 0

                for n in self.controller.state.all_nodes:
                    ep = _get_ep(n)
                    c_val = self.controller.state.node_colo.get(n, self.controller.state.node_colo.get(ep, "-"))
                    if not is_asian_node(n, colo=c_val):
                        if n not in self.controller.state.local_blacklist:
                            self.controller.state.local_blacklist.add(n)
                            self.controller.state.blacklist_reasons[n] = "非亚洲节点 (自动过滤)"
                        continue

                    if n in self.controller.state.local_blacklist or (ep and ep in self.controller.state.local_blacklist):
                        d_sk += 1
                        continue
                    if n in self.controller.state.speed_blacklist or (ep and ep in self.controller.state.speed_blacklist):
                        s_sk += 1
                        continue

                    # 核心去重：命中精选池审查
                    if n in self.controller.state.favorites or (ep and ep in fav_eps):
                        _should_purge = False
                        _purge_reason = ""
                        if not is_asian_node(n, colo=c_val):
                            _should_purge = True
                            _purge_reason = "非亚洲地区/命名"
                        else:
                            colo_hist = self.controller.state.node_colo_history.get(n, self.controller.state.node_colo_history.get(ep, []))
                            if colo_hist:
                                _dom, _, _has_drift, _drift_disp = analyze_colo_stats(colo_hist, time.time(), node_name=n)
                                if _has_drift or not is_asian_node(n, colo=_dom):
                                    _should_purge = True
                                    _purge_reason = f"机房漂移 ({_drift_disp})"
                        if _should_purge:
                            self.controller.state.local_blacklist.add(n)
                            self.controller.state.favorites.discard(n)
                            self.controller.state.blacklist_reasons[n] = _purge_reason
                            if ep:
                                self.controller.state.local_blacklist.add(ep)
                                self.controller.state.blacklist_reasons[ep] = _purge_reason
                                fav_eps.discard(ep)
                                for f in list(self.controller.state.favorites):
                                    if _get_ep(f) == ep:
                                        self.controller.state.favorites.discard(f)
                            if ep and ep in self.controller.state.verified_nodes:
                                del self.controller.state.verified_nodes[ep]
                            self.log_signal.emit(f"【精选审查淘汰】节点 {n} 命中规则：{_purge_reason}，已从精选清除并加入黑名单！")
                            continue

                        fav_sk += 1
                        continue

                    if (n in self.controller.state.verified_nodes) or (ep and ep in star_eps):
                        ver_sk += 1
                        continue

                    ep_to_untested.setdefault(ep, []).append(n)

            # 融合云端 pending.txt 待测端点（严格物理端点 1:1 去重，绝不重复测速）
            for p_ep, p_rem in pending_endpoints.items():
                if p_ep not in ep_to_untested and p_ep not in fav_eps and p_ep not in bl_eps and p_ep not in sbl_eps:
                    ep_to_untested.setdefault(p_ep, []).append(p_ep)

            unique_eps = list(ep_to_untested.keys())
            test_targets = [choose_canonical_node_name(ep_to_untested[ep]) for ep in unique_eps if ep]

            self.log_signal.emit(
                f"全量节点: {len(self.controller.state.all_nodes)} 个 | 严格限制亚洲节点 | "
                f"跳过精选: {fav_sk} | 跳过延迟黑名单: {d_sk} | 跳过低速黑名单: {s_sk} | "
                f"待测独立节点: {len(test_targets)} 个 (同源马甲已自动聚合)"
            )

            if not test_targets:
                self.status_signal.emit("无须测速")
                self.finished_signal.emit(True, "所有节点均位于精选、黑名单或沉淀池中，无新的待测节点！")
                return

            # 初始化待测表格行
            ep_to_row = {}
            test_rows = []
            with self.controller.state.lock:
                for ep in unique_eps:
                    rep_name = choose_canonical_node_name(ep_to_untested[ep])
                    c_hist = self.controller.state.node_colo_history.get(rep_name, self.controller.state.node_colo_history.get(ep, []))
                    c_disp = "-"
                    if c_hist:
                        _, _, _, c_disp = analyze_colo_stats(c_hist, time.time(), node_name=rep_name)

                    row = {
                        "status": "排队中...",
                        "colo": self.controller.state.node_colo.get(rep_name, self.controller.state.node_colo.get(ep, "-")),
                        "colo_hist": c_disp,
                        "reason": "-",
                        "delay": "-",
                        "avg_delay": "-",
                        "delay_hist": "-",
                        "hist_avg": "-",
                        "speed": "-",
                        "speed_hist": "-",
                        "name": rep_name,
                        "endpoint": ep,
                    }
                    ep_to_row[ep] = row
                    test_rows.append(row)

            self.rows_updated.emit([dict(r) for r in test_rows])
            self.status_signal.emit(f"待测节点: {len(test_rows)} 个")

            # 2. 多轮真实代理延迟初筛 (严格按设置参数 rounds 与 timeout_ms 执行真实链路测试)
            self.log_signal.emit(
                f"⚡ 开始执行 {rounds} 轮真实代理延迟初筛 (独立端点共 {len(unique_eps)} 个，单次超时上限: {timeout_ms}ms)..."
            )

            # 建立物理端点 -> 内核代理节点映射表，确保 100% 真实代理应用层测速
            core_proxies = self.controller.clash_client.get_proxies()
            ep_to_core_node = {}
            for p_name, p_info in core_proxies.items():
                if isinstance(p_info, dict):
                    s = p_info.get("server", "").strip()
                    p = str(p_info.get("port", "443")).strip()
                    if s:
                        ep_to_core_node[f"{s}:{p}"] = p_name

            all_known_nodes = set(self.controller.state.all_nodes)

            for r in range(1, rounds + 1):
                if self.isInterruptionRequested():
                    break

                total_eps = len(unique_eps)
                done_cnt = 0
                alive_cnt = 0
                done_lock = threading.Lock()
                last_log_t = 0.0
                last_status_t = 0.0

                def _single_delay(endpoint):
                    if self.isInterruptionRequested():
                        return
                    rep_node = choose_canonical_node_name(ep_to_untested[endpoint])
                    target_proxy_name = None
                    if rep_node in core_proxies:
                        target_proxy_name = rep_node
                    elif rep_node in all_known_nodes and rep_node in core_proxies:
                        target_proxy_name = rep_node
                    elif endpoint in ep_to_core_node:
                        target_proxy_name = ep_to_core_node[endpoint]

                    if target_proxy_name:
                        # 100% 真实代理链路测速：调用内核 RESTful API 发起真实 HTTP/HTTPS 延迟探测
                        cur_delay = self.controller.clash_client.query_proxy_delay(target_proxy_name, test_url, timeout_ms=timeout_ms)
                    else:
                        # 纯正测速原则：严禁使用 TCP ping 降级伪造代理延迟！内核未挂载的端点直接判定超时
                        cur_delay = 99999

                    with self.controller.state.lock:
                        if cur_delay < 99999:
                            _record_delay_sample(self.controller.state.node_delay_history, endpoint, cur_delay)
                        for n in ep_to_untested[endpoint]:
                            self.controller.state.node_delays[n] = cur_delay
                            hist = self.controller.state.node_history.setdefault(n, [])
                            hist.append(cur_delay)
                            self.controller.state.node_history[n] = hist[-rounds:]
                            if cur_delay < 99999:
                                _record_delay_sample(self.controller.state.node_delay_history, n, cur_delay)

                    row_ref = ep_to_row.get(endpoint)
                    if row_ref:
                        row_ref["delay"] = f"{cur_delay}ms" if cur_delay < 99999 else "超时"
                        h_vals = self.controller.state.node_history.get(rep_node, [])
                        row_ref["delay_hist"] = "/".join(str(v) if v < 99999 else "超时" for v in h_vals)
                        valid_vals = [v for v in h_vals if v < 99999]
                        if valid_vals:
                            row_ref["avg_delay"] = f"{int(sum(valid_vals)/len(valid_vals))} ms"

                    nonlocal done_cnt, alive_cnt, last_log_t, last_status_t
                    with done_lock:
                        done_cnt += 1
                        if cur_delay < 99999:
                            alive_cnt += 1
                        now_t = time.time()
                        # 每 50 个节点步长，或经过 1 秒，或最后一批时输出透明平滑进度
                        step_cond = (done_cnt % 50 == 0) or (now_t - last_log_t >= 1.0) or (done_cnt == total_eps)
                        if step_cond:
                            last_log_t = now_t
                            pct = int(done_cnt * 100 / total_eps)
                            cur_d_str = f"{cur_delay}ms" if cur_delay < 99999 else "超时"
                            self.log(
                                f"⚡ [初筛第 {r}/{rounds} 轮] 进度: {done_cnt}/{total_eps} ({pct}%) | "
                                f"实时存活: {alive_cnt} 个 | 最新端点: {endpoint} ({cur_d_str})"
                            )
                        if (now_t - last_status_t >= 0.5) or done_cnt == total_eps:
                            last_status_t = now_t
                            self.status_signal.emit(f"延迟初筛中: 第 {r}/{rounds} 轮 ({done_cnt}/{total_eps}) 存活:{alive_cnt}")

                with ThreadPoolExecutor(max_workers=min(20, len(unique_eps))) as executor:
                    list(executor.map(_single_delay, unique_eps))

                self.rows_updated.emit([dict(x) for x in test_rows])
                if self.isInterruptionRequested():
                    break
                time.sleep(0.5)

            if self.isInterruptionRequested():
                self.log("⏹ 用户已终止流水线任务")
                self.finished_signal.emit(False, "任务已被用户手动终止")
                return

            # 3. 达标排查与淘汰审计 (全部轮次完整跑完后，结合最佳延迟门槛、黑名单门槛与抖动机制综合审计)
            candidates = []
            newly_delay_blacklisted = 0
            for n in test_targets:
                if self.isInterruptionRequested():
                    break
                ep = _get_ep(n)
                hist = self.controller.state.node_history.get(n, [])
                best_delay = min(hist[-rounds:]) if hist else 99999

                # 延迟未达到设定要求 (> max_delay) 或超时 (>= 99999) 或超标 (>= bl_delay_threshold) 淘汰拉黑
                if best_delay > max_delay or best_delay >= bl_delay_threshold or best_delay >= 99999:
                    if best_delay >= 99999:
                        d_reason = "延迟超时 (≥99999ms)"
                    elif best_delay >= bl_delay_threshold:
                        d_reason = f"延迟超标 ({best_delay}ms ≥ {bl_delay_threshold}ms)"
                    else:
                        d_reason = f"延迟淘汰 ({best_delay}ms > {max_delay}ms)"

                    now_bl_t = time.time()
                    with self.controller.state.lock:
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = d_reason
                        self.controller.state.blacklist_timestamps[n] = now_bl_t
                        if ep:
                            self.controller.state.local_blacklist.add(ep)
                            self.controller.state.blacklist_reasons[ep] = d_reason
                            self.controller.state.blacklist_timestamps[ep] = now_bl_t
                        for same_n in ep_to_untested.get(ep, []):
                            self.controller.state.local_blacklist.add(same_n)
                            self.controller.state.favorites.discard(same_n)
                            self.controller.state.blacklist_reasons[same_n] = d_reason
                            self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]

                    if ep in ep_to_row:
                        ep_to_row[ep]["status"] = "延迟淘汰"
                        ep_to_row[ep]["reason"] = d_reason

                    newly_delay_blacklisted += 1
                    continue

                # 节点抖动拉黑机制：最低延迟≥设定值且向上抖动≥设定值，立即拉黑淘汰（最高延迟<设定最低延迟则豁免）
                is_j_bad, j_min, j_up = check_node_jitter_blacklisted(
                    hist[-rounds:], jitter_min_d, jitter_up_th
                )
                if is_j_bad:
                    j_reason = f"延迟抖动淘汰 (底{j_min}ms 抖动+{j_up}ms)"
                    now_bl_t = time.time()
                    with self.controller.state.lock:
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = j_reason
                        self.controller.state.blacklist_timestamps[n] = now_bl_t
                        if ep:
                            self.controller.state.local_blacklist.add(ep)
                            self.controller.state.blacklist_reasons[ep] = j_reason
                            self.controller.state.blacklist_timestamps[ep] = now_bl_t
                        for same_n in ep_to_untested.get(ep, []):
                            self.controller.state.local_blacklist.add(same_n)
                            self.controller.state.favorites.discard(same_n)
                            self.controller.state.blacklist_reasons[same_n] = j_reason
                            self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]

                    if ep in ep_to_row:
                        ep_to_row[ep]["status"] = "抖动淘汰"
                        ep_to_row[ep]["reason"] = j_reason

                    newly_delay_blacklisted += 1
                    self.log(f"【抖动淘汰】节点 {n} 最低延迟 {j_min}ms (≥{jitter_min_d}ms)，向上抖动 +{j_up}ms (≥{jitter_up_th}ms)，拉黑淘汰！")
                    continue

                cur_avg, hist_avg = compute_delay_stats(
                    n,
                    ep=ep,
                    node_history=self.controller.state.node_history,
                    node_delays=self.controller.state.node_delays,
                    node_delay_history=self.controller.state.node_delay_history,
                    get_node_endpoint_fn=_get_ep,
                )
                if ep in ep_to_row:
                    ep_to_row[ep]["status"] = "初筛达标"
                    ep_to_row[ep]["reason"] = f"延迟达标 ({best_delay}ms ≤ {max_delay}ms)"
                    ep_to_row[ep]["avg_delay"] = cur_avg
                    ep_to_row[ep]["hist_avg"] = hist_avg

                candidates.append(n)

            self.log(
                f"🏁 [延迟初筛完毕] 共 {len(candidates)} 个候选节点达标 (≤{max_delay}ms，淘汰超标/抖动: {newly_delay_blacklisted} 个)，立即转入真实 Colo 测定与测速..."
            )

            # 仅保留通过延迟考核合格的端点行，单次通知 UI 表格装配
            surviving_eps = { _get_ep(c) for c in candidates if _get_ep(c) }
            test_rows = [r for r in test_rows if r.get("endpoint") in surviving_eps]
            ep_to_row = { r["endpoint"]: r for r in test_rows if "endpoint" in r }
            self.rows_updated.emit([dict(x) for x in test_rows])
            self.status_signal.emit(f"初筛完毕: 合格 {len(candidates)} 个")

            if not candidates:
                self.status_signal.emit("无达标节点")
                self.finished_signal.emit(True, f"延迟初筛结束：所有待测节点延迟均未达到 ≤{max_delay}ms。")
                return

            # 3. 真实 Colo 测定与防漂移审计 (Step 3/4)
            candidates.sort(key=lambda n: min(self.controller.state.node_history.get(n, [99999])))
            self.log_signal.emit(f"正在对 {len(candidates)} 个候选节点校准真实 Colo 并录入 7 天时序桶...")
            self.status_signal.emit(f"Colo 校准: {len(candidates)} 个节点")

            def _probe_colo(n):
                if self.isInterruptionRequested():
                    return
                ep = _get_ep(n)
                if ":" in ep:
                    if ep.startswith("[") and "]:" in ep:
                        ip, port_str = ep[1:].split("]:", 1)
                    elif ep.count(":") > 1:
                        ip, port_str = ep.rsplit(":", 1)
                    else:
                        ip, port_str = ep.split(":", 1)
                    try:
                        port = int(port_str)
                    except (ValueError, TypeError):
                        port = 443
                    try:
                        c_code, c_disp = get_cf_colo_raw(ip, port, timeout=1.5)
                    except Exception:
                        c_code, c_disp = "UNKNOWN", "未知机房"
                    with self.controller.state.lock:
                        record_colo_sample(
                            self.controller.state.node_colo_history,
                            n,
                            ep,
                            c_code,
                            c_disp,
                            now=time.time(),
                            node_colo_dict=self.controller.state.node_colo,
                        )
                    if ep in ep_to_row:
                        ep_to_row[ep]["colo"] = c_disp
                        c_hist = self.controller.state.node_colo_history.get(n, self.controller.state.node_colo_history.get(ep, []))
                        if c_hist:
                            _, _, _, disp_str = analyze_colo_stats(c_hist, time.time(), node_name=n)
                            ep_to_row[ep]["colo_hist"] = disp_str

            with ThreadPoolExecutor(max_workers=min(16, len(candidates))) as ex:
                list(ex.map(_probe_colo, candidates))

            self.rows_updated.emit([dict(x) for x in test_rows])

            # 机房漂移排查
            drift_passed_candidates = []
            now_pipe_t = time.time()
            for n in candidates:
                if self.isInterruptionRequested():
                    break
                ep = _get_ep(n)
                colo_hist = self.controller.state.node_colo_history.get(n, self.controller.state.node_colo_history.get(ep, []))
                _, _, has_drift, drift_disp = analyze_colo_stats(colo_hist, now_pipe_t, node_name=n)
                if has_drift:
                    drift_reason = f"机房漂移 ({drift_disp})"
                    now_bl_t = time.time()
                    with self.controller.state.lock:
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = drift_reason
                        self.controller.state.blacklist_timestamps[n] = now_bl_t
                        if ep:
                            self.controller.state.local_blacklist.add(ep)
                            self.controller.state.blacklist_reasons[ep] = drift_reason
                            self.controller.state.blacklist_timestamps[ep] = now_bl_t
                        for same_n in ep_to_untested.get(ep, []):
                            self.controller.state.local_blacklist.add(same_n)
                            self.controller.state.favorites.discard(same_n)
                            self.controller.state.blacklist_reasons[same_n] = drift_reason
                            self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]

                    if ep in ep_to_row:
                        ep_to_row[ep]["status"] = "漂移淘汰"
                        ep_to_row[ep]["reason"] = drift_reason
                    self.log_signal.emit(f"【漂移直接淘汰】节点 {n} 发生机房漂移 ({drift_disp})，直接拉黑并清除！")
                else:
                    drift_passed_candidates.append(n)

            candidates = [n for n in drift_passed_candidates if is_asian_node(n, colo=self.controller.state.node_colo.get(n, self.controller.state.node_colo.get(_get_ep(n))))]
            surviving_eps = { _get_ep(c) for c in candidates if _get_ep(c) }
            test_rows = [r for r in test_rows if r.get("endpoint") in surviving_eps]
            ep_to_row = { r["endpoint"]: r for r in test_rows if "endpoint" in r }
            self.rows_updated.emit([dict(x) for x in test_rows])
            self.controller.data_changed.emit()

            if not candidates:
                self.status_signal.emit("候选节点已漂移淘汰")
                self.finished_signal.emit(True, "候选节点均发生机房漂移或非亚洲已被全部淘汰。")
                return

            # 4. 协议嫁接与真实下行带宽测速 (Step 4/4)
            all_known_nodes = set(self.controller.state.all_nodes)
            clean_endpoints_to_graft = []
            for n in candidates:
                ep = _get_ep(n)
                if n not in all_known_nodes and ep:
                    clean_endpoints_to_graft.append(ep)

            clean_endpoints_to_graft = list(dict.fromkeys(clean_endpoints_to_graft))
            graft_map = {}
            has_fission = False

            if clean_endpoints_to_graft:
                active_sub = getattr(self.controller.state, "active_profile", "") or self.config.get("profile_yaml", "") or "Rw0nNFlVIbnA.yaml"
                donor = find_cf_donor_node(active_profile=active_sub, verified_nodes=self.controller.state.verified_nodes)
                if donor:
                    self.log_signal.emit(f"🧬 [协议嫁接] 成功锁定 Cloudflare 协议母体 [{donor.get('name', 'CF-Donor')} / {donor.get('type')}]，为 {len(clean_endpoints_to_graft)} 个纯净端点实施换头裂变...")
                    fission_proxies = fission_clean_ips(donor, clean_endpoints_to_graft)
                    for p in fission_proxies:
                        graft_map[f"{p['server']}:{p['port']}"] = p["name"]

                    self.log_signal.emit("⚡ [协议嫁接] 正在将裂变代理注入 Script.js 并触发内核热加载...")
                    self.controller.reload_verge_with_fission(fission_proxies)
                    has_fission = True
                    self.log_signal.emit("⏳ 等待裂变节点热加载就绪 (3秒)...")
                    time.sleep(3.0)
                else:
                    self.log_signal.emit("⚠️ [协议嫁接] 未在订阅中寻获具备有效 TLS/SNI 凭证的 Cloudflare 协议母体，跳过协议裂变，保留探活结果。")

            proxies_data = self.controller.clash_client.get_proxies() or {}
            proxies_map = proxies_data if isinstance(proxies_data, dict) else {}
            global_info = proxies_map.get("GLOBAL", {})
            orig_global = global_info.get("now", "")
            global_all = global_info.get("all", [])

            mixed_port = self.controller.clash_client.get_mixed_port(default=7897)

            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
            speed_opener = urllib.request.build_opener(proxy_handler, https_handler)

            total_cand = len(candidates)
            orig_group_selections = {}
            premium_nodes = []
            tested_endpoint_speeds = {}
            hit_target_early = False
            newly_speed_blacklisted = 0

            self.log_signal.emit(f"启动带宽精测 (共 {total_cand} 个候选节点，下行门槛 ≥{min_speed} MB/s)...")

            try:
                with ClashModeGuard(self.controller.clash_client, temporary_mode="global"):
                    for idx, node_name in enumerate(candidates, 1):
                        if self.isInterruptionRequested():
                            break

                        ep = _get_ep(node_name)
                        clash_node_name = graft_map.get(ep, node_name)
                        row_ref = ep_to_row.get(ep)
                        target_str = f" [已集齐: {len(premium_nodes)}/{target_node_limit}]" if target_node_limit > 0 else f" [已入选 {len(premium_nodes)} 个]"
                        self.status_signal.emit(f"带宽精测: [{idx}/{total_cand}]{target_str} {node_name[:16]}...")

                        if row_ref:
                            row_ref["status"] = f"带宽测速中 [{idx}/{total_cand}]"
                            self.rows_updated.emit([dict(r) for r in test_rows])
                        self.log(f"🌐 [真实带宽测速 {idx}/{total_cand}] 正在测试节点真实下行: {node_name} (采样 {duration}s)...")

                        if ep in tested_endpoint_speeds:
                            speed_val = tested_endpoint_speeds[ep]
                        else:
                            target_group = None
                            if "🚀 节点选择" in proxies_map and clash_node_name in proxies_map["🚀 节点选择"].get("all", []):
                                target_group = "🚀 节点选择"
                            elif clash_node_name in global_all:
                                target_group = "GLOBAL"
                            else:
                                for g_name, g_info in proxies_map.items():
                                    if isinstance(g_info, dict) and g_info.get("type", "").lower() == "selector" and g_name != "GLOBAL":
                                        if clash_node_name in g_info.get("all", []):
                                            target_group = g_name
                                            break

                            if not target_group:
                                speed_val = -1.0
                            else:
                                if target_group not in orig_group_selections:
                                    orig_group_selections[target_group] = proxies_map.get(target_group, {}).get("now", "")

                                enc_tg = urllib.parse.quote(target_group, safe="")
                                self.controller.clash_client.call_api(f"/proxies/{enc_tg}", method="PUT", data={"name": clash_node_name})

                                if target_group != "GLOBAL" and target_group in global_all:
                                    enc_glb = urllib.parse.quote("GLOBAL", safe="")
                                    self.controller.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": target_group})

                                time.sleep(0.1)

                                speed_val = -1.0
                                total_bytes = 0
                                speed_timeout = max(1.5, min(3.5, round(duration + 0.5, 1)))
                                node_deadline = time.time() + duration + 1.0
                                try:
                                    req = urllib.request.Request(
                                        speed_url,
                                        headers={
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                            "Connection": "close",
                                        },
                                    )
                                    with speed_opener.open(req, timeout=speed_timeout) as resp:
                                        start_time = time.time()
                                        chunk_size = 16 * 1024
                                        while time.time() - start_time < duration:
                                            if time.time() >= node_deadline or self.isInterruptionRequested():
                                                break
                                            chunk = resp.read(chunk_size)
                                            if not chunk:
                                                break
                                            total_bytes += len(chunk)

                                        elapsed = time.time() - start_time
                                        if elapsed > 0 and total_bytes > 0:
                                            speed_val = round((total_bytes / (1024 * 1024)) / elapsed, 2)
                                        else:
                                            speed_val = 0.0
                                except Exception:
                                    speed_val = -1.0

                                tested_endpoint_speeds[ep] = speed_val

                        with self.controller.state.lock:
                            self.controller.state.node_speeds[node_name] = speed_val
                            if ep:
                                self.controller.state.node_speeds[ep] = speed_val
                            s_hist = self.controller.state.node_speed_history.setdefault(node_name, [])
                            s_hist.append(max(0.0, speed_val))
                            self.controller.state.node_speed_history[node_name] = s_hist[-4:]
                            if ep and ep != node_name:
                                s_hist_ep = self.controller.state.node_speed_history.setdefault(ep, [])
                                s_hist_ep.append(max(0.0, speed_val))
                                self.controller.state.node_speed_history[ep] = s_hist_ep[-4:]

                        if row_ref:
                            row_ref["speed"] = f"{speed_val:.2f} MB/s" if speed_val >= 0 else "失败"
                            s_vals = self.controller.state.node_speed_history.get(node_name, [])
                            row_ref["speed_hist"] = "/".join(f"{s:.1f}" for s in s_vals)

                        colo = self.controller.state.node_colo.get(node_name, self.controller.state.node_colo.get(ep, "JP"))
                        if not colo or colo == "-":
                            colo = "亚洲"

                        if speed_val >= min_speed and is_asian_node(node_name, colo=colo):
                            coronated_name = f"{colo} {speed_val:.2f} MB/s"
                            fav_target_name = coronated_name if coronated_name else node_name
                            premium_nodes.append(fav_target_name)
                            with self.controller.state.lock:
                                self.controller.state.favorites.add(fav_target_name)
                                if node_name != fav_target_name:
                                    self.controller.state.favorites.discard(node_name)
                                    self.controller._migrate_node_name(node_name, fav_target_name, ep)
                                d_val = self.controller.state.node_delays.get(fav_target_name, self.controller.state.node_delays.get(node_name, 0))
                                self.controller.state.fav_reasons[fav_target_name] = f"真实测速达标 ({speed_val:.2f}MB/s)"
                                if ep:
                                    self.controller.state.cloud_endpoints[ep] = coronated_name
                                    if ":" in ep:
                                        self.controller.state.cloud_endpoints[ep.split(":")[0]] = coronated_name

                            if row_ref:
                                row_ref["name"] = coronated_name
                                row_ref["status"] = "优质精选"
                                row_ref["reason"] = f"下行 {speed_val:.2f} MB/s ≥ {min_speed} MB/s"

                            self.log_signal.emit(f"⭐ [优质入选] 节点入选精选: {coronated_name} ({ep}) (实测下行: {speed_val:.2f} MB/s ≥ {min_speed} MB/s)")
                            test_rows = [r for r in test_rows if r.get("endpoint") != ep and r.get("name") not in (node_name, fav_target_name)]
                            self.rows_updated.emit([dict(r) for r in test_rows])
                            self.controller.data_changed.emit()

                            if target_node_limit > 0 and len(premium_nodes) >= target_node_limit:
                                hit_target_early = True
                                self.log_signal.emit(f"🎯 已集齐目标节点数 ({target_node_limit} 个)，提前结束测速！")
                                break
                        else:
                            spd_reason = "下行测速中断/失败" if speed_val < 0 else f"下行未达标 ({speed_val:.2f} < {min_speed} MB/s)"
                            now_bl_t = time.time()
                            with self.controller.state.lock:
                                self.controller.state.speed_blacklist.add(node_name)
                                self.controller.state.favorites.discard(node_name)
                                self.controller.state.blacklist_reasons[node_name] = spd_reason
                                self.controller.state.blacklist_timestamps[node_name] = now_bl_t
                                if ep:
                                    self.controller.state.speed_blacklist.add(ep)
                                    self.controller.state.blacklist_reasons[ep] = spd_reason
                                    self.controller.state.blacklist_timestamps[ep] = now_bl_t
                                for same_n in ep_to_untested.get(ep, []):
                                    self.controller.state.speed_blacklist.add(same_n)
                                    self.controller.state.favorites.discard(same_n)
                                    self.controller.state.blacklist_reasons[same_n] = spd_reason
                                    self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                                if ep in self.controller.state.verified_nodes:
                                    del self.controller.state.verified_nodes[ep]

                            if row_ref:
                                row_ref["status"] = "低速淘汰"
                                row_ref["reason"] = spd_reason

                            newly_speed_blacklisted += 1
                            self.log_signal.emit(f"【低速淘汰】节点 {node_name} 实测下行 {speed_val:.2f} MB/s 未达标 (门槛 ≥{min_speed} MB/s)")
                            test_rows = [r for r in test_rows if r.get("endpoint") != ep and r.get("name") != node_name]
                            self.rows_updated.emit([dict(r) for r in test_rows])
                            self.controller.data_changed.emit()

            finally:
                # 恢复原策略组选择与全局选择
                for g_name, orig_choice in orig_group_selections.items():
                    if orig_choice:
                        enc = urllib.parse.quote(g_name, safe="")
                        self.controller.clash_client.call_api(f"/proxies/{enc}", method="PUT", data={"name": orig_choice})

                if orig_global:
                    enc_glb = urllib.parse.quote("GLOBAL", safe="")
                    self.controller.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": orig_global})

                # 任务收尾物理自愈：若注入了裂变节点，无条件恢复纯净 Script.js 并热重载，彻底抹除临时裂变代理
                if has_fission:
                    self.log_signal.emit("🧹 [物理自愈] 正在清除临时裂变代理，恢复纯净策略组配置...")
                    self.controller.reload_verge_with_fission(None)

            if self.isInterruptionRequested():
                self.log_signal.emit("⏹ 用户已终止流水线任务")
                self.finished_signal.emit(False, "任务已被用户手动终止")
                return

            # 5. 收尾：多池聚合、生成 Script.js 并触发热重载
            self.status_signal.emit("写入 Script.js 并热更...")
            self.log_signal.emit("正在同步更新多池状态、写入 Script.js 策略组配置...")

            with self.controller.state.lock:
                self.controller.state.favorites.update(premium_nodes)
                deduplicate_favorites_by_endpoint(
                    self.controller.state.favorites,
                    self.controller.state.all_nodes,
                    self.controller.state.node_details,
                    _get_ep,
                    choose_canonical_node_name,
                )
                # 剥离越权入孵：全量大优选仅负责将达标节点纳入 favorites，绝对禁止自动塞入 verified_nodes 沉淀孵化池！
                # process_verified_lifecycle(
                #     self.controller.state.verified_nodes,
                #     list(self.controller.state.favorites),
                #     self.controller.state.stars_nodes,
                # )
                purge_invalid_and_blacklisted_from_all_pools(
                    self.controller.state.favorites,
                    self.controller.state.verified_nodes,
                    self.controller.state.stars_nodes,
                    self.controller.state.local_blacklist,
                    self.controller.state.speed_blacklist,
                    _get_ep,
                )

            # 固化配置
            self.controller.save_config(self.controller.get_state_snapshot())

            # 生成并写入 Script.js
            script_code, p_tokens, s_tokens = build_script_js(
                favorites=self.controller.state.favorites,
                stars_nodes=self.controller.state.stars_nodes,
                all_nodes=self.controller.state.all_nodes,
                node_details=self.controller.state.node_details,
                group_interval=group_interval,
                group_tolerance=group_tolerance,
                star_group_interval=star_group_interval,
                star_group_tolerance=star_group_tolerance,
                is_asian_node_fn=is_asian_node,
                get_node_endpoint_fn=_get_ep,
                cloud_endpoints=self.controller.state.cloud_endpoints,
                node_colo=self.controller.state.node_colo,
            )
            write_ok, write_res = write_script_js(script_code)
            if write_ok:
                self.log_signal.emit(f"✅ Script.js 策略组写入成功，生效优选节点 {len(p_tokens)} 个，典藏节点 {len(s_tokens)} 个")
            else:
                self.log_signal.emit(f"⚠️ Script.js 写入失败: {write_res}")

            # 触发系统级热键通知 Clash Verge 重新激活
            time.sleep(0.5)
            hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()
            if hotkey_ok:
                self.log_signal.emit(f"⚡ 热键通知成功: {hotkey_msg}")
            else:
                self.log_signal.emit(f"⚠️ 热键触发反馈: {hotkey_msg}")

            # 避开内核刚重载时的代理端口震荡期（静置 2 秒），确保代理隧道建立
            self.log_signal.emit("⏳ 等待内核网络通道平稳就绪 (2秒)...")
            time.sleep(2.0)

            # 在专属后台自愈通道中平稳执行精选池推云与待测池全量联动清洗（配备 curl 双引擎保底）
            self.controller.trigger_cloud_sync_and_purge_safely()

            summary_msg = f"全量大优选结束：新增入选 {len(premium_nodes)} 个优质极速节点，Script.js 规则已写入并触发热重载生效！"
            self.status_signal.emit("优选流程执行完成")
            self.log_signal.emit(f"🎯 {summary_msg}")
            self.finished_signal.emit(True, summary_msg)

        except Exception as e:
            err_tb = traceback.format_exc()
            self.log_signal.emit(f"流水线执行异常:\n{err_tb}")
            self.status_signal.emit("执行异常")
            self.finished_signal.emit(False, f"执行异常: {str(e)}")
