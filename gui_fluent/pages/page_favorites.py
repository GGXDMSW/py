"""
优质精选页面
包含两行精选参数控制与操作工具栏 (FavToolBar) 以及核心节点表格 (NodeTableView)
"""
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
else:
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
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


class GoogleHkCheckWorker(QThread):
    progress_signal = pyqtSignal(str, int, int)      # (提示文本, 当前索引, 总数)
    finished_signal = pyqtSignal(bool, dict)         # (成功与否, 汇总统计字典)

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller

    def run(self):
        self.controller._is_checking_google_hk = True
        orig_selections = {}
        orig_global = ""
        nodes_to_test = []
        with self.controller.state.lock:
            nodes_to_test = list(self.controller.state.favorites)
        total = len(nodes_to_test)
        if total == 0:
            self.controller._is_checking_google_hk = False
            self.finished_signal.emit(False, {"msg": "当前精选池为空，无需核验"})
            return
        tagged_nodes = []
        untagged_nodes = []
        clean_nodes = []
        failed_nodes = []
        try:
            # 1. 记录原各策略组当前选中项
            proxies_map = self.controller.clash_client.get_proxies()
            for g_name, g_info in proxies_map.items():
                if g_info.get("type", "").lower() in ["selector", "fallback"]:
                    orig_selections[g_name] = g_info.get("now", "")
            orig_global = proxies_map.get("GLOBAL", {}).get("now", "")
            # 2. 构造本地代理客户端
            mix_port = self.controller.clash_client.get_mixed_port(default=7897)
            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mix_port}",
                "https": f"http://127.0.0.1:{mix_port}",
            })
            opener = urllib.request.build_opener(proxy_handler)
            # 3. 逐个切组探测 Google
            for idx, n in enumerate(nodes_to_test, 1):
                self.progress_signal.emit(f"正在核验 [{idx}/{total}]: {n[:22]}", idx, total)
                # 切 GLOBAL 策略组直连当前节点
                enc_glb = urllib.parse.quote("GLOBAL", safe="")
                self.controller.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": n})
                time.sleep(0.15)
                is_hk = False
                success = False
                try:
                    req = urllib.request.Request(
                        "https://www.google.com",
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    )
                    with opener.open(req, timeout=3.0) as resp:
                        final_url = resp.geturl()
                        is_hk = ("google.com.hk" in final_url) or ("sorry" in final_url)
                        success = True
                except urllib.error.HTTPError as he:
                    if he.code in (429, 403) or "sorry" in getattr(he, "url", "") or "google.com.hk" in getattr(he, "url", ""):
                        is_hk = True
                        success = True
                    else:
                        success = False
                except Exception:
                    success = False
                if not success:
                    failed_nodes.append(n)
                    continue
                ep = self.controller._get_ep(n) or n
                if is_hk:
                    # 遭遇送中：若尚未打标，则规范重命名注入 [送中]
                    if "[送中]" not in n:
                        m = re.search(r"([\d.]+\s*MB/s)", n)
                        new_name = f"{n[:m.start()]}[送中] {n[m.start():]}" if m else f"{n} [送中]"
                        with self.controller.state.lock:
                            orig_f = n
                            self.controller._migrate_node_name(orig_f, new_name, ep)
                            self.controller.state.fav_reasons[new_name] = "一键核验打标[送中]"
                        tagged_nodes.append(new_name)
                    else:
                        tagged_nodes.append(n)
                else:
                    # 原生洁净：若此前曾被标记 [送中]，自动摘标平反！
                    if "[送中]" in n:
                        clean_name = n.replace(" [送中]", "").replace("[送中] ", "").replace("[送中]", "").strip()
                        with self.controller.state.lock:
                            orig_f = n
                            self.controller._migrate_node_name(orig_f, clean_name, ep)
                            self.controller.state.fav_reasons[clean_name] = "一键核验摘标平反"
                        untagged_nodes.append(clean_name)
                    else:
                        clean_nodes.append(n)
        finally:
            # 4. 百分之百原样恢复各策略组初始状态
            for g_name, orig_choice in orig_selections.items():
                if orig_choice:
                    enc = urllib.parse.quote(g_name, safe="")
                    self.controller.clash_client.call_api(f"/proxies/{enc}", method="PUT", data={"name": orig_choice})
            if orig_global:
                enc_glb = urllib.parse.quote("GLOBAL", safe="")
                self.controller.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": orig_global})
            self.controller._is_checking_google_hk = False
        # 5. 若发生打标或摘标更名：触发存盘、Script.js 0ms热更与云端 Worker 异步推送
        if tagged_nodes or untagged_nodes:
            self.controller.save_config(self.controller.get_state_snapshot())
            self.controller.generate_script_and_reload()
            self.controller.push_favorites_to_cloud()
            self.controller.data_changed.emit()
        res = {
            "total": total,
            "tagged_count": len(tagged_nodes),
            "untagged_count": len(untagged_nodes),
            "clean_count": len(clean_nodes),
            "failed_count": len(failed_nodes),
            "tagged_nodes": tagged_nodes,
            "untagged_nodes": untagged_nodes,
        }
        self.finished_signal.emit(True, res)


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

        self.btn_check_google_hk = PushButton("🌐 一键送中核验", self)
        row1.addWidget(self.btn_check_google_hk)

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
        self.btn_check_google_hk = self.toolbar.btn_check_google_hk
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
        self.toolbar.btn_check_google_hk.clicked.connect(self._on_check_google_hk_clicked)
        self._hk_worker = None

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

    def _on_check_google_hk_clicked(self):
        if self.controller.is_pipeline_running():
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.warning("任务互斥", "当前已有流水线或核验任务在运行，请稍候！", parent=self, position=InfoBarPosition.TOP)
            return
        self.toolbar.btn_check_google_hk.setEnabled(False)
        self.toolbar.lbl_fav_sched_status.setText("状态: 正在核验送中...")
        self._hk_worker = GoogleHkCheckWorker(self.controller, self)
        self._hk_worker.progress_signal.connect(lambda msg, cur, tot: self.toolbar.lbl_fav_sched_status.setText(f"状态: [{cur}/{tot}] 核验中"))

        def _on_finished(success, res):
            self.toolbar.btn_check_google_hk.setEnabled(True)
            if not success:
                self.toolbar.lbl_fav_sched_status.setText("状态: 核验终止")
                return
            tot = res.get("total", 0)
            tagged = res.get("tagged_count", 0)
            untagged = res.get("untagged_count", 0)
            clean = res.get("clean_count", 0)
            self.toolbar.lbl_fav_sched_status.setText(f"状态: 送中核验完成 ({tagged}送中/{clean}洁净)")
            # 弹窗汇报详细核验结果
            from qfluentwidgets import MessageBox
            title = "🌐 Google 送中状态核验总结"
            content = (
                f"共核验精选池节点 {tot} 个：\n\n"
                f"  • ✅ 原生洁净节点: {clean} 个\n"
                f"  • 🚨 新标记 [送中] 节点: {tagged} 个\n"
                f"  • 🕊️ 平反摘除 [送中] 节点: {untagged} 个\n\n"
                f"💡 调整已即刻写入 Script.js 生效，并已自动同步至云端 Worker！"
            )
            MessageBox(title, content, self).exec()

        self._hk_worker.finished_signal.connect(_on_finished)
        self._hk_worker.start()


