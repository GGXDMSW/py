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

