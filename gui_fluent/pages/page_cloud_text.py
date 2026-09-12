"""
云端文本管理页面 (PageCloudText)
管理 Cloudflare Worker 远端分发的三大核心文本（/auto.txt、/verified.txt、/）
支持独立及批量拉取、在线编辑、格式统计与强推覆盖。
"""
import sys
import time
import threading
import re

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QFrame,
    )
else:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QFrame,
    )

from qfluentwidgets import (
    TitleLabel,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    PushButton,
    PrimaryPushButton,
    SimpleCardWidget,
    PlainTextEdit,
    MessageBox,
    InfoBar,
    InfoBarPosition,
)
from gui_fluent.app_controller import AppController


class CloudTextCard(SimpleCardWidget):
    """
    单个云端分发文本管理卡片
    """
    fetch_requested = pyqtSignal(str)          # subpath
    push_requested = pyqtSignal(str, str)      # (subpath, text)

    def __init__(self, title: str, subpath: str, desc: str = "", parent=None):
        super().__init__(parent)
        self.subpath = subpath
        self.title_text = title
        self.desc_text = desc
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 1. 顶部标题栏与独立操作按钮
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.title_label = SubtitleLabel(self.title_text, self)
        top_bar.addWidget(self.title_label)
        top_bar.addStretch(1)

        self.btn_fetch = PushButton("📥 拉取", self)
        self.btn_fetch.setToolTip(f"从云端拉取最新的 {self.subpath} 内容")
        self.btn_fetch.clicked.connect(lambda: self.fetch_requested.emit(self.subpath))
        top_bar.addWidget(self.btn_fetch)

        if self.subpath == "/pending.txt":
            self.btn_purge = PushButton("🧹 联动清洗", self)
            self.btn_purge.setToolTip("立即比对黑名单与精选池，从云端待测池中清除所有已淘汰或已入选的节点")
            top_bar.addWidget(self.btn_purge)

        self.btn_push = PrimaryPushButton("📤 强推", self)
        self.btn_push.setToolTip(f"将当前编辑的内容强推覆盖至云端 {self.subpath}")
        self.btn_push.clicked.connect(lambda: self.push_requested.emit(self.subpath, self.get_text()))
        top_bar.addWidget(self.btn_push)

        layout.addLayout(top_bar)

        # 2. 功能说明标签
        if self.desc_text:
            self.desc_label = CaptionLabel(self.desc_text, self)
            self.desc_label.setStyleSheet("color: #94a3b8;")
            layout.addWidget(self.desc_label)

        # 3. 核心大文本编辑器
        self.editor = PlainTextEdit(self)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        self.editor.setPlaceholderText(
            f"IP:Port#备注名\n示例：\n1.1.1.1:443#优质香港 12.5MB/s\n8.8.8.8:443#备选日本 8.2MB/s"
        )
        # 兼容 PyQt5 / PyQt6 的 NoWrap 设置
        if hasattr(PlainTextEdit, "LineWrapMode"):
            self.editor.setLineWrapMode(PlainTextEdit.LineWrapMode.NoWrap)
        elif hasattr(PlainTextEdit, "NoWrap"):
            self.editor.setLineWrapMode(PlainTextEdit.NoWrap)

        self.editor.textChanged.connect(self._update_stats)
        layout.addWidget(self.editor, 1)

        # 4. 底部统计与状态栏
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 0, 0, 0)
        self.lbl_stats = CaptionLabel("共 0 行 | 0 字符", self)
        self.lbl_stats.setStyleSheet("color: #94a3b8;")
        bottom_bar.addWidget(self.lbl_stats)

        bottom_bar.addStretch(1)

        self.lbl_status = CaptionLabel("就绪", self)
        self.lbl_status.setStyleSheet("color: #64748b;")
        bottom_bar.addWidget(self.lbl_status)

        layout.addLayout(bottom_bar)

    def set_text(self, text: str):
        """更新文本内容"""
        self.editor.setPlainText(text or "")
        self._update_stats()

    def get_text(self) -> str:
        """获取当前编辑器文本"""
        return self.editor.toPlainText()

    def set_status(self, status: str, is_error: bool = False):
        """更新状态词"""
        self.lbl_status.setText(status)
        if is_error:
            self.lbl_status.setStyleSheet("color: #ef4444;")
        else:
            self.lbl_status.setStyleSheet("color: #10b981;")

    def set_loading(self, is_loading: bool):
        """切换加载状态"""
        self.btn_fetch.setEnabled(not is_loading)
        self.btn_push.setEnabled(not is_loading)
        if hasattr(self, "btn_purge"):
            self.btn_purge.setEnabled(not is_loading)
        if is_loading:
            self.btn_fetch.setText("⏳ 同步中...")
        else:
            self.btn_fetch.setText("📥 拉取")

    def _update_stats(self):
        """实时统计行数与字符数"""
        text = self.editor.toPlainText()
        non_empty_lines = [l for l in text.splitlines() if l.strip()]
        self.lbl_stats.setText(f"共 {len(non_empty_lines)} 行 | {len(text)} 字符")



