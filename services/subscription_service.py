import gzip
import hashlib
import os
import re
import ssl
import time
import urllib.parse
import urllib.request

from config.settings import PARENT_DIR


def extract_nodes_and_details_from_file(filepath):
    """
    解析 Clash 订阅配置文件（YAML/JSON），提取节点名称列表及物理端点详情字典
    返回: (nodes: list[str], details: dict[str, dict])
    """
    nodes = []
    details = {}
    if not os.path.exists(filepath):
        return nodes, details
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        inline_matches = re.findall(r"-\s*\{([^}]+)\}", content)
        for item in inline_matches:
            # 兼容引号内包含逗号的情况
            m_n = re.search(r'name:\s*"([^"]+)"', item) or re.search(r"name:\s*'([^']+)'", item) or re.search(r"name:\s*([^,\n}]+)", item)
            m_s = re.search(r'server:\s*"([^"]+)"', item) or re.search(r"server:\s*'([^']+)'", item) or re.search(r"server:\s*([^,\n}]+)", item)
            m_p = re.search(r"port:\s*(\d+)", item)
            if m_n:
                name = m_n.group(1).strip()
                if name not in details:
                    nodes.append(name)
                server = m_s.group(1).strip() if m_s else ""
                port = m_p.group(1).strip() if m_p else "443"
                details[name] = {"server": server, "port": port}

        if not nodes:
            p_idx = content.find("proxies:")
            proxies_text = content[p_idx:] if p_idx != -1 else content
            blocks = re.split(r"\n\s*-\s+", proxies_text)
            for b in blocks:
                m_n = re.search(r'(?:^|\n)\s*name:\s*"([^"\r\n]+)"', b) or re.search(r"(?:^|\n)\s*name:\s*'([^'\r\n]+)'", b) or re.search(r"(?:^|\n)\s*name:\s*([^\r\n]+)", b)
                m_s = re.search(r'(?:^|\n)\s*server:\s*"([^"\r\n]+)"', b) or re.search(r"(?:^|\n)\s*server:\s*'([^'\r\n]+)'", b) or re.search(r"(?:^|\n)\s*server:\s*([^\r\n]+)", b)
                m_p = re.search(r"(?:^|\n)\s*port:\s*(\d+)", b)
                if m_n:
                    name = m_n.group(1).strip()
                    if name not in details:
                        nodes.append(name)
                    server = m_s.group(1).strip() if m_s else ""
                    port = m_p.group(1).strip() if m_p else "443"
                    details[name] = {"server": server, "port": port}

        if not nodes:
            matches = re.findall(r"-\s*name:\s*[\"']?([^\"'\r\n]+)[\"']?", content)
            for n in matches:
                name = n.strip()
                nodes.append(name)
                details[name] = {"server": "", "port": "443"}
    except Exception:
        pass
    return list(dict.fromkeys(nodes)), details


def choose_canonical_node_name(node_list):
    """
    物理端点别名智能代表选择器：
    从共享同一 IP:Port 物理端点的马甲节点列表中，挑选出最具辨识度、最规范的代表名称。
    """
    if not node_list:
        return ""
    if len(node_list) == 1:
        return node_list[0]

    def _canonical_score(name):
        score = 0
        # 1. 包含具体测速/延迟标签（如 43.29ms, 12.88 MB/s）加最高分
        if re.search(r"\d+(?:\.\d+)?\s*(?:ms|mb/s|kb/s)", name, re.IGNORECASE):
            score += 60
        # 2. 包含优质、高速、专线、精品等质量关键词
        if any(k in name for k in ["优选", "高速", "精品", "专线", "PRO", "VIP"]):
            score += 30
        # 3. 包含清晰地区中英文标识
        if any(k in name for k in ["香港", "HK", "台湾", "TW", "日本", "JP", "韩国", "KR", "新加坡", "SG"]):
            score += 20
        # 4. 纯 IP 命名扣分，避免把没有语义的 IP:Port 选为主代表
        clean_n = name.strip()
        if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?$", clean_n):
            score -= 30
        # 5. 扣除临时调试标签
        if "auto" in name.lower() or "保活" in name:
            score -= 10
        return score

    return max(node_list, key=_canonical_score)


def get_node_endpoint(node_name, node_details=None, all_nodes=None, verified_nodes=None, clash_client=None):
    """
    统一的物理端点抽取与归一化：获取 node_name 的 IP:Port
    """
    if not node_name:
        return ""

    node_name_clean = str(node_name).strip()
    if re.match(r"^[\w\.\-]+\:\d+$", node_name_clean):
        return node_name_clean

    if "#" in node_name_clean:
        prefix = node_name_clean.split("#", 1)[0].strip()
        m_pre = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})$", prefix)
        if m_pre:
            return f"{m_pre.group(1)}:{m_pre.group(2)}"

    if node_details:
        info = node_details.get(node_name, {})
        server = info.get("server", "").strip()
        port = str(info.get("port", "443")).strip()
        if server:
            return f"{server}:{port}"

    m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{2,5}))?", node_name_clean)
    if m:
        ip = m.group(1)
        p = m.group(2) if m.group(2) else "443"
        return f"{ip}:{p}"

    if verified_nodes and node_name in verified_nodes:
        v_ep = verified_nodes[node_name].get("endpoint", "")
        if v_ep:
            return v_ep

    if clash_client and all_nodes and node_name in all_nodes:
        try:
            enc = urllib.parse.quote(node_name, safe="")
            res = clash_client.call_api(f"/proxies/{enc}", timeout=0.3)
            if res and isinstance(res, dict):
                s = res.get("server", "").strip()
                p = str(res.get("port", "443")).strip()
                if s:
                    if node_details is not None:
                        node_details[node_name] = {"server": s, "port": p}
                    return f"{s}:{p}"
        except Exception:
            pass

    return ""


