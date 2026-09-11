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