class PageCloudText(QWidget):
    """
    云端文本页面：管理向远端 Cloudflare Worker 自动推送/拉取的三个核心分发文本
    （/auto.txt、/verified.txt、/）
    """
    fetch_done_signal = pyqtSignal(str, bool, str)   # (subpath, success, content_or_err)
    push_done_signal = pyqtSignal(str, bool, str)    # (subpath, success, message)

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageCloudText")
        self.cards = {}
        self._initial_loaded = False

        self.init_ui()
        self._connect_signals()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. 顶部 Header 区域
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self.title_label = TitleLabel("☁️ 云端文本管理", self)
        title_box.addWidget(self.title_label)

        self.desc_label = BodyLabel(
            "查看与编辑 Cloudflare Worker 远端分发的三大核心文本（优质精选 /auto.txt、沉淀孵化 /verified.txt、典藏常青 /）。支持在线双向同步与手动强推覆盖。",
            self,
        )
        self.desc_label.setStyleSheet("color: #94a3b8;")
        title_box.addWidget(self.desc_label)
        header_layout.addLayout(title_box, 1)

        # 全局操作按钮组
        self.btn_fetch_all = PushButton("📥 一键拉取所有", self)
        self.btn_fetch_all.clicked.connect(self._on_fetch_all_clicked)
        header_layout.addWidget(self.btn_fetch_all)

        self.btn_push_all = PrimaryPushButton("📤 一键强推所有", self)
        self.btn_push_all.clicked.connect(self._on_push_all_clicked)
        header_layout.addWidget(self.btn_push_all)

        main_layout.addLayout(header_layout)

        # 2. 三列分栏卡片布局
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(14)

        # 卡片 1: /auto.txt (优质精选)
        card_auto = CloudTextCard(
            title="⭐ 优质精选池 (/auto.txt)",
            subpath="/auto.txt",
            desc="大优选产出的优质精选节点，直接下发自适应策略组",
            parent=self,
        )
        self.cards["/auto.txt"] = card_auto
        columns_layout.addWidget(card_auto, 1)

        # 卡片 2: /verified.txt (沉淀孵化)
        card_ver = CloudTextCard(
            title="⏳ 沉淀孵化池 (/verified.txt)",
            subpath="/verified.txt",
            desc="连续多轮测速达标的稳定节点，处于孵化培育状态",
            parent=self,
        )
        self.cards["/verified.txt"] = card_ver
        columns_layout.addWidget(card_ver, 1)

        # 卡片 3: / (典藏常青)
        card_root = CloudTextCard(
            title="🏆 典藏常青池 (/)",
            subpath="/",
            desc="高频考核历练出的极品常青树节点，顶级优先级直通",
            parent=self,
        )
        self.cards["/"] = card_root
        columns_layout.addWidget(card_root, 1)

        # 卡片 4: /pending.txt (待测归收池)
        card_pending = CloudTextCard(
            title="⚪ 待测归收池 (/pending.txt)",
            subpath="/pending.txt",
            desc="存放 C 段挖掘与移出黑名单节点，全量大优选启动时自动读取重新纳测",
            parent=self,
        )
        self.cards["/pending.txt"] = card_pending
        columns_layout.addWidget(card_pending, 1)

        main_layout.addLayout(columns_layout, 1)

    def _connect_signals(self):
        """绑定内部信号"""
        for subpath, card in self.cards.items():
            card.fetch_requested.connect(self._handle_card_fetch)
            card.push_requested.connect(self._handle_card_push)
            if hasattr(card, "btn_purge"):
                card.btn_purge.clicked.connect(self._on_manual_purge_clicked)

        self.fetch_done_signal.connect(self._on_fetch_done)
        self.push_done_signal.connect(self._on_push_done)

    def showEvent(self, event):
        """初次切入页面时自动静默拉取三大文本"""
        super().showEvent(event)
        if not self._initial_loaded:
            self._initial_loaded = True
            self._on_fetch_all_clicked(silent=True)

    # ==================== 单卡片操作 ====================

    def _handle_card_fetch(self, subpath: str):
        """单卡片拉取请求"""
        card = self.cards.get(subpath)
        if card:
            card.set_loading(True)
            card.set_status("正在从云端拉取...")

        def _worker():
            ok, content = self.controller.fetch_cloud_text(subpath=subpath)
            self.fetch_done_signal.emit(subpath, ok, content)

        threading.Thread(target=_worker, daemon=True).start()

    def _handle_card_push(self, subpath: str, text: str):
        """单卡片强推请求"""
        card = self.cards.get(subpath)
        title = card.title_text if card else subpath

        # 强推前二次确认
        w = MessageBox(
            "确认强推覆盖云端",
            f"确定要将当前编辑的内容强推覆盖至云端 {subpath} 吗？\n\n"
            f"⚠️ 目标模块：{title}\n"
            "该操作将立即直接覆盖远端 Cloudflare Worker 文本存储，不可撤销！",
            self.window(),
        )
        if not w.exec():
            return

        if card:
            card.set_loading(True)
            card.set_status("正在强推至云端...")

        def _worker():
            ok, msg = self.controller.push_cloud_text(subpath=subpath, text=text)
            self.push_done_signal.emit(subpath, ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    # ==================== 批量全局操作 ====================

    def _on_fetch_all_clicked(self, silent: bool = False):
        """一键拉取全部"""
        if not silent:
            InfoBar.info("正在拉取", "正在向 Cloudflare Worker 并发拉取三大分发文本...", duration=2000, parent=self.window())
        for subpath in self.cards:
            self._handle_card_fetch(subpath)

    def _on_push_all_clicked(self):
        """一键强推全部"""
        w = MessageBox(
            "确认批量强推全部云端文本",
            "确定要将当前编辑的全部 3 个文本（/auto.txt、/verified.txt、/）强推覆盖至云端吗？\n\n"
            "⚠️ 该操作将同时重写远端 Cloudflare Worker 全部数据，不可撤销！",
            self.window(),
        )
        if not w.exec():
            return

        InfoBar.info("正在强推", "正在向 Cloudflare Worker 批量推送三大分发文本...", duration=2000, parent=self.window())
        for subpath, card in self.cards.items():
            card.set_loading(True)
            card.set_status("正在强推至云端...")
            text = card.get_text()

            def _worker(sp=subpath, t=text):
                ok, msg = self.controller.push_cloud_text(subpath=sp, text=t)
                self.push_done_signal.emit(sp, ok, msg)

            threading.Thread(target=_worker, daemon=True).start()

    # ==================== 信号回调处理 ====================

    def _on_fetch_done(self, subpath: str, ok: bool, content: str):
        """拉取完成回调"""
        card = self.cards.get(subpath)
        if not card:
            return
        card.set_loading(False)
        if ok:
            card.set_text(content)
            card.set_status(f"拉取成功 ({time.strftime('%H:%M:%S')})", is_error=False)
            InfoBar.success("拉取成功", f"已成功拉取并更新 {subpath}", duration=2500, parent=self.window())
        else:
            card.set_status("拉取失败", is_error=True)
            InfoBar.error("拉取失败", f"{subpath}: {content}", duration=4000, parent=self.window())

    def _on_push_done(self, subpath: str, ok: bool, msg: str):
        """强推完成回调"""
        card = self.cards.get(subpath)
        if not card:
            return
        card.set_loading(False)
        if ok:
            card.set_status(f"强推成功 ({time.strftime('%H:%M:%S')})", is_error=False)
            InfoBar.success("强推成功", f"{subpath} 文本已成功写入远端 Worker！", duration=3000, parent=self.window())
        else:
            card.set_status("强推失败", is_error=True)
            InfoBar.error("强推失败", f"{subpath}: {msg}", duration=4500, parent=self.window())

    def _on_manual_purge_clicked(self):
        """用户在待测卡片上手动点击【🧹 联动清洗】的一键自愈操作"""
        card = self.cards.get("/pending.txt")
        if card:
            card.set_loading(True)
            card.set_status("正在比对全池清洗云端待测池...")

        def _worker():
            purged = self.controller.purge_pending_endpoints_from_cloud()
            time.sleep(0.5)
            # 清洗后自动重拉最新内容刷新编辑器
            ok, content = self.controller.fetch_cloud_text("/pending.txt")
            self.fetch_done_signal.emit("/pending.txt", ok, content)

        import threading
        threading.Thread(target=_worker, daemon=True).start()



