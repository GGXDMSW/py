import threading

class BasePipeline:
    """
    流水线抽象基类：
    提供统一的生命周期管理、中断取消控制与事件通知接口。
    """

    def __init__(self, on_log=None, on_status=None, on_finished=None, on_error=None, on_aborted=None):
        self.on_log = on_log or (lambda msg: None)
        self.on_status = on_status or (lambda status: None)
        self.on_finished = on_finished or (lambda *args: None)
        self.on_error = on_error or (lambda err: None)
        self.on_aborted = on_aborted or (lambda: None)

        self._is_running = False
        self._cancel_requested = False
        self._thread = None

    @property
    def is_running(self):
        return self._is_running

    def request_stop(self):
        self._cancel_requested = True

    def should_abort(self):
        return self._cancel_requested or not self._is_running

    def start(self, *args, **kwargs):
        if self._is_running:
            return
        self._is_running = True
        self._cancel_requested = False
        self._thread = threading.Thread(
            target=self._run_wrapper,
            args=args,
            kwargs=kwargs,
            daemon=True,
            name=self.__class__.__name__
        )
        self._thread.start()

    def _run_wrapper(self, *args, **kwargs):
        try:
            self.execute(*args, **kwargs)
        except Exception as ex:
            import traceback
            err_trace = traceback.format_exc()
            self.on_log(f"流水线发生未捕获异常:\n{err_trace}")
            self.on_error(err_trace)
        finally:
            self._is_running = False

    def execute(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement execute()")
