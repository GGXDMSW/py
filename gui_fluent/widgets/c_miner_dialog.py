"""
C 段全量高并发极速深度挖掘对话框 (CSegmentMinerDialog)
基于 PyQt-Fluent-Widgets 构建，支持对 /24 网段 254 个 IP 进行并发 TCP 测延与真实 Colo 机房判定，
并提供一键批量导入至优质精选池、沉淀孵化池或典藏常青池。
"""
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QColor, QBrush, QFont
    from PyQt5.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QWidget,
        QProgressDialog,
    )
else:
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QColor, QBrush, QFont
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QWidget,
        QProgressDialog,
    )

from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
    LineEdit,
    InfoBar,
    MessageBox,
    FluentIcon,
)

from services.probe_service import get_c_segment_ips, tcp_ping, get_cf_colo_raw
from services.colo_service import is_asian_node


class CSegmentMinerWorker(QThread):
    """
    C 段深度挖掘后台扫描线程：
    分两阶段进行：
      阶段 1: 50 线程高并发全网段 TCP Ping，快速筛选延迟 <= 门槛的活跃 IP
      阶段 2: 20 线程对达标 IP 进行 Cloudflare 真实机房 (Colo) 测定
    """
    progress_signal = pyqtSignal(int, int)  # (done, total)
    stage_signal = pyqtSignal(str)          # 阶段提示文本
    finished_signal = pyqtSignal(list)      # 扫描结果 list[dict]

    def __init__(self, c_ips: list[str], port: int = 443, threshold: int = 130, parent=None):
        super().__init__(parent)
        self.c_ips = list(c_ips)
        self.port = port
        self.threshold = threshold
        self._is_stopped = False

    def stop(self):
        self._is_stopped = True
        self.requestInterruption()

    def run(self):
        total = len(self.c_ips)
        if total == 0:
            self.finished_signal.emit([])
            return

        # 阶段 1: 全并发 TCP 测延
        self.stage_signal.emit(f"正在全并发 TCP 测延 (共 {total} 个 IP)...")
        results = []
        done_cnt = [0]

        def _scan_one(ip):
            if self._is_stopped or self.isInterruptionRequested():
                return None
            rtt = tcp_ping(ip, port=self.port, timeout=1.2)
            done_cnt[0] += 1
            if done_cnt[0] % 10 == 0 or done_cnt[0] >= total:
                self.progress_signal.emit(done_cnt[0], total)
            if rtt < 99999 and rtt <= self.threshold:
                return (ip, rtt)
            return None

        with ThreadPoolExecutor(max_workers=50) as ex:
            for res in ex.map(_scan_one, self.c_ips):
                if res:
                    results.append(res)
                if self._is_stopped or self.isInterruptionRequested():
                    break

        if self._is_stopped or self.isInterruptionRequested():
            self.stage_signal.emit("扫描已中止")
            self.finished_signal.emit([])
            return

        if not results:
            self.stage_signal.emit(f"TCP 测延完成：未发现延迟 ≤ {self.threshold}ms 的 IP")
            self.finished_signal.emit([])
            return

        # 阶段 2: 真实 Colo 机房校准 (严禁降级回退至普通地理属地，杜绝非 CF 服务器伪充优选)
        self.stage_signal.emit(f"TCP 达标 {len(results)} 个，正在严格鉴权 Cloudflare 真实机房...")
        colo_map = {}

        def _probe_colo(ip):
            if self._is_stopped or self.isInterruptionRequested():
                return
            # 严格关闭地理降级回退 (enable_geo_fallback=False)，确保只有真正响应 /cdn-cgi/trace 的 Cloudflare 机房才算达标
            c_code, c_disp = get_cf_colo_raw(ip, port=self.port, timeout=1.8, enable_geo_fallback=False)
            colo_map[ip] = (c_code, c_disp)

        with ThreadPoolExecutor(max_workers=20) as ex:
            for _ in ex.map(_probe_colo, [r[0] for r in results]):
                if self._is_stopped or self.isInterruptionRequested():
                    break

        # 按延迟从小到大排序
        results.sort(key=lambda x: x[1])

        final_rows = []
        valid_cf_count = 0
        for ip, rtt in results:
            c_code, c_disp = colo_map.get(ip, ("-", "-"))
            # 必须严格具备 Cloudflare Anycast 数据中心三字代码才视为达标
            is_cf = bool(c_code and c_code != "-" and c_code != "ANY")
            if is_cf:
                colo_label = c_disp
                status_text = "✅ 极速达标"
                valid_cf_count += 1
            else:
                colo_label = "非CF机房" if not c_disp or c_disp == "-" else f"{c_disp} (非CF)"
                status_text = "❌ 非CF机房"

            final_rows.append({
                "ip": ip,
                "port": self.port,
                "delay": rtt,
                "delay_str": f"{rtt} ms",
                "colo_code": c_code if is_cf else "-",
                "colo": colo_label,
                "status": status_text,
                "is_valid_cf": is_cf,
            })

        self.finished_signal.emit(final_rows)


