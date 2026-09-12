from concurrent.futures import ThreadPoolExecutor
import ctypes
import glob
import gzip
import hashlib
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import traceback
import urllib.error
import urllib.parse
import urllib.request
import winreg
import winsound

try:
    from PIL import Image, ImageDraw
    import pystray
    TRAY_SUPPORTED = True
except ImportError:
    TRAY_SUPPORTED = False

from config.settings import (
    BASE_DIR,
    PARENT_DIR,
    DEFAULT_SCRIPT_JS,
    CONFIG_STORAGE_PATH,
    RUN_REG_KEY,
    REG_APP_NAME,
    THEME,
    EXCLUDE_HK_REGEX,
    NON_ASIA_CN_KEYWORDS,
    NON_ASIA_CODE_SET,
    ASIA_CN_KEYWORDS,
    ASIA_CODE_SET,
    COLO_NAME_MAP,
    COLO_REGIONS,
    COUNTRY_NAME_MAP,
)
from config.config_manager import (
    atomic_save_config,
    safe_load_config,
    prune_expired_history,
)

from services.probe_service import (
    get_ip_location_fallback,
    get_cf_colo_raw,
    tcp_ping,
    get_c_segment_ips,
    detect_node_region,
    measure_http_download_speed,
)
from services.clash_client import ClashClient, ClashModeGuard
from core.state_manager import StateManager
from services.colo_service import (
    get_colo_region,
    record_colo_sample,
    analyze_colo_stats,
    is_node_hongkong,
    is_asian_node,
)
from services.filter_service import (
    compute_delay_stats,
    check_node_jitter_blacklisted,
    auto_filter_and_blacklist_non_asia_nodes,
)
from services.pool_service import (
    get_pool_endpoint_sets,
    deduplicate_favorites_by_endpoint,
    align_favorites_with_current_subscription,
    clean_offline_favorites,
    process_verified_lifecycle,
    purge_invalid_and_blacklisted_from_all_pools,
)
from services.script_generator import build_script_js, write_script_js
from pipelines.scheduler import SchedulerDaemon
from pipelines.base_pipeline import BasePipeline
from services.subscription_service import (
    extract_nodes_and_details_from_file,
    choose_canonical_node_name,
    get_node_endpoint,
    resolve_node_to_current,
    update_remote_subscription,
)

from utils.win32_utils import (
    send_system_notification,
    is_run_as_admin,
    trigger_verge_reactivate_hotkey,
    create_tray_icon_image,
    check_boot_startup_registry,
    set_boot_startup_registry,
    create_modern_btn,
)