def resolve_node_to_current(target_key, all_nodes, node_details):
    """
    智能对齐历史节点名/端点到当前订阅中真实存在的节点名称
    """
    if not target_key:
        return None
    if target_key in all_nodes:
        return target_key

    target_ep = ""
    info = node_details.get(target_key, {})
    s = info.get("server", "").strip()
    p = str(info.get("port", "443")).strip()
    if s:
        target_ep = f"{s}:{p}"
    else:
        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{2,5}))?", target_key)
        if m:
            target_ep = f"{m.group(1)}:{m.group(2) if m.group(2) else '443'}"

    if target_ep and ":" in target_ep:
        raw_ip, raw_port = target_ep.split(":", 1)
        for n in all_nodes:
            n_info = node_details.get(n, {})
            if (
                n_info.get("server", "").strip() == raw_ip
                and str(n_info.get("port", "443")).strip() == raw_port
            ):
                return n
        for n in all_nodes:
            n_info = node_details.get(n, {})
            if n_info.get("server", "").strip() == raw_ip:
                return n

    return None


def update_remote_subscription(target_yaml_path, mixed_port=7897, on_step_callback=None):
    """
    多通道下载最新远程订阅，支持 Gzip 解压与 MD5 变更检测
    返回: (ok: bool, msg: str, content_changed: bool)
    """
    fname = os.path.basename(target_yaml_path)
    file_stem = os.path.splitext(fname)[0]

    profiles_yaml = os.path.join(PARENT_DIR, "profiles.yaml")
    if not os.path.exists(profiles_yaml):
        return False, "未找到 profiles.yaml 文件", False

    sub_url = ""
    sub_name = ""
    try:
        with open(profiles_yaml, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        items = re.split(r"\n\s*-\s+", content)
        for itm in items:
            if fname in itm or file_stem in itm:
                m_url = re.search(r"url:\s*['\"]?([^'\"\r\n]+)['\"]?", itm)
                m_name = re.search(r"name:\s*['\"]?([^'\"\r\n]+)['\"]?", itm)
                if m_url:
                    sub_url = m_url.group(1).strip()
                    if m_name:
                        sub_name = m_name.group(1).strip()
                    break

        if not sub_url:
            m_curr = re.search(r"current:\s*['\"]?([^'\"\r\n]+)['\"]?", content)
            if m_curr:
                curr_val = m_curr.group(1).strip()
                curr_stem = os.path.splitext(curr_val)[0]
                for itm in items:
                    if curr_val in itm or curr_stem in itm:
                        m_url = re.search(r"url:\s*['\"]?([^'\"\r\n]+)['\"]?", itm)
                        if m_url:
                            sub_url = m_url.group(1).strip()
                            break
    except Exception as ex:
        return False, f"读取 profiles.yaml 异常: {ex}", False

    if not sub_url or not sub_url.startswith("http"):
        return False, f"在 profiles.yaml 中未定位到 {fname} 的有效远程 URL", False

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)

    old_md5 = ""
    if os.path.exists(target_yaml_path):
        try:
            with open(target_yaml_path, "rb") as f:
                old_md5 = hashlib.md5(f.read()).hexdigest()
        except Exception:
            old_md5 = ""

    last_error = ""

    for attempt in range(1, 4):
        for use_proxy in [True, False]:
            channel_name = f"本地代理端口:{mixed_port}" if use_proxy else "直接连接"
            try:
                if on_step_callback:
                    on_step_callback(f"[步骤 1/4] 同步更新订阅 (第 {attempt}/3 轮尝试 - {channel_name})...")

                headers = {
                    "User-Agent": "ClashforWindows/0.20.39 clash-verge-rev/1.7.7",
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate",
                }
                req = urllib.request.Request(sub_url, headers=headers)

                if use_proxy:
                    proxy_h = urllib.request.ProxyHandler({
                        "http": f"http://127.0.0.1:{mixed_port}",
                        "https": f"http://127.0.0.1:{mixed_port}",
                    })
                    opener = urllib.request.build_opener(proxy_h, https_handler)
                else:
                    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), https_handler)

                with opener.open(req, timeout=12) as resp:
                    data = resp.read()

                if len(data) >= 2 and data[:2] == b"\x1f\x8b":
                    try:
                        data = gzip.decompress(data)
                    except Exception:
                        pass

                if data and len(data) > 100:
                    text_head = data[:1500].decode("utf-8", errors="ignore")
                    if "proxies" in text_head or "- name:" in text_head or "- {" in text_head:
                        new_md5 = hashlib.md5(data).hexdigest()
                        content_changed = new_md5 != old_md5

                        if content_changed:
                            with open(target_yaml_path, "wb") as f:
                                f.write(data)
                            return True, f"成功同步更新【{sub_name or fname}】(内容已变动)", True
                        else:
                            return True, f"成功获取【{sub_name or fname}】(与本地完全一致，MD5未变)", False
                    else:
                        last_error = "获取内容非合法 Clash YAML"
            except Exception as ex:
                last_error = f"{type(ex).__name__}: {str(ex)}"
                continue

        time.sleep(1.0)

    return False, last_error, False
