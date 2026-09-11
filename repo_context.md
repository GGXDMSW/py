```python
File: main_fluent.py
"""
Clash Verge 节点管理助手 (Fluent 版)
规范化主启动入口
"""
import os
import sys
import traceback

# 优先导入 qfluentwidgets 以确定加载的 Qt 运行时绑定 (PyQt5 或 PyQt6)
import qfluentwidgets

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QMessageBox
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QMessageBox

from gui_fluent.main_window import MainWindow


def run_fluent_app():
    """
    启动 Fluent UI 主程序
    """
    try:
        # 高分屏清晰渲染适配 (Win11)
        if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )

        if hasattr(Qt, "AA_EnableHighDpiScaling"):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, "AA_UseHighDpiPixmaps"):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setApplicationName("ClashVergeAssistantFluent")

        window = MainWindow()
        window.show()

        sys.exit(app.exec_() if hasattr(app, "exec_") else app.exec())
    except Exception:
        err_msg = traceback.format_exc()
        try:
            with open("error_fluent_startup.log", "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        try:
            QMessageBox.critical(None, "启动异常", f"Fluent 版程序启动失败：\n{err_msg}")
        except Exception:
            print(f"Fluent 版程序启动失败：\n{err_msg}")


if __name__ == "__main__":
    run_fluent_app()

```

```python
File: gui_fluent/app_controller.py
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
from config.config_manager import atomic_save_config, safe_load_config, prune_expired_history
from pipelines.scheduler import SchedulerDaemon
from services.clash_client import ClashClient, ClashModeGuard
from services.subscription_service import get_node_endpoint, choose_canonical_node_name
from services.colo_service import is_asian_node, analyze_colo_stats
from services.filter_service import compute_delay_stats
from services.pool_service import get_pool_endpoint_sets
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
        self.clash_client = ClashClient(host="127.0.0.1", port=9097, secret="")
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

```

```python
File: gui_fluent/main_window.py
"""
Clash Verge 节点管理助手 - Fluent 风格主窗口
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QStackedWidget,
    )
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QStackedWidget,
    )

from qfluentwidgets import (
    SegmentedWidget,
    MessageBox,
    setTheme,
    Theme,
    PushButton,
)

from gui_fluent.app_controller import AppController
from gui_fluent.components.top_bar import TopBar
from gui_fluent.components.log_panel import LogPanel
from gui_fluent.components.bottom_action_bar import BottomActionBar
from gui_fluent.components.pipeline_card import PipelineCard

from gui_fluent.pages.page_active import PageActive
from gui_fluent.pages.page_favorites import PageFavorites
from gui_fluent.pages.page_verified import PageVerified
from gui_fluent.pages.page_stars import PageStars
from gui_fluent.pages.page_delay_black import PageDelayBlack
from gui_fluent.pages.page_speed_black import PageSpeedBlack
from gui_fluent.pages.page_cloud_text import PageCloudText

from gui_fluent.widgets.c_miner_dialog import CSegmentMinerDialog


class MainWindow(QWidget):
    """
    基于 PyQt-Fluent-Widgets 构建的全新横向顶部导航 Fluent 主窗口
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_app()

    def init_app(self):
        # 1. 基础属性与 Windows 11 深色主题
        self.setWindowTitle("Clash Verge 节点管理助手 (Fluent 版)")
        setTheme(Theme.DARK)
        self.setStyleSheet("""
            MainWindow {
                background-color: #1a1a1a;
                color: #f1f5f9;
            }
        """)

        self.setMinimumSize(1200, 760)
        self.resize(1260, 800)
        self.center_on_screen()

        # 2. 实例化中枢控制器
        self.controller = AppController(self)

        # 3. 组装自上而下的整体垂直布局结构
        self.init_layout_structure()

        # 4. 初始化 7 个子页面并添加到 stackedWidget 和顶部横向 SegmentedWidget
        self.init_sub_pages()

        # 5. 绑定控制器日志信号至界面日志面板
        self.controller.log_signal.connect(self.log_panel.append_log)
        self.controller.log("欢迎使用 Clash Verge 节点管理助手 (Fluent UI 现代版)！")

        # 6. 绑定流水线控制卡信号
        self._bind_pipeline_signals()

        # 7. 绑定底部操作栏业务动作
        self._bind_bottom_actions()

        # 8. 接入后台定时调度守护与精选自愈降级
        self.controller.set_scheduler_config_provider(self._get_scheduler_config)
        self.controller.scheduler_trigger_full_signal.connect(self._on_scheduler_trigger_full)
        self.controller.scheduler_trigger_fav_signal.connect(self._on_scheduler_trigger_fav)
        self.controller.fav_pipeline_fallback_needed.connect(self._on_fav_fallback_needed)

        # 9. 恢复初始配置与历史回显
        cfg = self.controller.load_config() or {}
        self.restore_ui_config(cfg)

    def init_layout_structure(self):
        """
        构建主窗体自上而下的整体布局结构：
        - SegmentedWidget (横向菜单，靠左排列)
        - self.top_bar (包含订阅与右侧一排测速按钮)
        - self.pipeline_card (流水线参数卡片)
        - self.stackedWidget (核心表格区，设置 stretch=1)
        - self.log_panel (日志区)
        - self.bottom_action_bar (底部按键)
        """
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 10)
        self.main_layout.setSpacing(8)

        # 1. 顶部横向 SegmentedWidget 与 C段挖掘入口
        self.nav_layout = QHBoxLayout()
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.segment = SegmentedWidget(self)
        self.nav_layout.addWidget(self.segment)
        self.nav_layout.addStretch(1)
        
        self.btn_c_miner = PushButton("🔍 C段深度挖掘", self)
        self.btn_c_miner.clicked.connect(self._on_c_miner_clicked)
        self.nav_layout.addWidget(self.btn_c_miner)

        self.main_layout.addLayout(self.nav_layout)

        # 2. 上：TopBar (~68px)
        self.top_bar = TopBar(self)
        self.top_bar.setFixedHeight(68)
        self.main_layout.addWidget(self.top_bar)

        # 3. 中上：PipelineCard（流水线参数控制卡）
        self.pipeline_card = PipelineCard(self)
        self.main_layout.addWidget(self.pipeline_card)

        # 4. 中：StackedWidget (核心表格区，自适应伸展 stretch=1)
        self.stackedWidget = QStackedWidget(self)
        self.main_layout.addWidget(self.stackedWidget, 1)

        # 5. 下：LogPanel (~120px)
        self.log_panel = LogPanel(self)
        self.log_panel.setFixedHeight(120)
        self.main_layout.addWidget(self.log_panel)

        # 6. 下：BottomActionBar (~50px)
        self.bottom_action_bar = BottomActionBar(self)
        self.bottom_action_bar.setFixedHeight(50)
        self.main_layout.addWidget(self.bottom_action_bar)

    def init_sub_pages(self):
        """
        创建 7 个功能页面，装配进 stackedWidget，并在顶部横排 SegmentedWidget 中注册标签项
        """
        self.page_active = PageActive(self.controller, self)
        self.page_favorites = PageFavorites(self.controller, self)
        self.page_verified = PageVerified(self.controller, self)
        self.page_stars = PageStars(self.controller, self)
        self.page_delay_black = PageDelayBlack(self.controller, self)
        self.page_speed_black = PageSpeedBlack(self.controller, self)
        self.page_cloud_text = PageCloudText(self.controller, self)

        # 页面加入 QStackedWidget
        self.stackedWidget.addWidget(self.page_active)
        self.stackedWidget.addWidget(self.page_favorites)
        self.stackedWidget.addWidget(self.page_verified)
        self.stackedWidget.addWidget(self.page_stars)
        self.stackedWidget.addWidget(self.page_delay_black)
        self.stackedWidget.addWidget(self.page_speed_black)
        self.stackedWidget.addWidget(self.page_cloud_text)

        # 顶部横排菜单注册项
        self.segment.addItem(
            routeKey="active",
            text="📋 活跃待测",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_active),
        )
        self.segment.addItem(
            routeKey="favorites",
            text="⭐ 优质精选",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_favorites),
        )
        self.segment.addItem(
            routeKey="verified",
            text="⏳ 沉淀孵化",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_verified),
        )
        self.segment.addItem(
            routeKey="stars",
            text="🏆 典藏管理",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_stars),
        )
        self.segment.addItem(
            routeKey="delay_black",
            text="🚫 延迟黑名单",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_delay_black),
        )
        self.segment.addItem(
            routeKey="speed_black",
            text="🐌 低速黑名单",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_speed_black),
        )
        self.segment.addItem(
            routeKey="cloud_text",
            text="☁️ 云端文本",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_cloud_text),
        )

        self.segment.setCurrentItem("active")

        # 监听标签页切换事件，切换时自动刷新目标页面数据
        self.stackedWidget.currentChanged.connect(self._on_page_changed)
        self.controller.data_changed.connect(self.update_tab_badges)
        self.update_tab_badges()

    def update_tab_badges(self):
        """
        动态更新顶部导航栏各标签后的实时节点数量角标
        """
        try:
            cnt_active = len(self.controller.get_table_rows("active"))
            cnt_fav = len(self.controller.get_table_rows("favorites"))
            cnt_ver = len(self.controller.get_table_rows("verified"))
            cnt_stars = len(self.controller.get_table_rows("stars"))
            cnt_delay_bl = len(self.controller.get_table_rows("delay_black"))
            cnt_speed_bl = len(self.controller.get_table_rows("speed_black"))

            self.segment.setItemText("active", f"📋 活跃待测 ({cnt_active})")
            self.segment.setItemText("favorites", f"⭐ 优质精选 ({cnt_fav})")
            self.segment.setItemText("verified", f"⏳ 沉淀孵化 ({cnt_ver})")
            self.segment.setItemText("stars", f"🏆 典藏管理 ({cnt_stars})")
            self.segment.setItemText("delay_black", f"🚫 延迟黑名单 ({cnt_delay_bl})")
            self.segment.setItemText("speed_black", f"🐌 低速黑名单 ({cnt_speed_bl})")
            self.segment.setItemText("cloud_text", "☁️ 云端文本")
        except Exception:
            pass

    def center_on_screen(self):
        """
        窗口居中显示于当前屏幕
        """
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(max(0, x), max(0, y))

    def _bind_pipeline_signals(self):
        pc = self.pipeline_card
        # 重连按钮：调用 AppController 检测连接状态并更新状态标签
        pc.btn_reconnect.clicked.connect(self._on_reconnect_clicked)

        # 启动与终止流水线按钮
        pc.btn_run_pipeline.clicked.connect(self._on_run_pipeline_clicked)
        pc.btn_stop_pipeline.clicked.connect(self._on_stop_pipeline_clicked)

        # 核心设置卡片操作按钮
        pc.btn_save_group.clicked.connect(self._on_save_group_clicked)
        pc.btn_test_worker.clicked.connect(self._on_test_worker_clicked)
        pc.btn_sync_auto.clicked.connect(self._on_sync_auto_clicked)

        # 绑定流水线结束与状态信号
        self.controller.pipeline_finished.connect(self._on_pipeline_finished)
        self.controller.pipeline_status_updated.connect(self._on_pipeline_status_updated)

        # 顶部 TopBar 快捷操作组按钮绑定
        self.top_bar.btn_update_sub.clicked.connect(self._on_update_sub_clicked)
        self.top_bar.btn_test_page_colo.clicked.connect(self._on_test_page_colo_clicked)
        self.top_bar.btn_clear_page_colo.clicked.connect(self._on_clear_page_colo_clicked)
        self.top_bar.btn_sync_kernel_delay.clicked.connect(self._on_sync_kernel_delay_clicked)
        self.top_bar.btn_clear_speed_records.clicked.connect(self._on_clear_speed_records_clicked)

        # 订阅下拉框加载可用 YAML 文件
        try:
            yamls = self.controller.get_all_yaml_profiles()
            self.top_bar.sub_combo.addItems(yamls)
            self.top_bar.sub_combo.currentTextChanged.connect(self._on_sub_combo_changed)
        except Exception:
            pass

    def _on_sub_combo_changed(self, yaml_name: str):
        if not yaml_name:
            return
        try:
            nodes, _ = self.controller.load_nodes_from_profile(yaml_name)
            setattr(self.controller.state, "active_profile", yaml_name)
            self.controller.save_config({"last_selected_yaml": yaml_name, "active_profile": yaml_name})
            self.controller.log(f"已切换订阅配置 [{yaml_name}]，加载了 {len(nodes)} 个节点")
            self.controller.data_changed.emit()
        except Exception as e:
            self.controller.log(f"加载订阅配置 [{yaml_name}] 失败: {str(e)}")

    def _on_run_pipeline_clicked(self):
        pc = self.pipeline_card
        current_yaml = self.top_bar.sub_combo.currentText().strip()
        if current_yaml and not self.controller.state.all_nodes:
            self._on_sub_combo_changed(current_yaml)

        config = {
            "max_delay": pc.max_delay.text().strip(),
            "min_speed": pc.min_speed.text().strip(),
            "target_count": pc.target_count.text().strip(),
            "test_rounds": pc.test_rounds.text().strip(),
            "test_timeout": pc.test_timeout.text().strip(),
            "speed_duration": pc.speed_duration.text().strip(),
            "blacklist_threshold": pc.blacklist_threshold.text().strip(),
            "speed_bl_threshold": pc.speed_bl_threshold.text().strip(),
            "speed_bl_rounds": pc.speed_bl_rounds.text().strip(),
            "jitter_min_delay": pc.jitter_min_delay.text().strip(),
            "jitter_up_threshold": pc.jitter_up_threshold.text().strip(),
            "test_url": pc.test_url.text().strip(),
            "speed_url": pc.speed_url.text().strip(),
            "schedule_interval": pc.schedule_interval.text().strip(),
            "schedule_times": pc.schedule_times.text().strip(),
            "group_interval": pc.group_interval.text().strip(),
            "group_tolerance": pc.group_tolerance.text().strip(),
            "star_group_interval": pc.star_group_interval.text().strip(),
            "star_group_tolerance": pc.star_group_tolerance.text().strip(),
            "worker_url": pc.worker_url.text().strip(),
            "worker_token": pc.worker_token.text().strip(),
            "clash_port": pc.clash_port.text().strip(),
            "clash_secret": pc.clash_secret.text().strip(),
        }

        started = self.controller.start_auto_pipeline(config)
        if started:
            pc.btn_run_pipeline.setEnabled(False)
            pc.btn_stop_pipeline.setEnabled(True)

    def _on_stop_pipeline_clicked(self):
        self.controller.stop_auto_pipeline()
        pc = self.pipeline_card
        pc.btn_stop_pipeline.setEnabled(False)

    def _on_pipeline_finished(self, success: bool, desc: str):
        pc = self.pipeline_card
        pc.btn_run_pipeline.setEnabled(True)
        pc.btn_stop_pipeline.setEnabled(False)
        self.controller.log(f"流水线运行结束: {'成功' if success else '中断/失败'} - {desc}")
        if hasattr(self, 'controller') and self.controller:
            self.controller.save_config(self.controller.state.get_snapshot())

        # 弹窗汇报大优选完成总结
        title = "🎉 全量大优选任务完成" if success else "⚠️ 流水线结束"
        fav_count = len(self.controller.state.favorites)
        star_count = len(self.controller.state.stars_nodes)
        d_bl_count = len(self.controller.state.local_blacklist)
        s_bl_count = len(self.controller.state.speed_blacklist)

        content = (
            f"【执行状态】: {desc}\n\n"
            f"📊 核心池最新统计：\n"
            f"  • ⭐ 优质精选池: {fav_count} 个\n"
            f"  • 🏆 典藏常青池: {star_count} 个\n"
            f"  • 🚫 延迟黑名单: {d_bl_count} 个\n"
            f"  • 🐌 低速黑名单: {s_bl_count} 个\n\n"
            f"✅ 最新策略组已自动写入 Script.js 并生效。"
        )
        msg_box = MessageBox(title, content, self)
        if hasattr(msg_box, "cancelButton") and msg_box.cancelButton:
            msg_box.cancelButton.hide()
        msg_box.exec()

    def _on_pipeline_status_updated(self, status_text: str):
        self.pipeline_card.lbl_sched_status.setText(status_text)

    def _on_reconnect_clicked(self):
        pc = self.pipeline_card
        port_text = pc.clash_port.text().strip()
        secret_text = pc.clash_secret.text().strip()
        try:
            port = int(port_text) if port_text else 9097
        except ValueError:
            port = 9097
        self.controller.update_clash_credentials(port=port, secret=secret_text)
        ok, ver = self.controller.get_clash_connection_status()
        if ok:
            pc.lbl_conn_status.setText(f"● 已连接 v{ver}")
            pc.lbl_conn_status.setStyleSheet("color: #10b981; font-weight: bold;")
            self.top_bar.lbl_status.setText(f"● 内核已连接 v{ver}")
            self.top_bar.lbl_status.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            pc.lbl_conn_status.setText("● 连接失败")
            pc.lbl_conn_status.setStyleSheet("color: #f87171; font-weight: bold;")
            self.top_bar.lbl_status.setText("● 内核未连接")
            self.top_bar.lbl_status.setStyleSheet("color: #f87171; font-weight: bold;")
        self.controller.log(f"Clash 连接检测: {'成功' if ok else '失败'} {ver}")

    def _on_save_group_clicked(self):
        pc = self.pipeline_card
        cfg = {
            "group_interval": pc.group_interval.text().strip(),
            "group_tolerance": pc.group_tolerance.text().strip(),
            "star_group_interval": pc.star_group_interval.text().strip(),
            "star_group_tolerance": pc.star_group_tolerance.text().strip(),
        }
        self.controller.save_config(cfg)
        self.controller.generate_script_and_reload()
        self.controller.log("💾 策略组配置已保存并重新写入 Script.js！")

    def _on_test_worker_clicked(self):
        pc = self.pipeline_card
        w_url = pc.worker_url.text().strip()
        w_tok = pc.worker_token.text().strip()
        self.controller.save_config({"worker_url": w_url, "worker_token": w_tok})
        self.controller.test_worker_connection(worker_url=w_url, token=w_tok)

    def _on_sync_auto_clicked(self):
        pc = self.pipeline_card
        w_url = pc.worker_url.text().strip()
        w_tok = pc.worker_token.text().strip()
        self.controller.save_config({"worker_url": w_url, "worker_token": w_tok})
        self.controller.push_favorites_to_cloud(base_url=w_url, token=w_tok)

    def _on_page_changed(self, index: int):
        """
        导航标签页切换时，同步顶部菜单高亮并主动刷新目标页面的表格数据
        """
        page = self.stackedWidget.currentWidget()
        route_map = {
            self.page_active: "active",
            self.page_favorites: "favorites",
            self.page_verified: "verified",
            self.page_stars: "stars",
            self.page_delay_black: "delay_black",
            self.page_speed_black: "speed_black",
            self.page_cloud_text: "cloud_text",
        }
        route_key = route_map.get(page)
        if route_key and self.segment.currentRouteKey() != route_key:
            self.segment.setCurrentItem(route_key)

        if page and hasattr(page, "refresh_data"):
            page.refresh_data()
        self.update_tab_badges()

    # ==================== 底部快捷操作栏绑定 ====================

    def _bind_bottom_actions(self):
        """
        绑定底部操作栏按钮的点击事件
        """
        bar = self.bottom_action_bar
        try:
            bar.btn_fav.clicked.disconnect()
        except Exception:
            pass
        bar.btn_fav.clicked.connect(self._on_btn_fav_clicked)

        try:
            bar.btn_promote.clicked.disconnect()
        except Exception:
            pass
        bar.btn_promote.clicked.connect(self._on_btn_promote_clicked)

        try:
            bar.btn_delay_black.clicked.disconnect()
        except Exception:
            pass
        bar.btn_delay_black.clicked.connect(self._on_btn_delay_black_clicked)

        try:
            bar.btn_speed_black.clicked.disconnect()
        except Exception:
            pass
        bar.btn_speed_black.clicked.connect(self._on_btn_speed_black_clicked)

        try:
            bar.btn_unblack.clicked.disconnect()
        except Exception:
            pass
        bar.btn_unblack.clicked.connect(self._on_btn_unblack_clicked)

        try:
            bar.btn_clear_bl.clicked.disconnect()
        except Exception:
            pass
        bar.btn_clear_bl.clicked.connect(self._on_btn_clear_bl_clicked)

        try:
            bar.btn_rescore.clicked.disconnect()
        except Exception:
            pass
        bar.btn_rescore.clicked.connect(self._on_btn_rescore_clicked)

        try:
            bar.btn_hotkey_sync.clicked.disconnect()
        except Exception:
            pass
        bar.btn_hotkey_sync.clicked.connect(self._on_btn_hotkey_sync_clicked)

    def _get_current_selected_nodes(self) -> list[str]:
        """
        获取当前激活页面中表格选中的节点名称或物理端点列表
        """
        page = self.stackedWidget.currentWidget()
        if not page or not hasattr(page, "table"):
            return []
        t = page.table
        if hasattr(t, "get_selected_node_names"):
            names = t.get_selected_node_names()
            if names:
                return names
        if hasattr(t, "get_selected_endpoints"):
            eps = t.get_selected_endpoints()
            if eps:
                return eps
        return []

    def _on_c_miner_clicked(self):
        """
        呼出 C 段全量极速深度挖掘对话框
        """
        seed_ip = "172.64.229.1"
        nodes = self._get_current_selected_nodes()
        if nodes:
            ep = nodes[0]
            if ":" in ep:
                seed_ip = ep.split(":")[0]
            else:
                seed_ip = ep
        dialog = CSegmentMinerDialog(seed_ip=seed_ip, seed_port=443, controller=self.controller, parent=self)
        dialog.exec()

    def _on_btn_fav_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要设为优质的节点！")
            return
        self.controller.move_nodes_to_favorites(nodes)

    def _on_btn_promote_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要晋升典藏的节点！")
            return
        self.controller.promote_nodes_to_stars(nodes)

    def _on_btn_delay_black_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要加入延迟黑名单的节点！")
            return
        self.controller.blacklist_nodes(nodes, reason="手动拉黑", bl_type="delay")

    def _on_btn_speed_black_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要加入低速黑名单的节点！")
            return
        self.controller.blacklist_nodes(nodes, reason="手动拉黑", bl_type="speed")

    def _on_btn_unblack_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要移出黑名单的节点！")
            return
        self.controller.remove_nodes_from_blacklist(nodes)

    def _on_btn_clear_bl_clicked(self):
        w = MessageBox("确认清空黑名单", "确定要清空所有延迟黑名单与低速黑名单记录吗？\n清空后所有被拉黑的节点将重新回到待测活跃池。", self)
        if w.exec():
            self.controller.clear_all_blacklists()

    def _on_btn_rescore_clicked(self):
        page = self.stackedWidget.currentWidget()
        if hasattr(page, "refresh_table"):
            page.refresh_table()
        elif hasattr(page, "refresh_data"):
            page.refresh_data()
        self.controller.log("📊 已重新计算综合评分与节点晋升状态！")

    def _on_btn_hotkey_sync_clicked(self):
        self.controller.trigger_verge_reload()

    # ==================== TopBar 顶部工具栏动作 ====================

    def _get_current_page_key(self) -> str:
        """
        获取当前激活页面的 key
        """
        curr = self.stackedWidget.currentWidget()
        if curr == self.page_favorites:
            return "favorites"
        elif curr == self.page_verified:
            return "verified"
        elif curr == self.page_stars:
            return "stars"
        elif curr == self.page_delay_black:
            return "delay_black"
        elif curr == self.page_speed_black:
            return "speed_black"
        elif curr == self.page_cloud_text:
            return "cloud_text"
        return "active"

    def _on_update_sub_clicked(self):
        curr_yaml = self.top_bar.sub_combo.currentText().strip()
        if not curr_yaml:
            self.controller.log("⚠️ 请先在下拉框选择要更新的订阅配置！")
            return
        self.controller.update_current_subscription(curr_yaml)

    def _on_test_page_colo_clicked(self):
        page_key = self._get_current_page_key()
        self.controller.test_current_page_colo(page_key)

    def _on_clear_page_colo_clicked(self):
        page_key = self._get_current_page_key()
        w = MessageBox(
            "确认清空机房记录",
            f"确定要清空当前标签页中所有节点的实时机房(Colo)与历史采样记录吗？\n\n"
            "• 该操作将清除最新 Colo 结果与 7 天滑动时序数据；\n"
            "• 归零后可点击【🌍 测当前页Colo】重新采集纯净数据。",
            self,
        )
        if w.exec():
            self.controller.clear_current_page_colo(page_key)

    def _on_sync_kernel_delay_clicked(self):
        self.controller.sync_kernel_delays()

    def _on_clear_speed_records_clicked(self):
        w = MessageBox(
            "清空确认",
            "确定要清空所有测速数据与延迟趋势记录吗？\n（不会清空您的黑名单及下行带宽历史）",
            self,
        )
        if w.exec():
            self.controller.clear_speed_records()

    # ==================== 后台定时调度与自愈降级 ====================

    def _get_scheduler_config(self) -> dict:
        """
        提供给 SchedulerDaemon 的动态定时参数字典
        """
        pc = self.pipeline_card
        pf = self.page_favorites
        return {
            "schedule_enabled": pc.chk_schedule.isChecked(),
            "schedule_times": pc.schedule_times.text().strip(),
            "schedule_interval": pc.schedule_interval.text().strip(),
            "fav_schedule_enabled": pf.chk_fav_schedule.isChecked(),
            "fav_schedule_interval": pf.fav_sched_interval.text().strip(),
        }

    def _on_scheduler_trigger_full(self, reason: str):
        self.controller.log(f"⏰ [定时调度] 触发全量大优选: {reason}")
        self._on_run_pipeline_clicked()

    def _on_scheduler_trigger_fav(self, reason: str):
        self.controller.log(f"⏰ [定时调度] 触发优质精选复检: {reason}")
        self.page_favorites._on_run_fav_clicked()

    def _on_fav_fallback_needed(self, reason: str):
        self.controller.log(f"⚡ 收到优质池自愈降级请求: {reason}，自动启动全量大优选...")
        self._on_run_pipeline_clicked()

    # ==================== 初始配置与历史回显 ====================

    def restore_ui_config(self, cfg: dict):
        """
        根据磁盘持久化配置恢复界面各项输入框、复选框与选中的订阅
        """
        if not cfg or not isinstance(cfg, dict):
            return

        pc = self.pipeline_card
        # 1. 恢复 PipelineCard 配置
        if "max_delay" in cfg:
            pc.max_delay.setText(str(cfg["max_delay"]))
        if "min_speed" in cfg:
            pc.min_speed.setText(str(cfg["min_speed"]))
        if "target_count" in cfg:
            pc.target_count.setText(str(cfg["target_count"]))
        if "test_rounds" in cfg:
            pc.test_rounds.setText(str(cfg["test_rounds"]))
        if "test_timeout" in cfg:
            pc.test_timeout.setText(str(cfg["test_timeout"]))
        if "speed_duration" in cfg:
            pc.speed_duration.setText(str(cfg["speed_duration"]))
        if "blacklist_threshold" in cfg:
            pc.blacklist_threshold.setText(str(cfg["blacklist_threshold"]))
        if "speed_bl_threshold" in cfg:
            pc.speed_bl_threshold.setText(str(cfg["speed_bl_threshold"]))
        if "speed_bl_rounds" in cfg:
            pc.speed_bl_rounds.setText(str(cfg["speed_bl_rounds"]))
        if "jitter_min_delay" in cfg:
            pc.jitter_min_delay.setText(str(cfg["jitter_min_delay"]))
        if "jitter_up_threshold" in cfg:
            pc.jitter_up_threshold.setText(str(cfg["jitter_up_threshold"]))
        if "test_url" in cfg:
            pc.test_url.setText(str(cfg["test_url"]))
        if "speed_url" in cfg:
            pc.speed_url.setText(str(cfg["speed_url"]))
        if "schedule_enabled" in cfg:
            pc.chk_schedule.setChecked(bool(cfg["schedule_enabled"]))
        if "schedule_interval" in cfg:
            pc.schedule_interval.setText(str(cfg["schedule_interval"]))
        if "schedule_times" in cfg:
            pc.schedule_times.setText(str(cfg["schedule_times"]))
        if "group_interval" in cfg:
            pc.group_interval.setText(str(cfg["group_interval"]))
        if "group_tolerance" in cfg:
            pc.group_tolerance.setText(str(cfg["group_tolerance"]))
        if "star_group_interval" in cfg:
            pc.star_group_interval.setText(str(cfg["star_group_interval"]))
        if "star_group_tolerance" in cfg:
            pc.star_group_tolerance.setText(str(cfg["star_group_tolerance"]))

        worker_url_val = cfg.get("worker_url") or cfg.get("cf_worker_url", "")
        if worker_url_val:
            pc.worker_url.setText(str(worker_url_val))
        worker_token_val = cfg.get("worker_token") or cfg.get("cf_worker_token", "")
        if worker_token_val:
            pc.worker_token.setText(str(worker_token_val))

        # 2. 恢复 PageFavorites 配置
        pf = self.page_favorites
        if "fav_max_delay" in cfg:
            pf.fav_max_delay.setText(str(cfg["fav_max_delay"]))
        if "fav_min_speed" in cfg:
            pf.fav_min_speed.setText(str(cfg["fav_min_speed"]))
        if "fav_rounds" in cfg:
            pf.fav_rounds.setText(str(cfg["fav_rounds"]))
        if "fav_speed_duration" in cfg:
            pf.fav_speed_duration.setText(str(cfg["fav_speed_duration"]))
        if "fav_jitter_min_delay" in cfg:
            pf.fav_jitter_min.setText(str(cfg["fav_jitter_min_delay"]))
        if "fav_jitter_up_threshold" in cfg:
            pf.fav_jitter_up.setText(str(cfg["fav_jitter_up_threshold"]))
        if "fav_schedule_enabled" in cfg:
            pf.chk_fav_schedule.setChecked(bool(cfg["fav_schedule_enabled"]))
        if "fav_schedule_interval" in cfg:
            pf.fav_sched_interval.setText(str(cfg["fav_schedule_interval"]))
        if "fav_target_hk_count" in cfg:
            pf.fav_target_hk.setText(str(cfg["fav_target_hk_count"]))
        if "fav_target_nohk_count" in cfg:
            pf.fav_target_nohk.setText(str(cfg["fav_target_nohk_count"]))
        if "fav_quota_early_stop" in cfg:
            pf.chk_fav_early_stop.setChecked(bool(cfg["fav_quota_early_stop"]))
        if "fav_fallback_enabled" in cfg:
            pf.chk_fav_fallback.setChecked(bool(cfg["fav_fallback_enabled"]))

        # 3. 恢复 PageVerified 配置
        pv = self.page_verified
        if "incubate_hours" in cfg:
            pv.incubate_hours.setText(str(cfg["incubate_hours"]))
        if "incubate_passes" in cfg:
            pv.incubate_passes.setText(str(cfg["incubate_passes"]))

        secret_val = cfg.get("clash_secret", "").strip() if cfg else ""
        if not secret_val:
            secret_val = "set-your-secret"
        pc.clash_secret.setText(secret_val)

        port_val = cfg.get("clash_port", "") if cfg else ""
        if not port_val:
            port_val = "9097"
        pc.clash_port.setText(str(port_val))

        # 4. 强制默认订阅选择并触发加载
        active_sub = "Rw0nNFlVIbnA.yaml"
        all_items = [self.top_bar.sub_combo.itemText(i) for i in range(self.top_bar.sub_combo.count())]
        if active_sub in all_items:
            self.top_bar.sub_combo.setCurrentText(active_sub)
            self.controller.load_nodes_from_profile(active_sub)
            self.controller.data_changed.emit()

        self._on_reconnect_clicked()

    def closeEvent(self, event):
        # 窗口关闭前强制存盘
        if hasattr(self, 'controller') and self.controller:
            self.controller.save_config(self.controller.state.get_snapshot())
            self.controller.log("💾 退出前已自动保存所有数据至 config...")
        super().closeEvent(event)

```