class ClashVergeTabsManager:

    def __init__(self, root):
        self.root = root
        self.root.title("Clash Verge 节点管理助手 (7天Colo长效防漂移与C段挖掘版)")
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = min(1480, max(1000, screen_w - 60))
        win_h = min(920, max(680, screen_h - 100))
        self.root.geometry(f"{win_w}x{win_h}")
        self.root.configure(bg=THEME["bg_main"])

        self.all_nodes = []
        self.favorites = set()
        self.local_blacklist = set()
        self.speed_blacklist = set()
        self.blacklist_reasons = {}
        self.fav_reasons = {}

        self.verified_nodes = {}
        self.stars_nodes = []

        self.node_delays = {}
        self.node_speeds = {}
        self.node_colo = {}
        # 核心：滑动7天时序桶结构 {key: [{"ts": 1725..., "colo": "HKG"}, ...]}
        self.node_colo_history = {}
        self.node_history = {}
        self.node_speed_history = {}
        self.node_delay_history = {}
        self.node_details = {}
        self.auto_endpoints = set()
        self.trees = {}
        self._delay_black_dirty = True
        self._speed_black_dirty = True

        self.is_pipeline_running = False
        self.has_shown_tray_tip = False
        self.tray_icon = None

        self.app_start_time = time.time()
        self.last_full_run_timestamp = 0.0
        self.last_fav_run_timestamp = 0.0

        # 控制变量
        self.port_var = tk.StringVar()
        self.secret_var = tk.StringVar()
        self._cached_port = "9097"
        self._cached_secret = ""
        self.search_var = tk.StringVar()

        self.max_delay_threshold_var = tk.StringVar(value="100")
        self.min_speed_threshold_var = tk.StringVar(value="5.0")
        self.target_node_count_var = tk.StringVar(value="")
        self.blacklist_threshold_var = tk.StringVar(value="130")

        self.speed_bl_threshold_var = tk.StringVar(value="1.0")
        self.speed_bl_rounds_var = tk.StringVar(value="4")

        self.jitter_min_delay_var = tk.StringVar(value="80")
        self.jitter_up_threshold_var = tk.StringVar(value="20")

        self.test_rounds_var = tk.StringVar(value="4")
        self.test_timeout_var = tk.StringVar(value="1500")
        self.speed_duration_var = tk.StringVar(value="3")

        self.test_url_var = tk.StringVar(value="http://www.msftconnecttest.com/connecttest.txt")
        self.speed_url_var = tk.StringVar(value="https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip")

        self.schedule_enabled_var = tk.BooleanVar(value=False)
        self.schedule_interval_var = tk.StringVar(value="120")
        self.schedule_times_var = tk.StringVar(value="08:00, 13:00, 20:00")
        self.boot_startup_var = tk.BooleanVar(value=check_boot_startup_registry())

        self.group_interval_var = tk.StringVar(value="300")
        self.group_tolerance_var = tk.StringVar(value="20")
        self.star_group_interval_var = tk.StringVar(value="300")
        self.star_group_tolerance_var = tk.StringVar(value="20")

        self.cf_worker_enabled_var = tk.BooleanVar(value=False)
        self.cf_worker_url_var = tk.StringVar(value="https://cf-nodes.douyutvshow.workers.dev/")
        self.cf_worker_token_var = tk.StringVar(value="MySecretToken2026")
        self._cached_cf_enabled = False
        self._cached_cf_url = "https://cf-nodes.douyutvshow.workers.dev/"
        self._cached_cf_token = "MySecretToken2026"
        self._is_initialized = False

        self.fav_max_delay_var = tk.StringVar(value="80")
        self.fav_min_speed_var = tk.StringVar(value="8.0")
        self.fav_rounds_var = tk.StringVar(value="2")
        self.fav_speed_duration_var = tk.StringVar(value="2")

        self.fav_jitter_min_delay_var = tk.StringVar(value="70")
        self.fav_jitter_up_threshold_var = tk.StringVar(value="15")

        self.fav_schedule_enabled_var = tk.BooleanVar(value=False)
        self.fav_schedule_interval_var = tk.StringVar(value="60")
        self.fav_target_hk_count_var = tk.StringVar(value="3")
        self.fav_target_nohk_count_var = tk.StringVar(value="5")

        self.fav_quota_early_stop_var = tk.BooleanVar(value=True)
        self.fav_fallback_enabled_var = tk.BooleanVar(value=True)

        self.incubate_hours_var = tk.StringVar(value="24")
        self.incubate_passes_var = tk.StringVar(value="5")

        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.clash_client = ClashClient(host="127.0.0.1", port=9097, secret="")
        self.state = StateManager()

        self.apply_theme_styles()
        self.setup_ui()
        self.setup_context_menus()
        self.load_persisted_config()
        self.auto_read_config()
        self.load_profile_data()
        self.align_favorites_with_current_subscription()
        self.purge_invalid_and_blacklisted_from_all_pools()
        self.save_persisted_config()
        self.do_write_script_file(list(self.favorites))

        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.test_connection(auto_sync=False)
        self.clear_test_history(silent=True)
        self.update_last_run_display()

        if TRAY_SUPPORTED:
            self.setup_tray_icon()
        else:
            self.sched_status_label.config(text="未检测到 pystray，托盘未加载", fg=THEME["accent_yellow"])

        self.log("系统就绪：已开启 7 天滑动 Colo 历史追踪与防漂移拦截。")
        self._is_initialized = True
        threading.Thread(target=self._scheduler_daemon_loop, daemon=True).start()

    def log(self, message):
        now_str = time.strftime("%H:%M:%S")
        formatted = f"[{now_str}] {message}"
        try:
            self.root.after(0, lambda: self._append_log_text(formatted))
        except Exception:
            pass

    def _append_log_text(self, text_line):
        if not hasattr(self, "log_text"):
            return
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text_line + "\n")
        lines = int(self.log_text.index("end-1c").split(".")[0])
        if lines > 400:
            self.log_text.delete("1.0", "100.0")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    # ==================== 7 天滑动 Colo 历史桶与分析算法 ====================
    def record_colo_sample(self, node_name, endpoint, c_code, c_disp):
        record_colo_sample(
            self.node_colo_history,
            node_name,
            endpoint,
            c_code,
            c_disp,
            node_colo_dict=self.node_colo,
        )

        disp_to_set = c_disp if (c_disp and c_disp != "-") else (c_code if c_code and c_code != "-" else "-")

        # 确保所有共享该物理端点的同名/别名节点的最新 Colo 同步刷新
        if endpoint and hasattr(self, "all_nodes"):
            for n in self.all_nodes:
                if self.get_node_endpoint(n) == endpoint:
                    if disp_to_set != "-" or n not in self.node_colo:
                        self.node_colo[n] = disp_to_set

        # 同步更新沉淀孵化池与典藏管理池对应项
        if endpoint and hasattr(self, "verified_nodes") and endpoint in self.verified_nodes:
            if disp_to_set != "-" or self.verified_nodes[endpoint].get("colo", "-") == "-":
                self.verified_nodes[endpoint]["colo"] = disp_to_set

        if hasattr(self, "stars_nodes"):
            for s_node in self.stars_nodes:
                if s_node.get("endpoint") == endpoint or (node_name and s_node.get("matched_name") == node_name):
                    if disp_to_set != "-" or s_node.get("colo", "-") == "-":
                        s_node["colo"] = disp_to_set

    def analyze_colo_stats(self, history_list, now=None, node_name=None):
        return analyze_colo_stats(history_list, now=now, node_name=node_name)

    def is_node_hongkong(self, node_name):
        return is_node_hongkong(node_name)

    def is_asian_node(self, node_name, colo=None):
        if not colo:
            ep = self.get_node_endpoint(node_name)
            colo = self.node_colo.get(node_name, self.node_colo.get(ep, "-"))
        return is_asian_node(node_name, colo=colo)

    def auto_filter_and_blacklist_non_asia_nodes(self):
        cnt, _ = auto_filter_and_blacklist_non_asia_nodes(
            self.all_nodes,
            self.local_blacklist,
            self.favorites,
            self.blacklist_reasons,
            self.get_node_endpoint,
            self.is_asian_node,
            node_colo_dict=self.node_colo,
        )
        if cnt > 0:
            self.save_persisted_config()
            self.root.after(0, self.refresh_tables)

    def audit_untested_against_history(self):
        """全面审计待测池：对已有历史测试记录且未达标的节点进行合规归类，杜绝已测不合格节点滞留待测池。
        1. 若节点历史延迟均 > max_delay 或超时，直接归入延迟黑名单，并拉黑物理端点
        2. 若节点历史测速存在且 < min_speed，直接归入低速黑名单，并拉黑物理端点
        返回归类淘汰的节点数量
        """
        try:
            max_d = int(self.max_delay_threshold_var.get().strip()) if self.max_delay_threshold_var.get().strip().isdigit() else 100
        except Exception:
            max_d = 100
        try:
            min_s = float(self.min_speed_threshold_var.get().strip()) if self.min_speed_threshold_var.get().strip() else 5.0
        except Exception:
            min_s = 5.0

        fav_eps, bl_eps, sbl_eps, star_eps = self.get_pool_endpoint_sets()
        audited_delay_cnt = 0
        audited_speed_cnt = 0

        for n in list(self.all_nodes):
            ep = self.get_node_endpoint(n)
            # 已在精选、黑名单、孵化、典藏中的跳过
            if (n in self.favorites) or (ep and ep in fav_eps):
                continue
            if (n in self.local_blacklist) or (ep and ep in bl_eps):
                continue
            if (n in self.speed_blacklist) or (ep and ep in sbl_eps):
                continue
            if (n in getattr(self, "verified_nodes", {})) or (ep and ep in star_eps):
                continue

            # 检查是否有历史延迟记录 (优先物理端点)
            hist_d_items = []
            if ep and ep in self.node_delay_history:
                hist_d_items = self.node_delay_history[ep]
            elif n in self.node_delay_history:
                hist_d_items = self.node_delay_history[n]

            valid_d = [x.get("d") for x in hist_d_items if isinstance(x, dict) and 0 < x.get("d", 0) < 99999]
            if valid_d:
                best_d = min(valid_d)
                if best_d > max_d:
                    d_reason = f"延迟超标 ({best_d}ms > {max_d}ms)"
                    self.local_blacklist.add(n)
                    self.record_blacklist_reason(n, d_reason)
                    if ep:
                        self.local_blacklist.add(ep)
                        self.record_blacklist_reason(ep, d_reason)
                    audited_delay_cnt += 1
                    continue

            # 检查是否有历史下行测速记录
            spd_hist = self.node_speed_history.get(n, self.node_speed_history.get(ep, []))
            valid_s = [s for s in spd_hist if isinstance(s, (int, float))]
            if valid_s:
                best_s = max(valid_s)
                if best_s < min_s:
                    s_reason = "下行测速失败" if best_s < 0 else f"下行未达标 ({best_s:.2f} < {min_s} MB/s)"
                    self.speed_blacklist.add(n)
                    self.record_blacklist_reason(n, s_reason)
                    if ep:
                        self.speed_blacklist.add(ep)
                        self.record_blacklist_reason(ep, s_reason)
                    audited_speed_cnt += 1
                    continue

        tot_audited = audited_delay_cnt + audited_speed_cnt
        if tot_audited > 0:
            self.save_persisted_config()
            self.log(f"📋【待测池历史归类】已将历史不合格节点自动归入黑名单: 延迟超标 {audited_delay_cnt} 个，低速 {audited_speed_cnt} 个")
        return tot_audited

    def apply_theme_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TNotebook", background=THEME["bg_main"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=THEME["bg_card"],
            foreground=THEME["text_muted"],
            padding=[16, 8],
            font=("Microsoft YaHei UI", 9, "bold"),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", THEME["accent_blue"])],
            foreground=[("selected", "#ffffff")],
        )

        style.configure(
            "Treeview",
            background=THEME["tree_bg"],
            fieldbackground=THEME["tree_bg"],
            foreground=THEME["text_main"],
            rowheight=32,
            borderwidth=0,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["bg_card"],
            foreground=THEME["text_muted"],
            relief="flat",
            padding=[8, 8],
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        style.map(
            "Treeview.Heading",
            background=[("active", THEME["bg_hover"])],
            foreground=[("active", THEME["text_main"])],
        )
        style.map(
            "Treeview",
            background=[("selected", THEME["tree_selected"])],
            foreground=[("selected", "#38bdf8")],
        )

        style.configure(
            "Vertical.TScrollbar",
            background=THEME["bg_card"],
            troughcolor=THEME["bg_main"],
            borderwidth=0,
            arrowsize=10,
        )

        style.configure(
            "TCombobox",
            fieldbackground=THEME["bg_input"],
            background=THEME["bg_card"],
            foreground=THEME["text_main"],
            arrowcolor=THEME["text_muted"],
            borderwidth=1,
            relief="flat",
        )
        self.root.option_add("*TCombobox*Listbox.background", THEME["bg_card"])
        self.root.option_add("*TCombobox*Listbox.foreground", THEME["text_main"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", THEME["accent_blue"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.root.option_add("*TCombobox*Listbox.font", ("Microsoft YaHei UI", 9))

    def update_last_run_display(self):
        full_str = time.strftime("%m-%d %H:%M:%S", time.localtime(self.last_full_run_timestamp)) if self.last_full_run_timestamp > 0 else "未运行"
        fav_str = time.strftime("%m-%d %H:%M:%S", time.localtime(self.last_fav_run_timestamp)) if self.last_fav_run_timestamp > 0 else "未运行"
        self.last_time_label.config(text=f"🕒 上次检测  全量: {full_str}  |  复检: {fav_str}")

    def load_persisted_config(self):
        data = safe_load_config(CONFIG_STORAGE_PATH)
        if not data:
            return
        try:
            self.max_delay_threshold_var.set(data.get("max_delay", "100"))
            self.min_speed_threshold_var.set(data.get("min_speed", "5.0"))
            self.target_node_count_var.set(data.get("target_count", ""))
            self.blacklist_threshold_var.set(data.get("blacklist_threshold", "130"))

            self.speed_bl_threshold_var.set(data.get("speed_bl_threshold", "1.0"))
            self.speed_bl_rounds_var.set(data.get("speed_bl_rounds", "4"))
            self.jitter_min_delay_var.set(data.get("jitter_min_delay", "80"))
            self.jitter_up_threshold_var.set(data.get("jitter_up_threshold", "20"))

            self.test_rounds_var.set(data.get("test_rounds", "4"))
            self.test_timeout_var.set(data.get("test_timeout", "1500"))
            self.speed_duration_var.set(data.get("speed_duration", "3"))
            self.test_url_var.set(data.get("test_url", "http://www.msftconnecttest.com/connecttest.txt"))
            self.speed_url_var.set(data.get("speed_url", "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip"))
            self.schedule_enabled_var.set(data.get("schedule_enabled", False))
            self.schedule_interval_var.set(data.get("schedule_interval", "120"))
            self.schedule_times_var.set(data.get("schedule_times", "08:00, 13:00, 20:00"))

            self.group_interval_var.set(data.get("group_interval", "300"))
            self.group_tolerance_var.set(data.get("group_tolerance", "20"))
            self.star_group_interval_var.set(data.get("star_group_interval", "300"))
            self.star_group_tolerance_var.set(data.get("star_group_tolerance", "20"))

            cf_en = data.get("cf_worker_enabled", False)
            cf_u = data.get("cf_worker_url", "https://cf-nodes.douyutvshow.workers.dev/")
            cf_tok = data.get("cf_worker_token", "MySecretToken2026")
            self.cf_worker_enabled_var.set(cf_en)
            self.cf_worker_url_var.set(cf_u)
            self.cf_worker_token_var.set(cf_tok)
            self._cached_cf_enabled = bool(cf_en)
            self._cached_cf_url = str(cf_u).strip()
            self._cached_cf_token = str(cf_tok).strip()

            self.fav_max_delay_var.set(data.get("fav_max_delay", "80"))
            self.fav_min_speed_var.set(data.get("fav_min_speed", "8.0"))
            self.fav_rounds_var.set(data.get("fav_rounds", "2"))
            self.fav_speed_duration_var.set(data.get("fav_speed_duration", "2"))
            self.fav_jitter_min_delay_var.set(data.get("fav_jitter_min_delay", "70"))
            self.fav_jitter_up_threshold_var.set(data.get("fav_jitter_up_threshold", "15"))

            self.fav_schedule_enabled_var.set(data.get("fav_schedule_enabled", False))
            self.fav_schedule_interval_var.set(data.get("fav_schedule_interval", "60"))
            self.fav_target_hk_count_var.set(data.get("fav_target_hk_count", "3"))
            self.fav_target_nohk_count_var.set(data.get("fav_target_nohk_count", "5"))

            self.fav_quota_early_stop_var.set(data.get("fav_quota_early_stop", True))
            self.fav_fallback_enabled_var.set(data.get("fav_fallback_enabled", True))

            self.incubate_hours_var.set(data.get("incubate_hours", "24"))
            self.incubate_passes_var.set(data.get("incubate_passes", "5"))

            self.last_full_run_timestamp = float(data.get("last_full_run_timestamp", 0.0))
            self.last_fav_run_timestamp = float(data.get("last_fav_run_timestamp", 0.0))

            self.favorites = set(data.get("favorites", []))
            self.local_blacklist = set(data.get("local_blacklist", []))
            self.speed_blacklist = set(data.get("speed_blacklist", []))
            self.blacklist_reasons = data.get("blacklist_reasons", {})
            self.fav_reasons = data.get("fav_reasons", {})
            self.node_speed_history = data.get("node_speed_history", {})
            self.node_colo = data.get("node_colo", {})

            # 兼容并载入带时间戳的 7 天时序桶
            raw_colo_hist = data.get("node_colo_history", {})
            self.node_colo_history = {}
            now_ts = time.time()
            cutoff = now_ts - 7 * 86400
            for k, v in raw_colo_hist.items():
                if isinstance(v, list):
                    migrated = []
                    for item in v:
                        if isinstance(item, dict) and item.get("ts", 0) >= cutoff:
                            migrated.append(item)
                        elif isinstance(item, str) and item != "-":
                            migrated.append({"ts": now_ts, "colo": item})
                    self.node_colo_history[k] = migrated

            # 载入并清洗7天滑动延迟时序记录
            raw_delay_hist = data.get("node_delay_history", {})
            self.node_delay_history = {}
            for k, v in raw_delay_hist.items():
                if isinstance(v, list):
                    migrated_delays = [
                        item for item in v
                        if isinstance(item, dict) and item.get("ts", 0) >= cutoff and 0 < item.get("d", 0) < 99999
                    ]
                    if migrated_delays:
                        self.node_delay_history[k] = migrated_delays[-30:]

            self.verified_nodes = data.get("verified_nodes", {})
            self.stars_nodes = data.get("stars_nodes", [])
            self.auto_endpoints = set(data.get("auto_endpoints", []))
            self.node_details.update(data.get("node_details", {}))

            self.deduplicate_favorites_by_endpoint()
            self.purge_invalid_and_blacklisted_from_all_pools()
            self.refresh_verified_table()
            self.refresh_stars_table()
            self.audit_untested_against_history()

            self._on_schedule_toggle()
            self._on_fav_schedule_toggle()
        except Exception:
            pass

    def save_persisted_config(self):
        try:
            cfg = {
                "max_delay": self.max_delay_threshold_var.get().strip(),
                "min_speed": self.min_speed_threshold_var.get().strip(),
                "target_count": self.target_node_count_var.get().strip(),
                "blacklist_threshold": self.blacklist_threshold_var.get().strip(),
                "speed_bl_threshold": self.speed_bl_threshold_var.get().strip(),
                "speed_bl_rounds": self.speed_bl_rounds_var.get().strip(),
                "jitter_min_delay": self.jitter_min_delay_var.get().strip(),
                "jitter_up_threshold": self.jitter_up_threshold_var.get().strip(),
                "test_rounds": self.test_rounds_var.get().strip(),
                "test_timeout": self.test_timeout_var.get().strip(),
                "speed_duration": self.speed_duration_var.get().strip(),
                "test_url": self.test_url_var.get().strip(),
                "speed_url": self.speed_url_var.get().strip(),
                "schedule_enabled": self.schedule_enabled_var.get(),
                "schedule_interval": self.schedule_interval_var.get().strip(),
                "schedule_times": self.schedule_times_var.get().strip(),
                "group_interval": self.group_interval_var.get().strip(),
                "group_tolerance": self.group_tolerance_var.get().strip(),
                "star_group_interval": self.star_group_interval_var.get().strip(),
                "star_group_tolerance": self.star_group_tolerance_var.get().strip(),
                "cf_worker_enabled": self.cf_worker_enabled_var.get(),
                "cf_worker_url": self.cf_worker_url_var.get().strip(),
                "cf_worker_token": self.cf_worker_token_var.get().strip(),
                "fav_max_delay": self.fav_max_delay_var.get().strip(),
                "fav_min_speed": self.fav_min_speed_var.get().strip(),
                "fav_rounds": self.fav_rounds_var.get().strip(),
                "fav_speed_duration": self.fav_speed_duration_var.get().strip(),
                "fav_jitter_min_delay": self.fav_jitter_min_delay_var.get().strip(),
                "fav_jitter_up_threshold": self.fav_jitter_up_threshold_var.get().strip(),
                "fav_schedule_enabled": self.fav_schedule_enabled_var.get(),
                "fav_schedule_interval": self.fav_schedule_interval_var.get().strip(),
                "fav_target_hk_count": self.fav_target_hk_count_var.get().strip(),
                "fav_target_nohk_count": self.fav_target_nohk_count_var.get().strip(),
                "fav_quota_early_stop": self.fav_quota_early_stop_var.get(),
                "fav_fallback_enabled": self.fav_fallback_enabled_var.get(),
                "incubate_hours": self.incubate_hours_var.get().strip(),
                "incubate_passes": self.incubate_passes_var.get().strip(),
                "last_full_run_timestamp": self.last_full_run_timestamp,
                "last_fav_run_timestamp": self.last_fav_run_timestamp,
                "favorites": list(self.favorites),
                "local_blacklist": list(self.local_blacklist),
                "speed_blacklist": list(self.speed_blacklist),
                "blacklist_reasons": getattr(self, "blacklist_reasons", {}),
                "fav_reasons": getattr(self, "fav_reasons", {}),
                "node_speed_history": self.node_speed_history,
                "node_delay_history": self.node_delay_history,
                "node_colo": self.node_colo,
                "node_colo_history": self.node_colo_history,
                "verified_nodes": self.verified_nodes,
                "stars_nodes": self.stars_nodes,
                "auto_endpoints": list(self.auto_endpoints),
                "node_details": self.node_details,
            }
            ok, err = atomic_save_config(CONFIG_STORAGE_PATH, cfg)
            if not ok and hasattr(self, "log"):
                self.log(f"⚠️ 配置文件原子写入警告: {err}")
        except Exception:
            pass

    def on_boot_toggle(self):
        val = self.boot_startup_var.get()
        ok, err = set_boot_startup_registry(val)
        if ok:
            msg = "已开启开机静默后台运行！" if val else "已关闭开机自启动。"
            self.status_label.config(text=msg)
            self.log(msg)
        else:
            messagebox.showerror("设置失败", f"开机注册表设置失败：\n{err}")
            self.boot_startup_var.set(not val)

    def _safe_var_get(self, var_name, default=False):
        try:
            v = getattr(self, var_name, None)
            if v is not None:
                return bool(v.get())
        except Exception:
            pass
        return default

    def setup_tray_icon(self):
        menu = pystray.Menu(
            pystray.MenuItem("打开主窗口", self.show_from_tray, default=True),
            pystray.MenuItem("🚀 立即执行一次全局优选", lambda: self.root.after(0, self.start_full_auto_pipeline)),
            pystray.MenuItem("⚡ 立即执行优质池复检", lambda: self.root.after(0, self.start_fav_review_pipeline)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "开机静默自启",
                self._toggle_boot_from_tray,
                checked=lambda item: self._safe_var_get("boot_startup_var"),
            ),
            pystray.MenuItem(
                "全局定时优选",
                self._toggle_sched_from_tray,
                checked=lambda item: self._safe_var_get("schedule_enabled_var"),
            ),
            pystray.MenuItem(
                "优质定时复检",
                self._toggle_fav_sched_from_tray,
                checked=lambda item: self._safe_var_get("fav_schedule_enabled_var"),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("完全退出", self.quit_app),
        )
        self.tray_icon = pystray.Icon(
            "ClashVergeNodeAssistant",
            create_tray_icon_image(),
            "Clash Verge 节点助手",
            menu,
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _toggle_boot_from_tray(self):
        cur = self.boot_startup_var.get()
        self.root.after(0, lambda: [self.boot_startup_var.set(not cur), self.on_boot_toggle()])

    def _toggle_sched_from_tray(self):
        cur = self.schedule_enabled_var.get()
        self.root.after(0, lambda: [self.schedule_enabled_var.set(not cur), self.save_persisted_config(), self._on_schedule_toggle()])

    def _toggle_fav_sched_from_tray(self):
        cur = self.fav_schedule_enabled_var.get()
        self.root.after(0, lambda: [self.fav_schedule_enabled_var.set(not cur), self.save_persisted_config(), self._on_fav_schedule_toggle()])

    def hide_to_tray(self):
        self.save_persisted_config()
        if not TRAY_SUPPORTED:
            self.root.destroy()
            return

        self.root.withdraw()
        if not self.has_shown_tray_tip:
            self.has_shown_tray_tip = True
            send_system_notification("节点助手已隐藏到后台", "程序已最小化到系统托盘，后台监控中。双击托盘图标可打开窗口。")

    def show_from_tray(self):
        self.root.after(0, self._restore_window)

    def _restore_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_app(self):
        self.save_persisted_config()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def auto_read_config(self):
        port, secret = ClashClient.auto_detect_credentials()
        self.port_var.set(str(port))
        self.secret_var.set(secret)
        self.clash_client.update_credentials(port, secret)

    def test_connection(self, auto_sync=False):
        port = self.port_var.get().strip()
        secret = self.secret_var.get().strip()
        self.clash_client.update_credentials(port, secret)
        ok, ver = self.clash_client.test_connection()
        if ok:
            self.conn_label.config(text=f"● 内核已联动 ({port})", fg=THEME["accent_green"])
            if auto_sync:
                threading.Thread(target=self.sync_existing_delays, daemon=True).start()
            return True
        self.conn_label.config(text="○ 未连接内核", fg=THEME["accent_red"])
        return False

    def _call_api(self, endpoint, timeout=2.5, method="GET", data=None):
        try:
            port = self.port_var.get().strip() if hasattr(self, "port_var") else "9097"
            self._cached_port = port
        except Exception:
            port = getattr(self, "_cached_port", "9097")
        try:
            secret = self.secret_var.get().strip() if hasattr(self, "secret_var") else ""
            self._cached_secret = secret
        except Exception:
            secret = getattr(self, "_cached_secret", "")

        self.clash_client.update_credentials(port, secret)
        return self.clash_client.call_api(endpoint, timeout=timeout, method=method, data=data)

    def get_clash_mixed_port(self):
        return self.clash_client.get_mixed_port(default=7897)

    def wait_for_kernel_reload(self, target_nodes, max_wait_sec=15):
        return self.clash_client.wait_for_kernel_reload(target_nodes, max_wait_sec=max_wait_sec)

    def extract_nodes_and_details_from_file(self, filepath):
        return extract_nodes_and_details_from_file(filepath)

    def resolve_node_to_current(self, target_key):
        return resolve_node_to_current(
            target_key,
            all_nodes=getattr(self, "all_nodes", []),
            node_details=getattr(self, "node_details", {}),
        )

    def choose_canonical_node_name(self, node_list):
        return choose_canonical_node_name(node_list)

    def get_node_endpoint(self, node_name):
        return get_node_endpoint(
            node_name,
            node_details=getattr(self, "node_details", None),
            all_nodes=getattr(self, "all_nodes", None),
            verified_nodes=getattr(self, "verified_nodes", None),
            clash_client=getattr(self, "clash_client", None),
        )
        if len(node_list) == 1:
            return node_list[0]

        def _canonical_score(name):
            score = 0
            # 1. 包含具体测速/延迟标签（如 43.29ms, 12.88 MB/s）加最高分
            if re.search(r"\d+(?:\.\d+)?\s*(?:ms|mb/s|kb/s)", name, re.IGNORECASE):
                score += 60
            # 2. 包含优质、高速、专线、精品等质量关键词
            if any(k in name for k in ["优选", "高速", "精品", "专线", "PRO", "VIP"]):
                score += 30
            # 3. 包含清晰地区中英文标识
            if any(k in name for k in ["香港", "HK", "台湾", "TW", "日本", "JP", "韩国", "KR", "新加坡", "SG"]):
                score += 20
            # 4. 纯 IP 命名扣分，避免把没有语义的 IP:Port 选为主代表
            clean_n = name.strip()
            if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?$", clean_n):
                score -= 30
            # 5. 扣除临时调试标签
            if "auto" in name.lower() or "保活" in name:
                score -= 10
            return score

        return max(node_list, key=_canonical_score)

    def get_node_endpoint(self, node_name):
        if not node_name:
            return ""

        # 1. 节点名本身直接就是 IP:端口格式 (如 '1.2.3.4:443')
        node_name_clean = str(node_name).strip()
        if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}$", node_name_clean):
            return node_name_clean

        # 2. 如果包含 '#'（如 Worker 节点文本 '1.2.3.4:443#香港 10MB/s'）
        if "#" in node_name_clean:
            prefix = node_name_clean.split("#", 1)[0].strip()
            m_pre = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})$", prefix)
            if m_pre:
                return f"{m_pre.group(1)}:{m_pre.group(2)}"

        # 3. 从当前已解析的 node_details 字典查找
        info = self.node_details.get(node_name, {})
        server = info.get("server", "").strip()
        port = str(info.get("port", "443")).strip()
        if server:
            return f"{server}:{port}"

        # 4. 从节点名中正则直接提取完整 IPv4 及端口 (如 '辣子鸡优选 | 多哥 TG | 129.154.50.72:8443')
        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{2,5}))?", node_name_clean)
        if m:
            ip = m.group(1)
            p = m.group(2) if m.group(2) else "443"
            return f"{ip}:{p}"

        # 5. 检查沉淀孵化池/典藏常青池已有物理端点记录
        if node_name in getattr(self, "verified_nodes", {}):
            v_ep = self.verified_nodes[node_name].get("endpoint", "")
            if v_ep:
                return v_ep

        # 6. 仅当该节点活跃在当前 Clash 配置中时，尝试内核 API 查询并缓存
        if getattr(self, "all_nodes", None) and node_name in self.all_nodes:
            try:
                enc = urllib.parse.quote(node_name, safe="")
                res = self._call_api(f"/proxies/{enc}", timeout=0.3)
                if res and isinstance(res, dict):
                    s = res.get("server", "").strip()
                    p = str(res.get("port", "443")).strip()
                    if s:
                        self.node_details[node_name] = {"server": s, "port": p}
                        return f"{s}:{p}"
            except Exception:
                pass

        return ""

    def get_pool_endpoint_sets(self):
        return get_pool_endpoint_sets(
            self.favorites,
            self.local_blacklist,
            self.speed_blacklist,
            getattr(self, "auto_endpoints", set()),
            getattr(self, "verified_nodes", {}),
            getattr(self, "stars_nodes", []),
            self.get_node_endpoint,
        )

    def fetch_auto_endpoints_from_cloud(self):
        """尝试从 Worker /auto.txt 获取云端保活的端点集合"""
        try:
            _, base_url, token = self.get_cf_worker_config()
            if not base_url or not base_url.startswith("http"):
                return set()
            auto_url = f"{base_url.rstrip('/')}/auto.txt"
            mixed_port = self.get_clash_mixed_port()
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            proxy_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
            direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))

            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            }
            req = urllib.request.Request(auto_url, headers=headers)
            for opener in [proxy_opener, direct_opener]:
                try:
                    with opener.open(req, timeout=5) as resp:
                        if resp.status == 200:
                            content = resp.read().decode("utf-8", errors="ignore")
                            eps = set()
                            for line in content.splitlines():
                                line = line.strip()
                                if not line or line.startswith("⏳") or line.startswith("Error"):
                                    continue
                                ep_part = line.split("#")[0].strip() if "#" in line else line.split()[0].strip()
                                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", ep_part)
                                if m:
                                    eps.add(m.group(1))
                            if eps:
                                return eps
                except Exception:
                    continue
        except Exception:
            pass
        return set()

    def get_cf_worker_config(self):
        """安全获取 Worker 配置，主线程与后台子线程均兼容，彻底避免 'main thread is not in main loop' 异常"""
        try:
            enabled = bool(self.cf_worker_enabled_var.get())
            self._cached_cf_enabled = enabled
        except Exception:
            enabled = getattr(self, "_cached_cf_enabled", False)

        try:
            url = self.cf_worker_url_var.get().strip()
            self._cached_cf_url = url
        except Exception:
            url = getattr(self, "_cached_cf_url", "https://cf-nodes.douyutvshow.workers.dev/")

        try:
            token = self.cf_worker_token_var.get().strip()
            self._cached_cf_token = token
        except Exception:
            token = getattr(self, "_cached_cf_token", "MySecretToken2026")

        return enabled, url, token

    def push_text_to_cf_worker(self, text_payload, subpath=""):
        _, base_url, token = self.get_cf_worker_config()
        base_url = base_url.rstrip("/")

        if not base_url or not base_url.startswith("http"):
            return False, "Worker 网址无效"

        # 安全防护：若内容为空或仅包含空白字符，避免向 Worker 发送空请求触发 HTTP 400 Bad Request
        if not text_payload or not text_payload.strip():
            return True, "内容为空，无需推送"

        target_url = f"{base_url}{subpath}" if subpath else f"{base_url}/"

        mixed_port = self.get_clash_mixed_port()
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        proxy_handler = urllib.request.ProxyHandler({
            "http": f"http://127.0.0.1:{mixed_port}",
            "https": f"http://127.0.0.1:{mixed_port}",
        })
        proxy_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
        direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/plain; charset=utf-8",
            "User-Agent": "ClashVergeNodeAssistant/1.0",
        }
        req = urllib.request.Request(target_url, data=text_payload.encode("utf-8"), headers=headers, method="POST")

        last_err = ""
        for attempt in range(1, 4):
            for use_proxy, opener in [(True, proxy_opener), (False, direct_opener)]:
                try:
                    with opener.open(req, timeout=10) as resp:
                        if resp.status in (200, 201, 204):
                            channel = f"代理端口:{mixed_port}" if use_proxy else "直连"
                            return True, f"成功推送至 {target_url} ({channel})"
                        last_err = f"Worker 返回状态码: {resp.status}"
                except urllib.error.HTTPError as ex:
                    if ex.code == 401:
                        return False, "认证失败(401)，请确认 AUTH_TOKEN 密钥！"
                    last_err = f"HTTP({ex.code}): {ex.reason}"
                except Exception as ex:
                    last_err = str(ex)
            time.sleep(1.0)

        return False, f"重试失败: {last_err}"

    def sync_premium_nodes_to_cf_worker(self, premium_nodes, subpath="/auto.txt"):
        lines = []
        seen_eps = set()
        for n in premium_nodes:
            endpoint = self.get_node_endpoint(n)
            if not endpoint or endpoint in seen_eps:
                continue
            seen_eps.add(endpoint)
            region = self.node_colo.get(n, detect_node_region(n))
            spd = self.node_speeds.get(n, 0.0)
            lines.append(f"{endpoint}#{region} {spd:.2f} MB/s")
        if not lines:
            return True, "本地优质池为空，跳过推送"
        return self.push_text_to_cf_worker("\r\n".join(lines) + "\r\n", subpath)

    def sync_all_pools_to_cf_worker(self):
        """
        全量同步推送当前三大池（优质精选池、沉淀孵化池、典藏常青池）至 Cloudflare Worker 远端文本。
        远端对应路径：
        1. /auto.txt      -> 优质精选池 (favorites)
        2. /verified.txt  -> 沉淀孵化池 (verified_nodes)
        3. /              -> 典藏常青池 (stars_nodes)
        任何不合规/被淘汰/拉黑的节点在此处均已被完全清洗排除，保证远端彻底同步净化。
        """
        enabled, base_url, token = self.get_cf_worker_config()
        if not enabled:
            return False, "Worker 推送开关未开启"
        if not base_url or not token:
            return False, "未配置 Worker 地址或授权密钥"

        # 1. 优质精选池 -> /auto.txt
        auto_ok, auto_msg = self.sync_premium_nodes_to_cf_worker(list(self.favorites), subpath="/auto.txt")
        self.log(f"Worker 优质池同步 (/auto.txt): {auto_msg}")

        # 2. 沉淀孵化池 -> /verified.txt
        ver_lines = []
        for v in self.verified_nodes.values():
            ep = v.get("endpoint", "")
            rem = v.get("remark", "优质沉淀")
            if ep:
                ver_lines.append(f"{ep}#{rem}")
        if ver_lines:
            ver_payload = "\r\n".join(ver_lines) + "\r\n"
            ver_ok, ver_msg = self.push_text_to_cf_worker(ver_payload, "/verified.txt")
            self.log(f"Worker 沉淀池同步 (/verified.txt): {ver_msg}")
        else:
            ver_ok = True
            self.log("Worker 沉淀池同步 (/verified.txt): 本地沉淀池为空，无需推送")

        # 3. 典藏常青池 -> / (根目录)
        star_lines = []
        for s in self.stars_nodes:
            ep = s.get("endpoint", "")
            rem = s.get("remark", "典藏常青")
            if ep:
                star_lines.append(f"{ep}#{rem}")
        if star_lines:
            star_payload = "\r\n".join(star_lines) + "\r\n"
            star_ok, star_msg = self.push_text_to_cf_worker(star_payload, "")
            self.log(f"Worker 典藏池同步 (/): {star_msg}")
        else:
            star_ok = True
            self.log("Worker 典藏池同步 (/): 本地典藏池为空，无需推送")

        all_ok = auto_ok and ver_ok and star_ok
        return all_ok, f"优质池:{auto_ok}, 沉淀池:{ver_ok}, 典藏池:{star_ok}"

    def record_blacklist_reason(self, name_or_ep, reason):
        if not hasattr(self, "blacklist_reasons") or not isinstance(self.blacklist_reasons, dict):
            self.blacklist_reasons = {}
        if not name_or_ep or not reason:
            return
        self.blacklist_reasons[name_or_ep] = reason
        ep = self.get_node_endpoint(name_or_ep) if hasattr(self, "get_node_endpoint") else ""
        if ep:
            self.blacklist_reasons[ep] = reason
            if ":" in ep:
                self.blacklist_reasons[ep.split(":")[0]] = reason

    def get_blacklist_reason(self, node_name, ep=None):
        if not hasattr(self, "blacklist_reasons") or not isinstance(self.blacklist_reasons, dict):
            self.blacklist_reasons = {}
        if not ep and node_name:
            ep = self.get_node_endpoint(node_name) if hasattr(self, "get_node_endpoint") else ""

        # 1. 优先从显式记录字典中提取
        if node_name and node_name in self.blacklist_reasons:
            return self.blacklist_reasons[node_name]
        if ep and ep in self.blacklist_reasons:
            return self.blacklist_reasons[ep]
        if ep and ":" in ep:
            ip = ep.split(":")[0]
            if ip in self.blacklist_reasons:
                return self.blacklist_reasons[ip]

        # 2. 智能自动推导（兜底历史遗留数据或未显式传参场景）
        ep_val = ep or (self.get_node_endpoint(node_name) if hasattr(self, "get_node_endpoint") else "")

        # 2.1 如果位于低速黑名单，优先推导下行测速原因
        is_s_black = (node_name in self.speed_blacklist) or (ep_val and ep_val in self.speed_blacklist)
        if is_s_black:
            s_val = self.node_speeds.get(node_name, None)
            if s_val is not None:
                if s_val < 0:
                    return "下行测速失败/中断"
                return f"下行过低 ({s_val:.2f} MB/s)"
            s_hist = self.node_speed_history.get(node_name, [])
            if s_hist:
                last_s = s_hist[-1]
                if last_s < 0:
                    return "下行测速中断"
                return f"下行过低 ({last_s:.2f} MB/s)"
            return "下行低速淘汰"

        # 2.2 检查机房漂移
        colo_hist = self.node_colo_history.get(node_name, self.node_colo_history.get(ep_val, []))
        if colo_hist:
            _, _, has_drift, drift_disp = self.analyze_colo_stats(colo_hist, time.time(), node_name=node_name)
            if has_drift:
                return f"机房漂移 ({drift_disp})"

        # 2.3 延迟数据判定（超时）
        d_val = self.node_delays.get(node_name, None)
        if d_val is not None and d_val >= 99999:
            return "延迟超时 (≥99999ms)"
        d_hist = self.node_history.get(node_name, [])
        if d_hist and d_hist[-1] >= 99999:
            return "延迟超时 (≥99999ms)"

        # 2.4 非亚洲地区/机房判定
        if node_name and not self.is_asian_node(node_name):
            colo_val = self.node_colo.get(ep_val, self.node_colo.get(node_name, ""))
            if colo_val and colo_val != "-":
                return f"非亚洲机房 ({colo_val})"
            return "非亚洲地区/命名"

        # 2.5 延迟黑名单其它超标情况
        is_d_black = (node_name in self.local_blacklist) or (ep_val and ep_val in self.local_blacklist)
        if is_d_black:
            if d_val is not None:
                return f"延迟超标 ({d_val}ms)"
            if d_hist:
                return f"延迟淘汰 ({d_hist[-1]}ms)"
            return "延迟超标淘汰"

        return "-"

    def record_fav_reason(self, name_or_ep, reason, ep=None):
        if not hasattr(self, "fav_reasons") or not isinstance(self.fav_reasons, dict):
            self.fav_reasons = {}
        if not name_or_ep or not reason:
            return
        self.fav_reasons[name_or_ep] = reason
        target_ep = ep or (self.get_node_endpoint(name_or_ep) if hasattr(self, "get_node_endpoint") else "")
        if target_ep:
            self.fav_reasons[target_ep] = reason
            if ":" in target_ep:
                self.fav_reasons[target_ep.split(":")[0]] = reason

    def get_fav_reason(self, node_name, ep=None):
        if not hasattr(self, "fav_reasons") or not isinstance(self.fav_reasons, dict):
            self.fav_reasons = {}
        if not ep and node_name:
            ep = self.get_node_endpoint(node_name) if hasattr(self, "get_node_endpoint") else ""

        # 1. 优先从显式记录字典中提取
        if node_name and node_name in self.fav_reasons:
            return self.fav_reasons[node_name]
        if ep and ep in self.fav_reasons:
            return self.fav_reasons[ep]
        if ep and ":" in ep:
            ip = ep.split(":")[0]
            if ip in self.fav_reasons:
                return self.fav_reasons[ip]

        # 2. 智能自动推导
        # 2.1 检查是否为典藏常青推荐
        star_eps = {st.get("endpoint", "") for st in getattr(self, "stars_nodes", []) if isinstance(st, dict)}
        if ep and ep in star_eps:
            return "典藏常青节点"

        # 2.2 检查是否在沉淀孵化池考核中
        if ep and ep in getattr(self, "verified_nodes", {}):
            v = self.verified_nodes[ep]
            passes = v.get("passes", 1)
            first_seen = v.get("first_seen", time.time())
            alive_h = round((time.time() - first_seen) / 3600.0, 1)
            return f"沉淀考核中 (达标{passes}次/{alive_h}h)"

        # 2.3 基于最新测速与延迟推导
        d_val = self.node_delays.get(node_name, self.node_delays.get(ep, None))
        s_val = self.node_speeds.get(node_name, self.node_speeds.get(ep, None))
        if s_val is not None and s_val > 0 and d_val is not None and d_val < 99999:
            return f"优选达标 ({d_val}ms / {s_val:.2f}MB/s)"
        elif d_val is not None and d_val < 99999:
            return f"延迟优选 ({d_val}ms)"

        return "优质精选"

    def purge_invalid_and_blacklisted_from_all_pools(self):
        return purge_invalid_and_blacklisted_from_all_pools(
            self.favorites,
            getattr(self, "verified_nodes", {}),
            getattr(self, "stars_nodes", []),
            self.local_blacklist,
            self.speed_blacklist,
            self.get_node_endpoint,
        )

    def test_cf_worker_upload(self):
        worker_url = self.cf_worker_url_var.get().strip()
        token = self.cf_worker_token_var.get().strip()

        if not worker_url or not token:
            messagebox.showwarning("提示", "请先填入 Cloudflare Worker 地址和授权密钥！")
            return

        self.save_persisted_config()

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text="正在测试 Cloudflare Worker (/auto.txt)..."))
            sample_nodes = list(self.favorites) if self.favorites else (self.all_nodes[:5] if self.all_nodes else ["测试节点"])
            ok, msg = self.sync_premium_nodes_to_cf_worker(sample_nodes, subpath="/auto.txt")
            if ok:
                auto_url = f"{worker_url.rstrip('/')}/auto.txt"
                self.log(f"Worker 自动池上传验证成功：{msg}")
                self.root.after(0, lambda: messagebox.showinfo(
                    "测试成功",
                    f"🎉 自动优选通道验证成功！\n\n详情：{msg}\n\n可在浏览器打开：\n{auto_url}\n查看纯文本输出。"
                ))
                self.root.after(0, lambda: self.status_label.config(text="Cloudflare Worker 测试成功！"))
            else:
                self.log(f"Worker 测试上传失败：{msg}")
                self.root.after(0, lambda: messagebox.showerror("测试失败", f"❌ 推送失败：\n\n{msg}"))
                self.root.after(0, lambda: self.status_label.config(text="Cloudflare Worker 测试失败"))

        threading.Thread(target=_worker, daemon=True).start()

    def resolve_star_matches(self):
        reverse_map = {}
        for name, info in self.node_details.items():
            s = info.get('server', '').strip()
            p = str(info.get('port', '')).strip()
            if s and p:
                reverse_map[f"{s}:{p}"] = name
                reverse_map[s] = name

        for n in self.all_nodes:
            info = self.node_details.get(n, {})
            s = info.get('server', '').strip()
            p = str(info.get('port', '')).strip()
            if s and p:
                reverse_map[f"{s}:{p}"] = n
                reverse_map[s] = n

        if not reverse_map:
            try:
                data = self._call_api("/proxies", timeout=0.3)
                if data and "proxies" in data:
                    for p_name, p_info in data["proxies"].items():
                        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{2,5}))?", p_name)
                        if m:
                            ip = m.group(1)
                            port = m.group(2) if m.group(2) else "443"
                            reverse_map[f"{ip}:{port}"] = p_name
                            reverse_map[ip] = p_name
            except Exception:
                pass

        return reverse_map

    # ==================== 🔍 C 段全量高并发极速挖掘引擎 ====================
    def open_c_segment_mining_dialog(self, seed_input):
        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?", seed_input)
        if not m:
            messagebox.showwarning("提示", f"未能从【{seed_input}】中识别出合法的 IPv4 地址！")
            return

        seed_ip = m.group(1)
        seed_port = m.group(2) if m.group(2) else "443"
        c_ips = get_c_segment_ips(seed_ip)
        if not c_ips:
            messagebox.showwarning("提示", "无法解析该 IP 的 C 段！")
            return

        c_segment_name = ".".join(seed_ip.split(".")[:3]) + ".0/24"

        dialog = tk.Toplevel(self.root)
        dialog.title(f"🔍 C 段全量极速深度挖掘 - {c_segment_name}")
        dialog.geometry("980x640")
        dialog.configure(bg=THEME["bg_card"])
        dialog.transient(self.root)

        top_f = tk.Frame(dialog, bg=THEME["bg_card"], padx=14, pady=10)
        top_f.pack(fill=tk.X)

        tk.Label(top_f, text=f"网段: {c_segment_name}", fg="#38bdf8", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(top_f, text="端口:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        port_var = tk.StringVar(value=str(seed_port))
        tk.Entry(top_f, textvariable=port_var, width=5, bg=THEME["bg_input"], fg=THEME["text_main"], relief="flat", font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(3, 10))

        tk.Label(top_f, text="延迟门槛(≤ ms):", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        threshold_var = tk.StringVar(value="130")
        tk.Entry(top_f, textvariable=threshold_var, width=4, bg=THEME["bg_input"], fg=THEME["text_main"], relief="flat", font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(3, 10))

        status_lbl = tk.Label(top_f, text="准备就绪 (共 254 个 IP)", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9))
        status_lbl.pack(side=tk.LEFT, padx=10)

        cols = ("ip", "port", "rtt", "colo", "status")
        tree = ttk.Treeview(dialog, columns=cols, show="headings", selectmode="extended")
        tree.heading("ip", text="IP 地址 ↕")
        tree.heading("port", text="端口")
        tree.heading("rtt", text="TCP 握手延迟 ↕")
        tree.heading("colo", text="真实机房 (Colo)")
        tree.heading("status", text="评估状态")

        tree.column("ip", width=160, anchor="center")
        tree.column("port", width=70, anchor="center")
        tree.column("rtt", width=120, anchor="center")
        tree.column("colo", width=180, anchor="center")
        tree.column("status", width=120, anchor="center")

        tree.tag_configure("pass", foreground="#34d399")
        tree.tag_configure("fail", foreground="#f87171")

        btn_sel_none = tk.Button(top_f, text="清空选择", command=lambda: tree.selection_remove(tree.selection()), bg=THEME["bg_input"], fg=THEME["text_muted"], relief="flat", padx=8, pady=1, font=("Microsoft YaHei UI", 8))
        btn_sel_all = tk.Button(top_f, text="全选达标", command=lambda: tree.selection_set(tree.get_children()), bg=THEME["bg_input"], fg="#38bdf8", relief="flat", padx=8, pady=1, font=("Microsoft YaHei UI", 8))
        btn_sel_none.pack(side=tk.RIGHT, padx=4)
        btn_sel_all.pack(side=tk.RIGHT, padx=4)

        tree_frame = tk.Frame(dialog, bg=THEME["bg_main"], padx=2, pady=2)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview, style="Vertical.TScrollbar")
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        bottom_f = tk.Frame(dialog, bg=THEME["bg_card"], padx=14, pady=10)
        bottom_f.pack(fill=tk.X)

        is_running = [False]

        def _start_mining():
            if is_running[0]:
                return
            is_running[0] = True
            btn_start.config(state="disabled", bg=THEME["bg_hover"])
            btn_stop.config(state="normal")
            tree.delete(*tree.get_children())

            p_val = port_var.get().strip()
            t_val = int(threshold_var.get().strip()) if threshold_var.get().strip().isdigit() else 130

            def _worker():
                status_lbl.config(text="正在全并发 TCP 测延...", fg="#fbbf24")
                results = []
                completed = [0]

                def _scan_one(ip):
                    if not is_running[0]:
                        return
                    rtt = tcp_ping(ip, p_val, timeout=1.2)
                    results.append((ip, rtt))
                    completed[0] += 1
                    if completed[0] % 10 == 0 or completed[0] == len(c_ips):
                        dialog.after(0, lambda c=completed[0]: status_lbl.config(text=f"TCP 测延中: {c}/254"))

                with ThreadPoolExecutor(max_workers=50) as ex:
                    list(ex.map(_scan_one, c_ips))

                if not is_running[0]:
                    dialog.after(0, lambda: status_lbl.config(text="扫描已中止", fg=THEME["text_muted"]))
                    return

                alive_results = [r for r in results if r[1] <= t_val]
                status_lbl.config(text=f"TCP 达标 {len(alive_results)} 个，正在校准真实 Colo...", fg="#38bdf8")

                colo_map = {}
                def _colo_one(ip):
                    if not is_running[0]:
                        return
                    c_code, c_disp = get_cf_colo_raw(ip, p_val, timeout=1.5)
                    colo_map[ip] = (c_code, c_disp)

                with ThreadPoolExecutor(max_workers=20) as ex:
                    list(ex.map(_colo_one, [r[0] for r in alive_results]))

                alive_results.sort(key=lambda x: x[1])

                def _render():
                    for ip, rtt in alive_results:
                        _, c_disp = colo_map.get(ip, ("-", "-"))
                        tree.insert("", tk.END, values=(ip, p_val, f"{rtt} ms", c_disp, "✅ 极速达标"), tags=["pass"])
                    status_lbl.config(text=f"挖掘完成！共发现 {len(alive_results)} 个极速纯净 IP", fg=THEME["accent_green"])
                    btn_start.config(state="normal", bg=THEME["accent_green"])
                    btn_stop.config(state="disabled")
                    is_running[0] = False

                dialog.after(0, _render)

            threading.Thread(target=_worker, daemon=True).start()

        def _stop_mining():
            is_running[0] = False
            btn_stop.config(state="disabled")
            status_lbl.config(text="正在停止...", fg=THEME["text_muted"])

        def _import_to_pool(target="verified"):
            if is_running[0]:
                _stop_mining()
                time.sleep(0.3)

            all_children = tree.get_children()
            if not all_children:
                messagebox.showwarning("提示", "当前无挖掘结果可导入！", parent=dialog)
                return

            sel = tree.selection()
            if sel and len(sel) < len(all_children):
                ans = messagebox.askyesnocancel(
                    "导入范围确认",
                    f"检测到您当前选中了 {len(sel)} 行（全表共 {len(all_children)} 个达标节点）。\n\n"
                    f"• 点击【是 (Yes)】：仅导入当前选中的 {len(sel)} 个节点\n"
                    f"• 点击【否 (No)】：一键全选并导入全部 {len(all_children)} 个达标节点 (推荐)\n"
                    f"• 点击【取消】：取消本次导入",
                    parent=dialog
                )
                if ans is None:
                    return
                rows_to_import = sel if ans else all_children
            else:
                rows_to_import = all_children

            btn_import_fav.config(state="disabled")
            btn_import_verified.config(state="disabled")
            btn_import_stars.config(state="disabled")

            cnt = 0
            reverse_map = self.resolve_star_matches()
            now_ts = time.time()

            for r in rows_to_import:
                vals = tree.item(r, "values")
                ip, port, rtt, colo, _ = vals
                ep = f"{ip}:{port}"
                rem = f"{colo} [C段挖掘] {rtt}"

                is_asia = False
                if rem and self.is_asian_node(rem, colo):
                    is_asia = True
                elif colo and colo != "-" and self.is_asian_node(ep, colo):
                    is_asia = True
                elif ep and self.is_asian_node(ep, colo):
                    is_asia = True

                if not is_asia:
                    self.local_blacklist.add(ep)
                    continue

                try:
                    clean_rtt = int(rtt.replace(" ms", "").strip())
                except Exception:
                    clean_rtt = 0

                if colo and colo != "-":
                    c_code = colo.split()[-1] if " " in colo else colo
                    self.record_colo_sample(None, ep, c_code, colo)

                if target == "verified":
                    if ep not in self.verified_nodes:
                        self.verified_nodes[ep] = {
                            "endpoint": ep,
                            "colo": colo,
                            "remark": rem,
                            "first_seen": now_ts,
                            "passes": 1,
                            "fails": 0,
                            "delay": clean_rtt,
                            "speed": 0.0,
                            "reason": "批量手动导入",
                        }
                        cnt += 1
                elif target == "fav":
                    matched_name = reverse_map.get(ep, "")
                    if not matched_name and ":" in ep:
                        matched_name = reverse_map.get(ep.split(":")[0], "")
                    target_name = matched_name if matched_name else ep

                    if not self.is_asian_node(target_name, colo):
                        self.local_blacklist.add(target_name)
                        continue

                    if target_name not in self.favorites:
                        self.favorites.add(target_name)
                        cnt += 1
                    self.record_fav_reason(target_name, "批量手动导入")
                    self.local_blacklist.discard(target_name)
                    self.speed_blacklist.discard(target_name)
                    if ep:
                        self.local_blacklist.discard(ep)
                        self.speed_blacklist.discard(ep)
                    if clean_rtt > 0:
                        self.node_delays[target_name] = clean_rtt
                        self.node_history[target_name] = [clean_rtt]
                    if colo and colo != "-":
                        self.node_colo[target_name] = colo
                else:
                    existing_eps = {s["endpoint"] for s in self.stars_nodes}
                    if ep not in existing_eps:
                        self.stars_nodes.append({
                            "endpoint": ep,
                            "colo": colo,
                            "remark": rem,
                            "delay": clean_rtt,
                            "speed": 0.0,
                            "matched_name": "",
                            "reason": "批量手动导入",
                        })
                        cnt += 1

            if target == "fav":
                self.align_favorites_with_current_subscription()
                self.deduplicate_favorites_by_endpoint()

            self.save_persisted_config()
            self.refresh_tables()
            self.refresh_verified_table()
            self.refresh_stars_table()

            target_names = {
                "verified": "【⏳ 沉淀孵化池】",
                "fav": "【⭐ 优质精选池】",
                "stars": "【🏆 典藏管理池】"
            }
            target_name = target_names.get(target, "目标池")
            self.log(f"已从 C 段挖掘成果中批量收编 {cnt} 个极品 IP 至 {target_name}")

            # 后台全链路自动闭环：Worker 同步 -> 订阅更新 -> 写入 Script.js -> 热键热更新激活 -> 内核重载探测
            def _post_import_worker():
                logs_step = [f"✅ 本地收编: 成功收录 {cnt} 个极品 IP 至 {target_name}"]

                # 步骤 1: 尝试推送至 Cloudflare Worker 云端
                base_url = self.cf_worker_url_var.get().strip().rstrip("/")
                if base_url.startswith("http"):
                    dialog.after(0, lambda: status_lbl.config(text="[1/3] 正在同步推送至 Cloudflare Worker...", fg="#38bdf8"))
                    self.log(f"正在将收编节点同步发布至 Cloudflare Worker...")
                    if target == "verified":
                        lines = [f"{v['endpoint']}#{v['remark']}" for v in self.verified_nodes.values()]
                        ok_w, msg_w = self.push_text_to_cf_worker("\r\n".join(lines) + "\r\n", "/verified.txt")
                    elif target == "fav":
                        ok_w, msg_w = self.sync_premium_nodes_to_cf_worker(list(self.favorites), subpath="/auto.txt")
                    else:
                        lines = [f"{item.get('endpoint', '')}#{item.get('remark', '')}" for item in self.stars_nodes]
                        ok_w, msg_w = self.push_text_to_cf_worker("\r\n".join(lines) + "\r\n", "")

                    if ok_w:
                        logs_step.append("✅ 云端同步: 已成功推送到 Cloudflare Worker")
                        self.log(f"Worker 同步成功: {msg_w}")
                        time.sleep(1.0)
                    else:
                        logs_step.append(f"⚠️ 云端同步: {msg_w}")
                        self.log(f"Worker 同步提示: {msg_w}")
                else:
                    logs_step.append("ℹ️ 云端同步: 未配置 Cloudflare Worker 地址，已保存本地")

                # 步骤 2: 执行订阅更新 (拉取最新 profiles yaml 并重新解析)
                cur_idx = self.file_combo.current()
                cur_file_info = self.file_items[cur_idx] if (cur_idx >= 0 and cur_idx < len(self.file_items)) else None
                if cur_file_info and os.path.exists(cur_file_info["path"]):
                    dialog.after(0, lambda: status_lbl.config(text="[2/3] 正在执行订阅更新 (拉取最新节点)...", fg="#38bdf8"))
                    self.log("正在执行订阅更新拉取...")
                    up_ok, up_msg, content_changed = self.update_remote_subscription(cur_file_info["path"])
                    if up_ok:
                        new_nodes, new_details = self.extract_nodes_and_details_from_file(cur_file_info["path"])
                        if new_nodes:
                            self.all_nodes = new_nodes
                            self.node_details.update(new_details)
                            cur_file_info["nodes"] = new_nodes
                            cur_file_info["details"] = new_details
                            b_cnt = self.auto_filter_and_blacklist_non_asia_nodes()
                            if b_cnt > 0:
                                logs_step.append(f"🛡️ 自动拉黑非亚洲节点: 已直接拉黑淘汰 {b_cnt} 个非亚洲节点")
                            if target == "fav":
                                self.align_favorites_with_current_subscription()
                                self.deduplicate_favorites_by_endpoint()
                        logs_step.append(f"✅ 订阅更新: {up_msg}")
                        self.log(f"订阅更新成功: {up_msg}")
                    else:
                        logs_step.append(f"⚠️ 订阅更新: {up_msg}")
                        self.log(f"订阅更新提示: {up_msg}")
                else:
                    logs_step.append("ℹ️ 订阅更新: 未检测到远程订阅文件，跳过拉取")

                # 步骤 3: 写入 Script.js 并触发热键热更新激活订阅
                dialog.after(0, lambda: status_lbl.config(text="[3/3] 正在写入 Script.js 并热激活订阅...", fg="#38bdf8"))
                write_ok, write_err = self.do_write_script_file(list(self.favorites))
                if write_ok:
                    logs_step.append("✅ 脚本规则: 已重新生成并写入 Script.js 注入规则")
                else:
                    logs_step.append(f"⚠️ 脚本规则: {write_err}")

                time.sleep(0.3)
                hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()
                if hotkey_ok:
                    logs_step.append("✅ 热更激活: 已通过全局热键 (Ctrl+Shift+F12) 激活订阅")
                else:
                    logs_step.append(f"⚠️ 热更激活: {hotkey_msg}")

                # 探测内核重载
                if cur_file_info and self.all_nodes:
                    dialog.after(0, lambda: status_lbl.config(text="正在探测 Clash 内核装载状态...", fg="#38bdf8"))
                    loaded_ok, loaded_msg = self.wait_for_kernel_reload(self.all_nodes, max_wait_sec=10)
                    logs_step.append(f"{'✅' if loaded_ok else '⚠️'} 内核探测: {loaded_msg}")
                    self.log(f"内核探测反馈: {loaded_msg}")

                # 刷新 UI
                self.root.after(0, self.refresh_tables)
                self.root.after(0, self.refresh_verified_table)
                self.root.after(0, self.refresh_stars_table)

                def _finish_ui():
                    btn_import_fav.config(state="normal")
                    btn_import_verified.config(state="normal")
                    btn_import_stars.config(state="normal")
                    status_lbl.config(text=f"收编与热激活完成！共收编 {cnt} 个 IP", fg=THEME["accent_green"])
                    self.status_label.config(text=f"C段收编完成：已成功收编 {cnt} 个 IP 至 {target_name} 并完成热更激活")
                    messagebox.showinfo(
                        "收编与热激活成功",
                        f"🎉 批量收编与热更新全流程已顺利完成！\n\n" + "\n".join(logs_step) + "\n\n软件与 Clash Verge 已成功读取并装载最新的节点与订阅！",
                        parent=dialog
                    )

                dialog.after(0, _finish_ui)

            threading.Thread(target=_post_import_worker, daemon=True).start()

        btn_start = create_modern_btn(bottom_f, text="🚀 开始极速挖掘", command=_start_mining, bg=THEME["accent_green"], hover_bg=THEME["accent_green_hover"])
        btn_start.pack(side=tk.LEFT, padx=4)

        btn_stop = create_modern_btn(bottom_f, text="⏹ 停止", command=_stop_mining, bg=THEME["bg_hover"], hover_bg=THEME["accent_red"], state="disabled")
        btn_stop.pack(side=tk.LEFT, padx=4)

        btn_import_stars = create_modern_btn(bottom_f, text="📥 批量导入至【🏆 典藏管理池】", command=lambda: _import_to_pool("stars"), bg="#b45309", hover_bg="#d97706")
        btn_import_stars.pack(side=tk.RIGHT, padx=4)

        btn_import_verified = create_modern_btn(bottom_f, text="📥 批量导入至【⏳ 沉淀孵化池】", command=lambda: _import_to_pool("verified"), bg=THEME["accent_cyan"], hover_bg=THEME["accent_cyan_hover"])
        btn_import_verified.pack(side=tk.RIGHT, padx=4)

        btn_import_fav = create_modern_btn(bottom_f, text="📥 批量导入至【⭐ 优质精选池】", command=lambda: _import_to_pool("fav"), bg=THEME["accent_blue"], hover_bg=THEME["accent_blue_hover"])
        btn_import_fav.pack(side=tk.RIGHT, padx=4)

    # ==================== ⏳ 沉淀孵化池与防漂移考核闭环 ====================
    def refresh_verified_table(self):
        if "verified" not in self.trees:
            return
        tree = self.trees["verified"]
        tree.delete(*tree.get_children())

        # 核心铁律：沉淀孵化池必须是优质精选池的严格子集（沉淀孵化 ⊆ 优质精选）
        fav_eps = {self.get_node_endpoint(f) for f in self.favorites if f and self.get_node_endpoint(f)}
        fav_eps.discard("")
        fav_eps.discard("127.0.0.1:443")
        _, bl_eps, sbl_eps, _ = self.get_pool_endpoint_sets()

        ver_removed = False
        for ep in list(self.verified_nodes.keys()):
            if (ep not in fav_eps) or (ep in self.local_blacklist) or (ep in self.speed_blacklist) or (ep in bl_eps) or (ep in sbl_eps):
                self.verified_nodes.pop(ep, None)
                ver_removed = True

        if ver_removed:
            self.save_persisted_config()

        reverse_map = self.resolve_star_matches()
        now = time.time()

        for ep, item in self.verified_nodes.items():
            rem = item.get("remark", "")
            d_val = item.get("delay", None)
            s_val = item.get("speed", None)
            c_val = item.get("colo")
            colo_str = c_val if (c_val and c_val != "-") else self.node_colo.get(ep, "-")

            matched_name = reverse_map.get(ep, "")
            if not matched_name and ":" in ep:
                matched_name = reverse_map.get(ep.split(":")[0], "未在当前订阅匹配")
            elif not matched_name:
                matched_name = "未在当前订阅匹配"
            item["matched_name"] = matched_name

            colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep, []), now, node_name=matched_name)[3]

            d_str = f"{d_val} ms" if (d_val is not None and d_val < 99999) else ("超时" if d_val == 99999 else "-")
            s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else "-"

            first_seen = item.get("first_seen", now)
            hours_alive = round((now - first_seen) / 3600.0, 1)
            time_str = f"已存活 {hours_alive}h"

            passes = item.get("passes", 0)
            fails = item.get("fails", 0)
            stats_str = f"达标 {passes} 次 / 失败 {fails} 次"

            reason_str = item.get("reason", "")
            if not reason_str:
                if passes > 1:
                    reason_str = f"考核留任 (达标{passes}次/{hours_alive}h)"
                else:
                    reason_str = "优选初筛建档 (第1次达标)"

            tags = ["fav"] if passes >= 3 else []
            tree.insert("", tk.END, values=(ep, colo_str, colo_hist_str, reason_str, rem, d_str, s_str, time_str, stats_str, matched_name), tags=tags)


        self.notebook.tab(2, text=f"⏳ 沉淀孵化 ({len(self.verified_nodes)})")

    def process_verified_lifecycle(self, current_favs, stars_nodes=None):
        try:
            h_val = float(self.incubate_hours_var.get().strip())
        except Exception:
            h_val = 24.0
        try:
            p_val = int(self.incubate_passes_var.get().strip())
        except Exception:
            p_val = 5

        process_verified_lifecycle(
            self.verified_nodes,
            current_favs,
            self.stars_nodes if stars_nodes is None else stars_nodes,
            incubate_hours=h_val,
            incubate_passes=p_val,
        )
        self.save_persisted_config()

    def pull_verified_from_cloud(self):
        base_url = self.cf_worker_url_var.get().strip().rstrip("/")
        if not base_url.startswith("http"):
            messagebox.showwarning("提示", "请在上方配置有效的 Cloudflare Worker 地址！")
            return

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text="正在从 Cloudflare 拉取 /verified.txt..."))
            self.log("正在从 Cloudflare /verified.txt 拉取沉淀节点...")
            mixed_port = self.get_clash_mixed_port()
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

            try:
                req = urllib.request.Request(f"{base_url}/verified.txt", headers={"User-Agent": "ClashVergeNodeAssistant/1.0"})
                with opener.open(req, timeout=10) as resp:
                    raw_text = resp.read().decode("utf-8", errors="ignore")

                fav_eps = {self.get_node_endpoint(f) for f in self.favorites if f and self.get_node_endpoint(f)}
                fav_eps.discard("")
                fav_eps.discard("127.0.0.1:443")

                now = time.time()
                for line in raw_text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("⏳") or line.startswith("Error"):
                        continue
                    if "#" in line:
                        parts = line.split("#", 1)
                        ep = parts[0].strip()
                        rem = parts[1].strip()
                    else:
                        ep = line
                        rem = "优质沉淀"

                    # 严格层级规则：沉淀孵化池必须是优质精选池的严格子集！不在精选池的一律拒绝纳入
                    if ep not in fav_eps:
                        continue

                    if not (self.is_asian_node(ep) or (rem and self.is_asian_node(rem))):
                        self.local_blacklist.add(ep)
                        continue

                    if ep not in self.verified_nodes:
                        self.verified_nodes[ep] = {
                            "endpoint": ep,
                            "colo": "-",
                            "remark": rem,
                            "first_seen": now,
                            "passes": 1,
                            "fails": 0,
                            "delay": None,
                            "speed": None,
                            "reason": "云端同步拉取",
                        }

                self.purge_invalid_and_blacklisted_from_all_pools()
                self.save_persisted_config()
                self.root.after(0, self.refresh_verified_table)
                self.log(f"成功从云端同步沉淀节点，当前总计 {len(self.verified_nodes)} 个")
                self.root.after(0, lambda: messagebox.showinfo("同步成功", f"🎉 成功拉取云端沉淀节点！当前池内共 {len(self.verified_nodes)} 个。"))
                self.root.after(0, lambda: self.status_label.config(text="沉淀节点拉取成功"))
            except Exception as ex:
                self.log(f"拉取 /verified.txt 失败: {str(ex)}")
                self.root.after(0, lambda: messagebox.showerror("拉取失败", f"无法获取沉淀数据：\n{str(ex)}"))

        threading.Thread(target=_worker, daemon=True).start()

    def manual_push_verified_to_cloud(self):
        lines = [f"{v['endpoint']}#{v['remark']}" for v in self.verified_nodes.values()]
        payload = "\r\n".join(lines) + "\r\n"

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text="正在推送沉淀池到 /verified.txt..."))
            ok, msg = self.push_text_to_cf_worker(payload, "/verified.txt")
            if ok:
                self.log("手动同步沉淀池至 /verified.txt 成功")
                self.root.after(0, lambda: messagebox.showinfo("同步成功", "🎉 沉淀池节点已成功发布至 /verified.txt！"))
                self.root.after(0, lambda: self.status_label.config(text="沉淀池同步成功"))
            else:
                self.log(f"手动同步沉淀池失败: {msg}")
                self.root.after(0, lambda: messagebox.showerror("同步失败", f"推送失败：{msg}"))

        threading.Thread(target=_worker, daemon=True).start()

    def delete_selected_verified(self):
        tree = self.trees["verified"]
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要移除的沉淀节点！")
            return
        if messagebox.askyesno("删除确认", f"确定从沉淀孵化池移除选中的 {len(sels)} 个节点吗？"):
            for s in sels:
                ep = tree.item(s, "values")[0]
                self.verified_nodes.pop(ep, None)
            self.save_persisted_config()
            self.refresh_verified_table()
            self.log(f"已从沉淀池手动移除 {len(sels)} 个节点")

    def force_promote_verified_to_stars(self):
        tree = self.trees["verified"]
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要提前加冕的节点！")
            return

        cnt = 0
        existing_eps = {s.get("endpoint") for s in self.stars_nodes}
        for s in sels:
            ep = tree.item(s, "values")[0]
            if ep in self.verified_nodes and ep not in existing_eps:
                v = self.verified_nodes[ep]
                self.stars_nodes.append({
                    "endpoint": ep,
                    "colo": v.get("colo", "-"),
                    "remark": f"{v.get('remark', '')} [手动加冕]",
                    "delay": v.get("delay"),
                    "speed": v.get("speed"),
                    "matched_name": v.get("matched_name", ""),
                    "reason": f"沉淀池提前加冕 (已达标{v.get('passes', 0)}次)",
                })
                existing_eps.add(ep)
                cnt += 1

        self.save_persisted_config()
        self.refresh_stars_table()
        self.log(f"手动加冕 {cnt} 个沉淀节点至 🏆 典藏常青池")
        messagebox.showinfo("加冕成功", f"🎉 已将选中的 {cnt} 个节点直接移入 🏆 典藏常青池！")

    # ==================== 🏆 典藏常青池专属业务 ====================
    def refresh_stars_table(self):
        if "stars" not in self.trees:
            return
        tree = self.trees["stars"]
        tree.delete(*tree.get_children())

        reverse_map = self.resolve_star_matches()
        now = time.time()

        for item in self.stars_nodes:
            ep = item.get("endpoint", "")
            rem = item.get("remark", "")
            d_val = item.get("delay", None)
            s_val = item.get("speed", None)
            c_val = item.get("colo")
            colo_str = c_val if (c_val and c_val != "-") else self.node_colo.get(ep, "-")

            matched_name = reverse_map.get(ep, "")
            if not matched_name and ":" in ep:
                matched_name = reverse_map.get(ep.split(":")[0], "未在当前订阅匹配")
            elif not matched_name:
                matched_name = "未在当前订阅匹配"
            item["matched_name"] = matched_name

            colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep, []), now, node_name=matched_name)[3]

            d_str = f"{d_val} ms" if (d_val is not None and d_val < 99999) else ("超时" if d_val == 99999 else "-")
            s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else "-"

            reason_str = item.get("reason", "")
            if not reason_str:
                if "加冕" in rem:
                    reason_str = "沉淀池提前加冕"
                elif "手动" in rem or "录入" in rem:
                    reason_str = "手动录入典藏"
                else:
                    reason_str = "考核通关晋升 (长效极稳)"

            tags = ["fav"] if matched_name != "未在当前订阅匹配" else ["offline"]
            tree.insert("", tk.END, values=(ep, colo_str, colo_hist_str, reason_str, rem, d_str, s_str, matched_name), tags=tags)


        self.notebook.tab(3, text=f"🏆 典藏管理 ({len(self.stars_nodes)})")

    def pull_stars_from_cloud(self):
        base_url = self.cf_worker_url_var.get().strip().rstrip("/")
        if not base_url.startswith("http"):
            messagebox.showwarning("提示", "请在上方配置有效的 Cloudflare Worker 地址！")
            return

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text="正在从 Cloudflare 根目录拉取典藏常青节点..."))
            self.log("正在从 Cloudflare 根地址拉取典藏节点...")
            mixed_port = self.get_clash_mixed_port()
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

            try:
                req = urllib.request.Request(f"{base_url}/", headers={"User-Agent": "ClashVergeNodeAssistant/1.0"})
                with opener.open(req, timeout=10) as resp:
                    raw_text = resp.read().decode("utf-8", errors="ignore")

                new_stars = []
                for line in raw_text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("⏳") or line.startswith("Error"):
                        continue
                    if "#" in line:
                        parts = line.split("#", 1)
                        ep = parts[0].strip()
                        rem = parts[1].strip()
                    else:
                        ep = line
                        rem = "典藏节点"
                    new_stars.append({"endpoint": ep, "colo": "-", "remark": rem, "delay": None, "speed": None, "reason": "云端根目录同步"})

                self.stars_nodes = new_stars
                self.save_persisted_config()
                self.root.after(0, self.refresh_stars_table)
                self.log(f"成功拉取到 {len(new_stars)} 个云端典藏节点！")
                self.root.after(0, lambda: messagebox.showinfo("拉取成功", f"🎉 成功从云端拉取并同步 {len(new_stars)} 个典藏常青节点！"))
                self.root.after(0, lambda: self.status_label.config(text=f"成功拉取 {len(new_stars)} 个典藏节点"))
            except Exception as ex:
                self.log(f"从云端拉取典藏失败: {str(ex)}")
                self.root.after(0, lambda: messagebox.showerror("拉取失败", f"无法从云端获取典藏数据：\n{str(ex)}"))
                self.root.after(0, lambda: self.status_label.config(text="拉取云端典藏失败"))

        threading.Thread(target=_worker, daemon=True).start()

    def manual_push_stars_to_cloud(self):
        if not self.stars_nodes:
            if not messagebox.askyesno("确认推送", "当前典藏列表为空，推送将清空云端典藏池，确定继续吗？"):
                return

        lines = [f"{item.get('endpoint', '')}#{item.get('remark', '')}" for item in self.stars_nodes]
        payload = "\r\n".join(lines) + "\r\n"

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text="正在手动同步典藏常青池到 Cloudflare 根目录..."))
            ok, msg = self.push_text_to_cf_worker(payload, "")
            if ok:
                self.log(f"已手动将 {len(self.stars_nodes)} 个典藏常青节点同步到 Worker 根地址")
                self.root.after(0, lambda: messagebox.showinfo(
                    "同步成功",
                    f"🎉 成功同步！\n\n共 {len(self.stars_nodes)} 个极品节点已发布至 Worker 根目录，你的 Pages 订阅源已即时生效！"
                ))
                self.root.after(0, lambda: self.status_label.config(text=f"已成功同步 {len(self.stars_nodes)} 个典藏节点"))
            else:
                self.log(f"手动推送典藏失败: {msg}")
                self.root.after(0, lambda: messagebox.showerror("推送失败", f"推送发生错误：\n{msg}"))

        threading.Thread(target=_worker, daemon=True).start()

    def edit_selected_star_remark(self):
        tree = self.trees["stars"]
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先在列表中选中需要修改备注的典藏节点！")
            return
        ep = tree.item(sel[0], "values")[0]
        curr_item = next((s for s in self.stars_nodes if s.get("endpoint") == ep), None)
        if not curr_item:
            curr_item = self.stars_nodes[tree.index(sel[0])]
        old_rem = curr_item.get("remark", "")

        new_rem = simpledialog.askstring("修改备注", f"修改节点 [{curr_item.get('endpoint')}] 的备注信息：", initialvalue=old_rem)
        if new_rem is not None:
            curr_item["remark"] = new_rem.strip()
            self.save_persisted_config()
            self.refresh_stars_table()
            self.log(f"已修改典藏节点 [{curr_item.get('endpoint')}] 备注为: {new_rem.strip()}")

    def delete_selected_stars(self):
        tree = self.trees["stars"]
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要删除的典藏节点！")
            return
        if messagebox.askyesno("删除确认", f"确定从本地典藏池移除选中的 {len(sels)} 个节点吗？\n（注：点击保存上传前云端数据不会变动）"):
            sel_eps = {tree.item(s, "values")[0] for s in sels}
            self.stars_nodes = [s for s in self.stars_nodes if s.get("endpoint") not in sel_eps]
            self.save_persisted_config()
            self.refresh_stars_table()
            self.log(f"已从典藏池移除 {len(sels)} 个节点")

    def promote_selected_to_stars(self):
        tree = self.get_current_tree()
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要晋升为典藏的节点！")
            return

        added_cnt = 0
        existing_eps = {item.get("endpoint") for item in self.stars_nodes}

        for s in sels:
            node_name = tree.item(s, "values")[-1]
            if not self.is_asian_node(node_name):
                self.local_blacklist.add(node_name)
                continue
            ep = self.get_node_endpoint(node_name)
            if ep in existing_eps:
                continue

            region = self.node_colo.get(node_name, detect_node_region(node_name))
            spd = self.node_speeds.get(node_name, 0.0)
            rem = f"{region} [典藏] {spd:.2f} MB/s" if spd > 0 else f"{region} [典藏常青]"

            self.stars_nodes.append({
                "endpoint": ep,
                "colo": self.node_colo.get(node_name, "-"),
                "remark": rem,
                "delay": self.node_delays.get(node_name),
                "speed": self.node_speeds.get(node_name),
                "matched_name": node_name,
                "reason": "手动晋升典藏",
            })
            existing_eps.add(ep)
            added_cnt += 1

        self.save_persisted_config()
        self.refresh_stars_table()
        self.log(f"已成功将 {added_cnt} 个节点加冕至【🏆 典藏管理】池")
        messagebox.showinfo("晋升成功", f"🎉 已将 {added_cnt} 个极品节点加入典藏常青池！\n可前往【🏆 典藏管理】标签页查看、测速或点击手动上传。")

    def open_import_stars_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("手动填写 / 批量导入典藏节点")
        dialog.geometry("620x500")
        dialog.configure(bg=THEME["bg_card"])
        dialog.transient(self.root)
        dialog.grab_set()

        lbl_tip = tk.Label(
            dialog,
            text="请在此直接粘贴节点信息（支持单行或多行批量）：\n格式支持：IP:端口#备注信息  或直接粘贴  IP:端口\n例如：104.18.33.229:443#香港高速主力",
            justify=tk.LEFT,
            font=("Microsoft YaHei UI", 9),
            fg="#38bdf8",
            bg=THEME["bg_card"],
            pady=8
        )
        lbl_tip.pack(fill=tk.X, padx=16, pady=(10, 4))

        txt_frame = tk.Frame(dialog, bg=THEME["bg_main"], padx=2, pady=2)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=6)

        txt_box = tk.Text(
            txt_frame,
            bg=THEME["bg_input"],
            fg=THEME["text_main"],
            insertbackground="#38bdf8",
            relief="flat",
            bd=0,
            font=("Consolas", 10),
            wrap="none"
        )
        sb_y = ttk.Scrollbar(txt_frame, orient=tk.VERTICAL, command=txt_box.yview, style="Vertical.TScrollbar")
        txt_box.configure(yscrollcommand=sb_y.set)
        txt_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)

        btn_box = tk.Frame(dialog, bg=THEME["bg_card"], pady=10)
        btn_box.pack(fill=tk.X, padx=16)

        def _do_parse_and_add():
            raw_text = txt_box.get("1.0", tk.END).strip()
            if not raw_text:
                messagebox.showwarning("提示", "请输入或粘贴内容！", parent=dialog)
                return

            existing_eps = {item.get("endpoint") for item in self.stars_nodes}
            added = 0
            skipped_dup = 0
            invalid = 0

            for raw_line in raw_text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                if "#" in line:
                    parts = line.split("#", 1)
                    ep = parts[0].strip()
                    rem = parts[1].strip()
                else:
                    ep = line.strip()
                    rem = ""

                m = re.search(r"([a-zA-Z0-9\.\-]+:\d{1,5})", ep)
                if not m:
                    invalid += 1
                    continue

                clean_ep = m.group(1)

                if clean_ep in existing_eps:
                    skipped_dup += 1
                    continue

                if not rem:
                    reg = detect_node_region(clean_ep)
                    rem = f"{reg} [手动录入]"

                if not (self.is_asian_node(rem) or self.is_asian_node(clean_ep)):
                    self.local_blacklist.add(clean_ep)
                    continue

                self.stars_nodes.append({
                    "endpoint": clean_ep,
                    "colo": "-",
                    "remark": rem,
                    "delay": None,
                    "speed": None,
                    "matched_name": "",
                    "reason": "手动录入典藏",
                })
                existing_eps.add(clean_ep)
                added += 1

            self.save_persisted_config()
            self.refresh_stars_table()
            self.log(f"手动录入典藏节点：成功添加 {added} 个，跳过重复 {skipped_dup} 个，格式无效 {invalid} 个")

            msg = f"录入结果汇总：\n\n• 成功添加：{added} 个\n• 跳过重复：{skipped_dup} 个"
            if invalid > 0:
                msg += f"\n• 格式无效：{invalid} 个"
            messagebox.showinfo("录入完成", msg, parent=dialog)
            dialog.destroy()

        create_modern_btn(
            btn_box,
            text="✅ 立即识别并添加进典藏",
            command=_do_parse_and_add,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"],
            padx=16,
            pady=6
        ).pack(side=tk.RIGHT, padx=6)

        create_modern_btn(
            btn_box,
            text="取消",
            command=dialog.destroy,
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            padx=12,
            pady=6
        ).pack(side=tk.RIGHT, padx=6)

    def test_stars_pipeline(self, mode="delay"):
        tree = self.trees["stars"]
        sels = tree.selection()
        if sels:
            ep_map = {s.get("endpoint"): s for s in self.stars_nodes}
            targets = [ep_map[tree.item(s, "values")[0]] for s in sels if tree.item(s, "values")[0] in ep_map]
        else:
            targets = self.stars_nodes

        if not targets:
            messagebox.showinfo("提示", "当前典藏池没有节点！")
            return

        self.refresh_stars_table()

        testable = [t for t in targets if t.get("matched_name") and t.get("matched_name") != "未在当前订阅匹配"]
        if not testable:
            messagebox.showwarning(
                "未在内核中找到代理",
                "所选典藏节点尚未在 Clash 内核中找到对应的完整代理配置！\n\n"
                "【解决步骤】：\n"
                "1. 请先点击右侧【💾 保存并推送根目录 /】；\n"
                "2. 确保在 Clash Verge 中已添加并更新了您的 Pages 订阅链接（源自 Worker 根地址）；\n"
                "3. 在 Clash Verge 中激活该订阅后，回到此处点击【🔄 拉取云端】刷新状态，即可正常测速！"
            )
            return

        test_url = self.test_url_var.get().strip()
        speed_url = self.speed_url_var.get().strip()

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text=f"正在对 {len(testable)} 个典藏节点测试{mode}..."))
            self.log(f"开始测试 {len(testable)} 个典藏节点 (模式: {mode})...")

            if mode == "delay":
                for item in testable:
                    name = item["matched_name"]
                    enc_name = urllib.parse.quote(name, safe="")
                    enc_url = urllib.parse.quote(test_url, safe="")
                    res = self._call_api(f"/proxies/{enc_name}/delay?timeout=1500&url={enc_url}", timeout=2.2)
                    d_val = res["delay"] if (res and "delay" in res) else 99999
                    item["delay"] = d_val
                    ep_raw = item.get("endpoint", "")
                    if ":" in ep_raw:
                        s_ip, s_p = ep_raw.split(":", 1)
                        c_code, c_disp = get_cf_colo_raw(s_ip, s_p)
                        self.record_colo_sample(name, ep_raw, c_code, c_disp)
                        item["colo"] = c_disp
                    self.root.after(0, self.refresh_stars_table)
                self.log("典藏节点延迟测速完成")
            else:
                mode_guard = ClashModeGuard(self.clash_client, temporary_mode="global")
                mode_guard.__enter__()
                mixed_port = self.get_clash_mixed_port()
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

                proxy_handler = urllib.request.ProxyHandler({
                    "http": f"http://127.0.0.1:{mixed_port}",
                    "https": f"http://127.0.0.1:{mixed_port}",
                })
                speed_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

                try:
                    for item in testable:
                        name = item["matched_name"]
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self._call_api(f"/proxies/{enc_glb}", method="PUT", data=json.dumps({"name": name}).encode("utf-8"))
                        time.sleep(0.1)

                        speed_val = 0.0
                        total_bytes = 0
                        stars_deadline = time.time() + 3.5
                        try:
                            req = urllib.request.Request(speed_url, headers={"User-Agent": "Mozilla/5.0", "Connection": "close"})
                            with speed_opener.open(req, timeout=2.5) as resp:
                                st = time.time()
                                chunk_size = 16 * 1024
                                while time.time() - st < 2.5:
                                    if time.time() >= stars_deadline:
                                        break
                                    ch = resp.read(chunk_size)
                                    if not ch:
                                        break
                                    total_bytes += len(ch)
                                el = time.time() - st
                                speed_val = round((total_bytes / (1024 * 1024)) / el, 2) if (el > 0 and total_bytes > 0) else 0.0
                        except Exception:
                            speed_val = -1.0

                        item["speed"] = speed_val
                        self.root.after(0, self.refresh_stars_table)
                finally:
                    mode_guard.__exit__(None, None, None)

                self.log("典藏节点下行测速完成")

            self.save_persisted_config()
            self.root.after(0, lambda: self.status_label.config(text="典藏节点测速完毕"))

        threading.Thread(target=_worker, daemon=True).start()

    # ==================== 右键菜单 (支持 C 段溯源) ====================

    def test_selected_node_colo(self):
        tree = self.get_current_tree()
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要测试 Colo 的节点！")
            return
        
        row_vals = tree.item(sels[0], "values")
        current_tab_idx = self.notebook.index(self.notebook.select())
        if current_tab_idx in [2, 3]: # 沉淀孵化池 或 典藏管理池
            endpoint = row_vals[0]
            node_name = row_vals[-1] if (len(row_vals) >= 8 and row_vals[-1] != "未在当前订阅匹配") else ""
        else:
            node_name = row_vals[-1]
            endpoint = self.get_node_endpoint(node_name)
        
        if not endpoint and node_name and ":" in node_name:
            endpoint = node_name
        if not endpoint or ":" not in endpoint:
            messagebox.showwarning("提示", f"无法从【{endpoint or node_name}】中提取有效的 IP:端口！")
            return
            
        ip, port = endpoint.split(":", 1)
        target_iid = sels[0]
        
        def _worker():
            self.root.after(0, lambda: self.status_label.config(text=f"正在测试 {ip}:{port} 的实时 Colo..."))
            self.log(f"开始测试节点/IP [{ip}:{port}] 的实时机房 (Colo)...")
            
            c_code, c_disp = get_cf_colo_raw(ip, port, timeout=2.5)
            
            n_key = node_name if node_name else None
            self.record_colo_sample(n_key, endpoint, c_code, c_disp)

            colo_hist = self.node_colo_history.get(endpoint, self.node_colo_history.get(n_key, []))
            _, _, has_drift, drift_disp = self.analyze_colo_stats(colo_hist, time.time(), node_name=n_key)
            if has_drift:
                reason = f"机房漂移 ({drift_disp})"
                if n_key:
                    self.local_blacklist.add(n_key)
                    self.favorites.discard(n_key)
                    self.record_blacklist_reason(n_key, reason)
                if endpoint:
                    self.local_blacklist.add(endpoint)
                    self.record_blacklist_reason(endpoint, reason)
                    if endpoint in self.verified_nodes:
                        del self.verified_nodes[endpoint]
                self.purge_invalid_and_blacklisted_from_all_pools()
                self.do_write_script_file(list(self.favorites))
                trigger_verge_reactivate_hotkey()
                if self.get_cf_worker_config()[0]:
                    self.sync_all_pools_to_cf_worker()
                msg = f"节点/IP: {ip}:{port}\n实时机房 (Colo): {c_disp}\n\n⚠️【严苛规则触发：机房漂移 ({drift_disp})】\n该节点已按规则直接加入延迟黑名单淘汰，并已从优质精选池及远端 Worker 清除！"
                self.log(f"【漂移直接淘汰】{n_key or endpoint} 发生机房漂移 ({drift_disp})，直接拉黑淘汰并同步远端！")
            else:
                msg = f"节点/IP: {ip}:{port}\n实时机房 (Colo): {c_disp}"

            self.save_persisted_config()

            def _update_ui():
                # 1. 优先就地实时更新当前选中行的界面展示 (Colo 与 Colo稳定性)
                try:
                    if tree.exists(target_iid):
                        curr_vals = list(tree.item(target_iid, "values"))
                        if len(curr_vals) > 2:
                            curr_vals[1] = c_disp
                            curr_vals[2] = drift_disp
                            tree.item(target_iid, values=curr_vals)
                except Exception:
                    pass

                # 2. 全量刷新表格以联动所有相关池
                self.refresh_tables()
                self.refresh_verified_table()
                self.refresh_stars_table()
                if current_tab_idx == 4 and hasattr(self, "_render_delay_black_table"):
                    self._render_delay_black_table()
                elif current_tab_idx == 5 and hasattr(self, "_render_speed_black_table"):
                    self._render_speed_black_table()

                # 3. 刷新后尝试重新高亮定位该节点
                try:
                    for item_id in tree.get_children():
                        v = tree.item(item_id, "values")
                        if v and (v[0] == endpoint or (len(v) > 10 and v[10] == node_name) or (len(v) > 7 and v[-1] == node_name)):
                            tree.selection_set(item_id)
                            tree.focus(item_id)
                            tree.see(item_id)
                            break
                except Exception:
                    pass

                self.status_label.config(text=f"Colo 测试完成: {c_disp}")
                messagebox.showinfo("Colo 测试结果", msg)

            self.root.after(0, _update_ui)
            self.log(f"Colo 测试结果 -> {ip}:{port} : {c_disp}")
            
        threading.Thread(target=_worker, daemon=True).start()

    def clear_selected_node_colo_history(self):
        """清空右键选中的特定节点的机房(Colo)信息与历史"""
        tree = self.get_current_tree()
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要清空机房(Colo)记录的节点！")
            return

        current_tab_idx = self.notebook.index(self.notebook.select())
        cleared_cnt = 0
        for s in sels:
            row_vals = tree.item(s, "values")
            if not row_vals:
                continue
            if current_tab_idx in [2, 3]:
                ep = row_vals[0]
                n_key = row_vals[-1] if len(row_vals) >= 7 else ""
            else:
                n_key = row_vals[-1]
                ep = self.get_node_endpoint(n_key)

            keys_to_clean = [n_key, ep]
            if ep and ":" in ep:
                keys_to_clean.append(ep.split(":")[0])
            for k in keys_to_clean:
                if k and k != "-":
                    self.node_colo.pop(k, None)
                    self.node_colo_history.pop(k, None)

            if ep in self.verified_nodes:
                self.verified_nodes[ep]["colo"] = "-"
            for s_node in self.stars_nodes:
                if s_node.get("endpoint") == ep or (n_key and s_node.get("matched_name") == n_key):
                    s_node["colo"] = "-"
            cleared_cnt += 1

        self.save_persisted_config()
        self.refresh_tables()
        self.refresh_verified_table()
        self.refresh_stars_table()
        self.log(f"已清空选中的 {cleared_cnt} 个节点的机房(Colo)历史记录。")
        self.status_label.config(text=f"已清空选中的 {cleared_cnt} 个节点机房记录")

    def setup_context_menus(self):
        self.all_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.all_menu.add_command(label="⭐ 设为优质", command=self.set_favorite)
        self.all_menu.add_command(label="🏆 测速计分并晋升", command=lambda: self.rescore_and_promote_selected(self.trees["all"]))
        self.all_menu.add_command(label="🏆 晋升 / 加入典藏常青池", command=self.promote_selected_to_stars)
        self.all_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["all"]))
        self.all_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.all_menu.add_command(label="🧹 清空所选节点Colo历史", command=self.clear_selected_node_colo_history)
        self.all_menu.add_separator()
        self.all_menu.add_command(label="↩ 移出黑名单 (恢复待测)", command=lambda: self.remove_from_blacklist(self.trees["all"]))
        self.all_menu.add_command(label="🚫 延迟拉黑", command=self.manual_add_delay_blacklist)
        self.all_menu.add_command(label="🐌 低速拉黑", command=self.manual_add_speed_blacklist)

        def _on_all_right_click(event):
            tree = self.trees["all"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.all_menu.post(event.x_root, event.y_root)

        self.trees["all"].bind("<Button-3>", _on_all_right_click)

        self.fav_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.fav_menu.add_command(label="🏆 测速计分并晋升", command=lambda: self.rescore_and_promote_selected(self.trees["fav"]))
        self.fav_menu.add_command(label="🏆 晋升 / 加入典藏常青池", command=self.promote_selected_to_stars)
        self.fav_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["fav"]))
        self.fav_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.fav_menu.add_command(label="🧹 清空所选节点Colo历史", command=self.clear_selected_node_colo_history)
        self.fav_menu.add_separator()
        self.fav_menu.add_command(label="↩ 移出黑名单 (恢复待测)", command=lambda: self.remove_from_blacklist(self.trees["fav"]))
        self.fav_menu.add_command(label="🚫 延迟拉黑", command=self.manual_add_delay_blacklist)
        self.fav_menu.add_command(label="🐌 低速拉黑", command=self.manual_add_speed_blacklist)

        def _on_fav_right_click(event):
            tree = self.trees["fav"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.fav_menu.post(event.x_root, event.y_root)

        self.trees["fav"].bind("<Button-3>", _on_fav_right_click)

        self.delay_black_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.delay_black_menu.add_command(label="↩ 移出延迟黑名单 (恢复待测)", command=lambda: self.remove_from_blacklist(self.trees["delay_black"]))
        self.delay_black_menu.add_command(label="⭐ 移出黑名单并设为优质", command=lambda: self.remove_from_blacklist_and_set_favorite(self.trees["delay_black"]))
        self.delay_black_menu.add_command(label="🏆 移出并测速计分晋升", command=lambda: self.rescore_and_promote_selected(self.trees["delay_black"]))
        self.delay_black_menu.add_command(label="🏆 移出并直接晋升典藏", command=self.promote_selected_to_stars)
        self.delay_black_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["delay_black"]))
        self.delay_black_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.delay_black_menu.add_separator()
        self.delay_black_menu.add_command(label="🧹 清空当前延迟黑名单", command=self.clear_delay_blacklist)
        self.delay_black_menu.add_command(label="🧹 一键清空全部黑名单", command=self.clear_all_blacklists)

        def _on_delay_black_right_click(event):
            tree = self.trees["delay_black"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.delay_black_menu.post(event.x_root, event.y_root)

        self.trees["delay_black"].bind("<Button-3>", _on_delay_black_right_click)

        self.speed_black_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.speed_black_menu.add_command(label="↩ 移出低速黑名单 (恢复待测)", command=lambda: self.remove_from_blacklist(self.trees["speed_black"]))
        self.speed_black_menu.add_command(label="⭐ 移出黑名单并设为优质", command=lambda: self.remove_from_blacklist_and_set_favorite(self.trees["speed_black"]))
        self.speed_black_menu.add_command(label="🏆 移出并测速计分晋升", command=lambda: self.rescore_and_promote_selected(self.trees["speed_black"]))
        self.speed_black_menu.add_command(label="🏆 移出并直接晋升典藏", command=self.promote_selected_to_stars)
        self.speed_black_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["speed_black"]))
        self.speed_black_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.speed_black_menu.add_separator()
        self.speed_black_menu.add_command(label="🧹 清空当前低速黑名单", command=self.clear_speed_blacklist)
        self.speed_black_menu.add_command(label="🧹 一键清空全部黑名单", command=self.clear_all_blacklists)

        def _on_speed_black_right_click(event):
            tree = self.trees["speed_black"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.speed_black_menu.post(event.x_root, event.y_root)

        self.trees["speed_black"].bind("<Button-3>", _on_speed_black_right_click)

        self.stars_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.stars_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["stars"]))
        self.stars_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.stars_menu.add_command(label="🧹 清空所选节点Colo历史", command=self.clear_selected_node_colo_history)
        self.stars_menu.add_command(label="✏️ 修改备注", command=self.edit_selected_star_remark)
        self.stars_menu.add_command(label="🗑️ 移除此典藏", command=self.delete_selected_stars)

        def _on_stars_right_click(event):
            tree = self.trees["stars"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.stars_menu.post(event.x_root, event.y_root)

        self.trees["stars"].bind("<Button-3>", _on_stars_right_click)

        self.verified_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.verified_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["verified"]))
        self.verified_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.verified_menu.add_command(label="🧹 清空所选节点Colo历史", command=self.clear_selected_node_colo_history)
        self.verified_menu.add_command(label="🏆 提前加冕至典藏", command=self.force_promote_verified_to_stars)
        self.verified_menu.add_command(label="🗑️ 移除沉淀", command=self.delete_selected_verified)

        def _on_verified_right_click(event):
            tree = self.trees["verified"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.verified_menu.post(event.x_root, event.y_root)

        self.trees["verified"].bind("<Button-3>", _on_verified_right_click)

    def _trigger_c_mining_from_tree(self, tree):
        sel = tree.selection()
        if not sel:
            return
        row_vals = tree.item(sel[0], "values")
        if tree in [self.trees.get("verified"), self.trees.get("stars")]:
            target_str = row_vals[0]
        else:
            node_name = row_vals[-1]
            target_str = self.get_node_endpoint(node_name)

        self.open_c_segment_mining_dialog(target_str)

    # ==================== 界面布局与初始化 ====================
    def setup_ui(self):
        def _make_entry(parent, textvariable, width, **kwargs):
            return tk.Entry(
                parent,
                textvariable=textvariable,
                width=width,
                bg=THEME["bg_input"],
                fg=THEME["text_main"],
                insertbackground="#38bdf8",
                relief="flat",
                highlightthickness=1,
                highlightbackground=THEME["border"],
                highlightcolor=THEME["accent_blue"],
                font=("Microsoft YaHei UI", 9),
                **kwargs,
            )

        top_card = tk.Frame(
            self.root, bg=THEME["bg_card"], padx=14, pady=8, highlightthickness=1, highlightbackground=THEME["border"]
        )
        top_card.pack(fill=tk.X, padx=12, pady=(10, 5))

        tk.Label(
            top_card,
            text="当前订阅:",
            font=("Microsoft YaHei UI", 9, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"],
        ).pack(side=tk.LEFT)

        self.file_combo = ttk.Combobox(top_card, width=34, state="readonly")
        self.file_combo.pack(side=tk.LEFT, padx=8)
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_changed)

        create_modern_btn(
            top_card,
            text="🔄 更新当前订阅",
            command=self.manual_update_subscription_and_reactivate,
            bg=THEME["bg_hover"],
            hover_bg=THEME["accent_blue"],
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.conn_label = tk.Label(
            top_card,
            text="● 正在连接内核...",
            font=("Microsoft YaHei UI", 9, "bold"),
            fg=THEME["accent_yellow"],
            bg=THEME["bg_card"],
        )
        self.conn_label.pack(side=tk.LEFT, padx=(6, 12))

        self.last_time_label = tk.Label(
            top_card,
            text="🕒 上次检测  全量: 未运行  |  复检: 未运行",
            font=("Microsoft YaHei UI", 9, "bold"),
            fg="#38bdf8",
            bg=THEME["bg_card"],
        )
        self.last_time_label.pack(side=tk.LEFT, padx=8)

        create_modern_btn(
            top_card,
            text="🗑️ 清空测速记录",
            command=lambda: self.clear_test_history(silent=False),
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
        ).pack(side=tk.RIGHT, padx=4)

        create_modern_btn(
            top_card,
            text="🧹 清当前页Colo",
            command=self.clear_current_tab_colo_history,
            bg=THEME["bg_hover"],
            hover_bg=THEME["accent_red"],
        ).pack(side=tk.RIGHT, padx=4)

        create_modern_btn(
            top_card,
            text="🌍 测当前页Colo",
            command=lambda: threading.Thread(target=self.test_all_nodes_colo, daemon=True).start(),
            bg=THEME["accent_cyan"],
            hover_bg=THEME["accent_cyan_hover"],
        ).pack(side=tk.RIGHT, padx=4)

        create_modern_btn(
            top_card,
            text="🔄 同步内核延迟",
            command=lambda: threading.Thread(target=self.sync_existing_delays, daemon=True).start(),
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
        ).pack(side=tk.RIGHT, padx=4)

        pipeline_card = tk.Frame(
            self.root, bg=THEME["bg_card"], padx=14, pady=10, highlightthickness=1, highlightbackground=THEME["border"]
        )
        pipeline_card.pack(fill=tk.X, padx=12, pady=(0, 5))

        r1 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r1.pack(fill=tk.X, pady=(0, 6))

        tk.Label(r1, text="⚡ 全局优选门槛:", fg="#38bdf8", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(r1, text="最低延迟(≤ ms):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r1, self.max_delay_threshold_var, 5).pack(side=tk.LEFT, padx=(4, 10))

        tk.Label(r1, text="优质下行(≥ MB/s):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r1, self.min_speed_threshold_var, 5).pack(side=tk.LEFT, padx=(4, 10))

        tk.Label(r1, text="🎯 达标目标(留空全测):", fg="#fbbf24", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r1, self.target_node_count_var, 4).pack(side=tk.LEFT, padx=(4, 10))

        tk.Label(r1, text="轮数:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r1, self.test_rounds_var, 3).pack(side=tk.LEFT, padx=(4, 6))

        tk.Label(r1, text="超时(ms):", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r1, self.test_timeout_var, 5).pack(side=tk.LEFT, padx=(4, 6))

        tk.Label(r1, text="采样:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r1, self.speed_duration_var, 4).pack(side=tk.LEFT, padx=(4, 2))
        tk.Label(r1, text="秒", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)

        r2 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r2.pack(fill=tk.X, pady=(0, 6))

        tk.Label(r2, text="🚫 自动拉黑规则:", fg="#f87171", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(r2, text="延迟拉黑(≥ ms):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r2, self.blacklist_threshold_var, 5).pack(side=tk.LEFT, padx=(4, 14))

        tk.Label(r2, text="低速拉黑(< MB/s):", fg="#fca5a5", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r2, self.speed_bl_threshold_var, 5).pack(side=tk.LEFT, padx=(4, 6))

        tk.Label(r2, text="连续低速次数:", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r2, self.speed_bl_rounds_var, 3).pack(side=tk.LEFT, padx=(4, 2))
        tk.Label(r2, text="次", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(r2, text="抖动基准(≥ ms):", fg="#fca5a5", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(4, 0))
        _make_entry(r2, self.jitter_min_delay_var, 4).pack(side=tk.LEFT, padx=(3, 6))

        tk.Label(r2, text="向上抖动(≥ ms):", fg="#fca5a5", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r2, self.jitter_up_threshold_var, 4).pack(side=tk.LEFT, padx=(3, 6))

        r3 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r3.pack(fill=tk.X, pady=(0, 6))

        tk.Label(r3, text="延迟源:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r3, self.test_url_var, 25).pack(side=tk.LEFT, padx=(4, 8))

        tk.Label(r3, text="带宽源:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r3, self.speed_url_var, 28).pack(side=tk.LEFT, padx=(4, 12))

        self.btn_run_pipeline = create_modern_btn(
            r3,
            text="🚀 启动一整套全自动优选与热键生效",
            command=self.start_full_auto_pipeline,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"],
        )
        self.btn_run_pipeline.pack(side=tk.LEFT, padx=3)

        self.btn_stop_pipeline = create_modern_btn(
            r3,
            text="⏹ 终止任务",
            command=self.stop_pipeline,
            bg=THEME["bg_hover"],
            hover_bg=THEME["accent_red"],
            state="disabled",
        )
        self.btn_stop_pipeline.pack(side=tk.LEFT, padx=3)

        r4 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r4.pack(fill=tk.X, pady=(0, 6))

        tk.Checkbutton(
            r4,
            text="🚀 开机静默自启",
            variable=self.boot_startup_var,
            bg=THEME["bg_card"],
            fg="#10b981",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#10b981",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=self.on_boot_toggle,
        ).pack(side=tk.LEFT, padx=(0, 12))

        tk.Checkbutton(
            r4,
            text="⏰ 启用全局定时优选 (按上次运行时间计)",
            variable=self.schedule_enabled_var,
            bg=THEME["bg_card"],
            fg="#38bdf8",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#38bdf8",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=lambda: [self._on_schedule_toggle(), self.save_persisted_config()],
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(r4, text="循环间隔(分钟):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r4, self.schedule_interval_var, 5).pack(side=tk.LEFT, padx=(4, 12))

        tk.Label(r4, text="固定时刻(HH:MM):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r4, self.schedule_times_var, 22).pack(side=tk.LEFT, padx=(4, 8))

        self.sched_status_label = tk.Label(
            r4,
            text="(全局定时未启动)",
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            font=("Microsoft YaHei UI", 9),
        )
        self.sched_status_label.pack(side=tk.LEFT, padx=6)

        r5 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r5.pack(fill=tk.X, pady=(0, 6))

        tk.Label(r5, text="⚙️ 策略组测速配置:", fg="#a78bfa", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))

        tk.Label(r5, text="常规间隔(s):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r5, self.group_interval_var, 4).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(r5, text="常规容差(ms):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r5, self.group_tolerance_var, 3).pack(side=tk.LEFT, padx=(2, 8))

        tk.Label(r5, text="典藏间隔(s):", fg="#fbbf24", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r5, self.star_group_interval_var, 4).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(r5, text="典藏容差(ms):", fg="#fbbf24", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r5, self.star_group_tolerance_var, 3).pack(side=tk.LEFT, padx=(2, 8))

        create_modern_btn(
            r5,
            text="💾 保存测速设置并热更",
            command=self.save_group_config_and_reload,
            bg=THEME["accent_purple"],
            hover_bg=THEME["accent_purple_hover"],
            pady=3,
            font_size=9,
        ).pack(side=tk.LEFT, padx=4)

        r6 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r6.pack(fill=tk.X)

        tk.Checkbutton(
            r6,
            text="☁️ 自动同步推送 Worker 三大文本 (/auto.txt, /verified.txt, /)",
            variable=self.cf_worker_enabled_var,
            bg=THEME["bg_card"],
            fg="#38bdf8",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#38bdf8",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=self.save_persisted_config,
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(r6, text="Worker 根地址:", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r6, self.cf_worker_url_var, 30).pack(side=tk.LEFT, padx=(3, 8))

        tk.Label(r6, text="授权密钥:", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r6, self.cf_worker_token_var, 15, show="*").pack(side=tk.LEFT, padx=(3, 8))

        create_modern_btn(
            r6,
            text="🧪 测试自动通道",
            command=self.test_cf_worker_upload,
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            pady=3,
            font_size=9,
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            r6,
            text="☁️ 同步auto.txt优质",
            command=lambda: self.sync_favorites_from_auto_text(show_notify=True),
            bg=THEME["accent_blue"],
            hover_bg=THEME["accent_blue_hover"],
            pady=3,
            font_size=9,
        ).pack(side=tk.LEFT, padx=3)

        tk.Label(r6, text="[典藏池:/ | 沉淀池:/verified.txt | 自动优选:/auto.txt]", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 8)).pack(side=tk.LEFT, padx=4)

        param_card = tk.Frame(
            self.root, bg=THEME["bg_card"], padx=14, pady=8, highlightthickness=1, highlightbackground=THEME["border"]
        )
        param_card.pack(fill=tk.X, padx=12, pady=(0, 8))

        tk.Label(param_card, text="端口:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(param_card, self.port_var, 6).pack(side=tk.LEFT, padx=(4, 8))

        tk.Label(param_card, text="密钥:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(param_card, self.secret_var, 14).pack(side=tk.LEFT, padx=(4, 8))

        create_modern_btn(
            param_card,
            text="重连",
            command=lambda: self.test_connection(auto_sync=False),
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            pady=3,
            font_size=8,
        ).pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(param_card, text="快速过滤:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        self.search_var.trace_add("write", lambda *args: self.refresh_tables())
        _make_entry(param_card, self.search_var, 18).pack(side=tk.LEFT, padx=(4, 10))

        self.status_label = tk.Label(
            param_card,
            text="",
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            font=("Microsoft YaHei UI", 9),
        )
        self.status_label.pack(side=tk.RIGHT)

        # 选项卡区域 (先创建实例，待底部固定栏布局完毕后再 pack 铺满剩余空间)
        self.notebook = ttk.Notebook(self.root)

        self.tab_all = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_fav = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_verified = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_stars = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_delay_black = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_speed_black = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_cloud_text = tk.Frame(self.notebook, bg=THEME["tree_bg"])

        self.notebook.add(self.tab_all, text="📋 活跃待测 (0)")
        self.notebook.add(self.tab_fav, text="⭐ 优质精选 (0)")
        self.notebook.add(self.tab_verified, text="⏳ 沉淀孵化 (0)")
        self.notebook.add(self.tab_stars, text="🏆 典藏管理 (0)")
        self.notebook.add(self.tab_delay_black, text="🚫 延迟黑名单 (0)")
        self.notebook.add(self.tab_speed_black, text="🐌 低速黑名单 (0)")
        self.notebook.add(self.tab_cloud_text, text="☁️ 云端文本查看")
        self.setup_cloud_text_ui()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_notebook_tab_changed)

        # 优质精选工具栏
        fav_tool_bar = tk.Frame(self.tab_fav, bg=THEME["bg_card"], padx=10, pady=8)
        fav_tool_bar.pack(fill=tk.X, padx=4, pady=(4, 4))

        ft_row1 = tk.Frame(fav_tool_bar, bg=THEME["bg_card"])
        ft_row1.pack(fill=tk.X, pady=(0, 6))

        tk.Label(ft_row1, text="⭐ 优质复检标准:", fg="#fbbf24", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(ft_row1, text="生效延迟(≤ ms):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row1, self.fav_max_delay_var, 4).pack(side=tk.LEFT, padx=(3, 8))

        tk.Label(ft_row1, text="生效下行(≥ MB/s):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row1, self.fav_min_speed_var, 4).pack(side=tk.LEFT, padx=(3, 8))

        tk.Label(ft_row1, text="轮数:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row1, self.fav_rounds_var, 3).pack(side=tk.LEFT, padx=(3, 6))

        tk.Label(ft_row1, text="采样:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row1, self.fav_speed_duration_var, 4).pack(side=tk.LEFT, padx=(3, 2))
        tk.Label(ft_row1, text="秒", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(ft_row1, text="抖动基准(≥ ms):", fg="#fca5a5", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(4, 0))
        _make_entry(ft_row1, self.fav_jitter_min_delay_var, 4).pack(side=tk.LEFT, padx=(3, 6))

        tk.Label(ft_row1, text="向上抖动(≥ ms):", fg="#fca5a5", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row1, self.fav_jitter_up_threshold_var, 4).pack(side=tk.LEFT, padx=(3, 8))

        create_modern_btn(
            ft_row1,
            text="⚡ 优质池双轨复检并写入",
            command=self.start_fav_review_pipeline,
            bg="#b45309",
            hover_bg="#d97706",
            font_size=9,
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            ft_row1,
            text="☁️ 同步auto.txt优质",
            command=lambda: self.sync_favorites_from_auto_text(show_notify=True),
            bg=THEME["accent_blue"],
            hover_bg=THEME["accent_blue_hover"],
            font_size=9,
        ).pack(side=tk.RIGHT, padx=3)

        create_modern_btn(
            ft_row1,
            text="⚡ 一键同步至 Verge",
            command=lambda: self.sync_favorites_to_verge(show_notify=True),
            bg="#16a34a",
            hover_bg="#15803d",
            font_size=9,
        ).pack(side=tk.RIGHT, padx=3)

        create_modern_btn(
            ft_row1,
            text="🛡️ 精选保活状态",
            command=self.clean_offline_favorites,
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            font_size=9,
        ).pack(side=tk.RIGHT, padx=3)

        ft_row2 = tk.Frame(fav_tool_bar, bg=THEME["bg_card"])
        ft_row2.pack(fill=tk.X)

        tk.Checkbutton(
            ft_row2,
            text="🔄 启用优质定时复检",
            variable=self.fav_schedule_enabled_var,
            bg=THEME["bg_card"],
            fg="#fbbf24",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#fbbf24",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=lambda: [self._on_fav_schedule_toggle(), self.save_persisted_config()],
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(ft_row2, text="间隔(m):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row2, self.fav_schedule_interval_var, 3).pack(side=tk.LEFT, padx=(2, 8))

        tk.Checkbutton(
            ft_row2,
            text="🎯 启用达标即停(取消则全测)",
            variable=self.fav_quota_early_stop_var,
            bg=THEME["bg_card"],
            fg="#38bdf8",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#38bdf8",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=self.save_persisted_config,
        ).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(ft_row2, text="香港目标:", fg="#38bdf8", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row2, self.fav_target_hk_count_var, 3).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(ft_row2, text="非香港目标:", fg="#34d399", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row2, self.fav_target_nohk_count_var, 3).pack(side=tk.LEFT, padx=(2, 10))

        tk.Checkbutton(
            ft_row2,
            text="⚠️ 不足唤醒全量优选",
            variable=self.fav_fallback_enabled_var,
            bg=THEME["bg_card"],
            fg="#f87171",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#f87171",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=self.save_persisted_config,
        ).pack(side=tk.LEFT, padx=(2, 8))

        self.fav_sched_status_label = tk.Label(
            ft_row2,
            text="(优质定时未启动)",
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            font=("Microsoft YaHei UI", 9),
        )
        self.fav_sched_status_label.pack(side=tk.LEFT, padx=4)

        # 沉淀孵化池工具栏
        verified_tool_bar = tk.Frame(self.tab_verified, bg=THEME["bg_card"], padx=10, pady=8)
        verified_tool_bar.pack(fill=tk.X, padx=4, pady=(4, 4))

        tk.Label(verified_tool_bar, text="⏳ 沉淀孵化 (发布至 /verified.txt):", fg="#34d399", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(verified_tool_bar, text="考核满存活(h):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(verified_tool_bar, self.incubate_hours_var, 3).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(verified_tool_bar, text="连续达标(次):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(verified_tool_bar, self.incubate_passes_var, 3).pack(side=tk.LEFT, padx=(2, 8))

        create_modern_btn(
            verified_tool_bar,
            text="🔄 拉取云端沉淀",
            command=self.pull_verified_from_cloud,
            bg=THEME["accent_cyan"],
            hover_bg=THEME["accent_cyan_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            verified_tool_bar,
            text="🏆 提前晋升典藏",
            command=self.force_promote_verified_to_stars,
            bg="#b45309",
            hover_bg="#d97706",
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            verified_tool_bar,
            text="🗑️ 移除选中",
            command=self.delete_selected_verified,
            bg="#991b1b",
            hover_bg="#b91c1c",
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            verified_tool_bar,
            text="💾 同步推送 /verified.txt",
            command=self.manual_push_verified_to_cloud,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.RIGHT, padx=2)

        # 典藏常青池工具栏
        stars_tool_bar = tk.Frame(self.tab_stars, bg=THEME["bg_card"], padx=10, pady=8)
        stars_tool_bar.pack(fill=tk.X, padx=4, pady=(4, 4))

        tk.Label(stars_tool_bar, text="🏆 典藏常青管理 (发布至根目录 /):", fg="#fbbf24", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        create_modern_btn(
            stars_tool_bar,
            text="➕ 录入/粘贴",
            command=self.open_import_stars_dialog,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="🔄 拉取云端",
            command=self.pull_stars_from_cloud,
            bg=THEME["accent_cyan"],
            hover_bg=THEME["accent_cyan_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="⚡ 测延迟",
            command=lambda: self.test_stars_pipeline(mode="delay"),
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="🚀 测下行",
            command=lambda: self.test_stars_pipeline(mode="speed"),
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="✏️ 备注",
            command=self.edit_selected_star_remark,
            bg=THEME["accent_blue"],
            hover_bg=THEME["accent_blue_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="🗑️ 删除",
            command=self.delete_selected_stars,
            bg="#991b1b",
            hover_bg="#b91c1c",
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="💾 保存并推送根目录 /",
            command=self.manual_push_stars_to_cloud,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.RIGHT, padx=2)

        self.trees["all"] = self.create_tree_widget(self.tab_all)
        self.trees["fav"] = self.create_tree_widget(self.tab_fav)
        self.trees["verified"] = self.create_verified_tree_widget(self.tab_verified)
        self.trees["stars"] = self.create_stars_tree_widget(self.tab_stars)
        self.trees["delay_black"] = self.create_tree_widget(self.tab_delay_black)
        self.trees["speed_black"] = self.create_tree_widget(self.tab_speed_black)

        log_card = tk.Frame(
            self.root, bg=THEME["bg_card"], padx=14, pady=6, highlightthickness=1, highlightbackground=THEME["border"]
        )

        log_head = tk.Frame(log_card, bg=THEME["bg_card"])
        log_head.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            log_head,
            text="📜 操作动态与实时运行日志:",
            font=("Microsoft YaHei UI", 9, "bold"),
            fg="#38bdf8",
            bg=THEME["bg_card"],
        ).pack(side=tk.LEFT)

        create_modern_btn(
            log_head,
            text="清屏",
            command=lambda: [self.log_text.config(state="normal"), self.log_text.delete("1.0", tk.END), self.log_text.config(state="disabled")],
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            pady=1,
            padx=8,
            font_size=8,
        ).pack(side=tk.RIGHT)

        log_inner = tk.Frame(log_card, bg=THEME["log_bg"])
        log_inner.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_inner,
            height=4,
            bg=THEME["log_bg"],
            fg="#94a3b8",
            insertbackground="#38bdf8",
            relief="flat",
            bd=0,
            font=("Consolas", 9),
            state="disabled",
            wrap="word",
        )
        log_scroll = ttk.Scrollbar(log_inner, orient=tk.VERTICAL, command=self.log_text.yview, style="Vertical.TScrollbar")
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        btn_card = tk.Frame(
            self.root, bg=THEME["bg_card"], padx=14, pady=8, highlightthickness=1, highlightbackground=THEME["border"]
        )
        # 底部栏永久锚定窗口最底部，彻底解决小分辨率或表格行过多时被挤出屏幕的问题
        btn_card.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 8))
        log_card.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 4))
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=(0, 5))

        create_modern_btn(
            btn_card,
            text="⭐ 设为优质",
            command=self.set_favorite,
            bg="#854d0e",
            hover_bg="#a16207",
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="🏆 晋升为典藏",
            command=self.promote_selected_to_stars,
            bg="#b45309",
            hover_bg="#d97706",
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="🚫 延迟拉黑",
            command=self.manual_add_delay_blacklist,
            bg="#991b1b",
            hover_bg="#b91c1c",
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="🐌 低速拉黑",
            command=self.manual_add_speed_blacklist,
            bg="#c2410c",
            hover_bg="#ea580c",
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="↩ 移出黑名单",
            command=self.remove_from_blacklist,
            bg=THEME["accent_cyan"],
            hover_bg=THEME["accent_cyan_hover"],
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="🧹 一键清空所有黑名单",
            command=self.clear_all_blacklists,
            bg=THEME["bg_hover"],
            hover_bg=THEME["accent_red"],
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="🏆 重新计分与晋升",
            command=self.trigger_rescore_and_promote,
            bg="#d97706",
            hover_bg="#b45309",
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="⚡ 手动写入并热键刷新 Verge (Ctrl+Shift+F12)",
            command=self.manual_write_and_trigger_hotkey,
            bg=THEME["accent_blue"],
            hover_bg=THEME["accent_blue_hover"],
        ).pack(side=tk.RIGHT, padx=3)

    def create_tree_widget(self, parent_tab):
        columns = ("status", "colo", "colo_hist", "reason", "delay", "avg_delay", "delay_hist", "hist_avg", "speed", "speed_hist", "name")
        tree = ttk.Treeview(parent_tab, columns=columns, show="headings", selectmode="extended")

        tree.heading("status", text="状态 ↕", command=lambda: self.sort_tree(tree, "status", False))
        tree.heading("colo", text="最新Colo ↕", command=lambda: self.sort_tree(tree, "colo", False))
        tree.heading("colo_hist", text="Colo稳定性 (7天)")
        tree.heading("reason", text="入选/拉黑原因 ↕", command=lambda: self.sort_tree(tree, "reason", False))
        tree.heading("delay", text="最新延迟 ↕", command=lambda: self.sort_tree(tree, "delay", False))
        tree.heading("avg_delay", text="本轮均值 ↕", command=lambda: self.sort_tree(tree, "avg_delay", False))
        tree.heading("delay_hist", text="延迟轨迹 (轮数)")
        tree.heading("hist_avg", text="历史均值/稳定度 ↕", command=lambda: self.sort_tree(tree, "hist_avg", False))
        tree.heading("speed", text="最新下行 ↕", command=lambda: self.sort_tree(tree, "speed", False))
        tree.heading("speed_hist", text="下行轨迹 (近4次)")
        tree.heading("name", text="节点名称 (鼠标按住可直接上下多选)")

        tree.column("status", width=90, anchor="center")
        tree.column("colo", width=85, anchor="center")
        tree.column("colo_hist", width=160, anchor="center")
        tree.column("reason", width=170, anchor="center")
        tree.column("delay", width=75, anchor="center")
        tree.column("avg_delay", width=95, anchor="center")
        tree.column("delay_hist", width=130, anchor="center")
        tree.column("hist_avg", width=155, anchor="center")
        tree.column("speed", width=80, anchor="center")
        tree.column("speed_hist", width=130, anchor="center")
        tree.column("name", width=340, anchor="w")

        tree.tag_configure("fast", foreground="#34d399")
        tree.tag_configure("medium", foreground="#fbbf24")
        tree.tag_configure("timeout", foreground="#f87171")
        tree.tag_configure("fav", background="#1a2e26", foreground="#38bdf8")
        tree.tag_configure("offline", background="#1e293b", foreground="#94a3b8")
        tree.tag_configure("black_delay", background="#2b181b", foreground="#f87171")
        tree.tag_configure("black_speed", background="#2b2018", foreground="#fb923c")

        scrollbar = ttk.Scrollbar(parent_tab, orient=tk.VERTICAL, command=tree.yview, style="Vertical.TScrollbar")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.bind_drag_selection(tree)
        return tree

    def create_verified_tree_widget(self, parent_tab):
        columns = ("endpoint", "colo", "colo_hist", "reason", "remark", "delay", "speed", "time", "stats", "match")
        tree = ttk.Treeview(parent_tab, columns=columns, show="headings", selectmode="extended")

        tree.heading("endpoint", text="IP:端口 ↕", command=lambda: self.sort_tree(tree, "endpoint", False))
        tree.heading("colo", text="最新Colo ↕", command=lambda: self.sort_tree(tree, "colo", False))
        tree.heading("colo_hist", text="Colo稳定性 (7天)")
        tree.heading("reason", text="入孵原因 / 考核状态 ↕", command=lambda: self.sort_tree(tree, "reason", False))
        tree.heading("remark", text="备注信息 ↕", command=lambda: self.sort_tree(tree, "remark", False))
        tree.heading("delay", text="最新延迟 ↕", command=lambda: self.sort_tree(tree, "delay", False))
        tree.heading("speed", text="最新下行 ↕", command=lambda: self.sort_tree(tree, "speed", False))
        tree.heading("time", text="存活时长 ↕", command=lambda: self.sort_tree(tree, "time", False))
        tree.heading("stats", text="考核统计 ↕", command=lambda: self.sort_tree(tree, "stats", False))
        tree.heading("match", text="本地订阅关联")

        tree.column("endpoint", width=125, anchor="center")
        tree.column("colo", width=85, anchor="center")
        tree.column("colo_hist", width=150, anchor="center")
        tree.column("reason", width=170, anchor="center")
        tree.column("remark", width=155, anchor="w")
        tree.column("delay", width=75, anchor="center")
        tree.column("speed", width=80, anchor="center")
        tree.column("time", width=90, anchor="center")
        tree.column("stats", width=130, anchor="center")
        tree.column("match", width=220, anchor="w")

        tree.tag_configure("fav", foreground="#34d399")
        scrollbar = ttk.Scrollbar(parent_tab, orient=tk.VERTICAL, command=tree.yview, style="Vertical.TScrollbar")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.bind_drag_selection(tree)
        return tree

    def create_stars_tree_widget(self, parent_tab):
        columns = ("endpoint", "colo", "colo_hist", "reason", "remark", "delay", "speed", "match")
        tree = ttk.Treeview(parent_tab, columns=columns, show="headings", selectmode="extended")

        tree.heading("endpoint", text="IP:端口 ↕", command=lambda: self.sort_tree(tree, "endpoint", False))
        tree.heading("colo", text="最新Colo ↕", command=lambda: self.sort_tree(tree, "colo", False))
        tree.heading("colo_hist", text="Colo稳定性 (7天)")
        tree.heading("reason", text="典藏入选原因 ↕", command=lambda: self.sort_tree(tree, "reason", False))
        tree.heading("remark", text="备注信息 (可双击修改) ↕", command=lambda: self.sort_tree(tree, "remark", False))
        tree.heading("delay", text="最新延迟 ↕", command=lambda: self.sort_tree(tree, "delay", False))
        tree.heading("speed", text="最新下行 ↕", command=lambda: self.sort_tree(tree, "speed", False))
        tree.heading("match", text="本地订阅关联状态")

        tree.column("endpoint", width=130, anchor="center")
        tree.column("colo", width=85, anchor="center")
        tree.column("colo_hist", width=150, anchor="center")
        tree.column("reason", width=190, anchor="center")
        tree.column("remark", width=200, anchor="w")
        tree.column("delay", width=75, anchor="center")
        tree.column("speed", width=85, anchor="center")
        tree.column("match", width=250, anchor="w")

        tree.tag_configure("fav", foreground="#38bdf8")
        tree.tag_configure("offline", foreground="#94a3b8")

        scrollbar = ttk.Scrollbar(parent_tab, orient=tk.VERTICAL, command=tree.yview, style="Vertical.TScrollbar")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree.bind("<Double-1>", lambda e: self.edit_selected_star_remark())
        self.bind_drag_selection(tree)
        return tree

    def bind_drag_selection(self, tree):
        tree._drag_start_item = None
        tree._base_selection = set()

        def on_press(event):
            item = tree.identify_row(event.y)
            if not item:
                return
            tree._drag_start_item = item
            if event.state & 0x0004:
                tree._base_selection = set(tree.selection())
            else:
                tree._base_selection = set()
                tree.selection_set(item)

        def on_drag(event):
            if not tree._drag_start_item:
                return
            cur_item = tree.identify_row(event.y)
            if not cur_item:
                return

            children = list(tree.get_children(""))
            if tree._drag_start_item in children and cur_item in children:
                idx_start = children.index(tree._drag_start_item)
                idx_cur = children.index(cur_item)
                low, high = min(idx_start, idx_cur), max(idx_start, idx_cur)
                drag_selected = set(children[low : high + 1])

                if event.state & 0x0004:
                    tree.selection_set(list(tree._base_selection | drag_selected))
                else:
                    tree.selection_set(list(drag_selected))

        def on_release(event):
            tree._drag_start_item = None

        tree.bind("<ButtonPress-1>", on_press, add="+")
        tree.bind("<B1-Motion>", on_drag, add="+")
        tree.bind("<ButtonRelease-1>", on_release, add="+")

    def get_current_tree(self):
        idx = self.notebook.index(self.notebook.select())
        mapping = [self.trees["all"], self.trees["fav"], self.trees["verified"], self.trees["stars"], self.trees["delay_black"], self.trees["speed_black"]]
        return mapping[idx] if idx < len(mapping) else self.trees["all"]

    def load_profile_data(self):
        profiles_yaml = os.path.join(PARENT_DIR, "profiles.yaml")
        profile_names_map = {}
        current_active_id = ""

        if os.path.exists(profiles_yaml):
            try:
                with open(profiles_yaml, "r", encoding="utf-8", errors="ignore") as f:
                    p_content = f.read()

                m_cur = re.search(r"current:\s*['\"]?([^'\"\r\n]+)['\"]?", p_content)
                if m_cur:
                    current_active_id = m_cur.group(1).strip()

                items = re.split(r"\n\s*-\s+", p_content)
                for itm in items:
                    m_id = re.search(r"(?:id|uid):\s*['\"]?([^'\"\r\n]+)['\"]?", itm)
                    m_name = re.search(r"name:\s*['\"]?([^'\"\r\n]+)['\"]?", itm)
                    if m_id and m_name:
                        profile_names_map[m_id.group(1).strip()] = m_name.group(1).strip()
            except Exception:
                pass

        yaml_files = glob.glob(os.path.join(BASE_DIR, "*.yaml"))
        self.file_items = []

        for fpath in yaml_files:
            fname = os.path.basename(fpath)
            if fname == "verge_filter_rules.yaml":
                continue
            nodes, details = self.extract_nodes_and_details_from_file(fpath)
            self.node_details.update(details)

            f_stem = os.path.splitext(fname)[0]
            display_title = profile_names_map.get(f_stem, fname)

            self.file_items.append(
                {
                    "display": f"{display_title} [{fname}] ({len(nodes)} 节点)",
                    "path": fpath,
                    "nodes": nodes,
                    "details": details,
                    "stem": f_stem,
                    "fname": fname,
                }
            )

        if not self.file_items:
            return

        active_idx = 0
        if current_active_id:
            curr_stem = os.path.splitext(current_active_id)[0]
            for idx, itm in enumerate(self.file_items):
                if itm["stem"] == curr_stem or itm["fname"] == current_active_id:
                    active_idx = idx
                    break

        self.file_combo["values"] = [item["display"] for item in self.file_items]
        self.file_combo.current(active_idx)
        self.apply_profile_selection(active_idx)

    def on_file_changed(self, event):
        idx = self.file_combo.current()
        if idx >= 0:
            self.apply_profile_selection(idx)

    def apply_profile_selection(self, idx):
        self.all_nodes = self.file_items[idx]["nodes"]
        self.node_details.update(self.file_items[idx].get("details", {}))
        self.auto_filter_and_blacklist_non_asia_nodes()
        self.align_favorites_with_current_subscription()
        self.refresh_tables()
        self.refresh_verified_table()
        self.refresh_stars_table()

    def update_remote_subscription(self, target_yaml_path):
        mixed_port = self.get_clash_mixed_port()
        return update_remote_subscription(
            target_yaml_path,
            mixed_port=mixed_port,
            on_step_callback=lambda txt: self.root.after(0, lambda: self.status_label.config(text=txt)),
        )

    def update_subscription_and_reactivate(self, on_step_callback=None, on_finish_callback=None):
        """通用订阅更新与热激活闭环：拉取最新远程订阅 -> 重新解析节点 -> 写入Script.js -> 触发热键 -> 探测内核装载"""
        def _worker():
            cur_idx = self.file_combo.current()
            cur_file_info = self.file_items[cur_idx] if (cur_idx >= 0 and cur_idx < len(self.file_items)) else None

            if not cur_file_info or not os.path.exists(cur_file_info["path"]):
                err_msg = "未检测到当前选中的有效订阅配置文件！"
                self.log(f"⚠️ {err_msg}")
                if on_step_callback:
                    self.root.after(0, lambda: on_step_callback("error", err_msg))
                if on_finish_callback:
                    self.root.after(0, lambda: on_finish_callback(False, err_msg, []))
                return

            logs_step = []
            if on_step_callback:
                self.root.after(0, lambda: on_step_callback("step", "正在拉取远程最新订阅 (多通道重试)..."))

            up_ok, up_msg, content_changed = self.update_remote_subscription(cur_file_info["path"])
            if not up_ok:
                logs_step.append(f"⚠️ 订阅拉取提示: {up_msg}")
                self.log(f"订阅拉取提示: {up_msg}")
            else:
                logs_step.append(f"✅ 订阅更新成功: {up_msg}")
                self.log(f"订阅更新成功: {up_msg}")

            new_nodes, new_details = self.extract_nodes_and_details_from_file(cur_file_info["path"])
            if new_nodes:
                self.all_nodes = new_nodes
                self.node_details.update(new_details)
                cur_file_info["nodes"] = new_nodes
                cur_file_info["details"] = new_details
                logs_step.append(f"✅ 解析出 {len(new_nodes)} 个代理节点")
                b_cnt = self.auto_filter_and_blacklist_non_asia_nodes()
                if b_cnt > 0:
                    logs_step.append(f"🛡️ 自动拉黑非亚洲节点: 已直接拉黑淘汰 {b_cnt} 个非亚洲节点")
                # 仅对齐本地优质精选池至当前订阅更名，坚决不从远端旧文件覆写本地复检成果
                self.align_favorites_with_current_subscription()
                logs_step.append(f"⭐ 优质精选池更名对齐: 当前有效存活 {len(self.favorites)} 个节点")

            # 写入 Script.js
            write_ok, write_err = self.do_write_script_file(list(self.favorites))
            if write_ok:
                logs_step.append("✅ 已重新生成并写入 Script.js 脚本规则")
            else:
                logs_step.append(f"⚠️ 写入 Script.js: {write_err}")

            # 触发热键
            if on_step_callback:
                self.root.after(0, lambda: on_step_callback("step", "正在触发热键通知内核装载新节点..."))
            time.sleep(0.3)
            hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()
            if hotkey_ok:
                logs_step.append("✅ 已模拟全局热键 (Ctrl+Shift+F12) 激活 Clash Verge")
            else:
                logs_step.append(f"⚠️ 触发快捷键提示: {hotkey_msg}")

            # 探测内核装载
            loaded_ok = False
            loaded_msg = ""
            if self.all_nodes:
                if on_step_callback:
                    self.root.after(0, lambda: on_step_callback("step", "正在探测内核装载状态..."))
                loaded_ok, loaded_msg = self.wait_for_kernel_reload(self.all_nodes, max_wait_sec=10)
                logs_step.append(f"{'✅' if loaded_ok else '⚠️'} 内核装载: {loaded_msg}")
                self.log(f"内核装载探测: {loaded_msg}")

            self.root.after(0, self.refresh_tables)
            self.root.after(0, self.refresh_verified_table)
            self.root.after(0, self.refresh_stars_table)

            final_ok = up_ok or loaded_ok
            if on_finish_callback:
                self.root.after(0, lambda: on_finish_callback(final_ok, up_msg, logs_step))

        threading.Thread(target=_worker, daemon=True).start()

    def manual_update_subscription_and_reactivate(self):
        """用户手动点击【🔄 更新当前订阅】触发的闭环处理"""
        cur_idx = self.file_combo.current()
        cur_file_info = self.file_items[cur_idx] if (cur_idx >= 0 and cur_idx < len(self.file_items)) else None
        if not cur_file_info:
            messagebox.showwarning("提示", "未找到当前选中的有效订阅文件！")
            return

        self.status_label.config(text="正在拉取最新订阅并触发热更新激活...")
        self.log("手动触发订阅更新与热激活闭环...")

        def _on_step(mode, text):
            self.status_label.config(text=text)

        def _on_finish(ok, msg, steps):
            if ok:
                full_msg = f"🎉 订阅更新与热更新激活成功！\n\n" + "\n".join(steps)
                self.status_label.config(text="订阅更新与热激活成功！")
                messagebox.showinfo("更新成功", full_msg)
            else:
                self.status_label.config(text="订阅更新或激活未完全成功")
                messagebox.showwarning("更新提示", f"订阅拉取或激活未完全成功：\n\n{msg}\n\n" + "\n".join(steps))

        self.update_subscription_and_reactivate(on_step_callback=_on_step, on_finish_callback=_on_finish)

    def clear_test_history(self, silent=False):
        if not silent:
            if not self.node_delays and not self.node_history and not self.node_speeds:
                messagebox.showinfo("提示", "当前没有测速记录！")
                return
            if not messagebox.askyesno(
                "清空确认",
                "确定要清空所有测速数据与延迟趋势记录吗？\n（不会清空您的黑名单及下行带宽历史）",
            ):
                return

        self.node_delays.clear()
        self.node_history.clear()
        self.node_speeds.clear()

        threading.Thread(
            target=lambda: self._call_api("/configs?force=true", method="PUT", data=b'{"path":""}'),
            daemon=True,
        ).start()

        self.status_label.config(text="测速记录已归零")
        self.log("所有测速与延迟记录已手动清空。")
        if getattr(self, "_is_initialized", False) or not silent:
            self.refresh_tables()

    def sync_existing_delays(self):
        data = self._call_api("/proxies")
        if not data or "proxies" not in data:
            return

        proxies = data["proxies"]
        updated = False

        try:
            target_rounds = max(1, int(self.test_rounds_var.get().strip())) if self.test_rounds_var.get().strip().isdigit() else 4
        except Exception:
            target_rounds = 4

        for name, info in proxies.items():
            history = info.get("history", [])
            if history:
                delays = [
                    h.get("delay", 0)
                    for h in history
                    if isinstance(h.get("delay"), int)
                ]
                normalized = [d if d > 0 else 99999 for d in delays]
                if normalized:
                    self.node_history[name] = normalized[-target_rounds:]
                    self.node_delays[name] = normalized[-1]
                    updated = True

        if updated:
            self.root.after(0, self.refresh_tables)
            self.log("已成功从内核同步现有节点延迟历史。")

    def stop_pipeline(self):
        self.is_pipeline_running = False
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 正在停止...")
        self.status_label.config(text="已发送停止指令，正在安全收尾...")
        self.log("已收到手动中止指令，正在收尾...")

    def _on_schedule_toggle(self):
        if self.schedule_enabled_var.get():
            self.sched_status_label.config(text="● 全局定时运行中", fg=THEME["accent_green"])
        else:
            self.sched_status_label.config(text="(全局定时未启动)", fg=THEME["text_muted"])

    def _on_fav_schedule_toggle(self):
        if self.fav_schedule_enabled_var.get():
            self.fav_sched_status_label.config(text="● 优质定时运行中", fg=THEME["accent_green"])
        else:
            self.fav_sched_status_label.config(text="(优质定时未启动)", fg=THEME["text_muted"])

    def _scheduler_daemon_loop(self):
        self.scheduler = SchedulerDaemon(
            get_config_fn=lambda: {
                "is_pipeline_running": self.is_pipeline_running,
                "schedule_enabled": self.schedule_enabled_var.get(),
                "schedule_times": self.schedule_times_var.get(),
                "schedule_interval": self.schedule_interval_var.get(),
                "fav_schedule_enabled": self.fav_schedule_enabled_var.get(),
                "fav_schedule_interval": self.fav_schedule_interval_var.get(),
            },
            on_trigger_full=lambda reason: self.root.after(0, lambda r=reason: self._trigger_scheduled_full_pipeline(r)),
            on_trigger_fav=lambda reason: self.root.after(0, lambda r=reason: self._trigger_scheduled_fav_pipeline(r)),
        )
        self.scheduler.update_last_run(self.last_full_run_timestamp, self.last_fav_run_timestamp)
        self.scheduler.start()

    def _trigger_scheduled_full_pipeline(self, reason):
        if not self.is_pipeline_running:
            self.log(f"⏰ 全局定时触发（{reason}），启动全自动优选")
            self.status_label.config(text=f"⏰ 全局定时触发（{reason}），启动全自动优选...")
            self.start_full_auto_pipeline()

    def _trigger_scheduled_fav_pipeline(self, reason):
        if not self.is_pipeline_running:
            self.log(f"⏰ 优质复检触发（{reason}），启动优质池测试")
            self.status_label.config(text=f"⏰ 优质复检触发（{reason}），启动优质池测试...")
            self.start_fav_review_pipeline()

    def save_group_config_and_reload(self):
        inter_str = self.group_interval_var.get().strip()
        tol_str = self.group_tolerance_var.get().strip()
        star_inter_str = self.star_group_interval_var.get().strip()
        star_tol_str = self.star_group_tolerance_var.get().strip()

        for val, name in [
            (inter_str, "常规间隔"),
            (tol_str, "常规容差"),
            (star_inter_str, "典藏间隔"),
            (star_tol_str, "典藏容差"),
        ]:
            if not val.isdigit() or int(val) < 0:
                messagebox.showerror("参数错误", f"{name} 必须为纯正整数！")
                return

        self.save_persisted_config()

        script_path = DEFAULT_SCRIPT_JS
        if not os.path.exists(script_path):
            js_files = glob.glob(os.path.join(BASE_DIR, "*.js"))
            if js_files:
                script_path = js_files[0]

        if not os.path.exists(script_path):
            ok, err = self.do_write_script_file(list(self.favorites))
            if ok:
                time.sleep(0.2)
                trigger_verge_reactivate_hotkey()
                self.log(f"策略组配置已更新 (常规:{inter_str}s, 典藏:{star_inter_str}s)")
                messagebox.showinfo("成功", "已生成新脚本并应用三代理组测速设置！")
            else:
                messagebox.showerror("失败", f"生成脚本失败: {err}")
            return

        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()

            new_content = re.sub(r"const groupInterval = \d+;", f"const groupInterval = {inter_str};", content)
            new_content = re.sub(r"const groupTolerance = \d+;", f"const groupTolerance = {tol_str};", new_content)
            new_content = re.sub(r"const starsGroupInterval = \d+;", f"const starsGroupInterval = {star_inter_str};", new_content)
            new_content = re.sub(r"const starsGroupTolerance = \d+;", f"const starsGroupTolerance = {star_tol_str};", new_content)

            if "autoGroupStars" not in new_content:
                ok, err = self.do_write_script_file(list(self.favorites))
                if not ok:
                    messagebox.showerror("更新失败", f"更新 Script.js 失败：{err}")
                    return
            else:
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self.root.clipboard_clear()
                self.root.clipboard_append(new_content)

            time.sleep(0.2)
            hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()

            msg = (
                f"✅ 三大策略组测速配置已更新成功！\n\n"
                f"• 常规组 (自动/非香港)：间隔 {inter_str}s，容差 {tol_str}ms\n"
                f"• 典藏专属组 (典藏)：间隔 {star_inter_str}s，容差 {star_tol_str}ms\n\n"
            )
            if hotkey_ok:
                msg += "⚡ 已通过全局热键触发 Verge 即时热更生效！全部节点列表完好保留。"
            else:
                msg += f"⚠️ 已修改脚本，热键模拟触发失败({hotkey_msg})，请手动按 Ctrl+Shift+F12 刷新。"

            self.status_label.config(text=f"策略组测速参数已更新 (常规:{inter_str}s, 典藏:{star_inter_str}s)")
            self.log(f"策略组测速参数已更新 (常规:{inter_str}s, 典藏:{star_inter_str}s) 并热键重载")
            messagebox.showinfo("保存并热更成功", msg)
        except Exception as ex:
            messagebox.showerror("更新失败", f"修改 Script.js 失败：\n{str(ex)}")

    # ==================== 全量大优选 (含 7 天 Colo 轨迹更新) ====================
    def start_full_auto_pipeline(self):
        if self.is_pipeline_running:
            return

        self.last_full_run_timestamp = time.time()
        self.save_persisted_config()
        self.update_last_run_display()
        self.log("🚀 启动一整套全自动大优选流程...")

        try:
            max_delay = int(self.max_delay_threshold_var.get().strip()) if self.max_delay_threshold_var.get().strip().isdigit() else 100
            min_speed = float(self.min_speed_threshold_var.get().strip()) if self.min_speed_threshold_var.get().strip() else 5.0
            rounds = max(1, int(self.test_rounds_var.get().strip())) if self.test_rounds_var.get().strip().isdigit() else 4
            timeout_ms = int(self.test_timeout_var.get().strip()) if hasattr(self, "test_timeout_var") and self.test_timeout_var.get().strip().isdigit() else 1500
            try:
                duration = max(0.5, float(self.speed_duration_var.get().strip()))
            except Exception:
                duration = 3.0

            bl_delay_threshold = int(self.blacklist_threshold_var.get().strip()) if self.blacklist_threshold_var.get().strip().isdigit() else 130
            speed_bl_threshold = float(self.speed_bl_threshold_var.get().strip()) if self.speed_bl_threshold_var.get().strip() else 1.0
            speed_bl_rounds = max(1, int(self.speed_bl_rounds_var.get().strip())) if self.speed_bl_rounds_var.get().strip().isdigit() else 4
            jitter_min_d = int(self.jitter_min_delay_var.get().strip()) if hasattr(self, "jitter_min_delay_var") and self.jitter_min_delay_var.get().strip().isdigit() else 80
            jitter_up_th = int(self.jitter_up_threshold_var.get().strip()) if hasattr(self, "jitter_up_threshold_var") and self.jitter_up_threshold_var.get().strip().isdigit() else 20

            test_url = self.test_url_var.get().strip()
            speed_url = self.speed_url_var.get().strip()

            target_cnt_str = self.target_node_count_var.get().strip() if hasattr(self, "target_node_count_var") else ""
            target_node_limit = int(target_cnt_str) if (target_cnt_str.isdigit() and int(target_cnt_str) > 0) else 0
        except Exception as err:
            if not self.root.winfo_viewable():
                send_system_notification("优选启动异常", f"参数错误: {str(err)}")
            else:
                messagebox.showerror("参数格式错误", f"请检查输入参数是否正确：\n{str(err)}")
            return

        if not test_url.startswith("http") or not speed_url.startswith("http"):
            if self.root.winfo_viewable():
                messagebox.showerror("参数格式错误", "测试地址与测速源必须以 http:// 或 https:// 开头！")
            return

        if not self.test_connection(auto_sync=False):
            if self.root.winfo_viewable():
                messagebox.showwarning("提示", "无法连接内核！")
            return

        self.is_pipeline_running = True
        self.btn_run_pipeline.config(state="disabled")
        self.btn_stop_pipeline.config(state="normal", text="⏹ 终止任务")
        self.file_combo.config(state="disabled")

        def _pipeline_worker():
            try:
                cur_idx = self.file_combo.current()
                cur_file_info = self.file_items[cur_idx] if (cur_idx >= 0 and cur_idx < len(self.file_items)) else None

                if not cur_file_info:
                    self.root.after(0, lambda: self._on_fetch_failed_abort("未检测到当前有效的订阅文件！"))
                    return

                self.root.after(0, lambda: self.status_label.config(text="[步骤 1/4] 正在拉取远程最新订阅 (多通道重试)..."))
                up_ok, up_msg, content_changed = self.update_remote_subscription(cur_file_info["path"])

                if not up_ok:
                    self.root.after(0, lambda m=up_msg: self._on_fetch_failed_abort(m))
                    return

                new_nodes, new_details = self.extract_nodes_and_details_from_file(cur_file_info["path"])
                if not new_nodes:
                    self.root.after(0, lambda: self._on_fetch_failed_abort("订阅文件拉取成功，但未能解析出任何代理节点！"))
                    return

                self.all_nodes = new_nodes
                self.node_details.update(new_details)
                cur_file_info["nodes"] = new_nodes
                cur_file_info["details"] = new_details
                self.auto_filter_and_blacklist_non_asia_nodes()
                self.root.after(0, self.refresh_tables)
                self.root.after(0, self.refresh_verified_table)
                self.root.after(0, self.refresh_stars_table)

                if content_changed:
                    self.log("订阅内容已更新(MD5变动)，触发热键通知内核装载新节点...")
                    self.root.after(0, lambda: self.status_label.config(text="[步骤 1/4] 订阅更新(MD5变动)，正在触发热键并检测内核装载..."))
                    trigger_verge_reactivate_hotkey()

                    loaded_ok, loaded_msg = self.wait_for_kernel_reload(new_nodes, max_wait_sec=15)
                    self.log(f"内核指纹探针反馈: {loaded_msg}")
                    if loaded_ok:
                        self.root.after(0, lambda m=loaded_msg: self.status_label.config(text=f"[步骤 1/4] {m}"))
                    else:
                        self.root.after(0, lambda m=loaded_msg: self.status_label.config(text=f"[步骤 1/4] ⚠️ 警告：{m}"))
                    time.sleep(0.8)
                else:
                    self.log("订阅源内容未发生任何改变 (MD5一致)，跳过热键与内核重载，无缝开测！")
                    self.root.after(0, lambda: self.status_label.config(text="[步骤 1/4] 订阅MD5一致，跳过重载直接开测"))
                    time.sleep(0.2)

                # 尝试从 /auto.txt 获取云端优质保活端点，双重确保绝对去重
                cloud_eps = self.fetch_auto_endpoints_from_cloud()
                if cloud_eps:
                    self.auto_endpoints.update(cloud_eps)

                fav_eps, bl_eps, sbl_eps, star_eps = self.get_pool_endpoint_sets()

                ep_to_untested = {}
                fav_sk = 0
                d_sk = 0
                s_sk = 0
                ver_sk = 0

                for n in self.all_nodes:
                    if not self.is_asian_node(n):
                        if n not in self.local_blacklist:
                            self.local_blacklist.add(n)
                        continue

                    ep = self.get_node_endpoint(n)
                    if n in self.local_blacklist or (ep and ep in self.local_blacklist):
                        d_sk += 1
                        continue
                    if n in self.speed_blacklist or (ep and ep in self.speed_blacklist):
                        s_sk += 1
                        continue
                    # 核心去重：命中优质精选、auto.txt 云端保活或孵化端点，一律跳过初测（绝不多重收录同端点冗余马甲）
                    if n in self.favorites or (ep and ep in fav_eps):
                        # ★ 新增：精选节点快速漂移/非亚洲审查
                        _should_purge = False
                        _purge_reason = ""
                        if not self.is_asian_node(n):
                            _should_purge = True
                            _purge_reason = "非亚洲地区/命名"
                        else:
                            colo_hist = self.node_colo_history.get(n, self.node_colo_history.get(ep, []))
                            if colo_hist:
                                _dom, _, _has_drift, _drift_disp = self.analyze_colo_stats(colo_hist, time.time(), node_name=n)
                                if _has_drift or not self.is_asian_node(n, colo=_dom):
                                    _should_purge = True
                                    _purge_reason = f"机房漂移 ({_drift_disp})"
                        if _should_purge:
                            self.local_blacklist.add(n)
                            self.favorites.discard(n)
                            self.record_blacklist_reason(n, _purge_reason)
                            if ep:
                                self.local_blacklist.add(ep)
                                self.record_blacklist_reason(ep, _purge_reason)
                                fav_eps.discard(ep)
                                for f in list(self.favorites):
                                    if self.get_node_endpoint(f) == ep:
                                        self.favorites.discard(f)
                            if ep and hasattr(self, "verified_nodes") and ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                            self.log(f"【精选审查淘汰】节点 {n} 命中规则：{_purge_reason}，已从精选清除并加入黑名单！")
                            continue  # 已拉黑，无需进测试队列
                        # ★ 未触发审查的精选节点，正常跳过
                        fav_sk += 1
                        continue
                    if (n in getattr(self, "verified_nodes", {})) or (ep and ep in star_eps):
                        ver_sk += 1
                        continue

                    ep_to_untested.setdefault(ep, []).append(n)

                unique_eps = list(ep_to_untested.keys())
                test_targets = [self.choose_canonical_node_name(ep_to_untested[ep]) for ep in unique_eps]
                total_untested_nodes = sum(len(nodes) for nodes in ep_to_untested.values())

                self.log(f"全量节点: {len(new_nodes)} 个 | 严格限制亚洲节点 | 跳过已知精选: {fav_sk} | 跳过延迟黑名单: {d_sk} | 跳过低速黑名单: {s_sk} | 待测独立节点: {len(test_targets)} 个 (同源马甲已自动聚合)")

                if not self.is_pipeline_running:
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                if not test_targets:
                    self.root.after(0, lambda: self._on_pipeline_error("所有节点均位于精选、黑名单或沉淀池中，无新的待测节点！"))
                    return

                self.log(f"开始执行 {rounds} 轮延迟初筛 (独立端点纯净版: 共 {len(unique_eps)} 个)...")
                for r in range(1, rounds + 1):
                    if not self.is_pipeline_running:
                        break

                    total = len(unique_eps)
                    done = [0]
                    round_ep_delays = {}

                    def _single_delay(endpoint):
                        if not self.is_pipeline_running:
                            return
                        rep_node = self.choose_canonical_node_name(ep_to_untested[endpoint])
                        enc_name = urllib.parse.quote(rep_node, safe="")
                        enc_url = urllib.parse.quote(test_url, safe="")
                        endpoint_url = f"/proxies/{enc_name}/delay?timeout={timeout_ms}&url={enc_url}"
                        res = self._call_api(endpoint_url, timeout=(timeout_ms / 1000.0) + 0.6)

                        cur_delay = res["delay"] if (res and "delay" in res) else 99999
                        round_ep_delays[endpoint] = cur_delay
                        if cur_delay < 99999:
                            self.record_delay_sample(endpoint, cur_delay)

                        for n in ep_to_untested[endpoint]:
                            self.node_delays[n] = cur_delay
                            if n not in self.node_history:
                                self.node_history[n] = []
                            self.node_history[n].append(cur_delay)
                            self.node_history[n] = self.node_history[n][-rounds:]
                            if cur_delay < 99999:
                                self.record_delay_sample(n, cur_delay)

                        done[0] += 1
                        if done[0] % 5 == 0 or done[0] >= total:
                            self.root.after(
                                0,
                                lambda: self.status_label.config(
                                    text=f"[步骤 2/4] 延迟初筛中: 第 {r}/{rounds} 轮 ({min(done[0], total)}/{total})"
                                ),
                            )

                    with ThreadPoolExecutor(max_workers=10) as executor:
                        list(executor.map(_single_delay, unique_eps))

                    self.root.after(0, self.refresh_tables)
                    if not self.is_pipeline_running:
                        break
                    time.sleep(1)

                if not self.is_pipeline_running:
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                candidates = []
                newly_delay_blacklisted = 0

                for n in test_targets:
                    hist = self.node_history.get(n, [])
                    best_delay = min(hist[-rounds:]) if hist else 99999

                    # 严格拉黑淘汰：延迟未达到设定要求(> max_delay)或超时(>= 99999)，直接加入延迟黑名单并淘汰
                    if best_delay > max_delay or best_delay >= bl_delay_threshold or best_delay >= 99999:
                        if best_delay >= 99999:
                            d_reason = "延迟超时 (≥99999ms)"
                        elif best_delay >= bl_delay_threshold:
                            d_reason = f"延迟超标 ({best_delay}ms ≥ {bl_delay_threshold}ms)"
                        else:
                            d_reason = f"延迟淘汰 ({best_delay}ms > {max_delay}ms)"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, d_reason)
                        ep = self.get_node_endpoint(n)
                        if ep:
                            self.local_blacklist.add(ep)
                            self.record_blacklist_reason(ep, d_reason)
                        for same_n in ep_to_untested.get(ep, []):
                            self.local_blacklist.add(same_n)
                            self.favorites.discard(same_n)
                            self.record_blacklist_reason(same_n, d_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        newly_delay_blacklisted += 1
                        continue

                    # 节点抖动拉黑机制：最低延迟≥设定值且向上抖动≥设定值，立即拉黑淘汰（最高延迟<设定最低延迟则豁免）
                    is_j_bad, j_min, j_up = self.check_node_jitter_blacklisted(
                        hist[-rounds:], jitter_min_d, jitter_up_th
                    )
                    if is_j_bad:
                        j_reason = f"延迟抖动淘汰 (底{j_min}ms 抖动+{j_up}ms)"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, j_reason)
                        ep = self.get_node_endpoint(n)
                        if ep:
                            self.local_blacklist.add(ep)
                            self.record_blacklist_reason(ep, j_reason)
                        for same_n in ep_to_untested.get(ep, []):
                            self.local_blacklist.add(same_n)
                            self.favorites.discard(same_n)
                            self.record_blacklist_reason(same_n, j_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        newly_delay_blacklisted += 1
                        self.log(f"【抖动直接淘汰】节点 {n} 最低延迟 {j_min}ms (≥{jitter_min_d}ms)，向上抖动 +{j_up}ms (≥{jitter_up_th}ms)，立即拉黑淘汰！")
                        continue

                    candidates.append(n)

                if newly_delay_blacklisted > 0:
                    self.save_persisted_config()

                self.root.after(0, self.refresh_tables)
                self.log(f"延迟初筛完成：{len(candidates)} 个候选节点达到 ≤{max_delay}ms (新增延迟拉黑淘汰: {newly_delay_blacklisted} 个)")

                if not candidates:
                    self.root.after(0, lambda: send_system_notification("优选结束", f"待测节点延迟均未达到 ≤{max_delay}ms。"))
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                candidates.sort(key=lambda n: min(self.node_history.get(n, [99999])))

                # 自动采集 Colo 并记入 7 天滑动桶
                self.log(f"正在对 {len(candidates)} 个候选节点校准真实 Colo 并录入 7 天时序桶...")
                def _probe_colo(n):
                    ep = self.get_node_endpoint(n)
                    if ":" in ep:
                        ip, port = ep.split(":", 1)
                        c_code, c_disp = get_cf_colo_raw(ip, port, timeout=1.5)
                        self.record_colo_sample(n, ep, c_code, c_disp)

                with ThreadPoolExecutor(max_workers=15) as ex:
                    list(ex.map(_probe_colo, candidates))
                self.root.after(0, self.refresh_tables)

                # 严格漂移检测：发生机房漂移一次即直接拉黑淘汰！
                drift_passed_candidates = []
                now_pipe_t = time.time()
                for n in candidates:
                    ep = self.get_node_endpoint(n)
                    colo_hist = self.node_colo_history.get(n, self.node_colo_history.get(ep, []))
                    _, _, has_drift, drift_disp = self.analyze_colo_stats(colo_hist, now_pipe_t, node_name=n)
                    if has_drift:
                        drift_reason = f"机房漂移 ({drift_disp})"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, drift_reason)
                        if ep:
                            self.local_blacklist.add(ep)
                            self.record_blacklist_reason(ep, drift_reason)
                        for same_n in ep_to_untested.get(ep, []):
                            self.local_blacklist.add(same_n)
                            self.favorites.discard(same_n)
                            self.record_blacklist_reason(same_n, drift_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        newly_delay_blacklisted += 1
                        self.log(f"【漂移直接淘汰】节点 {n} 发生机房漂移 ({drift_disp})，直接拉黑并清除！")
                    else:
                        drift_passed_candidates.append(n)

                candidates = [n for n in drift_passed_candidates if self.is_asian_node(n)]
                if newly_delay_blacklisted > 0:
                    self.save_persisted_config()
                self.root.after(0, self.refresh_tables)

                if not candidates:
                    self.root.after(0, lambda: send_system_notification("优选结束", "候选节点均发生机房漂移已被全部淘汰。"))
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                proxies_data = self._call_api("/proxies") or {}
                proxies_map = proxies_data.get("proxies", {})
                global_info = proxies_map.get("GLOBAL", {})
                orig_global = global_info.get("now", "")
                global_all = global_info.get("all", [])

                mixed_port = self.get_clash_mixed_port()
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

                mode_guard = ClashModeGuard(self.clash_client, temporary_mode="global")
                mode_guard.__enter__()
                try:

                    for idx, node_name in enumerate(candidates, 1):
                        if not self.is_pipeline_running:
                            break

                        ep = self.get_node_endpoint(node_name)
                        target_str = f" [已集齐: {len(premium_nodes)}/{target_node_limit}]" if target_node_limit > 0 else f" [全测模式: 已集齐 {len(premium_nodes)} 个]"
                        self.root.after(
                            0,
                            lambda i=idx, n=node_name, ts=target_str: self.status_label.config(
                                text=f"[步骤 3/4] 带宽精测: [{i}/{total_cand}]{ts} {n[:18]}..."
                            ),
                        )

                        if ep in tested_endpoint_speeds:
                            speed_val = tested_endpoint_speeds[ep]
                            self.node_speeds[node_name] = speed_val
                            if node_name not in self.node_speed_history:
                                self.node_speed_history[node_name] = []
                            self.node_speed_history[node_name].append(max(0.0, speed_val))
                            self.node_speed_history[node_name] = self.node_speed_history[node_name][-4:]

                            if speed_val >= min_speed and node_name not in self.speed_blacklist and self.is_asian_node(node_name):
                                premium_nodes.append(node_name)
                                self.favorites.add(node_name)
                                d_val = self.node_delays.get(node_name, 0)
                                self.record_fav_reason(node_name, f"全量优选达标 ({d_val}ms / {speed_val:.2f}MB/s)")
                                self.root.after(0, self.refresh_tables)
                            else:
                                spd_reason = "下行测速中断/失败" if speed_val < 0 else f"下行未达标 ({speed_val:.2f} < {min_speed} MB/s)"
                                self.speed_blacklist.add(node_name)
                                self.favorites.discard(node_name)
                                self.record_blacklist_reason(node_name, spd_reason)
                                if ep:
                                    self.speed_blacklist.add(ep)
                                    self.record_blacklist_reason(ep, spd_reason)
                                for same_n in ep_to_untested.get(ep, []):
                                    self.speed_blacklist.add(same_n)
                                    self.favorites.discard(same_n)
                                    self.record_blacklist_reason(same_n, spd_reason)
                                if ep in self.verified_nodes:
                                    del self.verified_nodes[ep]
                                newly_speed_blacklisted += 1
                                self.log(f"【低速直接淘汰】节点 {node_name} 速度 {speed_val:.2f} MB/s 未达标(≥{min_speed} MB/s)，直接拉黑！")
                            continue

                        target_group = None
                        if "🚀 节点选择" in proxies_map and node_name in proxies_map["🚀 节点选择"].get("all", []):
                            target_group = "🚀 节点选择"
                        elif node_name in global_all:
                            target_group = "GLOBAL"
                        else:
                            for g_name, g_info in proxies_map.items():
                                if g_info.get("type", "").lower() == "selector" and g_name != "GLOBAL":
                                    if node_name in g_info.get("all", []):
                                        target_group = g_name
                                        break

                        if not target_group:
                            self.node_speeds[node_name] = -1.0
                            self.speed_blacklist.add(node_name)
                            self.favorites.discard(node_name)
                            self.record_blacklist_reason(node_name, "未找到代理选择策略组")
                            if ep:
                                self.speed_blacklist.add(ep)
                                self.record_blacklist_reason(ep, "未找到代理选择策略组")
                            for same_n in ep_to_untested.get(ep, []):
                                self.speed_blacklist.add(same_n)
                                self.favorites.discard(same_n)
                                self.record_blacklist_reason(same_n, "未找到代理选择策略组")
                            if ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                            newly_speed_blacklisted += 1
                            continue

                        if target_group not in orig_group_selections:
                            orig_group_selections[target_group] = proxies_map.get(target_group, {}).get("now", "")

                        enc_tg = urllib.parse.quote(target_group, safe="")
                        self._call_api(f"/proxies/{enc_tg}", method="PUT", data=json.dumps({"name": node_name}).encode("utf-8"))

                        if target_group != "GLOBAL" and target_group in global_all:
                            enc_glb = urllib.parse.quote("GLOBAL", safe="")
                            self._call_api(f"/proxies/{enc_glb}", method="PUT", data=json.dumps({"name": target_group}).encode("utf-8"))

                        time.sleep(0.1)

                        speed_val = -1.0
                        total_bytes = 0
                        speed_timeout = max(1.5, min(2.5, round(duration + 0.5, 1)))
                        node_deadline = time.time() + duration + 1.0
                        try:
                            req = urllib.request.Request(
                                speed_url,
                                headers={
                                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                                    "Connection": "close",
                                },
                            )
                            with speed_opener.open(req, timeout=speed_timeout) as resp:
                                start_time = time.time()
                                chunk_size = 16 * 1024
                                while time.time() - start_time < duration:
                                    if time.time() >= node_deadline or not self.is_pipeline_running:
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
                        self.node_speeds[node_name] = speed_val

                        if node_name not in self.node_speed_history:
                            self.node_speed_history[node_name] = []
                        self.node_speed_history[node_name].append(max(0.0, speed_val))
                        self.node_speed_history[node_name] = self.node_speed_history[node_name][-4:]

                        # 严格拉黑淘汰：单次测速不达标(< min_speed)或失败(<0)直接加入低速黑名单！
                        if speed_val >= min_speed and node_name not in self.speed_blacklist and self.is_asian_node(node_name):
                            premium_nodes.append(node_name)
                            self.favorites.add(node_name)
                            d_val = self.node_delays.get(node_name, 0)
                            self.record_fav_reason(node_name, f"全量优选达标 ({d_val}ms / {speed_val:.2f}MB/s)")
                            self.root.after(0, self.refresh_tables)

                            if target_node_limit > 0 and len(premium_nodes) >= target_node_limit:
                                hit_target_early = True
                                break
                        else:
                            spd_reason = "下行测速中断/失败" if speed_val < 0 else f"下行未达标 ({speed_val:.2f} < {min_speed} MB/s)"
                            self.speed_blacklist.add(node_name)
                            self.favorites.discard(node_name)
                            self.record_blacklist_reason(node_name, spd_reason)
                            if ep:
                                self.speed_blacklist.add(ep)
                                self.record_blacklist_reason(ep, spd_reason)
                            for same_n in ep_to_untested.get(ep, []):
                                self.speed_blacklist.add(same_n)
                                self.favorites.discard(same_n)
                                self.record_blacklist_reason(same_n, spd_reason)
                            if ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                            newly_speed_blacklisted += 1
                            self.log(f"【低速直接淘汰】节点 {node_name} 速度 {speed_val:.2f} MB/s 未达标(≥{min_speed} MB/s)，直接拉黑！")

                finally:
                    for g_name, orig_choice in orig_group_selections.items():
                        if orig_choice:
                            enc = urllib.parse.quote(g_name, safe="")
                            self._call_api(f"/proxies/{enc}", method="PUT", data=json.dumps({"name": orig_choice}).encode("utf-8"))

                    if orig_global:
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self._call_api(f"/proxies/{enc_glb}", method="PUT", data=json.dumps({"name": orig_global}).encode("utf-8"))

                    mode_guard.__exit__(None, None, None)

                if not self.is_pipeline_running:
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                self.root.after(0, lambda: self.status_label.config(text="[步骤 4/4] 写入 Script.js 并触发热键秒级刷新..."))

                self.favorites.update(premium_nodes)
                self.deduplicate_favorites_by_endpoint()
                self.process_verified_lifecycle(list(self.favorites), [])
                self.purge_invalid_and_blacklisted_from_all_pools()
                self.save_persisted_config()
                self.root.after(0, self.refresh_tables)
                self.root.after(0, self.refresh_verified_table)
                self.root.after(0, self.refresh_stars_table)

                write_ok, err_msg = self.do_write_script_file(list(self.favorites))

                hotkey_ok = False
                hotkey_msg = ""
                if write_ok:
                    time.sleep(0.5)
                    hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()

                loaded_ok = False
                loaded_msg = ""
                target_check_nodes = list(self.favorites) if self.favorites else self.all_nodes
                if target_check_nodes:
                    self.root.after(0, lambda: self.status_label.config(text="正在探测 Clash Verge 内核装载状态..."))
                    loaded_ok, loaded_msg = self.wait_for_kernel_reload(target_check_nodes, max_wait_sec=10)
                    self.log(f"内核装载探测: {loaded_msg}")

                cf_ok, cf_msg = False, ""
                if self.get_cf_worker_config()[0]:
                    self.root.after(0, lambda: self.status_label.config(text="正在推送并净化 Cloudflare Worker 三大池..."))
                    cf_ok, cf_msg = self.sync_all_pools_to_cf_worker()
                    self.log(f"Cloudflare Worker 三池全量净化同步: {cf_msg}")

                self.log(f"全量大优选结束：共入选 {len(premium_nodes)} 个优质极速节点，Script.js 规则已写入并触发热重载生效！")

                self.root.after(
                    0,
                    lambda: self._on_pipeline_finished(
                        newly_delay_blacklisted, newly_speed_blacklisted, len(candidates), premium_nodes, max_delay, min_speed, bl_delay_threshold, speed_bl_threshold, speed_bl_rounds, write_ok, err_msg, hotkey_ok, hotkey_msg, hit_target_early, target_node_limit, cf_ok, cf_msg
                    ),
                )

            except Exception as e:
                err_detail = traceback.format_exc()
                self.log(f"执行发生异常：\n{err_detail}")
                self.root.after(0, lambda: self._on_pipeline_error(err_detail))

        threading.Thread(target=_pipeline_worker, daemon=True).start()

    # ==================== 优质池复检 (Colo 轨迹更新) ====================
    def start_fav_review_pipeline(self):
        if self.is_pipeline_running:
            return

        self.last_fav_run_timestamp = time.time()
        self.save_persisted_config()
        self.update_last_run_display()
        self.log("⚡ 启动优质精选池复检流程...")

        try:
            f_max_d = int(self.fav_max_delay_var.get().strip()) if self.fav_max_delay_var.get().strip().isdigit() else 80
            f_min_s = float(self.fav_min_speed_var.get().strip()) if self.fav_min_speed_var.get().strip() else 8.0
            f_rounds = max(1, int(self.fav_rounds_var.get().strip())) if self.fav_rounds_var.get().strip().isdigit() else 2
            try:
                f_duration = max(0.5, float(self.fav_speed_duration_var.get().strip()))
            except Exception:
                f_duration = 2.0
            f_jitter_min_d = int(self.fav_jitter_min_delay_var.get().strip()) if hasattr(self, "fav_jitter_min_delay_var") and self.fav_jitter_min_delay_var.get().strip().isdigit() else 70
            f_jitter_up_th = int(self.fav_jitter_up_threshold_var.get().strip()) if hasattr(self, "fav_jitter_up_threshold_var") and self.fav_jitter_up_threshold_var.get().strip().isdigit() else 15

            target_hk = int(self.fav_target_hk_count_var.get().strip()) if self.fav_target_hk_count_var.get().strip().isdigit() else 3
            target_nohk = int(self.fav_target_nohk_count_var.get().strip()) if self.fav_target_nohk_count_var.get().strip().isdigit() else 5

            test_url = self.test_url_var.get().strip()
            speed_url = self.speed_url_var.get().strip()
            timeout_ms = int(self.test_timeout_var.get().strip()) if self.test_timeout_var.get().strip().isdigit() else 1500
        except Exception as err:
            messagebox.showerror("参数错误", f"优质池专属参数格式错误：\n{str(err)}")
            return

        self.align_favorites_with_current_subscription()
        self.auto_filter_and_blacklist_non_asia_nodes()
        active_fav_targets = [n for n in self.favorites if n in self.all_nodes and self.is_asian_node(n)]

        if not active_fav_targets:
            if self.fav_fallback_enabled_var.get():
                self.root.after(0, lambda: self._trigger_fallback_regeneration("优质池中无存活节点"))
            else:
                self.log("优质池中无存活节点，且已关闭自动唤醒全量大优选。")
                messagebox.showinfo("提示", "优质精选池中暂无可用的存活节点。")
            return

        if not self.test_connection(auto_sync=False):
            messagebox.showwarning("提示", "无法连接内核！")
            return

        for n in active_fav_targets:
            self.node_delays[n] = None
            self.node_history[n] = []
        self.refresh_tables()

        self.is_pipeline_running = True
        self.btn_run_pipeline.config(state="disabled")
        self.btn_stop_pipeline.config(state="normal", text="⏹ 终止任务")
        self.file_combo.config(state="disabled")

        def _fav_worker():
            try:
                tot = len(active_fav_targets)
                self.log(f"优质池待复测节点共 {tot} 个 (端点去重版 | 达标即停={self.fav_quota_early_stop_var.get()})")
                self.root.after(0, lambda: self.status_label.config(text=f"[优质池复测] 正在快速检测 {tot} 个优质候选延迟..."))

                for r in range(1, f_rounds + 1):
                    if not self.is_pipeline_running:
                        break

                    ep_to_nodes = {}
                    for n in active_fav_targets:
                        ep = self.get_node_endpoint(n)
                        ep_to_nodes.setdefault(ep, []).append(n)

                    def _fav_delay(endpoint):
                        if not self.is_pipeline_running:
                            return
                        rep_node = ep_to_nodes[endpoint][0]
                        enc_name = urllib.parse.quote(rep_node, safe="")
                        enc_url = urllib.parse.quote(test_url, safe="")
                        res = self._call_api(f"/proxies/{enc_name}/delay?timeout={timeout_ms}&url={enc_url}", timeout=(timeout_ms / 1000.0) + 0.6)
                        cur_d = res["delay"] if (res and "delay" in res) else 99999
                        if cur_d < 99999:
                            self.record_delay_sample(endpoint, cur_d)

                        for n in ep_to_nodes[endpoint]:
                            self.node_delays[n] = cur_d
                            if n not in self.node_history:
                                self.node_history[n] = []
                            self.node_history[n].append(cur_d)
                            self.node_history[n] = self.node_history[n][-f_rounds:]
                            if cur_d < 99999:
                                self.record_delay_sample(n, cur_d)

                    with ThreadPoolExecutor(max_workers=8) as ex:
                        list(ex.map(_fav_delay, list(ep_to_nodes.keys())))

                    self.root.after(0, self.refresh_tables)
                    if not self.is_pipeline_running:
                        break
                    time.sleep(0.5)

                if not self.is_pipeline_running:
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                # 达标初筛候选先进行实时 Colo 校准与 7 天滑动桶记录
                temp_passed = []
                for n in active_fav_targets:
                    hist = self.node_history.get(n, [99999])
                    best_d = min(hist[-f_rounds:]) if hist else 99999
                    if best_d > f_max_d or best_d >= 99999:
                        d_reason = "延迟超时 (≥99999ms)" if best_d >= 99999 else f"复测延迟淘汰 ({best_d}ms > {f_max_d}ms)"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, d_reason)
                        ep = self.get_node_endpoint(n)
                        if ep:
                            self.record_blacklist_reason(ep, d_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        self.log(f"【优质淘汰-延迟超标】节点 {n} 延迟 {best_d}ms 未达门槛(≤{f_max_d}ms)，直接拉黑淘汰！")
                        continue

                    # 节点抖动拉黑机制：最低延迟≥设定值且向上抖动≥设定值，直接淘汰（最高延迟<设定最低延迟则豁免）
                    is_j_bad, j_min, j_up = self.check_node_jitter_blacklisted(
                        hist[-f_rounds:], f_jitter_min_d, f_jitter_up_th
                    )
                    if is_j_bad:
                        j_reason = f"复测抖动淘汰 (底{j_min}ms 抖动+{j_up}ms)"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, j_reason)
                        ep = self.get_node_endpoint(n)
                        if ep:
                            self.record_blacklist_reason(ep, j_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        self.log(f"【优质淘汰-抖动超标】节点 {n} 最低延迟 {j_min}ms (≥{f_jitter_min_d}ms)，向上抖动 +{j_up}ms (≥{f_jitter_up_th}ms)，直接拉黑淘汰！")
                        continue

                    temp_passed.append(n)

                def _probe_fav_colo(n):
                    ep = self.get_node_endpoint(n)
                    if ":" in ep:
                        ip, port = ep.split(":", 1)
                        c_code, c_disp = get_cf_colo_raw(ip, port, timeout=1.5)
                        self.record_colo_sample(n, ep, c_code, c_disp)

                with ThreadPoolExecutor(max_workers=10) as ex:
                    list(ex.map(_probe_fav_colo, temp_passed))
                self.root.after(0, self.refresh_tables)

                # 严格漂移检测：发生机房漂移一次即直接拉黑淘汰
                drift_passed = []
                now_fav_t = time.time()
                for n in temp_passed:
                    ep = self.get_node_endpoint(n)
                    colo_hist = self.node_colo_history.get(n, self.node_colo_history.get(ep, []))
                    _, _, has_drift, drift_disp = self.analyze_colo_stats(colo_hist, now_fav_t, node_name=n)
                    if has_drift:
                        drift_reason = f"机房漂移 ({drift_disp})"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, drift_reason)
                        if ep:
                            self.record_blacklist_reason(ep, drift_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        self.log(f"【优质淘汰-机房漂移】节点 {n} 发生机房漂移 ({drift_disp})，直接拉黑淘汰！")
                    else:
                        drift_passed.append(n)
                temp_passed = drift_passed

                hk_candidates = []
                nohk_candidates = []

                for n in temp_passed:
                    if not self.is_asian_node(n):
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, "非亚洲地区/命名")
                        continue
                    if self.is_node_hongkong(n):
                        hk_candidates.append(n)
                    else:
                        nohk_candidates.append(n)

                hk_candidates.sort(key=lambda n: min(self.node_history.get(n, [99999])))
                nohk_candidates.sort(key=lambda n: min(self.node_history.get(n, [99999])))
                self.log(f"优质复检初筛通过（经Colo物理核验）：香港候选 {len(hk_candidates)} 个，非香港候选 {len(nohk_candidates)} 个")


                proxies_data = self._call_api("/proxies") or {}
                proxies_map = proxies_data.get("proxies", {})
                global_info = proxies_map.get("GLOBAL", {})
                orig_global = global_info.get("now", "")
                global_all = global_info.get("all", [])

                mixed_port = self.get_clash_mixed_port()
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
                early_stop_enabled = self.fav_quota_early_stop_var.get()

                fav_mode_guard = ClashModeGuard(self.clash_client, temporary_mode="global")
                fav_mode_guard.__enter__()
                try:

                    def _test_single_speed(n, track_label, cur_cnt, tgt_cnt):
                        ep = self.get_node_endpoint(n)
                        if ep in tested_ep_speeds:
                            spd = tested_ep_speeds[ep]
                            self.node_speeds[n] = spd
                            if n not in self.node_speed_history:
                                self.node_speed_history[n] = []
                            self.node_speed_history[n].append(max(0.0, spd))
                            self.node_speed_history[n] = self.node_speed_history[n][-4:]
                            return spd

                        tgt_text = f"{tgt_cnt}" if early_stop_enabled else "全测"
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"[优质复测-{track_label}] 目标:{cur_cnt}/{tgt_text} | 测速: {n[:18]}..."
                        ))

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
                        self._call_api(f"/proxies/{enc_tg}", method="PUT", data=json.dumps({"name": n}).encode("utf-8"))

                        if target_group != "GLOBAL" and target_group in global_all:
                            enc_glb = urllib.parse.quote("GLOBAL", safe="")
                            self._call_api(f"/proxies/{enc_glb}", method="PUT", data=json.dumps({"name": target_group}).encode("utf-8"))

                        time.sleep(0.1)

                        speed_val = 0.0
                        total_bytes = 0
                        fav_speed_timeout = max(1.5, min(2.5, round(f_duration + 0.5, 1)))
                        fav_node_deadline = time.time() + f_duration + 1.0
                        try:
                            req = urllib.request.Request(
                                speed_url,
                                headers={"User-Agent": "Mozilla/5.0", "Connection": "close"}
                            )
                            with speed_opener.open(req, timeout=fav_speed_timeout) as resp:
                                st = time.time()
                                chunk_size = 16 * 1024
                                while time.time() - st < f_duration:
                                    if time.time() >= fav_node_deadline or not self.is_pipeline_running:
                                        break
                                    ch = resp.read(chunk_size)
                                    if not ch:
                                        break
                                    total_bytes += len(ch)
                                el = time.time() - st
                                speed_val = round((total_bytes / (1024 * 1024)) / el, 2) if (el > 0 and total_bytes > 0) else 0.0
                        except Exception:
                            speed_val = -1.0

                        tested_ep_speeds[ep] = speed_val
                        self.node_speeds[n] = speed_val

                        if n not in self.node_speed_history:
                            self.node_speed_history[n] = []
                        self.node_speed_history[n].append(max(0.0, speed_val))
                        self.node_speed_history[n] = self.node_speed_history[n][-4:]

                        return speed_val

                    for n in hk_candidates:
                        if not self.is_pipeline_running:
                            break
                        if early_stop_enabled and target_hk > 0 and len(qualified_hk) >= target_hk:
                            self.log(f"优质复测-香港队列已达目标 ({len(qualified_hk)}/{target_hk})，早停")
                            break
                        spd = _test_single_speed(n, "香港", len(qualified_hk), target_hk)
                        if spd >= f_min_s:
                            qualified_hk.append(n)
                            cur_d = self.node_delays.get(n, 0)
                            self.record_fav_reason(n, f"复测考核留任 ({cur_d}ms / {spd:.2f}MB/s)")
                            self.root.after(0, self.refresh_tables)
                        else:
                            spd_reason = "下行测速中断/失败" if spd < 0 else f"复测下行淘汰 ({spd:.2f} < {f_min_s} MB/s)"
                            self.speed_blacklist.add(n)
                            self.favorites.discard(n)
                            self.record_blacklist_reason(n, spd_reason)
                            ep = self.get_node_endpoint(n)
                            if ep:
                                self.record_blacklist_reason(ep, spd_reason)
                            if ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                            self.log(f"【优质淘汰-低速淘汰】香港节点 {n} 下行 {spd:.2f} MB/s 未达标(≥{f_min_s} MB/s)，直接拉黑淘汰！")

                    for n in nohk_candidates:
                        if not self.is_pipeline_running:
                            break
                        if early_stop_enabled and target_nohk > 0 and len(qualified_nohk) >= target_nohk:
                            self.log(f"优质复测-非香港队列已达目标 ({len(qualified_nohk)}/{target_nohk})，早停")
                            break
                        spd = _test_single_speed(n, "非香港", len(qualified_nohk), target_nohk)
                        if spd >= f_min_s:
                            qualified_nohk.append(n)
                            cur_d = self.node_delays.get(n, 0)
                            self.record_fav_reason(n, f"复测考核留任 ({cur_d}ms / {spd:.2f}MB/s)")
                            self.root.after(0, self.refresh_tables)
                        else:
                            spd_reason = "下行测速中断/失败" if spd < 0 else f"复测下行淘汰 ({spd:.2f} < {f_min_s} MB/s)"
                            self.speed_blacklist.add(n)
                            self.favorites.discard(n)
                            self.record_blacklist_reason(n, spd_reason)
                            ep = self.get_node_endpoint(n)
                            if ep:
                                self.record_blacklist_reason(ep, spd_reason)
                            if ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                            self.log(f"【优质淘汰-低速淘汰】非香港节点 {n} 下行 {spd:.2f} MB/s 未达标(≥{f_min_s} MB/s)，直接拉黑淘汰！")

                finally:
                    for g_name, orig_choice in orig_group_selections.items():
                        if orig_choice:
                            enc = urllib.parse.quote(g_name, safe="")
                            self._call_api(f"/proxies/{enc}", method="PUT", data=json.dumps({"name": orig_choice}).encode("utf-8"))

                    if orig_global:
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self._call_api(f"/proxies/{enc_glb}", method="PUT", data=json.dumps({"name": orig_global}).encode("utf-8"))

                    fav_mode_guard.__exit__(None, None, None)

                if not self.is_pipeline_running:
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                total_final_selected = qualified_hk + qualified_nohk
                self.save_persisted_config()

                self.process_verified_lifecycle(total_final_selected, active_fav_targets)

                self.root.after(
                    0,
                    lambda: self._on_fav_review_finished(
                        tot, len(qualified_hk), len(qualified_nohk), target_hk, target_nohk, total_final_selected, f_max_d, f_min_s
                    ),
                )

            except Exception as e:
                err_detail = traceback.format_exc()
                self.log(f"优质池复测异常：\n{err_detail}")
                self.root.after(0, lambda: self._on_pipeline_error(err_detail))

        threading.Thread(target=_fav_worker, daemon=True).start()

    def _on_fav_review_finished(self, total_tested, qual_hk_cnt, qual_nohk_cnt, target_hk, target_nohk, total_nodes, f_max_d, f_min_s):
        self.is_pipeline_running = False
        self.btn_run_pipeline.config(state="normal")
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 终止任务")
        self.file_combo.config(state="readonly")
        self.sort_tree(self.trees["fav"], "speed", True)

        self.log(f"优质复检统计：香港达标 {qual_hk_cnt}/{target_hk}，非香港达标 {qual_nohk_cnt}/{target_nohk} (已同步沉淀池)")

        fallback_enabled = self.fav_fallback_enabled_var.get()
        hk_lack = (target_hk > 0 and qual_hk_cnt < target_hk)
        nohk_lack = (target_nohk > 0 and qual_nohk_cnt < target_nohk)

        if fallback_enabled and (hk_lack or nohk_lack):
            reasons = []
            if hk_lack:
                reasons.append(f"香港达标({qual_hk_cnt}/{target_hk})")
            if nohk_lack:
                reasons.append(f"非香港达标({qual_nohk_cnt}/{target_nohk})")
            reason_str = "、".join(reasons)

            if len(total_nodes) > 0:
                self.do_write_script_file(total_nodes)
                trigger_verge_reactivate_hotkey()

            self.log(f"检测到配额不足且已开启唤醒开关，触发自愈大优选：{reason_str}")
            self._trigger_fallback_regeneration(f"优质复测不足：{reason_str}")
            return

        write_ok, err_msg = self.do_write_script_file(total_nodes)
        hotkey_ok = False
        if write_ok:
            time.sleep(0.5)
            hotkey_ok, _ = trigger_verge_reactivate_hotkey()

        target_check_favs = total_nodes if total_nodes else self.all_nodes
        if target_check_favs:
            loaded_ok, loaded_msg = self.wait_for_kernel_reload(target_check_favs, max_wait_sec=10)
            self.log(f"优质复测内核装载探测: {loaded_msg}")

        status_txt = f"优质复测完毕！主力 {qual_hk_cnt} 个香港 + {qual_nohk_cnt} 个非香港已生效"
        self.status_label.config(text=status_txt)
        self.log(f"优质复检已写入 Script.js 并触发热键生效 (香港:{qual_hk_cnt}, 非港:{qual_nohk_cnt})")

        notify_msg = f"优质复检完毕：精选香港 {qual_hk_cnt} 个 + 非香港 {qual_nohk_cnt} 个，热键已刷新生效！"
        send_system_notification("优质复测完毕", notify_msg)

        # 全量同步净化推送远端 Worker 三大池 (/auto.txt, /verified.txt, /)
        if self.get_cf_worker_config()[0]:
            self.sync_all_pools_to_cf_worker()

        if self.root.winfo_viewable():
            mode_desc = "达标即停模式" if self.fav_quota_early_stop_var.get() else "全测获取全部合格模式"
            fallback_desc = "已开启" if fallback_enabled else "已关闭 (不足不唤醒)"
            msg = (
                f"🎯【优质池双轨复检完毕】\n\n"
                f"• 当前运行模式：{mode_desc}\n"
                f"• 不足唤醒大优选：{fallback_desc}\n\n"
                f"• 香港极速主力：{qual_hk_cnt} / {target_hk} 个\n"
                f"• 非香港主力：{qual_nohk_cnt} / {target_nohk} 个\n"
                f"• 标准门槛：[延迟≤{f_max_d}ms 且 下行≥{f_min_s}MB/s]\n\n"
                f"⏳ 达标节点已自动传送至【沉淀孵化池】并记入 7 天滑动 Colo 时序桶追踪考核！\n\n"
            )
            if write_ok and hotkey_ok:
                msg += "✅ 这批极速主力已自动写入 Script.js 并通过热键瞬间刷新 Verge！"
            elif not write_ok:
                msg += f"❌ 自动写入 Script.js 失败：{err_msg}"
            else:
                msg += "⚠️ 已写入 Script.js，热键模拟失败，请手动按下 Ctrl+Shift+F12。"
            messagebox.showinfo("优质复测结果", msg)

    def _trigger_fallback_regeneration(self, reason_detail):
        msg = f"检测到【{reason_detail}】，自动启动全量订阅大优选补充节点池..."
        self.status_label.config(text=f"🔄 自愈闭环触发：{msg}")
        self.log(f"🔄 唤醒动作执行：{msg}")
        send_system_notification("自愈闭环触发", msg)
        self.root.after(800, self.start_full_auto_pipeline)

    def align_favorites_with_current_subscription(self):
        return align_favorites_with_current_subscription(self.favorites, self.all_nodes, self.resolve_node_to_current)

    def deduplicate_favorites_by_endpoint(self):
        favs, _ = deduplicate_favorites_by_endpoint(
            self.favorites,
            self.all_nodes,
            self.node_details,
            self.get_node_endpoint,
            self.choose_canonical_node_name,
        )
        return favs

    def clean_offline_favorites(self):
        return clean_offline_favorites(
            self.favorites,
            self.all_nodes,
            self.local_blacklist,
            self.speed_blacklist,
            self.get_node_endpoint,
        )

    def sync_favorites_to_verge(self, show_notify=True):
        """
        一键双向对齐并即时同步精选池到 Clash Verge 策略组
        """
        self.align_favorites_with_current_subscription()
        self.purge_invalid_and_blacklisted_from_all_pools()
        self.save_persisted_config()
        self.refresh_tables()
        self.refresh_verified_table()
        self.refresh_stars_table()

        fav_list = list(self.favorites)
        write_ok, err_msg = self.do_write_script_file(fav_list)
        if write_ok:
            time.sleep(0.2)
            trigger_verge_reactivate_hotkey()

        if show_notify:
            if write_ok:
                msg = f"✅ 已成功将精选池 {len(fav_list)} 个节点即时写入 Script.js 并热激活 Clash Verge！\n\nClash 策略组【⚡ 自动选择】已完全对齐。"
                self.log(f"一键同步: {len(fav_list)} 个精选节点已写入 Script.js 并热激活 Verge")
                self.status_label.config(text=f"已同步 {len(fav_list)} 个精选节点至 Clash Verge")
                messagebox.showinfo("同步成功", msg)
            else:
                self.log(f"一键同步失败: {err_msg}")
                messagebox.showerror("同步失败", f"写入 Script.js 失败：\n{err_msg}")

    def _on_fetch_failed_abort(self, err_reason):
        self.is_pipeline_running = False
        self.btn_run_pipeline.config(state="normal")
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 终止任务")
        self.file_combo.config(state="readonly")

        tip_msg = f"❌ 远程最新订阅同步失败（{err_reason}），已终止任务，拒绝使用陈旧缓存！"
        self.status_label.config(text=tip_msg)
        self.log(f"订阅同步失败任务中止: {err_reason}")
        send_system_notification("优选终止 (拒绝旧缓存)", f"无法拉取远程最新订阅: {err_reason}。\n已按要求终止任务。")

        if self.root.winfo_viewable():
            messagebox.showerror(
                "订阅同步失败 (任务已终止)",
                f"未能拉取到远程最新订阅节点：\n\n【错误详情】：{err_reason}\n\n已按要求终止后续流程，未对任何本地旧缓存节点进行无效测试！"
            )

    def _on_pipeline_error(self, err_text):
        self.is_pipeline_running = False
        self.btn_run_pipeline.config(state="normal")
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 终止任务")
        self.file_combo.config(state="readonly")
        self.status_label.config(text="执行异常，任务停止")
        self.log(f"流水线异常中止: {err_text}")
        if self.root.winfo_viewable():
            messagebox.showerror("运行异常", f"执行流水线时出现错误：\n\n{err_text}")
        else:
            send_system_notification("优选异常停止", "流水线运行捕获到异常")

    def _on_pipeline_aborted(self):
        self.is_pipeline_running = False
        self.btn_run_pipeline.config(state="normal")
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 终止任务")
        self.file_combo.config(state="readonly")
        self.status_label.config(text="任务已手动中止，正在保护成果并同步至 Verge...")
        self.log("任务已手动中止，正在保护并同步已测精选节点至 Verge...")
        self.align_favorites_with_current_subscription()
        self.purge_invalid_and_blacklisted_from_all_pools()
        self.save_persisted_config()
        self.refresh_tables()
        write_ok, _ = self.do_write_script_file(list(self.favorites))
        if write_ok:
            time.sleep(0.2)
            trigger_verge_reactivate_hotkey()
        self.status_label.config(text="任务已中止，已测成果已安全同步写入 Verge")

    def _on_pipeline_finished(self, new_delay_bl, new_speed_bl, cand_cnt, premium_nodes, max_d, min_s, d_bl_th, s_bl_th, s_bl_rounds, write_ok, err_msg, hotkey_ok, hotkey_msg, hit_early, target_limit, cf_ok, cf_msg):
        self.is_pipeline_running = False
        self.btn_run_pipeline.config(state="normal")
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 终止任务")
        self.file_combo.config(state="readonly")
        self.sort_tree(self.get_current_tree(), "speed", True)

        p_count = len(premium_nodes)
        extra_note = f"（已集齐 {target_limit} 个达标节点提前完成）" if hit_early else "（已全测完毕待测池所有候选）"
        self.status_label.config(text=f"优选完成！精选优质 {p_count} 个并已生效 {extra_note}")

        cf_note = "已同步至 Cloudflare" if cf_ok else (f"Cloudflare 同步失败({cf_msg})" if self.cf_worker_enabled_var.get() else "未开启 Cloudflare 同步")
        notify_msg = f"本次拉黑: 延迟淘汰 {new_delay_bl} 个, 低速淘汰 {new_speed_bl} 个。精选优质 {p_count} 个已生效！({cf_note})"
        send_system_notification("Clash Verge 优选刷新成功", notify_msg)

        if self.root.winfo_viewable():
            msg = (
                f"🎯【全自动优选与热键生效完毕】\n\n"
                f"1. 订阅同步：通过 MD5 哈希校验，确认最新订阅就绪且装载完成。\n"
                f"2. 延迟淘汰：新增 {new_delay_bl} 个节点延迟未达标(>{max_d}ms)或超时抖动，已直接拉黑淘汰(未测速)。\n"
                f"3. 低速淘汰：新增 {new_speed_bl} 个节点测速下行未达标(<{min_s}MB/s)或失败，已直接拉黑淘汰。\n"
                f"4. 优质精选：精选出 {p_count} 个双达标极速节点{extra_note}。\n\n"
            )
            if write_ok and hotkey_ok:
                msg += "✅ 已自动写入 Script.js 并通过热键瞬间激活 Verge！\n"
            elif not write_ok:
                msg += f"❌ 自动写入 Script.js 失败：{err_msg}\n"
            else:
                msg += f"⚠️ 已写入 Script.js，热键模拟触发失败: {hotkey_msg}\n"

            if self.cf_worker_enabled_var.get():
                if cf_ok:
                    msg += f"☁️ Cloudflare Worker 自动池(/auto.txt)推送成功！({cf_msg})\n"
                else:
                    msg += f"⚠️ Cloudflare Worker 推送失败：{cf_msg}\n"

            messagebox.showinfo("优选结果", msg)

    def sync_runtime_clash_yaml_and_reload(self, premium_tokens, star_tokens=None):
        """
        双保险内核热同步：
        直接按照 Script.js 相同规则把优选优质节点更新至 clash-verge.yaml，
        并通过 PUT /configs?force=true 带真实文件路径通知 Mihomo 秒级重载。
        彻底解决 Windows UIPI 权限隔离导致快捷键无法穿透、必须手动在 Verge 内点击激活的问题。
        """
        clash_runtime_yaml = os.path.join(PARENT_DIR, "clash-verge.yaml")
        if not os.path.exists(clash_runtime_yaml):
            return False, "未找到 clash-verge.yaml 运行时文件"

        try:
            import yaml
            with open(clash_runtime_yaml, "r", encoding="utf-8") as f_y:
                rt_cfg = yaml.safe_load(f_y)

            if not rt_cfg or not isinstance(rt_cfg, dict):
                return False, "clash-verge.yaml 配置格式异常"

            rt_proxies = rt_cfg.get("proxies", [])

            def is_premium(p):
                if not premium_tokens:
                    return True
                name = p.get("name", "")
                ep = f"{p.get('server', '')}:{p.get('port', '')}"
                return name in premium_tokens or ep in premium_tokens

            ex_re = re.compile(r"(香港|HK|Hong\s*Kong|HongKong|中国(?!\s*台湾)|大陆|回国|\bCN\b)", re.IGNORECASE)

            # 1. 【⚡ 自动选择】
            seen_auto = set()
            live_auto_proxies = []
            for p in rt_proxies:
                if not isinstance(p, dict):
                    continue
                ep = f"{p.get('server', '')}:{p.get('port', '')}"
                name = p.get("name", "")
                is_auto_node = ("优质保活" in name) or ("auto" in name.lower())
                if is_auto_node and is_premium(p) and ep not in seen_auto:
                    seen_auto.add(ep)
                    live_auto_proxies.append(name)

            for p in rt_proxies:
                if not isinstance(p, dict):
                    continue
                ep = f"{p.get('server', '')}:{p.get('port', '')}"
                name = p.get("name", "")
                if is_premium(p) and ep not in seen_auto:
                    seen_auto.add(ep)
                    live_auto_proxies.append(name)

            if not live_auto_proxies:
                live_auto_proxies = [p["name"] for p in rt_proxies if isinstance(p, dict) and "name" in p]
            if not live_auto_proxies:
                live_auto_proxies = ["DIRECT"]

            # 2. 【⚡ 自动选择 (非香港)】
            seen_nohk = set()
            live_nohk_proxies = []
            for p in rt_proxies:
                if not isinstance(p, dict):
                    continue
                ep = f"{p.get('server', '')}:{p.get('port', '')}"
                name = p.get("name", "")
                is_auto_node = ("优质保活" in name) or ("auto" in name.lower())
                if is_auto_node and is_premium(p) and not ex_re.search(name) and ep not in seen_nohk:
                    seen_nohk.add(ep)
                    live_nohk_proxies.append(name)

            for p in rt_proxies:
                if not isinstance(p, dict):
                    continue
                ep = f"{p.get('server', '')}:{p.get('port', '')}"
                name = p.get("name", "")
                if is_premium(p) and not ex_re.search(name) and ep not in seen_nohk:
                    seen_nohk.add(ep)
                    live_nohk_proxies.append(name)

            if not live_nohk_proxies:
                live_nohk_proxies = [p["name"] for p in rt_proxies if isinstance(p, dict) and "name" in p and not ex_re.search(p["name"])]
            if not live_nohk_proxies:
                live_nohk_proxies = ["DIRECT"]

            # 3. 【⚡ 自动选择 (典藏)】
            live_star_proxies = []
            rt_names = {p.get("name") for p in rt_proxies if isinstance(p, dict)}
            for item in getattr(self, "stars_nodes", []):
                m_n = item.get("matched_name", "")
                rem = item.get("remark", "")
                if m_n and m_n in rt_names:
                    live_star_proxies.append(m_n)
                elif rem and rem in rt_names:
                    live_star_proxies.append(rem)
            live_star_proxies = list(dict.fromkeys(live_star_proxies))
            if not live_star_proxies:
                live_star_proxies = ["DIRECT"]

            auto_group_name = "⚡ 自动选择"
            auto_group_nohk_name = "⚡ 自动选择 (非香港)"
            auto_group_stars_name = "⚡ 自动选择 (典藏)"

            for g in rt_cfg.get("proxy-groups", []):
                g_name = g.get("name", "")
                if g_name == auto_group_name:
                    g["proxies"] = live_auto_proxies
                elif g_name == auto_group_nohk_name:
                    g["proxies"] = live_nohk_proxies
                elif g_name == auto_group_stars_name:
                    g["proxies"] = live_star_proxies

            # 原子写入防并发写坏
            temp_file = clash_runtime_yaml + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f_out:
                yaml.dump(rt_cfg, f_out, allow_unicode=True, sort_keys=False)
            os.replace(temp_file, clash_runtime_yaml)

            # 热调用内核重载配置（明确传入真实文件路径）
            reload_payload = json.dumps({"path": clash_runtime_yaml}).encode("utf-8")
            self._call_api("/configs?force=true", method="PUT", data=reload_payload)
            return True, f"已热同步至内核，【⚡ 自动选择】生效 {len(live_auto_proxies)} 个优质节点"
        except Exception as y_err:
            return False, str(y_err)

    # ==================== 三代理组 Script.js 生成 ====================
    def do_write_script_file(self, target_nodes=None):
        script_code, premium_tokens, star_tokens = build_script_js(
            favorites=self.favorites,
            stars_nodes=getattr(self, "stars_nodes", []),
            all_nodes=getattr(self, "all_nodes", []),
            node_details=getattr(self, "node_details", {}),
            group_interval=self.group_interval_var.get(),
            group_tolerance=self.group_tolerance_var.get(),
            star_group_interval=self.star_group_interval_var.get(),
            star_group_tolerance=self.star_group_tolerance_var.get(),
            target_nodes=target_nodes,
            is_asian_node_fn=self.is_asian_node,
            get_node_endpoint_fn=self.get_node_endpoint,
            resolve_node_to_current_fn=self.resolve_node_to_current,
            cloud_endpoints=getattr(self, "cloud_endpoints", None),
            node_colo=getattr(self, "node_colo", None),
        )

        ok, write_res = write_script_js(script_code)
        if not ok:
            return False, write_res

        # 核心增强：双引擎热同步 —— 直接原子写入 clash-verge.yaml 并通知 Mihomo API 秒级重载
        sync_ok, sync_msg = self.sync_runtime_clash_yaml_and_reload(premium_tokens, star_tokens)
        if sync_ok:
            self.log(f"双保险内核热同步: {sync_msg}")
        else:
            self.log(f"运行时 YAML 同步提示: {sync_msg}")

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(script_code)
        except Exception:
            pass
        return True, ""

    def manual_write_and_trigger_hotkey(self):
        target_nodes = list(self.favorites)
        if not target_nodes:
            tree = self.get_current_tree()
            selections = tree.selection()
            if selections:
                target_nodes = [tree.item(s, "values")[-1] for s in selections]

        if not target_nodes:
            messagebox.showwarning("提示", "当前没有选定优质节点，请先设为优质或在列表中多选！")
            return

        ok, err = self.do_write_script_file(target_nodes)
        if ok:
            time.sleep(0.2)
            hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()
            if hotkey_ok:
                messagebox.showinfo(
                    "写入并刷新成功",
                    f"已成功将选中的 {len(target_nodes)} 个节点写入 Script.js，并通过全局热键秒级触发 Verge 重新激活！",
                )
            else:
                messagebox.showinfo(
                    "写入成功",
                    f"已写入 Script.js，热键模拟失败（{hotkey_msg}），请手动在键盘按下 Ctrl+Shift+F12 激活刷新。",
                )
            self.status_label.config(text=f"已成功写入 {len(target_nodes)} 个节点并触发热键")
            self.log(f"手动写入 {len(target_nodes)} 个节点至 Script.js 并触发热键生效")
        else:
            messagebox.showerror("写入失败", f"写入失败：{err}")

    def format_history_chain(self, delays):
        if not delays:
            return "-"
        formatted = []
        for d in delays:
            if d >= 99999 or d <= 0:
                formatted.append("✕超时")
            else:
                formatted.append(f"{d}ms")
        return " → ".join(formatted)

    def format_speed_history_chain(self, speeds):
        if not speeds:
            return "-"
        return " → ".join([f"{s:.2f}M" for s in speeds[-4:]])

    def record_delay_sample(self, key_or_name, delay):
        if not delay or delay >= 99999 or delay <= 0:
            return
        now_ts = time.time()
        ep = self.get_node_endpoint(key_or_name) if key_or_name else ""
        keys_to_update = {key_or_name}
        if ep and ep != "127.0.0.1:443":
            keys_to_update.add(ep)
        cutoff = now_ts - 7 * 86400
        for k in keys_to_update:
            if not k:
                continue
            if k not in self.node_delay_history:
                self.node_delay_history[k] = []
            self.node_delay_history[k].append({"ts": now_ts, "d": int(delay)})
            self.node_delay_history[k] = [
                x for x in self.node_delay_history[k] if isinstance(x, dict) and x.get("ts", 0) >= cutoff
            ][-30:]

    def compute_delay_stats(self, node_name, ep=None):
        return compute_delay_stats(
            node_name,
            ep=ep,
            node_history=getattr(self, "node_history", {}),
            node_delays=getattr(self, "node_delays", {}),
            node_delay_history=getattr(self, "node_delay_history", {}),
            get_node_endpoint_fn=self.get_node_endpoint,
        )

    def check_node_jitter_blacklisted(self, delays, jitter_min_delay=80, jitter_up_threshold=20, min_delay_threshold=None, up_jitter_threshold=None):
        return check_node_jitter_blacklisted(
            delays,
            jitter_min_delay=jitter_min_delay,
            jitter_up_threshold=jitter_up_threshold,
            min_delay_threshold=min_delay_threshold,
            up_jitter_threshold=up_jitter_threshold,
        )




    def test_all_nodes_colo(self):
        # 获取当前选中的标签页索引
        current_tab_idx = self.notebook.index(self.notebook.select())
        tree = self.get_current_tree()
        
        # 从当前标签页的 Treeview 中提取所有行显示的节点/IP
        nodes_to_test = []
        for item_id in tree.get_children(""):
            row_vals = tree.item(item_id, "values")
            if not row_vals:
                continue
            # 依据不同标签页的表格结构提取对应的节点名称或IP
            if current_tab_idx in [2, 3]: # 沉淀孵化池 (2) 或 典藏管理池 (3)
                ep = row_vals[0] # 第一列是 IP:端口
                if ep and ep != "-":
                    nodes_to_test.append(ep)
            else: # 活跃待测、优质精选、黑名单等，最后一列是节点名称
                name = row_vals[-1]
                if name and name != "-":
                    nodes_to_test.append(name)
                    
        if not nodes_to_test:
            tab_names = ["📋 活跃待测", "⭐ 优质精选", "⏳ 沉淀孵化", "🏆 典藏管理", "🚫 延迟黑名单", "🐌 低速黑名单"]
            curr_name = tab_names[current_tab_idx] if current_tab_idx < len(tab_names) else "当前"
            messagebox.showinfo("提示", f"【{curr_name}】标签页当前没有可测速的节点！")
            return
        
        def _worker():
            tab_names = ["📋 活跃待测", "⭐ 优质精选", "⏳ 沉淀孵化", "🏆 典藏管理", "🚫 延迟黑名单", "🐌 低速黑名单"]
            curr_name = tab_names[current_tab_idx] if current_tab_idx < len(tab_names) else "当前标签页"
            
            self.root.after(0, lambda: self.status_label.config(text=f"正在测试【{curr_name}】中 {len(nodes_to_test)} 个节点的实时机房 (Colo)..."))
            self.log(f"开始测试【{curr_name}】标签页下的 {len(nodes_to_test)} 个节点的实时机房 (Colo)...")
            
            completed = [0]
            total = len(nodes_to_test)
            
            def _test_one(target_item):
                if ":" in target_item and any(c.isdigit() for c in target_item.split(":")[0]):
                    ep = target_item
                    n_key = None
                else:
                    n_key = target_item
                    ep = self.get_node_endpoint(n_key)
                    
                if ep and ":" in ep:
                    ip, port = ep.split(":", 1)
                    c_code, c_disp = get_cf_colo_raw(ip, port, timeout=1.8)
                    self.record_colo_sample(n_key, ep, c_code, c_disp)
                    
                completed[0] += 1
                if completed[0] % 5 == 0 or completed[0] == total:
                    self.root.after(0, lambda c=completed[0]: self.status_label.config(text=f"当前页测Colo: {c}/{total}"))
            
            with ThreadPoolExecutor(max_workers=20) as ex:
                list(ex.map(_test_one, nodes_to_test))
                
            # 严格漂移检测：当前页测试后，凡发生机房漂移的节点直接拉黑淘汰并移出所有池
            drift_purged_count = 0
            now_t = time.time()
            for target_item in nodes_to_test:
                if ":" in target_item and any(c.isdigit() for c in target_item.split(":")[0]):
                    ep = target_item
                    n_key = self.resolve_star_matches().get(ep, None)
                else:
                    n_key = target_item
                    ep = self.get_node_endpoint(n_key)
                
                colo_hist = self.node_colo_history.get(n_key, self.node_colo_history.get(ep, []))
                if colo_hist:
                    _, _, has_drift, drift_disp = self.analyze_colo_stats(colo_hist, now_t, node_name=n_key)
                    if has_drift:
                        drift_reason = f"机房漂移 ({drift_disp})"
                        if n_key:
                            self.local_blacklist.add(n_key)
                            self.favorites.discard(n_key)
                            self.record_blacklist_reason(n_key, drift_reason)
                        if ep:
                            self.local_blacklist.add(ep)
                            self.record_blacklist_reason(ep, drift_reason)
                            if ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                        drift_purged_count += 1
                        self.log(f"【页面Colo测定-漂移淘汰】{n_key or ep} 发生机房漂移 ({drift_disp})，直接拉黑并清除！")

            if drift_purged_count > 0:
                self.purge_invalid_and_blacklisted_from_all_pools()
                self.do_write_script_file(list(self.favorites))
                trigger_verge_reactivate_hotkey()
                if self.get_cf_worker_config()[0]:
                    self.sync_all_pools_to_cf_worker()

            self.save_persisted_config()
            self.root.after(0, self.refresh_tables)
            self.root.after(0, self.refresh_verified_table)
            self.root.after(0, self.refresh_stars_table)
            
            self.log(f"【{curr_name}】标签页节点实时机房 (Colo) 检测完成！(漂移淘汰: {drift_purged_count} 个)")
            self.root.after(0, lambda: self.status_label.config(text=f"当前标签页 Colo 检测完成！(漂移淘汰:{drift_purged_count})"))
            finish_msg = f"🎉 已成功完成【{curr_name}】中 {total} 个节点的实时机房 (Colo) 测定！"
            if drift_purged_count > 0:
                finish_msg += f"\n\n⚠️ 检测到 {drift_purged_count} 个节点发生机房漂移，已按超严规则直接拉黑淘汰并从所有池及远端 Worker 彻底清除！"
            self.root.after(0, lambda: messagebox.showinfo("完成", finish_msg))
            
        threading.Thread(target=_worker, daemon=True).start()

    def clear_current_tab_colo_history(self):
        """一键清空当前标签页中所有节点的实时机房(Colo)与7天滑动历史数据"""
        current_tab_idx = self.notebook.index(self.notebook.select())
        if current_tab_idx == 6:
            messagebox.showinfo("提示", "【☁️ 云端文本查看】标签页不支持清空机房记录！")
            return

        tree = self.get_current_tree()
        tab_names = ["📋 活跃待测", "⭐ 优质精选", "⏳ 沉淀孵化", "🏆 典藏管理", "🚫 延迟黑名单", "🐌 低速黑名单", "☁️ 云端文本查看"]
        curr_name = tab_names[current_tab_idx] if current_tab_idx < len(tab_names) else "当前页面"

        items = tree.get_children("")
        if not items:
            messagebox.showinfo("提示", f"【{curr_name}】标签页当前没有节点！")
            return

        if not messagebox.askyesno(
            "确认清空机房(Colo)历史",
            f"确定要清空【{curr_name}】中全部 {len(items)} 个节点的机房(Colo)信息与历史采样记录吗？\n\n"
            "• 该操作将清除最新 Colo 结果与 7 天滑动时序数据；\n"
            "• 归零后可点击【🌍 测当前页Colo】从零开始重新记录，以便精准考核与晋升。"
        ):
            return

        cleared_count = 0
        for item_id in items:
            row_vals = tree.item(item_id, "values")
            if not row_vals:
                continue
            if current_tab_idx in [2, 3]:
                ep = row_vals[0]
                n_key = row_vals[-1] if len(row_vals) >= 7 else ""
            else:
                n_key = row_vals[-1]
                ep = self.get_node_endpoint(n_key)

            keys_to_clean = [n_key, ep]
            if ep and ":" in ep:
                keys_to_clean.append(ep.split(":")[0])

            for k in keys_to_clean:
                if k and k != "-":
                    self.node_colo.pop(k, None)
                    self.node_colo_history.pop(k, None)

            if ep in self.verified_nodes:
                self.verified_nodes[ep]["colo"] = "-"
            for s_node in self.stars_nodes:
                if s_node.get("endpoint") == ep or (n_key and s_node.get("matched_name") == n_key):
                    s_node["colo"] = "-"
            cleared_count += 1

        self.save_persisted_config()
        self.refresh_tables()
        self.refresh_verified_table()
        self.refresh_stars_table()

        msg = f"已清空【{curr_name}】共 {cleared_count} 个节点的机房(Colo)记录与7天历史。"
        self.log(f"🧹 {msg} 可点击【🌍 测当前页Colo】重新录入。")
        self.status_label.config(text=msg)
        messagebox.showinfo("清空成功", f"🎉 {msg}\n\n历史采样数据已归零，现在你可以点击【🌍 测当前页Colo】重新采集纯净数据！")

    def sync_favorites_from_auto_text(self, show_notify=False, source_text=None):
        """
        全量同步 Worker 云端 /auto.txt 优质端点至本地【⭐ 优质精选】：
        1. 获取 Worker 远端 /auto.txt 内容（若传入 source_text 则优先使用，否则从 Worker 拉取，无网络则取云端文本框内容）
        2. 提取有效端点 (IP:端口)，在当前订阅中精准匹配所有对应活跃的亚洲节点加入 favorites
        3. 对比迁移现有 favorites 中更名存活的节点，清除下线失效及非亚洲/黑名单节点
        4. 精准写入 Script.js (严格按节点全名匹配，消除通配误差，确保节点管理器与 Clash Verge 自动选择 1:1 绝对对齐)
        5. 触发全局热键 (Ctrl+Shift+F12) 通知 Clash Verge 即刻重载生效
        6. 同步刷新 UI 表格与状态
        """
        raw_text = source_text if source_text else ""
        fetch_err = ""
        base_url = self.cf_worker_url_var.get().strip().rstrip("/")

        if not raw_text and base_url:
            auto_url = f"{base_url}/auto.txt"
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            mixed_port = self.get_clash_mixed_port()
            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            proxy_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
            direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))

            for opener in [proxy_opener, direct_opener]:
                try:
                    req = urllib.request.Request(auto_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                    with opener.open(req, timeout=6) as resp:
                        raw_text = resp.read().decode("utf-8", errors="ignore")
                        if raw_text:
                            break
                except Exception as e:
                    fetch_err = str(e)

        if not raw_text or "❌ 读取失败" in raw_text or "错误：" in raw_text:
            box_text = self.cloud_text_box.get("1.0", tk.END).strip()
            if box_text and "❌ 读取失败" not in box_text and "错误：" not in box_text:
                raw_text = box_text

        if not raw_text or "❌ 读取失败" in raw_text or "错误：" in raw_text:
            if show_notify:
                messagebox.showwarning("同步提示", f"未能获取到 /auto.txt 的有效内容！\n(Worker 请求提示: {fetch_err})")
            return 0, 0

        # 提取端点集合
        auto_eps = set()
        for line in raw_text.splitlines():
            line = line.strip()
            if not line or line.startswith("⏳") or line.startswith("Error") or line.startswith("❌"):
                continue
            if "#" in line:
                ep_part = line.split("#", 1)[0].strip()
            else:
                ep_part = line.split()[0].strip()
            m = re.search(r"([a-zA-Z0-9\.\-]+:\d{1,5})", ep_part)
            if m:
                auto_eps.add(m.group(1))

        self.auto_endpoints.update(auto_eps)

        # 建立端点 -> 当前订阅活跃亚洲节点映射
        ep_to_nodes = {}
        for n in self.all_nodes:
            if not self.is_asian_node(n):
                continue
            ep = self.get_node_endpoint(n)
            if ep and ep != "127.0.0.1:443":
                ep_to_nodes.setdefault(ep, []).append(n)

        # 将 auto.txt 中命中的活跃亚洲节点加入（严格 1 对 1 端点唯一代表录用）
        for ep in auto_eps:
            if ep in ep_to_nodes:
                cands = ep_to_nodes[ep]
                auto_cands = [c for c in cands if "优质保活" in c or "auto" in c.lower()]
                rep_node = auto_cands[0] if auto_cands else cands[0]
                for n in cands:
                    self.local_blacklist.discard(n)
                    self.speed_blacklist.discard(n)
                synced_favs.add(rep_node)

        # 迁移与保留现有存活且为亚洲的优质节点
        for f in list(self.favorites):
            if not self.is_asian_node(f):
                continue
            if f in self.all_nodes:
                self.local_blacklist.discard(f)
                self.speed_blacklist.discard(f)
                synced_favs.add(f)
            else:
                resolved = self.resolve_node_to_current(f)
                if resolved and resolved in self.all_nodes and self.is_asian_node(resolved):
                    self.local_blacklist.discard(resolved)
                    self.speed_blacklist.discard(resolved)
                    synced_favs.add(resolved)

        self.favorites = synced_favs
        self.deduplicate_favorites_by_endpoint()
        self.save_persisted_config()

        # 写入 Script.js 并触发热键激活
        write_ok, err_msg = self.do_write_script_file(list(self.favorites))
        hotkey_ok = False
        if write_ok:
            time.sleep(0.3)
            hotkey_ok, _ = trigger_verge_reactivate_hotkey()

        # 刷新 UI 表格
        self.refresh_tables()
        self.log(f"☁️ 同步 auto.txt 优质池完成：当前优质精选池共 {len(self.favorites)} 个节点")

        if show_notify:
            msg = (
                f"🎉 【auto.txt 优质池同步完成】！\n\n"
                f"• 从 auto.txt 解析出物理端点: {len(auto_eps)} 个\n"
                f"• 当前订阅匹配活跃亚洲优质节点: {len(self.favorites)} 个\n"
                f"• 【📋 活跃待测】页面已完全过滤排除全部优质候选，仅展示未测试纯净节点\n\n"
            )
            if write_ok and hotkey_ok:
                msg += "✅ 已写入 Script.js 并通过热键瞬间刷新激活 Clash Verge！\n优质精选节点与 Clash【⚡ 自动选择】已实现 1:1 绝对对齐。"
            elif not write_ok:
                msg += f"⚠️ 写入 Script.js 失败: {err_msg}"
            else:
                msg += "⚠️ 已写入 Script.js，热键模拟未生效，请手动按下 Ctrl+Shift+F12。"
            messagebox.showinfo("同步成功", msg)

        return len(auto_eps), len(self.favorites)

    def import_cloud_text_to_favorites(self):
        raw_text = self.cloud_text_box.get("1.0", tk.END).strip()
        if not raw_text or "❌ 读取失败" in raw_text or "错误：" in raw_text:
            messagebox.showwarning("提示", "当前文本框没有可导入的有效节点内容！")
            return
        self.sync_favorites_from_auto_text(show_notify=True, source_text=raw_text)


    def _on_notebook_tab_changed(self, event=None):
        try:
            tab_idx = self.notebook.index(self.notebook.select())
            if tab_idx == 2:
                self.refresh_verified_table()
            elif tab_idx == 3:
                self.refresh_stars_table()
            elif tab_idx == 4 and getattr(self, "_delay_black_dirty", True):
                self._render_delay_black_table()
            elif tab_idx == 5 and getattr(self, "_speed_black_dirty", True):
                self._render_speed_black_table()
        except Exception:
            pass

    def _render_delay_black_table(self):
        if "delay_black" not in self.trees:
            return
        tree = self.trees["delay_black"]
        tree.delete(*tree.get_children())
        kw = self.search_var.get().strip().lower()

        seen_d_eps = set()

        for name in self.all_nodes:
            if kw and kw not in name.lower():
                continue
            ep_val = self.get_node_endpoint(name)
            is_asian = self.is_asian_node(name)
            if is_asian:
                is_d_black = (name in self.local_blacklist) or (ep_val and ep_val in self.local_blacklist)
            else:
                is_d_black = True
            if is_d_black:
                ep_key = ep_val if ep_val else name
                if ep_key in seen_d_eps:
                    continue
                seen_d_eps.add(ep_key)

                d_val = self.node_delays.get(name, None)
                if d_val is None:
                    d_str = "已跳过"
                elif d_val >= 99999:
                    d_str = "超时 / 失败"
                else:
                    d_str = f"{d_val} ms"
                colo_str = self.node_colo.get(ep_val, self.node_colo.get(name, "-"))
                colo_hist = self.node_colo_history.get(ep_val, self.node_colo_history.get(name, []))
                colo_hist_str = self.analyze_colo_stats(colo_hist, time.time(), node_name=name)[3]
                cur_avg_str, hist_avg_str = self.compute_delay_stats(name, ep_val)
                delay_hist_str = self.format_history_chain(self.node_history.get(name, []))
                speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(name, []))
                reason_str = self.get_blacklist_reason(name, ep_val)
                row_data = ("🚫 延迟黑名单", colo_str, colo_hist_str, reason_str, d_str, cur_avg_str, delay_hist_str, hist_avg_str, "-", speed_hist_str, name)
                tree.insert("", tk.END, values=row_data, tags=["black_delay"])

        for b_name in self.local_blacklist:
            if b_name not in self.all_nodes:
                if kw and kw not in b_name.lower():
                    continue
                b_ep = self.get_node_endpoint(b_name)
                ep_key = b_ep if b_ep else b_name
                if ep_key in seen_d_eps:
                    continue
                seen_d_eps.add(ep_key)

                s_hist = self.format_speed_history_chain(self.node_speed_history.get(b_name, []))
                cur_avg, hist_avg = self.compute_delay_stats(b_name)
                b_reason = self.get_blacklist_reason(b_name, b_ep)
                row_data = ("🚫 历史黑名单", "-", "-", b_reason, "已跳过", cur_avg, "-", hist_avg, "-", s_hist, b_name)
                tree.insert("", tk.END, values=row_data, tags=["black_delay"])
        self._delay_black_dirty = False

    def _render_speed_black_table(self):
        if "speed_black" not in self.trees:
            return
        tree = self.trees["speed_black"]
        tree.delete(*tree.get_children())
        kw = self.search_var.get().strip().lower()

        seen_s_eps = set()

        for name in self.all_nodes:
            if kw and kw not in name.lower():
                continue
            ep_val = self.get_node_endpoint(name)
            is_s_black = (name in self.speed_blacklist) or (ep_val and ep_val in self.speed_blacklist)
            if is_s_black:
                ep_key = ep_val if ep_val else name
                if ep_key in seen_s_eps:
                    continue
                seen_s_eps.add(ep_key)

                s_val = self.node_speeds.get(name, None)
                s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else ("测速失败" if s_val is not None else "-")
                colo_str = self.node_colo.get(ep_val, self.node_colo.get(name, "-"))
                colo_hist = self.node_colo_history.get(ep_val, self.node_colo_history.get(name, []))
                colo_hist_str = self.analyze_colo_stats(colo_hist, time.time(), node_name=name)[3]
                cur_avg_str, hist_avg_str = self.compute_delay_stats(name, ep_val)
                delay_hist_str = self.format_history_chain(self.node_history.get(name, []))
                speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(name, []))
                reason_str = self.get_blacklist_reason(name, ep_val)
                row_data = ("🐌 低速黑名单", colo_str, colo_hist_str, reason_str, "-", cur_avg_str, delay_hist_str, hist_avg_str, s_str, speed_hist_str, name)
                tree.insert("", tk.END, values=row_data, tags=["black_speed"])

        for s_name in self.speed_blacklist:
            if s_name not in self.all_nodes:
                if kw and kw not in s_name.lower():
                    continue
                s_ep = self.get_node_endpoint(s_name)
                ep_key = s_ep if s_ep else s_name
                if ep_key in seen_s_eps:
                    continue
                seen_s_eps.add(ep_key)

                s_hist = self.format_speed_history_chain(self.node_speed_history.get(s_name, []))
                cur_avg, hist_avg = self.compute_delay_stats(s_name)
                s_reason = self.get_blacklist_reason(s_name, s_ep)
                row_data = ("🐌 历史低速", "-", "-", s_reason, "已跳过", cur_avg, "-", hist_avg, "-", s_hist, s_name)
                tree.insert("", tk.END, values=row_data, tags=["black_speed"])
        self._speed_black_dirty = False

    def refresh_tables(self):
        self.align_favorites_with_current_subscription()
        self.purge_invalid_and_blacklisted_from_all_pools()
        kw = self.search_var.get().strip().lower()
        now = time.time()

        curr_tab = -1
        try:
            curr_tab = self.notebook.index(self.notebook.select())
        except Exception:
            curr_tab = 0

        for tab_k in ["all", "fav"]:
            if tab_k in self.trees:
                self.trees[tab_k].delete(*self.trees[tab_k].get_children())

        if curr_tab == 4:
            if "delay_black" in self.trees:
                self.trees["delay_black"].delete(*self.trees["delay_black"].get_children())
            self._delay_black_dirty = False
        else:
            self._delay_black_dirty = True

        if curr_tab == 5:
            if "speed_black" in self.trees:
                self.trees["speed_black"].delete(*self.trees["speed_black"].get_children())
            self._speed_black_dirty = False
        else:
            self._speed_black_dirty = True

        fav_eps, bl_eps, sbl_eps, star_eps = self.get_pool_endpoint_sets()

        # 1. 待测池节点按端点聚合（严格1对1去重，纯净展示）
        untested_groups = {}
        seen_d_eps = set()
        seen_s_eps = set()

        for name in self.all_nodes:
            ep_val = self.get_node_endpoint(name)
            is_asian = self.is_asian_node(name)
            if not is_asian:
                if name not in self.local_blacklist:
                    self.local_blacklist.add(name)
                is_d_black = True
                is_s_black = False
            else:
                is_d_black = (name in self.local_blacklist) or (ep_val and ep_val in self.local_blacklist)
                is_s_black = not is_d_black and ((name in self.speed_blacklist) or (ep_val and ep_val in self.speed_blacklist))

            # 严格对齐：精选池仅准入 self.favorites 中的代表节点，同端点其他马甲作为别名隔离，绝不重复塞入精选表
            is_fav = not is_d_black and not is_s_black and (name in self.favorites)
            is_fav_alias = not is_d_black and not is_s_black and not is_fav and (ep_val and ep_val in fav_eps)
            is_ver_star = not is_d_black and not is_s_black and not is_fav and not is_fav_alias and ((name in self.verified_nodes) or (ep_val and ep_val in star_eps))

            # 归集待测池
            if not is_d_black and not is_s_black and not is_fav and not is_fav_alias and not is_ver_star:
                key = ep_val if ep_val else name
                untested_groups.setdefault(key, []).append(name)

            # 渲染精选池
            if is_fav:
                if kw and kw not in name.lower():
                    continue
                d_val = self.node_delays.get(name, None)
                tags = ["fav"]
                if d_val is None:
                    d_str = "未测速"
                elif d_val >= 99999:
                    d_str = "超时 / 失败"
                    tags.append("timeout")
                else:
                    d_str = f"{d_val} ms"
                    tags.append("fast" if d_val < 150 else "medium")

                s_val = self.node_speeds.get(name, None)
                s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else ("测速失败" if s_val is not None else "-")
                colo_str = self.node_colo.get(ep_val, self.node_colo.get(name, "-"))
                colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep_val, self.node_colo_history.get(name, [])), now, node_name=name)[3]
                cur_avg_str, hist_avg_str = self.compute_delay_stats(name, ep_val)
                delay_hist_str = self.format_history_chain(self.node_history.get(name, []))
                speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(name, []))
                reason_str = self.get_fav_reason(name, ep_val)
                row_data = ("⭐ 优质候选", colo_str, colo_hist_str, reason_str, d_str, cur_avg_str, delay_hist_str, hist_avg_str, s_str, speed_hist_str, name)
                self.trees["fav"].insert("", tk.END, values=row_data, tags=tags)

            # 延迟黑名单 (按端点去重)
            if is_d_black and curr_tab == 4:
                ep_key = ep_val if ep_val else name
                if ep_key not in seen_d_eps:
                    seen_d_eps.add(ep_key)
                    if not kw or (kw in name.lower()):
                        d_val = self.node_delays.get(name, None)
                        tags = ["black_delay"]
                        if d_val is None:
                            d_str = "已跳过"
                        elif d_val >= 99999:
                            d_str = "超时 / 失败"
                            tags.append("timeout")
                        else:
                            d_str = f"{d_val} ms"
                        colo_str = self.node_colo.get(ep_val, self.node_colo.get(name, "-"))
                        colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep_val, self.node_colo_history.get(name, [])), now, node_name=name)[3]
                        cur_avg_str, hist_avg_str = self.compute_delay_stats(name, ep_val)
                        delay_hist_str = self.format_history_chain(self.node_history.get(name, []))
                        speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(name, []))
                        reason_str = self.get_blacklist_reason(name, ep_val)
                        row_data = ("🚫 延迟黑名单", colo_str, colo_hist_str, reason_str, d_str, cur_avg_str, delay_hist_str, hist_avg_str, "-", speed_hist_str, name)
                        self.trees["delay_black"].insert("", tk.END, values=row_data, tags=tags)

            # 低速黑名单 (按端点去重)
            if is_s_black and curr_tab == 5:
                ep_key = ep_val if ep_val else name
                if ep_key not in seen_s_eps:
                    seen_s_eps.add(ep_key)
                    if not kw or (kw in name.lower()):
                        s_val = self.node_speeds.get(name, None)
                        tags = ["black_speed"]
                        s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else ("测速失败" if s_val is not None else "-")
                        colo_str = self.node_colo.get(ep_val, self.node_colo.get(name, "-"))
                        colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep_val, self.node_colo_history.get(name, [])), now, node_name=name)[3]
                        cur_avg_str, hist_avg_str = self.compute_delay_stats(name, ep_val)
                        delay_hist_str = self.format_history_chain(self.node_history.get(name, []))
                        speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(name, []))
                        reason_str = self.get_blacklist_reason(name, ep_val)
                        row_data = ("🐌 低速黑名单", colo_str, colo_hist_str, reason_str, "-", cur_avg_str, delay_hist_str, hist_avg_str, s_str, speed_hist_str, name)
                        self.trees["speed_black"].insert("", tk.END, values=row_data, tags=tags)

        # 渲染待测池 (对每个唯一端点仅渲染1个主代表节点，彻底杜绝重复)
        display_active_count = 0
        for ep_key, group_nodes in untested_groups.items():
            canonical_name = self.choose_canonical_node_name(group_nodes)
            if kw:
                matched_kw = (kw in canonical_name.lower()) or any(kw in n.lower() for n in group_nodes)
                if not matched_kw:
                    continue

            d_val = self.node_delays.get(canonical_name, self.node_delays.get(ep_key, None))
            tags = []
            if d_val is None:
                d_str = "未测速"
            elif d_val >= 99999:
                d_str = "超时 / 失败"
                tags.append("timeout")
            else:
                d_str = f"{d_val} ms"
                tags.append("fast" if d_val < 150 else "medium")

            s_val = self.node_speeds.get(canonical_name, self.node_speeds.get(ep_key, None))
            if s_val is None:
                s_str = "-"
            elif s_val < 0:
                s_str = "测速失败"
            else:
                s_str = f"{s_val:.2f} MB/s"

            colo_str = self.node_colo.get(ep_key, self.node_colo.get(canonical_name, "-"))
            colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep_key, self.node_colo_history.get(canonical_name, [])), now, node_name=canonical_name)[3]

            cur_avg_str, hist_avg_str = self.compute_delay_stats(canonical_name, ep_key)
            delay_hist_str = self.format_history_chain(self.node_history.get(canonical_name, []))
            speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(canonical_name, []))
            reason_str = "-"

            row_data = ("⚪ 活跃待测", colo_str, colo_hist_str, reason_str, d_str, cur_avg_str, delay_hist_str, hist_avg_str, s_str, speed_hist_str, canonical_name)
            self.trees["all"].insert("", tk.END, values=row_data, tags=tags)
            display_active_count += 1

        for fav_name in self.favorites:
            if fav_name not in self.all_nodes:
                curr_active = self.resolve_node_to_current(fav_name)
                if curr_active and curr_active in self.all_nodes:
                    continue
                if kw and kw not in fav_name.lower():
                    continue
                s_hist = self.format_speed_history_chain(self.node_speed_history.get(fav_name, []))
                colo_str = self.node_colo.get(fav_name, "-")
                colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(fav_name, []), now, node_name=fav_name)[3]
                cur_avg, hist_avg = self.compute_delay_stats(fav_name)
                off_reason = self.get_fav_reason(fav_name)
                off_reason_str = f"{off_reason} (已下线)" if off_reason and off_reason != "优质精选" else "订阅已下线"
                row_data = ("⚠️ 订阅已下线", colo_str, colo_hist_str, off_reason_str, "-", cur_avg, "-", hist_avg, "-", s_hist, fav_name)
                self.trees["fav"].insert("", tk.END, values=row_data, tags=["offline"])

        if curr_tab == 4 and "delay_black" in self.trees:
            for b_name in self.local_blacklist:
                if b_name not in self.all_nodes:
                    if kw and kw not in b_name.lower():
                        continue
                    b_ep = self.get_node_endpoint(b_name)
                    ep_key = b_ep if b_ep else b_name
                    if ep_key in seen_d_eps:
                        continue
                    seen_d_eps.add(ep_key)

                    s_hist = self.format_speed_history_chain(self.node_speed_history.get(b_name, []))
                    cur_avg, hist_avg = self.compute_delay_stats(b_name)
                    b_reason = self.get_blacklist_reason(b_name, b_ep)
                    row_data = ("🚫 历史黑名单", "-", "-", b_reason, "已跳过", cur_avg, "-", hist_avg, "-", s_hist, b_name)
                    self.trees["delay_black"].insert("", tk.END, values=row_data, tags=["black_delay"])

        if curr_tab == 5 and "speed_black" in self.trees:
            for s_name in self.speed_blacklist:
                if s_name not in self.all_nodes:
                    if kw and kw not in s_name.lower():
                        continue
                    s_ep = self.get_node_endpoint(s_name)
                    ep_key = s_ep if s_ep else s_name
                    if ep_key in seen_s_eps:
                        continue
                    seen_s_eps.add(ep_key)

                    s_hist = self.format_speed_history_chain(self.node_speed_history.get(s_name, []))
                    cur_avg, hist_avg = self.compute_delay_stats(s_name)
                    s_reason = self.get_blacklist_reason(s_name, s_ep)
                    row_data = ("🐌 历史低速", "-", "-", s_reason, "已跳过", cur_avg, "-", hist_avg, "-", s_hist, s_name)
                    self.trees["speed_black"].insert("", tk.END, values=row_data, tags=["black_speed"])

        fav_tree_count = len(self.trees["fav"].get_children())
        self.notebook.tab(0, text=f"📋 活跃待测 ({display_active_count})")
        self.notebook.tab(1, text=f"⭐ 优质精选 ({fav_tree_count})")
        self.notebook.tab(2, text=f"⏳ 沉淀孵化 ({len(self.verified_nodes)})")
        self.notebook.tab(3, text=f"🏆 典藏管理 ({len(self.stars_nodes)})")
        self.notebook.tab(4, text=f"🚫 延迟黑名单 ({len(bl_eps) if bl_eps else len(self.local_blacklist)})")
        self.notebook.tab(5, text=f"🐌 低速黑名单 ({len(sbl_eps) if sbl_eps else len(self.speed_blacklist)})")

        if not self.is_pipeline_running:
            self.status_label.config(
                text=f"待测: {display_active_count}  |  优质: {fav_tree_count}  |  孵化: {len(self.verified_nodes)}  |  典藏: {len(self.stars_nodes)}"
            )

    def sort_tree(self, tree, col, reverse):
        items = [(tree.set(k, col), k) for k in tree.get_children("")]
        if col == "delay":

            def _sort_key(x):
                txt = x[0]
                m = re.search(r"(\d+)", txt)
                if m:
                    return int(m.group(1))
                elif "超时" in txt:
                    return 999999
                elif "已跳过" in txt or "-" in txt:
                    return 999997
                return 999998

            items.sort(key=_sort_key, reverse=reverse)
        elif col == "avg_delay":

            def _sort_avg(x):
                txt = x[0]
                m = re.search(r"(\d+)\s*ms", txt)
                if m:
                    return int(m.group(1))
                elif "超时" in txt:
                    return 999999
                return 999998

            items.sort(key=_sort_avg, reverse=reverse)
        elif col == "hist_avg":

            def _sort_hist(x):
                txt = x[0]
                m = re.search(r"(\d+)\s*ms", txt)
                if m:
                    return int(m.group(1))
                return 999998

            items.sort(key=_sort_hist, reverse=reverse)
        elif col == "speed":

            def _sort_speed(x):
                txt = x[0]
                if "MB/s" in txt:
                    try:
                        return float(txt.replace(" MB/s", ""))
                    except Exception:
                        return -1.0
                elif "失败" in txt:
                    return -2.0
                return -3.0

            items.sort(key=_sort_speed, reverse=reverse)
        else:
            items.sort(reverse=reverse)

        for idx, (_, k) in enumerate(items):
            tree.move(k, "", idx)
        tree.heading(col, command=lambda: self.sort_tree(tree, col, not reverse))

    def set_favorite(self):
        tree = self.get_current_tree()
        non_asia_blocked = 0
        added_cnt = 0
        for sel in tree.selection():
            name = tree.item(sel, "values")[-1]
            if not self.is_asian_node(name):
                self.local_blacklist.add(name)
                self.favorites.discard(name)
                non_asia_blocked += 1
                continue
            self.local_blacklist.discard(name)
            self.speed_blacklist.discard(name)
            self.favorites.add(name)
            self.record_fav_reason(name, "手动设为优质")
            added_cnt += 1
        self.deduplicate_favorites_by_endpoint()
        self.save_persisted_config()
        self.refresh_tables()
        if non_asia_blocked > 0:
            self.log(f"⚠️ 已拦截并直接拉黑 {non_asia_blocked} 个非亚洲节点（仅限亚洲节点加入精选）")
        if added_cnt > 0:
            self.log(f"已手动设为优质：{added_cnt} 个亚洲节点")

    def manual_add_delay_blacklist(self):
        tree = self.get_current_tree()
        selections = tree.selection()
        if not selections:
            messagebox.showinfo("提示", "请先在列表中选中需要拉黑的节点！")
            return

        for sel in selections:
            name = tree.item(sel, "values")[-1]
            self.favorites.discard(name)
            self.speed_blacklist.discard(name)
            self.local_blacklist.add(name)
            self.record_blacklist_reason(name, "手动加入延迟黑名单")
            ep = self.get_node_endpoint(name)
            if ep:
                self.local_blacklist.add(ep)
                self.record_blacklist_reason(ep, "手动加入延迟黑名单")
                self.verified_nodes.pop(ep, None)
        self.purge_invalid_and_blacklisted_from_all_pools()
        self.save_persisted_config()
        self.refresh_tables()
        self.refresh_verified_table()
        self.status_label.config(text=f"已手动将选中的 {len(selections)} 个节点加入【延迟黑名单】")
        self.log(f"手动加入延迟黑名单：{len(selections)} 个节点")

    def manual_add_speed_blacklist(self):
        tree = self.get_current_tree()
        selections = tree.selection()
        if not selections:
            messagebox.showinfo("提示", "请先在列表中选中需要拉黑的节点！")
            return

        for sel in selections:
            name = tree.item(sel, "values")[-1]
            self.favorites.discard(name)
            self.local_blacklist.discard(name)
            self.speed_blacklist.add(name)
            self.record_blacklist_reason(name, "手动加入低速黑名单")
            ep = self.get_node_endpoint(name)
            if ep:
                self.speed_blacklist.add(ep)
                self.record_blacklist_reason(ep, "手动加入低速黑名单")
                self.verified_nodes.pop(ep, None)
        self.purge_invalid_and_blacklisted_from_all_pools()
        self.save_persisted_config()
        self.refresh_tables()
        self.refresh_verified_table()
        self.status_label.config(text=f"已手动将选中的 {len(selections)} 个节点加入【低速黑名单】")
        self.log(f"手动加入低速黑名单：{len(selections)} 个节点")

    def remove_from_blacklist(self, tree=None):
        if tree is None:
            tree = self.get_current_tree()
        selections = tree.selection()
        if not selections:
            messagebox.showinfo("提示", "请先在列表中选中要移出黑名单的节点！")
            return

        removed_names = []
        for sel in selections:
            vals = tree.item(sel, "values")
            name = vals[-1] if vals else ""
            if not name:
                continue
            removed_names.append(name)
            self.local_blacklist.discard(name)
            self.speed_blacklist.discard(name)
            if hasattr(self, "blacklist_reasons"):
                self.blacklist_reasons.pop(name, None)

            # 同时彻底拔除物理端点与纯 IP 记录，包括包含该 IP 的历史条目
            ep = self.get_node_endpoint(name)
            if ep:
                self.local_blacklist.discard(ep)
                self.speed_blacklist.discard(ep)
                if hasattr(self, "blacklist_reasons"):
                    self.blacklist_reasons.pop(ep, None)
                if ":" in ep:
                    ip = ep.split(":")[0]
                    self.local_blacklist.discard(ip)
                    self.speed_blacklist.discard(ip)
                    if hasattr(self, "blacklist_reasons"):
                        self.blacklist_reasons.pop(ip, None)
                    for b in list(self.local_blacklist):
                        if ip in b:
                            self.local_blacklist.discard(b)
                            if hasattr(self, "blacklist_reasons"):
                                self.blacklist_reasons.pop(b, None)
                    for s in list(self.speed_blacklist):
                        if ip in s:
                            self.speed_blacklist.discard(s)
                            if hasattr(self, "blacklist_reasons"):
                                self.blacklist_reasons.pop(s, None)

            if name in self.node_speed_history:
                self.node_speed_history[name].clear()
            if ep and ep in self.node_speed_history:
                self.node_speed_history[ep].clear()

        self._all_nodes_set = None
        self.save_persisted_config()
        self.refresh_tables()
        self.status_label.config(text=f"已成功将选中的 {len(removed_names)} 个节点移出黑名单并恢复待测")
        self.log(f"已移出黑名单恢复活跃：{len(removed_names)} 个节点 ({', '.join(removed_names[:3])}{'...' if len(removed_names)>3 else ''})")

    def remove_from_blacklist_and_set_favorite(self, tree=None):
        if tree is None:
            tree = self.get_current_tree()
        selections = tree.selection()
        if not selections:
            messagebox.showinfo("提示", "请先在列表中选中节点！")
            return

        added_cnt = 0
        non_asia_blocked = 0
        for sel in selections:
            vals = tree.item(sel, "values")
            name = vals[-1] if vals else ""
            if not name:
                continue
            if not self.is_asian_node(name):
                self.local_blacklist.add(name)
                non_asia_blocked += 1
                continue

            self.local_blacklist.discard(name)
            self.speed_blacklist.discard(name)
            if hasattr(self, "blacklist_reasons"):
                self.blacklist_reasons.pop(name, None)
            ep = self.get_node_endpoint(name)
            if ep:
                self.local_blacklist.discard(ep)
                self.speed_blacklist.discard(ep)
                if hasattr(self, "blacklist_reasons"):
                    self.blacklist_reasons.pop(ep, None)
                if ":" in ep:
                    ip = ep.split(":")[0]
                    self.local_blacklist.discard(ip)
                    self.speed_blacklist.discard(ip)
                    if hasattr(self, "blacklist_reasons"):
                        self.blacklist_reasons.pop(ip, None)
                    for b in list(self.local_blacklist):
                        if ip in b:
                            self.local_blacklist.discard(b)
                            if hasattr(self, "blacklist_reasons"):
                                self.blacklist_reasons.pop(b, None)
                    for s in list(self.speed_blacklist):
                        if ip in s:
                            self.speed_blacklist.discard(s)
                            if hasattr(self, "blacklist_reasons"):
                                self.blacklist_reasons.pop(s, None)

            self.favorites.add(name)
            self.record_fav_reason(name, "移出黑名单设为优质")
            added_cnt += 1

        self._all_nodes_set = None
        self.deduplicate_favorites_by_endpoint()
        self.save_persisted_config()
        self.refresh_tables()
        if non_asia_blocked > 0:
            self.log(f"⚠️ 已拦截并保持拉黑 {non_asia_blocked} 个非亚洲节点")
        if added_cnt > 0:
            self.status_label.config(text=f"已将选中的 {added_cnt} 个节点移出黑名单并加入精选池")
            self.log(f"已移出黑名单并加入精选：{added_cnt} 个节点")

    def clear_all_blacklists(self):
        tot_d = len(self.local_blacklist)
        tot_s = len(self.speed_blacklist)
        if tot_d == 0 and tot_s == 0:
            messagebox.showinfo("提示", "当前所有黑名单均为空，无需清空！")
            return

        if not messagebox.askyesno(
            "一键清空黑名单确认",
            f"确定要一键清空全部黑名单吗？\n\n"
            f"• 延迟黑名单：{tot_d} 条\n"
            f"• 低速黑名单：{tot_s} 条\n\n"
            f"清空后所有被拉黑的节点将重置状态，并全部恢复至【📋 活跃待测】池，\n"
            f"可重新进行全量测速、计分与典藏晋升！"
        ):
            return

        self.local_blacklist.clear()
        self.speed_blacklist.clear()
        if hasattr(self, "blacklist_timestamps") and isinstance(self.blacklist_timestamps, dict):
            self.blacklist_timestamps.clear()
        if hasattr(self, "blacklist_reasons") and isinstance(self.blacklist_reasons, dict):
            self.blacklist_reasons.clear()

        # 重置测速记录，让节点纯净重新参与计分
        for n in list(self.node_speed_history.keys()):
            self.node_speed_history[n].clear()

        self._all_nodes_set = None
        self.save_persisted_config()
        self.refresh_tables()
        self.status_label.config(text=f"🎉 已成功一键清空所有黑名单，恢复全部节点至待测区！")
        self.log(f"🎉【一键清空黑名单】已清空 {tot_d} 条延迟黑名单与 {tot_s} 条低速黑名单，全量节点已恢复活跃待测！")
        messagebox.showinfo("清空成功", f"🎉 已成功清空全部黑名单！\n\n当前共有 {len(self.all_nodes)} 个节点已恢复待测，\n可立即点击【全量优选】或右键重新给节点测速、计分与晋升！")

    def clear_delay_blacklist(self):
        if not self.local_blacklist:
            messagebox.showinfo("提示", "延迟黑名单为空！")
            return
        if messagebox.askyesno("清空确认", f"确定清空全部 {len(self.local_blacklist)} 个延迟黑名单吗？"):
            if hasattr(self, "blacklist_reasons") and isinstance(self.blacklist_reasons, dict):
                for b in list(self.local_blacklist):
                    self.blacklist_reasons.pop(b, None)
            self.local_blacklist.clear()
            self._all_nodes_set = None
            self.save_persisted_config()
            self.refresh_tables()
            self.log("已清空延迟黑名单。")

    def clear_speed_blacklist(self):
        if not self.speed_blacklist:
            messagebox.showinfo("提示", "低速黑名单为空！")
            return
        if messagebox.askyesno("清空确认", f"确定清空全部 {len(self.speed_blacklist)} 个低速黑名单并重置测速记录吗？"):
            if hasattr(self, "blacklist_reasons") and isinstance(self.blacklist_reasons, dict):
                for s in list(self.speed_blacklist):
                    self.blacklist_reasons.pop(s, None)
            for n in self.speed_blacklist:
                if n in self.node_speed_history:
                    self.node_speed_history[n].clear()
            self.speed_blacklist.clear()
            self._all_nodes_set = None
            self.save_persisted_config()
            self.refresh_tables()
            self.log("已清空低速黑名单。")

    def clear_current_tab_blacklist(self):
        idx = self.notebook.index(self.notebook.select())
        if idx == 4:
            self.clear_delay_blacklist()
        elif idx == 5:
            self.clear_speed_blacklist()
        else:
            self.clear_all_blacklists()

    def trigger_rescore_and_promote(self):
        if self.is_pipeline_running:
            messagebox.showinfo("提示", "当前已有优选流水线正在运行，请等待完成后再试！")
            return

        if not messagebox.askyesno(
            "重新计分晋升确认",
            "是否立即对所有待测节点启动【全量重新计分与晋升流水线】？\n\n"
            "流水线将依次进行：\n"
            "1. 延迟多轮精测与抖动评分考核\n"
            "2. 高速带宽并发下行压测与计分\n"
            "3. 筛选达标最优节点晋升入【⭐ 优质精选池】\n"
            "4. 同步计分纳入【⏳ 沉淀孵化池】并评定【🏆 典藏常青池】晋升\n"
            "5. 一键热生效写入 Clash 内核\n\n"
            "点击【是】立即启动！"
        ):
            return

        self.start_full_auto_pipeline()

    def rescore_and_promote_selected(self, tree=None):
        if tree is None:
            tree = self.get_current_tree()
        selections = tree.selection()
        if not selections:
            messagebox.showinfo("提示", "请先在列表中选中需要测速计分并晋升的节点！")
            return

        sel_nodes = []
        for sel in selections:
            vals = tree.item(sel, "values")
            name = vals[-1] if vals else ""
            if name:
                sel_nodes.append(name)

        if not sel_nodes:
            return

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text=f"正在对选中的 {len(sel_nodes)} 个节点进行测速计分与晋升评定..."))
            promoted_cnt = 0
            for idx, name in enumerate(sel_nodes, 1):
                # 1. 移出黑名单
                self.local_blacklist.discard(name)
                self.speed_blacklist.discard(name)
                if hasattr(self, "blacklist_reasons"):
                    self.blacklist_reasons.pop(name, None)
                ep = self.get_node_endpoint(name)
                if ep:
                    self.local_blacklist.discard(ep)
                    self.speed_blacklist.discard(ep)
                    if hasattr(self, "blacklist_reasons"):
                        self.blacklist_reasons.pop(ep, None)
                    if ":" in ep:
                        ip = ep.split(":")[0]
                        self.local_blacklist.discard(ip)
                        self.speed_blacklist.discard(ip)
                        if hasattr(self, "blacklist_reasons"):
                            self.blacklist_reasons.pop(ip, None)

                # 2. 延迟多轮采样测速计分
                test_url = self.test_url_var.get().strip() or "http://www.gstatic.com/generate_204"
                enc_n = urllib.parse.quote(name, safe="")
                enc_u = urllib.parse.quote(test_url, safe="")
                delays = []
                for _ in range(3):
                    res = self._call_api(f"/proxies/{enc_n}/delay?timeout=2500&url={enc_u}", timeout=3.0)
                    if res and "delay" in res:
                        delays.append(res["delay"])
                    time.sleep(0.1)

                if not delays:
                    self.log(f"⚠️ 节点 {name} 延迟测试失败，无法计分")
                    continue

                avg_d = round(sum(delays) / len(delays))
                self.node_delays[name] = avg_d
                self.record_delay_sample(name, avg_d)
                if ep:
                    self.record_delay_sample(ep, avg_d)

                # 3. Colo 实时机房探测
                if ep and ":" in ep:
                    ip, port = ep.split(":", 1)
                    c_code, c_disp = get_cf_colo_raw(ip, port, timeout=1.5)
                    self.record_colo_sample(name, ep, c_code, c_disp)

                # 4. 下行带宽测速
                speed_url = self.speed_url_var.get().strip()
                spd = -1.0
                if speed_url and speed_url.startswith("http"):
                    try:
                        proxies_data = self._call_api("/proxies") or {}
                        proxies_map = proxies_data.get("proxies", {})
                        tg = "🚀 节点选择" if "🚀 节点选择" in proxies_map else "GLOBAL"
                        enc_tg = urllib.parse.quote(tg, safe="")
                        orig_choice = proxies_map.get(tg, {}).get("now", "")
                        self._call_api(f"/proxies/{enc_tg}", method="PUT", data=json.dumps({"name": name}).encode("utf-8"))
                        time.sleep(0.1)

                        mixed_port = self.get_clash_mixed_port()
                        proxy_handler = urllib.request.ProxyHandler({
                            "http": f"http://127.0.0.1:{mixed_port}",
                            "https": f"http://127.0.0.1:{mixed_port}",
                        })
                        opener = urllib.request.build_opener(proxy_handler)
                        req = urllib.request.Request(speed_url, headers={"User-Agent": "Mozilla/5.0"})
                        t_start = time.time()
                        total_b = 0
                        with opener.open(req, timeout=3.0) as resp:
                            while time.time() - t_start < 2.0:
                                chunk = resp.read(65536)
                                if not chunk:
                                    break
                                total_b += len(chunk)
                        dur = max(0.1, time.time() - t_start)
                        spd = round((total_b / dur) / (1024 * 1024), 2)

                        if orig_choice:
                            self._call_api(f"/proxies/{enc_tg}", method="PUT", data=json.dumps({"name": orig_choice}).encode("utf-8"))
                    except Exception:
                        spd = 0.0

                if spd >= 0:
                    self.node_speeds[name] = spd
                    self.node_speed_history.setdefault(name, []).append(spd)
                    self.node_speed_history[name] = self.node_speed_history[name][-4:]

                # 5. 晋升考核判定
                try:
                    max_d = int(self.max_delay_var.get().strip())
                except Exception:
                    max_d = 400
                try:
                    min_s = float(self.min_speed_var.get().strip())
                except Exception:
                    min_s = 2.0

                is_pass = (avg_d <= max_d) and (spd >= min_s if spd >= 0 else True) and self.is_asian_node(name)
                if is_pass:
                    self.favorites.add(name)
                    self.record_fav_reason(name, f"计分晋升 ({avg_d}ms / {spd:.2f}MB/s)")
                    promoted_cnt += 1
                    self.log(f"🎉【计分晋升】节点 {name} 计分通过（延迟 {avg_d}ms，下行 {spd} MB/s），已晋升至优质精选！")

            self._all_nodes_set = None
            self.deduplicate_favorites_by_endpoint()
            self.process_verified_lifecycle(list(self.favorites), [])
            self.save_persisted_config()
            self.root.after(0, self.refresh_tables)
            self.root.after(0, self.refresh_verified_table)
            self.root.after(0, self.refresh_stars_table)
            self.root.after(0, lambda: self.status_label.config(text=f"测速计分完成：成功晋升 {promoted_cnt}/{len(sel_nodes)} 个节点！"))

        threading.Thread(target=_worker, daemon=True).start()



    def setup_cloud_text_ui(self):
        toolbar = tk.Frame(self.tab_cloud_text, bg=THEME["bg_card"], padx=10, pady=8)
        toolbar.pack(fill=tk.X, padx=4, pady=(4, 4))

        tk.Label(toolbar, text="选择查看的云端文本:", fg="#38bdf8", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        self.cloud_file_var = tk.StringVar(value="/auto.txt (自动优选池)")
        self.cloud_combo = ttk.Combobox(
            toolbar,
            textvariable=self.cloud_file_var,
            values=["/auto.txt (自动优选池)", "/verified.txt (沉淀孵化池)", "/ (根目录典藏池)"],
            state="readonly",
            width=28
        )
        self.cloud_combo.pack(side=tk.LEFT, padx=6)
        self.cloud_combo.bind("<<ComboboxSelected>>", lambda e: self.load_cloud_text())

        create_modern_btn(
            toolbar,
            text="🔄 实时读取刷新",
            command=self.load_cloud_text,
            bg=THEME["accent_cyan"],
            hover_bg=THEME["accent_cyan_hover"] if "accent_cyan_hover" in THEME else THEME["accent_cyan"],
            font_size=9,
        ).pack(side=tk.LEFT, padx=6)

        create_modern_btn(
            toolbar,
            text="📥 导入至【优质精选】",
            command=self.import_cloud_text_to_favorites,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"] if "accent_green_hover" in THEME else THEME["accent_green"],
            font_size=9,
        ).pack(side=tk.RIGHT, padx=4)

        create_modern_btn(
            toolbar,
            text="📋 复制全文",
            command=self.copy_cloud_text,
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            font_size=9,
        ).pack(side=tk.RIGHT, padx=4)

        text_frame = tk.Frame(self.tab_cloud_text, bg=THEME["tree_bg"], padx=4, pady=4)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.cloud_text_box = tk.Text(
            text_frame,
            bg=THEME["bg_input"],
            fg=THEME["text_main"],
            insertbackground="#38bdf8",
            relief="flat",
            bd=0,
            font=("Consolas", 10),
            wrap="word"
        )
        sb_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.cloud_text_box.yview, style="Vertical.TScrollbar")
        self.cloud_text_box.configure(yscrollcommand=sb_y.set)
        self.cloud_text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 默认加载一次
        self.root.after(600, self.load_cloud_text)

    def load_cloud_text(self):
        base_url = self.cf_worker_url_var.get().strip().rstrip("/")
        if not base_url.startswith("http"):
            self.cloud_text_box.config(state="normal")
            self.cloud_text_box.delete("1.0", tk.END)
            self.cloud_text_box.insert(tk.END, "错误：请先在上方配置有效的 Cloudflare Worker 根地址！")
            self.cloud_text_box.config(state="disabled")
            return

        selection = self.cloud_file_var.get()
        if "auto.txt" in selection:
            subpath = "/auto.txt"
        elif "verified.txt" in selection:
            subpath = "/verified.txt"
        else:
            subpath = "/"

        target_url = f"{base_url}{subpath}" if subpath != "/" else f"{base_url}/"

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text=f"正在实时读取云端 {subpath} ..."))
            self.log(f"正在从云端读取文本: {target_url}")
            
            mixed_port = self.get_clash_mixed_port()
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            proxy_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
            direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))

            content_str = ""
            success = False
            last_err = ""

            for opener in [proxy_opener, direct_opener]:
                try:
                    req = urllib.request.Request(target_url, headers={"User-Agent": "ClashVergeNodeAssistant/1.0"})
                    with opener.open(req, timeout=10) as resp:
                        content_str = resp.read().decode("utf-8", errors="ignore")
                        success = True
                        break
                except Exception as ex:
                    last_err = str(ex)

            def _update_ui():
                self.cloud_text_box.config(state="normal")
                self.cloud_text_box.delete("1.0", tk.END)
                if success:
                    self.cloud_text_box.insert(tk.END, content_str)
                    self.status_label.config(text=f"成功读取云端 {subpath} ({len(content_str)} 字节)")
                    self.log(f"成功读取云端 {subpath}")
                else:
                    self.cloud_text_box.insert(tk.END, f"❌ 读取失败 ({target_url})\n错误原因: {last_err}\n\n请检查 Worker 地址是否正确、网络是否畅通或是否已成功推送过该文本。")
                    self.status_label.config(text=f"读取云端 {subpath} 失败")
                self.cloud_text_box.config(state="disabled")

            self.root.after(0, _update_ui)

        threading.Thread(target=_worker, daemon=True).start()

    def copy_cloud_text(self):
        txt = self.cloud_text_box.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showinfo("提示", "当前文本框为空！")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(txt)
        messagebox.showinfo("复制成功", "🎉 已将当前云端文本内容复制到剪贴板！")


