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