```python
File: gui_fluent/__init__.py
"""
Clash Verge 节点管理助手 - Fluent UI 组件库
"""

```

```python
File: gui_fluent/components/bottom_action_bar.py
"""
底部快捷操作栏组件
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QHBoxLayout
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QHBoxLayout

from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
)


class BottomActionBar(QWidget):
    """
    底部高频操作栏：提供节点晋升、拉黑、恢复与配置热刷新的快捷动作入口
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # 常用操作按钮
        self.btn_fav = PushButton("⭐ 设为优质", self)
        layout.addWidget(self.btn_fav)

        self.btn_promote = PushButton("🏆 晋升为典藏", self)
        layout.addWidget(self.btn_promote)

        self.btn_delay_black = PushButton("🚫 延迟拉黑", self)
        layout.addWidget(self.btn_delay_black)

        self.btn_speed_black = PushButton("🐌 低速拉黑", self)
        layout.addWidget(self.btn_speed_black)

        self.btn_unblack = PushButton("↩ 移出黑名单", self)
        layout.addWidget(self.btn_unblack)

        self.btn_clear_bl = PushButton("🧹 一键清空所有黑名单", self)
        layout.addWidget(self.btn_clear_bl)

        self.btn_rescore = PushButton("🏆 重新计分与晋升", self)
        layout.addWidget(self.btn_rescore)

        # 弹性空白隔断
        layout.addStretch(1)

        # 右侧重点操作按钮
        self.btn_hotkey_sync = PrimaryPushButton("⚡ 手动写入并热键刷新 Verge", self)
        layout.addWidget(self.btn_hotkey_sync)

        self.setStyleSheet("""
            BottomActionBar {
                background-color: rgba(30, 41, 59, 0.45);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)

```

```python
File: gui_fluent/components/log_panel.py
"""
实时日志面板组件
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
else:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    BodyLabel,
    PlainTextEdit,
    PushButton,
)


class LogPanel(QWidget):
    """
    底部日志监控面板：支持线程安全追加日志文本与一键清屏
    """
    _append_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self._append_signal.connect(self._do_append_log)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(4)

        # 顶部工具条：标题 + 右对齐清屏按钮
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_title = BodyLabel("📜 操作动态与实时运行日志:", self)
        self.lbl_title.setStyleSheet("font-weight: bold; color: #38bdf8;")
        top_layout.addWidget(self.lbl_title)

        top_layout.addStretch(1)

        self.btn_clear = PushButton("清屏", self)
        self.btn_clear.setFixedWidth(64)
        self.btn_clear.clicked.connect(self.clear_log)
        top_layout.addWidget(self.btn_clear)
        layout.addLayout(top_layout)

        # 主体文本区域
        self.text_edit = PlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        font = QFont("Consolas", 9)
        self.text_edit.setFont(font)
        self.text_edit.setStyleSheet("""
            PlainTextEdit {
                background-color: #0f111a;
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.text_edit)

        self.setStyleSheet("""
            LogPanel {
                background-color: rgba(30, 41, 59, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
            }
        """)

    def append_log(self, text: str):
        """
        公开方法：线程安全追加日志
        """
        self._append_signal.emit(str(text))

    def _do_append_log(self, text: str):
        self.text_edit.appendPlainText(text)
        bar = self.text_edit.verticalScrollBar()
        if bar:
            bar.setValue(bar.maximum())

    def clear_log(self):
        self.text_edit.clear()

```

