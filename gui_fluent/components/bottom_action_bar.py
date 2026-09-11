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
