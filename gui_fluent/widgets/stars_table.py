"""
典藏管理池表格组件 (StarsTableView)
展示 8 列核心长青节点数据，支持双击编辑信号触发与智能排序
"""
import re
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, pyqtSignal, QItemSelection, QItemSelectionModel
    from PyQt5.QtGui import QColor, QBrush
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QInputDialog,
    )
else:
    from PyQt6.QtCore import Qt, pyqtSignal, QItemSelection, QItemSelectionModel
    from PyQt6.QtGui import QColor, QBrush
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QInputDialog,
    )

from qfluentwidgets import RoundMenu, Action, FluentIcon, InfoBar, MessageBox
from gui_fluent.widgets.node_table import DragSelectTableWidget


class StarsTableView(QWidget):
    """
    典藏管理池表格组件
    """

    double_clicked = pyqtSignal(str)

    COLUMN_KEYS = [
        "endpoint",
        "colo",
        "colo_hist",
        "reason",
        "remark",
        "delay",
        "speed",
        "match",
    ]

    COLUMN_HEADERS = [
        "IP:端口",
        "最新Colo",
        "Colo稳定性(7天)",
        "典藏入选原因",
        "备注信息 (可双击修改)",
        "最新延迟",
        "最新下行",
        "本地订阅关联状态",
    ]

    COLUMN_WIDTHS = [130, 85, 150, 190, 200, 75, 85, 250]

    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self._sort_col = -1
        self._sort_asc = True
        self._raw_rows = []
        self.init_ui()

    def set_controller(self, controller):
        """绑定控制器"""
        self.controller = controller

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = DragSelectTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #181b26;
                color: #e2e8f0;
                gridline-color: rgba(255, 255, 255, 0.06);
                border: none;
                selection-background-color: #28334a;
                selection-color: #ffffff;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1e2230;
                color: #8d98af;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QTableCornerButton::section {
                background-color: #1e2230;
                border: none;
            }
            QScrollBar:vertical {
                background: #181b26;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)

        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        # 开启右键上下文菜单策略
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

    def _copy_to_clipboard(self, items: list[str], label: str = "内容"):
        """复制内容至系统剪贴板"""
        if not items:
            return
        text = "\n".join(str(x) for x in items if str(x).strip())
        QApplication.clipboard().setText(text)
        InfoBar.success(
            title="已复制到剪贴板",
            content=f"已成功复制 {len(items)} 条{label}",
            duration=2000,
            parent=self.window(),
        )

    def _edit_remark(self, ep: str):
        """弹出修改备注输入框"""
        if not ep or not self.controller:
            return
        text, ok = QInputDialog.getText(self, "修改备注", f"修改典藏节点 [{ep}] 的备注信息:")
        if ok and text is not None:
            self.controller.update_star_remark(ep, text.strip())

    def _confirm_delete(self, eps: list[str]):
        """删除选中典藏节点确认"""
        if not eps or not self.controller:
            return
        w = MessageBox("删除确认", f"确定从本地典藏池移除选中的 {len(eps)} 个节点吗？\n（注：点击保存推送前云端数据不会变动）", self.window())
        if w.exec():
            self.controller.delete_selected_stars(eps)

    def _show_context_menu(self, pos):
        """弹出 Fluent 风格圆角右键悬浮菜单"""
        item_at = self.table.itemAt(pos)
        if not item_at:
            return
        clicked_row = item_at.row()
        selected_rows = {idx.row() for idx in self.table.selectedIndexes()}
        if clicked_row not in selected_rows:
            self.table.clearSelection()
            self.table.selectRow(clicked_row)

        selected_eps = self.get_selected_endpoints()
        if not selected_eps:
            return

        cnt = len(selected_eps)
        menu = RoundMenu(parent=self)

        # 1. 剪贴板复制
        copy_ep_action = Action(FluentIcon.COPY, f"复制物理端点 ({cnt}项)", self)
        copy_ep_action.triggered.connect(lambda: self._copy_to_clipboard(selected_eps, "物理端点"))
        menu.addAction(copy_ep_action)

        if cnt == 1:
            edit_action = Action(FluentIcon.EDIT, "✏️ 修改备注信息", self)
            edit_action.triggered.connect(lambda: self._edit_remark(selected_eps[0]))
            menu.addAction(edit_action)

        menu.addSeparator()

        # 2. 业务操作
        if self.controller:
            test_delay_action = Action(FluentIcon.WIFI, f"⚡ 测选中延迟 ({cnt}项)", self)
            test_delay_action.triggered.connect(lambda: self.controller.test_stars_pipeline(mode="delay", endpoints=selected_eps))
            menu.addAction(test_delay_action)

            test_speed_action = Action(FluentIcon.SYNC, f"🚀 测选中下行速度 ({cnt}项)", self)
            test_speed_action.triggered.connect(lambda: self.controller.test_stars_pipeline(mode="speed", endpoints=selected_eps))
            menu.addAction(test_speed_action)

            colo_action = Action(getattr(FluentIcon, "EARTH", FluentIcon.GLOBE), "🌍 测当前 Colo", self)
            colo_action.triggered.connect(lambda: self.controller.test_nodes_colo(selected_eps))
            menu.addAction(colo_action)

            # 补充 C 段挖掘功能
            mine_action = Action(FluentIcon.SEARCH, "🔍 C段挖掘", self)
            mine_action.triggered.connect(lambda: self.controller.mine_c_subnet(selected_eps))
            menu.addAction(mine_action)

            menu.addSeparator()

            del_action = Action(FluentIcon.DELETE, f"🗑️ 从典藏池移除 ({cnt}项)", self)
            del_action.triggered.connect(lambda: self._confirm_delete(selected_eps))
            menu.addAction(del_action)

        menu.exec(self.table.mapToGlobal(pos))

    def populate(self, rows: list[dict]):
        self._raw_rows = list(rows)
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            match_text = str(row_data.get("match", ""))
            delay_text = str(row_data.get("delay", ""))
            ep = str(row_data.get("endpoint", ""))

            # 颜色规则
            if ("未匹配" in match_text) or ("离线" in match_text) or ("已下线" in match_text):
                row_color = QColor("#94a3b8")
            elif "超时" in delay_text:
                row_color = QColor("#f87171")
            elif ep:
                row_color = QColor("#38bdf8")
            else:
                row_color = QColor("#94a3b8")

            for col_idx, key in enumerate(self.COLUMN_KEYS):
                val_str = str(row_data.get(key, "-"))
                item = QTableWidgetItem(val_str)
                item.setForeground(QBrush(row_color))

                if key in ["remark", "match"]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, ep)

                self.table.setItem(row_idx, col_idx, item)

    def get_selected_endpoints(self) -> list[str]:
        endpoints = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                ep = item.data(Qt.ItemDataRole.UserRole)
                endpoints.append(ep if ep else item.text().strip())
        return endpoints

    def _on_cell_double_clicked(self, row: int, col: int):
        item = self.table.item(row, 0)
        if item:
            ep = item.data(Qt.ItemDataRole.UserRole)
            self.double_clicked.emit(ep if ep else item.text().strip())

    def _on_header_clicked(self, col: int):
        if not self._raw_rows:
            return

        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        key = self.COLUMN_KEYS[col]
        is_numeric = key in ["delay", "speed"]

        def _sort_key(row_dict):
            val = str(row_dict.get(key, ""))
            if is_numeric:
                if not val or val == "-" or "超时" in val:
                    return float("inf") if self._sort_asc else float("-inf")
                m = re.search(r"[-+]?\d*\.?\d+", val)
                return float(m.group()) if m else (float("inf") if self._sort_asc else float("-inf"))
            return val.lower()

        sorted_rows = sorted(self._raw_rows, key=_sort_key, reverse=not self._sort_asc)
        self.populate(sorted_rows)