```python
File: gui_fluent/components/pipeline_card.py
"""
流水线控制卡组件 (PipelineCard)
集中配置全自动优选门槛、拉黑规则、测速源、定时调度与内核连接参数
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit
    PASSWORD_ECHO_MODE = QLineEdit.Password
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit
    PASSWORD_ECHO_MODE = QLineEdit.EchoMode.Password

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CheckBox,
    LineEdit,
    PushButton,
    PrimaryPushButton,
)


class PipelineCard(QWidget):
    """
    流水线控制卡：提供 5 行紧凑参数配置与操作控制
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("PipelineCard")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ──────── 第 1 行：全局优选门槛 ────────
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(8)

        lbl_r1 = BodyLabel("⚡ 全局优选门槛:", self)
        lbl_r1.setStyleSheet("color: #38bdf8; font-weight: bold;")
        row1.addWidget(lbl_r1)

        row1.addWidget(CaptionLabel("最低延迟(≤ ms):", self))
        self.max_delay = LineEdit(self)
        self.max_delay.setObjectName("max_delay")
        self.max_delay.setText("100")
        self.max_delay.setFixedWidth(55)
        self.max_delay.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.max_delay)

        row1.addWidget(CaptionLabel("优质下行(≥ MB/s):", self))
        self.min_speed = LineEdit(self)
        self.min_speed.setObjectName("min_speed")
        self.min_speed.setText("5.0")
        self.min_speed.setFixedWidth(50)
        self.min_speed.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.min_speed)

        lbl_target = CaptionLabel("达标目标(留空全测):", self)
        lbl_target.setStyleSheet("color: #fbbf24;")
        row1.addWidget(lbl_target)

        self.target_count = LineEdit(self)
        self.target_count.setObjectName("target_count")
        self.target_count.setText("")
        self.target_count.setFixedWidth(45)
        self.target_count.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.target_count)

        row1.addWidget(CaptionLabel("轮数:", self))
        self.test_rounds = LineEdit(self)
        self.test_rounds.setObjectName("test_rounds")
        self.test_rounds.setText("4")
        self.test_rounds.setFixedWidth(36)
        self.test_rounds.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.test_rounds)

        row1.addWidget(CaptionLabel("超时(ms):", self))
        self.test_timeout = LineEdit(self)
        self.test_timeout.setObjectName("test_timeout")
        self.test_timeout.setText("1500")
        self.test_timeout.setFixedWidth(50)
        self.test_timeout.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.test_timeout)

        row1.addWidget(CaptionLabel("采样:", self))
        self.speed_duration = LineEdit(self)
        self.speed_duration.setObjectName("speed_duration")
        self.speed_duration.setText("3")
        self.speed_duration.setFixedWidth(36)
        self.speed_duration.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.speed_duration)
        row1.addWidget(CaptionLabel("秒", self))

        self.btn_run_pipeline = PrimaryPushButton("🚀 启动一整套全自动优选与热键生效", self)
        self.btn_run_pipeline.setObjectName("btn_run_pipeline")
        self.btn_run_pipeline.setStyleSheet("""
            PrimaryPushButton {
                background-color: #10b981;
                border: 1px solid #10b981;
            }
            PrimaryPushButton:hover {
                background-color: #059669;
                border: 1px solid #059669;
            }
            PrimaryPushButton:pressed {
                background-color: #047857;
                border: 1px solid #047857;
            }
        """)
        row1.addWidget(self.btn_run_pipeline)

        self.btn_stop_pipeline = PushButton("⏹ 终止任务", self)
        self.btn_stop_pipeline.setObjectName("btn_stop_pipeline")
        self.btn_stop_pipeline.setEnabled(False)
        row1.addWidget(self.btn_stop_pipeline)

        layout.addLayout(row1)

        # ──────── 第 2 行：自动拉黑规则 ────────
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(8)

        lbl_r2 = BodyLabel("🚫 自动拉黑规则:", self)
        lbl_r2.setStyleSheet("color: #f87171; font-weight: bold;")
        row2.addWidget(lbl_r2)

        row2.addWidget(CaptionLabel("延迟拉黑(≥ ms):", self))
        self.blacklist_threshold = LineEdit(self)
        self.blacklist_threshold.setObjectName("blacklist_threshold")
        self.blacklist_threshold.setText("130")
        self.blacklist_threshold.setFixedWidth(55)
        self.blacklist_threshold.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.blacklist_threshold)

        row2.addWidget(CaptionLabel("低速拉黑(< MB/s):", self))
        self.speed_bl_threshold = LineEdit(self)
        self.speed_bl_threshold.setObjectName("speed_bl_threshold")
        self.speed_bl_threshold.setText("1.0")
        self.speed_bl_threshold.setFixedWidth(50)
        self.speed_bl_threshold.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.speed_bl_threshold)

        row2.addWidget(CaptionLabel("连续低速次数:", self))
        self.speed_bl_rounds = LineEdit(self)
        self.speed_bl_rounds.setObjectName("speed_bl_rounds")
        self.speed_bl_rounds.setText("4")
        self.speed_bl_rounds.setFixedWidth(36)
        self.speed_bl_rounds.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.speed_bl_rounds)
        row2.addWidget(CaptionLabel("次", self))

        row2.addWidget(CaptionLabel("抖动基准(≥ ms):", self))
        self.jitter_min_delay = LineEdit(self)
        self.jitter_min_delay.setObjectName("jitter_min_delay")
        self.jitter_min_delay.setText("80")
        self.jitter_min_delay.setFixedWidth(45)
        self.jitter_min_delay.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.jitter_min_delay)

        row2.addWidget(CaptionLabel("向上抖动(≥ ms):", self))
        self.jitter_up_threshold = LineEdit(self)
        self.jitter_up_threshold.setObjectName("jitter_up_threshold")
        self.jitter_up_threshold.setText("20")
        self.jitter_up_threshold.setFixedWidth(45)
        self.jitter_up_threshold.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.jitter_up_threshold)

        row2.addStretch(1)
        layout.addLayout(row2)

        # ──────── 第 3 行：测速 URL 与策略组配置 ────────
        row3 = QHBoxLayout()
        row3.setContentsMargins(0, 0, 0, 0)
        row3.setSpacing(8)

        lbl_test_url = CaptionLabel("延迟源:", self)
        lbl_test_url.setStyleSheet("color: #8d98af;")
        row3.addWidget(lbl_test_url)

        self.test_url = LineEdit(self)
        self.test_url.setObjectName("test_url")
        self.test_url.setText("http://www.msftconnecttest.com/connecttest.txt")
        self.test_url.setFixedWidth(220)
        row3.addWidget(self.test_url)

        lbl_speed_url = CaptionLabel("带宽源:", self)
        lbl_speed_url.setStyleSheet("color: #8d98af;")
        row3.addWidget(lbl_speed_url)

        self.speed_url = LineEdit(self)
        self.speed_url.setObjectName("speed_url")
        self.speed_url.setText("https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip")
        self.speed_url.setFixedWidth(220)
        row3.addWidget(self.speed_url)

        row3.addStretch(1)
        layout.addLayout(row3)

        # ──────── 第 4 行：定时调度 + 策略组间隔 ────────
        row4 = QHBoxLayout()
        row4.setContentsMargins(0, 0, 0, 0)
        row4.setSpacing(8)

        self.chk_schedule = CheckBox("⏰ 启用全局定时优选", self)
        self.chk_schedule.setObjectName("chk_schedule")
        row4.addWidget(self.chk_schedule)

        row4.addWidget(CaptionLabel("循环间隔(分钟):", self))
        self.schedule_interval = LineEdit(self)
        self.schedule_interval.setObjectName("schedule_interval")
        self.schedule_interval.setText("120")
        self.schedule_interval.setFixedWidth(45)
        self.schedule_interval.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.schedule_interval)

        row4.addWidget(CaptionLabel("固定时刻(HH:MM):", self))
        self.schedule_times = LineEdit(self)
        self.schedule_times.setObjectName("schedule_times")
        self.schedule_times.setText("08:00, 13:00, 20:00")
        self.schedule_times.setFixedWidth(140)
        self.schedule_times.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.schedule_times)

        self.lbl_sched_status = CaptionLabel("(全局定时未启动)", self)
        self.lbl_sched_status.setObjectName("lbl_sched_status")
        self.lbl_sched_status.setStyleSheet("color: #94a3b8;")
        row4.addWidget(self.lbl_sched_status)

        row4.addStretch(1)

        lbl_grp = BodyLabel("⚙️ 策略组:", self)
        lbl_grp.setStyleSheet("color: #a78bfa; font-weight: bold;")
        row4.addWidget(lbl_grp)

        row4.addWidget(CaptionLabel("常规间隔(s):", self))
        self.group_interval = LineEdit(self)
        self.group_interval.setObjectName("group_interval")
        self.group_interval.setText("300")
        self.group_interval.setFixedWidth(45)
        self.group_interval.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.group_interval)

        row4.addWidget(CaptionLabel("容差(ms):", self))
        self.group_tolerance = LineEdit(self)
        self.group_tolerance.setObjectName("group_tolerance")
        self.group_tolerance.setText("20")
        self.group_tolerance.setFixedWidth(36)
        self.group_tolerance.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.group_tolerance)

        row4.addWidget(CaptionLabel("典藏间隔(s):", self))
        self.star_group_interval = LineEdit(self)
        self.star_group_interval.setObjectName("star_group_interval")
        self.star_group_interval.setText("300")
        self.star_group_interval.setFixedWidth(45)
        self.star_group_interval.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.star_group_interval)

        row4.addWidget(CaptionLabel("容差(ms):", self))
        self.star_group_tolerance = LineEdit(self)
        self.star_group_tolerance.setObjectName("star_group_tolerance")
        self.star_group_tolerance.setText("20")
        self.star_group_tolerance.setFixedWidth(36)
        self.star_group_tolerance.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.star_group_tolerance)

        self.btn_save_group = PushButton("💾 保存并热更", self)
        self.btn_save_group.setObjectName("btn_save_group")
        row4.addWidget(self.btn_save_group)

        layout.addLayout(row4)

        # ──────── 第 5 行：Worker 云端同步 + Clash 连接参数 ────────
        row5 = QHBoxLayout()
        row5.setContentsMargins(0, 0, 0, 0)
        row5.setSpacing(8)

        self.chk_worker_enabled = CheckBox("☁️ 自动推送 Worker", self)
        self.chk_worker_enabled.setObjectName("chk_worker_enabled")
        row5.addWidget(self.chk_worker_enabled)

        row5.addWidget(CaptionLabel("根地址:", self))
        self.worker_url = LineEdit(self)
        self.worker_url.setObjectName("worker_url")
        self.worker_url.setText("https://cf-nodes.douyutvshow.workers.dev/")
        self.worker_url.setFixedWidth(200)
        row5.addWidget(self.worker_url)

        row5.addWidget(CaptionLabel("密钥:", self))
        self.worker_token = LineEdit(self)
        self.worker_token.setObjectName("worker_token")
        self.worker_token.setText("MySecretToken2026")
        self.worker_token.setFixedWidth(120)
        self.worker_token.setEchoMode(PASSWORD_ECHO_MODE)
        row5.addWidget(self.worker_token)

        self.btn_test_worker = PushButton("🧪 测试通道", self)
        self.btn_test_worker.setObjectName("btn_test_worker")
        row5.addWidget(self.btn_test_worker)

        self.btn_sync_auto = PushButton("☁️ 同步auto.txt", self)
        self.btn_sync_auto.setObjectName("btn_sync_auto")
        row5.addWidget(self.btn_sync_auto)

        row5.addStretch(1)

        row5.addWidget(CaptionLabel("端口:", self))
        self.clash_port = LineEdit(self)
        self.clash_port.setObjectName("clash_port")
        self.clash_port.setText("9097")
        self.clash_port.setFixedWidth(55)
        self.clash_port.setAlignment(Qt.AlignCenter)
        row5.addWidget(self.clash_port)

        row5.addWidget(CaptionLabel("密钥:", self))
        self.clash_secret = LineEdit(self)
        self.clash_secret.setObjectName("clash_secret")
        self.clash_secret.setText("")
        self.clash_secret.setFixedWidth(100)
        row5.addWidget(self.clash_secret)

        self.btn_reconnect = PushButton("重连", self)
        self.btn_reconnect.setObjectName("btn_reconnect")
        row5.addWidget(self.btn_reconnect)

        row5.addWidget(CaptionLabel("快速过滤:", self))
        self.search_box = LineEdit(self)
        self.search_box.setObjectName("search_box")
        self.search_box.setText("")
        self.search_box.setFixedWidth(130)
        row5.addWidget(self.search_box)

        self.lbl_conn_status = CaptionLabel("● 未连接", self)
        self.lbl_conn_status.setObjectName("lbl_conn_status")
        self.lbl_conn_status.setStyleSheet("color: #fbbf24; font-weight: bold;")
        row5.addWidget(self.lbl_conn_status)

        layout.addLayout(row5)

        self.setStyleSheet("""
            PipelineCard {
                background-color: rgba(30, 34, 50, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)

```

```python
File: gui_fluent/components/top_bar.py
"""
顶部信息栏与快捷工具组组件
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QHBoxLayout
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QHBoxLayout

from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    PushButton,
    CaptionLabel,
)


class TopBar(QWidget):
    """
    顶部信息栏：包含当前订阅选择、内核连接状态、上次更新时间及右侧快捷操作工具组
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # 1. 订阅选择下拉框 (本阶段空列表占位)
        self.sub_combo = ComboBox(self)
        self.sub_combo.setPlaceholderText("选择或加载订阅配置文件...")
        self.sub_combo.setMinimumWidth(220)
        layout.addWidget(self.sub_combo)

        # 2. 更新当前订阅按钮
        self.btn_update_sub = PushButton("🔄 更新当前订阅", self)
        layout.addWidget(self.btn_update_sub)

        # 3. 内核连接状态标签 (文字："● 正在连接内核..."，颜色 #fbbf24)
        self.lbl_status = BodyLabel("● 正在连接内核...", self)
        self.lbl_status.setStyleSheet("color: #fbbf24; font-weight: bold;")
        layout.addWidget(self.lbl_status)

        # 4. 上次检测时间标签
        self.lbl_last_check = CaptionLabel("上次检测: 未执行", self)
        self.lbl_last_check.setStyleSheet("color: #94a3b8;")
        layout.addWidget(self.lbl_last_check)

        # 弹性空白隔断
        layout.addStretch(1)

        # 5. 右侧工具按钮组
        self.btn_test_page_colo = PushButton("🌍 测当前页Colo", self)
        layout.addWidget(self.btn_test_page_colo)

        self.btn_sync_kernel_delay = PushButton("🔄 同步内核延迟", self)
        layout.addWidget(self.btn_sync_kernel_delay)

        self.btn_clear_page_colo = PushButton("🧹 清当前页Colo", self)
        layout.addWidget(self.btn_clear_page_colo)

        self.btn_clear_speed_records = PushButton("🗑️ 清空测速记录", self)
        layout.addWidget(self.btn_clear_speed_records)

        self.setStyleSheet("""
            TopBar {
                background-color: rgba(30, 41, 59, 0.45);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)

```

```python
File: gui_fluent/components/__init__.py
"""
Fluent UI 通用界面组件模块
"""
from gui_fluent.components.top_bar import TopBar
from gui_fluent.components.log_panel import LogPanel
from gui_fluent.components.bottom_action_bar import BottomActionBar
from gui_fluent.components.pipeline_card import PipelineCard

__all__ = ["TopBar", "LogPanel", "BottomActionBar", "PipelineCard"]


```

```python
File: gui_fluent/pages/page_active.py
"""
活跃待测页面
完整表格视图，展示聚合去重后的独立端点活跃待测节点
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout
else:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout

from gui_fluent.app_controller import AppController
from gui_fluent.widgets.node_table import NodeTableView


class PageActive(QWidget):
    """
    活跃待测页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageActive")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 核心通用节点表格
        self.table = NodeTableView(self, controller=self.controller, page_type="active")
        layout.addWidget(self.table, 1)

        # 绑定中枢控制器的流水线数据实时更新信号
        self.controller.pipeline_rows_updated.connect(self.table.populate)

        # 绑定全局数据变化信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)
        self.refresh_data()

    def refresh_data(self):
        """
        重新装配活跃待测池数据并刷新表格
        """
        rows = self.controller.get_table_rows("active")
        self.table.populate(rows)



```

```python
File: gui_fluent/pages/page_cloud_text.py
"""
云端文本管理页面 (PageCloudText)
管理 Cloudflare Worker 远端分发的三大核心文本（/auto.txt、/verified.txt、/）
支持独立及批量拉取、在线编辑、格式统计与强推覆盖。
"""
import sys
import time
import threading
import re

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QFrame,
    )
else:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QFrame,
    )

from qfluentwidgets import (
    TitleLabel,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    PushButton,
    PrimaryPushButton,
    SimpleCardWidget,
    PlainTextEdit,
    MessageBox,
    InfoBar,
    InfoBarPosition,
)
from gui_fluent.app_controller import AppController


class CloudTextCard(SimpleCardWidget):
    """
    单个云端分发文本管理卡片
    """
    fetch_requested = pyqtSignal(str)          # subpath
    push_requested = pyqtSignal(str, str)      # (subpath, text)

    def __init__(self, title: str, subpath: str, desc: str = "", parent=None):
        super().__init__(parent)
        self.subpath = subpath
        self.title_text = title
        self.desc_text = desc
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 1. 顶部标题栏与独立操作按钮
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.title_label = SubtitleLabel(self.title_text, self)
        top_bar.addWidget(self.title_label)
        top_bar.addStretch(1)

        self.btn_fetch = PushButton("📥 拉取", self)
        self.btn_fetch.setToolTip(f"从云端拉取最新的 {self.subpath} 内容")
        self.btn_fetch.clicked.connect(lambda: self.fetch_requested.emit(self.subpath))
        top_bar.addWidget(self.btn_fetch)

        if self.subpath == "/pending.txt":
            self.btn_purge = PushButton("🧹 联动清洗", self)
            self.btn_purge.setToolTip("立即比对黑名单与精选池，从云端待测池中清除所有已淘汰或已入选的节点")
            top_bar.addWidget(self.btn_purge)

        self.btn_push = PrimaryPushButton("📤 强推", self)
        self.btn_push.setToolTip(f"将当前编辑的内容强推覆盖至云端 {self.subpath}")
        self.btn_push.clicked.connect(lambda: self.push_requested.emit(self.subpath, self.get_text()))
        top_bar.addWidget(self.btn_push)

        layout.addLayout(top_bar)

        # 2. 功能说明标签
        if self.desc_text:
            self.desc_label = CaptionLabel(self.desc_text, self)
            self.desc_label.setStyleSheet("color: #94a3b8;")
            layout.addWidget(self.desc_label)

        # 3. 核心大文本编辑器
        self.editor = PlainTextEdit(self)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        self.editor.setPlaceholderText(
            f"IP:Port#备注名\n示例：\n1.1.1.1:443#优质香港 12.5MB/s\n8.8.8.8:443#备选日本 8.2MB/s"
        )
        # 兼容 PyQt5 / PyQt6 的 NoWrap 设置
        if hasattr(PlainTextEdit, "LineWrapMode"):
            self.editor.setLineWrapMode(PlainTextEdit.LineWrapMode.NoWrap)
        elif hasattr(PlainTextEdit, "NoWrap"):
            self.editor.setLineWrapMode(PlainTextEdit.NoWrap)

        self.editor.textChanged.connect(self._update_stats)
        layout.addWidget(self.editor, 1)

        # 4. 底部统计与状态栏
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 0, 0, 0)
        self.lbl_stats = CaptionLabel("共 0 行 | 0 字符", self)
        self.lbl_stats.setStyleSheet("color: #94a3b8;")
        bottom_bar.addWidget(self.lbl_stats)

        bottom_bar.addStretch(1)

        self.lbl_status = CaptionLabel("就绪", self)
        self.lbl_status.setStyleSheet("color: #64748b;")
        bottom_bar.addWidget(self.lbl_status)

        layout.addLayout(bottom_bar)

    def set_text(self, text: str):
        """更新文本内容"""
        self.editor.setPlainText(text or "")
        self._update_stats()

    def get_text(self) -> str:
        """获取当前编辑器文本"""
        return self.editor.toPlainText()

    def set_status(self, status: str, is_error: bool = False):
        """更新状态词"""
        self.lbl_status.setText(status)
        if is_error:
            self.lbl_status.setStyleSheet("color: #ef4444;")
        else:
            self.lbl_status.setStyleSheet("color: #10b981;")

    def set_loading(self, is_loading: bool):
        """切换加载状态"""
        self.btn_fetch.setEnabled(not is_loading)
        self.btn_push.setEnabled(not is_loading)
        if is_loading:
            self.btn_fetch.setText("⏳ 同步中...")
        else:
            self.btn_fetch.setText("📥 拉取")

    def _update_stats(self):
        """实时统计行数与字符数"""
        text = self.editor.toPlainText()
        non_empty_lines = [l for l in text.splitlines() if l.strip()]
        self.lbl_stats.setText(f"共 {len(non_empty_lines)} 行 | {len(text)} 字符")



class PageCloudText(QWidget):
    """
    云端文本页面：管理向远端 Cloudflare Worker 自动推送/拉取的三个核心分发文本
    （/auto.txt、/verified.txt、/）
    """
    fetch_done_signal = pyqtSignal(str, bool, str)   # (subpath, success, content_or_err)
    push_done_signal = pyqtSignal(str, bool, str)    # (subpath, success, message)

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageCloudText")
        self.cards = {}
        self._initial_loaded = False

        self.init_ui()
        self._connect_signals()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. 顶部 Header 区域
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self.title_label = TitleLabel("☁️ 云端文本管理", self)
        title_box.addWidget(self.title_label)

        self.desc_label = BodyLabel(
            "查看与编辑 Cloudflare Worker 远端分发的三大核心文本（优质精选 /auto.txt、沉淀孵化 /verified.txt、典藏常青 /）。支持在线双向同步与手动强推覆盖。",
            self,
        )
        self.desc_label.setStyleSheet("color: #94a3b8;")
        title_box.addWidget(self.desc_label)
        header_layout.addLayout(title_box, 1)

        # 全局操作按钮组
        self.btn_fetch_all = PushButton("📥 一键拉取所有", self)
        self.btn_fetch_all.clicked.connect(self._on_fetch_all_clicked)
        header_layout.addWidget(self.btn_fetch_all)

        self.btn_push_all = PrimaryPushButton("📤 一键强推所有", self)
        self.btn_push_all.clicked.connect(self._on_push_all_clicked)
        header_layout.addWidget(self.btn_push_all)

        main_layout.addLayout(header_layout)

        # 2. 三列分栏卡片布局
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(14)

        # 卡片 1: /auto.txt (优质精选)
        card_auto = CloudTextCard(
            title="⭐ 优质精选池 (/auto.txt)",
            subpath="/auto.txt",
            desc="大优选产出的优质精选节点，直接下发自适应策略组",
            parent=self,
        )
        self.cards["/auto.txt"] = card_auto
        columns_layout.addWidget(card_auto, 1)

        # 卡片 2: /verified.txt (沉淀孵化)
        card_ver = CloudTextCard(
            title="⏳ 沉淀孵化池 (/verified.txt)",
            subpath="/verified.txt",
            desc="连续多轮测速达标的稳定节点，处于孵化培育状态",
            parent=self,
        )
        self.cards["/verified.txt"] = card_ver
        columns_layout.addWidget(card_ver, 1)

        # 卡片 3: / (典藏常青)
        card_root = CloudTextCard(
            title="🏆 典藏常青池 (/)",
            subpath="/",
            desc="高频考核历练出的极品常青树节点，顶级优先级直通",
            parent=self,
        )
        self.cards["/"] = card_root
        columns_layout.addWidget(card_root, 1)

        # 卡片 4: /pending.txt (待测归收池)
        card_pending = CloudTextCard(
            title="⚪ 待测归收池 (/pending.txt)",
            subpath="/pending.txt",
            desc="存放 C 段挖掘与移出黑名单节点，全量大优选启动时自动读取重新纳测",
            parent=self,
        )
        self.cards["/pending.txt"] = card_pending
        columns_layout.addWidget(card_pending, 1)

        main_layout.addLayout(columns_layout, 1)

    def _connect_signals(self):
        """绑定内部信号"""
        for subpath, card in self.cards.items():
            card.fetch_requested.connect(self._handle_card_fetch)
            card.push_requested.connect(self._handle_card_push)
            if hasattr(card, "btn_purge"):
                card.btn_purge.clicked.connect(self._on_manual_purge_clicked)

        self.fetch_done_signal.connect(self._on_fetch_done)
        self.push_done_signal.connect(self._on_push_done)

    def showEvent(self, event):
        """初次切入页面时自动静默拉取三大文本"""
        super().showEvent(event)
        if not self._initial_loaded:
            self._initial_loaded = True
            self._on_fetch_all_clicked(silent=True)

    # ==================== 单卡片操作 ====================

    def _handle_card_fetch(self, subpath: str):
        """单卡片拉取请求"""
        card = self.cards.get(subpath)
        if card:
            card.set_loading(True)
            card.set_status("正在从云端拉取...")

        def _worker():
            ok, content = self.controller.fetch_cloud_text(subpath=subpath)
            self.fetch_done_signal.emit(subpath, ok, content)

        threading.Thread(target=_worker, daemon=True).start()

    def _handle_card_push(self, subpath: str, text: str):
        """单卡片强推请求"""
        card = self.cards.get(subpath)
        title = card.title_text if card else subpath

        # 强推前二次确认
        w = MessageBox(
            "确认强推覆盖云端",
            f"确定要将当前编辑的内容强推覆盖至云端 {subpath} 吗？\n\n"
            f"⚠️ 目标模块：{title}\n"
            "该操作将立即直接覆盖远端 Cloudflare Worker 文本存储，不可撤销！",
            self.window(),
        )
        if not w.exec():
            return

        if card:
            card.set_loading(True)
            card.set_status("正在强推至云端...")

        def _worker():
            ok, msg = self.controller.push_cloud_text(subpath=subpath, text=text)
            self.push_done_signal.emit(subpath, ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    # ==================== 批量全局操作 ====================

    def _on_fetch_all_clicked(self, silent: bool = False):
        """一键拉取全部"""
        if not silent:
            InfoBar.info("正在拉取", "正在向 Cloudflare Worker 并发拉取三大分发文本...", duration=2000, parent=self.window())
        for subpath in self.cards:
            self._handle_card_fetch(subpath)

    def _on_push_all_clicked(self):
        """一键强推全部"""
        w = MessageBox(
            "确认批量强推全部云端文本",
            "确定要将当前编辑的全部 3 个文本（/auto.txt、/verified.txt、/）强推覆盖至云端吗？\n\n"
            "⚠️ 该操作将同时重写远端 Cloudflare Worker 全部数据，不可撤销！",
            self.window(),
        )
        if not w.exec():
            return

        InfoBar.info("正在强推", "正在向 Cloudflare Worker 批量推送三大分发文本...", duration=2000, parent=self.window())
        for subpath, card in self.cards.items():
            card.set_loading(True)
            card.set_status("正在强推至云端...")
            text = card.get_text()

            def _worker(sp=subpath, t=text):
                ok, msg = self.controller.push_cloud_text(subpath=sp, text=t)
                self.push_done_signal.emit(sp, ok, msg)

            threading.Thread(target=_worker, daemon=True).start()

    # ==================== 信号回调处理 ====================

    def _on_fetch_done(self, subpath: str, ok: bool, content: str):
        """拉取完成回调"""
        card = self.cards.get(subpath)
        if not card:
            return
        card.set_loading(False)
        if ok:
            card.set_text(content)
            card.set_status(f"拉取成功 ({time.strftime('%H:%M:%S')})", is_error=False)
            InfoBar.success("拉取成功", f"已成功拉取并更新 {subpath}", duration=2500, parent=self.window())
        else:
            card.set_status("拉取失败", is_error=True)
            InfoBar.error("拉取失败", f"{subpath}: {content}", duration=4000, parent=self.window())

    def _on_push_done(self, subpath: str, ok: bool, msg: str):
        """强推完成回调"""
        card = self.cards.get(subpath)
        if not card:
            return
        card.set_loading(False)
        if ok:
            card.set_status(f"强推成功 ({time.strftime('%H:%M:%S')})", is_error=False)
            InfoBar.success("强推成功", f"{subpath} 文本已成功写入远端 Worker！", duration=3000, parent=self.window())
        else:
            card.set_status("强推失败", is_error=True)
            InfoBar.error("强推失败", f"{subpath}: {msg}", duration=4500, parent=self.window())

    def _on_manual_purge_clicked(self):
        """用户在待测卡片上手动点击【🧹 联动清洗】的一键自愈操作"""
        card = self.cards.get("/pending.txt")
        if card:
            card.set_loading(True)
            card.set_status("正在比对全池清洗云端待测池...")

        def _worker():
            purged = self.controller.purge_pending_endpoints_from_cloud()
            time.sleep(0.5)
            # 清洗后自动重拉最新内容刷新编辑器
            ok, content = self.controller.fetch_cloud_text("/pending.txt")
            self.fetch_done_signal.emit("/pending.txt", ok, content)

        import threading
        threading.Thread(target=_worker, daemon=True).start()



```

