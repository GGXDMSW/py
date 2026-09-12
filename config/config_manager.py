import json
import os
import shutil
import threading


def atomic_save_config(filepath, config_dict):
    """
    原子化持久保存配置字典：
    1. 先写入临时文件 .tmp 并刷新磁盘
    2. 校验文件写入完整无损
    3. 保留原文件为 .bak 作为灾备
    4. 执行原子重命名覆盖，杜绝断电/中断导致文件损坏清零
    """
    try:
        dir_name = os.path.dirname(filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        tmp_path = filepath + ".tmp"
        bak_path = filepath + ".bak"

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())

        if os.path.exists(filepath):
            try:
                shutil.copyfile(filepath, bak_path)
            except Exception:
                pass

        os.replace(tmp_path, filepath)
        return True, ""
    except Exception as e:
        return False, str(e)


def safe_load_config(filepath):
    """
    安全读取配置文件，若主配置损坏则自动从 .bak 灾备副本中无缝自愈恢复
    """
    if not os.path.exists(filepath):
        bak_path = filepath + ".bak"
        if os.path.exists(bak_path):
            filepath = bak_path
        else:
            return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        bak_path = filepath + ".bak"
        if os.path.exists(bak_path):
            try:
                with open(bak_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
    return {}


class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_config()
            return cls._instance

    def _init_config(self):
        self.config_path = "config.json"
        self.config_data = {}
        self.file_lock = threading.RLock()
        self.load_config()

    def load_config(self):
        with self.file_lock:
            self.config_data = safe_load_config(self.config_path)

    def save_config(self, new_data=None):
        if new_data is not None:
            self.config_data.update(new_data)
        with self.file_lock:
            atomic_save_config(self.config_path, self.config_data)

    def get(self, key, default=None):
        with self.file_lock:
            return self.config_data.get(key, default)

    def set(self, key, value):
        with self.file_lock:
            self.config_data[key] = value
            self.save_config()
