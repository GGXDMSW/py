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