```python
File: gui_fluent/pages/page_delay_black.py
"""
延迟黑名单页面
展示因超时、高延迟、向上抖动剧烈或机房跨洲漂移被淘汰的节点与端点
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout
else:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout

from gui_fluent.app_controller import AppController
from gui_fluent.widgets.node_table import NodeTableView


class PageDelayBlack(QWidget):
    """
    延迟黑名单页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageDelayBlack")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 核心通用节点表格
        self.table = NodeTableView(self, controller=self.controller, page_type="delay_black")
        layout.addWidget(self.table, 1)

        # 绑定数据变更信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)
        self.refresh_data()

    def refresh_data(self):
        """
        重新装配延迟黑名单数据并刷新表格
        """
        rows = self.controller.get_table_rows("delay_black")
        self.table.populate(rows)


```

```python
File: gui_fluent/pages/page_favorites.py
"""
优质精选页面
包含两行精选参数控制与操作工具栏 (FavToolBar) 以及核心节点表格 (NodeTableView)
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CheckBox,
    LineEdit,
    PushButton,
    PrimaryPushButton,
)
from gui_fluent.app_controller import AppController
from gui_fluent.widgets.node_table import NodeTableView


class FavToolBar(QWidget):
    """
    优质精选工具栏 (包含两行控制项)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(6)

        # 第一行：测速指标门槛与控制按钮
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(6)

        row1.addWidget(BodyLabel("精选标准 延迟<", self))
        self.fav_max_delay = LineEdit(self)
        self.fav_max_delay.setText("80")
        self.fav_max_delay.setFixedWidth(40)
        self.fav_max_delay.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_max_delay)
        row1.addWidget(BodyLabel("ms", self))

        row1.addWidget(BodyLabel("测速>", self))
        self.fav_min_speed = LineEdit(self)
        self.fav_min_speed.setText("8.0")
        self.fav_min_speed.setFixedWidth(40)
        self.fav_min_speed.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_min_speed)
        row1.addWidget(BodyLabel("MB/s", self))

        row1.addWidget(BodyLabel("轮数", self))
        self.fav_rounds = LineEdit(self)
        self.fav_rounds.setText("2")
        self.fav_rounds.setFixedWidth(30)
        self.fav_rounds.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_rounds)

        row1.addWidget(BodyLabel("时长", self))
        self.fav_speed_duration = LineEdit(self)
        self.fav_speed_duration.setText("2")
        self.fav_speed_duration.setFixedWidth(30)
        self.fav_speed_duration.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_speed_duration)
        row1.addWidget(BodyLabel("s", self))

        row1.addWidget(BodyLabel("抖动基线<", self))
        self.fav_jitter_min = LineEdit(self)
        self.fav_jitter_min.setText("70")
        self.fav_jitter_min.setFixedWidth(35)
        self.fav_jitter_min.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_jitter_min)
        row1.addWidget(BodyLabel("ms", self))

        row1.addWidget(BodyLabel("抬升<", self))
        self.fav_jitter_up = LineEdit(self)
        self.fav_jitter_up.setText("15")
        self.fav_jitter_up.setFixedWidth(30)
        self.fav_jitter_up.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_jitter_up)
        row1.addWidget(BodyLabel("ms", self))

        self.btn_fav_run = PrimaryPushButton("▶ 启动精选全自动测速", self)
        row1.addWidget(self.btn_fav_run)

        row1.addStretch(1)

        self.btn_fav_reload_history = PushButton("重载历史", self)
        row1.addWidget(self.btn_fav_reload_history)

        self.btn_fav_clean_stale = PushButton("清理过期", self)
        row1.addWidget(self.btn_fav_clean_stale)

        self.btn_fav_clear_all = PushButton("清空精选", self)
        row1.addWidget(self.btn_fav_clear_all)

        self.btn_fav_sync_now = PushButton("⚡ 立即同步到活跃池", self)
        row1.addWidget(self.btn_fav_sync_now)

        main_layout.addLayout(row1)

        # 第二行：定时与达标即停配置
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(6)

        self.chk_fav_schedule = CheckBox("定时运行精选 (分):", self)
        row2.addWidget(self.chk_fav_schedule)

        self.fav_sched_interval = LineEdit(self)
        self.fav_sched_interval.setText("60")
        self.fav_sched_interval.setFixedWidth(45)
        self.fav_sched_interval.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.fav_sched_interval)

        self.chk_fav_early_stop = CheckBox("达标即停 (HK:", self)
        self.chk_fav_early_stop.setChecked(True)
        row2.addWidget(self.chk_fav_early_stop)

        self.fav_target_hk = LineEdit(self)
        self.fav_target_hk.setText("3")
        self.fav_target_hk.setFixedWidth(30)
        self.fav_target_hk.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.fav_target_hk)

        row2.addWidget(BodyLabel("非HK:", self))

        self.fav_target_nohk = LineEdit(self)
        self.fav_target_nohk.setText("5")
        self.fav_target_nohk.setFixedWidth(30)
        self.fav_target_nohk.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.fav_target_nohk)

        row2.addWidget(BodyLabel(")", self))

        self.chk_fav_fallback = CheckBox("HK不足降级", self)
        row2.addWidget(self.chk_fav_fallback)

        self.lbl_fav_sched_status = CaptionLabel("状态: 未运行", self)
        self.lbl_fav_sched_status.setStyleSheet("color: #888888; font-weight: bold;")
        row2.addWidget(self.lbl_fav_sched_status)

        row2.addStretch(1)

        main_layout.addLayout(row2)

        self.setStyleSheet("""
            FavToolBar {
                background-color: #202020;
                border-bottom: 1px solid #333333;
            }
        """)


class PageFavorites(QWidget):
    """
    优质精选页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageFavorites")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        self.toolbar = FavToolBar(self)
        layout.addWidget(self.toolbar)

        # 核心通用节点表格
        self.table = NodeTableView(self, controller=self.controller, page_type="favorites")
        layout.addWidget(self.table, 1)

        # 便于外部直接通过页面对象访问工具栏控件
        self.fav_max_delay = self.toolbar.fav_max_delay
        self.fav_min_speed = self.toolbar.fav_min_speed
        self.fav_rounds = self.toolbar.fav_rounds
        self.fav_speed_duration = self.toolbar.fav_speed_duration
        self.fav_jitter_min = self.toolbar.fav_jitter_min
        self.fav_jitter_up = self.toolbar.fav_jitter_up
        self.btn_fav_run = self.toolbar.btn_fav_run
        self.btn_fav_reload_history = self.toolbar.btn_fav_reload_history
        self.btn_fav_clean_stale = self.toolbar.btn_fav_clean_stale
        self.btn_fav_clear_all = self.toolbar.btn_fav_clear_all
        self.btn_fav_sync_now = self.toolbar.btn_fav_sync_now
        self.chk_fav_schedule = self.toolbar.chk_fav_schedule
        self.fav_sched_interval = self.toolbar.fav_sched_interval
        self.chk_fav_early_stop = self.toolbar.chk_fav_early_stop
        self.fav_target_hk = self.toolbar.fav_target_hk
        self.fav_target_nohk = self.toolbar.fav_target_nohk
        self.chk_fav_fallback = self.toolbar.chk_fav_fallback
        self.lbl_fav_sched_status = self.toolbar.lbl_fav_sched_status

        # 绑定数据变更信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)
        self.controller.fav_pipeline_status_updated.connect(self.lbl_fav_sched_status.setText)
        self.controller.fav_pipeline_finished.connect(self._on_fav_pipeline_finished)

        # 绑定工具栏按钮业务
        self.btn_fav_run.clicked.connect(self._on_run_fav_clicked)
        self.btn_fav_reload_history.clicked.connect(self._on_reload_history_clicked)
        self.btn_fav_clean_stale.clicked.connect(self._on_clean_stale_clicked)
        self.btn_fav_clear_all.clicked.connect(self._on_clear_all_clicked)
        self.btn_fav_sync_now.clicked.connect(self._on_sync_now_clicked)

        self.refresh_data()

    def refresh_data(self):
        """
        重新装配优质精选池数据并刷新表格
        """
        rows = self.controller.get_table_rows("favorites")
        self.table.populate(rows)

    def _on_reload_history_clicked(self):
        self.controller.reconcile_endpoints()
        self.controller.data_changed.emit()

    def _on_clean_stale_clicked(self):
        self.controller.clean_stale_favorites()
        self.controller.data_changed.emit()

    def _on_sync_now_clicked(self):
        self.controller.sync_favorites_to_active()
        self.controller.data_changed.emit()

    def _on_run_fav_clicked(self):
        """
        启动或终止精选池复测流水线
        """
        if self.controller.is_pipeline_running():
            self.controller.stop_fav_pipeline()
            self.btn_fav_run.setText("▶ 启动精选全自动测速")
            return

        cfg = self.get_fav_config()
        started = self.controller.start_fav_pipeline(cfg)
        if started:
            self.btn_fav_run.setText("⏹ 终止精选测速")

    def _on_fav_pipeline_finished(self, success: bool, msg: str):
        self.btn_fav_run.setText("▶ 启动精选全自动测速")
        self.lbl_fav_sched_status.setText(f"完成: {msg[:25]}")
        if hasattr(self, 'controller') and self.controller:
            self.controller.save_config(self.controller.state.get_snapshot())

    def _on_clear_all_clicked(self):
        from qfluentwidgets import MessageBox
        w = MessageBox("确认清空精选池", "确定要清空优质精选池中所有节点吗？\n清空后需重新运行全量优选或手动添加节点。", self)
        if w.exec():
            self.controller.clear_all_favorites()
            self.controller.data_changed.emit()

    def get_fav_config(self) -> dict:
        """
        提取当前精选页面的配置字典
        """
        cfg_storage = self.controller.load_config() if hasattr(self, 'controller') and self.controller else {}
        speed_url = str(cfg_storage.get("speed_url", "")).strip() or "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip"
        return {
            "speed_url": speed_url,
            "fav_max_delay": self.fav_max_delay.text().strip(),
            "fav_min_speed": self.fav_min_speed.text().strip(),
            "fav_rounds": self.fav_rounds.text().strip(),
            "fav_speed_duration": self.fav_speed_duration.text().strip(),
            "fav_jitter_min_delay": self.fav_jitter_min.text().strip(),
            "fav_jitter_up_threshold": self.fav_jitter_up.text().strip(),
            "fav_schedule_enabled": self.chk_fav_schedule.isChecked(),
            "fav_schedule_interval": self.fav_sched_interval.text().strip(),
            "fav_target_hk_count": self.fav_target_hk.text().strip(),
            "fav_target_nohk_count": self.fav_target_nohk.text().strip(),
            "fav_quota_early_stop": self.chk_fav_early_stop.isChecked(),
            "fav_fallback_enabled": self.chk_fav_fallback.isChecked(),
        }


```

```python
File: gui_fluent/pages/page_speed_black.py
"""
低速黑名单页面
展示因下载实测带宽低于设定淘汰门槛或连续测速失败而被淘汰的节点与端点
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout
else:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout

from gui_fluent.app_controller import AppController
from gui_fluent.widgets.node_table import NodeTableView


class PageSpeedBlack(QWidget):
    """
    低速黑名单页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageSpeedBlack")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 核心通用节点表格
        self.table = NodeTableView(self, controller=self.controller, page_type="speed_black")
        layout.addWidget(self.table, 1)

        # 绑定数据变更信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)
        self.refresh_data()

    def refresh_data(self):
        """
        重新装配低速黑名单数据并刷新表格
        """
        rows = self.controller.get_table_rows("speed_black")
        self.table.populate(rows)


```

