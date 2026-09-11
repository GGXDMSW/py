import ctypes
import os
import subprocess
import sys
import time
import tkinter as tk
import winreg
import winsound

try:
    from PIL import Image, ImageDraw
    TRAY_IMAGE_SUPPORTED = True
except ImportError:
    TRAY_IMAGE_SUPPORTED = False

from config.settings import RUN_REG_KEY, REG_APP_NAME, THEME


def send_system_notification(title, message):
    """
    发送 Windows 系统级 Toast 通知并附带系统提示音
    """
    try:
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass

    t_clean = title.replace("'", "''").replace('"', "")
    m_clean = message.replace("'", "''").replace('"', "")
    ps_script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
        "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
        "$toastXml = [xml]$template.GetXml(); "
        f"$toastXml.GetElementsByTagName('text')[0].AppendChild($toastXml.CreateTextNode('{t_clean}')) > $null; "
        f"$toastXml.GetElementsByTagName('text')[1].AppendChild($toastXml.CreateTextNode('{m_clean}')) > $null; "
        "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
        "$xml.LoadXml($toastXml.OuterXml); "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Clash Verge 节点助手').Show($toast);"
    )
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            creationflags=0x08000000,
        )
    except Exception:
        pass


def is_run_as_admin():
    """
    检测当前进程是否具备 Windows 管理员提权权限
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def trigger_verge_reactivate_hotkey():
    """
    模拟系统级全局组合热键 (Ctrl + Shift + F12) 通知 Clash Verge 重新激活装载规则
    """
    user32 = ctypes.windll.user32
    VK_CONTROL = 0x11
    VK_SHIFT = 0x10
    VK_F12 = 0x7B
    KEYEVENTF_KEYUP = 0x0002

    try:
        # 释放潜在的物理按键粘滞状态
        for vk in [VK_CONTROL, VK_SHIFT, VK_F12]:
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)

        # 模拟按下组合键
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(VK_SHIFT, 0, 0, 0)
        user32.keybd_event(VK_F12, 0, 0, 0)
        time.sleep(0.15)  # 保持 150ms 确保被系统级热键总线捕获

        # 模拟释放组合键
        user32.keybd_event(VK_F12, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        return True, ""
    except Exception as e:
        return False, str(e)


def create_tray_icon_image():
    """
    动态生成 64x64 现代蓝色渐变系统托盘矢量图标
    """
    if not TRAY_IMAGE_SUPPORTED:
        return None
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill="#2563eb", outline="#38bdf8", width=3)
    draw.polygon([(34, 12), (22, 34), (32, 34), (30, 52), (42, 30), (32, 30)], fill="#ffffff")
    return img


def check_boot_startup_registry():
    """
    检查注册表自启项
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_KEY, 0, winreg.KEY_READ)
        _, _ = winreg.QueryValueEx(key, REG_APP_NAME)
        winreg.CloseKey(key)
        return True
    except WindowsError:
        return False


def set_boot_startup_registry(enable=True):
    """
    开启或关闭 Windows 开机自启（写入当前用户注册表）
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_KEY, 0, winreg.KEY_SET_VALUE)
        if enable:
            python_exe = sys.executable
            pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw_exe):
                pythonw_exe = python_exe
            script_path = os.path.abspath(sys.argv[0])
            cmd_val = f'"{pythonw_exe}" "{script_path}" --tray'
            winreg.SetValueEx(key, REG_APP_NAME, 0, winreg.REG_SZ, cmd_val)
        else:
            try:
                winreg.DeleteValue(key, REG_APP_NAME)
            except WindowsError:
                pass
        winreg.CloseKey(key)
        return True, ""
    except Exception as e:
        return False, str(e)


def create_modern_btn(parent, text, command, bg, fg="#ffffff", hover_bg=None, font_size=9, **kwargs):
    """
    创建现代化扁平样式按钮，内置鼠标滑过悬停变色动效
    """
    if hover_bg is None:
        hover_bg = THEME["bg_hover"]

    padx = kwargs.pop("padx", 12)
    pady = kwargs.pop("pady", 6)

    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        activebackground=hover_bg,
        activeforeground=fg,
        relief="flat",
        bd=0,
        padx=padx,
        pady=pady,
        cursor="hand2",
        font=("Microsoft YaHei UI", font_size, "bold"),
        **kwargs,
    )

    def on_enter(e):
        if btn["state"] != "disabled":
            btn.config(bg=hover_bg)

    def on_leave(e):
        if btn["state"] != "disabled":
            btn.config(bg=bg)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn
