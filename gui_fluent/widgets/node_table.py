"""
通用节点表格组件 (NodeTableView)
支持 11 列完整信息展示、状态高亮着色、智能列排序与鼠标拖选多行
"""
import re
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, QItemSelection, QItemSelectionModel
    from PyQt5.QtGui import QColor, QBrush, QFont
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
    )
else:
    from PyQt6.QtCore import Qt, QItemSelection, QItemSelectionModel
    from PyQt6.QtGui import QColor, QBrush, QFont
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
    )

from qfluentwidgets import RoundMenu, Action, FluentIcon, InfoBar


class DragSelectTableWidget(QTableWidget):
    """
    增强型 QTableWidget：支持鼠标按住左键直接上下拖拽滑动多选行
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start_row = -1

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_row = self.rowAt(event.pos().y())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self._drag_start_row >= 0:
            curr_row = self.rowAt(event.pos().y())
            if curr_row >= 0:
                start = min(self._drag_start_row, curr_row)
                end = max(self._drag_start_row, curr_row)
                selection = QItemSelection(
                    self.model().index(start, 0),
                    self.model().index(end, self.columnCount() - 1),
                )
                self.selectionModel().select(
                    selection,
                    QItemSelectionModel.SelectionFlag.ClearAndSelect
                    | QItemSelectionModel.SelectionFlag.Rows,
                )
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_row = -1
        super().mouseReleaseEvent(event)


class NodeTableView(QWidget):
    """
    通用节点表格视图：适用于 活跃待测 / 优质精选 / 延迟黑名单 / 低速黑名单
    """

    COLUMN_KEYS = [
        "status",
        "colo",
        "colo_hist",
        "reason",
        "delay",
        "avg_delay",
        "delay_hist",
        "hist_avg",
        "speed",
        "speed_hist",
        "endpoint",
        "name",
    ]

    COLUMN_HEADERS = [
        "状态",
        "最新Colo",
        "Colo稳定性(7天)",
        "入选/拉黑原因",
        "最新延迟",
        "本轮均值",
        "延迟轨迹(轮数)",
        "历史均值/稳定度",
        "最新下行",
        "下行轨迹(近4次)",
        "IP:端口",
        "节点名称",
    ]

    COLUMN_WIDTHS = [90, 80, 150, 160, 75, 85, 120, 140, 75, 120, 140, 260]

    def __init__(self, parent=None, controller=None, page_type: str = "active"):
        super().__init__(parent)
        self.controller = controller
        self.page_type = page_type
        self._sort_col = -1
        self._sort_asc = True
        self._raw_rows = []
        self.init_ui()

    def set_controller(self, controller, page_type: str = "active"):
        """绑定控制器与当前页面类型"""
        self.controller = controller
        self.page_type = page_type

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = DragSelectTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        # 样式设定：深色风格
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

        # 预设初始列宽
        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        # 开启右键上下文菜单策略
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

    def populate(self, rows: list[dict]):
        """
        填充表格数据
        rows 为字典列表，每个字典包含 COLUMN_KEYS 中的字段
        """
        self._raw_rows = list(rows)
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            status_text = str(row_data.get("status", ""))
            delay_text = str(row_data.get("delay", ""))

            # 颜色规则
            if "优质精选" in status_text or "云端已保活" in status_text:
                row_color = QColor("#38bdf8")
            elif "活跃待测" in status_text:
                row_color = QColor("#e2e8f0")
            elif ("黑名单" in status_text) or ("拉黑" in status_text) or ("超时" in status_text) or ("超时" in delay_text) or ("淘汰" in status_text):
                row_color = QColor("#f87171")
            elif "缺失" in status_text:
                row_color = QColor("#fbbf24")
            else:
                row_color = QColor("#94a3b8")

            node_name = str(row_data.get("raw_name", row_data.get("name", "")))
            ep_val = str(row_data.get("endpoint", row_data.get("IP:端口", "")))
            if not ep_val or ep_val == "-":
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", node_name)
                if m:
                    ep_val = m.group(1)

            for col_idx, key in enumerate(self.COLUMN_KEYS):
                val_str = str(row_data.get(key, "-"))
                item = QTableWidgetItem(val_str)
                item.setForeground(QBrush(row_color))

                # 对齐方式：除最后一列“节点名称”靠左居中外，其余全部水平居中
                if key == "name":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # 将原始节点名称与端点绑定到每一行首列的 UserRole
                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, node_name)
                    item.setData(Qt.ItemDataRole.UserRole + 1, ep_val)

                self.table.setItem(row_idx, col_idx, item)

    def get_selected_node_names(self) -> list[str]:
        """
        获取当前选中行的节点名称列表
        """
        selected_names = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                name = item.data(Qt.ItemDataRole.UserRole)
                if name and name not in ["", "无", "-"]:
                    selected_names.append(name)
                else:
                    ep = item.data(Qt.ItemDataRole.UserRole + 1)
                    if ep and ep not in ["", "-"]:
                        selected_names.append(ep)
                    else:
                        name_item = self.table.item(r, len(self.COLUMN_KEYS) - 1)
                        if name_item and name_item.text().strip() not in ["", "无", "-"]:
                            selected_names.append(name_item.text().strip())
        return selected_names

    def get_selected_endpoints(self) -> list[str]:
        """
        获取当前选中行的物理端点 (IP:Port) 列表
        """
        selected_eps = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                ep = item.data(Qt.ItemDataRole.UserRole + 1)
                if ep and ep not in ["", "-"]:
                    selected_eps.append(ep)
                else:
                    col_ep = self.COLUMN_KEYS.index("endpoint") if "endpoint" in self.COLUMN_KEYS else -1
                    if col_ep >= 0:
                        ep_item = self.table.item(r, col_ep)
                        if ep_item and ep_item.text().strip() not in ["", "-"]:
                            selected_eps.append(ep_item.text().strip())
                            continue
                    name = item.data(Qt.ItemDataRole.UserRole)
                    if hasattr(self, "controller") and self.controller:
                        ep_res = self.controller.get_node_endpoint(name)
                        if ep_res:
                            selected_eps.append(ep_res)
                    else:
                        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", str(name))
                        if m:
                            selected_eps.append(m.group(1))
        return selected_eps

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

        selected_nodes = self.get_selected_node_names()
        if not selected_nodes:
            return

        selected_endpoints = self.get_selected_endpoints()
        cnt = len(selected_nodes)

        menu = RoundMenu(parent=self)

        # 1. 基础剪贴板复制
        copy_name_action = Action(FluentIcon.COPY, f"复制节点名称 ({cnt}项)", self)
        copy_name_action.triggered.connect(lambda: self._copy_to_clipboard(selected_nodes, "节点名称"))
        menu.addAction(copy_name_action)

        if selected_endpoints:
            copy_ep_action = Action(FluentIcon.SHARE, f"复制物理端点 ({len(selected_endpoints)}项)", self)
            copy_ep_action.triggered.connect(lambda: self._copy_to_clipboard(selected_endpoints, "物理端点"))
            menu.addAction(copy_ep_action)

        menu.addSeparator()

        # 2. 业务操作
        if self.controller:
            test_delay_action = Action(FluentIcon.WIFI, f"⚡ 立即测延迟 ({cnt}项)", self)
            test_delay_action.triggered.connect(lambda: self.controller.test_nodes_delay(selected_nodes))
            menu.addAction(test_delay_action)

            colo_action = Action(getattr(FluentIcon, "EARTH", FluentIcon.GLOBE), "🌍 测当前 Colo", self)
            colo_action.triggered.connect(lambda: self.controller.test_nodes_colo(selected_nodes))
            menu.addAction(colo_action)

            # 补充 C 段挖掘功能
            mine_action = Action(FluentIcon.SEARCH, "🔍 C段挖掘", self)
            mine_action.triggered.connect(lambda: self.controller.mine_c_subnet(selected_nodes))
            menu.addAction(mine_action)

            p_type = getattr(self, "page_type", "active")
            if p_type == "active":
                fav_action = Action(FluentIcon.HEART, "⭐ 设为优质精选", self)
                fav_action.triggered.connect(lambda: self.controller.move_nodes_to_favorites(selected_nodes))
                menu.addAction(fav_action)

                star_action = Action(FluentIcon.ACCEPT, "🏆 晋升至典藏常青", self)
                star_action.triggered.connect(lambda: self.controller.promote_nodes_to_stars(selected_nodes))
                menu.addAction(star_action)

                menu.addSeparator()

                delay_bl_action = Action(FluentIcon.CANCEL, "🚫 延迟拉黑", self)
                delay_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "右键手动拉黑", "delay"))
                menu.addAction(delay_bl_action)

                speed_bl_action = Action(FluentIcon.REMOVE, "🐢 低速拉黑", self)
                speed_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "右键手动拉黑", "speed"))
                menu.addAction(speed_bl_action)

            elif p_type == "favorites":
                star_action = Action(FluentIcon.ACCEPT, "🏆 晋升至典藏常青", self)
                star_action.triggered.connect(lambda: self.controller.promote_nodes_to_stars(selected_nodes))
                menu.addAction(star_action)

                ver_action = Action(FluentIcon.SYNC, "⏳ 纳入沉淀孵化池", self)
                ver_action.triggered.connect(lambda: self.controller.sync_favorites_to_verified())
                menu.addAction(ver_action)

                menu.addSeparator()

                remove_fav_action = Action(FluentIcon.DELETE, "🗑️ 移出精选池", self)
                remove_fav_action.triggered.connect(lambda: self.controller.remove_nodes_from_favorites(selected_nodes))
                menu.addAction(remove_fav_action)

                delay_bl_action = Action(FluentIcon.CANCEL, "🚫 延迟拉黑", self)
                delay_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "从精选池手动拉黑", "delay"))
                menu.addAction(delay_bl_action)

                speed_bl_action = Action(FluentIcon.REMOVE, "🐢 低速拉黑", self)
                speed_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "从精选池手动拉黑", "speed"))
                menu.addAction(speed_bl_action)

            elif p_type in ["delay_black", "speed_black"]:
                unbl_action = Action(FluentIcon.SYNC, "♻️ 移出黑名单 (恢复待测)", self)
                unbl_action.triggered.connect(lambda: self.controller.remove_nodes_from_blacklist(selected_nodes))
                menu.addAction(unbl_action)

                fav_action = Action(FluentIcon.HEART, "⭐ 破格设为优质", self)
                fav_action.triggered.connect(lambda: self.controller.move_nodes_to_favorites(selected_nodes))
                menu.addAction(fav_action)

                menu.addSeparator()

                if p_type == "delay_black":
                    to_speed_action = Action(FluentIcon.REMOVE, "🐢 转为低速拉黑", self)
                    to_speed_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "转为低速黑名单", "speed"))
                    menu.addAction(to_speed_action)
                else:
                    to_delay_action = Action(FluentIcon.CANCEL, "🚫 转为延迟拉黑", self)
                    to_delay_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "转为延迟黑名单", "delay"))
                    menu.addAction(to_delay_action)

        menu.exec(self.table.mapToGlobal(pos))

    def _on_header_clicked(self, col: int):
        """
        点击列标题执行智能排序（区分数值与字符串）
        """
        if not self._raw_rows:
            return

        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        key = self.COLUMN_KEYS[col]
        is_numeric = key in ["delay", "avg_delay", "hist_avg", "speed"]

        def _sort_key(row_dict):
            val = str(row_dict.get(key, ""))
            if is_numeric:
                if not val or val == "-" or "超时" in val or "失败" in val:
                    return float("inf") if self._sort_asc else float("-inf")
                m = re.search(r"[-+]?\d*\.?\d+", val)
                return float(m.group()) if m else (float("inf") if self._sort_asc else float("-inf"))
            return val.lower()

        sorted_rows = sorted(self._raw_rows, key=_sort_key, reverse=not self._sort_asc)
        self.populate(sorted_rows)