```python
File: gui_fluent/pages/page_stars.py
"""
典藏管理池页面
包含典藏节点操作工具栏 (StarsToolBar) 以及典藏专用表格 (StarsTableView)
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
)
from gui_fluent.app_controller import AppController
from gui_fluent.widgets.stars_table import StarsTableView


class StarsToolBar(QWidget):
    """
    典藏管理池工具栏
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self.btn_add = PushButton("➕ 录入节点", self)
        layout.addWidget(self.btn_add)

        self.btn_pull_favorites = PushButton("📥 从精选池拉取", self)
        layout.addWidget(self.btn_pull_favorites)

        self.btn_test_delay = PushButton("⚡ 测延迟", self)
        layout.addWidget(self.btn_test_delay)

        self.btn_test_speed = PushButton("🚀 测速度", self)
        layout.addWidget(self.btn_test_speed)

        self.btn_remark = PushButton("✏️ 修改备注", self)
        layout.addWidget(self.btn_remark)

        self.btn_delete = PushButton("🗑️ 删除", self)
        layout.addWidget(self.btn_delete)

        layout.addStretch(1)

        self.btn_sync_root = PrimaryPushButton("💾 保存并推送根目录 /", self)
        layout.addWidget(self.btn_sync_root)

        self.setStyleSheet("""
            StarsToolBar {
                background-color: #202020;
                border-bottom: 1px solid #333333;
            }
        """)


class PageStars(QWidget):
    """
    典藏管理池页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageStars")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 工具栏
        self.toolbar = StarsToolBar(self)
        layout.addWidget(self.toolbar)

        # 典藏专用表格
        self.table = StarsTableView(self, controller=self.controller)
        layout.addWidget(self.table, 1)

        # 便于外部直接通过页面对象访问工具栏控件
        self.btn_add = self.toolbar.btn_add
        self.btn_pull_favorites = self.toolbar.btn_pull_favorites
        self.btn_test_delay = self.toolbar.btn_test_delay
        self.btn_test_speed = self.toolbar.btn_test_speed
        self.btn_remark = self.toolbar.btn_remark
        self.btn_delete = self.toolbar.btn_delete
        self.btn_sync_root = self.toolbar.btn_sync_root

        # 绑定数据变更信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)

        # 绑定工具栏按钮业务与双击修改备注
        self.table.double_clicked.connect(lambda ep: self._on_remark_clicked())
        self.btn_add.clicked.connect(self._on_add_clicked)
        self.btn_pull_favorites.clicked.connect(self._on_pull_favorites_clicked)
        self.btn_test_delay.clicked.connect(lambda: self.controller.test_stars_pipeline(mode="delay", endpoints=self.table.get_selected_endpoints() or None))
        self.btn_test_speed.clicked.connect(lambda: self.controller.test_stars_pipeline(mode="speed", endpoints=self.table.get_selected_endpoints() or None))
        self.btn_remark.clicked.connect(self._on_remark_clicked)
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        self.btn_sync_root.clicked.connect(lambda: self.controller.push_stars_to_cloud())

        self.refresh_data()

    def refresh_data(self):
        """
        重新装配典藏管理池数据并刷新表格
        """
        rows = self.controller.get_table_rows("stars")
        self.table.populate(rows)

    def _on_pull_favorites_clicked(self):
        favs = list(self.controller.state.favorites)
        if not favs:
            self.controller.log("⚠️ 优质精选池当前暂无节点可拉入！")
            return
        self.controller.promote_nodes_to_stars(favs)
        self.controller.data_changed.emit()

    def _on_add_clicked(self):
        if "PyQt5" in sys.modules:
            from PyQt5.QtWidgets import QInputDialog
        else:
            from PyQt6.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, "录入典藏节点", "请输入节点端点及备注 (格式: IP:端口#备注 或 IP:端口):")
        if ok and text and text.strip():
            raw = text.strip()
            if "#" in raw:
                parts = raw.split("#", 1)
                ep = parts[0].strip()
                rem = parts[1].strip() or "手动录入"
            else:
                ep = raw
                rem = "手动录入"
            self.controller.add_star_node(ep, rem)

    def _on_remark_clicked(self):
        eps = self.table.get_selected_endpoints()
        if not eps:
            self.controller.log("⚠️ 请先在列表中选中需要修改备注的典藏节点！")
            return
        if "PyQt5" in sys.modules:
            from PyQt5.QtWidgets import QInputDialog
        else:
            from PyQt6.QtWidgets import QInputDialog

        ep = eps[0]
        text, ok = QInputDialog.getText(self, "修改备注", f"修改典藏节点 [{ep}] 的备注信息:")
        if ok and text is not None:
            self.controller.update_star_remark(ep, text.strip())

    def _on_delete_clicked(self):
        eps = self.table.get_selected_endpoints()
        if not eps:
            self.controller.log("⚠️ 请先在列表中选中要删除的典藏节点！")
            return
        from qfluentwidgets import MessageBox
        w = MessageBox("删除确认", f"确定从本地典藏池移除选中的 {len(eps)} 个节点吗？\n（注：点击保存推送前云端数据不会变动）", self)
        if w.exec():
            self.controller.delete_selected_stars(eps)


```

```python
File: gui_fluent/pages/page_verified.py
"""
沉淀孵化池页面
包含孵化考核阈值与流转工具栏 (VerifiedToolBar) 以及孵化表格 (VerifiedTableView)
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    BodyLabel,
    LineEdit,
    PushButton,
    PrimaryPushButton,
)
from gui_fluent.app_controller import AppController
from gui_fluent.widgets.verified_table import VerifiedTableView


class VerifiedToolBar(QWidget):
    """
    沉淀孵化池工具栏
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        layout.addWidget(BodyLabel("孵化达标要求: 连续合格时长 >", self))
        self.incubate_hours = LineEdit(self)
        self.incubate_hours.setText("24")
        self.incubate_hours.setFixedWidth(40)
        self.incubate_hours.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.incubate_hours)
        layout.addWidget(BodyLabel("小时", self))

        layout.addWidget(BodyLabel("达标轮数 >=", self))
        self.incubate_passes = LineEdit(self)
        self.incubate_passes.setText("5")
        self.incubate_passes.setFixedWidth(35)
        self.incubate_passes.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.incubate_passes)
        layout.addWidget(BodyLabel("轮", self))

        self.btn_pull_favorites = PushButton("📥 从精选池拉入", self)
        layout.addWidget(self.btn_pull_favorites)

        self.btn_promote = PushButton("⚡ 立即晋升达标节点", self)
        layout.addWidget(self.btn_promote)

        self.btn_remove = PushButton("🗑️ 从观察池移出", self)
        layout.addWidget(self.btn_remove)

        layout.addStretch(1)

        self.btn_sync_verified = PrimaryPushButton("💾 同步推送 /verified.txt", self)
        layout.addWidget(self.btn_sync_verified)

        self.setStyleSheet("""
            VerifiedToolBar {
                background-color: #202020;
                border-bottom: 1px solid #333333;
            }
        """)


class PageVerified(QWidget):
    """
    沉淀孵化池页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageVerified")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 工具栏
        self.toolbar = VerifiedToolBar(self)
        layout.addWidget(self.toolbar)

        # 沉淀孵化池专用表格
        self.table = VerifiedTableView(self, controller=self.controller)
        layout.addWidget(self.table, 1)

        # 便于外部直接通过页面对象访问工具栏控件
        self.incubate_hours = self.toolbar.incubate_hours
        self.incubate_passes = self.toolbar.incubate_passes
        self.btn_pull_favorites = self.toolbar.btn_pull_favorites
        self.btn_promote = self.toolbar.btn_promote
        self.btn_remove = self.toolbar.btn_remove
        self.btn_sync_verified = self.toolbar.btn_sync_verified

        # 绑定数据变更信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)

        # 绑定工具栏按钮业务
        self.btn_pull_favorites.clicked.connect(self.controller.sync_favorites_to_verified)
        self.btn_promote.clicked.connect(self._on_promote_clicked)
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        self.btn_sync_verified.clicked.connect(lambda: self.controller.push_verified_to_cloud())

        self.refresh_data()

    def refresh_data(self):
        """
        重新装配沉淀孵化池数据并刷新表格
        """
        rows = self.controller.get_table_rows("verified")
        self.table.populate(rows)

    def _on_promote_clicked(self):
        eps = self.table.get_selected_endpoints()
        if not eps:
            self.controller.log("⚠️ 请先在表格中选中要加冕的沉淀节点！")
            return
        self.controller.force_promote_verified_to_stars(eps)

    def _on_remove_clicked(self):
        eps = self.table.get_selected_endpoints()
        if not eps:
            self.controller.log("⚠️ 请先在表格中选中要移出的沉淀节点！")
            return
        from qfluentwidgets import MessageBox
        w = MessageBox("确认移出", f"确定要从沉淀池移出选中的 {len(eps)} 个节点吗？", self)
        if w.exec():
            self.controller.delete_selected_verified(eps)

    def get_verified_config(self) -> dict:
        """
        提取当前沉淀孵化池配置字典
        """
        return {
            "incubate_hours": self.incubate_hours.text().strip(),
            "incubate_passes": self.incubate_passes.text().strip(),
        }


```

```python
File: gui_fluent/pages/__init__.py
"""
Fluent UI 各功能页面模块导出
"""
from gui_fluent.pages.page_active import PageActive
from gui_fluent.pages.page_favorites import PageFavorites
from gui_fluent.pages.page_verified import PageVerified
from gui_fluent.pages.page_stars import PageStars
from gui_fluent.pages.page_delay_black import PageDelayBlack
from gui_fluent.pages.page_speed_black import PageSpeedBlack
from gui_fluent.pages.page_cloud_text import PageCloudText

__all__ = [
    "PageActive",
    "PageFavorites",
    "PageVerified",
    "PageStars",
    "PageDelayBlack",
    "PageSpeedBlack",
    "PageCloudText",
]

```

```python
File: gui_fluent/pipelines/auto_pipeline.py
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
from services.probe_service import get_cf_colo_raw, tcp_ping
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

    def log(self, msg: str):
        """发射日志信号的统一快捷方法"""
        self.log_signal.emit(msg)

    def run(self):
        self.log_signal.emit("🚀 启动一整套全自动大优选流程 (Fluent 后台线程)...")
        try:
            # 0. 解析配置参数
            max_delay = int(self.config.get("max_delay", 100)) if str(self.config.get("max_delay", "")).isdigit() else 100
            try:
                min_speed = float(self.config.get("min_speed", 5.0))
            except Exception:
                min_speed = 5.0
            # 极限淘汰制：严格初筛轮数为 2 轮
            rounds = 2
            raw_timeout = int(self.config.get("test_timeout", 500)) if str(self.config.get("test_timeout", "")).isdigit() else 500
            timeout_ms = min(500, raw_timeout)
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
                    if not is_asian_node(n):
                        if n not in self.controller.state.local_blacklist:
                            self.controller.state.local_blacklist.add(n)
                            self.controller.state.blacklist_reasons[n] = "非亚洲节点 (自动过滤)"
                        continue

                    ep = _get_ep(n)
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
                        if not is_asian_node(n):
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

            # 2. 并发延迟初筛 (两轮极限淘汰制 Fail-Fast，接入双轨测速分流)
            self.log_signal.emit(f"⚡ 开始执行两轮极限淘汰制初筛 (全量待测端点共 {len(unique_eps)} 个，单次超时上限: {timeout_ms}ms)...")

            all_known_nodes = set(self.controller.state.all_nodes)

            def _measure_endpoint_delay(endpoint: str, rep_node: str, t_ms: int) -> int:
                """
                双轨分流测速引擎：
                1. 订阅已有实体代理节点：调用 Clash 内核 RESTful 接口执行真实链路测速；
                2. pending.txt 等未入库裸端点：通过原生 Socket tcp_ping 进行真实 TCP SYN 握手探活；
                彻底杜绝向 Clash 内核请求不存在的节点导致 404 秒级误杀！
                """
                # 轨道 A: 节点已在 Clash 订阅代理列表中
                if rep_node in all_known_nodes:
                    return self.controller.clash_client.query_proxy_delay(rep_node, test_url, timeout_ms=t_ms)

                # 轨道 B: 裸端点（未在 Clash 代理树中注册）
                target_host = endpoint
                target_port = 443
                if ":" in target_host:
                    parts = target_host.split(":", 1)
                    target_host = parts[0].strip()
                    if parts[1].isdigit():
                        target_port = int(parts[1])

                timeout_sec = max(0.2, min(0.5, t_ms / 1000.0))
                return tcp_ping(target_host, port=target_port, timeout=timeout_sec)

            # ======================== 第 1 轮：全量普筛与极速淘汰 ========================
            round1_survivors = []
            survivor_lock = threading.Lock()
            total_pending = len(unique_eps)
            done_r1 = 0
            last_log_emit = 0.0
            last_status_emit = 0.0

            def _test_round1(endpoint):
                if self.isInterruptionRequested():
                    return
                rep_node = choose_canonical_node_name(ep_to_untested[endpoint])
                cur_delay = _measure_endpoint_delay(endpoint, rep_node, timeout_ms)

                # 淘汰判定 (Fail-Fast: 真实超时或延迟超标即刻出清)
                if cur_delay >= 99999 or cur_delay > max_delay or cur_delay >= bl_delay_threshold:
                    if cur_delay >= 99999:
                        reason = "首轮初筛超时 (≥99999ms)"
                    elif cur_delay >= bl_delay_threshold:
                        reason = f"首轮延迟超标 ({cur_delay}ms ≥ {bl_delay_threshold}ms)"
                    else:
                        reason = f"首轮延迟淘汰 ({cur_delay}ms > {max_delay}ms)"

                    now_bl_t = time.time()
                    with self.controller.state.lock:
                        self.controller.state.local_blacklist.add(rep_node)
                        self.controller.state.favorites.discard(rep_node)
                        self.controller.state.blacklist_reasons[rep_node] = reason
                        self.controller.state.blacklist_timestamps[rep_node] = now_bl_t
                        if endpoint:
                            self.controller.state.local_blacklist.add(endpoint)
                            self.controller.state.blacklist_reasons[endpoint] = reason
                            self.controller.state.blacklist_timestamps[endpoint] = now_bl_t
                        for same_n in ep_to_untested.get(endpoint, []):
                            self.controller.state.local_blacklist.add(same_n)
                            self.controller.state.favorites.discard(same_n)
                            self.controller.state.blacklist_reasons[same_n] = reason
                            self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                        if endpoint in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[endpoint]

                    row_ref = ep_to_row.get(endpoint)
                    if row_ref:
                        row_ref["status"] = "首轮淘汰"
                        row_ref["reason"] = reason
                        row_ref["delay"] = f"{cur_delay}ms" if cur_delay < 99999 else "超时"
                else:
                    # 首轮合格幸存
                    with self.controller.state.lock:
                        _record_delay_sample(self.controller.state.node_delay_history, rep_node, cur_delay, ep=endpoint)
                        for n in ep_to_untested[endpoint]:
                            self.controller.state.node_delays[n] = cur_delay
                            hist = self.controller.state.node_history.setdefault(n, [])
                            hist.append(cur_delay)
                            self.controller.state.node_history[n] = hist[-2:]

                    row_ref = ep_to_row.get(endpoint)
                    if row_ref:
                        row_ref["delay"] = f"{cur_delay}ms"
                        row_ref["status"] = "首轮达标 (待复测)"
                        row_ref["delay_hist"] = str(cur_delay)

                    with survivor_lock:
                        round1_survivors.append(endpoint)

            # 并发严格压制在 max_workers = 40，防止 Windows 端口与 Socket 缓冲耗尽
            with ThreadPoolExecutor(max_workers=min(40, len(unique_eps))) as executor:
                futures_r1 = {executor.submit(_test_round1, ep): ep for ep in unique_eps}
                for fut in as_completed(futures_r1):
                    if self.isInterruptionRequested():
                        break
                    done_r1 += 1
                    now_ts = time.time()

                    # 时间戳节流心跳：每 1 秒输出一次控制台进度日志
                    if (now_ts - last_log_emit >= 1.0) or done_r1 == total_pending:
                        last_log_emit = now_ts
                        with survivor_lock:
                            s_cnt = len(round1_survivors)
                        failed_cnt = done_r1 - s_cnt
                        self.log(f"⚡ [初筛第1轮进度] {done_r1}/{total_pending} | 存活: {s_cnt} | 淘汰: {failed_cnt}")

                    # 状态栏节流更新 (>= 0.5s)
                    if (now_ts - last_status_emit >= 0.5) or done_r1 == total_pending:
                        last_status_emit = now_ts
                        with survivor_lock:
                            s_cnt = len(round1_survivors)
                        self.status_signal.emit(f"初筛第 1/2 轮 (全量淘汰): {done_r1}/{total_pending} [幸存 {s_cnt}]")

            if self.isInterruptionRequested():
                self.log("⏹ 用户已终止流水线任务")
                self.finished_signal.emit(False, "任务已被用户手动终止")
                return

            self.log(f"🏁 [第1轮初筛完毕] 共生还 {len(round1_survivors)} 个节点，立即转入第 2 轮复筛...")

            if not round1_survivors:
                self.status_signal.emit("首轮全军覆没")
                self.finished_signal.emit(True, f"延迟初筛结束：{total_pending} 个待测节点在首轮测试中全部超时或超标。")
                return

            # ======================== 第 2 轮：幸存者极限复测 ========================
            round2_survivors = []
            candidates = []
            total_r2 = len(round1_survivors)
            done_r2 = 0
            last_log_emit_r2 = 0.0
            last_status_emit_r2 = 0.0

            def _test_round2(endpoint):
                if self.isInterruptionRequested():
                    return
                ep = endpoint
                rep_node = choose_canonical_node_name(ep_to_untested[endpoint])
                cur_delay = _measure_endpoint_delay(endpoint, rep_node, timeout_ms)

                # 复测淘汰判定 (要求 100% 全通率)
                if cur_delay >= 99999 or cur_delay > max_delay or cur_delay >= bl_delay_threshold:
                    if cur_delay >= 99999:
                        reason = "次轮复测超时波动 (≥99999ms)"
                    elif cur_delay >= bl_delay_threshold:
                        reason = f"次轮复测延迟超标 ({cur_delay}ms ≥ {bl_delay_threshold}ms)"
                    else:
                        reason = f"次轮复测超标 ({cur_delay}ms > {max_delay}ms)"

                    now_bl_t = time.time()
                    with self.controller.state.lock:
                        self.controller.state.local_blacklist.add(rep_node)
                        self.controller.state.favorites.discard(rep_node)
                        self.controller.state.blacklist_reasons[rep_node] = reason
                        self.controller.state.blacklist_timestamps[rep_node] = now_bl_t
                        if endpoint:
                            self.controller.state.local_blacklist.add(endpoint)
                            self.controller.state.blacklist_reasons[endpoint] = reason
                            self.controller.state.blacklist_timestamps[endpoint] = now_bl_t
                        for same_n in ep_to_untested.get(endpoint, []):
                            self.controller.state.local_blacklist.add(same_n)
                            self.controller.state.favorites.discard(same_n)
                            self.controller.state.blacklist_reasons[same_n] = reason
                            self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                        if endpoint in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[endpoint]

                    row_ref = ep_to_row.get(endpoint)
                    if row_ref:
                        row_ref["status"] = "次轮淘汰"
                        row_ref["reason"] = reason
                        h_vals = self.controller.state.node_history.get(rep_node, [])
                        row_ref["delay_hist"] = "/".join(str(v) if v < 99999 else "超时" for v in h_vals) + f"/{cur_delay if cur_delay < 99999 else '超时'}"
                else:
                    # 记录第 2 轮样本
                    with self.controller.state.lock:
                        _record_delay_sample(self.controller.state.node_delay_history, rep_node, cur_delay, ep=endpoint)
                        for n in ep_to_untested[endpoint]:
                            self.controller.state.node_delays[n] = cur_delay
                            hist = self.controller.state.node_history.setdefault(n, [])
                            hist.append(cur_delay)
                            self.controller.state.node_history[n] = hist[-2:]

                    # 抖动判定
                    hist = self.controller.state.node_history.get(rep_node, [])
                    is_j_bad, j_min, j_up = check_node_jitter_blacklisted(hist[-2:], jitter_min_d, jitter_up_th)
                    if is_j_bad:
                        j_reason = f"延迟抖动淘汰 (底{j_min}ms 抖动+{j_up}ms)"
                        now_bl_t = time.time()
                        with self.controller.state.lock:
                            self.controller.state.local_blacklist.add(rep_node)
                            self.controller.state.favorites.discard(rep_node)
                            self.controller.state.blacklist_reasons[rep_node] = j_reason
                            self.controller.state.blacklist_timestamps[rep_node] = now_bl_t
                            if endpoint:
                                self.controller.state.local_blacklist.add(endpoint)
                                self.controller.state.blacklist_reasons[ep] = j_reason
                                self.controller.state.blacklist_timestamps[ep] = now_bl_t
                            for same_n in ep_to_untested.get(endpoint, []):
                                self.controller.state.local_blacklist.add(same_n)
                                self.controller.state.favorites.discard(same_n)
                                self.controller.state.blacklist_reasons[same_n] = j_reason
                                self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                            if endpoint in self.controller.state.verified_nodes:
                                del self.controller.state.verified_nodes[endpoint]

                        row_ref = ep_to_row.get(endpoint)
                        if row_ref:
                            row_ref["status"] = "抖动淘汰"
                            row_ref["reason"] = j_reason
                    else:
                        # 双轮全通，准入合格
                        cur_avg, hist_avg = compute_delay_stats(
                            rep_node,
                            ep=endpoint,
                            node_history=self.controller.state.node_history,
                            node_delays=self.controller.state.node_delays,
                            node_delay_history=self.controller.state.node_delay_history,
                            get_node_endpoint_fn=_get_ep,
                        )
                        row_ref = ep_to_row.get(endpoint)
                        if row_ref:
                            row_ref["status"] = "初筛合格"
                            row_ref["reason"] = f"双轮全通 (均值 {cur_avg})"
                            row_ref["avg_delay"] = cur_avg
                            row_ref["hist_avg"] = hist_avg
                            h_vals = self.controller.state.node_history.get(rep_node, [])
                            row_ref["delay_hist"] = "/".join(str(v) if v < 99999 else "超时" for v in h_vals)

                        with survivor_lock:
                            round2_survivors.append(endpoint)
                            candidates.append(rep_node)

            # 并发严格压制在 max_workers = 40
            with ThreadPoolExecutor(max_workers=min(40, len(round1_survivors))) as executor:
                futures_r2 = {executor.submit(_test_round2, ep): ep for ep in round1_survivors}
                for fut in as_completed(futures_r2):
                    if self.isInterruptionRequested():
                        break
                    done_r2 += 1
                    now_ts = time.time()

                    # 时间戳节流心跳：每 1 秒输出一次控制台进度日志
                    if (now_ts - last_log_emit_r2 >= 1.0) or done_r2 == total_r2:
                        last_log_emit_r2 = now_ts
                        with survivor_lock:
                            s_cnt = len(candidates)
                        failed_cnt = done_r2 - s_cnt
                        self.log(f"⚡ [复测第2轮进度] {done_r2}/{total_r2} | 存活: {s_cnt} | 淘汰: {failed_cnt}")

                    # 状态栏节流更新 (>= 0.5s)
                    if (now_ts - last_status_emit_r2 >= 0.5) or done_r2 == total_r2:
                        last_status_emit_r2 = now_ts
                        with survivor_lock:
                            s_cnt = len(candidates)
                        self.status_signal.emit(f"初筛第 2/2 轮 (极限复测): {done_r2}/{total_r2} [合格 {s_cnt}]")

            if self.isInterruptionRequested():
                self.log("⏹ 用户已终止流水线任务")
                self.finished_signal.emit(False, "任务已被用户手动终止")
                return

            self.log(
                f"🏁 [第2轮复筛完毕] 最终晋级 {len(candidates)} 个高质节点，立即转入 Colo 测定与测速..."
            )

            # 仅保留通过双轮考核合格的端点行，单次通知 UI 表格装配
            surviving_eps = set(round2_survivors)
            test_rows = [r for r in test_rows if r.get("endpoint") in surviving_eps]
            ep_to_row = { r["endpoint"]: r for r in test_rows if "endpoint" in r }
            self.rows_updated.emit([dict(x) for x in test_rows])
            self.status_signal.emit(f"初筛完毕: 合格 {len(candidates)} 个")

            if not candidates:
                self.status_signal.emit("无达标节点")
                self.finished_signal.emit(True, "延迟初筛结束：所有节点均未能通过两轮极限淘汰考核。")
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
                            self.log_signal.emit("⏹ 用户已终止流水线任务")
                            self.finished_signal.emit(False, "任务已被用户手动终止")
                            return

                        ep = _get_ep(node_name)
                        clash_node_name = graft_map.get(ep, node_name)
                        row_ref = ep_to_row.get(ep)
                        target_str = f" [已集齐: {len(premium_nodes)}/{target_node_limit}]" if target_node_limit > 0 else f" [已入选 {len(premium_nodes)} 个]"
                        self.status_signal.emit(f"带宽精测: [{idx}/{total_cand}]{target_str} {node_name[:16]}...")

                        if row_ref:
                            row_ref["status"] = f"带宽测速中 [{idx}/{total_cand}]"
                            self.rows_updated.emit([dict(r) for r in test_rows])

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
                            premium_nodes.append(node_name)
                            with self.controller.state.lock:
                                self.controller.state.favorites.add(node_name)
                                d_val = self.controller.state.node_delays.get(node_name, 0)
                                self.controller.state.fav_reasons[node_name] = f"真实测速达标 ({speed_val:.2f}MB/s)"
                                if ep:
                                    self.controller.state.cloud_endpoints[ep] = coronated_name
                                    if ":" in ep:
                                        self.controller.state.cloud_endpoints[ep.split(":")[0]] = coronated_name

                            if row_ref:
                                row_ref["name"] = coronated_name
                                row_ref["status"] = "优质精选"
                                row_ref["reason"] = f"下行 {speed_val:.2f} MB/s ≥ {min_speed} MB/s"

                            self.log_signal.emit(f"⭐ 节点入选精选: {coronated_name} ({ep}) (下行: {speed_val:.2f} MB/s)")
                            test_rows = [r for r in test_rows if r.get("endpoint") != ep and r.get("name") != node_name]
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

                            newly_speed_blacklisted += 1

                            self.log_signal.emit(f"【低速淘汰】节点 {node_name} 速度 {speed_val:.2f} MB/s 未达标 (≥{min_speed} MB/s)")
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

```

