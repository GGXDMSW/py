import json
import os
import shutil
import time

def _json_default_serializer(obj):
    if isinstance(obj, (set, frozenset)):
        return list(obj)
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return str(obj)


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
            json.dump(config_dict, f, ensure_ascii=False, indent=2, default=_json_default_serializer)
            f.flush()
            os.fsync(f.fileno())

        # 如果已有原配置文件，先保留一份备份
        if os.path.exists(filepath):
            try:
                shutil.copyfile(filepath, bak_path)
            except Exception:
                pass

        # 原子重命名覆盖
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
        # 主文件损坏，尝试从备份读取
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


def prune_expired_history(node_colo_history, node_delay_history, max_days=7):
    """
    对 7 天时序桶与历史延迟进行定期老化清理，控制存储体积，杜绝内存/磁盘无限制膨胀
    """
    now_ts = time.time()
    cutoff = now_ts - max_days * 86400

    pruned_colo = {}
    for k, v in node_colo_history.items():
        if isinstance(v, list):
            valid_items = [
                item for item in v
                if isinstance(item, dict) and item.get("ts", 0) >= cutoff
            ]
            if valid_items:
                pruned_colo[k] = valid_items

    pruned_delay = {}
    for k, v in node_delay_history.items():
        if isinstance(v, list):
            valid_delays = [
                item for item in v
                if isinstance(item, dict) and item.get("ts", 0) >= cutoff and 0 < item.get("d", 0) < 99999
            ]
            if valid_delays:
                pruned_delay[k] = valid_delays[-30:]

    return pruned_colo, pruned_delay
