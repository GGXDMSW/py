import copy
import glob
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import yaml

from config.settings import PARENT_DIR, BASE_DIR, THEME
from utils.win32_utils import trigger_verge_reactivate_hotkey, is_run_as_admin


class ClashClient:
    """
    Clash / Clash Verge REST API 客户端：
    封装与内核 external-controller 的 HTTP 通信、延迟检测、模式切换与装载探测。
    """

    def __init__(self, host="127.0.0.1", port=9097, secret=""):
        self.host = host
        self.port = int(port)
        self.secret = str(secret).strip()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def update_credentials(self, port=None, secret=None):
        if port is not None:
            try:
                self.port = int(port)
            except (ValueError, TypeError):
                pass
        if secret is not None:
            self.secret = str(secret).strip()

    @staticmethod
    def auto_detect_credentials():
        """
        从 clash-verge.yaml 中自动检测并提取 external-controller 端口与 secret
        """
        port = 9097
        secret = ""
        clash_yaml = os.path.join(PARENT_DIR, "clash-verge.yaml")
        if os.path.exists(clash_yaml):
            try:
                with open(clash_yaml, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line_s = line.strip()
                        if line_s.startswith("external-controller:"):
                            m = re.search(r":(\d+)", line_s)
                            if m:
                                port = int(m.group(1))
                        elif line_s.startswith("secret:"):
                            m = re.search(r"secret:\s*['\"]?([^'\"\r\n]*)['\"]?", line_s)
                            if m and m.group(1).strip():
                                secret = m.group(1).strip()
            except Exception:
                pass
        return port, secret

    def call_api(self, endpoint, timeout=2.5, method="GET", data=None):
        url = f"http://{self.host}:{self.port}{endpoint}"
        req_data = data
        if isinstance(data, dict):
            req_data = json.dumps(data).encode("utf-8")
        elif isinstance(data, str):
            req_data = data.encode("utf-8")

        req = urllib.request.Request(url, data=req_data, method=method)
        if self.secret:
            req.add_header("Authorization", f"Bearer {self.secret}")
        if req_data:
            req.add_header("Content-Type", "application/json")

        try:
            with self.opener.open(req, timeout=timeout) as resp:
                res = resp.read()
                return json.loads(res.decode("utf-8")) if res else {}
        except Exception:
            return None

    def test_connection(self):
        """
        测试与内核的连接连通性
        返回: (is_connected: bool, version_info: str)
        """
        data = self.call_api("/version", timeout=1.5)
        if data and isinstance(data, dict) and "version" in data:
            return True, data.get("version", "")
        return False, ""

    def get_configs(self):
        return self.call_api("/configs", timeout=2.0) or {}

    def patch_configs(self, patch_dict):
        res = self.call_api("/configs", method="PATCH", data=patch_dict, timeout=2.0)
        return res is not None

    def get_mixed_port(self, default=7897):
        configs = self.get_configs()
        if configs:
            m_port = configs.get("mixed-port", 0)
            if m_port and int(m_port) > 0:
                return int(m_port)
            port = configs.get("port", 0)
            if port and int(port) > 0:
                return int(port)
        return default

    def get_proxies(self):
        data = self.call_api("/proxies", timeout=3.0)
        return data.get("proxies", {}) if (data and isinstance(data, dict)) else {}

    def query_proxy_delay(self, proxy_name, test_url, timeout_ms=1500):
        enc_name = urllib.parse.quote(proxy_name, safe="")
        enc_url = urllib.parse.quote(test_url, safe="")
        endpoint = f"/proxies/{enc_name}/delay?timeout={timeout_ms}&url={enc_url}"
        res = self.call_api(endpoint, timeout=(timeout_ms / 1000.0) + 0.6)
        if res and isinstance(res, dict) and "delay" in res:
            return res["delay"]
        return 99999

    def wait_for_kernel_reload(self, target_nodes, max_wait_sec=15):
        if not target_nodes:
            return True, "无节点需要装载"

        probe_sample = target_nodes[:30]
        start_t = time.time()
        retried_hotkey = False
        last_stat = "无数据"

        while time.time() - start_t < max_wait_sec:
            time.sleep(0.8)
            all_proxies_map = self.get_proxies()
            if not all_proxies_map:
                continue

            core_proxies = set(all_proxies_map.keys())
            auto_group = all_proxies_map.get("⚡ 自动选择", {})
            auto_members = set(auto_group.get("all", []))
            matched_in_auto = sum(1 for n in probe_sample if n in auto_members)
            matched = sum(1 for n in probe_sample if n in core_proxies)
            match_rate = matched / len(probe_sample)
            last_stat = f"内核节点数: {len(core_proxies)}，自动选择成员数: {len(auto_members)}"

            if matched_in_auto > 0 or match_rate >= 0.7:
                return True, f"内核装载成功，【⚡ 自动选择】策略组已包含 {len(auto_members)} 个优质节点"

            if time.time() - start_t > 3.5 and not retried_hotkey:
                trigger_verge_reactivate_hotkey()
                retried_hotkey = True

        admin_tip = "" if is_run_as_admin() else "【提示：当前以普通权限运行，已由内核API直连完成热同步】"
        sample_preview = probe_sample[:2]
        return False, f"超时未检测到装载。最新状态: {last_stat}。文件前2个节点: {sample_preview} {admin_tip}"


class ClashModeGuard:
    """
    Clash 运行模式安全熔断保护上下文管理器 (RAII 机制)：
    进入时：自动保存原分流模式 (如 rule)，无缝临时切换为指定模式 (如 global 用于精测测速)
    退出时：无论正常完成、发生异常中断还是用户强制取消，保证 100% 自动恢复原分流模式，杜绝网络瘫痪！
    """

    def __init__(self, client: ClashClient, temporary_mode="global"):
        self.client = client
        self.temporary_mode = temporary_mode
        self.original_mode = "rule"

    def __enter__(self):
        try:
            configs = self.client.get_configs()
            self.original_mode = configs.get("mode", "rule")
            if self.original_mode != self.temporary_mode:
                self.client.patch_configs({"mode": self.temporary_mode})
        except Exception:
            pass
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.client.patch_configs({"mode": self.original_mode})
        except Exception:
            pass
        return False


def find_cf_donor_node(yaml_filepath=None, active_profile=None, verified_nodes=None):
    """
    从订阅配置或验证池中寻找 1 个可用的 Cloudflare 协议母体
    要求包含 uuid/password、tls=True 及 valid host/sni
    """
    # 1. 尝试从 verified_nodes 中查找
    if verified_nodes and isinstance(verified_nodes, dict):
        for k, v in verified_nodes.items():
            if isinstance(v, dict):
                node_data = v.get("node_data") or v.get("detail")
                if isinstance(node_data, dict):
                    has_cred = bool(node_data.get("uuid") or node_data.get("password"))
                    tls = bool(node_data.get("tls", False))
                    sni = (
                        node_data.get("servername")
                        or node_data.get("sni")
                        or (node_data.get("ws-opts", {}).get("headers", {}).get("Host") if isinstance(node_data.get("ws-opts"), dict) else None)
                    )
                    if has_cred and tls and sni:
                        return copy.deepcopy(node_data)

    # 2. 从当前/指定的 YAML 订阅文件中查找
    paths = []
    if yaml_filepath and os.path.exists(yaml_filepath):
        paths.append(yaml_filepath)
    if active_profile:
        p = os.path.join(BASE_DIR, active_profile) if not os.path.isabs(active_profile) else active_profile
        if os.path.exists(p) and p not in paths:
            paths.append(p)
    # 检索 BASE_DIR 下的所有 yaml 文件
    for yf in glob.glob(os.path.join(BASE_DIR, "*.yaml")):
        if yf not in paths:
            paths.append(yf)

    cf_protocols = {"vless", "vmess", "trojan"}
    for ypath in paths:
        try:
            with open(ypath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_s = line.strip()
                    if line_s.startswith("- {") and any(proto in line_s for proto in cf_protocols):
                        try:
                            node = yaml.safe_load(line_s[2:])
                            if isinstance(node, dict):
                                n_type = str(node.get("type", "")).lower()
                                if n_type in cf_protocols:
                                    has_cred = bool(node.get("uuid") or node.get("password"))
                                    tls = bool(node.get("tls", False))
                                    sni = (
                                        node.get("servername")
                                        or node.get("sni")
                                        or (node.get("ws-opts", {}).get("headers", {}).get("Host") if isinstance(node.get("ws-opts"), dict) else None)
                                    )
                                    if has_cred and tls and sni:
                                        return node
                        except Exception:
                            continue
        except Exception:
            continue

    return None


def fission_clean_ips(donor_node: dict, clean_endpoints: list) -> list:
    """
    批量换头裂变：提取母体协议参数（uuid、path、sni、tls 等），
    对纯净 Clean IP 端点批量克隆，替换 server 与 port，构建合法 Proxies 临时列表。
    """
    if not donor_node or not clean_endpoints:
        return []

    fissioned = []
    seen = set()
    for ep in clean_endpoints:
        if not ep or ep in seen:
            continue
        seen.add(ep)

        host = ep
        port = 443
        if ":" in host:
            parts = host.split(":", 1)
            host = parts[0].strip()
            if parts[1].strip().isdigit():
                port = int(parts[1].strip())

        clone = copy.deepcopy(donor_node)
        clone["name"] = f"⚡_graft_{ep}"
        clone["server"] = host
        clone["port"] = port

        # 智能匹配端口协议 TLS 属性
        if port in [80, 8080, 8880, 2052, 2082, 2086]:
            clone["tls"] = False
        elif port in [443, 8443, 2053, 2083, 2087, 2096]:
            clone["tls"] = True

        fissioned.append(clone)

    return fissioned