```python
File: gui_fluent/pipelines/fav_pipeline.py
"""
优质精选池复测流水线工作线程 (FavPipelineWorker)
基于 QThread 运行，完全解耦 UI 渲染，1:1 平移 gui/app.py 中 start_fav_review_pipeline 核心业务逻辑
"""
import json
import ssl
import sys
import time
import traceback
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
                )

                for f in list(self.controller.state.favorites):
                    target_ep = _get_ep(f) or str(f)
                    # 如果能在当前订阅中找到该物理端点对应的实体节点
                    matched_proxy = current_ep_to_proxy.get(target_ep)
                    if matched_proxy:
                        if matched_proxy not in seen_targets and is_asian_node(matched_proxy):
                            active_fav_targets.append(matched_proxy)
                            seen_targets.add(matched_proxy)
                            fav_origin_map[matched_proxy] = f
                    elif f in self.controller.state.all_nodes and is_asian_node(f):
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
                    if not is_asian_node(n):
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
                        qualified_nohk.append(n)
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

```

```python
File: gui_fluent/pipelines/__init__.py
"""
Fluent 流水线模块
"""
from gui_fluent.pipelines.auto_pipeline import AutoPipelineWorker
from gui_fluent.pipelines.fav_pipeline import FavPipelineWorker

__all__ = ["AutoPipelineWorker", "FavPipelineWorker"]

```

```python
File: gui_fluent/widgets/c_miner_dialog.py
"""
C 段全量高并发极速深度挖掘对话框 (CSegmentMinerDialog)
基于 PyQt-Fluent-Widgets 构建，支持对 /24 网段 254 个 IP 进行并发 TCP 测延与真实 Colo 机房判定，
并提供一键批量导入至优质精选池、沉淀孵化池或典藏常青池。
"""
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QColor, QBrush, QFont
    from PyQt5.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QWidget,
        QProgressDialog,
    )
else:
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QColor, QBrush, QFont
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QWidget,
        QProgressDialog,
    )

from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
    LineEdit,
    InfoBar,
    MessageBox,
    FluentIcon,
)

from services.probe_service import get_c_segment_ips, tcp_ping, get_cf_colo_raw
from services.colo_service import is_asian_node


class CSegmentMinerWorker(QThread):
    """
    C 段深度挖掘后台扫描线程：
    分两阶段进行：
      阶段 1: 50 线程高并发全网段 TCP Ping，快速筛选延迟 <= 门槛的活跃 IP
      阶段 2: 20 线程对达标 IP 进行 Cloudflare 真实机房 (Colo) 测定
    """
    progress_signal = pyqtSignal(int, int)  # (done, total)
    stage_signal = pyqtSignal(str)          # 阶段提示文本
    finished_signal = pyqtSignal(list)      # 扫描结果 list[dict]

    def __init__(self, c_ips: list[str], port: int = 443, threshold: int = 130, parent=None):
        super().__init__(parent)
        self.c_ips = list(c_ips)
        self.port = port
        self.threshold = threshold
        self._is_stopped = False

    def stop(self):
        self._is_stopped = True
        self.requestInterruption()

    def run(self):
        total = len(self.c_ips)
        if total == 0:
            self.finished_signal.emit([])
            return

        # 阶段 1: 全并发 TCP 测延
        self.stage_signal.emit(f"正在全并发 TCP 测延 (共 {total} 个 IP)...")
        results = []
        done_cnt = [0]

        def _scan_one(ip):
            if self._is_stopped or self.isInterruptionRequested():
                return None
            rtt = tcp_ping(ip, port=self.port, timeout=1.2)
            done_cnt[0] += 1
            if done_cnt[0] % 10 == 0 or done_cnt[0] >= total:
                self.progress_signal.emit(done_cnt[0], total)
            if rtt < 99999 and rtt <= self.threshold:
                return (ip, rtt)
            return None

        with ThreadPoolExecutor(max_workers=50) as ex:
            for res in ex.map(_scan_one, self.c_ips):
                if res:
                    results.append(res)
                if self._is_stopped or self.isInterruptionRequested():
                    break

        if self._is_stopped or self.isInterruptionRequested():
            self.stage_signal.emit("扫描已中止")
            self.finished_signal.emit([])
            return

        if not results:
            self.stage_signal.emit(f"TCP 测延完成：未发现延迟 ≤ {self.threshold}ms 的 IP")
            self.finished_signal.emit([])
            return

        # 阶段 2: 真实 Colo 机房校准 (严禁降级回退至普通地理属地，杜绝非 CF 服务器伪充优选)
        self.stage_signal.emit(f"TCP 达标 {len(results)} 个，正在严格鉴权 Cloudflare 真实机房...")
        colo_map = {}

        def _probe_colo(ip):
            if self._is_stopped or self.isInterruptionRequested():
                return
            # 严格关闭地理降级回退 (enable_geo_fallback=False)，确保只有真正响应 /cdn-cgi/trace 的 Cloudflare 机房才算达标
            c_code, c_disp = get_cf_colo_raw(ip, port=self.port, timeout=1.8, enable_geo_fallback=False)
            colo_map[ip] = (c_code, c_disp)

        with ThreadPoolExecutor(max_workers=20) as ex:
            for _ in ex.map(_probe_colo, [r[0] for r in results]):
                if self._is_stopped or self.isInterruptionRequested():
                    break

        # 按延迟从小到大排序
        results.sort(key=lambda x: x[1])

        final_rows = []
        valid_cf_count = 0
        for ip, rtt in results:
            c_code, c_disp = colo_map.get(ip, ("-", "-"))
            # 必须严格具备 Cloudflare Anycast 数据中心三字代码才视为达标
            is_cf = bool(c_code and c_code != "-" and c_code != "ANY")
            if is_cf:
                colo_label = c_disp
                status_text = "✅ 极速达标"
                valid_cf_count += 1
            else:
                colo_label = "非CF机房" if not c_disp or c_disp == "-" else f"{c_disp} (非CF)"
                status_text = "❌ 非CF机房"

            final_rows.append({
                "ip": ip,
                "port": self.port,
                "delay": rtt,
                "delay_str": f"{rtt} ms",
                "colo_code": c_code if is_cf else "-",
                "colo": colo_label,
                "status": status_text,
                "is_valid_cf": is_cf,
            })

        self.finished_signal.emit(final_rows)


class PostImportWorker(QThread):
    """
    C 段导入后全链路闭环专职工作线程：
    继承 QThread 并通过 pyqtSignal 跨线程安全通信，彻底杜绝 UI 假死与 QObject 亲和性冲突。
    """
    step_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, list)

    def __init__(self, controller, target: str, count: int, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.target = target
        self.count = count

    def run(self):
        pool_names = {
            "fav": "【⭐ 优质精选池】",
            "verified": "【⏳ 沉淀孵化池】",
            "stars": "【🏆 典藏管理池】",
            "pending": "【⚪ 活跃待测池】",
        }
        target_name = pool_names.get(self.target, "目标池")
        logs_step = [f"✅ 本地收编: 成功收录 {self.count} 个极速 IP 至 {target_name}"]
        try:
            # 步骤 1: 尝试推送至 Cloudflare Worker 云端
            self.step_signal.emit("[1/4] 正在同步推送至 Cloudflare Worker...")
            ok_w = False
            msg_w = ""
            if self.target == "fav":
                fav_lines = []
                seen_eps = set()
                with self.controller.state.lock:
                    for f in list(self.controller.state.favorites):
                        ep_val = self.controller._get_ep(f) or str(f)
                        if not ep_val or ep_val in seen_eps or ep_val == "127.0.0.1:443":
                            continue
                        seen_eps.add(ep_val)
                        colo = self.controller.state.node_colo.get(f, self.controller.state.node_colo.get(ep_val, "JP"))
                        if not colo or colo == "-":
                            colo = "亚洲"
                        spd = self.controller.state.node_speeds.get(f, self.controller.state.node_speeds.get(ep_val, 0.0))
                        reason = self.controller.state.fav_reasons.get(f, self.controller.state.fav_reasons.get(ep_val, ""))
                        if spd and spd > 0.1:
                            uniform_name = f"{colo} {spd:.2f} MB/s"
                        elif "C段" in reason:
                            uniform_name = f"{colo} [C段挖掘]"
                        else:
                            uniform_name = colo
                        fav_lines.append(f"{ep_val}#{uniform_name}")
                        self.controller.state.cloud_endpoints[ep_val] = uniform_name
                        if ":" in ep_val:
                            self.controller.state.cloud_endpoints[ep_val.split(":")[0]] = uniform_name
                payload = ("\r\n".join(fav_lines) + "\r\n") if fav_lines else "# empty\r\n"
                ok_w, msg_w = self.controller.push_text_to_cf_worker(payload, subpath="/auto.txt")
            elif self.target == "verified":
                with self.controller.state.lock:
                    lines = [f"{v['endpoint']}#{v.get('remark', '')}" for v in self.controller.state.verified_nodes.values() if v.get("endpoint")]
                payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
                ok_w, msg_w = self.controller.push_text_to_cf_worker(payload, subpath="/verified.txt")
            elif self.target == "stars":
                with self.controller.state.lock:
                    lines = [f"{item.get('endpoint', '')}#{item.get('remark', '')}" for item in self.controller.state.stars_nodes if item.get('endpoint')]
                payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
                ok_w, msg_w = self.controller.push_text_to_cf_worker(payload, subpath="")
            elif self.target == "pending":
                # 同步追加推送到 /pending.txt 并自动排查已存在的精选与黑名单
                pending_items = getattr(self, "pending_items", [])
                ok_w, msg_w = self.controller.append_pending_endpoints_to_cloud_sync(pending_items)

            if ok_w:
                logs_step.append("✅ 云端同步: 已成功推送到 Cloudflare Worker")
                self.controller.log(f"Worker 同步成功: {msg_w}")
            else:
                logs_step.append(f"⚠️ 云端同步: {msg_w}")
                self.controller.log(f"Worker 同步提示: {msg_w}")

            # 重新拉取云端映射
            self.controller.fetch_cloud_endpoints_sync()
            self.controller.fetch_pending_endpoints_sync()
            time.sleep(0.5)

            # 步骤 2: 在线拉取更新订阅 (拉取最新 profiles yaml 并重新解析)
            self.step_signal.emit("[2/4] 正在拉取远程最新订阅并解析节点...")
            up_ok, up_msg = self.controller.update_remote_subscription_sync()
            if up_ok:
                logs_step.append(f"✅ 订阅更新: {up_msg}")
            else:
                logs_step.append(f"⚠️ 订阅更新: {up_msg}")

            # 步骤 3: 写入 Script.js 并触发热键热更激活订阅
            self.step_signal.emit("[3/4] 正在写入 Script.js 并触发热更激活...")
            self.controller.generate_script_and_reload()
            logs_step.append("✅ 热更激活: 已生成 Script.js 并模拟热键激活")

            # 步骤 4: 探测 Clash 内核装载状态
            self.step_signal.emit("[4/4] 正在探测 Clash 内核装载状态...")
            loaded_ok, loaded_msg = self.controller.clash_client.wait_for_kernel_reload(
                self.controller.state.all_nodes, max_wait_sec=10
            )
            logs_step.append(f"{'✅' if loaded_ok else '⚠️'} 内核装载: {loaded_msg}")
            self.controller.log(f"内核探测反馈: {loaded_msg}")

            # 保存状态与触发 UI 刷新
            self.controller.save_config(self.controller.get_state_snapshot())
            self.controller.data_changed.emit()

            final_ok = ok_w or up_ok or loaded_ok
            self.finished_signal.emit(final_ok, f"已成功收编 {self.count} 个 IP 并完成热更闭环！", logs_step)

        except Exception as ex:
            err_msg = f"收编后闭环处理异常: {ex}"
            self.controller.log(f"❌ {err_msg}")
            self.finished_signal.emit(False, err_msg, logs_step)


class CSegmentMinerDialog(QDialog):
    """
    Fluent 风格 C 段全量深度挖掘对话框
    """

    COLUMN_HEADERS = ["IP 地址", "端口", "TCP 握手延迟", "真实机房 (Colo)", "评估状态"]
    COLUMN_WIDTHS = [180, 75, 130, 200, 130]

    def __init__(self, seed_ip: str, seed_port: int = 443, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.seed_ip = seed_ip
        self.seed_port = seed_port
        self.c_ips = get_c_segment_ips(seed_ip)
        self.c_segment_name = ".".join(seed_ip.split(".")[:3]) + ".0/24" if "." in seed_ip else seed_ip
        self.worker = None
        self._post_worker = None
        self._current_results = []

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"🔍 C 段全量极速深度挖掘 - {self.c_segment_name}")
        self.setMinimumSize(920, 600)
        self.resize(960, 640)

        # 深色窗口风格
        self.setStyleSheet("""
            QDialog {
                background-color: #151822;
                color: #e2e8f0;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QTableWidget {
                background-color: #181b26;
                color: #e2e8f0;
                gridline-color: rgba(255, 255, 255, 0.06);
                border: 1px solid #2c3246;
                border-radius: 6px;
                selection-background-color: #28334a;
                selection-color: #ffffff;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1e2230;
                color: #8d98af;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 4px;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 1. 顶部控制栏
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        top_layout.addWidget(QLabel("目标 IP / 种子 IP:", self))
        self.ip_edit = LineEdit(self)
        self.ip_edit.setText(self.seed_ip)
        self.ip_edit.setFixedWidth(160)
        self.ip_edit.setPlaceholderText("输入 IPv4 地址，如 172.64.229.1")
        self.ip_edit.textChanged.connect(self._on_ip_input_changed)
        top_layout.addWidget(self.ip_edit)

        self.lbl_seg_info = QLabel(f"({self.c_segment_name})", self)
        self.lbl_seg_info.setStyleSheet("color: #38bdf8; font-size: 12px;")
        top_layout.addWidget(self.lbl_seg_info)

        top_layout.addWidget(QLabel("端口:", self))
        self.port_edit = LineEdit(self)
        self.port_edit.setText(str(self.seed_port))
        self.port_edit.setFixedWidth(65)
        top_layout.addWidget(self.port_edit)

        top_layout.addWidget(QLabel("延迟门槛(≤ ms):", self))
        self.threshold_edit = LineEdit(self)
        self.threshold_edit.setText("130")
        self.threshold_edit.setFixedWidth(65)
        top_layout.addWidget(self.threshold_edit)

        self.lbl_status = QLabel(f"准备就绪 (共 {len(self.c_ips)} 个 IP)", self)
        self.lbl_status.setStyleSheet("color: #8d98af;")
        top_layout.addWidget(self.lbl_status)

        top_layout.addStretch()

        self.btn_sel_all = PushButton("全选达标", self)
        self.btn_sel_all.clicked.connect(self._select_all_rows)
        top_layout.addWidget(self.btn_sel_all)

        self.btn_sel_none = PushButton("清空选择", self)
        self.btn_sel_none.clicked.connect(self._clear_selection)
        top_layout.addWidget(self.btn_sel_none)

        layout.addLayout(top_layout)

        # 2. 中间结果表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(28)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        layout.addWidget(self.table)

        # 3. 底部操作栏
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.btn_start = PrimaryPushButton("🚀 开始极速挖掘", self)
        self.btn_start.clicked.connect(self._start_mining)
        bottom_layout.addWidget(self.btn_start)

        self.btn_stop = PushButton("⏹ 停止", self)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_mining)
        bottom_layout.addWidget(self.btn_stop)

        bottom_layout.addStretch()

        self.btn_import_pending = PushButton("📥 导入【⚪ 活跃待测池】", self)
        self.btn_import_pending.clicked.connect(lambda: self._import_to_pool("pending"))
        bottom_layout.addWidget(self.btn_import_pending)

        self.btn_import_fav = PushButton("📥 导入【⭐ 优质精选池】", self)
        self.btn_import_fav.clicked.connect(lambda: self._import_to_pool("fav"))
        bottom_layout.addWidget(self.btn_import_fav)

        self.btn_import_verified = PushButton("📥 导入【⏳ 沉淀孵化池】", self)
        self.btn_import_verified.clicked.connect(lambda: self._import_to_pool("verified"))
        bottom_layout.addWidget(self.btn_import_verified)

        self.btn_import_stars = PushButton("📥 导入【🏆 典藏管理池】", self)
        self.btn_import_stars.clicked.connect(lambda: self._import_to_pool("stars"))
        bottom_layout.addWidget(self.btn_import_stars)

        layout.addLayout(bottom_layout)

    def _select_all_rows(self):
        """全选所有真正属于 Cloudflare 的达标行"""
        self.table.clearSelection()
        for row_idx, r in enumerate(self._current_results):
            if r.get("status") == "✅ 极速达标":
                self.table.selectRow(row_idx)

    def _clear_selection(self):
        self.table.clearSelection()

    def _on_ip_input_changed(self, text: str):
        ip = text.strip()
        parts = ip.split(".")
        if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
            seg = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            self.lbl_seg_info.setText(f"({seg})")
        else:
            self.lbl_seg_info.setText("(无效 IP 格式)")

    def _start_mining(self):
        if self.worker and self.worker.isRunning():
            return

        target_ip = self.ip_edit.text().strip()
        m = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3})$", target_ip)
        if not m:
            InfoBar.warning("输入错误", "请输入合法的 IPv4 格式地址（如 172.64.229.1）！", parent=self)
            return

        # 动态重新生成 254 个 C 段 IP 列表
        self.c_ips = get_c_segment_ips(target_ip)
        self.c_segment_name = ".".join(target_ip.split(".")[:3]) + ".0/24"
        self.setWindowTitle(f"🔍 C 段全量极速深度挖掘 - {self.c_segment_name}")

        port_str = self.port_edit.text().strip()
        port = int(port_str) if port_str.isdigit() else 443
        th_str = self.threshold_edit.text().strip()
        threshold = int(th_str) if th_str.isdigit() else 130

        self.table.clearContents()
        self.table.setRowCount(0)
        self._current_results = []

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText("正在准备并发测延...")

        self.worker = CSegmentMinerWorker(self.c_ips, port=port, threshold=threshold, parent=self)
        self.worker.progress_signal.connect(self._on_worker_progress)
        self.worker.stage_signal.connect(self._on_worker_stage)
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.start()

    def _stop_mining(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.btn_stop.setEnabled(False)
            self.lbl_status.setText("正在中止扫描...")

    def _on_worker_progress(self, done: int, total: int):
        self.lbl_status.setText(f"TCP 测延中: {done}/{total}")

    def _on_worker_stage(self, stage_text: str):
        self.lbl_status.setText(stage_text)

    def _on_worker_finished(self, results: list):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._current_results = list(results)

        self.table.clearContents()
        self.table.setRowCount(len(results))

        for row_idx, r in enumerate(results):
            ip_item = QTableWidgetItem(r.get("ip", ""))
            ip_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, ip_item)

            port_item = QTableWidgetItem(str(r.get("port", 443)))
            port_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 1, port_item)

            delay_item = QTableWidgetItem(r.get("delay_str", ""))
            delay_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            delay_item.setForeground(QBrush(QColor("#38bdf8")))
            self.table.setItem(row_idx, 2, delay_item)

            colo_item = QTableWidgetItem(r.get("colo", "-"))
            colo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, colo_item)

            status_item = QTableWidgetItem(r.get("status", ""))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color = "#34d399" if r.get("status") == "✅ 极速达标" else "#f87171"
            status_item.setForeground(QBrush(QColor(color)))
            self.table.setItem(row_idx, 4, status_item)

        valid_cnt = sum(1 for r in results if r.get("status") == "✅ 极速达标")
        self.lbl_status.setText(f"挖掘完成！共发现 {valid_cnt} 个极速达标 IP")

    def _get_target_rows(self) -> list[dict]:
        """获取需要导入的行数据（自动过滤掉非 CF 节点，确保流入池中的都是可用代理）"""
        if not self._current_results:
            return []

        selected_row_indices = sorted({idx.row() for idx in self.table.selectedIndexes()})
        if selected_row_indices:
            candidates = [self._current_results[i] for i in selected_row_indices if i < len(self._current_results)]
        else:
            candidates = list(self._current_results)

        # 强力阻断非 CF 节点流入优质池
        valid_targets = [r for r in candidates if r.get("status") == "✅ 极速达标"]
        return valid_targets

    def _import_to_pool(self, target: str):
        """导入至指定目标池"""
        if self.worker and self.worker.isRunning():
            self._stop_mining()
            time.sleep(0.2)

        rows_to_import = self._get_target_rows()
        if not rows_to_import:
            InfoBar.warning(
                title="提示",
                content="当前无挖掘结果可导入！请先点击开始挖掘。",
                duration=3000,
                parent=self,
            )
            return

        if not self.controller:
            return

        now_ts = time.time()
        cnt = 0
        pool_names = {
            "fav": "【⭐ 优质精选池】",
            "verified": "【⏳ 沉淀孵化池】",
            "stars": "【🏆 典藏管理池】",
            "pending": "【⚪ 活跃待测池】",
        }
        target_name = pool_names.get(target, "目标池")

        pending_items_to_send = []
        if target == "pending":
            with self.controller.state.lock:
                for r in rows_to_import:
                    ip = r.get("ip", "")
                    port = r.get("port", 443)
                    ep = f"{ip}:{port}"
                    colo = r.get("colo", "亚洲")
                    rem = f"{colo} [C段挖掘待测]"
                    pending_items_to_send.append((ep, rem))
                    self.controller.state.local_blacklist.discard(ep)
                    self.controller.state.speed_blacklist.discard(ep)
                    cnt += 1
        else:
            with self.controller.state.lock:
                for r in rows_to_import:
                    ip = r.get("ip", "")
                    port = r.get("port", 443)
                    ep = f"{ip}:{port}"
                    colo = r.get("colo", "-")
                    delay = r.get("delay", 0)
                    rem = f"{colo} [C段挖掘]"

                    if target == "fav":
                        self.controller.state.favorites.add(ep)
                        self.controller.state.fav_reasons[ep] = "C段深度挖掘"
                        if delay > 0:
                            self.controller.state.node_delays[ep] = delay
                            hist = self.controller.state.node_history.setdefault(ep, [])
                            hist.append(delay)
                            self.controller.state.node_history[ep] = hist[-6:]
                        if colo and colo != "-":
                            self.controller.state.node_colo[ep] = colo
                        self.controller.state.local_blacklist.discard(ep)
                        self.controller.state.speed_blacklist.discard(ep)
                        self.controller.state.cloud_endpoints[ep] = rem
                        if ":" in ep:
                            self.controller.state.cloud_endpoints[ep.split(":")[0]] = rem
                        self.controller.state.auto_endpoints.add(ep)
                        cnt += 1

                    elif target == "verified":
                        if ep not in self.controller.state.verified_nodes:
                            self.controller.state.verified_nodes[ep] = {
                                "endpoint": ep,
                                "colo": colo,
                                "remark": rem,
                                "first_seen": now_ts,
                                "passes": 1,
                                "fails": 0,
                                "delay": delay,
                                "speed": 0.0,
                                "reason": "C段深度挖掘入孵",
                            }
                            cnt += 1

                    elif target == "stars":
                        existing_eps = {s.get("endpoint", "") for s in self.controller.state.stars_nodes}
                        if ep not in existing_eps:
                            self.controller.state.stars_nodes.append({
                                "endpoint": ep,
                                "colo": colo,
                                "remark": rem,
                                "delay": delay,
                                "speed": 0.0,
                                "matched_name": "",
                                "reason": "C段深度挖掘加冕",
                            })
                            cnt += 1

        # 保存快照并记录日志
        self.controller.save_config(self.controller.get_state_snapshot())
        self.controller.log(f"📥 C 段挖掘: 已收录 {cnt} 个达标 IP 到 {target_name}")

        # 启动 PostImportWorker 统一执行 4 步全链路热更闭环
        self._post_worker = PostImportWorker(self.controller, target, cnt, parent=self)
        if target == "pending":
            self._post_worker.pending_items = pending_items_to_send

        progress_dialog = QProgressDialog("正在执行热更闭环处理...", "取消", 0, 0, self)
        progress_dialog.setWindowTitle("同步推进中")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.setStyleSheet("""
            QProgressDialog {
                background-color: #1a1d29;
                color: #e2e8f0;
            }
            QLabel {
                color: #38bdf8;
                font-size: 13px;
            }
        """)

        def _on_step(msg):
            progress_dialog.setLabelText(msg)

        def _on_post_finished(success, message, steps):
            progress_dialog.close()
            dlg_detail = "\n".join(steps)
            if success:
                MessageBox("收编与热更完成", f"{message}\n\n执行明细:\n{dlg_detail}", self).exec()
            else:
                MessageBox("热更过程提示", f"{message}\n\n执行明细:\n{dlg_detail}", self).exec()
            # 若导入的是精选、孵化或典藏，顺手触发一次云端待测池大扫除，清除已收编的端点
            if target != "pending":
                import threading
                threading.Thread(target=self.controller.purge_pending_endpoints_from_cloud, daemon=True).start()

        self._post_worker.step_signal.connect(_on_step)
        self._post_worker.finished_signal.connect(_on_post_finished)
        self._post_worker.start()
        progress_dialog.exec()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(500)
        if hasattr(self, "_post_worker") and self._post_worker and self._post_worker.isRunning():
            self._post_worker.wait(2000)
        super().closeEvent(event)

```

