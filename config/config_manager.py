import os
import json
import threading
import shutil

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
            try:
                if os.path.exists(self.config_path):
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        self.config_data = json.load(f)
                else:
                    self.config_data = {}
            except Exception as e:
                print(f"读取配置文件异常，已使用空配置兜底: {e}")
                self.config_data = {}

    def save_config(self, new_data=None):
        if new_data is not None:
            self.config_data.update(new_data)
        
        with self.file_lock:
            temp_path = self.config_path + ".tmp"
            try:
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(self.config_data, f, indent=4, ensure_ascii=False)
                # 原子替换，防止写入一半断电导致配置丢失为 0KB
                os.replace(temp_path, self.config_path)
            except Exception as e:
                print(f"配置文件安全写入失败，已拦截异常: {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass

    def get(self, key, default=None):
        with self.file_lock:
            return self.config_data.get(key, default)

    def set(self, key, value):
        with self.file_lock:
            self.config_data[key] = value
            self.save_config()
