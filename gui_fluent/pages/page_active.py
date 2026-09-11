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


