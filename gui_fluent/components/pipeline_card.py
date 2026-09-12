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

        # ──────── 第 6 行：链路秒级自愈与托盘常驻 ────────
        row6 = QHBoxLayout()
        row6.setContentsMargins(0, 0, 0, 0)
        row6.setSpacing(8)

        lbl_heal = BodyLabel("🛡️ 链路秒级自愈:", self)
        lbl_heal.setStyleSheet("color: #34d399; font-weight: bold;")
        row6.addWidget(lbl_heal)

        self.chk_auto_heal = CheckBox("启用断流秒级无感自愈", self)
        self.chk_auto_heal.setObjectName("chk_auto_heal")
        self.chk_auto_heal.setChecked(True)
        row6.addWidget(self.chk_auto_heal)

        row6.addWidget(CaptionLabel("黑洞阈值(s):", self))
        self.auto_heal_threshold = LineEdit(self)
        self.auto_heal_threshold.setObjectName("auto_heal_threshold")
        self.auto_heal_threshold.setText("2.0")
        self.auto_heal_threshold.setFixedWidth(40)
        self.auto_heal_threshold.setAlignment(Qt.AlignCenter)
        row6.addWidget(self.auto_heal_threshold)

        row6.addWidget(CaptionLabel("熔断隔离(分):", self))
        self.auto_heal_cooldown = LineEdit(self)
        self.auto_heal_cooldown.setObjectName("auto_heal_cooldown")
        self.auto_heal_cooldown.setText("15")
        self.auto_heal_cooldown.setFixedWidth(36)
        self.auto_heal_cooldown.setAlignment(Qt.AlignCenter)
        row6.addWidget(self.auto_heal_cooldown)

        self.chk_minimize_to_tray = CheckBox("关闭窗口时最小化至托盘静默守护", self)
        self.chk_minimize_to_tray.setObjectName("chk_minimize_to_tray")
        self.chk_minimize_to_tray.setChecked(True)
        row6.addWidget(self.chk_minimize_to_tray)

        self.btn_diagnose_link = PushButton("⚡ 诊断当前链路", self)
        self.btn_diagnose_link.setObjectName("btn_diagnose_link")
        row6.addWidget(self.btn_diagnose_link)

        row6.addStretch(1)

        self.lbl_auto_heal_status = CaptionLabel("🟢 链路守卫中 (今日自愈: 0 次)", self)
        self.lbl_auto_heal_status.setObjectName("lbl_auto_heal_status")
        self.lbl_auto_heal_status.setStyleSheet("color: #34d399; font-weight: bold;")
        row6.addWidget(self.lbl_auto_heal_status)

        layout.addLayout(row6)

        self.setStyleSheet("""
            PipelineCard {
                background-color: rgba(30, 34, 50, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
