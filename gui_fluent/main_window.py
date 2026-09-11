"""
Clash Verge 节点管理助手 - Fluent 风格主窗口
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QStackedWidget,
    )
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QStackedWidget,
    )

from qfluentwidgets import (
    SegmentedWidget,
    MessageBox,
    setTheme,
    Theme,
    PushButton,
)

from gui_fluent.app_controller import AppController
from gui_fluent.components.top_bar import TopBar
from gui_fluent.components.log_panel import LogPanel
from gui_fluent.components.bottom_action_bar import BottomActionBar
from gui_fluent.components.pipeline_card import PipelineCard

from gui_fluent.pages.page_active import PageActive
from gui_fluent.pages.page_favorites import PageFavorites
from gui_fluent.pages.page_verified import PageVerified
from gui_fluent.pages.page_stars import PageStars
from gui_fluent.pages.page_delay_black import PageDelayBlack
from gui_fluent.pages.page_speed_black import PageSpeedBlack
from gui_fluent.pages.page_cloud_text import PageCloudText

from gui_fluent.widgets.c_miner_dialog import CSegmentMinerDialog


class MainWindow(QWidget):
    """
    基于 PyQt-Fluent-Widgets 构建的全新横向顶部导航 Fluent 主窗口
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_app()

    def init_app(self):
        # 1. 基础属性与 Windows 11 深色主题
        self.setWindowTitle("Clash Verge 节点管理助手 (Fluent 版)")
        setTheme(Theme.DARK)
        self.setStyleSheet("""
            MainWindow {
                background-color: #1a1a1a;
                color: #f1f5f9;
            }
        """)

        self.setMinimumSize(1200, 760)
        self.resize(1260, 800)
        self.center_on_screen()

        # 2. 实例化中枢控制器
        self.controller = AppController(self)

        # 3. 组装自上而下的整体垂直布局结构
        self.init_layout_structure()

        # 4. 初始化 7 个子页面并添加到 stackedWidget 和顶部横向 SegmentedWidget
        self.init_sub_pages()

        # 5. 绑定控制器日志信号至界面日志面板
        self.controller.log_signal.connect(self.log_panel.append_log)
        self.controller.log("欢迎使用 Clash Verge 节点管理助手 (Fluent UI 现代版)！")

        # 6. 绑定流水线控制卡信号
        self._bind_pipeline_signals()

        # 7. 绑定底部操作栏业务动作
        self._bind_bottom_actions()

        # 8. 接入后台定时调度守护与精选自愈降级
        self.controller.set_scheduler_config_provider(self._get_scheduler_config)
        self.controller.scheduler_trigger_full_signal.connect(self._on_scheduler_trigger_full)
        self.controller.scheduler_trigger_fav_signal.connect(self._on_scheduler_trigger_fav)
        self.controller.fav_pipeline_fallback_needed.connect(self._on_fav_fallback_needed)

        # 9. 恢复初始配置与历史回显
        cfg = self.controller.load_config() or {}
        self.restore_ui_config(cfg)

    def init_layout_structure(self):
        """
        构建主窗体自上而下的整体布局结构：
        - SegmentedWidget (横向菜单，靠左排列)
        - self.top_bar (包含订阅与右侧一排测速按钮)
        - self.pipeline_card (流水线参数卡片)
        - self.stackedWidget (核心表格区，设置 stretch=1)
        - self.log_panel (日志区)
        - self.bottom_action_bar (底部按键)
        """
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 10)
        self.main_layout.setSpacing(8)

        # 1. 顶部横向 SegmentedWidget 与 C段挖掘入口
        self.nav_layout = QHBoxLayout()
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.segment = SegmentedWidget(self)
        self.nav_layout.addWidget(self.segment)
        self.nav_layout.addStretch(1)
        
        self.btn_c_miner = PushButton("🔍 C段深度挖掘", self)
        self.btn_c_miner.clicked.connect(self._on_c_miner_clicked)
        self.nav_layout.addWidget(self.btn_c_miner)

        self.main_layout.addLayout(self.nav_layout)

        # 2. 上：TopBar (~68px)
        self.top_bar = TopBar(self)
        self.top_bar.setFixedHeight(68)
        self.main_layout.addWidget(self.top_bar)

        # 3. 中上：PipelineCard（流水线参数控制卡）
        self.pipeline_card = PipelineCard(self)
        self.main_layout.addWidget(self.pipeline_card)

        # 4. 中：StackedWidget (核心表格区，自适应伸展 stretch=1)
        self.stackedWidget = QStackedWidget(self)
        self.main_layout.addWidget(self.stackedWidget, 1)

        # 5. 下：LogPanel (~120px)
        self.log_panel = LogPanel(self)
        self.log_panel.setFixedHeight(120)
        self.main_layout.addWidget(self.log_panel)

        # 6. 下：BottomActionBar (~50px)
        self.bottom_action_bar = BottomActionBar(self)
        self.bottom_action_bar.setFixedHeight(50)
        self.main_layout.addWidget(self.bottom_action_bar)

    def init_sub_pages(self):
        """
        创建 7 个功能页面，装配进 stackedWidget，并在顶部横排 SegmentedWidget 中注册标签项
        """
        self.page_active = PageActive(self.controller, self)
        self.page_favorites = PageFavorites(self.controller, self)
        self.page_verified = PageVerified(self.controller, self)
        self.page_stars = PageStars(self.controller, self)
        self.page_delay_black = PageDelayBlack(self.controller, self)
        self.page_speed_black = PageSpeedBlack(self.controller, self)
        self.page_cloud_text = PageCloudText(self.controller, self)

        # 页面加入 QStackedWidget
        self.stackedWidget.addWidget(self.page_active)
        self.stackedWidget.addWidget(self.page_favorites)
        self.stackedWidget.addWidget(self.page_verified)
        self.stackedWidget.addWidget(self.page_stars)
        self.stackedWidget.addWidget(self.page_delay_black)
        self.stackedWidget.addWidget(self.page_speed_black)
        self.stackedWidget.addWidget(self.page_cloud_text)

        # 顶部横排菜单注册项
        self.segment.addItem(
            routeKey="active",
            text="📋 活跃待测",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_active),
        )
        self.segment.addItem(
            routeKey="favorites",
            text="⭐ 优质精选",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_favorites),
        )
        self.segment.addItem(
            routeKey="verified",
            text="⏳ 沉淀孵化",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_verified),
        )
        self.segment.addItem(
            routeKey="stars",
            text="🏆 典藏管理",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_stars),
        )
        self.segment.addItem(
            routeKey="delay_black",
            text="🚫 延迟黑名单",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_delay_black),
        )
        self.segment.addItem(
            routeKey="speed_black",
            text="🐌 低速黑名单",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_speed_black),
        )
        self.segment.addItem(
            routeKey="cloud_text",
            text="☁️ 云端文本",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_cloud_text),
        )

        self.segment.setCurrentItem("active")

        # 监听标签页切换事件，切换时自动刷新目标页面数据
        self.stackedWidget.currentChanged.connect(self._on_page_changed)
        self.controller.data_changed.connect(self.update_tab_badges)
        self.update_tab_badges()

    def update_tab_badges(self):
        """
        动态更新顶部导航栏各标签后的实时节点数量角标
        """
        try:
            cnt_active = len(self.controller.get_table_rows("active"))
            cnt_fav = len(self.controller.get_table_rows("favorites"))
            cnt_ver = len(self.controller.get_table_rows("verified"))
            cnt_stars = len(self.controller.get_table_rows("stars"))
            cnt_delay_bl = len(self.controller.get_table_rows("delay_black"))
            cnt_speed_bl = len(self.controller.get_table_rows("speed_black"))

            self.segment.setItemText("active", f"📋 活跃待测 ({cnt_active})")
            self.segment.setItemText("favorites", f"⭐ 优质精选 ({cnt_fav})")
            self.segment.setItemText("verified", f"⏳ 沉淀孵化 ({cnt_ver})")
            self.segment.setItemText("stars", f"🏆 典藏管理 ({cnt_stars})")
            self.segment.setItemText("delay_black", f"🚫 延迟黑名单 ({cnt_delay_bl})")
            self.segment.setItemText("speed_black", f"🐌 低速黑名单 ({cnt_speed_bl})")
            self.segment.setItemText("cloud_text", "☁️ 云端文本")
        except Exception:
            pass

    def center_on_screen(self):
        """
        窗口居中显示于当前屏幕
        """
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(max(0, x), max(0, y))

    def _bind_pipeline_signals(self):
        pc = self.pipeline_card
        # 重连按钮：调用 AppController 检测连接状态并更新状态标签
        pc.btn_reconnect.clicked.connect(self._on_reconnect_clicked)

        # 启动与终止流水线按钮
        pc.btn_run_pipeline.clicked.connect(self._on_run_pipeline_clicked)
        pc.btn_stop_pipeline.clicked.connect(self._on_stop_pipeline_clicked)

        # 核心设置卡片操作按钮
        pc.btn_save_group.clicked.connect(self._on_save_group_clicked)
        pc.btn_test_worker.clicked.connect(self._on_test_worker_clicked)
        pc.btn_sync_auto.clicked.connect(self._on_sync_auto_clicked)

        # 绑定流水线结束与状态信号
        self.controller.pipeline_finished.connect(self._on_pipeline_finished)
        self.controller.pipeline_status_updated.connect(self._on_pipeline_status_updated)

        # 顶部 TopBar 快捷操作组按钮绑定
        self.top_bar.btn_update_sub.clicked.connect(self._on_update_sub_clicked)
        self.top_bar.btn_test_page_colo.clicked.connect(self._on_test_page_colo_clicked)
        self.top_bar.btn_clear_page_colo.clicked.connect(self._on_clear_page_colo_clicked)
        self.top_bar.btn_sync_kernel_delay.clicked.connect(self._on_sync_kernel_delay_clicked)
        self.top_bar.btn_clear_speed_records.clicked.connect(self._on_clear_speed_records_clicked)

        # 订阅下拉框加载可用 YAML 文件
        try:
            yamls = self.controller.get_all_yaml_profiles()
            self.top_bar.sub_combo.addItems(yamls)
            self.top_bar.sub_combo.currentTextChanged.connect(self._on_sub_combo_changed)
        except Exception:
            pass

    def _on_sub_combo_changed(self, yaml_name: str):
        if not yaml_name:
            return
        try:
            nodes, _ = self.controller.load_nodes_from_profile(yaml_name)
            setattr(self.controller.state, "active_profile", yaml_name)
            self.controller.save_config({"last_selected_yaml": yaml_name, "active_profile": yaml_name})
            self.controller.log(f"已切换订阅配置 [{yaml_name}]，加载了 {len(nodes)} 个节点")
            self.controller.data_changed.emit()
        except Exception as e:
            self.controller.log(f"加载订阅配置 [{yaml_name}] 失败: {str(e)}")

    def _on_run_pipeline_clicked(self):
        pc = self.pipeline_card
        current_yaml = self.top_bar.sub_combo.currentText().strip()
        if current_yaml and not self.controller.state.all_nodes:
            self._on_sub_combo_changed(current_yaml)

        config = {
            "max_delay": pc.max_delay.text().strip(),
            "min_speed": pc.min_speed.text().strip(),
            "target_count": pc.target_count.text().strip(),
            "test_rounds": pc.test_rounds.text().strip(),
            "test_timeout": pc.test_timeout.text().strip(),
            "speed_duration": pc.speed_duration.text().strip(),
            "blacklist_threshold": pc.blacklist_threshold.text().strip(),
            "speed_bl_threshold": pc.speed_bl_threshold.text().strip(),
            "speed_bl_rounds": pc.speed_bl_rounds.text().strip(),
            "jitter_min_delay": pc.jitter_min_delay.text().strip(),
            "jitter_up_threshold": pc.jitter_up_threshold.text().strip(),
            "test_url": pc.test_url.text().strip(),
            "speed_url": pc.speed_url.text().strip(),
            "schedule_interval": pc.schedule_interval.text().strip(),
            "schedule_times": pc.schedule_times.text().strip(),
            "group_interval": pc.group_interval.text().strip(),
            "group_tolerance": pc.group_tolerance.text().strip(),
            "star_group_interval": pc.star_group_interval.text().strip(),
            "star_group_tolerance": pc.star_group_tolerance.text().strip(),
            "worker_url": pc.worker_url.text().strip(),
            "worker_token": pc.worker_token.text().strip(),
            "clash_port": pc.clash_port.text().strip(),
            "clash_secret": pc.clash_secret.text().strip(),
        }

        started = self.controller.start_auto_pipeline(config)
        if started:
            pc.btn_run_pipeline.setEnabled(False)
            pc.btn_stop_pipeline.setEnabled(True)

    def _on_stop_pipeline_clicked(self):
        self.controller.stop_auto_pipeline()
        pc = self.pipeline_card
        pc.btn_stop_pipeline.setEnabled(False)

    def _on_pipeline_finished(self, success: bool, desc: str):
        pc = self.pipeline_card
        pc.btn_run_pipeline.setEnabled(True)
        pc.btn_stop_pipeline.setEnabled(False)
        self.controller.log(f"流水线运行结束: {'成功' if success else '中断/失败'} - {desc}")
        if hasattr(self, 'controller') and self.controller:
            self.controller.save_config(self.controller.state.get_snapshot())

        # 弹窗汇报大优选完成总结
        title = "🎉 全量大优选任务完成" if success else "⚠️ 流水线结束"
        fav_count = len(self.controller.state.favorites)
        star_count = len(self.controller.state.stars_nodes)
        d_bl_count = len(self.controller.state.local_blacklist)
        s_bl_count = len(self.controller.state.speed_blacklist)

        content = (
            f"【执行状态】: {desc}\n\n"
            f"📊 核心池最新统计：\n"
            f"  • ⭐ 优质精选池: {fav_count} 个\n"
            f"  • 🏆 典藏常青池: {star_count} 个\n"
            f"  • 🚫 延迟黑名单: {d_bl_count} 个\n"
            f"  • 🐌 低速黑名单: {s_bl_count} 个\n\n"
            f"✅ 最新策略组已自动写入 Script.js 并生效。"
        )
        msg_box = MessageBox(title, content, self)
        if hasattr(msg_box, "cancelButton") and msg_box.cancelButton:
            msg_box.cancelButton.hide()
        msg_box.exec()

    def _on_pipeline_status_updated(self, status_text: str):
        self.pipeline_card.lbl_sched_status.setText(status_text)

    def _on_reconnect_clicked(self):
        pc = self.pipeline_card
        port_text = pc.clash_port.text().strip()
        secret_text = pc.clash_secret.text().strip()
        try:
            port = int(port_text) if port_text else 9097
        except ValueError:
            port = 9097
        self.controller.update_clash_credentials(port=port, secret=secret_text)
        ok, ver = self.controller.get_clash_connection_status()
        if ok:
            pc.lbl_conn_status.setText(f"● 已连接 v{ver}")
            pc.lbl_conn_status.setStyleSheet("color: #10b981; font-weight: bold;")
            self.top_bar.lbl_status.setText(f"● 内核已连接 v{ver}")
            self.top_bar.lbl_status.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            pc.lbl_conn_status.setText("● 连接失败")
            pc.lbl_conn_status.setStyleSheet("color: #f87171; font-weight: bold;")
            self.top_bar.lbl_status.setText("● 内核未连接")
            self.top_bar.lbl_status.setStyleSheet("color: #f87171; font-weight: bold;")
        self.controller.log(f"Clash 连接检测: {'成功' if ok else '失败'} {ver}")

    def _on_save_group_clicked(self):
        pc = self.pipeline_card
        cfg = {
            "group_interval": pc.group_interval.text().strip(),
            "group_tolerance": pc.group_tolerance.text().strip(),
            "star_group_interval": pc.star_group_interval.text().strip(),
            "star_group_tolerance": pc.star_group_tolerance.text().strip(),
        }
        self.controller.save_config(cfg)
        self.controller.generate_script_and_reload()
        self.controller.log("💾 策略组配置已保存并重新写入 Script.js！")

    def _on_test_worker_clicked(self):
        pc = self.pipeline_card
        w_url = pc.worker_url.text().strip()
        w_tok = pc.worker_token.text().strip()
        self.controller.save_config({"worker_url": w_url, "worker_token": w_tok})
        self.controller.test_worker_connection(worker_url=w_url, token=w_tok)

    def _on_sync_auto_clicked(self):
        pc = self.pipeline_card
        w_url = pc.worker_url.text().strip()
        w_tok = pc.worker_token.text().strip()
        self.controller.save_config({"worker_url": w_url, "worker_token": w_tok})
        self.controller.push_favorites_to_cloud(base_url=w_url, token=w_tok)

    def _on_page_changed(self, index: int):
        """
        导航标签页切换时，同步顶部菜单高亮并主动刷新目标页面的表格数据
        """
        page = self.stackedWidget.currentWidget()
        route_map = {
            self.page_active: "active",
            self.page_favorites: "favorites",
            self.page_verified: "verified",
            self.page_stars: "stars",
            self.page_delay_black: "delay_black",
            self.page_speed_black: "speed_black",
            self.page_cloud_text: "cloud_text",
        }
        route_key = route_map.get(page)
        if route_key and self.segment.currentRouteKey() != route_key:
            self.segment.setCurrentItem(route_key)

        if page and hasattr(page, "refresh_data"):
            page.refresh_data()
        self.update_tab_badges()

    # ==================== 底部快捷操作栏绑定 ====================

    def _bind_bottom_actions(self):
        """
        绑定底部操作栏按钮的点击事件
        """
        bar = self.bottom_action_bar
        try:
            bar.btn_fav.clicked.disconnect()
        except Exception:
            pass
        bar.btn_fav.clicked.connect(self._on_btn_fav_clicked)

        try:
            bar.btn_promote.clicked.disconnect()
        except Exception:
            pass
        bar.btn_promote.clicked.connect(self._on_btn_promote_clicked)

        try:
            bar.btn_delay_black.clicked.disconnect()
        except Exception:
            pass
        bar.btn_delay_black.clicked.connect(self._on_btn_delay_black_clicked)

        try:
            bar.btn_speed_black.clicked.disconnect()
        except Exception:
            pass
        bar.btn_speed_black.clicked.connect(self._on_btn_speed_black_clicked)

        try:
            bar.btn_unblack.clicked.disconnect()
        except Exception:
            pass
        bar.btn_unblack.clicked.connect(self._on_btn_unblack_clicked)

        try:
            bar.btn_clear_bl.clicked.disconnect()
        except Exception:
            pass
        bar.btn_clear_bl.clicked.connect(self._on_btn_clear_bl_clicked)

        try:
            bar.btn_rescore.clicked.disconnect()
        except Exception:
            pass
        bar.btn_rescore.clicked.connect(self._on_btn_rescore_clicked)

        try:
            bar.btn_hotkey_sync.clicked.disconnect()
        except Exception:
            pass
        bar.btn_hotkey_sync.clicked.connect(self._on_btn_hotkey_sync_clicked)

    def _get_current_selected_nodes(self) -> list[str]:
        """
        获取当前激活页面中表格选中的节点名称或物理端点列表
        """
        page = self.stackedWidget.currentWidget()
        if not page or not hasattr(page, "table"):
            return []
        t = page.table
        if hasattr(t, "get_selected_node_names"):
            names = t.get_selected_node_names()
            if names:
                return names
        if hasattr(t, "get_selected_endpoints"):
            eps = t.get_selected_endpoints()
            if eps:
                return eps
        return []

    def _on_c_miner_clicked(self):
        """
        呼出 C 段全量极速深度挖掘对话框
        """
        seed_ip = "172.64.229.1"
        nodes = self._get_current_selected_nodes()
        if nodes:
            ep = nodes[0]
            if ":" in ep:
                seed_ip = ep.split(":")[0]
            else:
                seed_ip = ep
        dialog = CSegmentMinerDialog(seed_ip=seed_ip, seed_port=443, controller=self.controller, parent=self)
        dialog.exec()

    def _on_btn_fav_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要设为优质的节点！")
            return
        self.controller.move_nodes_to_favorites(nodes)

    def _on_btn_promote_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要晋升典藏的节点！")
            return
        self.controller.promote_nodes_to_stars(nodes)

    def _on_btn_delay_black_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要加入延迟黑名单的节点！")
            return
        self.controller.blacklist_nodes(nodes, reason="手动拉黑", bl_type="delay")

    def _on_btn_speed_black_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要加入低速黑名单的节点！")
            return
        self.controller.blacklist_nodes(nodes, reason="手动拉黑", bl_type="speed")

    def _on_btn_unblack_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要移出黑名单的节点！")
            return
        self.controller.remove_nodes_from_blacklist(nodes)

    def _on_btn_clear_bl_clicked(self):
        w = MessageBox("确认清空黑名单", "确定要清空所有延迟黑名单与低速黑名单记录吗？\n清空后所有被拉黑的节点将重新回到待测活跃池。", self)
        if w.exec():
            self.controller.clear_all_blacklists()

    def _on_btn_rescore_clicked(self):
        page = self.stackedWidget.currentWidget()
        if hasattr(page, "refresh_table"):
            page.refresh_table()
        elif hasattr(page, "refresh_data"):
            page.refresh_data()
        self.controller.log("📊 已重新计算综合评分与节点晋升状态！")

    def _on_btn_hotkey_sync_clicked(self):
        self.controller.trigger_verge_reload()

    # ==================== TopBar 顶部工具栏动作 ====================

    def _get_current_page_key(self) -> str:
        """
        获取当前激活页面的 key
        """
        curr = self.stackedWidget.currentWidget()
        if curr == self.page_favorites:
            return "favorites"
        elif curr == self.page_verified:
            return "verified"
        elif curr == self.page_stars:
            return "stars"
        elif curr == self.page_delay_black:
            return "delay_black"
        elif curr == self.page_speed_black:
            return "speed_black"
        elif curr == self.page_cloud_text:
            return "cloud_text"
        return "active"

    def _on_update_sub_clicked(self):
        curr_yaml = self.top_bar.sub_combo.currentText().strip()
        if not curr_yaml:
            self.controller.log("⚠️ 请先在下拉框选择要更新的订阅配置！")
            return
        self.controller.update_current_subscription(curr_yaml)

    def _on_test_page_colo_clicked(self):
        page_key = self._get_current_page_key()
        self.controller.test_current_page_colo(page_key)

    def _on_clear_page_colo_clicked(self):
        page_key = self._get_current_page_key()
        w = MessageBox(
            "确认清空机房记录",
            f"确定要清空当前标签页中所有节点的实时机房(Colo)与历史采样记录吗？\n\n"
            "• 该操作将清除最新 Colo 结果与 7 天滑动时序数据；\n"
            "• 归零后可点击【🌍 测当前页Colo】重新采集纯净数据。",
            self,
        )
        if w.exec():
            self.controller.clear_current_page_colo(page_key)

    def _on_sync_kernel_delay_clicked(self):
        self.controller.sync_kernel_delays()

    def _on_clear_speed_records_clicked(self):
        w = MessageBox(
            "清空确认",
            "确定要清空所有测速数据与延迟趋势记录吗？\n（不会清空您的黑名单及下行带宽历史）",
            self,
        )
        if w.exec():
            self.controller.clear_speed_records()

    # ==================== 后台定时调度与自愈降级 ====================

    def _get_scheduler_config(self) -> dict:
        """
        提供给 SchedulerDaemon 的动态定时参数字典
        """
        pc = self.pipeline_card
        pf = self.page_favorites
        return {
            "schedule_enabled": pc.chk_schedule.isChecked(),
            "schedule_times": pc.schedule_times.text().strip(),
            "schedule_interval": pc.schedule_interval.text().strip(),
            "fav_schedule_enabled": pf.chk_fav_schedule.isChecked(),
            "fav_schedule_interval": pf.fav_sched_interval.text().strip(),
        }

    def _on_scheduler_trigger_full(self, reason: str):
        self.controller.log(f"⏰ [定时调度] 触发全量大优选: {reason}")
        self._on_run_pipeline_clicked()

    def _on_scheduler_trigger_fav(self, reason: str):
        self.controller.log(f"⏰ [定时调度] 触发优质精选复检: {reason}")
        self.page_favorites._on_run_fav_clicked()

    def _on_fav_fallback_needed(self, reason: str):
        self.controller.log(f"⚡ 收到优质池自愈降级请求: {reason}，自动启动全量大优选...")
        self._on_run_pipeline_clicked()

    # ==================== 初始配置与历史回显 ====================

    def restore_ui_config(self, cfg: dict):
        """
        根据磁盘持久化配置恢复界面各项输入框、复选框与选中的订阅
        """
        if not cfg or not isinstance(cfg, dict):
            return

        pc = self.pipeline_card
        # 1. 恢复 PipelineCard 配置
        if "max_delay" in cfg:
            pc.max_delay.setText(str(cfg["max_delay"]))
        if "min_speed" in cfg:
            pc.min_speed.setText(str(cfg["min_speed"]))
        if "target_count" in cfg:
            pc.target_count.setText(str(cfg["target_count"]))
        if "test_rounds" in cfg:
            pc.test_rounds.setText(str(cfg["test_rounds"]))
        if "test_timeout" in cfg:
            pc.test_timeout.setText(str(cfg["test_timeout"]))
        if "speed_duration" in cfg:
            pc.speed_duration.setText(str(cfg["speed_duration"]))
        if "blacklist_threshold" in cfg:
            pc.blacklist_threshold.setText(str(cfg["blacklist_threshold"]))
        if "speed_bl_threshold" in cfg:
            pc.speed_bl_threshold.setText(str(cfg["speed_bl_threshold"]))
        if "speed_bl_rounds" in cfg:
            pc.speed_bl_rounds.setText(str(cfg["speed_bl_rounds"]))
        if "jitter_min_delay" in cfg:
            pc.jitter_min_delay.setText(str(cfg["jitter_min_delay"]))
        if "jitter_up_threshold" in cfg:
            pc.jitter_up_threshold.setText(str(cfg["jitter_up_threshold"]))
        if "test_url" in cfg:
            pc.test_url.setText(str(cfg["test_url"]))
        if "speed_url" in cfg:
            pc.speed_url.setText(str(cfg["speed_url"]))
        if "schedule_enabled" in cfg:
            pc.chk_schedule.setChecked(bool(cfg["schedule_enabled"]))
        if "schedule_interval" in cfg:
            pc.schedule_interval.setText(str(cfg["schedule_interval"]))
        if "schedule_times" in cfg:
            pc.schedule_times.setText(str(cfg["schedule_times"]))
        if "group_interval" in cfg:
            pc.group_interval.setText(str(cfg["group_interval"]))
        if "group_tolerance" in cfg:
            pc.group_tolerance.setText(str(cfg["group_tolerance"]))
        if "star_group_interval" in cfg:
            pc.star_group_interval.setText(str(cfg["star_group_interval"]))
        if "star_group_tolerance" in cfg:
            pc.star_group_tolerance.setText(str(cfg["star_group_tolerance"]))

        worker_url_val = cfg.get("worker_url") or cfg.get("cf_worker_url", "")
        if worker_url_val:
            pc.worker_url.setText(str(worker_url_val))
        worker_token_val = cfg.get("worker_token") or cfg.get("cf_worker_token", "")
        if worker_token_val:
            pc.worker_token.setText(str(worker_token_val))

        # 2. 恢复 PageFavorites 配置
        pf = self.page_favorites
        if "fav_max_delay" in cfg:
            pf.fav_max_delay.setText(str(cfg["fav_max_delay"]))
        if "fav_min_speed" in cfg:
            pf.fav_min_speed.setText(str(cfg["fav_min_speed"]))
        if "fav_rounds" in cfg:
            pf.fav_rounds.setText(str(cfg["fav_rounds"]))
        if "fav_speed_duration" in cfg:
            pf.fav_speed_duration.setText(str(cfg["fav_speed_duration"]))
        if "fav_jitter_min_delay" in cfg:
            pf.fav_jitter_min.setText(str(cfg["fav_jitter_min_delay"]))
        if "fav_jitter_up_threshold" in cfg:
            pf.fav_jitter_up.setText(str(cfg["fav_jitter_up_threshold"]))
        if "fav_schedule_enabled" in cfg:
            pf.chk_fav_schedule.setChecked(bool(cfg["fav_schedule_enabled"]))
        if "fav_schedule_interval" in cfg:
            pf.fav_sched_interval.setText(str(cfg["fav_schedule_interval"]))
        if "fav_target_hk_count" in cfg:
            pf.fav_target_hk.setText(str(cfg["fav_target_hk_count"]))
        if "fav_target_nohk_count" in cfg:
            pf.fav_target_nohk.setText(str(cfg["fav_target_nohk_count"]))
        if "fav_quota_early_stop" in cfg:
            pf.chk_fav_early_stop.setChecked(bool(cfg["fav_quota_early_stop"]))
        if "fav_fallback_enabled" in cfg:
            pf.chk_fav_fallback.setChecked(bool(cfg["fav_fallback_enabled"]))

        # 3. 恢复 PageVerified 配置
        pv = self.page_verified
        if "incubate_hours" in cfg:
            pv.incubate_hours.setText(str(cfg["incubate_hours"]))
        if "incubate_passes" in cfg:
            pv.incubate_passes.setText(str(cfg["incubate_passes"]))

        secret_val = cfg.get("clash_secret", "").strip() if cfg else ""
        if not secret_val:
            secret_val = "set-your-secret"
        pc.clash_secret.setText(secret_val)

        port_val = cfg.get("clash_port", "") if cfg else ""
        if not port_val:
            port_val = "9097"
        pc.clash_port.setText(str(port_val))

        # 4. 强制默认订阅选择并触发加载
        active_sub = "Rw0nNFlVIbnA.yaml"
        all_items = [self.top_bar.sub_combo.itemText(i) for i in range(self.top_bar.sub_combo.count())]
        if active_sub in all_items:
            self.top_bar.sub_combo.setCurrentText(active_sub)
            self.controller.load_nodes_from_profile(active_sub)
            self.controller.data_changed.emit()

        self._on_reconnect_clicked()

    def closeEvent(self, event):
        # 窗口关闭前强制存盘
        if hasattr(self, 'controller') and self.controller:
            self.controller.save_config(self.controller.state.get_snapshot())
            self.controller.log("💾 退出前已自动保存所有数据至 config...")
        super().closeEvent(event)
