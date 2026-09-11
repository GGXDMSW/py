from concurrent.futures import ThreadPoolExecutor
import time

from services.probe_service import get_c_segment_ips, get_cf_colo_raw, tcp_ping


def scan_c_segment(
    seed_ip,
    port=443,
    ping_timeout=1.2,
    colo_timeout=1.5,
    max_workers=25,
    on_ip_tested=None,
    cancel_check=None,
):
    """
    针对输入 IP 所在的 /24 C段网段开展并发探测扫描
    返回: list[dict] -> [{"ip": ip, "delay": rtt, "colo_code": c_code, "colo_disp": c_disp}, ...]
    """
    c_ips = get_c_segment_ips(seed_ip)
    if not c_ips:
        return []

    results = []

    def _scan_single(target_ip):
        if cancel_check and cancel_check():
            return None

        rtt = tcp_ping(target_ip, port=port, timeout=ping_timeout)
        if rtt >= 99999:
            if on_ip_tested:
                on_ip_tested(target_ip, 99999, "-", "-")
            return None

        c_code, c_disp = get_cf_colo_raw(target_ip, port=port, timeout=colo_timeout)
        res = {
            "ip": target_ip,
            "port": port,
            "delay": rtt,
            "colo_code": c_code,
            "colo_disp": c_disp,
        }
        if on_ip_tested:
            on_ip_tested(target_ip, rtt, c_code, c_disp)
        return res

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for item in executor.map(_scan_single, c_ips):
            if item:
                results.append(item)

    # 按延迟从小到大排序
    results.sort(key=lambda x: x["delay"])
    return results
