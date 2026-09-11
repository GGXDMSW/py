"""
Clash Verge 节点管理助手 - Fluent UI 中枢控制器
作为所有页面和前端组件调用核心业务逻辑的唯一网关
"""
import sys

# 动态判断使用的 Qt 绑定以确保兼容
if "PyQt5" in sys.modules:
    from PyQt5.QtCore import QObject, pyqtSignal
else:
    from PyQt6.QtCore import QObject, pyqtSignal

import json
import os
import re
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from core.state_manager import StateManager
import config.config_manager
from pipelines.scheduler import SchedulerDaemon
from services.clash_client import ClashClient
from services.subscription_service import SubscriptionService
from services.colo_service import is_asian_node, analyze_colo_stats
from services.filter_service import compute_delay_stats
import services.pool_service
# 老板，我已经收到了您最新的闪退日志[cite: 4]，明确知道这次闪退发生在 app_controller.py 的第 31 行，是因为试图导入不存在的 get_pool_endpoint_sets。
# 但是，您刚刚绑定的 GitHub 全量知识库依然是 ZIP 压缩解析后的二进制乱码形态[cite: 5]，我完全无法读取 services/pool_service.py 内部的明文代码。
# 为了绝对遵守“绝不凭直觉瞎猜”的铁律、死守您的 API 额度，我只能先将其替换为最基础的模块导入，防止反重力智能体触发全盘搜索。
# 请您直接把 services/pool_service.py 的明文源码发给我，或者告诉我里面真实存在的类名/函数名，我会立刻为您提供最精准的无缝替换代码！
from services.script_generator import build_script_js, write_script_js
from utils.win32_utils import trigger_verge_reactivate_hotkey