```python
File: gui_fluent/widgets/node_table.py
"""
通用节点表格组件 (NodeTableView)
支持 11 列完整信息展示、状态高亮着色、智能列排序与鼠标拖选多行
"""
import re
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, QItemSelection, QItemSelectionModel
    from PyQt5.QtGui import QColor, QBrush, QFont
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
    )
else:
    from PyQt6.QtCore import Qt, QItemSelection, QItemSelectionModel
    from PyQt6.QtGui import QColor, QBrush, QFont
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
    )

from qfluentwidgets import RoundMenu, Action, FluentIcon, InfoBar


class DragSelectTableWidget(QTableWidget):
    """
    增强型 QTableWidget：支持鼠标按住左键直接上下拖拽滑动多选行
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start_row = -1

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_row = self.rowAt(event.pos().y())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self._drag_start_row >= 0:
            curr_row = self.rowAt(event.pos().y())
            if curr_row >= 0:
                start = min(self._drag_start_row, curr_row)
                end = max(self._drag_start_row, curr_row)
                selection = QItemSelection(
                    self.model().index(start, 0),
                    self.model().index(end, self.columnCount() - 1),
                )
                self.selectionModel().select(
                    selection,
                    QItemSelectionModel.SelectionFlag.ClearAndSelect
                    | QItemSelectionModel.SelectionFlag.Rows,
                )
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_row = -1
        super().mouseReleaseEvent(event)


class NodeTableView(QWidget):
    """
    通用节点表格视图：适用于 活跃待测 / 优质精选 / 延迟黑名单 / 低速黑名单
    """

    COLUMN_KEYS = [
        "status",
        "colo",
        "colo_hist",
        "reason",
        "delay",
        "avg_delay",
        "delay_hist",
        "hist_avg",
        "speed",
        "speed_hist",
        "endpoint",
        "name",
    ]

    COLUMN_HEADERS = [
        "状态",
        "最新Colo",
        "Colo稳定性(7天)",
        "入选/拉黑原因",
        "最新延迟",
        "本轮均值",
        "延迟轨迹(轮数)",
        "历史均值/稳定度",
        "最新下行",
        "下行轨迹(近4次)",
        "IP:端口",
        "节点名称",
    ]

    COLUMN_WIDTHS = [90, 80, 150, 160, 75, 85, 120, 140, 75, 120, 140, 260]

    def __init__(self, parent=None, controller=None, page_type: str = "active"):
        super().__init__(parent)
        self.controller = controller
        self.page_type = page_type
        self._sort_col = -1
        self._sort_asc = True
        self._raw_rows = []
        self.init_ui()

    def set_controller(self, controller, page_type: str = "active"):
        """绑定控制器与当前页面类型"""
        self.controller = controller
        self.page_type = page_type

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = DragSelectTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        # 样式设定：深色风格
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #181b26;
                color: #e2e8f0;
                gridline-color: rgba(255, 255, 255, 0.06);
                border: none;
                selection-background-color: #28334a;
                selection-color: #ffffff;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1e2230;
                color: #8d98af;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QTableCornerButton::section {
                background-color: #1e2230;
                border: none;
            }
            QScrollBar:vertical {
                background: #181b26;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)

        # 预设初始列宽
        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        # 开启右键上下文菜单策略
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

    def populate(self, rows: list[dict]):
        """
        填充表格数据
        rows 为字典列表，每个字典包含 COLUMN_KEYS 中的字段
        """
        self._raw_rows = list(rows)
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            status_text = str(row_data.get("status", ""))
            delay_text = str(row_data.get("delay", ""))

            # 颜色规则
            if "优质精选" in status_text or "云端已保活" in status_text:
                row_color = QColor("#38bdf8")
            elif "活跃待测" in status_text:
                row_color = QColor("#e2e8f0")
            elif ("黑名单" in status_text) or ("拉黑" in status_text) or ("超时" in status_text) or ("超时" in delay_text) or ("淘汰" in status_text):
                row_color = QColor("#f87171")
            elif "缺失" in status_text:
                row_color = QColor("#fbbf24")
            else:
                row_color = QColor("#94a3b8")

            node_name = str(row_data.get("raw_name", row_data.get("name", "")))
            ep_val = str(row_data.get("endpoint", row_data.get("IP:端口", "")))
            if not ep_val or ep_val == "-":
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", node_name)
                if m:
                    ep_val = m.group(1)

            for col_idx, key in enumerate(self.COLUMN_KEYS):
                val_str = str(row_data.get(key, "-"))
                item = QTableWidgetItem(val_str)
                item.setForeground(QBrush(row_color))

                # 对齐方式：除最后一列“节点名称”靠左居中外，其余全部水平居中
                if key == "name":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # 将原始节点名称与端点绑定到每一行首列的 UserRole
                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, node_name)
                    item.setData(Qt.ItemDataRole.UserRole + 1, ep_val)

                self.table.setItem(row_idx, col_idx, item)

    def get_selected_node_names(self) -> list[str]:
        """
        获取当前选中行的节点名称列表
        """
        selected_names = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                name = item.data(Qt.ItemDataRole.UserRole)
                if name and name not in ["", "无", "-"]:
                    selected_names.append(name)
                else:
                    ep = item.data(Qt.ItemDataRole.UserRole + 1)
                    if ep and ep not in ["", "-"]:
                        selected_names.append(ep)
                    else:
                        name_item = self.table.item(r, len(self.COLUMN_KEYS) - 1)
                        if name_item and name_item.text().strip() not in ["", "无", "-"]:
                            selected_names.append(name_item.text().strip())
        return selected_names

    def get_selected_endpoints(self) -> list[str]:
        """
        获取当前选中行的物理端点 (IP:Port) 列表
        """
        selected_eps = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                ep = item.data(Qt.ItemDataRole.UserRole + 1)
                if ep and ep not in ["", "-"]:
                    selected_eps.append(ep)
                else:
                    col_ep = self.COLUMN_KEYS.index("endpoint") if "endpoint" in self.COLUMN_KEYS else -1
                    if col_ep >= 0:
                        ep_item = self.table.item(r, col_ep)
                        if ep_item and ep_item.text().strip() not in ["", "-"]:
                            selected_eps.append(ep_item.text().strip())
                            continue
                    name = item.data(Qt.ItemDataRole.UserRole)
                    if hasattr(self, "controller") and self.controller:
                        ep_res = self.controller.get_node_endpoint(name)
                        if ep_res:
                            selected_eps.append(ep_res)
                    else:
                        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", str(name))
                        if m:
                            selected_eps.append(m.group(1))
        return selected_eps

    def _copy_to_clipboard(self, items: list[str], label: str = "内容"):
        """复制内容至系统剪贴板"""
        if not items:
            return
        text = "\n".join(str(x) for x in items if str(x).strip())
        QApplication.clipboard().setText(text)
        InfoBar.success(
            title="已复制到剪贴板",
            content=f"已成功复制 {len(items)} 条{label}",
            duration=2000,
            parent=self.window(),
        )

    def _show_context_menu(self, pos):
        """弹出 Fluent 风格圆角右键悬浮菜单"""
        item_at = self.table.itemAt(pos)
        if not item_at:
            return
        clicked_row = item_at.row()
        selected_rows = {idx.row() for idx in self.table.selectedIndexes()}
        if clicked_row not in selected_rows:
            self.table.clearSelection()
            self.table.selectRow(clicked_row)

        selected_nodes = self.get_selected_node_names()
        if not selected_nodes:
            return

        selected_endpoints = self.get_selected_endpoints()
        cnt = len(selected_nodes)

        menu = RoundMenu(parent=self)

        # 1. 基础剪贴板复制
        copy_name_action = Action(FluentIcon.COPY, f"复制节点名称 ({cnt}项)", self)
        copy_name_action.triggered.connect(lambda: self._copy_to_clipboard(selected_nodes, "节点名称"))
        menu.addAction(copy_name_action)

        if selected_endpoints:
            copy_ep_action = Action(FluentIcon.SHARE, f"复制物理端点 ({len(selected_endpoints)}项)", self)
            copy_ep_action.triggered.connect(lambda: self._copy_to_clipboard(selected_endpoints, "物理端点"))
            menu.addAction(copy_ep_action)

        menu.addSeparator()

        # 2. 业务操作
        if self.controller:
            test_delay_action = Action(FluentIcon.WIFI, f"⚡ 立即测延迟 ({cnt}项)", self)
            test_delay_action.triggered.connect(lambda: self.controller.test_nodes_delay(selected_nodes))
            menu.addAction(test_delay_action)

            colo_action = Action(getattr(FluentIcon, "EARTH", FluentIcon.GLOBE), "🌍 测当前 Colo", self)
            colo_action.triggered.connect(lambda: self.controller.test_nodes_colo(selected_nodes))
            menu.addAction(colo_action)

            # 补充 C 段挖掘功能
            mine_action = Action(FluentIcon.SEARCH, "🔍 C段挖掘", self)
            mine_action.triggered.connect(lambda: self.controller.mine_c_subnet(selected_nodes))
            menu.addAction(mine_action)

            p_type = getattr(self, "page_type", "active")
            if p_type == "active":
                fav_action = Action(FluentIcon.HEART, "⭐ 设为优质精选", self)
                fav_action.triggered.connect(lambda: self.controller.move_nodes_to_favorites(selected_nodes))
                menu.addAction(fav_action)

                star_action = Action(FluentIcon.ACCEPT, "🏆 晋升至典藏常青", self)
                star_action.triggered.connect(lambda: self.controller.promote_nodes_to_stars(selected_nodes))
                menu.addAction(star_action)

                menu.addSeparator()

                delay_bl_action = Action(FluentIcon.CANCEL, "🚫 延迟拉黑", self)
                delay_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "右键手动拉黑", "delay"))
                menu.addAction(delay_bl_action)

                speed_bl_action = Action(FluentIcon.REMOVE, "🐢 低速拉黑", self)
                speed_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "右键手动拉黑", "speed"))
                menu.addAction(speed_bl_action)

            elif p_type == "favorites":
                star_action = Action(FluentIcon.ACCEPT, "🏆 晋升至典藏常青", self)
                star_action.triggered.connect(lambda: self.controller.promote_nodes_to_stars(selected_nodes))
                menu.addAction(star_action)

                ver_action = Action(FluentIcon.SYNC, "⏳ 纳入沉淀孵化池", self)
                ver_action.triggered.connect(lambda: self.controller.sync_favorites_to_verified())
                menu.addAction(ver_action)

                menu.addSeparator()

                remove_fav_action = Action(FluentIcon.DELETE, "🗑️ 移出精选池", self)
                remove_fav_action.triggered.connect(lambda: self.controller.remove_nodes_from_favorites(selected_nodes))
                menu.addAction(remove_fav_action)

                delay_bl_action = Action(FluentIcon.CANCEL, "🚫 延迟拉黑", self)
                delay_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "从精选池手动拉黑", "delay"))
                menu.addAction(delay_bl_action)

                speed_bl_action = Action(FluentIcon.REMOVE, "🐢 低速拉黑", self)
                speed_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "从精选池手动拉黑", "speed"))
                menu.addAction(speed_bl_action)

            elif p_type in ["delay_black", "speed_black"]:
                unbl_action = Action(FluentIcon.SYNC, "♻️ 移出黑名单 (恢复待测)", self)
                unbl_action.triggered.connect(lambda: self.controller.remove_nodes_from_blacklist(selected_nodes))
                menu.addAction(unbl_action)

                fav_action = Action(FluentIcon.HEART, "⭐ 破格设为优质", self)
                fav_action.triggered.connect(lambda: self.controller.move_nodes_to_favorites(selected_nodes))
                menu.addAction(fav_action)

                menu.addSeparator()

                if p_type == "delay_black":
                    to_speed_action = Action(FluentIcon.REMOVE, "🐢 转为低速拉黑", self)
                    to_speed_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "转为低速黑名单", "speed"))
                    menu.addAction(to_speed_action)
                else:
                    to_delay_action = Action(FluentIcon.CANCEL, "🚫 转为延迟拉黑", self)
                    to_delay_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "转为延迟黑名单", "delay"))
                    menu.addAction(to_delay_action)

        menu.exec(self.table.mapToGlobal(pos))

    def _on_header_clicked(self, col: int):
        """
        点击列标题执行智能排序（区分数值与字符串）
        """
        if not self._raw_rows:
            return

        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        key = self.COLUMN_KEYS[col]
        is_numeric = key in ["delay", "avg_delay", "hist_avg", "speed"]

        def _sort_key(row_dict):
            val = str(row_dict.get(key, ""))
            if is_numeric:
                if not val or val == "-" or "超时" in val or "失败" in val:
                    return float("inf") if self._sort_asc else float("-inf")
                m = re.search(r"[-+]?\d*\.?\d+", val)
                return float(m.group()) if m else (float("inf") if self._sort_asc else float("-inf"))
            return val.lower()

        sorted_rows = sorted(self._raw_rows, key=_sort_key, reverse=not self._sort_asc)
        self.populate(sorted_rows)

```

