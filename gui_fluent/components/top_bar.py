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
