from PyQt5.QtCore import QObject, pyqtSignal
import threading

class SignalBus(QObject):
    """
    全局信号总线，解决非主线程跨线程更新 UI 引发的崩溃隐患。
    所有子线程（探针测速、任务调度等），必须通过 emit 发送信号，严禁直接操作界面控件。
    """
    _instance = None
    _init_lock = threading.Lock()

    # 节点数据注入信号 (参数: 节点数据列表)
    node_table_update = pyqtSignal(list)
    # 日志面板打印信号 (参数: 日志级别, 日志内容)
    log_print = pyqtSignal(str, str)
    # 状态流转通知信号 (参数: 状态信息)
    pool_transition = pyqtSignal(str)

    def __new__(cls):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

# 全局单例实例化，供各多线程模块安全调用
global_signals = SignalBus()