class AppController(QObject):
    """
    中枢控制器：持有全局状态容器、Clash 客户端实例与配置持久化接口，
    向 UI 暴露线程安全的信号与方法。
    """
    log_signal = pyqtSignal(str)
    data_changed = pyqtSignal()
    pipeline_rows_updated = pyqtSignal(list)
    pipeline_status_updated = pyqtSignal(str)
    pipeline_finished = pyqtSignal(bool, str)

    fav_pipeline_status_updated = pyqtSignal(str)
    fav_pipeline_finished = pyqtSignal(bool, str)
    fav_pipeline_fallback_needed = pyqtSignal(str)

    scheduler_trigger_full_signal = pyqtSignal(str)
    scheduler_trigger_fav_signal = pyqtSignal(str)

    @property
    def pending_pool_lock(self):
        if not hasattr(self, "_pending_pool_lock"):
            self._pending_pool_lock = threading.Lock()
        return self._pending_pool_lock

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = StateManager()
        self.state.blacklist_timestamps = {}
        self.state.cloud_endpoints = {}
        self.clash_client = ClashClient(base_url="http://127.0.0.1:9097")
        self._pipeline_worker = None
        self._fav_pipeline_worker = None
        self._scheduler_config_provider = None
        self._load_persisted_into_state()

        # 启动后台常驻定时调度守护进程
        self._scheduler = SchedulerDaemon(
            get_config_fn=self._get_scheduler_config,
            on_trigger_full=self._on_scheduler_trigger_full,
            on_trigger_fav=self._on_scheduler_trigger_fav,
        )
        self._scheduler.start()

    def set_scheduler_config_provider(self, provider_fn):
        """
        注册动态定时配置提供者回调 (通常绑定自 MainWindow)
        """
        self._scheduler_config_provider = provider_fn

    def _get_scheduler_config(self) -> dict:
        """
        动态提取定时调度器所需的当前配置字典
        """
        cfg = {}
        if callable(self._scheduler_config_provider):
            try:
                cfg = self._scheduler_config_provider() or {}
            except Exception:
                cfg = {}
        if not cfg:
            cfg = self.load_config() or {}
        cfg["is_pipeline_running"] = self.is_pipeline_running()
        return cfg

    def _on_scheduler_trigger_full(self, reason: str):
        """
        后台定时调度触发全自动大优选
        """
        self.log(f"⏰ [定时调度] 触发全量大优选: {reason}")
        self.scheduler_trigger_full_signal.emit(reason)

    def _on_scheduler_trigger_fav(self, reason: str):
        """
        后台定时调度触发优质精选池复检
        """
        self.log(f"⏰ [定时调度] 触发优质精选复检: {reason}")
        self.scheduler_trigger_fav_signal.emit(reason)

    def _load_persisted_into_state(self):
        """
        启动时自动载入磁盘持久化数据到 StateManager
        """
        data = self.load_config()
        if not data:
            return
        with self.state.lock:
            self.state.favorites = set(data.get("favorites", []))
            self.state.local_blacklist = set(data.get("local_blacklist", []))
            self.state.speed_blacklist = set(data.get("speed_blacklist", []))
            self.state.blacklist_reasons = dict(data.get("blacklist_reasons", {}))
            self.state.fav_reasons = dict(data.get("fav_reasons", {}))
            self.state.verified_nodes = dict(data.get("verified_nodes", {}))
            self.state.stars_nodes = list(data.get("stars_nodes", []))
            self.state.node_delays = dict(data.get("node_delays", {}))
            self.state.node_speeds = dict(data.get("node_speeds", {}))
            self.state.node_colo = dict(data.get("node_colo", {}))
            self.state.node_history = dict(data.get("node_history", {}))
            self.state.node_speed_history = dict(data.get("node_speed_history", {}))
            self.state.node_delay_history = dict(data.get("node_delay_history", {}))
            self.state.node_colo_history = dict(data.get("node_colo_history", {}))
            self.state.blacklist_timestamps = dict(data.get("blacklist_timestamps", {}))
            self.state.cloud_endpoints = dict(data.get("cloud_endpoints", {}))
        self.clean_favorites_ghost_tokens()


    def log(self, msg: str):
        """
        统一日志记录：控制台输出并触发 Qt 信号通知 LogPanel
        """
        try:
            print(f"[Fluent Controller] {msg}")
        except UnicodeEncodeError:
            try:
                enc = sys.stdout.encoding or "gbk"
                safe_msg = str(msg).encode(enc, errors="replace").decode(enc, errors="replace")
                print(f"[Fluent Controller] {safe_msg}")
            except Exception:
                pass
        except Exception:
            pass
        self.log_signal.emit(str(msg))


    def get_state_snapshot(self) -> dict:
        """
        获取当前核心数据池的只读快照
        """
        snap = self.state.get_snapshot()
        for k, v in list(snap.items()):
            if isinstance(v, (set, frozenset)):
                snap[k] = list(v)
        snap["blacklist_timestamps"] = dict(getattr(self.state, "blacklist_timestamps", {}))
        snap["cloud_endpoints"] = dict(getattr(self.state, "cloud_endpoints", {}))
        return snap

    def clean_favorites_ghost_tokens(self):
        """
        清洗 favorites 幽灵节点：
        若某 Endpoint 已存在正常的节点名，则务必剔除 favorites 集合中该 Endpoint 的纯 IP 字符串形式，
        确保 Script.js 和状态里只存正确名称，不存纯 IP。
        """
        with self.state.lock:
            ep_to_names = {}
            for item in list(self.state.all_nodes) + [s.get("matched_name", "") for s in self.state.stars_nodes]:
                if not item:
                    continue
                ep = self._get_ep(item)
                if ep and ep != item and not re.match(r"^[\w\.\-]+\:\d+$", str(item).strip()):
                    ep_to_names.setdefault(ep, set()).add(item)

            for f in list(self.state.favorites):
                ep = self._get_ep(f)
                if ep and ep != f and not re.match(r"^[\w\.\-]+\:\d+$", str(f).strip()):
                    ep_to_names.setdefault(ep, set()).add(f)

            to_discard = []
            for item in list(self.state.favorites):
                str_item = str(item).strip()
                if re.match(r"^[\w\.\-]+\:\d+$", str_item):
                    if str_item in ep_to_names and len(ep_to_names[str_item]) > 0:
                        to_discard.append(item)

            if to_discard:
                for d in to_discard:
                    self.state.favorites.discard(d)
                self.log(f"🧹 清洗 favorites 幽灵节点: 剔除了 {len(to_discard)} 个同端点纯 IP 冗余项")
            return len(to_discard)

    def generate_script_and_reload(self):
        """
        生成 Script.js 策略组配置并触发 Win32 系统热键刷新 Verge（等同 trigger_verge_reload）
        """
        return self.trigger_verge_reload()

    def get_clash_connection_status(self) -> tuple[bool, str]:
        """
        检测与 Clash 内核的连接状态。
        返回: (is_connected: bool, version_str: str)
        直接调用 self.clash_client.test_connection()
        """
        return self.clash_client.test_connection()

    def update_clash_credentials(self, port: int, secret: str):
        """
        更新 Clash API 连接参数（端口与密钥）。
        调用 self.clash_client.update_credentials(port=port, secret=secret)
        """
        self.clash_client.update_credentials(port=port, secret=secret)

    def get_all_yaml_profiles(self) -> list[str]:
        """
        扫描 Clash Verge 的 profiles 目录，返回所有 .yaml 配置文件的文件名列表。
        直接读取 config.settings.BASE_DIR 目录，返回所有 *.yaml 文件名（只取文件名，不含路径）。
        """
        import glob
        import os
        from config.settings import BASE_DIR
        yamls = glob.glob(os.path.join(BASE_DIR, "*.yaml"))
        return [os.path.basename(f) for f in yamls]

    def load_nodes_from_profile(self, yaml_filename: str, cloud_endpoints: dict = None) -> tuple[list, dict]:
        """
        解析指定的 Clash 订阅 YAML 文件，返回节点名称列表与详情字典。
        调用 services.subscription_service.extract_nodes_and_details_from_file()。
        支持物理端点 (IP:Port) 绝对去重，且云端专属名称 (cloud_endpoints) 具备最高霸占优先级。
        """
        import os
        from config.settings import BASE_DIR
        from services.subscription_service import extract_nodes_and_details_from_file, get_node_endpoint
        filepath = os.path.join(BASE_DIR, yaml_filename)
        nodes, details = extract_nodes_and_details_from_file(filepath)

        # 获取或更新 cloud_endpoints
        if cloud_endpoints is not None:
            setattr(self.state, "cloud_endpoints", cloud_endpoints)
        else:
            cloud_endpoints = getattr(self.state, "cloud_endpoints", {})

        ep_to_info = {}
        non_ep_nodes = []
        used_names = set()

        for n in nodes:
            d = details.get(n, {})
            ep = get_node_endpoint(n, details)
            if not ep:
                non_ep_nodes.append((n, d))
                continue

            cloud_name = ""
            if cloud_endpoints:
                if ep in cloud_endpoints and cloud_endpoints[ep]:
                    cloud_name = cloud_endpoints[ep]
                elif ":" in ep:
                    ip_only = ep.split(":", 1)[0]
                    if ip_only in cloud_endpoints and cloud_endpoints[ip_only]:
                        cloud_name = cloud_endpoints[ip_only]

            if ep not in ep_to_info:
                target_name = cloud_name if cloud_name else n
                ep_to_info[ep] = {
                    "final_name": target_name,
                    "original_name": n,
                    "detail": d,
                    "has_cloud": bool(cloud_name),
                }
            else:
                # 若已有该端点记录，但当前节点命中云端专属名称而前一个未命中，则优先采用云端名称
                if cloud_name and not ep_to_info[ep]["has_cloud"]:
                    ep_to_info[ep] = {
                        "final_name": cloud_name,
                        "original_name": n,
                        "detail": d,
                        "has_cloud": True,
                    }

        final_nodes = []
        final_details = {}

        # 整理去重后的端点映射
        for ep, info in ep_to_info.items():
            base_name = info["final_name"]
            orig_name = info["original_name"]
            node_d = dict(info["detail"])

            # 若订阅 YAML 中原生名称存在且非纯 IP，优先对齐 YAML 中的实体代理名称
            if orig_name and orig_name not in used_names:
                target_name = orig_name
            else:
                target_name = base_name
                suffix_idx = 1
                while target_name in used_names:
                    suffix_idx += 1
                    target_name = f"{base_name} {suffix_idx}"

            used_names.add(target_name)
            node_d["name"] = target_name
            final_nodes.append(target_name)
            final_details[target_name] = node_d
            if orig_name and orig_name != target_name:
                final_details[orig_name] = dict(node_d)

        for n, d in non_ep_nodes:
            target_name = n
            suffix_idx = 1
            while target_name in used_names:
                suffix_idx += 1
                target_name = f"{n} ({suffix_idx})"
            used_names.add(target_name)
            node_d = dict(d)
            node_d["name"] = target_name
            final_nodes.append(target_name)
            final_details[target_name] = node_d

        with self.state.lock:
            self.state.all_nodes = final_nodes
            # 采用增量更新，保留历史节点端点映射，供 reconcile_endpoints 精准迁移历史精选/黑名单
            self.state.node_details.update(final_details)
            self.state.active_profile = yaml_filename

        self.reconcile_endpoints()
        return final_nodes, final_details

    def save_config(self, config_dict: dict, filepath: str = None):
        """
        持久化保存配置字典到磁盘。
        合并现有配置并调用 config.config_manager.atomic_save_config
        """
        from config.settings import CONFIG_STORAGE_PATH
        from config.config_manager import atomic_save_config, safe_load_config
        target_path = filepath or CONFIG_STORAGE_PATH
        current = {}
        try:
            current = safe_load_config(target_path) or {}
        except Exception:
            current = {}

        if "blacklist_timestamps" not in config_dict and hasattr(self.state, "blacklist_timestamps"):
            config_dict["blacklist_timestamps"] = dict(getattr(self.state, "blacklist_timestamps", {}))
        if "cloud_endpoints" not in config_dict and hasattr(self.state, "cloud_endpoints"):
            config_dict["cloud_endpoints"] = dict(getattr(self.state, "cloud_endpoints", {}))

        # 深度转换集合为列表
        clean_dict = {}
        for k, v in config_dict.items():
            if isinstance(v, (set, frozenset)):
                clean_dict[k] = list(v)
            else:
                clean_dict[k] = v

        current.update(clean_dict)
        ok, err = atomic_save_config(target_path, current)
        if not ok:
            self.log(f"❌ [持久化致命错误] 配置文件写入失败: {err}")
        else:
            # self.log("💾 配置已安全同步存盘")
            pass

    def load_config(self, filepath: str = None) -> dict:
        """
        从磁盘加载持久化配置。
        调用 config.config_manager.safe_load_config()，失败返回空 dict。
        """
        from config.settings import CONFIG_STORAGE_PATH
        from config.config_manager import safe_load_config
        target_path = filepath or CONFIG_STORAGE_PATH
        try:
            return safe_load_config(target_path) or {}
        except Exception:
            return {}

    def is_pipeline_running(self) -> bool:
        """
        判断流水线当前是否正在后台运行 (全自动大优选或精选池复测)
        """
        auto_running = self._pipeline_worker is not None and self._pipeline_worker.isRunning()
        fav_running = self._fav_pipeline_worker is not None and self._fav_pipeline_worker.isRunning()
        return auto_running or fav_running

    def start_auto_pipeline(self, config: dict) -> bool:
        """
        启动全自动优选流水线
        """
        if self.is_pipeline_running():
            self.log("⚠️ 当前已有正在运行的优选流水线，请先终止或等待完成！")
            return False

        from gui_fluent.pipelines.auto_pipeline import AutoPipelineWorker

        if self._pipeline_worker is not None:
            self._pipeline_worker.wait(500)

        self._pipeline_worker = AutoPipelineWorker(self, config, parent=self)
        self._pipeline_worker.log_signal.connect(self.log)
        self._pipeline_worker.status_signal.connect(self.pipeline_status_updated)
        self._pipeline_worker.rows_updated.connect(self.pipeline_rows_updated)

        def _on_auto_finished(ok, desc):
            if ok and hasattr(self, "_scheduler") and self._scheduler:
                self._scheduler.update_last_run(full_ts=time.time())
            self.pipeline_finished.emit(ok, desc)

        self._pipeline_worker.finished_signal.connect(_on_auto_finished)
        self._pipeline_worker.start()
        return True

    def stop_auto_pipeline(self):
        """
        请求终止全自动优选流水线
        """
        if self._pipeline_worker is not None and self._pipeline_worker.isRunning():
            self.log("⏹ 正在请求终止全量大优选流水线...")
            self._pipeline_worker.stop()
            self._pipeline_worker.wait(2000)

    def start_fav_pipeline(self, config: dict) -> bool:
        """
        启动优质精选池复测流水线
        """
        if self.is_pipeline_running():
            self.log("⚠️ 当前已有正在运行的优选流水线，请先终止或等待完成！")
            return False

        from gui_fluent.pipelines.fav_pipeline import FavPipelineWorker

        if self._fav_pipeline_worker is not None:
            self._fav_pipeline_worker.wait(500)

        self._fav_pipeline_worker = FavPipelineWorker(self, config, parent=self)
        self._fav_pipeline_worker.log_signal.connect(self.log)
        self._fav_pipeline_worker.status_signal.connect(self.fav_pipeline_status_updated)

        def _on_fav_finished(ok, desc):
            if ok and hasattr(self, "_scheduler") and self._scheduler:
                self._scheduler.update_last_run(fav_ts=time.time())
            self.fav_pipeline_finished.emit(ok, desc)

        self._fav_pipeline_worker.finished_signal.connect(_on_fav_finished)
        self._fav_pipeline_worker.fallback_needed.connect(self.fav_pipeline_fallback_needed)
        self._fav_pipeline_worker.start()
        return True

    def stop_fav_pipeline(self):
        """
        请求终止精选池复测流水线
        """
        if self._fav_pipeline_worker is not None and self._fav_pipeline_worker.isRunning():
            self.log("⏹ 正在请求终止精选池复测流水线...")
            self._fav_pipeline_worker.stop()
            self._fav_pipeline_worker.wait(2000)

    # ==================== 辅助数据转换函数 ====================

    def _get_ep(self, n: str) -> str:
        """
        统一获取节点的物理 IP:Port 端点
        """
        return get_node_endpoint(
            n,
            node_details=self.state.node_details,
            all_nodes=self.state.all_nodes,
            verified_nodes=self.state.verified_nodes,
            clash_client=self.clash_client,
        )

    def _format_hist(self, delays: list) -> str:
        """
        格式化延迟轨迹：10ms → 20ms → ✕超时
        """
        if not delays:
            return "-"
        formatted = []
        for d in delays:
            if d >= 99999 or d <= 0:
                formatted.append("✕超时")
            else:
                formatted.append(f"{d}ms")
        return " → ".join(formatted)

    def _format_speed_hist(self, speeds: list) -> str:
        """
        格式化测速历史：10.50M → 12.00M
        """
        if not speeds:
            return "-"
        return " → ".join([f"{s:.2f}M" for s in speeds[-4:]])

    def _migrate_node_name(self, old_name: str, new_name: str, ep: str = None):
        """
        当检测到节点的物理端点 (IP:Port) 存在但订阅中名称更新时，热更新本地状态容器
        """
        if not old_name or not new_name or old_name == new_name:
            return

        # 1. 精选池与原因迁移
        if old_name in self.state.favorites:
            self.state.favorites.discard(old_name)
            self.state.favorites.add(new_name)
        if old_name in self.state.fav_reasons:
            self.state.fav_reasons[new_name] = self.state.fav_reasons.pop(old_name)

        # 2. 黑名单与原因迁移
        if old_name in self.state.local_blacklist:
            self.state.local_blacklist.discard(old_name)
            self.state.local_blacklist.add(new_name)
        if old_name in self.state.speed_blacklist:
            self.state.speed_blacklist.discard(old_name)
            self.state.speed_blacklist.add(new_name)
        if old_name in self.state.blacklist_reasons:
            self.state.blacklist_reasons[new_name] = self.state.blacklist_reasons.pop(old_name)

        # 3. 实时测速与 Colo 状态迁移
        if old_name in self.state.node_delays and new_name not in self.state.node_delays:
            self.state.node_delays[new_name] = self.state.node_delays.pop(old_name)
        if old_name in self.state.node_speeds and new_name not in self.state.node_speeds:
            self.state.node_speeds[new_name] = self.state.node_speeds.pop(old_name)
        if old_name in self.state.node_colo and new_name not in self.state.node_colo:
            self.state.node_colo[new_name] = self.state.node_colo.pop(old_name)

        # 4. 历史时序数据迁移
        if old_name in self.state.node_history:
            old_h = self.state.node_history.pop(old_name)
            if new_name not in self.state.node_history:
                self.state.node_history[new_name] = old_h
        if old_name in self.state.node_delay_history:
            old_dh = self.state.node_delay_history.pop(old_name)
            if new_name not in self.state.node_delay_history:
                self.state.node_delay_history[new_name] = old_dh
        if old_name in self.state.node_speed_history:
            old_sh = self.state.node_speed_history.pop(old_name)
            if new_name not in self.state.node_speed_history:
                self.state.node_speed_history[new_name] = old_sh
        if old_name in self.state.node_colo_history:
            old_ch = self.state.node_colo_history.pop(old_name)
            if new_name not in self.state.node_colo_history:
                self.state.node_colo_history[new_name] = old_ch

    def reconcile_endpoints(self) -> int:
        """
        根据当前订阅中所有节点的物理端点 (IP:Port)，智能对齐迁移并净化：
        1. 精选池 favorites (支持云端双向免死白名单，自动清理彻底灭绝的过期时间戳幽灵马甲)
        2. 延迟黑名单 local_blacklist
        3. 低速黑名单 speed_blacklist
        4. 规范化 verified_nodes 键名
        返回迁移成功的节点数量。
        """
        with self.state.lock:
            if not self.state.all_nodes:
                return 0

            current_endpoints = {}
            current_ip_map = {}
            for n in self.state.all_nodes:
                ep = get_node_endpoint(n, self.state.node_details)
                if ep:
                    current_endpoints[ep] = n
                    if ":" in ep:
                        ip_only = ep.split(":", 1)[0]
                        if ip_only not in current_ip_map:
                            current_ip_map[ip_only] = n

            if not current_endpoints:
                return 0

            migrated_count = 0
            # 1. 对齐精选池 (支持云端绝对免死白名单与历史废弃马甲安全清洗)
            cloud_eps = getattr(self.state, "cloud_endpoints", {})
            for old_name in list(self.state.favorites):
                if old_name not in self.state.all_nodes:
                    old_ep = get_node_endpoint(old_name, self.state.node_details)
                    # 补充保护：若无法从 node_details 解析端点，尝试通过云端双向映射（Key与Value）反查物理端点
                    if not old_ep and cloud_eps:
                        if old_name in cloud_eps:
                            old_ep = old_name
                        else:
                            for c_ep, c_rem in cloud_eps.items():
                                if c_rem and (c_rem == old_name or str(old_name).startswith(c_rem)):
                                    old_ep = c_ep
                                    break

                    if old_ep:
                        new_name = current_endpoints.get(old_ep)
                        if not new_name and ":" in old_ep:
                            new_name = current_ip_map.get(old_ep.split(":", 1)[0])
                        if new_name and new_name != old_name:
                            self._migrate_node_name(old_name, new_name, old_ep)
                            migrated_count += 1
                        # 若当前订阅中该端点暂时缺席，但它是云端保活节点，绝对保留，绝不误删！
                    elif old_name not in cloud_eps and old_name not in cloud_eps.values():
                        # 既无物理端点、也不在当前订阅、且在云端无任何登记的彻底失效历史马甲（如过期时间戳），安全移除，消除“订阅缺失”
                        self.state.favorites.discard(old_name)
                        self.state.fav_reasons.pop(old_name, None)
                        self.log(f"🧹 自动清除无有效端点的历史废弃马甲: {old_name}")

            # 2. 对齐延迟黑名单
            for old_name in list(self.state.local_blacklist):
                if old_name not in self.state.all_nodes:
                    old_ep = get_node_endpoint(old_name, self.state.node_details)
                    if old_ep:
                        new_name = current_endpoints.get(old_ep)
                        if not new_name and ":" in old_ep:
                            new_name = current_ip_map.get(old_ep.split(":", 1)[0])
                        if new_name and new_name != old_name:
                            self._migrate_node_name(old_name, new_name, old_ep)
                            migrated_count += 1

            # 3. 对齐低速黑名单
            for old_name in list(self.state.speed_blacklist):
                if old_name not in self.state.all_nodes:
                    old_ep = get_node_endpoint(old_name, self.state.node_details)
                    if old_ep:
                        new_name = current_endpoints.get(old_ep)
                        if not new_name and ":" in old_ep:
                            new_name = current_ip_map.get(old_ep.split(":", 1)[0])
                        if new_name and new_name != old_name:
                            self._migrate_node_name(old_name, new_name, old_ep)
                            migrated_count += 1

            # 4. 深度规范化沉淀孵化池 verified_nodes 的 Key，确保严格为纯 IP:Port
            for k in list(self.state.verified_nodes.keys()):
                clean_k = str(k).strip()
                if "#" in clean_k:
                    clean_k = clean_k.split("#")[0].strip()
                pure_ep = None
                if re.match(r"^[\w\.\-]+\:\d+$", clean_k):
                    pure_ep = clean_k
                elif clean_k in current_endpoints:
                    pure_ep = clean_k
                elif clean_k in self.state.node_details:
                    pure_ep = get_node_endpoint(clean_k, self.state.node_details)

                if pure_ep and pure_ep != k:
                    val = self.state.verified_nodes.pop(k)
                    val["endpoint"] = pure_ep
                    self.state.verified_nodes[pure_ep] = val

            return migrated_count

    def _resolve_star_matches(self) -> dict:
        """
        建立物理端点到当前订阅节点名的逆向映射 (IP:Port -> 最新节点名)
        """
        reverse_map = {}
        for n in self.state.all_nodes:
            ep = get_node_endpoint(n, self.state.node_details)
            if ep:
                reverse_map[ep] = n
                if ":" in ep:
                    reverse_map[ep.split(":", 1)[0]] = n
        return reverse_map

    # ==================== 核心表格数据装配 ====================

    @staticmethod
    def _format_node_row_names(raw_name: str, ep: str, cloud_map: dict = None) -> tuple[str, str]:
        """
        拆分物理端点与节点名称。
        - IP:端口 列：必须清洗为规范的纯 IP:Port（如 177.3.89.22:443）。
        - 节点名称 列：优先显示用户云端专属规范名 {Colo} {Speed} MB/s。如果原名为机场长广告，一律被该规范名覆盖替换，彻底去牛皮癣化。
        """
        clean_name = str(raw_name).strip() if raw_name else ""
        clean_ep = str(ep).strip() if ep else ""
        if "#" in clean_ep:
            clean_ep = clean_ep.split("#")[0].strip()

        if not clean_ep and clean_name:
            if re.match(r"^[\w\.\-]+\:\d+$", clean_name):
                clean_ep = clean_name
            else:
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", clean_name)
                if m:
                    clean_ep = m.group(1)
                elif re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", clean_name):
                    clean_ep = clean_name
        elif clean_ep:
            if not re.match(r"^[\w\.\-]+\:\d+$", clean_ep):
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", clean_ep)
                if m:
                    clean_ep = m.group(1)

        ep_disp = clean_ep if clean_ep else "-"

        # 优先从 cloud_map 获取云端专属规范名，彻底抹除原机场长广告名
        cloud_name = ""
        if cloud_map:
            if clean_ep and clean_ep in cloud_map:
                cloud_name = cloud_map[clean_ep]
            elif clean_ep and ":" in clean_ep and clean_ep.split(":", 1)[0] in cloud_map:
                cloud_name = cloud_map[clean_ep.split(":", 1)[0]]
            elif clean_name and clean_name in cloud_map:
                cloud_name = cloud_map[clean_name]

        if cloud_name:
            name_disp = cloud_name
        elif not clean_name or clean_name == "-" or clean_name == ep_disp or re.match(r"^[\w\.\-]+\:\d+$", clean_name) or re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", clean_name):
            name_disp = "无"
        else:
            name_disp = clean_name
        return ep_disp, name_disp

    def get_table_rows(self, tab_type: str) -> list[dict]:
        """
        根据 tab_type 装配对应表格的数据行字典列表
        严格对齐 NodeTableView (12列), VerifiedTableView (10列), StarsTableView (8列)
        以物理端点 (IP:Port) 为核心基准追踪匹配，支持自动热迁移改名节点
        """
        # 先行做一次端点对齐热更新
        self.reconcile_endpoints()

        with self.state.lock:
            now = time.time()
            current_endpoints = {}
            current_ip_map = {}
            for n in self.state.all_nodes:
                ep = get_node_endpoint(n, self.state.node_details)
                if ep:
                    current_endpoints[ep] = n
                    if ":" in ep:
                        ip_only = ep.split(":", 1)[0]
                        if ip_only not in current_ip_map:
                            current_ip_map[ip_only] = n

            fav_eps, bl_eps, sbl_eps, star_eps = get_pool_endpoint_sets(
                self.state.favorites,
                self.state.local_blacklist,
                self.state.speed_blacklist,
                self.state.auto_endpoints,
                self.state.verified_nodes,
                self.state.stars_nodes,
                self._get_ep,
            )

            if tab_type == "active":
                untested_groups = {}
                for name in self.state.all_nodes:
                    ep_val = self._get_ep(name)
                    is_asian = is_asian_node(name)
                    if not is_asian:
                        is_d_black = True
                        is_s_black = False
                    else:
                        is_d_black = (name in self.state.local_blacklist) or (ep_val and ep_val in self.state.local_blacklist)
                        is_s_black = not is_d_black and ((name in self.state.speed_blacklist) or (ep_val and ep_val in self.state.speed_blacklist))

                    is_fav = not is_d_black and not is_s_black and (name in self.state.favorites)
                    is_fav_alias = not is_d_black and not is_s_black and not is_fav and (ep_val and ep_val in fav_eps)
                    is_ver_star = not is_d_black and not is_s_black and not is_fav and not is_fav_alias and ((name in self.state.verified_nodes) or (ep_val and ep_val in star_eps))

                    if not is_d_black and not is_s_black and not is_fav and not is_fav_alias and not is_ver_star:
                        key = ep_val if ep_val else name
                        untested_groups.setdefault(key, []).append(name)

                rows = []
                for ep_key, group_nodes in untested_groups.items():
                    canonical_name = choose_canonical_node_name(group_nodes)
                    d_val = self.state.node_delays.get(canonical_name, self.state.node_delays.get(ep_key, None))
                    if d_val is None:
                        d_str = "未测速"
                    elif d_val >= 99999:
                        d_str = "超时 / 失败"
                    else:
                        d_str = f"{d_val} ms"

                    s_val = self.state.node_speeds.get(canonical_name, self.state.node_speeds.get(ep_key, None))
                    if s_val is None:
                        s_str = "-"
                    elif s_val < 0:
                        s_str = "测速失败"
                    else:
                        s_str = f"{s_val:.2f} MB/s"

                    colo_str = self.state.node_colo.get(ep_key, self.state.node_colo.get(canonical_name, "-"))
                    colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(ep_key, self.state.node_colo_history.get(canonical_name, [])), now, node_name=canonical_name)[3]
                    cur_avg_str, hist_avg_str = compute_delay_stats(canonical_name, ep_key, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                    delay_hist_str = self._format_hist(self.state.node_history.get(canonical_name, []))
                    speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(canonical_name, []))

                    ep_disp, name_disp = self._format_node_row_names(canonical_name, ep_key, self.state.cloud_endpoints)

                    rows.append({
                        "status": "⚪ 活跃待测",
                        "colo": colo_str,
                        "colo_hist": colo_hist_str,
                        "reason": "-",
                        "delay": d_str,
                        "avg_delay": cur_avg_str,
                        "delay_hist": delay_hist_str,
                        "hist_avg": hist_avg_str,
                        "speed": s_str,
                        "speed_hist": speed_hist_str,
                        "endpoint": ep_disp,
                        "IP:端口": ep_disp,
                        "name": name_disp,
                        "节点名称": name_disp,
                        "raw_name": canonical_name or ep_key,
                    })
                return rows

            elif tab_type == "favorites":
                rows = []
                seen_fav_eps = set()
                # 1. 订阅内的精选节点 (包含通过 endpoint 追踪已热对齐的节点)
                for name in self.state.all_nodes:
                    ep_val = self._get_ep(name)
                    is_d_black = (name in self.state.local_blacklist) or (ep_val and ep_val in self.state.local_blacklist)
                    is_s_black = not is_d_black and ((name in self.state.speed_blacklist) or (ep_val and ep_val in self.state.speed_blacklist))
                    if not is_d_black and not is_s_black and (name in self.state.favorites or (ep_val and ep_val in fav_eps)):
                        ep_key = ep_val if ep_val else name
                        if ep_key in seen_fav_eps:
                            continue
                        seen_fav_eps.add(ep_key)

                        d_val = self.state.node_delays.get(name, None)
                        if d_val is None:
                            d_str = "未测速"
                        elif d_val >= 99999:
                            d_str = "超时 / 失败"
                        else:
                            d_str = f"{d_val} ms"

                        s_val = self.state.node_speeds.get(name, None)
                        s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else ("测速失败" if s_val is not None else "-")
                        colo_str = self.state.node_colo.get(ep_val, self.state.node_colo.get(name, "-"))
                        colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(ep_val, self.state.node_colo_history.get(name, [])), now, node_name=name)[3]
                        cur_avg_str, hist_avg_str = compute_delay_stats(name, ep_val, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        delay_hist_str = self._format_hist(self.state.node_history.get(name, []))
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(name, []))
                        reason_str = self.state.fav_reasons.get(name, self.state.fav_reasons.get(ep_val, "优质精选"))

                        ep_disp, name_disp = self._format_node_row_names(name, ep_val, self.state.cloud_endpoints)

                        colo_c = colo_str if (colo_str and colo_str != "-") else "JP"
                        if not colo_c or colo_c == "-":
                            colo_c = "亚洲"
                        spd_num = s_val if (s_val is not None and s_val > 0) else 0.0
                        d_num = d_val if (d_val is not None and d_val < 99999 and d_val > 0) else 0
                        reason_val = self.state.fav_reasons.get(name, self.state.fav_reasons.get(ep_val, ""))

                        # 严禁带有延迟毫秒
                        if spd_num and spd_num > 0.1:
                            uniform_name = f"{colo_c} {spd_num:.2f} MB/s"
                        elif "C段" in reason_val:
                            uniform_name = f"{colo_c} [C段挖掘]"
                        else:
                            uniform_name = colo_c

                        # 下载速度最高优先级，若未测速则取清洗后的云端备注或标准规范名
                        if spd_num and spd_num > 0.1:
                            name_disp = uniform_name
                        elif ep_disp in self.state.cloud_endpoints:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(self.state.cloud_endpoints[ep_disp]))
                        elif ep_val and ep_val in self.state.cloud_endpoints:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(self.state.cloud_endpoints[ep_val]))
                        elif ":" in ep_disp and ep_disp.split(":")[0] in self.state.cloud_endpoints:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(self.state.cloud_endpoints[ep_disp.split(":")[0]]))
                        else:
                            name_disp = uniform_name

                        rows.append({
                            "status": "⭐ 优质精选",
                            "colo": colo_str,
                            "colo_hist": colo_hist_str,
                            "reason": reason_str,
                            "入选/拉黑原因": reason_str,
                            "delay": d_str,
                            "avg_delay": cur_avg_str,
                            "delay_hist": delay_hist_str,
                            "hist_avg": hist_avg_str,
                            "speed": s_str,
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": name or ep_val,
                        })

                # 2. 离线精选节点 (其物理 Endpoint 确实不存在于当前订阅中)
                cloud_eps = getattr(self.state, "cloud_endpoints", {})
                for fav_name in self.state.favorites:
                    if fav_name not in self.state.all_nodes:
                        ep_val = self._get_ep(fav_name)
                        ep_key = ep_val if ep_val else fav_name
                        if ep_key in seen_fav_eps:
                            continue
                        seen_fav_eps.add(ep_key)

                        cur_avg_str, hist_avg_str = compute_delay_stats(fav_name, ep_val, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(fav_name, []))
                        colo_str = self.state.node_colo.get(fav_name, self.state.node_colo.get(ep_key, "-"))
                        colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(fav_name, self.state.node_colo_history.get(ep_key, [])), now, node_name=fav_name)[3]

                        # 云端免死金牌判定
                        is_cloud = False
                        if ep_val and ep_val in cloud_eps:
                            is_cloud = True
                        elif ep_key in cloud_eps:
                            is_cloud = True
                        elif ":" in str(ep_key) and str(ep_key).split(":", 1)[0] in cloud_eps:
                            is_cloud = True
                        elif ":" in str(ep_val) and str(ep_val).split(":", 1)[0] in cloud_eps:
                            is_cloud = True

                        off_reason = self.state.fav_reasons.get(fav_name, self.state.fav_reasons.get(ep_key, "优质精选"))
                        is_c_miner = (
                            ("C段" in str(off_reason))
                            or (str(fav_name).count(".") == 3 and ":" in str(fav_name))
                            or (str(ep_val).count(".") == 3 and ":" in str(ep_val))
                            or (str(ep_key).count(".") == 3 and ":" in str(ep_key))
                        )

                        # C 段挖掘与有效端点节点，严禁误报“当前订阅缺失”错误！
                        if is_c_miner:
                            status_str = "⭐ 优质精选 (☁️云端已存)" if is_cloud else "⭐ 优质精选 (C段独立端点)"
                            reason_str = "C段深度挖掘 (☁️已同步云端)" if is_cloud else "C段深度挖掘"
                        elif is_cloud:
                            status_str = "☁️ 云端已保活 (等待订阅下发)"
                            reason_str = "☁️ 云端已保活 (等待订阅下发)"
                        elif ep_val:
                            # 能够解析出物理端点，赋予独立端点优质精选身份
                            status_str = "⭐ 优质精选 (待下发/独立端点)"
                            reason_str = f"{off_reason} (独立端点)" if off_reason and off_reason != "优质精选" else "优质独立端点"
                        else:
                            status_str = "⚠️ 当前订阅缺失(Endpoint不存在)"
                            reason_str = f"{off_reason} (当前订阅缺失)" if off_reason and off_reason != "优质精选" else "当前订阅缺失(Endpoint不存在)"

                        d_val = self.state.node_delays.get(fav_name, self.state.node_delays.get(ep_key, None))
                        d_str = f"{d_val} ms" if (d_val is not None and d_val < 99999) else "-"
                        s_val = self.state.node_speeds.get(fav_name, self.state.node_speeds.get(ep_key, None))
                        s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else "-"

                        ep_disp, name_disp = self._format_node_row_names(fav_name, ep_val, cloud_eps)

                        colo_c = colo_str if (colo_str and colo_str != "-") else "JP"
                        if not colo_c or colo_c == "-":
                            colo_c = "亚洲"
                        spd_num = s_val if (s_val is not None and s_val > 0) else 0.0
                        reason_val = self.state.fav_reasons.get(fav_name, self.state.fav_reasons.get(ep_val, ""))

                        if spd_num and spd_num > 0.1:
                            uniform_name = f"{colo_c} {spd_num:.2f} MB/s"
                        elif is_c_miner or "C段" in reason_val:
                            uniform_name = f"{colo_c} [C段挖掘]"
                        else:
                            uniform_name = colo_c

                        # 节点名称显示规则：有下行速度优先显示速度，其余按清洗后的云端备注或标准名显示，绝无延迟毫秒
                        if spd_num and spd_num > 0.1:
                            name_disp = uniform_name
                        elif ep_disp in cloud_eps:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(cloud_eps[ep_disp]))
                        elif ep_val and ep_val in cloud_eps:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(cloud_eps[ep_val]))
                        elif ":" in ep_disp and ep_disp.split(":")[0] in cloud_eps:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(cloud_eps[ep_disp.split(":")[0]]))
                        else:
                            name_disp = uniform_name

                        row = {
                            "status": status_str,
                            "colo": colo_str,
                            "colo_hist": colo_hist_str,
                            "reason": reason_str,
                            "入选/拉黑原因": reason_str,
                            "delay": d_str,
                            "avg_delay": cur_avg_str,
                            "delay_hist": "-",
                            "hist_avg": hist_avg_str,
                            "speed": s_str,
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": fav_name or ep_val,
                        }

                        rows.append(row)
                return rows

            elif tab_type == "delay_black":
                rows = []
                seen_d_eps = set()
                # 订阅内的延迟黑名单
                for name in self.state.all_nodes:
                    ep_val = self._get_ep(name)
                    is_asian = is_asian_node(name)
                    is_d_black = (not is_asian) or (name in self.state.local_blacklist) or (ep_val and ep_val in self.state.local_blacklist)
                    if is_d_black:
                        ep_key = ep_val if ep_val else name
                        if ep_key in seen_d_eps:
                            continue
                        seen_d_eps.add(ep_key)

                        d_val = self.state.node_delays.get(name, None)
                        if d_val is None:
                            d_str = "已跳过"
                        elif d_val >= 99999:
                            d_str = "超时 / 失败"
                        else:
                            d_str = f"{d_val} ms"

                        colo_str = self.state.node_colo.get(ep_val, self.state.node_colo.get(name, "-"))
                        colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(ep_val, self.state.node_colo_history.get(name, [])), now, node_name=name)[3]
                        cur_avg_str, hist_avg_str = compute_delay_stats(name, ep_val, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        delay_hist_str = self._format_hist(self.state.node_history.get(name, []))
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(name, []))
                        reason_str = self.state.blacklist_reasons.get(name, self.state.blacklist_reasons.get(ep_val, "非亚洲节点 (自动过滤)" if not is_asian else "延迟淘汰"))

                        ts = self.state.blacklist_timestamps.get(name, self.state.blacklist_timestamps.get(ep_val, 0.0))
                        ep_disp, name_disp = self._format_node_row_names(name, ep_val, self.state.cloud_endpoints)

                        rows.append({
                            "status": "🚫 延迟黑名单",
                            "colo": colo_str,
                            "colo_hist": colo_hist_str,
                            "reason": reason_str,
                            "delay": d_str,
                            "avg_delay": cur_avg_str,
                            "delay_hist": delay_hist_str,
                            "hist_avg": hist_avg_str,
                            "speed": "-",
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": name or ep_val,
                            "_ts": ts,
                        })

                # 离线延迟黑名单
                for b_name in self.state.local_blacklist:
                    if b_name not in self.state.all_nodes:
                        b_ep = self._get_ep(b_name)
                        ep_key = b_ep if b_ep else b_name
                        if ep_key in seen_d_eps:
                            continue
                        seen_d_eps.add(ep_key)

                        cur_avg_str, hist_avg_str = compute_delay_stats(b_name, b_ep, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(b_name, []))
                        b_reason = self.state.blacklist_reasons.get(b_name, self.state.blacklist_reasons.get(b_ep, "历史黑名单"))

                        ts = self.state.blacklist_timestamps.get(b_name, self.state.blacklist_timestamps.get(b_ep, 0.0))
                        ep_disp, name_disp = self._format_node_row_names(b_name, b_ep, self.state.cloud_endpoints)

                        rows.append({
                            "status": "🚫 当前订阅缺失(Endpoint不存在)",
                            "colo": "-",
                            "colo_hist": "-",
                            "reason": f"{b_reason} (历史黑名单)",
                            "delay": "已跳过",
                            "avg_delay": cur_avg_str,
                            "delay_hist": "-",
                            "hist_avg": hist_avg_str,
                            "speed": "-",
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": b_name or b_ep,
                            "_ts": ts,
                        })

                rows.sort(key=lambda x: x.get("_ts", 0.0), reverse=True)
                return rows

            elif tab_type == "speed_black":
                rows = []
                seen_s_eps = set()
                # 订阅内的低速黑名单
                for name in self.state.all_nodes:
                    ep_val = self._get_ep(name)
                    is_d_black = (not is_asian_node(name)) or (name in self.state.local_blacklist) or (ep_val and ep_val in self.state.local_blacklist)
                    is_s_black = not is_d_black and ((name in self.state.speed_blacklist) or (ep_val and ep_val in self.state.speed_blacklist))
                    if is_s_black:
                        ep_key = ep_val if ep_val else name
                        if ep_key in seen_s_eps:
                            continue
                        seen_s_eps.add(ep_key)

                        s_val = self.state.node_speeds.get(name, None)
                        s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else ("测速失败" if s_val is not None else "-")
                        colo_str = self.state.node_colo.get(ep_val, self.state.node_colo.get(name, "-"))
                        colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(ep_val, self.state.node_colo_history.get(name, [])), now, node_name=name)[3]
                        cur_avg_str, hist_avg_str = compute_delay_stats(name, ep_val, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        delay_hist_str = self._format_hist(self.state.node_history.get(name, []))
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(name, []))
                        reason_str = self.state.blacklist_reasons.get(name, self.state.blacklist_reasons.get(ep_val, "低速淘汰"))

                        ts = self.state.blacklist_timestamps.get(name, self.state.blacklist_timestamps.get(ep_val, 0.0))
                        ep_disp, name_disp = self._format_node_row_names(name, ep_val, self.state.cloud_endpoints)

                        rows.append({
                            "status": "🐌 低速黑名单",
                            "colo": colo_str,
                            "colo_hist": colo_hist_str,
                            "reason": reason_str,
                            "delay": "-",
                            "avg_delay": cur_avg_str,
                            "delay_hist": delay_hist_str,
                            "hist_avg": hist_avg_str,
                            "speed": s_str,
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": name or ep_val,
                            "_ts": ts,
                        })

                # 离线低速黑名单
                for s_name in self.state.speed_blacklist:
                    if s_name not in self.state.all_nodes:
                        s_ep = self._get_ep(s_name)
                        ep_key = s_ep if s_ep else s_name
                        if ep_key in seen_s_eps:
                            continue
                        seen_s_eps.add(ep_key)

                        cur_avg_str, hist_avg_str = compute_delay_stats(s_name, s_ep, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(s_name, []))
                        s_reason = self.state.blacklist_reasons.get(s_name, self.state.blacklist_reasons.get(s_ep, "历史低速黑名单"))

                        ts = self.state.blacklist_timestamps.get(s_name, self.state.blacklist_timestamps.get(s_ep, 0.0))
                        ep_disp, name_disp = self._format_node_row_names(s_name, s_ep, self.state.cloud_endpoints)

                        rows.append({
                            "status": "🐌 当前订阅缺失(Endpoint不存在)",
                            "colo": "-",
                            "colo_hist": "-",
                            "reason": f"{s_reason} (历史低速黑名单)",
                            "delay": "-",
                            "avg_delay": cur_avg_str,
                            "delay_hist": "-",
                            "hist_avg": hist_avg_str,
                            "speed": "低速",
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": s_name or s_ep,
                            "_ts": ts,
                        })

                rows.sort(key=lambda x: x.get("_ts", 0.0), reverse=True)
                return rows

            elif tab_type == "verified":
                # VerifiedTableView (10 列)
                rows = []
                for ep, item in self.state.verified_nodes.items():
                    rem = item.get("remark", "")
                    d_val = item.get("delay", None)
                    s_val = item.get("speed", None)
                    c_val = item.get("colo")

                    # 清洗端点为严格纯 IP:Port，杜绝机场名错位在第一列
                    clean_ep = str(item.get("endpoint", ep)).strip()
                    if "#" in clean_ep:
                        clean_ep = clean_ep.split("#")[0].strip()
                    if not re.match(r"^[\w\.\-]+\:\d+$", clean_ep):
                        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", clean_ep)
                        if m:
                            clean_ep = m.group(1)

                    colo_str = c_val if (c_val and c_val != "-") else self.state.node_colo.get(clean_ep, self.state.node_colo.get(ep, "-"))

                    # 构建统一规范名 {Colo} {Speed} MB/s
                    colo_c = colo_str if (colo_str and colo_str != "-") else "JP"
                    if not colo_c or colo_c == "-":
                        colo_c = "亚洲"
                    spd_num = s_val if (s_val is not None and s_val > 0) else self.state.node_speeds.get(clean_ep, self.state.node_speeds.get(ep, 0.0))
                    d_num = d_val if (d_val is not None and d_val < 99999 and d_val > 0) else self.state.node_delays.get(clean_ep, self.state.node_delays.get(ep, 0))
                    ver_reason = item.get("reason", "")

                    if spd_num and spd_num > 0.1:
                        calc_uniform = f"{colo_c} {spd_num:.2f} MB/s"
                    elif "C段" in ver_reason:
                        if d_num and 0 < d_num < 99999:
                            calc_uniform = f"{colo_c} [C段挖掘] {d_num}ms"
                        else:
                            calc_uniform = f"{colo_c} [C段挖掘]"
                    else:
                        if d_num and 0 < d_num < 99999:
                            calc_uniform = f"{colo_c} {d_num}ms"
                        else:
                            calc_uniform = colo_c

                    # 优先获取用户云端专属规范名
                    cloud_rem = self.state.cloud_endpoints.get(clean_ep, "")
                    if not cloud_rem and ":" in clean_ep:
                        cloud_rem = self.state.cloud_endpoints.get(clean_ep.split(":")[0], "")
                    if not cloud_rem and rem and not rem.startswith("精选拉入"):
                        cloud_rem = rem

                    uniform_name = cloud_rem if cloud_rem else calc_uniform

                    # 物理端点追踪匹配当前订阅中的最新节点名
                    matched_name = current_endpoints.get(clean_ep, "")
                    if not matched_name and ":" in clean_ep:
                        matched_name = current_ip_map.get(clean_ep.split(":")[0], "")
                    if not matched_name:
                        ep_res = get_node_endpoint(clean_ep, self.state.node_details)
                        if ep_res:
                            matched_name = current_endpoints.get(ep_res, "")

                    # 节点名称优先显示用户云端专属规范名，彻底去牛皮癣化覆盖原机场名
                    if matched_name and matched_name != "当前订阅缺失(Endpoint不存在)":
                        display_name = uniform_name
                    else:
                        display_name = f"{uniform_name} (☁️云端已存)"

                    colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(clean_ep, self.state.node_colo_history.get(ep, [])), now, node_name=display_name)[3]
                    d_str = f"{d_val} ms" if (d_val is not None and d_val < 99999) else ("超时" if d_val == 99999 else "-")
                    s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else "-"

                    first_seen = item.get("first_seen", now)
                    hours_alive = round((now - first_seen) / 3600.0, 1)
                    time_str = f"已存活 {hours_alive}h"

                    passes = item.get("passes", item.get("pass_count", 0))
                    fails = item.get("fails", 0)
                    stats_str = f"达标 {passes} 次 / 失败 {fails} 次"

                    reason_str = item.get("reason", "")
                    if not reason_str:
                        if passes > 1:
                            reason_str = f"考核留任 (达标{passes}次/{hours_alive}h)"
                        else:
                            reason_str = "优选初筛建档 (第1次达标)"

                    rows.append({
                        "endpoint": clean_ep,
                        "IP:端口": clean_ep,
                        "name": display_name,
                        "节点名称": display_name,
                        "colo": colo_str,
                        "colo_hist": colo_hist_str,
                        "reason": reason_str,
                        "remark": rem if (rem and not rem.startswith("精选拉入")) else display_name,
                        "delay": d_str,
                        "speed": s_str,
                        "time": time_str,
                        "stats": stats_str,
                        "match": display_name,
                    })
                return rows

            elif tab_type == "stars":
                # StarsTableView (8 列)
                rows = []
                for item in self.state.stars_nodes:
                    ep = item.get("endpoint", "")
                    rem = item.get("remark", "")
                    d_val = item.get("delay", None)
                    s_val = item.get("speed", None)
                    c_val = item.get("colo")
                    colo_str = c_val if (c_val and c_val != "-") else self.state.node_colo.get(ep, "-")

                    # 物理端点追踪匹配当前订阅中的最新节点名
                    matched_name = current_endpoints.get(ep, "")
                    if not matched_name and ":" in ep:
                        matched_name = current_ip_map.get(ep.split(":")[0], "")
                    if not matched_name:
                        ep_res = get_node_endpoint(ep, self.state.node_details)
                        if ep_res:
                            matched_name = current_endpoints.get(ep_res, "")

                    # 终极免死金牌：如果在当前订阅中缺失，但在云端映射中已存在，则正常显示云端命名并标注云端保活
                    if not matched_name or matched_name == "当前订阅缺失(Endpoint不存在)":
                        cloud_rem = self.state.cloud_endpoints.get(ep, "")
                        if not cloud_rem and ":" in ep:
                            cloud_rem = self.state.cloud_endpoints.get(ep.split(":")[0], "")

                        if cloud_rem:
                            matched_name = f"{cloud_rem} (☁️云端已存)"
                        else:
                            matched_name = "当前订阅缺失(Endpoint不存在)"

                    colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(ep, []), now, node_name=matched_name)[3]
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

                    rows.append({
                        "endpoint": ep,
                        "colo": colo_str,
                        "colo_hist": colo_hist_str,
                        "reason": reason_str,
                        "remark": rem,
                        "delay": d_str,
                        "speed": s_str,
                        "match": matched_name,
                    })
                return rows

            return []

    # ==================== 业务流转与节点操作 ====================

    def get_node_endpoint(self, n: str) -> str:
        """
        公开接口：获取节点的物理端点 (IP:Port)
        """
        return self._get_ep(n)

    def test_nodes_delay(self, nodes: list[str], callback=None):
        """
        并发快速测试指定节点列表的实时延迟
        """
        if not nodes:
            return
        cfg = self.load_config()
        test_url = cfg.get("test_url", "http://www.msftconnecttest.com/connecttest.txt")
        timeout_ms = int(cfg.get("test_timeout", 1500)) if str(cfg.get("test_timeout", "")).isdigit() else 1500

        # 如果传入的是端点，尝试解析出实际节点名称
        resolved_nodes = []
        reverse_map = {}
        with self.state.lock:
            for item in self.state.all_nodes:
                ep = self._get_ep(item)
                if ep:
                    reverse_map[ep] = item

        for item in nodes:
            if item in self.state.all_nodes:
                resolved_nodes.append(item)
            elif item in reverse_map:
                resolved_nodes.append(reverse_map[item])
            else:
                resolved_nodes.append(item)

        def _worker():
            self.log(f"⚡ 开始测试 {len(resolved_nodes)} 个选定节点的延迟...")
            results = {}

            def _query(node_name):
                try:
                    d = self.clash_client.query_proxy_delay(node_name, test_url, timeout_ms=timeout_ms)
                    return node_name, d
                except Exception:
                    return node_name, 99999

            with ThreadPoolExecutor(max_workers=min(16, max(1, len(resolved_nodes)))) as executor:
                for n_name, d_val in executor.map(_query, resolved_nodes):
                    results[n_name] = d_val

            with self.state.lock:
                for n_name, d_val in results.items():
                    if d_val > 0:
                        self.state.node_delays[n_name] = d_val
                        hist = self.state.node_history.setdefault(n_name, [])
                        hist.append(d_val)
                        self.state.node_history[n_name] = hist[-30:]
                        ep = self._get_ep(n_name)
                        if ep:
                            self.state.node_delays[ep] = d_val

            self.data_changed.emit()
            self.log(f"✅ {len(resolved_nodes)} 个选定节点延迟测试完成！")
            if callback:
                callback(results)

        threading.Thread(target=_worker, daemon=True).start()

    def test_nodes_colo(self, nodes: list[str], callback=None):
        """
        并发检测指定节点列表的实时物理机房 (Colo) 与严格防漂移审查
        """
        from services.probe_service import get_cf_colo_raw
        from services.colo_service import record_colo_sample
        from services.pool_service import purge_invalid_and_blacklisted_from_all_pools

        if not nodes:
            return

        targets = []
        with self.state.lock:
            for item in nodes:
                n_name = item
                ep = self._get_ep(item)
                if not ep and ":" in item:
                    ep = item
                targets.append((n_name, ep))

        def _worker():
            self.log(f"🌍 开始并发测试选中的 {len(targets)} 个节点的物理机房(Colo)...")

            def _probe(item):
                n_name, n_ep = item
                if n_ep and ":" in n_ep:
                    raw_ip, raw_port = n_ep.rsplit(":", 1)
                    c_code, c_disp = get_cf_colo_raw(raw_ip, raw_port, timeout=1.8)
                    with self.state.lock:
                        record_colo_sample(self.state.node_colo_history, n_name, n_ep, c_code, c_disp)
                        if n_name:
                            self.state.node_colo[n_name] = c_disp
                        if n_ep:
                            self.state.node_colo[n_ep] = c_disp

            with ThreadPoolExecutor(max_workers=min(15, max(1, len(targets)))) as ex:
                list(ex.map(_probe, targets))

            # 严格防漂移审查
            drift_count = 0
            now_t = time.time()
            with self.state.lock:
                for n_name, n_ep in targets:
                    colo_hist = self.state.node_colo_history.get(n_name, self.state.node_colo_history.get(n_ep, []))
                    if colo_hist:
                        _, _, has_drift, drift_disp = analyze_colo_stats(colo_hist, now_t, node_name=n_name)
                        if has_drift:
                            reason = f"机房漂移 ({drift_disp})"
                            if n_name:
                                self.state.local_blacklist.add(n_name)
                                self.state.favorites.discard(n_name)
                                self.state.blacklist_reasons[n_name] = reason
                            if n_ep:
                                self.state.local_blacklist.add(n_ep)
                                self.state.blacklist_reasons[n_ep] = reason
                                if n_ep in self.state.verified_nodes:
                                    del self.state.verified_nodes[n_ep]
                            drift_count += 1
                            self.log(f"【Colo测定-漂移淘汰】{n_name or n_ep} 发生机房漂移 ({drift_disp})，直接拉黑并清除！")

                if drift_count > 0:
                    purge_invalid_and_blacklisted_from_all_pools(
                        self.state.favorites,
                        self.state.verified_nodes,
                        self.state.stars_nodes,
                        self.state.local_blacklist,
                        self.state.speed_blacklist,
                        self._get_ep,
                    )
                    self.trigger_verge_reload()

            self.save_config(self.get_state_snapshot())
            self.data_changed.emit()
            self.log(f"✅ 选中节点 Colo 检测完成，共测定 {len(targets)} 个节点，漂移淘汰 {drift_count} 个。")
            if callback:
                callback(len(targets), drift_count)

        threading.Thread(target=_worker, daemon=True).start()

    def mine_c_subnet(self, selected_nodes=None, parent=None):
        """
        基于选中的节点/端点打开 C 段全量高并发深度挖掘对话框
        """
        seed_ip = "172.64.229.1"
        seed_port = 443

        if selected_nodes:
            if isinstance(selected_nodes, (list, tuple, set)):
                target = next(iter(selected_nodes), "")
            else:
                target = str(selected_nodes)

            ep = self._get_ep(target) or str(target)
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?", ep)
            if not m:
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?", str(target))
            if m:
                seed_ip = m.group(1)
                if m.group(2):
                    seed_port = int(m.group(2))

        # 正常打开对话框 (即使无选中也打开默认对话框)
        try:
            from gui_fluent.widgets.c_miner_dialog import CSegmentMinerDialog
            win = parent or (self.parent() if hasattr(self, "parent") else None)
            if win is None:
                if "PyQt5" in sys.modules:
                    from PyQt5.QtWidgets import QApplication
                else:
                    from PyQt6.QtWidgets import QApplication
                win = QApplication.activeWindow()

            dlg = CSegmentMinerDialog(seed_ip=seed_ip, seed_port=seed_port, controller=self, parent=win)
            dlg.exec()
        except Exception as e:
            self.log(f"❌ 启动 C 段挖掘对话框失败: {e}")

    def remove_nodes_from_favorites(self, nodes: list[str]):
        """
        将指定节点从精选池中移出
        """
        if not nodes:
            return
        with self.state.lock:
            for n in nodes:
                self.state.favorites.discard(n)
                self.state.fav_reasons.pop(n, None)
                ep = self._get_ep(n) or str(n)
                if ep:
                    self.state.favorites.discard(ep)
                    self.state.fav_reasons.pop(ep, None)
                    # 同步从云端缓存中剔除，防止被逆向复活
                    self.state.auto_endpoints.discard(ep)
                    self.state.cloud_endpoints.pop(ep, None)
                    if ":" in ep:
                        self.state.cloud_endpoints.pop(ep.split(":")[0], None)
                    for f in list(self.state.favorites):
                        if self._get_ep(f) == ep:
                            self.state.favorites.discard(f)
                            self.state.fav_reasons.pop(f, None)
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🗑️ 已从精选池移出 {len(nodes)} 个节点")
        self.sync_favorites_to_cloud()

    def clear_all_favorites(self):
        """
        清空优质精选池
        """
        with self.state.lock:
            self.state.favorites.clear()
            self.state.fav_reasons.clear()
            self.state.auto_endpoints.clear()
            self.state.cloud_endpoints.clear()
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log("🗑️ 优质精选池已全部清空。")
        self.sync_favorites_to_cloud()

    def move_nodes_to_favorites(self, nodes: list[str]):
        """
        将指定节点加入优质精选池，并同步清除对应物理端点 (IP:Port) 的所有衍生黑名单
        """
        if not nodes:
            return
        with self.state.lock:
            for n in nodes:
                ep = self._get_ep(n)
                self.state.favorites.add(n)
                self.state.fav_reasons[n] = "手动设为优质"
                self.state.local_blacklist.discard(n)
                self.state.speed_blacklist.discard(n)
                self.state.blacklist_reasons.pop(n, None)
                if ep:
                    self.state.local_blacklist.discard(ep)
                    self.state.speed_blacklist.discard(ep)
                    self.state.blacklist_reasons.pop(ep, None)
                    # 清除共享相同 IP:Port 的衍生命名节点
                    for b in list(self.state.local_blacklist):
                        if self._get_ep(b) == ep:
                            self.state.local_blacklist.discard(b)
                            self.state.blacklist_reasons.pop(b, None)
                    for s in list(self.state.speed_blacklist):
                        if self._get_ep(s) == ep:
                            self.state.speed_blacklist.discard(s)
                            self.state.blacklist_reasons.pop(s, None)

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"⭐ 已手动将 {len(nodes)} 个节点加入优质精选池 (并同步清除同端点黑名单)")

    def promote_nodes_to_stars(self, nodes: list[str]):
        """
        将指定节点晋升至典藏管理池
        """
        if not nodes:
            return
        added_count = 0
        with self.state.lock:
            existing_eps = {s.get("endpoint", "") for s in self.state.stars_nodes}
            for n in nodes:
                ep = self._get_ep(n) or n
                if ep not in existing_eps:
                    colo = self.state.node_colo.get(ep, self.state.node_colo.get(n, "-"))
                    d_val = self.state.node_delays.get(n, self.state.node_delays.get(ep, None))
                    s_val = self.state.node_speeds.get(n, self.state.node_speeds.get(ep, None))
                    self.state.stars_nodes.append({
                        "endpoint": ep,
                        "remark": f"手动晋升 ({n})",
                        "reason": "手动晋升典藏",
                        "colo": colo,
                        "delay": d_val,
                        "speed": s_val,
                    })
                    existing_eps.add(ep)
                    added_count += 1
                self.state.favorites.add(n)
                if ep:
                    self.state.local_blacklist.discard(ep)
                    self.state.speed_blacklist.discard(ep)
                    self.state.blacklist_reasons.pop(ep, None)
                    for b in list(self.state.local_blacklist):
                        if self._get_ep(b) == ep:
                            self.state.local_blacklist.discard(b)
                            self.state.blacklist_reasons.pop(b, None)
                    for s in list(self.state.speed_blacklist):
                        if self._get_ep(s) == ep:
                            self.state.speed_blacklist.discard(s)
                            self.state.blacklist_reasons.pop(s, None)

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🏆 已将 {len(nodes)} 个节点晋升至典藏管理池 (新增 {added_count} 个独立端点)")

    def blacklist_nodes(self, nodes: list[str], reason: str = "手动拉黑", bl_type: str = "delay"):
        """
        将指定节点加入延迟或低速黑名单，同时拉黑共享相同 IP:Port 端点的所有衍生节点，并从精选池与孵化池彻底移出
        """
        if not nodes:
            return
        now_t = time.time()
        with self.state.lock:
            if not hasattr(self.state, "blacklist_timestamps"):
                self.state.blacklist_timestamps = {}

            for n in nodes:
                ep = self._get_ep(n)
                target_names = {n}
                if ep:
                    for item_name in list(self.state.all_nodes) + list(self.state.favorites):
                        if self._get_ep(item_name) == ep:
                            target_names.add(item_name)

                for t_name in target_names:
                    if bl_type == "speed":
                        self.state.speed_blacklist.add(t_name)
                    else:
                        self.state.local_blacklist.add(t_name)
                    self.state.blacklist_reasons[t_name] = reason
                    self.state.blacklist_timestamps[t_name] = now_t
                    self.state.favorites.discard(t_name)

                if ep:
                    if bl_type == "speed":
                        self.state.speed_blacklist.add(ep)
                    else:
                        self.state.local_blacklist.add(ep)
                    self.state.blacklist_reasons[ep] = reason
                    self.state.blacklist_timestamps[ep] = now_t
                    self.state.favorites.discard(ep)
                    for f in list(self.state.favorites):
                        if self._get_ep(f) == ep:
                            self.state.favorites.discard(f)
                    if ep in self.state.verified_nodes:
                        del self.state.verified_nodes[ep]

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        tag = "低速黑名单" if bl_type == "speed" else "延迟黑名单"
        self.log(f"🚫 已手动将 {len(nodes)} 个节点加入{tag} (原因: {reason})，并关联处理了同端点衍生节点")

    def remove_nodes_from_blacklist(self, nodes: list[str]):
        """
        将指定节点从黑名单中移出，恢复至活跃池。
        同时确保清除了共享相同 IP:Port 物理端点的所有衍生命名节点。
        """
        if not nodes:
            return
        with self.state.lock:
            ts_map = getattr(self.state, "blacklist_timestamps", {})
            for n in nodes:
                ep = self._get_ep(n)
                self.state.local_blacklist.discard(n)
                self.state.speed_blacklist.discard(n)
                self.state.blacklist_reasons.pop(n, None)
                ts_map.pop(n, None)
                if ep:
                    self.state.local_blacklist.discard(ep)
                    self.state.speed_blacklist.discard(ep)
                    self.state.blacklist_reasons.pop(ep, None)
                    ts_map.pop(ep, None)
                    # 清除共享相同 IP:Port 的所有衍生命名节点
                    for b in list(self.state.local_blacklist):
                        if self._get_ep(b) == ep:
                            self.state.local_blacklist.discard(b)
                            self.state.blacklist_reasons.pop(b, None)
                            ts_map.pop(b, None)
                    for s in list(self.state.speed_blacklist):
                        if self._get_ep(s) == ep:
                            self.state.speed_blacklist.discard(s)
                            self.state.blacklist_reasons.pop(s, None)
                            ts_map.pop(s, None)

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"↩ 已将 {len(nodes)} 个节点及其同端点别名从黑名单移出，恢复至活跃待测池")

        # 移出黑名单的节点自动上传至云端待测池 (/pending.txt)，确保全量优选能再次纳测
        unblacklisted_eps = []
        for n in nodes:
            ep = self._get_ep(n)
            if ep and ep != "127.0.0.1:443":
                unblacklisted_eps.append((ep, f"{self.state.node_colo.get(n, '亚洲')} [解黑恢复待测]"))
        if unblacklisted_eps:
            import threading
            threading.Thread(
                target=self.append_pending_endpoints_to_cloud,
                args=(unblacklisted_eps,),
                daemon=True
            ).start()

    def clear_all_blacklists(self):
        """
        一键清空所有延迟与低速黑名单
        """
        with self.state.lock:
            d_count = len(self.state.local_blacklist)
            s_count = len(self.state.speed_blacklist)
            self.state.local_blacklist.clear()
            self.state.speed_blacklist.clear()
            self.state.blacklist_reasons.clear()
            if hasattr(self.state, "blacklist_timestamps"):
                self.state.blacklist_timestamps.clear()

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🧹 已清空所有黑名单记录 (清理延迟黑名单 {d_count} 项，低速黑名单 {s_count} 项)")

    def trigger_verge_reload(self):
        """
        生成 Script.js 策略组配置并触发 Win32 系统热键刷新 Verge
        """
        return self.reload_verge_with_fission(None)

    def reload_verge_with_fission(self, fission_proxies=None):
        """
        生成包含临时裂变节点的 Script.js 并触发热更 (fission_proxies=None 时物理恢复纯净配置)
        """
        with self.state.lock:
            favs = set(self.state.favorites)
            stars = list(self.state.stars_nodes)
            all_n = list(self.state.all_nodes)
            n_det = dict(self.state.node_details)

        cfg = self.load_config() or {}
        g_inter = str(cfg.get("group_interval", "300"))
        g_tol = str(cfg.get("group_tolerance", "20"))
        s_inter = str(cfg.get("star_group_interval", "300"))
        s_tol = str(cfg.get("star_group_tolerance", "20"))

        script_code, p_tokens, s_tokens = build_script_js(
            favorites=favs,
            stars_nodes=stars,
            all_nodes=all_n,
            node_details=n_det,
            group_interval=g_inter,
            group_tolerance=g_tol,
            star_group_interval=s_inter,
            star_group_tolerance=s_tol,
            is_asian_node_fn=is_asian_node,
            get_node_endpoint_fn=self._get_ep,
            fission_proxies=fission_proxies,
        )
        ok, res = write_script_js(script_code)
        if ok:
            fiss_cnt = len(fission_proxies) if fission_proxies else 0
            if fiss_cnt > 0:
                self.log(f"⚡ Script.js 临时裂变注入成功 (裂变节点: {fiss_cnt} 个，优选: {len(p_tokens)} 个)")
            else:
                self.log(f"✅ Script.js 纯净策略组恢复成功 (优选: {len(p_tokens)} 个，典藏: {len(s_tokens)} 个)")
        else:
            self.log(f"⚠️ Script.js 写入失败: {res}")

        hk_ok, hk_msg = trigger_verge_reactivate_hotkey()
        if hk_ok:
            self.log(f"⚡ 热键通知成功: {hk_msg}")
        else:
            self.log(f"⚠️ 热键触发反馈: {hk_msg}")
        return hk_ok

    # ==================== TopBar 顶部工具栏业务 ====================

    def update_remote_subscription_sync(self, yaml_filename: str = None) -> tuple[bool, str]:
        """
        同步在线拉取并更新指定（或当前）订阅 YAML 文件，更新后重新解析加载节点
        """
        from config.settings import BASE_DIR
        from services.subscription_service import update_remote_subscription

        target_name = yaml_filename or getattr(self.state, "active_profile", "")
        if not target_name:
            profiles = self.get_all_yaml_profiles()
            target_name = profiles[0] if profiles else ""

        if not target_name:
            msg = "未定位到可更新的订阅配置文件！"
            self.log(f"⚠️ {msg}")
            return False, msg

        target_path = os.path.join(BASE_DIR, target_name)
        mixed_port = self.clash_client.get_mixed_port(default=7897)

        self.log(f"🔄 开始在线拉取更新订阅: {target_name}...")
        try:
            ok, msg, changed = update_remote_subscription(target_path, mixed_port=mixed_port)
            if ok:
                self.log(f"✅ 订阅更新成功: {msg}")
                self.load_nodes_from_profile(target_name)
                self.data_changed.emit()
                return True, msg
            else:
                self.log(f"⚠️ 订阅更新失败: {msg}")
                return False, msg
        except Exception as e:
            err_msg = f"更新订阅异常: {e}"
            self.log(f"❌ {err_msg}")
            return False, err_msg

    def update_current_subscription(self, yaml_filename: str = None, callback=None):
        """
        在线拉取并更新指定（或当前）订阅 YAML 文件，并自动执行 Script.js 写入与热更探测闭环（异步后台线程）
        """
        def _worker():
            ok, msg = self.update_remote_subscription_sync(yaml_filename)
            if ok:
                self.log("⚡ 订阅拉取完成，正在重新生成 Script.js 策略组并触发热更...")
                self.generate_script_and_reload()
                time.sleep(0.5)
                loaded_ok, loaded_msg = self.clash_client.wait_for_kernel_reload(
                    self.state.all_nodes, max_wait_sec=10
                )
                self.log(f"内核装载探测: {loaded_msg}")
            if callback:
                callback(ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    def test_current_page_colo(self, page_key: str = "active", callback=None):
        """
        并发检测指定页面中所有节点的实时物理机房 (Colo) 与严格防漂移审查
        """
        from services.probe_service import get_cf_colo_raw
        from services.colo_service import record_colo_sample
        from services.pool_service import purge_invalid_and_blacklisted_from_all_pools

        rows = self.get_table_rows(page_key)
        if not rows:
            self.log(f"⚠️ 当前页面 [{page_key}] 暂无节点可供测试 Colo")
            if callback:
                callback(0, 0)
            return

        targets = []
        for r in rows:
            name = r.get("name") or r.get("matched_name", "")
            ep = r.get("endpoint", "")
            if not ep and name:
                ep = self._get_ep(name)
            targets.append((name, ep))

        def _worker():
            self.log(f"🌍 开始并发测试当前页面 [{page_key}] 共 {len(targets)} 个节点的物理机房(Colo)...")

            def _probe(item):
                n_name, n_ep = item
                if n_ep and ":" in n_ep:
                    raw_ip, raw_port = n_ep.rsplit(":", 1)
                    c_code, c_disp = get_cf_colo_raw(raw_ip, raw_port, timeout=1.8)
                    with self.state.lock:
                        record_colo_sample(self.state.node_colo_history, n_name, n_ep, c_code, c_disp)
                        if n_name:
                            self.state.node_colo[n_name] = c_disp
                        if n_ep:
                            self.state.node_colo[n_ep] = c_disp

            with ThreadPoolExecutor(max_workers=15) as ex:
                list(ex.map(_probe, targets))

            # 严格防漂移审查
            drift_count = 0
            now_t = time.time()
            with self.state.lock:
                for n_name, n_ep in targets:
                    colo_hist = self.state.node_colo_history.get(n_name, self.state.node_colo_history.get(n_ep, []))
                    if colo_hist:
                        _, _, has_drift, drift_disp = analyze_colo_stats(colo_hist, now_t, node_name=n_name)
                        if has_drift:
                            reason = f"机房漂移 ({drift_disp})"
                            if n_name:
                                self.state.local_blacklist.add(n_name)
                                self.state.favorites.discard(n_name)
                                self.state.blacklist_reasons[n_name] = reason
                            if n_ep:
                                self.state.local_blacklist.add(n_ep)
                                self.state.blacklist_reasons[n_ep] = reason
                                if n_ep in self.state.verified_nodes:
                                    del self.state.verified_nodes[n_ep]
                            drift_count += 1
                            self.log(f"【页面Colo测定-漂移淘汰】{n_name or n_ep} 发生机房漂移 ({drift_disp})，直接拉黑并清除！")

                if drift_count > 0:
                    purge_invalid_and_blacklisted_from_all_pools(
                        self.state.favorites,
                        self.state.verified_nodes,
                        self.state.stars_nodes,
                        self.state.local_blacklist,
                        self.state.speed_blacklist,
                        self._get_ep,
                    )
                    self.trigger_verge_reload()

            self.save_config(self.get_state_snapshot())
            self.data_changed.emit()
            self.log(f"✅ 当前页面 Colo 检测完成，共测定 {len(targets)} 个节点，漂移淘汰 {drift_count} 个。")
            if callback:
                callback(len(targets), drift_count)

        threading.Thread(target=_worker, daemon=True).start()

    def clear_current_page_colo(self, page_key: str = "active") -> int:
        """
        清空指定页面中所有节点的实时 Colo 及历史记录
        """
        rows = self.get_table_rows(page_key)
        if not rows:
            return 0
        cleared_count = 0
        with self.state.lock:
            for r in rows:
                name = r.get("name") or r.get("matched_name", "")
                ep = r.get("endpoint", "")
                if not ep and name:
                    ep = self._get_ep(name)
                keys_to_clean = [name, ep]
                if ep and ":" in ep:
                    keys_to_clean.append(ep.split(":")[0])
                for k in keys_to_clean:
                    if k:
                        self.state.node_colo.pop(k, None)
                        self.state.node_colo_history.pop(k, None)
                if ep in self.state.verified_nodes:
                    self.state.verified_nodes[ep]["colo"] = "-"
                for s in self.state.stars_nodes:
                    if s.get("endpoint") == ep or (name and s.get("matched_name") == name):
                        s["colo"] = "-"
                cleared_count += 1

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🧹 已清空页面 [{page_key}] 共 {cleared_count} 个节点的机房 (Colo) 记录与时序历史")
        return cleared_count

    def sync_kernel_delays(self) -> bool:
        """
        从内核 /proxies 同步所有节点延迟与时延历史
        """
        data = self.clash_client.call_api("/proxies")
        if not data or "proxies" not in data:
            self.log("⚠️ 无法从 Clash 内核获取代理节点列表")
            return False

        proxies = data["proxies"]
        updated = 0
        with self.state.lock:
            for name, info in proxies.items():
                history = info.get("history", [])
                if history:
                    delays = [h.get("delay", 0) for h in history if isinstance(h.get("delay"), int)]
                    normalized = [d if d > 0 else 99999 for d in delays]
                    if normalized:
                        self.state.node_history[name] = normalized[-4:]
                        self.state.node_delays[name] = normalized[-1]
                        updated += 1
        if updated > 0:
            self.data_changed.emit()
            self.log(f"🔄 已成功从 Clash 内核同步 {updated} 个节点的实时延迟与历史记录")
            return True
        else:
            self.log("ℹ️ 内核中暂无可同步的节点延迟历史")
            return False

    def clear_speed_records(self, silent=False):
        """
        清空所有测速数据与延迟趋势记录
        """
        with self.state.lock:
            self.state.node_delays.clear()
            self.state.node_history.clear()
            self.state.node_speeds.clear()

        threading.Thread(
            target=lambda: self.clash_client.call_api("/configs?force=true", method="PUT", data={"path": ""}),
            daemon=True,
        ).start()

        self.data_changed.emit()
        self.log("🗑️ 所有节点测速记录与延迟轨迹已全部重置归零。")

    # ==================== 优质精选池专属业务 ====================

    def clean_stale_favorites(self):
        """
        清理精选池中已过期（不在当前订阅中）或已在黑名单中的失效节点
        """
        with self.state.lock:
            stale = [
                n for n in self.state.favorites
                if n not in self.state.all_nodes
                or n in self.state.local_blacklist
                or n in self.state.speed_blacklist
            ]
            for n in stale:
                self.state.favorites.discard(n)
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🧹 已清理 {len(stale)} 个过期/失效/已拉黑的精选节点")

    def sync_favorites_to_active(self):
        """
        将精选池节点名称与当前活跃订阅进行双向对齐映射
        """
        from services.pool_service import align_favorites_with_current_subscription
        from services.subscription_service import resolve_node_to_current

        with self.state.lock:
            migrated = align_favorites_with_current_subscription(
                self.state.favorites,
                self.state.all_nodes,
                lambda k: resolve_node_to_current(k, self.state.all_nodes, self.state.node_details),
            )
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"⚡ 精选池已与当前活跃订阅完成双向对齐映射 (迁移更名: {migrated} 个)！")

    # ==================== Cloudflare Worker 同步与纯文本推送 ====================

    def get_cf_worker_config(self) -> tuple[bool, str, str]:
        """
        获取 Cloudflare Worker 配置: (enabled, url, token)
        """
        cfg = self.load_config() or {}
        enabled = bool(cfg.get("cf_worker_enabled", False))
        url = str(cfg.get("worker_url") or cfg.get("cf_worker_url", "https://cf-nodes.douyutvshow.workers.dev/")).strip()
        token = str(cfg.get("worker_token") or cfg.get("cf_worker_token", "MySecretToken2026")).strip()
        return enabled, url, token

    def fetch_cloud_text(self, subpath: str = "", base_url: str = None, token: str = None) -> tuple[bool, str]:
        """
        从 Cloudflare Worker 拉取指定子路径的纯文本内容。
        支持双通道回退（优先 Clash 代理，失败回退直连）。
        """
        cfg = self.load_config()
        b_url = (base_url or cfg.get("worker_url") or cfg.get("cf_worker_url", "")).rstrip("/")
        tok = token or cfg.get("worker_token") or cfg.get("cf_worker_token", "")

        if not b_url or not b_url.startswith("http"):
            return False, "Worker 网址无效"

        target_url = f"{b_url}{subpath}" if subpath else f"{b_url}/"
        mixed_port = self.clash_client.get_mixed_port(default=7897)

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
            "Authorization": f"Bearer {tok}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        req = urllib.request.Request(target_url, headers=headers)

        last_err = ""
        for attempt in range(1, 4):
            for use_proxy, opener in [(True, proxy_opener), (False, direct_opener)]:
                try:
                    with opener.open(req, timeout=10) as resp:
                        if resp.status == 200:
                            content = resp.read().decode("utf-8", errors="ignore")
                            return True, content
                        last_err = f"Worker 返回状态码: {resp.status}"
                except urllib.error.HTTPError as ex:
                    if ex.code == 401:
                        return False, "认证失败(401)，请确认 AUTH_TOKEN 密钥！"
                    last_err = f"HTTP({ex.code}): {ex.reason}"
                except Exception as ex:
                    last_err = str(ex)
            time.sleep(0.5)

        return False, f"拉取失败: {last_err}"

    def push_cloud_text(self, subpath: str = "", text: str = "", base_url: str = None, token: str = None) -> tuple[bool, str]:
        """
        推送纯文本内容至 Cloudflare Worker（别名包装）
        """
        return self.push_text_to_cf_worker(text_payload=text, subpath=subpath, base_url=base_url, token=token)

    def fetch_cloud_endpoints_sync(self) -> dict[str, str]:
        """
        同步从 Cloudflare Worker 拉取 /auto.txt，并解析端点与专属备注映射字典。
        支持纯 IPv4:Port 以及 域名(FQDN):Port (如 saas.sin.fan:443)
        返回: { "Endpoint": "云端专属备注名", "Host": "云端专属备注名" }
        """
        ok, content = self.fetch_cloud_text("/auto.txt")
        cloud_map = {}
        if not ok or not content:
            self.log(f"⚠️ 未能从云端获取 auto.txt: {content if not ok else '内容为空'}")
            return cloud_map

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//") or line.startswith("⏳") or line.startswith("Error"):
                continue
            if "#" in line:
                parts = line.split("#", 1)
                ep_str = parts[0].strip()
                remark_str = parts[1].strip()
            else:
                parts = line.split(None, 1)
                ep_str = parts[0].strip()
                remark_str = parts[1].strip() if len(parts) > 1 else ""

            # 优先匹配规范的主机:端口 (支持 IPv4、IPv6及 FQDN 域名)
            m = re.match(r"^([\w\.\-]+):(\d{1,5})$", ep_str)
            if not m:
                # 兼容文本中嵌有 IPv4:Port 的情况
                m_ip = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?", ep_str)
                if m_ip:
                    ip = m_ip.group(1)
                    port = m_ip.group(2) if m_ip.group(2) else "443"
                    endpoint = f"{ip}:{port}"
                    host = ip
                else:
                    continue
            else:
                host = m.group(1)
                port = m.group(2)
                endpoint = f"{host}:{port}"

            effective_rem = remark_str if remark_str else "云端精选"
            cloud_map[endpoint] = effective_rem
            if host not in cloud_map:
                cloud_map[host] = effective_rem

        with self.state.lock:
            self.state.cloud_endpoints = cloud_map
            self.state.auto_endpoints = set(cloud_map.keys())
        valid_lines_count = len([line for line in content.splitlines() if line.strip() and not line.strip().startswith(("#", "//", "⏳", "Error"))])
        self.log(f"☁️ 从云端 auto.txt 成功同步 {valid_lines_count} 个精选节点 (已建立 {len(cloud_map)} 条多键映射)")
        return cloud_map

    def fetch_pending_endpoints_sync(self) -> dict[str, str]:
        """
        同步从 Cloudflare Worker 拉取 /pending.txt，获取待测归收池节点
        支持纯 IPv4:Port 与 域名(FQDN):Port
        返回: { "Endpoint": "待测备注名" }
        """
        ok, content = self.fetch_cloud_text("/pending.txt")
        pending_map = {}
        if not ok or not content:
            return pending_map

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//") or line.startswith("Error"):
                continue
            if "#" in line:
                parts = line.split("#", 1)
                ep_str = parts[0].strip()
                rem_str = parts[1].strip()
            else:
                parts = line.split(None, 1)
                ep_str = parts[0].strip()
                rem_str = parts[1].strip() if len(parts) > 1 else "待测节点"

            m = re.match(r"^([\w\.\-]+):(\d{1,5})$", ep_str)
            if not m:
                m_ip = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?", ep_str)
                if m_ip:
                    ip = m_ip.group(1)
                    port = m_ip.group(2) if m_ip.group(2) else "443"
                    endpoint = f"{ip}:{port}"
                else:
                    continue
            else:
                endpoint = f"{m.group(1)}:{m.group(2)}"

            pending_map[endpoint] = rem_str

        with self.state.lock:
            self.state.pending_endpoints = pending_map
        if pending_map:
            self.log(f"☁️ 从云端 pending.txt 成功同步 {len(pending_map)} 个待测节点")
        return pending_map

    def append_pending_endpoints_to_cloud(self, endpoints_with_remarks: list[tuple[str, str]]):
        if not endpoints_with_remarks:
            return
        with self.pending_pool_lock:
            current_map = self.fetch_pending_endpoints_sync()
            for ep, rem in endpoints_with_remarks:
                if ep and ep != "127.0.0.1:443":
                    current_map[ep] = rem or "待测候选"

            lines = [f"{ep}#{rem}" for ep, rem in current_map.items()]
            payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
            ok, msg = self.push_text_to_cf_worker(payload, subpath="/pending.txt")
            if ok:
                self.log(f"☁️ 成功同步 {len(endpoints_with_remarks)} 个节点至云端待测池 (/pending.txt，现有总量: {len(current_map)})")
            else:
                self.log(f"⚠️ 同步云端待测池 /pending.txt 失败: {msg}")

    def append_pending_endpoints_to_cloud_sync(self, endpoints_with_remarks: list[tuple[str, str]]) -> tuple[bool, str]:
        if not endpoints_with_remarks:
            return True, "无待测节点需要同步"
        with self.pending_pool_lock:
            current_map = self.fetch_pending_endpoints_sync()
            with self.state.lock:
                excluded = set()
                for n in (self.state.favorites | self.state.local_blacklist | self.state.speed_blacklist):
                    ep = self._get_ep(n)
                    if ep:
                        excluded.add(ep)
                        if ":" in ep:
                            excluded.add(ep.split(":")[0])
                    else:
                        excluded.add(str(n).strip())
                for star in self.state.stars_nodes:
                    s_ep = star.get("endpoint", "") if isinstance(star, dict) else ""
                    if s_ep:
                        excluded.add(s_ep)
                        if ":" in s_ep:
                            excluded.add(s_ep.split(":")[0])
                for v_ep in self.state.verified_nodes:
                    excluded.add(str(v_ep).strip())
                    if ":" in str(v_ep):
                        excluded.add(str(v_ep).split(":")[0])

            new_added = 0
            for ep, rem in endpoints_with_remarks:
                if not ep or ep == "127.0.0.1:443" or ep.startswith("1.1.1.1"):
                    continue
                ip_only = ep.split(":")[0] if ":" in ep else ep
                if ep not in excluded and ip_only not in excluded:
                    current_map[ep] = rem or "待测候选"
                    new_added += 1

            lines = [f"{ep}#{rem}" for ep, rem in current_map.items() if ep and not ep.startswith("1.1.1.1")]
            payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
            ok, msg = self.push_text_to_cf_worker(payload, subpath="/pending.txt")
            if ok:
                with self.state.lock:
                    self.state.pending_endpoints = current_map
                return True, f"成功同步待测池 (/pending.txt，本次新增 {new_added} 个，现有总量: {len(current_map)})"
            return False, f"同步待测池失败: {msg}"

    def purge_pending_endpoints_from_cloud(self) -> int:
        with self.pending_pool_lock:
            try:
                pending_map = self.fetch_pending_endpoints_sync()
                if not pending_map:
                    return 0

                forbidden_eps = set()
                with self.state.lock:
                    for s in (self.state.local_blacklist | self.state.speed_blacklist | self.state.favorites):
                        ep = self._get_ep(s)
                        if ep:
                            forbidden_eps.add(ep)
                            if ":" in ep:
                                forbidden_eps.add(ep.split(":")[0])
                        else:
                            forbidden_eps.add(str(s).strip())

                    for v_ep in self.state.verified_nodes:
                        forbidden_eps.add(str(v_ep).strip())
                        if ":" in str(v_ep):
                            forbidden_eps.add(str(v_ep).split(":")[0])

                    for star in self.state.stars_nodes:
                        s_ep = star.get("endpoint", "") if isinstance(star, dict) else ""
                        if s_ep:
                            forbidden_eps.add(s_ep)
                            if ":" in s_ep:
                                forbidden_eps.add(s_ep.split(":")[0])

                cleaned_map = {}
                purged_cnt = 0
                for ep, rem in pending_map.items():
                    if not ep or ep.startswith("1.1.1.1"):
                        purged_cnt += 1
                        continue
                    ip_only = ep.split(":")[0] if ":" in ep else ep
                    if ep in forbidden_eps or ip_only in forbidden_eps:
                        purged_cnt += 1
                        continue
                    cleaned_map[ep] = rem

                if purged_cnt > 0:
                    lines = [f"{ep}#{rem}" for ep, rem in cleaned_map.items()]
                    payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
                    ok, msg = self.push_text_to_cf_worker(payload, subpath="/pending.txt")
                    if ok:
                        with self.state.lock:
                            self.state.pending_endpoints = cleaned_map
                        self.log(f"🧹 已成功清洗云端待测池 (/pending.txt)：剔除已入黑名单/精选/孵化/典藏节点 {purged_cnt} 个，待测剩余 {len(cleaned_map)} 个")
                        return purged_cnt
                    else:
                        self.log(f"⚠️ 清洗云端待测池未回执成功: {msg}，已挂起后台自动补救自愈！")
                        self._schedule_pending_purge_retry()
                        return -1
                else:
                    self.log("☁️ 云端待测池当前已是纯净状态，无已判决的淘汰节点需要清洗。")
                    return 0
            except Exception as ex:
                self.log(f"❌ 清洗云端待测池异常: {ex}")
                self._schedule_pending_purge_retry()
                return -1

    def _schedule_pending_purge_retry(self):
        """后台挂起 20 秒延迟自动自愈重试清洗"""
        def _delay_worker():
            time.sleep(20)
            self.log("🔄 [后台自愈] 正在执行挂起的云端待测池清洗重试任务...")
            self.purge_pending_endpoints_from_cloud()
        import threading
        threading.Thread(target=_delay_worker, daemon=True).start()

    def trigger_cloud_sync_and_purge_safely(self):
        """
        在 Clash 内核稳定就绪后，以专属线程平稳执行精选池推云与待测池清洗
        """
        def _worker():
            try:
                # 1. 安全同步精选池至云端
                self.sync_favorites_to_cloud()
                time.sleep(1.0)
                # 2. 全池联动清洗待测池
                self.purge_pending_endpoints_from_cloud()
            except Exception as ex:
                self.log(f"❌ 平稳推云与清洗线程异常: {ex}")
        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def push_text_to_cf_worker(self, text_payload: str, subpath: str = "", base_url: str = None, token: str = None) -> tuple[bool, str]:
        """
        推送纯文本内容至 Cloudflare Worker。
        具备【urllib + 系统原生 curl.exe】双引擎强力容灾保底机制，彻底解决 SSL 握手超时痛点。
        """
        import os
        import subprocess
        import tempfile

        cfg = self.load_config()
        b_url = (base_url or cfg.get("worker_url") or cfg.get("cf_worker_url", "")).rstrip("/")
        tok = token or cfg.get("worker_token") or cfg.get("cf_worker_token", "")

        if not b_url or not b_url.startswith("http"):
            return False, "Worker 网址无效"

        if not text_payload or not text_payload.strip():
            text_payload = "# empty\r\n"

        target_url = f"{b_url}{subpath}" if subpath else f"{b_url}/"
        mixed_port = self.clash_client.get_mixed_port(default=7897)

        # 引擎 1: Python 原生 urllib (优先代理，失败回退直连，超时放宽至 15s)
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
            "Authorization": f"Bearer {tok}",
            "Content-Type": "text/plain; charset=utf-8",
            "User-Agent": "ClashVergeNodeAssistant/1.0",
        }
        req_data = text_payload.encode("utf-8")

        urllib_err = ""
        for attempt in range(1, 3):
            for use_proxy, opener in [(True, proxy_opener), (False, direct_opener)]:
                try:
                    req = urllib.request.Request(target_url, data=req_data, headers=headers, method="POST")
                    with opener.open(req, timeout=15) as resp:
                        if resp.status in (200, 201, 204):
                            channel = f"代理端口:{mixed_port}" if use_proxy else "直连"
                            return True, f"成功推送至 {target_url} ({channel})"
                        urllib_err = f"Worker 状态码: {resp.status}"
                except urllib.error.HTTPError as ex:
                    if ex.code == 401:
                        return False, "认证失败(401)，请确认 AUTH_TOKEN 密钥！"
                    urllib_err = f"HTTP({ex.code}): {ex.reason}"
                except Exception as ex:
                    urllib_err = str(ex)
            time.sleep(0.5)

        # 引擎 2 (终极保底): 自动唤醒 Windows 系统底层原生 curl.exe 执行强力穿透
        self.log(f"⚠️ [双引擎自愈] urllib 握手异常 ({urllib_err})，自动唤醒系统原生 curl.exe 强力保底...")
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tf:
                tf.write(req_data)
                temp_file_path = tf.name

            for curl_proxy in [f"http://127.0.0.1:{mixed_port}", None]:
                curl_cmd = [
                    "curl.exe", "-s",
                    "--max-time", "15",
                    "--retry", "2",
                    "-X", "POST",
                    "-H", f"Authorization: Bearer {tok}",
                    "-H", "Content-Type: text/plain; charset=utf-8",
                    "--data-binary", f"@{temp_file_path}",
                    target_url
                ]
                if curl_proxy:
                    curl_cmd.extend(["--proxy", curl_proxy])
                else:
                    curl_cmd.append("--noproxy", "*")

                res = subprocess.run(curl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode == 0:
                    out_msg = res.stdout.decode("utf-8", errors="ignore").strip()
                    self.log(f"✅ [双引擎自愈] curl.exe 保底成功: {out_msg or '写入成功'}")
                    return True, f"curl.exe 保底成功: {out_msg or '写入成功'}"
        except Exception as curl_ex:
            self.log(f"❌ [双引擎自愈] curl.exe 执行异常: {curl_ex}")
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

        return False, f"双引擎重试失败: {urllib_err}"

    def sync_premium_nodes_to_cf_worker(self, premium_nodes: list[str] = None, subpath: str = "/auto.txt") -> tuple[bool, str]:
        """
        将指定优质节点列表（默认全量 favorites）同步格式化推送到 Worker 指定子路径
        """
        with self.state.lock:
            nodes_to_push = list(premium_nodes) if premium_nodes is not None else list(self.state.favorites)
            lines = []
            seen_eps = set()
            for n in nodes_to_push:
                ep = self._get_ep(n) or n
                if not ep or ep == "127.0.0.1:443" or ep in seen_eps:
                    continue
                seen_eps.add(ep)
                colo = self.state.node_colo.get(n, self.state.node_colo.get(ep, "JP"))
                if not colo or colo == "-":
                    colo = "亚洲"
                spd = self.state.node_speeds.get(n, self.state.node_speeds.get(ep, 0.0))
                d = self.state.node_delays.get(n, self.state.node_delays.get(ep, 0))
                reason = self.state.fav_reasons.get(n, self.state.fav_reasons.get(ep, ""))

                if spd and spd > 0.1:
                    remark = f"{colo} {spd:.2f} MB/s"
                elif "C段" in reason:
                    remark = f"{colo} [C段挖掘]"
                else:
                    remark = colo
                lines.append(f"{ep}#{remark}")

        if not lines:
            return True, "本地优质池为空，跳过推送"
        payload = "\r\n".join(lines) + "\r\n"
        return self.push_text_to_cf_worker(payload, subpath=subpath)

    def push_favorites_to_cloud(self, base_url: str = None, token: str = None, callback=None):
        """
        异步推送优质精选池节点至 Cloudflare Worker /auto.txt
        """
        def _worker():
            with self.state.lock:
                fav_count = len(self.state.favorites)
            self.log(f"☁️ 正在推送 {fav_count} 个优质精选节点至 /auto.txt...")
            ok, msg = self.sync_premium_nodes_to_cf_worker(subpath="/auto.txt")
            if ok:
                self.log(f"✅ 同步优质精选池至 /auto.txt 成功: {msg}")
            else:
                self.log(f"❌ 同步优质精选池失败: {msg}")
            if callback:
                callback(ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    def sync_favorites_to_cloud(self):
        """
        将当前最新的 favorites 精选池全量覆写至 Cloudflare Worker /auto.txt 并重载映射
        (严格核验有效物理端点，彻底禁绝无端点纯文本马甲被误推上云污染云端)
        """
        def _worker():
            try:
                fav_lines = []
                seen_eps = set()
                with self.state.lock:
                    for f in list(self.state.favorites):
                        ep_val = self._get_ep(f)
                        if not ep_val:
                            # 尝试从 cloud_endpoints 或名称中反查有效端点
                            if re.match(r"^[\w\.\-]+:\d+$", str(f).strip()):
                                ep_val = str(f).strip()
                            else:
                                for c_ep, c_rem in self.state.cloud_endpoints.items():
                                    if c_rem and (c_rem == f or str(f).startswith(c_rem)):
                                        if ":" in c_ep:
                                            ep_val = c_ep
                                            break
                        # 强校验：必须为有效的 host:port 格式，且排除本地回环与重复项
                        if not ep_val or not re.match(r"^[\w\.\-]+:\d+$", ep_val) or ep_val in seen_eps or ep_val == "127.0.0.1:443":
                            continue
                        seen_eps.add(ep_val)

                        colo = self.state.node_colo.get(f, self.state.node_colo.get(ep_val, "JP"))
                        if not colo or colo == "-":
                            colo = "亚洲"

                        spd = self.state.node_speeds.get(f, self.state.node_speeds.get(ep_val, 0.0))
                        d = self.state.node_delays.get(f, self.state.node_delays.get(ep_val, 0))
                        reason = self.state.fav_reasons.get(f, self.state.fav_reasons.get(ep_val, ""))

                        # 优先级 1：只要有真实测速带宽 (>0.1)，必须以真实下载速度加冕！
                        if spd and spd > 0.1:
                            uniform_name = f"{colo} {spd:.2f} MB/s"
                        # 优先级 2：仅当该节点确系 C 段挖掘导入、且尚未测速时，显示 [C段挖掘]，绝不带毫秒延迟
                        elif "C段" in reason:
                            uniform_name = f"{colo} [C段挖掘]"
                        # 优先级 3：其他未测速的常规节点，仅显示归属地
                        else:
                            uniform_name = colo

                        fav_lines.append(f"{ep_val}#{uniform_name}")
                        self.state.cloud_endpoints[ep_val] = uniform_name
                        if ":" in ep_val:
                            self.state.cloud_endpoints[ep_val.split(":")[0]] = uniform_name

                payload = ("\r\n".join(fav_lines) + "\r\n") if fav_lines else "# empty\r\n"
                ok, msg = self.push_text_to_cf_worker(payload, subpath="/auto.txt")
                if ok:
                    self.log(f"☁️ 已自动同步最新精选池 ({len(fav_lines)} 个) 至云端 /auto.txt")
                else:
                    self.log(f"⚠️ 自动同步云端 /auto.txt 失败: {msg}")

                self.fetch_cloud_endpoints_sync()
                self.save_config(self.get_state_snapshot())
                self.data_changed.emit()
            except Exception as e:
                self.log(f"❌ 同步精选至云端异常: {e}")

        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def test_worker_connection(self, worker_url: str = None, token: str = None, callback=None):
        """
        测试 Cloudflare Worker 通道连通性与权限认证
        """
        def _worker():
            self.log("🌐 正在测试 Cloudflare Worker 通信连接与鉴权...")
            ok, content = self.fetch_cloud_text(subpath="/auto.txt", base_url=worker_url, token=token)
            if ok:
                msg = f"Worker 通信正常！成功获取云端响应 (内容长度: {len(content)} 字符)"
                self.log(f"✅ {msg}")
            else:
                msg = f"Worker 通信测试失败: {content}"
                self.log(f"❌ {msg}")
            if callback:
                callback(ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    # ==================== 沉淀孵化池专属业务 ====================

    def pull_verified_from_cloud(self, base_url: str = None, callback=None):
        """
        从 Cloudflare Worker 拉取 /verified.txt 沉淀节点
        """
        cfg = self.load_config()
        b_url = (base_url or cfg.get("worker_url") or cfg.get("cf_worker_url", "")).rstrip("/")
        if not b_url.startswith("http"):
            msg = "请配置有效的 Cloudflare Worker 地址！"
            self.log(f"⚠️ {msg}")
            if callback:
                callback(False, msg)
            return

        def _worker():
            self.log("正在从 Cloudflare /verified.txt 拉取沉淀节点...")
            mixed_port = self.clash_client.get_mixed_port(default=7897)
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

            try:
                req = urllib.request.Request(f"{b_url}/verified.txt", headers={"User-Agent": "ClashVergeNodeAssistant/1.0"})
                with opener.open(req, timeout=10) as resp:
                    raw_text = resp.read().decode("utf-8", errors="ignore")

                now = time.time()
                with self.state.lock:
                    fav_eps = {self._get_ep(f) for f in self.state.favorites if f and self._get_ep(f)}
                    fav_eps.discard("")
                    fav_eps.discard("127.0.0.1:443")

                    added_count = 0
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

                        # 沉淀孵化池必须是优质精选池的严格子集
                        if ep not in fav_eps:
                            continue

                        if not (is_asian_node(ep) or (rem and is_asian_node(rem))):
                            self.state.local_blacklist.add(ep)
                            continue

                        if ep not in self.state.verified_nodes:
                            self.state.verified_nodes[ep] = {
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
                            added_count += 1

                self.save_config(self.get_state_snapshot())
                self.data_changed.emit()
                msg = f"成功拉取云端沉淀节点！当前池内共 {len(self.state.verified_nodes)} 个。"
                self.log(f"✅ {msg}")
                if callback:
                    callback(True, msg)
            except Exception as ex:
                err_msg = f"拉取 /verified.txt 失败: {str(ex)}"
                self.log(f"❌ {err_msg}")
                if callback:
                    callback(False, err_msg)

        threading.Thread(target=_worker, daemon=True).start()

    def push_verified_to_cloud(self, base_url: str = None, token: str = None, callback=None):
        """
        推送沉淀池至 Cloudflare Worker /verified.txt
        """
        with self.state.lock:
            lines = [f"{v['endpoint']}#{v.get('remark', '')}" for v in self.state.verified_nodes.values() if v.get("endpoint")]
        payload = "\r\n".join(lines) + "\r\n"

        def _worker():
            self.log(f"正在推送 {len(lines)} 个沉淀节点至 /verified.txt...")
            ok, msg = self.push_text_to_cf_worker(payload, "/verified.txt", base_url=base_url, token=token)
            if ok:
                self.log(f"✅ 手动同步沉淀池至 /verified.txt 成功: {msg}")
            else:
                self.log(f"❌ 手动同步沉淀池失败: {msg}")
            if callback:
                callback(ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    def delete_selected_verified(self, endpoints: list[str]):
        """
        从沉淀池移除选定端点
        """
        if not endpoints:
            return
        with self.state.lock:
            for ep in endpoints:
                self.state.verified_nodes.pop(ep, None)
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🗑️ 已从沉淀孵化池移除 {len(endpoints)} 个节点")
        self.push_verified_to_cloud()

    def force_promote_verified_to_stars(self, endpoints: list[str]) -> int:
        """
        将选定沉淀节点提前加冕至典藏常青池
        """
        if not endpoints:
            return 0
        cnt = 0
        with self.state.lock:
            existing_eps = {s.get("endpoint") for s in self.state.stars_nodes}
            for ep in endpoints:
                if ep in self.state.verified_nodes and ep not in existing_eps:
                    v = self.state.verified_nodes[ep]
                    self.state.stars_nodes.append({
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
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🏆 手动加冕 {cnt} 个沉淀节点至典藏常青池")
        return cnt

    def sync_favorites_to_verified(self):
        """
        从精选池手工纳入新端点至沉淀孵化池
        """
        now = time.time()
        cnt = 0
        with self.state.lock:
            for f in self.state.favorites:
                ep = self._get_ep(f)
                if not ep or ep == "127.0.0.1:443":
                    continue
                if ep not in self.state.verified_nodes:
                    self.state.verified_nodes[ep] = {
                        "endpoint": ep,
                        "colo": self.state.node_colo.get(f, "-"),
                        "remark": f"精选拉入 [{f}]",
                        "first_seen": now,
                        "passes": 1,
                        "fails": 0,
                        "delay": self.state.node_delays.get(f),
                        "speed": self.state.node_speeds.get(f),
                        "matched_name": f,
                        "reason": "从精选池手工纳入",
                    }
                    cnt += 1
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"📥 已将精选池中 {cnt} 个新端点纳入沉淀孵化池")

    # ==================== 典藏管理池专属业务 ====================

    def pull_stars_from_cloud(self, base_url: str = None, callback=None):
        """
        从 Cloudflare Worker 根目录拉取典藏常青节点
        """
        cfg = self.load_config()
        b_url = (base_url or cfg.get("worker_url") or cfg.get("cf_worker_url", "")).rstrip("/")
        if not b_url.startswith("http"):
            msg = "请配置有效的 Cloudflare Worker 地址！"
            self.log(f"⚠️ {msg}")
            if callback:
                callback(False, msg)
            return

        def _worker():
            self.log("正在从 Cloudflare 根目录拉取典藏常青节点...")
            mixed_port = self.clash_client.get_mixed_port(default=7897)
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

            try:
                req = urllib.request.Request(f"{b_url}/", headers={"User-Agent": "ClashVergeNodeAssistant/1.0"})
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
                    new_stars.append({
                        "endpoint": ep,
                        "colo": "-",
                        "remark": rem,
                        "delay": None,
                        "speed": None,
                        "reason": "云端根目录同步",
                    })

                with self.state.lock:
                    self.state.stars_nodes = new_stars
                self.save_config(self.get_state_snapshot())
                self.data_changed.emit()
                msg = f"成功从云端拉取并同步 {len(new_stars)} 个典藏常青节点！"
                self.log(f"✅ {msg}")
                if callback:
                    callback(True, msg)
            except Exception as ex:
                err_msg = f"从云端拉取典藏失败: {str(ex)}"
                self.log(f"❌ {err_msg}")
                if callback:
                    callback(False, err_msg)

        threading.Thread(target=_worker, daemon=True).start()

    def push_stars_to_cloud(self, base_url: str = None, token: str = None, callback=None):
        """
        手动同步典藏常青池到 Cloudflare 根目录
        """
        with self.state.lock:
            lines = [f"{s.get('endpoint', '')}#{s.get('remark', '')}" for s in self.state.stars_nodes if s.get("endpoint")]
        payload = "\r\n".join(lines) + "\r\n"

        def _worker():
            self.log(f"正在手动推送 {len(lines)} 个典藏常青节点至 Cloudflare 根目录...")
            ok, msg = self.push_text_to_cf_worker(payload, "", base_url=base_url, token=token)
            if ok:
                self.log(f"✅ 手动同步典藏常青池到根目录成功: {msg}")
            else:
                self.log(f"❌ 手动同步典藏常青池失败: {msg}")
            if callback:
                callback(ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    def add_star_node(self, endpoint: str, remark: str = "典藏节点") -> bool:
        """
        手动录入单个典藏节点
        """
        ep = endpoint.strip()
        if not ep:
            return False
        with self.state.lock:
            for s in self.state.stars_nodes:
                if s.get("endpoint") == ep:
                    s["remark"] = remark
                    self.save_config(self.get_state_snapshot())
                    self.data_changed.emit()
                    return True
            self.state.stars_nodes.append({
                "endpoint": ep,
                "colo": "-",
                "remark": remark,
                "delay": None,
                "speed": None,
                "reason": "手动录入典藏",
            })
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"➕ 已成功将节点 [{ep}] 录入典藏池")
        return True

    def update_star_remark(self, endpoint: str, new_remark: str):
        """
        修改典藏节点备注
        """
        with self.state.lock:
            for s in self.state.stars_nodes:
                if s.get("endpoint") == endpoint:
                    s["remark"] = new_remark.strip()
                    break
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"✏️ 已更新典藏节点 [{endpoint}] 的备注为: {new_remark.strip()}")

    def delete_selected_stars(self, endpoints: list[str]):
        """
        从典藏池移除选定端点
        """
        if not endpoints:
            return
        ep_set = set(endpoints)
        with self.state.lock:
            self.state.stars_nodes = [s for s in self.state.stars_nodes if s.get("endpoint") not in ep_set]
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🗑️ 已从典藏池移除 {len(endpoints)} 个节点")
        self.push_stars_to_cloud()

    def test_stars_pipeline(self, mode="delay", endpoints: list[str] = None, callback=None):
        """
        对典藏节点执行延迟或带宽测速
        """
        with self.state.lock:
            stars = list(self.state.stars_nodes)
            all_n = list(self.state.all_nodes)

        if endpoints:
            ep_set = set(endpoints)
            targets = [s for s in stars if s.get("endpoint") in ep_set]
        else:
            targets = stars

        if not targets:
            self.log("⚠️ 当前典藏池没有节点可测！")
            if callback:
                callback(False, "无待测节点")
            return

        reverse_map = {}
        for n in all_n:
            ep = self._get_ep(n)
            if ep:
                reverse_map[ep] = n

        testable = []
        for t in targets:
            ep = t.get("endpoint", "")
            m_name = reverse_map.get(ep, "")
            if not m_name and ":" in ep:
                m_name = reverse_map.get(ep.split(":")[0], "")
            if m_name:
                t["matched_name"] = m_name
                testable.append(t)

        if not testable:
            msg = "所选典藏节点尚未在当前订阅/Clash内核中找到对应的匹配节点！"
            self.log(f"⚠️ {msg}")
            if callback:
                callback(False, msg)
            return

        cfg = self.load_config()
        test_url = cfg.get("test_url", "https://www.google.com/generate_204")
        speed_url = cfg.get("speed_url", "https://speed.cloudflare.com/__down?bytes=50000000")

        def _worker():
            self.log(f"开始测试 {len(testable)} 个典藏节点 (模式: {mode})...")
            if mode == "delay":
                from services.probe_service import get_cf_colo_raw
                from services.colo_service import record_colo_sample
                for item in testable:
                    name = item["matched_name"]
                    d_val = self.clash_client.query_proxy_delay(name, test_url, timeout_ms=1500)
                    item["delay"] = d_val
                    ep_raw = item.get("endpoint", "")
                    if ":" in ep_raw:
                        s_ip, s_p = ep_raw.rsplit(":", 1)
                        c_code, c_disp = get_cf_colo_raw(s_ip, s_p)
                        with self.state.lock:
                            record_colo_sample(self.state.node_colo_history, name, ep_raw, c_code, c_disp)
                            item["colo"] = c_disp
                            self.state.node_colo[name] = c_disp
                            self.state.node_colo[ep_raw] = c_disp
                self.save_config(self.get_state_snapshot())
                self.data_changed.emit()
                self.log("✅ 典藏节点延迟测速完成！")
                if callback:
                    callback(True, "延迟测速完成")
            else:
                mode_guard = ClashModeGuard(self.clash_client, temporary_mode="global")
                mode_guard.__enter__()
                mixed_port = self.clash_client.get_mixed_port(default=7897)
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
                        self.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": name})
                        time.sleep(0.1)

                        speed_val = 0.0
                        total_bytes = 0
                        st = time.time()
                        try:
                            req = urllib.request.Request(speed_url, headers={"User-Agent": "Mozilla/5.0", "Connection": "close"})
                            with speed_opener.open(req, timeout=2.5) as resp:
                                chunk_size = 16 * 1024
                                while time.time() - st < 2.0:
                                    ch = resp.read(chunk_size)
                                    if not ch:
                                        break
                                    total_bytes += len(ch)
                                el = time.time() - st
                                speed_val = round((total_bytes / (1024 * 1024)) / el, 2) if (el > 0 and total_bytes > 0) else 0.0
                        except Exception:
                            speed_val = -1.0
                        item["speed"] = speed_val
                finally:
                    mode_guard.__exit__(None, None, None)

                self.save_config(self.get_state_snapshot())
                self.data_changed.emit()
                self.log("✅ 典藏节点带宽测速完成！")
                if callback:
                    callback(True, "带宽测速完成")

        threading.Thread(target=_worker, daemon=True).start()
