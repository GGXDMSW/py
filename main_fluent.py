"""
Clash Verge 节点管理助手 (Fluent 版)
规范化主启动入口
"""
import os
import sys
import traceback

# 优先导入 qfluentwidgets 以确定加载的 Qt 运行时绑定 (PyQt5 或 PyQt6)
import qfluentwidgets

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QMessageBox
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QMessageBox

from gui_fluent.main_window import MainWindow


def run_fluent_app():
    """
    启动 Fluent UI 主程序
    """
    try:
        # 高分屏清晰渲染适配 (Win11)
        if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )

        if hasattr(Qt, "AA_EnableHighDpiScaling"):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, "AA_UseHighDpiPixmaps"):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setApplicationName("ClashVergeAssistantFluent")

        window = MainWindow()
        window.show()

        sys.exit(app.exec_() if hasattr(app, "exec_") else app.exec())
    except Exception:
        err_msg = traceback.format_exc()
        try:
            with open("error_fluent_startup.log", "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        try:
            QMessageBox.critical(None, "启动异常", f"Fluent 版程序启动失败：\n{err_msg}")
        except Exception:
            print(f"Fluent 版程序启动失败：\n{err_msg}")


if __name__ == "__main__":
    run_fluent_app()
