import json
import re
import socket
import ssl
import time
import urllib.request

from config.settings import COLO_NAME_MAP, COUNTRY_NAME_MAP

_IP_GEO_CACHE = {}


def get_ip_location_fallback(ip):
    """
    当无法获取 Cloudflare 原生 trace 数据时，通过公开 IP 数据库解析归属国家与 ISP
    """
    if not ip or ip in ["127.0.0.1", "localhost"]:
        return "-", "-"
    if ip in _IP_GEO_CACHE:
        return _IP_GEO_CACHE[ip]
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,city,isp,as"
        req = urllib.request.Request(url, headers={"User-Agent": "curl/7.88.1"})
        with urllib.request.urlopen(req, timeout=1.8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                cc = data.get("countryCode", "").upper()
                country_cn = COUNTRY_NAME_MAP.get(cc, data.get("country", cc))
                isp = data.get("isp", "")
                isp_short = isp.split()[0] if isp else ""
                disp = f"{country_cn} {cc}" + (f" ({isp_short})" if isp_short else "")
                res = (cc, disp)
                _IP_GEO_CACHE[ip] = res
                return res
    except Exception:
        pass
    _IP_GEO_CACHE[ip] = ("-", "-")
    return "-", "-"


def get_cf_colo_raw(ip, port=443, timeout=1.8, enable_geo_fallback=True):
    """
    直连探测 Cloudflare CDN Anycast 真实数据中心代码 (Colo)：
    发送 GET /cdn-cgi/trace 并提取三字码 (如 HKG, NRT, SJC, SIN 等)
    """
    try:
        is_ssl = int(port) in [443, 8443, 2053, 2083, 2087, 2096]
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, int(port)))
        if is_ssl:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            sock = ctx.wrap_socket(sock, server_hostname="cloudflare.com")

        req = b"GET /cdn-cgi/trace HTTP/1.1\r\nHost: cloudflare.com\r\nUser-Agent: curl/7.88.1\r\nConnection: close\r\n\r\n"
        sock.sendall(req)

        resp = b""
        while True:
            chunk = sock.recv(1024)
            if not chunk:
                break
            resp += chunk
            if b"colo=" in resp and b"\n" in resp[resp.find(b"colo=") :]:
                break
        sock.close()

        text = resp.decode("utf-8", errors="ignore")
        m = re.search(r"colo=([A-Z]{3})", text)
        if m:
            code = m.group(1)
            return code, COLO_NAME_MAP.get(code, f"{code}")
    except Exception:
        pass

    # 若非原生 Cloudflare Anycast 节点（如第三方反代 VPS），自动降级回退至 IP 物理机房与地理归属地解析
    if enable_geo_fallback:
        code, disp = get_ip_location_fallback(ip)
        if code != "-":
            return code, disp

    return "-", "-"


def tcp_ping(ip, port=443, timeout=1.2):
    """
    执行纯 TCP 握手 RTT 测速（单位: 毫秒 ms）
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        st = time.time()
        s.connect((ip, int(port)))
        rtt = int((time.time() - st) * 1000)
        s.close()
        return rtt
    except Exception:
        return 99999


def get_c_segment_ips(ip_str):
    """
    生成给定 IP 的整个 /24 C段 IP 清单 (x.x.x.1 ~ x.x.x.254)
    """
    m = re.search(r"^(\d{1,3}\.\d{1,3}\.\d{1,3})\.\d{1,3}$", ip_str.strip())
    if not m:
        return []
    prefix = m.group(1)
    return [f"{prefix}.{i}" for i in range(1, 255)]


def detect_node_region(node_name):
    """
    基于节点名称提取主要国家/地区中文标识
    """
    n = node_name.lower()
    if any(k in n for k in ["香港", "hk", "hongkong", "hong kong"]):
        return "香港"
    if any(k in n for k in ["台湾", "tw", "taiwan"]):
        return "台湾"
    if any(k in n for k in ["日本", "jp", "japan"]):
        return "日本"
    if any(k in n for k in ["新加坡", "sg", "singapore", "狮城"]):
        return "新加坡"
    if any(k in n for k in ["韩国", "kr", "korea", "首尔"]):
        return "韩国"
    if any(k in n for k in ["美国", "us", "usa", "united states", "洛杉矶", "硅谷", "西雅图"]):
        return "美国"
    if any(k in n for k in ["德国", "de", "germany", "法兰克福"]):
        return "德国"
    if any(k in n for k in ["英国", "uk", "great britain", "london", "伦敦"]):
        return "英国"
    if any(k in n for k in ["马来西亚", "my", "malaysia"]):
        return "马来西亚"
    if any(k in n for k in ["加拿大", "ca", "canada"]):
        return "加拿大"
    if any(k in n for k in ["法国", "fr", "france"]):
        return "法国"
    if any(k in n for k in ["澳大利亚", "au", "australia", "悉尼"]):
        return "澳大利亚"
    if any(k in n for k in ["印度", "in", "india"]):
        return "印度"
    m = re.search(r"\b([A-Z]{2})\b", node_name)
    if m:
        return m.group(1)
    return "优质节点"


def measure_http_download_speed(speed_opener, speed_url, duration=3.0, cancel_check=None):
    """
    通过 HTTP/HTTPS 下载测速源测量下行有效带宽 (单位: MB/s)
    """
    speed_timeout = max(1.5, min(2.5, round(duration + 0.5, 1)))
    node_deadline = time.time() + duration + 1.0
    total_bytes = 0

    try:
        req = urllib.request.Request(
            speed_url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Connection": "close",
            },
        )
        with speed_opener.open(req, timeout=speed_timeout) as resp:
            start_time = time.time()
            chunk_size = 16 * 1024
            while time.time() - start_time < duration:
                if time.time() >= node_deadline or (cancel_check and not cancel_check()):
                    break
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                total_bytes += len(chunk)

            elapsed = time.time() - start_time
            if elapsed > 0 and total_bytes > 0:
                return round((total_bytes / (1024 * 1024)) / elapsed, 2)
            else:
                return 0.0
    except Exception:
        return -1.0