class PostImportWorker(QThread):
    """
    C 段导入后全链路闭环专职工作线程：
    继承 QThread 并通过 pyqtSignal 跨线程安全通信，彻底杜绝 UI 假死与 QObject 亲和性冲突。
    """
    step_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, list)

    def __init__(self, controller, target: str, count: int, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.target = target
        self.count = count

    def run(self):
        pool_names = {
            "fav": "【⭐ 优质精选池】",
            "verified": "【⏳ 沉淀孵化池】",
            "stars": "【🏆 典藏管理池】",
            "pending": "【⚪ 活跃待测池】",
        }
        target_name = pool_names.get(self.target, "目标池")
        logs_step = [f"✅ 本地收编: 成功收录 {self.count} 个极速 IP 至 {target_name}"]
        try:
            # 步骤 1: 尝试推送至 Cloudflare Worker 云端
            self.step_signal.emit("[1/4] 正在同步推送至 Cloudflare Worker...")
            ok_w = False
            msg_w = ""
            if self.target == "fav":
                fav_lines = []
                seen_eps = set()
                with self.controller.state.lock:
                    for f in list(self.controller.state.favorites):
                        ep_val = self.controller._get_ep(f) or str(f)
                        if not ep_val or ep_val in seen_eps or ep_val == "127.0.0.1:443":
                            continue
                        seen_eps.add(ep_val)
                        colo = self.controller.state.node_colo.get(f, self.controller.state.node_colo.get(ep_val, "JP"))
                        if not colo or colo == "-":
                            colo = "亚洲"
                        spd = self.controller.state.node_speeds.get(f, self.controller.state.node_speeds.get(ep_val, 0.0))
                        reason = self.controller.state.fav_reasons.get(f, self.controller.state.fav_reasons.get(ep_val, ""))
                        if spd and spd > 0.1:
                            uniform_name = f"{colo} {spd:.2f} MB/s"
                        elif "C段" in reason:
                            uniform_name = f"{colo} [C段挖掘]"
                        else:
                            uniform_name = colo
                        fav_lines.append(f"{ep_val}#{uniform_name}")
                        self.controller.state.cloud_endpoints[ep_val] = uniform_name
                        if ":" in ep_val:
                            self.controller.state.cloud_endpoints[ep_val.split(":")[0]] = uniform_name
                payload = ("\r\n".join(fav_lines) + "\r\n") if fav_lines else "# empty\r\n"
                ok_w, msg_w = self.controller.push_text_to_cf_worker(payload, subpath="/auto.txt")
            elif self.target == "verified":
                with self.controller.state.lock:
                    lines = [f"{v['endpoint']}#{v.get('remark', '')}" for v in self.controller.state.verified_nodes.values() if v.get("endpoint")]
                payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
                ok_w, msg_w = self.controller.push_text_to_cf_worker(payload, subpath="/verified.txt")
            elif self.target == "stars":
                with self.controller.state.lock:
                    lines = [f"{item.get('endpoint', '')}#{item.get('remark', '')}" for item in self.controller.state.stars_nodes if item.get('endpoint')]
                payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
                ok_w, msg_w = self.controller.push_text_to_cf_worker(payload, subpath="")
            elif self.target == "pending":
                # 同步追加推送到 /pending.txt 并自动排查已存在的精选与黑名单
                pending_items = getattr(self, "pending_items", [])
                ok_w, msg_w = self.controller.append_pending_endpoints_to_cloud_sync(pending_items)

            if ok_w:
                logs_step.append("✅ 云端同步: 已成功推送到 Cloudflare Worker")
                self.controller.log(f"Worker 同步成功: {msg_w}")
            else:
                logs_step.append(f"⚠️ 云端同步: {msg_w}")
                self.controller.log(f"Worker 同步提示: {msg_w}")

            # 重新拉取云端映射
            self.controller.fetch_cloud_endpoints_sync()
            self.controller.fetch_pending_endpoints_sync()
            time.sleep(0.5)

            # 步骤 2: 在线拉取更新订阅 (拉取最新 profiles yaml 并重新解析)
            self.step_signal.emit("[2/4] 正在拉取远程最新订阅并解析节点...")
            up_ok, up_msg = self.controller.update_remote_subscription_sync()
            if up_ok:
                logs_step.append(f"✅ 订阅更新: {up_msg}")
            else:
                logs_step.append(f"⚠️ 订阅更新: {up_msg}")

            # 步骤 3: 写入 Script.js 并触发热键热更激活订阅
            self.step_signal.emit("[3/4] 正在写入 Script.js 并触发热更激活...")
            self.controller.generate_script_and_reload()
            logs_step.append("✅ 热更激活: 已生成 Script.js 并模拟热键激活")

            # 步骤 4: 探测 Clash 内核装载状态
            self.step_signal.emit("[4/4] 正在探测 Clash 内核装载状态...")
            loaded_ok, loaded_msg = self.controller.clash_client.wait_for_kernel_reload(
                self.controller.state.all_nodes, max_wait_sec=10
            )
            logs_step.append(f"{'✅' if loaded_ok else '⚠️'} 内核装载: {loaded_msg}")
            self.controller.log(f"内核探测反馈: {loaded_msg}")

            # 保存状态与触发 UI 刷新
            self.controller.save_config(self.controller.get_state_snapshot())
            self.controller.data_changed.emit()

            final_ok = ok_w or up_ok or loaded_ok
            self.finished_signal.emit(final_ok, f"已成功收编 {self.count} 个 IP 并完成热更闭环！", logs_step)

        except Exception as ex:
            err_msg = f"收编后闭环处理异常: {ex}"
            self.controller.log(f"❌ {err_msg}")
            self.finished_signal.emit(False, err_msg, logs_step)


class CSegmentMinerDialog(QDialog):
    """
    Fluent 风格 C 段全量深度挖掘对话框
    """

    COLUMN_HEADERS = ["IP 地址", "端口", "TCP 握手延迟", "真实机房 (Colo)", "评估状态"]
    COLUMN_WIDTHS = [180, 75, 130, 200, 130]

    def __init__(self, seed_ip: str, seed_port: int = 443, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.seed_ip = seed_ip
        self.seed_port = seed_port
        self.c_ips = get_c_segment_ips(seed_ip)
        self.c_segment_name = ".".join(seed_ip.split(".")[:3]) + ".0/24" if "." in seed_ip else seed_ip
        self.worker = None
        self._post_worker = None
        self._current_results = []

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"🔍 C 段全量极速深度挖掘 - {self.c_segment_name}")
        self.setMinimumSize(920, 600)
        self.resize(960, 640)

        # 深色窗口风格
        self.setStyleSheet("""
            QDialog {
                background-color: #151822;
                color: #e2e8f0;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QTableWidget {
                background-color: #181b26;
                color: #e2e8f0;
                gridline-color: rgba(255, 255, 255, 0.06);
                border: 1px solid #2c3246;
                border-radius: 6px;
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
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 1. 顶部控制栏
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        top_layout.addWidget(QLabel("目标 IP / 种子 IP:", self))
        self.ip_edit = LineEdit(self)
        self.ip_edit.setText(self.seed_ip)
        self.ip_edit.setFixedWidth(160)
        self.ip_edit.setPlaceholderText("输入 IPv4 地址，如 172.64.229.1")
        self.ip_edit.textChanged.connect(self._on_ip_input_changed)
        top_layout.addWidget(self.ip_edit)

        self.lbl_seg_info = QLabel(f"({self.c_segment_name})", self)
        self.lbl_seg_info.setStyleSheet("color: #38bdf8; font-size: 12px;")
        top_layout.addWidget(self.lbl_seg_info)

        top_layout.addWidget(QLabel("端口:", self))
        self.port_edit = LineEdit(self)
        self.port_edit.setText(str(self.seed_port))
        self.port_edit.setFixedWidth(65)
        top_layout.addWidget(self.port_edit)

        top_layout.addWidget(QLabel("延迟门槛(≤ ms):", self))
        self.threshold_edit = LineEdit(self)
        self.threshold_edit.setText("130")
        self.threshold_edit.setFixedWidth(65)
        top_layout.addWidget(self.threshold_edit)

        self.lbl_status = QLabel(f"准备就绪 (共 {len(self.c_ips)} 个 IP)", self)
        self.lbl_status.setStyleSheet("color: #8d98af;")
        top_layout.addWidget(self.lbl_status)

        top_layout.addStretch()

        self.btn_sel_all = PushButton("全选达标", self)
        self.btn_sel_all.clicked.connect(self._select_all_rows)
        top_layout.addWidget(self.btn_sel_all)

        self.btn_sel_none = PushButton("清空选择", self)
        self.btn_sel_none.clicked.connect(self._clear_selection)
        top_layout.addWidget(self.btn_sel_none)

        layout.addLayout(top_layout)

        # 2. 中间结果表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(28)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        layout.addWidget(self.table)

        # 3. 底部操作栏
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.btn_start = PrimaryPushButton("🚀 开始极速挖掘", self)
        self.btn_start.clicked.connect(self._start_mining)
        bottom_layout.addWidget(self.btn_start)

        self.btn_stop = PushButton("⏹ 停止", self)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_mining)
        bottom_layout.addWidget(self.btn_stop)

        bottom_layout.addStretch()

        self.btn_import_pending = PushButton("📥 导入【⚪ 活跃待测池】", self)
        self.btn_import_pending.clicked.connect(lambda: self._import_to_pool("pending"))
        bottom_layout.addWidget(self.btn_import_pending)

        self.btn_import_fav = PushButton("📥 导入【⭐ 优质精选池】", self)
        self.btn_import_fav.clicked.connect(lambda: self._import_to_pool("fav"))
        bottom_layout.addWidget(self.btn_import_fav)

        self.btn_import_verified = PushButton("📥 导入【⏳ 沉淀孵化池】", self)
        self.btn_import_verified.clicked.connect(lambda: self._import_to_pool("verified"))
        bottom_layout.addWidget(self.btn_import_verified)

        self.btn_import_stars = PushButton("📥 导入【🏆 典藏管理池】", self)
        self.btn_import_stars.clicked.connect(lambda: self._import_to_pool("stars"))
        bottom_layout.addWidget(self.btn_import_stars)

        layout.addLayout(bottom_layout)

    def _select_all_rows(self):
        """全选所有真正属于 Cloudflare 的达标行"""
        self.table.clearSelection()
        for row_idx, r in enumerate(self._current_results):
            if r.get("status") == "✅ 极速达标":
                self.table.selectRow(row_idx)

    def _clear_selection(self):
        self.table.clearSelection()

    def _on_ip_input_changed(self, text: str):
        ip = text.strip()
        parts = ip.split(".")
        if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
            seg = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            self.lbl_seg_info.setText(f"({seg})")
        else:
            self.lbl_seg_info.setText("(无效 IP 格式)")

    def _start_mining(self):
        if self.worker and self.worker.isRunning():
            return

        target_ip = self.ip_edit.text().strip()
        m = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3})$", target_ip)
        if not m:
            InfoBar.warning("输入错误", "请输入合法的 IPv4 格式地址（如 172.64.229.1）！", parent=self)
            return

        # 动态重新生成 254 个 C 段 IP 列表
        self.c_ips = get_c_segment_ips(target_ip)
        self.c_segment_name = ".".join(target_ip.split(".")[:3]) + ".0/24"
        self.setWindowTitle(f"🔍 C 段全量极速深度挖掘 - {self.c_segment_name}")

        port_str = self.port_edit.text().strip()
        port = int(port_str) if port_str.isdigit() else 443
        th_str = self.threshold_edit.text().strip()
        threshold = int(th_str) if th_str.isdigit() else 130

        self.table.clearContents()
        self.table.setRowCount(0)
        self._current_results = []

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText("正在准备并发测延...")

        self.worker = CSegmentMinerWorker(self.c_ips, port=port, threshold=threshold, parent=self)
        self.worker.progress_signal.connect(self._on_worker_progress)
        self.worker.stage_signal.connect(self._on_worker_stage)
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.start()

    def _stop_mining(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.btn_stop.setEnabled(False)
            self.lbl_status.setText("正在中止扫描...")

    def _on_worker_progress(self, done: int, total: int):
        self.lbl_status.setText(f"TCP 测延中: {done}/{total}")

    def _on_worker_stage(self, stage_text: str):
        self.lbl_status.setText(stage_text)

    def _on_worker_finished(self, results: list):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._current_results = list(results)

        self.table.clearContents()
        self.table.setRowCount(len(results))

        for row_idx, r in enumerate(results):
            ip_item = QTableWidgetItem(r.get("ip", ""))
            ip_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, ip_item)

            port_item = QTableWidgetItem(str(r.get("port", 443)))
            port_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 1, port_item)

            delay_item = QTableWidgetItem(r.get("delay_str", ""))
            delay_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            delay_item.setForeground(QBrush(QColor("#38bdf8")))
            self.table.setItem(row_idx, 2, delay_item)

            colo_item = QTableWidgetItem(r.get("colo", "-"))
            colo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, colo_item)

            status_item = QTableWidgetItem(r.get("status", ""))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color = "#34d399" if r.get("status") == "✅ 极速达标" else "#f87171"
            status_item.setForeground(QBrush(QColor(color)))
            self.table.setItem(row_idx, 4, status_item)

        valid_cnt = sum(1 for r in results if r.get("status") == "✅ 极速达标")
        self.lbl_status.setText(f"挖掘完成！共发现 {valid_cnt} 个极速达标 IP")

    def _get_target_rows(self) -> list[dict]:
        """获取需要导入的行数据（自动过滤掉非 CF 节点，确保流入池中的都是可用代理）"""
        if not self._current_results:
            return []

        selected_row_indices = sorted({idx.row() for idx in self.table.selectedIndexes()})
        if selected_row_indices:
            candidates = [self._current_results[i] for i in selected_row_indices if i < len(self._current_results)]
        else:
            candidates = list(self._current_results)

        # 强力阻断非 CF 节点流入优质池
        valid_targets = [r for r in candidates if r.get("status") == "✅ 极速达标"]
        return valid_targets

    def _import_to_pool(self, target: str):
        """导入至指定目标池"""
        if self.worker and self.worker.isRunning():
            self._stop_mining()
            time.sleep(0.2)

        rows_to_import = self._get_target_rows()
        if not rows_to_import:
            InfoBar.warning(
                title="提示",
                content="当前无挖掘结果可导入！请先点击开始挖掘。",
                duration=3000,
                parent=self,
            )
            return

        if not self.controller:
            return

        now_ts = time.time()
        cnt = 0
        pool_names = {
            "fav": "【⭐ 优质精选池】",
            "verified": "【⏳ 沉淀孵化池】",
            "stars": "【🏆 典藏管理池】",
            "pending": "【⚪ 活跃待测池】",
        }
        target_name = pool_names.get(target, "目标池")

        pending_items_to_send = []
        if target == "pending":
            with self.controller.state.lock:
                for r in rows_to_import:
                    ip = r.get("ip", "")
                    port = r.get("port", 443)
                    ep = f"{ip}:{port}"
                    colo = r.get("colo", "亚洲")
                    rem = f"{colo} [C段挖掘待测]"
                    pending_items_to_send.append((ep, rem))
                    self.controller.state.local_blacklist.discard(ep)
                    self.controller.state.speed_blacklist.discard(ep)
                    cnt += 1
        else:
            with self.controller.state.lock:
                for r in rows_to_import:
                    ip = r.get("ip", "")
                    port = r.get("port", 443)
                    ep = f"{ip}:{port}"
                    colo = r.get("colo", "-")
                    delay = r.get("delay", 0)
                    rem = f"{colo} [C段挖掘]"

                    if target == "fav":
                        self.controller.state.favorites.add(ep)
                        self.controller.state.fav_reasons[ep] = "C段深度挖掘"
                        if delay > 0:
                            self.controller.state.node_delays[ep] = delay
                            hist = self.controller.state.node_history.setdefault(ep, [])
                            hist.append(delay)
                            self.controller.state.node_history[ep] = hist[-6:]
                        if colo and colo != "-":
                            self.controller.state.node_colo[ep] = colo
                        self.controller.state.local_blacklist.discard(ep)
                        self.controller.state.speed_blacklist.discard(ep)
                        self.controller.state.cloud_endpoints[ep] = rem
                        if ":" in ep:
                            self.controller.state.cloud_endpoints[ep.split(":")[0]] = rem
                        self.controller.state.auto_endpoints.add(ep)
                        cnt += 1

                    elif target == "verified":
                        if ep not in self.controller.state.verified_nodes:
                            self.controller.state.verified_nodes[ep] = {
                                "endpoint": ep,
                                "colo": colo,
                                "remark": rem,
                                "first_seen": now_ts,
                                "passes": 1,
                                "fails": 0,
                                "delay": delay,
                                "speed": 0.0,
                                "reason": "C段深度挖掘入孵",
                            }
                            cnt += 1

                    elif target == "stars":
                        existing_eps = {s.get("endpoint", "") for s in self.controller.state.stars_nodes}
                        if ep not in existing_eps:
                            self.controller.state.stars_nodes.append({
                                "endpoint": ep,
                                "colo": colo,
                                "remark": rem,
                                "delay": delay,
                                "speed": 0.0,
                                "matched_name": "",
                                "reason": "C段深度挖掘加冕",
                            })
                            cnt += 1

        # 保存快照并记录日志
        self.controller.save_config(self.controller.get_state_snapshot())
        self.controller.log(f"📥 C 段挖掘: 已收录 {cnt} 个达标 IP 到 {target_name}")

        # 启动 PostImportWorker 统一执行 4 步全链路热更闭环
        self._post_worker = PostImportWorker(self.controller, target, cnt, parent=self)
        if target == "pending":
            self._post_worker.pending_items = pending_items_to_send

        progress_dialog = QProgressDialog("正在执行热更闭环处理...", "取消", 0, 0, self)
        progress_dialog.setWindowTitle("同步推进中")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.setStyleSheet("""
            QProgressDialog {
                background-color: #1a1d29;
                color: #e2e8f0;
            }
            QLabel {
                color: #38bdf8;
                font-size: 13px;
            }
        """)

        def _on_step(msg):
            progress_dialog.setLabelText(msg)

        def _on_post_finished(success, message, steps):
            progress_dialog.close()
            dlg_detail = "\n".join(steps)
            if success:
                MessageBox("收编与热更完成", f"{message}\n\n执行明细:\n{dlg_detail}", self).exec()
            else:
                MessageBox("热更过程提示", f"{message}\n\n执行明细:\n{dlg_detail}", self).exec()
            # 若导入的是精选、孵化或典藏，顺手触发一次云端待测池大扫除，清除已收编的端点
            if target != "pending":
                import threading
                threading.Thread(target=self.controller.purge_pending_endpoints_from_cloud, daemon=True).start()

        self._post_worker.step_signal.connect(_on_step)
        self._post_worker.finished_signal.connect(_on_post_finished)
        self._post_worker.start()
        progress_dialog.exec()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(500)
        if hasattr(self, "_post_worker") and self._post_worker and self._post_worker.isRunning():
            self._post_worker.wait(2000)
        super().closeEvent(event)
