import re
import threading
import time

class SchedulerDaemon:
    """
    后台常驻定时调度守护服务：
    脱离 UI 线程，独立在守护线程中根据设定的时间点或定时间隔，自动触发大优选与优质池复检。
    """

    def __init__(self, get_config_fn, on_trigger_full, on_trigger_fav):
        self.get_config_fn = get_config_fn
        self.on_trigger_full = on_trigger_full
        self.on_trigger_fav = on_trigger_fav

        self._thread = None
        self._running = False
        self.last_full_run_timestamp = 0.0
        self.last_fav_run_timestamp = 0.0
        self.app_start_time = time.time()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="SchedulerDaemonThread")
        self._thread.start()

    def stop(self):
        self._running = False

    def update_last_run(self, full_ts=None, fav_ts=None):
        if full_ts is not None:
            self.last_full_run_timestamp = float(full_ts)
        if fav_ts is not None:
            self.last_fav_run_timestamp = float(fav_ts)

    def _loop(self):
        last_fixed_time_triggered = ""

        while self._running:
            time.sleep(3)
            try:
                now = time.time()
                if now - self.app_start_time < 10.0:
                    continue

                cfg = self.get_config_fn()
                if not cfg or cfg.get("is_pipeline_running", False):
                    continue

                now_dt = time.localtime(now)
                cur_hhmm = time.strftime("%H:%M", now_dt)
                cur_minute_key = time.strftime("%Y-%m-%d %H:%M", now_dt)

                # 1. 全自动大优选定时检测
                if cfg.get("schedule_enabled", False):
                    triggered_full = False
                    trigger_reason_full = ""

                    fixed_times_str = cfg.get("schedule_times", "").strip()
                    if fixed_times_str:
                        times_list = [t.strip() for t in re.split(r"[,，\s]+", fixed_times_str) if t.strip()]
                        if cur_hhmm in times_list and cur_minute_key != last_fixed_time_triggered:
                            last_fixed_time_triggered = cur_minute_key
                            triggered_full = True
                            trigger_reason_full = f"到达设定时间 {cur_hhmm}"

                    interval_str = str(cfg.get("schedule_interval", "")).strip()
                    if not triggered_full and interval_str.isdigit() and int(interval_str) > 0:
                        interval_sec = int(interval_str) * 60
                        elapsed_since_last = now - self.last_full_run_timestamp
                        if elapsed_since_last >= interval_sec:
                            triggered_full = True
                            elapsed_mins = int(elapsed_since_last // 60)
                            trigger_reason_full = f"距离上次测试已过 {elapsed_mins} 分钟"

                    if triggered_full:
                        self.on_trigger_full(trigger_reason_full)
                        continue

                # 2. 优质池复测定时检测
                if cfg.get("fav_schedule_enabled", False) and not cfg.get("is_pipeline_running", False):
                    fav_interval_str = str(cfg.get("fav_schedule_interval", "")).strip()
                    if fav_interval_str.isdigit() and int(fav_interval_str) > 0:
                        fav_interval_sec = int(fav_interval_str) * 60
                        elapsed_fav = now - self.last_fav_run_timestamp
                        if elapsed_fav >= fav_interval_sec:
                            elapsed_fav_mins = int(elapsed_fav // 60)
                            r_reason = f"距离上次优质复测已过 {elapsed_fav_mins} 分钟"
                            self.on_trigger_fav(r_reason)

            except Exception:
                pass
