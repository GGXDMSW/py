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

