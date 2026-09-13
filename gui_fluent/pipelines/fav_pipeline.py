"""
优质精选池复测流水线工作线程 (FavPipelineWorker)
基于 QThread 运行，完全解耦 UI 渲染，1:1 平移 gui/app.py 中 start_fav_review_pipeline 核心业务逻辑
"""
import json
import ssl
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import QThread, pyqtSignal
else:
    from PyQt6.QtCore import QThread, pyqtSignal

from services.subscription_service import get_node_endpoint, choose_canonical_node_name
from services.colo_service import is_asian_node, is_node_hongkong, analyze_colo_stats, record_colo_sample
from services.probe_service import get_cf_colo_raw
from services.clash_client import ClashClient, ClashModeGuard
from services.script_generator import build_script_js, write_script_js
from services.pool_service import (
    purge_invalid_and_blacklisted_from_all_pools,
    process_verified_lifecycle,
)
from services.filter_service import (
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


class FavPipelineWorker(QThread):
    """
    优质精选池复检工作线程：
    对当前精选池候选节点执行端点去重、多轮延迟复测、实时机房(Colo)探测、严格机房防漂移审查、
    以及双轨分流(香港/非香港)下行带宽实测与达标早停。
    """

    log_signal = pyqtSignal(str)              # 过程日志
    status_signal = pyqtSignal(str)           # 简短状态词
    rows_updated = pyqtSignal(list)           # 返回当前待测/测试中的 dict 列表
    finished_signal = pyqtSignal(bool, str)   # (是否成功, 结果描述)
    fallback_needed = pyqtSignal(str)         # 触发大优选自愈信号 (原因)

    def __init__(self, controller, config: dict, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.config = dict(config)
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True
        self.requestInterruption()

    def run(self):
        self.log_signal.emit("⚡ 启动优质精选池复检流程 (Fluent 后台线程)...")
        try:
            # 0. 解析配置参数
            f_max_d = int(self.config.get("fav_max_delay", 80)) if str(self.config.get("fav_max_delay", "")).isdigit() else 80
            try:
                f_min_s = float(self.config.get("fav_min_speed", 8.0))
            except Exception:
                f_min_s = 8.0
            f_rounds = max(1, int(self.config.get("fav_rounds", 2))) if str(self.config.get("fav_rounds", "")).isdigit() else 2
            try:
                f_duration = max(0.5, float(self.config.get("fav_speed_duration", 2.0)))
            except Exception:
                f_duration = 2.0
            f_jitter_min_d = int(self.config.get("fav_jitter_min_delay", 70)) if str(self.config.get("fav_jitter_min_delay", "")).isdigit() else 70
            f_jitter_up_th = int(self.config.get("fav_jitter_up_threshold", 15)) if str(self.config.get("fav_jitter_up_threshold", "")).isdigit() else 15

            target_hk = int(self.config.get("fav_target_hk_count", 3)) if str(self.config.get("fav_target_hk_count", "")).isdigit() else 3
            target_nohk = int(self.config.get("fav_target_nohk_count", 5)) if str(self.config.get("fav_target_nohk_count", "")).isdigit() else 5
            early_stop_enabled = bool(self.config.get("fav_quota_early_stop", True))
            fallback_enabled = bool(self.config.get("fav_fallback_enabled", True))

            cfg_global = self.controller.load_config() if hasattr(self.controller, "load_config") else {}
            test_url = str(self.config.get("test_url") or cfg_global.get("test_url") or "https://www.google.com/generate_204").strip()
            speed_url = str(self.config.get("speed_url") or cfg_global.get("speed_url") or "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip").strip()
            # 严格拦截阻断已被 Cloudflare 边缘防火墙掐断 TLS 握手的失效测速源，全面切换为全球极速稳定之 Google CDN 测速源
            if not speed_url or "speed.cloudflare.com" in speed_url:
                speed_url = "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip"
            timeout_ms = int(self.config.get("test_timeout", 1500)) if str(self.config.get("test_timeout", "")).isdigit() else 1500

            group_interval = str(self.config.get("group_interval", "300")).strip() or "300"
            group_tolerance = str(self.config.get("group_tolerance", "20")).strip() or "20"
            star_group_interval = str(self.config.get("star_group_interval", "300")).strip() or "300"
            star_group_tolerance = str(self.config.get("star_group_tolerance", "20")).strip() or "20"

            # 1. 前置准备：拉取远程订阅与云端文本，并热更内核
            self.log_signal.emit("🔄 [前置准备] 正在强制更新远程订阅与云端文本...")
            self.controller.update_remote_subscription_sync()
            self.controller.fetch_cloud_endpoints_sync()

            active_sub = self.controller.state.active_profile or "Rw0nNFlVIbnA.yaml"
            self.controller.load_nodes_from_profile(active_sub)
            self.controller.generate_script_and_reload()
            time.sleep(3)  # 给予内核重载缓冲

            def _get_ep(node_name):
                return get_node_endpoint(node_name, node_details=self.controller.state.node_details)

            # 建立当前订阅中 IP:Port -> 订阅中可用代理节点名的逆向映射表
            current_ep_to_proxy = {}
            for node in self.controller.state.all_nodes:
                ep = _get_ep(node)
                if ep and ep not in current_ep_to_proxy:
                    current_ep_to_proxy[ep] = node

            # 穿透提取待复测的真实代理节点
            active_fav_targets = []
            seen_targets = set()
            fav_origin_map = {}

            with self.controller.state.lock:
                # 优先执行非亚洲节点过滤
                auto_filter_and_blacklist_non_asia_nodes(
                    all_nodes=list(self.controller.state.favorites),
                    local_blacklist=self.controller.state.local_blacklist,
                    favorites=self.controller.state.favorites,
                    blacklist_reasons=self.controller.state.blacklist_reasons,
                    get_node_endpoint_fn=_get_ep,
                    is_asian_node_fn=is_asian_node,
                    node_colo_dict=self.controller.state.node_colo,
                )

                for f in list(self.controller.state.favorites):
                    target_ep = _get_ep(f) or str(f)
                    # 如果能在当前订阅中找到该物理端点对应的实体节点
                    matched_proxy = current_ep_to_proxy.get(target_ep)
                    if matched_proxy:
                        c_val = self.controller.state.node_colo.get(matched_proxy, self.controller.state.node_colo.get(target_ep, "-"))
                        if matched_proxy not in seen_targets and is_asian_node(matched_proxy, colo=c_val):
                            active_fav_targets.append(matched_proxy)
                            seen_targets.add(matched_proxy)
                            fav_origin_map[matched_proxy] = f
                    elif f in self.controller.state.all_nodes:
                        c_val = self.controller.state.node_colo.get(f, self.controller.state.node_colo.get(target_ep, "-"))
                        if is_asian_node(f, colo=c_val):
                            if f not in seen_targets:
                                active_fav_targets.append(f)
                                seen_targets.add(f)
                                fav_origin_map[f] = f

            tot = len(active_fav_targets)
            self.log_signal.emit(f"优质池待复测节点共 {tot} 个 (已穿透对齐 C 段端点 | 达标即停={early_stop_enabled})")

            if not active_fav_targets:
                self.log_signal.emit("优质精选池中暂无可用的存活节点。")
                if fallback_enabled:
                    self.log_signal.emit("⚡ 优质池无存活节点，触发自愈大优选...")
                    self.fallback_needed.emit("优质池中无存活节点")
                    self.finished_signal.emit(False, "优质池无存活节点，已触发自愈大优选")
                else:
                    self.finished_signal.emit(False, "优质精选池中暂无可用的存活节点")
                return

            # 2. 内核连通性校验
            conn_ok, conn_ver = self.controller.get_clash_connection_status()
            if not conn_ok:
                self.log_signal.emit("❌ 无法连接 Clash 内核！")
                self.status_signal.emit("内核未连接")
                self.finished_signal.emit(False, "无法连接 Clash 内核")
                return

            # 3. 初始化待测节点延迟状态
            with self.controller.state.lock:
                for n in active_fav_targets:
                    self.controller.state.node_delays[n] = None
                    self.controller.state.node_history[n] = []

            self.controller.data_changed.emit()

            self.status_signal.emit(f"[优质复测] 检测 {tot} 个优质候选延迟...")

            # 4. 多轮并发延迟测试 (端点去重)
            for r in range(1, f_rounds + 1):
                if self._stop_requested or self.isInterruptionRequested():
                    self.log_signal.emit("优质池复测已被手动终止。")
                    self.status_signal.emit("已终止")
                    self.finished_signal.emit(False, "用户手动终止任务")
                    return

                ep_to_nodes = {}
                for n in active_fav_targets:
                    ep = _get_ep(n)
                    ep_to_nodes.setdefault(ep, []).append(n)

                def _fav_delay(endpoint):
                    if self._stop_requested or self.isInterruptionRequested():
                        return
                    rep_node = ep_to_nodes[endpoint][0]
                    cur_d = self.controller.clash_client.query_proxy_delay(rep_node, test_url, timeout_ms=timeout_ms)
                    with self.controller.state.lock:
                        if cur_d < 99999:
                            _record_delay_sample(self.controller.state.node_delay_history, endpoint, cur_d)
                        for n in ep_to_nodes[endpoint]:
                            self.controller.state.node_delays[n] = cur_d
                            hist = self.controller.state.node_history.setdefault(n, [])
                            hist.append(cur_d)
                            self.controller.state.node_history[n] = hist[-f_rounds:]
                            if cur_d < 99999:
                                _record_delay_sample(self.controller.state.node_delay_history, n, cur_d)

                with ThreadPoolExecutor(max_workers=8) as ex:
                    list(ex.map(_fav_delay, list(ep_to_nodes.keys())))

                self.controller.data_changed.emit()
                if self._stop_requested or self.isInterruptionRequested():
                    self.log_signal.emit("优质池复测已被手动终止。")
                    self.status_signal.emit("已终止")
                    self.finished_signal.emit(False, "用户手动终止任务")
                    return
                time.sleep(0.5)

            # 5. 达标初筛：延迟门槛与抖动淘汰
            temp_passed = []
            with self.controller.state.lock:
                for n in active_fav_targets:
                    hist = self.controller.state.node_history.get(n, [99999])
                    best_d = min(hist[-f_rounds:]) if hist else 99999
                    if best_d > f_max_d or best_d >= 99999:
                        d_reason = "延迟超时 (≥99999ms)" if best_d >= 99999 else f"复测延迟淘汰 ({best_d}ms > {f_max_d}ms)"
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = d_reason
                        ep = _get_ep(n)
                        if ep:
                            self.controller.state.blacklist_reasons[ep] = d_reason
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]
                        self.log_signal.emit(f"【优质淘汰-延迟超标】节点 {n} 延迟 {best_d}ms 未达门槛(≤{f_max_d}ms)，直接拉黑淘汰！")
                        continue

                    is_j_bad, j_min, j_up = check_node_jitter_blacklisted(
                        hist[-f_rounds:], f_jitter_min_d, f_jitter_up_th
                    )
                    if is_j_bad:
                        j_reason = f"复测抖动淘汰 (底{j_min}ms 抖动+{j_up}ms)"
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = j_reason
                        ep = _get_ep(n)
                        if ep:
                            self.controller.state.blacklist_reasons[ep] = j_reason
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]
                        self.log_signal.emit(f"【优质淘汰-抖动超标】节点 {n} 最低延迟 {j_min}ms (≥{f_jitter_min_d}ms)，向上抖动 +{j_up}ms (≥{f_jitter_up_th}ms)，直接拉黑淘汰！")
                        continue

                    temp_passed.append(n)

            if self._stop_requested or self.isInterruptionRequested():
                self.status_signal.emit("已终止")
                self.finished_signal.emit(False, "用户手动终止任务")
                return

            # 6. 实时机房 (Colo) 物理探测与采样
            self.status_signal.emit(f"[优质复测] 正在核验 {len(temp_passed)} 个候选的物理机房(Colo)...")

            def _probe_fav_colo(n):
                ep = _get_ep(n)
                if ":" in ep:
                    raw_ip, raw_port = ep.rsplit(":", 1)
                    c_code, c_disp = get_cf_colo_raw(raw_ip, raw_port, timeout=1.5)
                    with self.controller.state.lock:
                        record_colo_sample(self.controller.state.node_colo_history, n, ep, c_code, c_disp)
                        self.controller.state.node_colo[n] = c_disp
                        if ep:
                            self.controller.state.node_colo[ep] = c_disp

            with ThreadPoolExecutor(max_workers=10) as ex:
                list(ex.map(_probe_fav_colo, temp_passed))

            self.controller.data_changed.emit()

            # 7. 严格机房漂移审查：发生机房漂移一次即直接拉黑淘汰
            drift_passed = []
            now_fav_t = time.time()
            with self.controller.state.lock:
                for n in temp_passed:
                    ep = _get_ep(n)
                    colo_hist = self.controller.state.node_colo_history.get(n, self.controller.state.node_colo_history.get(ep, []))
                    _, _, has_drift, drift_disp = analyze_colo_stats(colo_hist, now_fav_t, node_name=n)
                    if has_drift:
                        drift_reason = f"机房漂移 ({drift_disp})"
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = drift_reason
                        if ep:
                            self.controller.state.blacklist_reasons[ep] = drift_reason
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]
                        self.log_signal.emit(f"【优质淘汰-机房漂移】节点 {n} 发生机房漂移 ({drift_disp})，直接拉黑淘汰！")
                    else:
                        drift_passed.append(n)
            temp_passed = drift_passed

            # 8. 分流香港候选与非香港候选
            hk_candidates = []
            nohk_candidates = []
            with self.controller.state.lock:
                for n in temp_passed:
                    c_val = self.controller.state.node_colo.get(n, self.controller.state.node_colo.get(_get_ep(n), "-"))
                    if not is_asian_node(n, colo=c_val):
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = "非亚洲地区/命名"
                        continue
                    if is_node_hongkong(n):
                        hk_candidates.append(n)
                    else:
                        nohk_candidates.append(n)

                hk_candidates.sort(key=lambda n: min(self.controller.state.node_history.get(n, [99999])))
                nohk_candidates.sort(key=lambda n: min(self.controller.state.node_history.get(n, [99999])))

            self.log_signal.emit(f"优质复检初筛通过（经Colo物理核验）：香港候选 {len(hk_candidates)} 个，非香港候选 {len(nohk_candidates)} 个")

            if self._stop_requested or self.isInterruptionRequested():
                self.status_signal.emit("已终止")
                self.finished_signal.emit(False, "用户手动终止任务")
                return

            # 9. 下行真实带宽测速 (ClashModeGuard 保护下切换全局模式)
            proxies_map = self.controller.clash_client.get_proxies()
            global_info = proxies_map.get("GLOBAL", {})
            orig_global = global_info.get("now", "")
            global_all = global_info.get("all", [])

            mixed_port = self.controller.clash_client.get_mixed_port(default=7897)
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            speed_opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({
                    "http": f"http://127.0.0.1:{mixed_port}",
                    "https": f"http://127.0.0.1:{mixed_port}",
                }),
                urllib.request.HTTPSHandler(context=ssl_ctx)
            )

            qualified_hk = []
            qualified_nohk = []
            tested_ep_speeds = {}
            orig_group_selections = {}
            google_hk_detected_nodes = set()

            fav_mode_guard = ClashModeGuard(self.controller.clash_client, temporary_mode="global")
            fav_mode_guard.__enter__()
            try:
                def _test_single_speed(n, track_label, cur_cnt, tgt_cnt):
                    ep = _get_ep(n)
                    if ep in tested_ep_speeds:
                        spd = tested_ep_speeds[ep]
                        with self.controller.state.lock:
                            self.controller.state.node_speeds[n] = spd
                            h = self.controller.state.node_speed_history.setdefault(n, [])
                            h.append(max(0.0, spd))
                            self.controller.state.node_speed_history[n] = h[-4:]
                        return spd

                    tgt_text = f"{tgt_cnt}" if early_stop_enabled else "全测"
                    self.status_signal.emit(f"[优质复测-{track_label}] 目标:{cur_cnt}/{tgt_text} | 测速: {n[:18]}...")

                    target_group = None
                    if "🚀 节点选择" in proxies_map and n in proxies_map["🚀 节点选择"].get("all", []):
                        target_group = "🚀 节点选择"
                    elif n in global_all:
                        target_group = "GLOBAL"
                    else:
                        for g_name, g_info in proxies_map.items():
                            if g_info.get("type", "").lower() == "selector" and g_name != "GLOBAL":
                                if n in g_info.get("all", []):
                                    target_group = g_name
                                    break

                    if not target_group:
                        return 0.0

                    if target_group not in orig_group_selections:
                        orig_group_selections[target_group] = proxies_map.get(target_group, {}).get("now", "")

                    enc_tg = urllib.parse.quote(target_group, safe="")
                    self.controller.clash_client.call_api(
                        f"/proxies/{enc_tg}", method="PUT", data={"name": n}
                    )

                    # 在 global 模式下，直接切换 GLOBAL 策略组指向当前节点，实现 100% 物理直达穿透
                    if n in global_all:
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self.controller.clash_client.call_api(
                            f"/proxies/{enc_glb}", method="PUT", data={"name": n}
                        )
                    elif target_group != "GLOBAL" and target_group in global_all:
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self.controller.clash_client.call_api(
                            f"/proxies/{enc_glb}", method="PUT", data={"name": target_group}
                        )

                    time.sleep(0.15)

                    # 非香港赛道专属：Google 送中与官方拦截洁净度感知探测 (打标分流，不粗暴判 0)
                    if track_label == "非香港":
                        try:
                            g_req = urllib.request.Request(
                                "https://www.google.com",
                                headers={"User-Agent": "Mozilla/5.0"}
                            )
                            with speed_opener.open(g_req, timeout=2.5) as g_resp:
                                final_gurl = g_resp.geturl()
                                if "google.com.hk" in final_gurl or "sorry" in final_gurl:
                                    google_hk_detected_nodes.add(n)
                                    tag_label = "送中重定向" if "google.com.hk" in final_gurl else "官方验证拦截"
                                    self.log_signal.emit(
                                        f"🏷️ [Google合规打标] 节点 {n} 遭{tag_label} ({final_gurl})，将打上 [送中] 标并转入常规优选组！"
                                    )
                        except urllib.error.HTTPError as he:
                            if he.code in (429, 403) or "sorry" in getattr(he, "url", ""):
                                google_hk_detected_nodes.add(n)
                                self.log_signal.emit(
                                    f"🏷️ [Google合规打标] 节点 {n} 遭官方风控拦截 (HTTP {he.code})，将打上 [送中] 标并转入常规优选组！"
                                )
                        except Exception:
                            pass

                    speed_val = 0.0
                    total_bytes = 0
                    # 消除 2.5s 硬编码截断 Bug，给予网络握手与下载充足裕量
                    fav_speed_timeout = max(5.0, round(f_duration + 3.0, 1))
                    fav_node_deadline = time.time() + f_duration + 3.0
                    try:
                        req = urllib.request.Request(
                            speed_url,
                            headers={"User-Agent": "Mozilla/5.0", "Connection": "close"}
                        )
                        with speed_opener.open(req, timeout=fav_speed_timeout) as resp:
                            st = time.time()
                            chunk_size = 64 * 1024
                            while time.time() - st < f_duration:
                                if time.time() >= fav_node_deadline or self._stop_requested or self.isInterruptionRequested():
                                    break
                                ch = resp.read(chunk_size)
                                if not ch:
                                    break
                                total_bytes += len(ch)
                            el = time.time() - st
                            speed_val = round((total_bytes / (1024 * 1024)) / el, 2) if (el > 0 and total_bytes > 0) else 0.0
                    except Exception as e:
                        self.log_signal.emit(f"⚠️ 节点 {n[:18]} 测速网络异常 ({type(e).__name__}: {e})")
                        speed_val = -1.0

                    tested_ep_speeds[ep] = speed_val
                    with self.controller.state.lock:
                        self.controller.state.node_speeds[n] = speed_val
                        h = self.controller.state.node_speed_history.setdefault(n, [])
                        h.append(max(0.0, speed_val))
                        self.controller.state.node_speed_history[n] = h[-4:]

                    return speed_val

                # 测试香港队列
                for n in hk_candidates:
                    if self._stop_requested or self.isInterruptionRequested():
                        break
                    if early_stop_enabled and target_hk > 0 and len(qualified_hk) >= target_hk:
                        self.log_signal.emit(f"优质复测-香港队列已达目标 ({len(qualified_hk)}/{target_hk})，早停")
                        break
                    spd = _test_single_speed(n, "香港", len(qualified_hk), target_hk)
                    if spd >= f_min_s:
                        qualified_hk.append(n)
                        cur_d = self.controller.state.node_delays.get(n, 0)
                        self.controller.state.fav_reasons[n] = f"复测考核留任 ({cur_d}ms / {spd:.2f}MB/s)"
                        with self.controller.state.lock:
                            orig_f = fav_origin_map.get(n, n)
                            if orig_f != n:
                                self.controller._migrate_node_name(orig_f, n, _get_ep(n))
                            self.controller.state.favorites.add(n)
                        self.controller.data_changed.emit()
                    else:
                        spd_reason = "下行测速中断/失败" if spd < 0 else f"复测下行淘汰 ({spd:.2f} < {f_min_s} MB/s)"
                        with self.controller.state.lock:
                            orig_f = fav_origin_map.get(n, n)
                            self.controller.state.speed_blacklist.add(n)
                            self.controller.state.favorites.discard(n)
                            if orig_f != n:
                                self.controller.state.speed_blacklist.add(orig_f)
                                self.controller.state.favorites.discard(orig_f)
                                self.controller.state.blacklist_reasons[orig_f] = spd_reason
                            self.controller.state.blacklist_reasons[n] = spd_reason
                            ep = _get_ep(n)
                            if ep:
                                self.controller.state.blacklist_reasons[ep] = spd_reason
                            if ep in self.controller.state.verified_nodes:
                                del self.controller.state.verified_nodes[ep]
                        self.log_signal.emit(f"【优质淘汰-低速淘汰】香港节点 {n} 下行 {spd:.2f} MB/s 未达标(≥{f_min_s} MB/s)，直接拉黑淘汰！")

                # 测试非香港队列
                for n in nohk_candidates:
                    if self._stop_requested or self.isInterruptionRequested():
                        break
                    if early_stop_enabled and target_nohk > 0 and len(qualified_nohk) >= target_nohk:
                        self.log_signal.emit(f"优质复测-非香港队列已达目标 ({len(qualified_nohk)}/{target_nohk})，早停")
                        break
                    spd = _test_single_speed(n, "非香港", len(qualified_nohk), target_nohk)
                    if spd >= f_min_s:
                        cur_d = self.controller.state.node_delays.get(n, 0)
                        if n in google_hk_detected_nodes:
                            # 打上 [送中] 标签并更名
                            if "[送中]" not in n:
                                m = re.search(r"([\d.]+\s*MB/s)", n)
                                target_name = f"{n[:m.start()]}[送中] {n[m.start():]}" if m else f"{n} [送中]"
                            else:
                                target_name = n

                            with self.controller.state.lock:
                                orig_f = fav_origin_map.get(n, n)
                                if orig_f != target_name:
                                    self.controller._migrate_node_name(orig_f, target_name, _get_ep(n))
                                self.controller.state.favorites.add(target_name)
                                self.controller.state.fav_reasons[target_name] = f"Google送中打标留任常规组 ({cur_d}ms / {spd:.2f}MB/s)"
                                self.controller.state.node_speeds[target_name] = spd
                                self.controller.state.node_delays[target_name] = cur_d
                            self.controller.data_changed.emit()
                            self.log_signal.emit(f"✅ 节点 【{target_name}】 达标留任！由于带有 [送中] 标记，将自动服务于【常规自动组】，不占用非港名额。")
                            # 注意：不加入 qualified_nohk，让非香港队列继续测试其他纯净节点，直到凑齐 target_nohk
                        else:
                            # 纯净非香港节点，正常进入非香港配额
                            qualified_nohk.append(n)
                            self.controller.state.fav_reasons[n] = f"复测考核留任 ({cur_d}ms / {spd:.2f}MB/s)"
                            with self.controller.state.lock:
                                orig_f = fav_origin_map.get(n, n)
                                if orig_f != n:
                                    self.controller._migrate_node_name(orig_f, n, _get_ep(n))
                                self.controller.state.favorites.add(n)
                            self.controller.data_changed.emit()
                    else:
                        spd_reason = "下行测速中断/失败" if spd < 0 else f"复测下行淘汰 ({spd:.2f} < {f_min_s} MB/s)"
                        with self.controller.state.lock:
                            orig_f = fav_origin_map.get(n, n)
                            self.controller.state.speed_blacklist.add(n)
                            self.controller.state.favorites.discard(n)
                            if orig_f != n:
                                self.controller.state.speed_blacklist.add(orig_f)
                                self.controller.state.favorites.discard(orig_f)
                                self.controller.state.blacklist_reasons[orig_f] = spd_reason
                            self.controller.state.blacklist_reasons[n] = spd_reason
                            ep = _get_ep(n)
                            if ep:
                                self.controller.state.blacklist_reasons[ep] = spd_reason
                            if ep in self.controller.state.verified_nodes:
                                del self.controller.state.verified_nodes[ep]
                        self.log_signal.emit(f"【优质淘汰-低速淘汰】非香港节点 {n} 下行 {spd:.2f} MB/s 未达标(≥{f_min_s} MB/s)，直接拉黑淘汰！")

            finally:
                # 恢复原策略组选择
                for g_name, orig_choice in orig_group_selections.items():
                    if orig_choice:
                        enc = urllib.parse.quote(g_name, safe="")
                        self.controller.clash_client.call_api(f"/proxies/{enc}", method="PUT", data={"name": orig_choice})

                if orig_global:
                    enc_glb = urllib.parse.quote("GLOBAL", safe="")
                    self.controller.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": orig_global})

                fav_mode_guard.__exit__(None, None, None)

            if self._stop_requested or self.isInterruptionRequested():
                self.status_signal.emit("已终止")
                self.finished_signal.emit(False, "用户手动终止任务")
                return

            total_final_selected = qualified_hk + qualified_nohk

            # 10. 沉淀池与生命周期维护
            # 仅对本次复测达标存活的节点建档/累加考核
            qualified_endpoints = []
            with self.controller.state.lock:
                for node in total_final_selected:
                    ep = _get_ep(node) or str(node)
                    if ep and ep != "127.0.0.1:443":
                        qualified_endpoints.append(ep)

                process_verified_lifecycle(
                    self.controller.state.verified_nodes,
                    qualified_endpoints,
                    self.controller.state.stars_nodes,
                )
                purge_invalid_and_blacklisted_from_all_pools(
                    self.controller.state.favorites,
                    self.controller.state.verified_nodes,
                    self.controller.state.stars_nodes,
                    self.controller.state.local_blacklist,
                    self.controller.state.speed_blacklist,
                    _get_ep,
                )

            # 持久化
            self.controller.save_config(self.controller.get_state_snapshot())
            self.controller.data_changed.emit()

            self.log_signal.emit(f"优质复检统计：香港达标 {len(qualified_hk)}/{target_hk}，非香港达标 {len(qualified_nohk)}/{target_nohk} (已同步沉淀池)")

            hk_lack = (target_hk > 0 and len(qualified_hk) < target_hk)
            nohk_lack = (target_nohk > 0 and len(qualified_nohk) < target_nohk)

            # 11. 自愈大优选降级判断
            if fallback_enabled and (hk_lack or nohk_lack):
                reasons = []
                if hk_lack:
                    reasons.append(f"香港达标({len(qualified_hk)}/{target_hk})")
                if nohk_lack:
                    reasons.append(f"非香港达标({len(qualified_nohk)}/{target_nohk})")
                reason_str = "、".join(reasons)

                if len(total_final_selected) > 0:
                    script_code, p_toks, s_toks = build_script_js(
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
                    write_script_js(script_code)
                    trigger_verge_reactivate_hotkey()

                # 精选复测结束后自动推送到云端 /verified.txt
                self.controller.push_verified_to_cloud()
                self.log_signal.emit(f"⚡ 检测到配额不足且已开启唤醒开关，触发自愈大优选：{reason_str}")
                self.fallback_needed.emit(f"优质复测不足：{reason_str}")
                self.finished_signal.emit(True, f"优质复测配额不足 ({reason_str})，已触发自愈大优选")
                return

            # 正常写入 Script.js 并触发热键生效
            script_code, p_toks, s_toks = build_script_js(
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
                self.log_signal.emit(f"✅ Script.js 策略组写入成功 (留任优选: {len(p_toks)} 个，典藏: {len(s_toks)} 个)")
                hk_ok, hk_msg = trigger_verge_reactivate_hotkey()
                if hk_ok:
                    self.log_signal.emit(f"⚡ 热键通知成功: {hk_msg}")
            else:
                self.log_signal.emit(f"⚠️ Script.js 写入失败: {write_res}")

            # 精选复测结束后自动推送到云端 /verified.txt
            self.controller.push_verified_to_cloud()

            summary_msg = f"优质池复测完成：留任优质节点 {len(total_final_selected)} 个 (香港 {len(qualified_hk)}，非香港 {len(qualified_nohk)})"
            self.status_signal.emit("优质复测执行完成")
            self.log_signal.emit(f"🎯 {summary_msg}")
            self.finished_signal.emit(True, summary_msg)

        except Exception as e:
            err_tb = traceback.format_exc()
            self.log_signal.emit(f"优质池复测异常:\n{err_tb}")
            self.status_signal.emit("执行异常")
            self.finished_signal.emit(False, f"执行异常: {str(e)}")