```python
File: gui_fluent/widgets/stars_table.py
"""
典藏管理池表格组件 (StarsTableView)
展示 8 列核心长青节点数据，支持双击编辑信号触发与智能排序
"""
import re
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, pyqtSignal, QItemSelection, QItemSelectionModel
    from PyQt5.QtGui import QColor, QBrush
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QInputDialog,
    )
else:
    from PyQt6.QtCore import Qt, pyqtSignal, QItemSelection, QItemSelectionModel
    from PyQt6.QtGui import QColor, QBrush
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QInputDialog,
    )

from qfluentwidgets import RoundMenu, Action, FluentIcon, InfoBar, MessageBox
from gui_fluent.widgets.node_table import DragSelectTableWidget


class StarsTableView(QWidget):
    """
    典藏管理池表格组件
    """

    double_clicked = pyqtSignal(str)

    COLUMN_KEYS = [
        "endpoint",
        "colo",
        "colo_hist",
        "reason",
        "remark",
        "delay",
        "speed",
        "match",
    ]

    COLUMN_HEADERS = [
        "IP:端口",
        "最新Colo",
        "Colo稳定性(7天)",
        "典藏入选原因",
        "备注信息 (可双击修改)",
        "最新延迟",
        "最新下行",
        "本地订阅关联状态",
    ]

    COLUMN_WIDTHS = [130, 85, 150, 190, 200, 75, 85, 250]

    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self._sort_col = -1
        self._sort_asc = True
        self._raw_rows = []
        self.init_ui()

    def set_controller(self, controller):
        """绑定控制器"""
        self.controller = controller

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = DragSelectTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #181b26;
                color: #e2e8f0;
                gridline-color: rgba(255, 255, 255, 0.06);
                border: none;
                selection-background-color: #28334a;
                selection-color: #ffffff;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1e2230;
                color: #8d98af;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QTableCornerButton::section {
                background-color: #1e2230;
                border: none;
            }
            QScrollBar:vertical {
                background: #181b26;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)

        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        # 开启右键上下文菜单策略
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

    def _copy_to_clipboard(self, items: list[str], label: str = "内容"):
        """复制内容至系统剪贴板"""
        if not items:
            return
        text = "\n".join(str(x) for x in items if str(x).strip())
        QApplication.clipboard().setText(text)
        InfoBar.success(
            title="已复制到剪贴板",
            content=f"已成功复制 {len(items)} 条{label}",
            duration=2000,
            parent=self.window(),
        )

    def _edit_remark(self, ep: str):
        """弹出修改备注输入框"""
        if not ep or not self.controller:
            return
        text, ok = QInputDialog.getText(self, "修改备注", f"修改典藏节点 [{ep}] 的备注信息:")
        if ok and text is not None:
            self.controller.update_star_remark(ep, text.strip())

    def _confirm_delete(self, eps: list[str]):
        """删除选中典藏节点确认"""
        if not eps or not self.controller:
            return
        w = MessageBox("删除确认", f"确定从本地典藏池移除选中的 {len(eps)} 个节点吗？\n（注：点击保存推送前云端数据不会变动）", self.window())
        if w.exec():
            self.controller.delete_selected_stars(eps)

    def _show_context_menu(self, pos):
        """弹出 Fluent 风格圆角右键悬浮菜单"""
        item_at = self.table.itemAt(pos)
        if not item_at:
            return
        clicked_row = item_at.row()
        selected_rows = {idx.row() for idx in self.table.selectedIndexes()}
        if clicked_row not in selected_rows:
            self.table.clearSelection()
            self.table.selectRow(clicked_row)

        selected_eps = self.get_selected_endpoints()
        if not selected_eps:
            return

        cnt = len(selected_eps)
        menu = RoundMenu(parent=self)

        # 1. 剪贴板复制
        copy_ep_action = Action(FluentIcon.COPY, f"复制物理端点 ({cnt}项)", self)
        copy_ep_action.triggered.connect(lambda: self._copy_to_clipboard(selected_eps, "物理端点"))
        menu.addAction(copy_ep_action)

        if cnt == 1:
            edit_action = Action(FluentIcon.EDIT, "✏️ 修改备注信息", self)
            edit_action.triggered.connect(lambda: self._edit_remark(selected_eps[0]))
            menu.addAction(edit_action)

        menu.addSeparator()

        # 2. 业务操作
        if self.controller:
            test_delay_action = Action(FluentIcon.WIFI, f"⚡ 测选中延迟 ({cnt}项)", self)
            test_delay_action.triggered.connect(lambda: self.controller.test_stars_pipeline(mode="delay", endpoints=selected_eps))
            menu.addAction(test_delay_action)

            test_speed_action = Action(FluentIcon.SYNC, f"🚀 测选中下行速度 ({cnt}项)", self)
            test_speed_action.triggered.connect(lambda: self.controller.test_stars_pipeline(mode="speed", endpoints=selected_eps))
            menu.addAction(test_speed_action)

            colo_action = Action(getattr(FluentIcon, "EARTH", FluentIcon.GLOBE), "🌍 测当前 Colo", self)
            colo_action.triggered.connect(lambda: self.controller.test_nodes_colo(selected_eps))
            menu.addAction(colo_action)

            # 补充 C 段挖掘功能
            mine_action = Action(FluentIcon.SEARCH, "🔍 C段挖掘", self)
            mine_action.triggered.connect(lambda: self.controller.mine_c_subnet(selected_eps))
            menu.addAction(mine_action)

            menu.addSeparator()

            del_action = Action(FluentIcon.DELETE, f"🗑️ 从典藏池移除 ({cnt}项)", self)
            del_action.triggered.connect(lambda: self._confirm_delete(selected_eps))
            menu.addAction(del_action)

        menu.exec(self.table.mapToGlobal(pos))

    def populate(self, rows: list[dict]):
        self._raw_rows = list(rows)
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            match_text = str(row_data.get("match", ""))
            delay_text = str(row_data.get("delay", ""))
            ep = str(row_data.get("endpoint", ""))

            # 颜色规则
            if ("未匹配" in match_text) or ("离线" in match_text) or ("已下线" in match_text):
                row_color = QColor("#94a3b8")
            elif "超时" in delay_text:
                row_color = QColor("#f87171")
            elif ep:
                row_color = QColor("#38bdf8")
            else:
                row_color = QColor("#94a3b8")

            for col_idx, key in enumerate(self.COLUMN_KEYS):
                val_str = str(row_data.get(key, "-"))
                item = QTableWidgetItem(val_str)
                item.setForeground(QBrush(row_color))

                if key in ["remark", "match"]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, ep)

                self.table.setItem(row_idx, col_idx, item)

    def get_selected_endpoints(self) -> list[str]:
        endpoints = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                ep = item.data(Qt.ItemDataRole.UserRole)
                endpoints.append(ep if ep else item.text().strip())
        return endpoints

    def _on_cell_double_clicked(self, row: int, col: int):
        item = self.table.item(row, 0)
        if item:
            ep = item.data(Qt.ItemDataRole.UserRole)
            self.double_clicked.emit(ep if ep else item.text().strip())

    def _on_header_clicked(self, col: int):
        if not self._raw_rows:
            return

        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        key = self.COLUMN_KEYS[col]
        is_numeric = key in ["delay", "speed"]

        def _sort_key(row_dict):
            val = str(row_dict.get(key, ""))
            if is_numeric:
                if not val or val == "-" or "超时" in val:
                    return float("inf") if self._sort_asc else float("-inf")
                m = re.search(r"[-+]?\d*\.?\d+", val)
                return float(m.group()) if m else (float("inf") if self._sort_asc else float("-inf"))
            return val.lower()

        sorted_rows = sorted(self._raw_rows, key=_sort_key, reverse=not self._sort_asc)
        self.populate(sorted_rows)

```

```python
File: gui_fluent/widgets/verified_table.py
"""
沉淀孵化池表格组件 (VerifiedTableView)
展示 10 列信息：端点、机房、7天稳定性、考核状态、存活时长与订阅关联
"""
import re
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, QItemSelection, QItemSelectionModel
    from PyQt5.QtGui import QColor, QBrush
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
    )
else:
    from PyQt6.QtCore import Qt, QItemSelection, QItemSelectionModel
    from PyQt6.QtGui import QColor, QBrush
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
    )

from qfluentwidgets import RoundMenu, Action, FluentIcon, InfoBar

from gui_fluent.widgets.node_table import DragSelectTableWidget


class VerifiedTableView(QWidget):
    """
    沉淀孵化池表格组件
    """

    COLUMN_KEYS = [
        "endpoint",
        "colo",
        "colo_hist",
        "reason",
        "remark",
        "delay",
        "speed",
        "time",
        "stats",
        "match",
    ]

    COLUMN_HEADERS = [
        "IP:端口",
        "最新Colo",
        "Colo稳定性(7天)",
        "入孵原因 / 考核状态",
        "备注信息",
        "最新延迟",
        "最新下行",
        "存活时长",
        "考核统计",
        "本地订阅关联",
    ]

    COLUMN_WIDTHS = [125, 85, 150, 170, 155, 75, 80, 90, 130, 220]

    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self._sort_col = -1
        self._sort_asc = True
        self._raw_rows = []
        self.init_ui()

    def set_controller(self, controller):
        """绑定控制器"""
        self.controller = controller

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = DragSelectTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #181b26;
                color: #e2e8f0;
                gridline-color: rgba(255, 255, 255, 0.06);
                border: none;
                selection-background-color: #28334a;
                selection-color: #ffffff;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1e2230;
                color: #8d98af;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QTableCornerButton::section {
                background-color: #1e2230;
                border: none;
            }
            QScrollBar:vertical {
                background: #181b26;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)

        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        # 开启右键上下文菜单策略
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

    def _copy_to_clipboard(self, items: list[str], label: str = "内容"):
        """复制内容至系统剪贴板"""
        if not items:
            return
        text = "\n".join(str(x) for x in items if str(x).strip())
        QApplication.clipboard().setText(text)
        InfoBar.success(
            title="已复制到剪贴板",
            content=f"已成功复制 {len(items)} 条{label}",
            duration=2000,
            parent=self.window(),
        )

    def _show_context_menu(self, pos):
        """弹出 Fluent 风格圆角右键悬浮菜单"""
        item_at = self.table.itemAt(pos)
        if not item_at:
            return
        clicked_row = item_at.row()
        selected_rows = {idx.row() for idx in self.table.selectedIndexes()}
        if clicked_row not in selected_rows:
            self.table.clearSelection()
            self.table.selectRow(clicked_row)

        selected_eps = self.get_selected_endpoints()
        if not selected_eps:
            return

        selected_names = self.get_selected_node_names()
        cnt = len(selected_eps)

        menu = RoundMenu(parent=self)

        # 1. 剪贴板复制
        copy_ep_action = Action(FluentIcon.COPY, f"复制物理端点 ({cnt}项)", self)
        copy_ep_action.triggered.connect(lambda: self._copy_to_clipboard(selected_eps, "物理端点"))
        menu.addAction(copy_ep_action)

        valid_names = [n for n in selected_names if n]
        if valid_names:
            copy_name_action = Action(FluentIcon.SHARE, f"复制关联节点名 ({len(valid_names)}项)", self)
            copy_name_action.triggered.connect(lambda: self._copy_to_clipboard(valid_names, "节点名称"))
            menu.addAction(copy_name_action)

        menu.addSeparator()

        # 2. 业务操作
        if self.controller:
            test_targets = valid_names if valid_names else selected_eps
            test_delay_action = Action(FluentIcon.WIFI, f"⚡ 立即测延迟 ({len(test_targets)}项)", self)
            test_delay_action.triggered.connect(lambda: self.controller.test_nodes_delay(test_targets))
            menu.addAction(test_delay_action)

            colo_action = Action(getattr(FluentIcon, "EARTH", FluentIcon.GLOBE), "🌍 测当前 Colo", self)
            colo_action.triggered.connect(lambda: self.controller.test_nodes_colo(test_targets))
            menu.addAction(colo_action)

            # 补充 C 段挖掘功能
            mine_action = Action(FluentIcon.SEARCH, "🔍 C段挖掘", self)
            mine_action.triggered.connect(lambda: self.controller.mine_c_subnet(selected_eps))
            menu.addAction(mine_action)

            promote_action = Action(FluentIcon.ACCEPT, f"🏆 提前加冕至典藏常青池 ({cnt}项)", self)
            promote_action.triggered.connect(lambda: self.controller.force_promote_verified_to_stars(selected_eps))
            menu.addAction(promote_action)

            menu.addSeparator()

            remove_action = Action(FluentIcon.DELETE, f"🗑️ 从沉淀池移出 ({cnt}项)", self)
            remove_action.triggered.connect(lambda: self.controller.delete_selected_verified(selected_eps))
            menu.addAction(remove_action)

            bl_action = Action(FluentIcon.CANCEL, f"🚫 延迟拉黑并移出 ({cnt}项)", self)
            bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_eps, "从孵化池手动拉黑", "delay"))
            menu.addAction(bl_action)

        menu.exec(self.table.mapToGlobal(pos))

    def populate(self, rows: list[dict]):
        self._raw_rows = list(rows)
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            reason_text = str(row_data.get("reason", ""))
            delay_text = str(row_data.get("delay", ""))

            # 颜色规则
            if ("已验证" in reason_text) or ("达标" in reason_text) or ("留任" in reason_text):
                row_color = QColor("#34d399")
            elif ("黑名单" in reason_text) or ("拉黑" in reason_text) or ("超时" in delay_text):
                row_color = QColor("#f87171")
            else:
                row_color = QColor("#94a3b8")

            ep = str(row_data.get("endpoint", ""))
            matched_name = str(row_data.get("match", ""))

            for col_idx, key in enumerate(self.COLUMN_KEYS):
                val_str = str(row_data.get(key, "-"))
                item = QTableWidgetItem(val_str)
                item.setForeground(QBrush(row_color))

                if key in ["remark", "match"]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, ep)
                    item.setData(Qt.ItemDataRole.UserRole + 1, matched_name)

                self.table.setItem(row_idx, col_idx, item)

    def get_selected_endpoints(self) -> list[str]:
        endpoints = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                ep = item.data(Qt.ItemDataRole.UserRole)
                endpoints.append(ep if ep else item.text().strip())
        return endpoints

    def get_selected_node_names(self) -> list[str]:
        names = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                n = item.data(Qt.ItemDataRole.UserRole + 1)
                names.append(n if n else "")
        return names

    def _on_header_clicked(self, col: int):
        if not self._raw_rows:
            return

        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        key = self.COLUMN_KEYS[col]
        is_numeric = key in ["delay", "speed", "time"]

        def _sort_key(row_dict):
            val = str(row_dict.get(key, ""))
            if is_numeric:
                if not val or val == "-" or "超时" in val:
                    return float("inf") if self._sort_asc else float("-inf")
                m = re.search(r"[-+]?\d*\.?\d+", val)
                return float(m.group()) if m else (float("inf") if self._sort_asc else float("-inf"))
            return val.lower()

        sorted_rows = sorted(self._raw_rows, key=_sort_key, reverse=not self._sort_asc)
        self.populate(sorted_rows)

```

```python
File: gui_fluent/widgets/__init__.py
"""
自定义 Fluent 风格小部件模块
"""
from gui_fluent.widgets.node_table import NodeTableView
from gui_fluent.widgets.verified_table import VerifiedTableView
from gui_fluent.widgets.stars_table import StarsTableView

__all__ = ["NodeTableView", "VerifiedTableView", "StarsTableView"]

```

