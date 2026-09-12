"""
Clash Verge 节点管理助手 - Fluent 风格主窗口
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QStackedWidget,
        QSystemTrayIcon,
        QMenu,
        QAction,
        QStyle,
    )
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon, QAction
    from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QStackedWidget,
        QSystemTrayIcon,
        QMenu,
        QStyle,
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

        # 10. 初始化 Windows 系统托盘与自愈守护信号
        self._init_system_tray()
        self._bind_auto_heal_signals()

        # 11. 绑定全界面控件实时编辑自动存盘
        self._bind_auto_save_signals()

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

        # 第 6 行：自愈守护与诊断控件绑定
        pc.chk_auto_heal.stateChanged.connect(self._on_auto_heal_toggled)
        pc.btn_diagnose_link.clicked.connect(self._on_diagnose_link_clicked)
        pc.auto_heal_threshold.textChanged.connect(self._update_auto_heal_params)
        pc.auto_heal_cooldown.textChanged.connect(self._update_auto_heal_params)
        pc.chk_minimize_to_tray.stateChanged.connect(self._on_tray_pref_changed)

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

    # ==================== Windows 系统托盘与断流秒级自愈 ====================

    def _init_system_tray(self):
        """
        初始化 Windows 系统托盘与右键菜单
        """
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = self.windowIcon()
        if not icon or icon.isNull():
            icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon)

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Clash Verge 节点管理助手 (断流秒级自愈守护中)")

        tray_menu = QMenu()
        act_show = tray_menu.addAction("显示主界面")
        act_show.triggered.connect(self._show_window)

        act_diag = tray_menu.addAction("⚡ 诊断当前链路")
        act_diag.triggered.connect(self._on_diagnose_link_clicked)

        self.act_tray_heal_toggle = tray_menu.addAction("🛡️ 断流秒级自愈")
        self.act_tray_heal_toggle.setCheckable(True)
        self.act_tray_heal_toggle.setChecked(self.pipeline_card.chk_auto_heal.isChecked())
        self.act_tray_heal_toggle.triggered.connect(lambda chk: self.pipeline_card.chk_auto_heal.setChecked(chk))

        tray_menu.addSeparator()
        act_quit = tray_menu.addAction("退出应用")
        act_quit.triggered.connect(self._force_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
        self._tray_balloon_shown = False

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self._show_window()

    def _show_window(self):
        self.showNormal()
        self.activateWindow()

    def _force_quit(self):
        if hasattr(self, 'controller') and self.controller:
            self.save_all_ui_settings()
            self.controller.save_config(self.controller.state.get_snapshot())
            self.controller.log("💾 正在退出并保存所有状态...")
        QApplication.quit()

    def _bind_auto_heal_signals(self):
        self.controller.auto_heal_status_updated.connect(self._on_auto_heal_status_updated)
        self.controller.auto_heal_event_triggered.connect(self._on_auto_heal_event_triggered)

    def _on_auto_heal_status_updated(self, status: dict):
        if not status:
            return
        healed_count = status.get("healed_count", 0)
        enabled = status.get("enabled", True)
        act_node = status.get("active_node", "")
        nohk_node = status.get("active_nohk_node", "")

        def _fmt(n):
            if not n:
                return "无"
            return n if len(n) <= 14 else n[:12] + ".."

        pc = self.pipeline_card
        yc_count = status.get("yellow_cards_count", 0)
        yc_str = f" | 🟨预警: {yc_count}" if yc_count > 0 else ""
        if not enabled:
            pc.lbl_auto_heal_status.setText(f"⏸ 自愈已暂停")
            pc.lbl_auto_heal_status.setStyleSheet("color: #94a3b8; font-weight: bold;")
        else:
            pc.lbl_auto_heal_status.setText(f"🟢 链路守卫中 (全量: {_fmt(act_node)} | 非港: {_fmt(nohk_node)} | 自愈: {healed_count}次{yc_str})")
            pc.lbl_auto_heal_status.setStyleSheet("color: #34d399; font-weight: bold;")

        if hasattr(self, "tray_icon") and self.tray_icon:
            yc_tip = f"\n黄牌预警: {yc_count}个" if yc_count > 0 else ""
            self.tray_icon.setToolTip(f"Clash Verge 节点助手\n全量: {act_node}\n非港AI: {nohk_node}\n今日自愈: {healed_count}次{yc_tip}")

    def _on_auto_heal_event_triggered(self, dead_node: str, backup_node: str, info: dict):
        grp = info.get("group", "⚡ 自动选择")
        is_non_hk = info.get("is_non_hk", False)
        cost_ms = info.get("cost_ms", 0)
        evicted = info.get("evicted", 0)
        tag = "非港AI" if is_non_hk else "全量出口"
        title = f"🛡️ 【{tag}】秒级断流自愈"
        tip = "\n✨ 严格继承非港限制，Gemini/反重力不受影响" if is_non_hk else ""
        msg = f"策略组 【{grp}】 坏死断流！\n已在 {cost_ms}ms 内斩断 {evicted} 条僵尸连接，并顺移至 【{backup_node}】{tip}"
        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 4500)

    def _on_auto_heal_toggled(self, state: int):
        enabled = bool(state == 2 or (hasattr(Qt, "CheckState") and state == Qt.CheckState.Checked.value) or bool(state))
        self.controller.toggle_auto_heal(enabled)
        if hasattr(self, "act_tray_heal_toggle"):
            self.act_tray_heal_toggle.setChecked(enabled)
        self.controller.save_config({"auto_heal_enabled": enabled})

    def _on_diagnose_link_clicked(self):
        res = self.controller.diagnose_current_link()
        node = res.get("active_node", "未知")
        nohk_node = res.get("active_nohk_node", "未知")
        delay = res.get("delay_ms", "超时")
        nohk_delay = res.get("delay_nohk_ms", "超时")
        healthy = res.get("is_healthy", False)
        conns = res.get("total_connections", 0)
        status_str = "双通道全部正常畅通" if healthy else "检测到部分通道异常"
        MessageBox(
            "双通道链路深度诊断结果",
            f"⚡ 全量出口 (常规/视频): {node}\n"
            f"   延迟测定: {delay} ms\n\n"
            f"⚡ 非港出口 (Gemini/反重力/AI): {nohk_node}\n"
            f"   延迟测定: {nohk_delay} ms\n\n"
            f"综合状态: {status_str}\n"
            f"活跃连接: {conns} 条\n"
            f"今日自愈: {res.get('healed_count', 0)} 次",
            self
        ).exec()

    def _update_auto_heal_params(self):
        pc = self.pipeline_card
        try:
            th = float(pc.auto_heal_threshold.text().strip())
        except ValueError:
            th = 3.5
        try:
            cd = float(pc.auto_heal_cooldown.text().strip()) * 60.0
        except ValueError:
            cd = 900.0
        if hasattr(self.controller, "auto_heal_watcher"):
            self.controller.auto_heal_watcher.update_config(
                blackhole_timeout=th,
                cooldown_duration=cd
            )
        self.controller.save_config({
            "auto_heal_threshold": th,
            "auto_heal_cooldown": cd / 60.0
        })

    def _on_tray_pref_changed(self, state: int):
        enabled = bool(state == 2 or (hasattr(Qt, "CheckState") and state == Qt.CheckState.Checked.value) or bool(state))
        self.controller.save_config({"minimize_to_tray_enabled": enabled})

    # ==================== 界面配置自动采集、实时持久化与记忆回显 ====================

    def collect_all_ui_config(self) -> dict:
        """
        全面采集主界面所有输入框、复选框、调度与订阅的最新设置字典
        """
        pc = getattr(self, "pipeline_card", None)
        pf = getattr(self, "page_favorites", None)
        pv = getattr(self, "page_verified", None)
        cfg = {}

        if pc:
            cfg.update({
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
                "schedule_enabled": pc.chk_schedule.isChecked(),
                "schedule_interval": pc.schedule_interval.text().strip(),
                "schedule_times": pc.schedule_times.text().strip(),
                "group_interval": pc.group_interval.text().strip(),
                "group_tolerance": pc.group_tolerance.text().strip(),
                "star_group_interval": pc.star_group_interval.text().strip(),
                "star_group_tolerance": pc.star_group_tolerance.text().strip(),
                "cf_worker_enabled": getattr(pc, "chk_worker_enabled", None) and pc.chk_worker_enabled.isChecked(),
                "worker_url": pc.worker_url.text().strip(),
                "worker_token": pc.worker_token.text().strip(),
                "clash_port": pc.clash_port.text().strip(),
                "clash_secret": pc.clash_secret.text().strip(),
                "auto_heal_enabled": pc.chk_auto_heal.isChecked(),
                "auto_heal_threshold": pc.auto_heal_threshold.text().strip(),
                "auto_heal_cooldown": pc.auto_heal_cooldown.text().strip(),
                "minimize_to_tray_enabled": pc.chk_minimize_to_tray.isChecked(),
            })

        if pf:
            cfg.update({
                "fav_max_delay": pf.fav_max_delay.text().strip(),
                "fav_min_speed": pf.fav_min_speed.text().strip(),
                "fav_rounds": pf.fav_rounds.text().strip(),
                "fav_speed_duration": pf.fav_speed_duration.text().strip(),
                "fav_jitter_min_delay": pf.fav_jitter_min.text().strip(),
                "fav_jitter_up_threshold": pf.fav_jitter_up.text().strip(),
                "fav_schedule_enabled": pf.chk_fav_schedule.isChecked(),
                "fav_schedule_interval": pf.fav_sched_interval.text().strip(),
                "fav_target_hk_count": pf.fav_target_hk.text().strip(),
                "fav_target_nohk_count": pf.fav_target_nohk.text().strip(),
                "fav_quota_early_stop": pf.chk_fav_early_stop.isChecked(),
                "fav_fallback_enabled": pf.chk_fav_fallback.isChecked(),
            })

        if pv:
            cfg.update({
                "incubate_hours": pv.incubate_hours.text().strip(),
                "incubate_passes": pv.incubate_passes.text().strip(),
            })

        if hasattr(self, "top_bar") and hasattr(self.top_bar, "sub_combo"):
            current_sub = self.top_bar.sub_combo.currentText().strip()
            if current_sub:
                cfg["last_selected_yaml"] = current_sub
                cfg["active_profile"] = current_sub

        return cfg

    def save_all_ui_settings(self):
        """
        统一存盘调度：采集所有控件数据并原子化持久化到磁盘
        """
        if hasattr(self, "controller") and self.controller:
            ui_cfg = self.collect_all_ui_config()
            self.controller.save_config(ui_cfg)

    def _bind_auto_save_signals(self):
        """
        为所有参数输入框 (editingFinished)、复选框 (stateChanged) 及订阅切换绑定静默实时自动存盘
        """
        pc = getattr(self, "pipeline_card", None)
        pf = getattr(self, "page_favorites", None)
        pv = getattr(self, "page_verified", None)

        if pc:
            pc_line_edits = [
                getattr(pc, "max_delay", None),
                getattr(pc, "min_speed", None),
                getattr(pc, "target_count", None),
                getattr(pc, "test_rounds", None),
                getattr(pc, "test_timeout", None),
                getattr(pc, "speed_duration", None),
                getattr(pc, "blacklist_threshold", None),
                getattr(pc, "speed_bl_threshold", None),
                getattr(pc, "speed_bl_rounds", None),
                getattr(pc, "jitter_min_delay", None),
                getattr(pc, "jitter_up_threshold", None),
                getattr(pc, "test_url", None),
                getattr(pc, "speed_url", None),
                getattr(pc, "schedule_interval", None),
                getattr(pc, "schedule_times", None),
                getattr(pc, "group_interval", None),
                getattr(pc, "group_tolerance", None),
                getattr(pc, "star_group_interval", None),
                getattr(pc, "star_group_tolerance", None),
                getattr(pc, "worker_url", None),
                getattr(pc, "worker_token", None),
                getattr(pc, "clash_port", None),
                getattr(pc, "clash_secret", None),
                getattr(pc, "auto_heal_threshold", None),
                getattr(pc, "auto_heal_cooldown", None),
            ]
            for le in pc_line_edits:
                if le and hasattr(le, "editingFinished"):
                    le.editingFinished.connect(self.save_all_ui_settings)

            pc_checkboxes = [
                getattr(pc, "chk_schedule", None),
                getattr(pc, "chk_worker_enabled", None),
                getattr(pc, "chk_auto_heal", None),
                getattr(pc, "chk_minimize_to_tray", None),
            ]
            for cb in pc_checkboxes:
                if cb and hasattr(cb, "stateChanged"):
                    cb.stateChanged.connect(lambda _st=None: self.save_all_ui_settings())

        if pf:
            pf_line_edits = [
                getattr(pf, "fav_max_delay", None),
                getattr(pf, "fav_min_speed", None),
                getattr(pf, "fav_rounds", None),
                getattr(pf, "fav_speed_duration", None),
                getattr(pf, "fav_jitter_min", None),
                getattr(pf, "fav_jitter_up", None),
                getattr(pf, "fav_sched_interval", None),
                getattr(pf, "fav_target_hk", None),
                getattr(pf, "fav_target_nohk", None),
            ]
            for le in pf_line_edits:
                if le and hasattr(le, "editingFinished"):
                    le.editingFinished.connect(self.save_all_ui_settings)

            pf_checkboxes = [
                getattr(pf, "chk_fav_schedule", None),
                getattr(pf, "chk_fav_early_stop", None),
                getattr(pf, "chk_fav_fallback", None),
            ]
            for cb in pf_checkboxes:
                if cb and hasattr(cb, "stateChanged"):
                    cb.stateChanged.connect(lambda _st=None: self.save_all_ui_settings())

        if pv:
            pv_line_edits = [
                getattr(pv, "incubate_hours", None),
                getattr(pv, "incubate_passes", None),
            ]
            for le in pv_line_edits:
                if le and hasattr(le, "editingFinished"):
                    le.editingFinished.connect(self.save_all_ui_settings)

        if hasattr(self, "top_bar") and hasattr(self.top_bar, "sub_combo"):
            self.top_bar.sub_combo.currentTextChanged.connect(lambda _txt=None: self.save_all_ui_settings())

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
        if "cf_worker_enabled" in cfg and hasattr(pc, "chk_worker_enabled"):
            pc.chk_worker_enabled.setChecked(bool(cfg["cf_worker_enabled"]))

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

        # 4. 订阅选择与触发加载 (优先记忆上次选中的 profile/yaml)
        saved_sub = cfg.get("last_selected_yaml") or cfg.get("active_profile") or "Rw0nNFlVIbnA.yaml"
        all_items = [self.top_bar.sub_combo.itemText(i) for i in range(self.top_bar.sub_combo.count())]
        active_sub = saved_sub if saved_sub in all_items else (all_items[0] if all_items else "")
        if active_sub:
            self.top_bar.sub_combo.setCurrentText(active_sub)
            self.controller.load_nodes_from_profile(active_sub)
            setattr(self.controller.state, "active_profile", active_sub)
            self.controller.data_changed.emit()

        self._on_reconnect_clicked()

        # 5. 恢复自愈与托盘设置
        if "auto_heal_enabled" in cfg:
            pc.chk_auto_heal.setChecked(bool(cfg["auto_heal_enabled"]))
            self.controller.toggle_auto_heal(bool(cfg["auto_heal_enabled"]))
        if "auto_heal_threshold" in cfg:
            pc.auto_heal_threshold.setText(str(cfg["auto_heal_threshold"]))
        if "auto_heal_cooldown" in cfg:
            pc.auto_heal_cooldown.setText(str(cfg["auto_heal_cooldown"]))
        if "minimize_to_tray_enabled" in cfg:
            pc.chk_minimize_to_tray.setChecked(bool(cfg["minimize_to_tray_enabled"]))
        self._update_auto_heal_params()

    def closeEvent(self, event):
        pc = self.pipeline_card
        if (
            hasattr(pc, "chk_minimize_to_tray")
            and pc.chk_minimize_to_tray.isChecked()
            and hasattr(self, "tray_icon")
            and self.tray_icon.isVisible()
        ):
            event.ignore()
            self.hide()
            if not getattr(self, "_tray_balloon_shown", False):
                self.tray_icon.showMessage(
                    "Clash Verge 节点管理助手",
                    "助手已最小化至系统托盘，后台保持秒级自愈与定时优选守护中...",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
                self._tray_balloon_shown = True
            return

        # 真正退出前强制存盘
        if hasattr(self, 'controller') and self.controller:
            self.save_all_ui_settings()
            self.controller.save_config(self.controller.state.get_snapshot())
            self.controller.log("💾 退出前已自动保存所有数据至 config...")
        super().closeEvent(event)
