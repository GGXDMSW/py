"""
Clash Verge 节点管理助手 (7天Colo长效防漂移与C段挖掘版)
规范化工程主启动入口
"""
import os
import sys
import tkinter as tk
import traceback
from tkinter import messagebox

from gui.app import ClashVergeTabsManager


def run_app(argv=None):
    """
    主程序启动器：
    处理命令行参数 (--tray 托盘静默启动)、构建主窗口与全局崩溃日志追踪
    """
    if argv is None:
        argv = sys.argv

    try:
        root = tk.Tk()
        app = ClashVergeTabsManager(root)
        if "--tray" in argv:
            root.withdraw()
        root.mainloop()
    except Exception:
        err_msg = traceback.format_exc()
        try:
            with open("error_startup.log", "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        try:
            messagebox.showerror("启动异常", f"程序启动失败：\n{err_msg}")
        except Exception:
            print(f"启动异常：\n{err_msg}")


if __name__ == "__main__":
    run_app()
