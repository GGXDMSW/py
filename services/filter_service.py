import math
import time


def compute_delay_stats(node_name, ep=None, node_history=None, node_delays=None, node_delay_history=None, get_node_endpoint_fn=None):
    """
    计算节点的本轮平均延迟(及极差)与7天历史平均延迟(及抖动/稳定度评估)
    返回: (cur_avg_str, hist_avg_str)
    """
    if node_history is None:
        node_history = {}
    if node_delays is None:
        node_delays = {}
    if node_delay_history is None:
        node_delay_history = {}

    # 1. 本轮统计 (来自 node_history)
    cur_samples = node_history.get(node_name, [])
    valid_cur = [d for d in cur_samples if isinstance(d, (int, float)) and 0 < d < 99999]
    if not valid_cur:
        single_d = node_delays.get(node_name, None)
        if single_d is not None and 0 < single_d < 99999:
            valid_cur = [single_d]

    if not valid_cur:
        cur_avg_str = "-"
    elif len(valid_cur) == 1:
        cur_avg_str = f"{int(valid_cur[0])} ms"
    else:
        c_avg = int(sum(valid_cur) / len(valid_cur))
        c_jit = int(max(valid_cur) - min(valid_cur))
        cur_avg_str = f"{c_avg} ms (±{c_jit})"

    # 2. 历史统计 (来自 node_delay_history，优先按物理端点聚合)
    if not ep and get_node_endpoint_fn:
        ep = get_node_endpoint_fn(node_name)

    hist_records = []
    if ep and ep in node_delay_history:
        hist_records = node_delay_history[ep]
    elif node_name in node_delay_history:
        hist_records = node_delay_history[node_name]

    valid_hist = [
        x["d"] for x in hist_records
        if isinstance(x, dict) and isinstance(x.get("d"), (int, float)) and 0 < x["d"] < 99999
    ]

    if not valid_hist:
        hist_avg_str = "-"
    elif len(valid_hist) == 1:
        hist_avg_str = f"{int(valid_hist[0])} ms"
    else:
        h_avg = int(sum(valid_hist) / len(valid_hist))
        variance = sum((x - h_avg) ** 2 for x in valid_hist) / len(valid_hist)
        std_jitter = int(variance ** 0.5)
        if std_jitter <= 8:
            rating = "🟢极稳"
        elif std_jitter <= 20:
            rating = "🟡平稳"
        else:
            rating = "🔴抖动"
        hist_avg_str = f"{h_avg} ms (±{std_jitter} {rating})"

    return cur_avg_str, hist_avg_str


def check_node_jitter_blacklisted(
    delays,
    jitter_min_delay=80,
    jitter_up_threshold=20,
    min_delay_threshold=None,
    up_jitter_threshold=None,
):
    """
    根据节点向上抖动机制判定是否淘汰拉黑：
    1. 至少需要 2 个有效延迟测量样本。
    2. 最低延迟 >= jitter_min_delay (例如 80ms)。
    3. (最高延迟 - 最低延迟) >= jitter_up_threshold (例如 20ms)。
    4. 特殊保护：若最高延迟 < jitter_min_delay，判定为性能极佳豁免拉黑。
    返回: (is_blacklisted: bool, min_d: int, up_jitter: int)
    """
    if min_delay_threshold is not None:
        jitter_min_delay = min_delay_threshold
    if up_jitter_threshold is not None:
        jitter_up_threshold = up_jitter_threshold

    if not delays or jitter_min_delay <= 0 or jitter_up_threshold <= 0:
        return False, 0, 0

    valid = [d for d in delays if isinstance(d, (int, float)) and 0 < d < 99999]
    if len(valid) < 2:
        return False, 0, 0

    min_d = min(valid)
    max_d = max(valid)
    up_jitter = max_d - min_d

    if max_d < jitter_min_delay:
        return False, min_d, up_jitter

    if min_d >= jitter_min_delay and up_jitter >= jitter_up_threshold:
        return True, min_d, up_jitter

    return False, min_d, up_jitter


def auto_filter_and_blacklist_non_asia_nodes(
    all_nodes,
    local_blacklist,
    favorites,
    blacklist_reasons,
    get_node_endpoint_fn,
    is_asian_node_fn,
    node_colo_dict=None,
):
    """
    执行非亚洲节点全量排查与自动拉黑，并对历史误伤节点执行智能自愈：
    1. 自愈扫描：对 local_blacklist 中因“非亚洲”原因被拉黑的节点重新审计，若新规则或实测物理Colo确认为亚洲节点，自动从黑名单中移出释放！
    2. 增量排查：基于物理机房最高真理原则与净化词库排查待测池。
    返回: (filtered_count: int, blacklisted_names: list[str])
    """
    def _lookup_colo(key):
        if not node_colo_dict or not key:
            return None
        c = node_colo_dict.get(key)
        if not c or c == "-":
            ep = get_node_endpoint_fn(key) if get_node_endpoint_fn else None
            if ep:
                c = node_colo_dict.get(ep)
        return c if (c and c != "-") else None

    def _eval_is_asian(name):
        c = _lookup_colo(name)
        try:
            return is_asian_node_fn(name, colo=c)
        except TypeError:
            return is_asian_node_fn(name)

    # 0. 智能自愈：自动释放曾因 "非亚洲" 被误杀的合法亚洲节点
    for bl_node in list(local_blacklist):
        reason = blacklist_reasons.get(bl_node, "")
        if "非亚洲" in reason:
            if _eval_is_asian(bl_node):
                local_blacklist.discard(bl_node)
                blacklist_reasons.pop(bl_node, None)
                if get_node_endpoint_fn:
                    ep = get_node_endpoint_fn(bl_node)
                    if ep:
                        local_blacklist.discard(ep)
                        blacklist_reasons.pop(ep, None)

    # 1. 增量排查与拉黑
    newly_blacklisted = []
    for n in all_nodes:
        if not _eval_is_asian(n):
            if n not in local_blacklist:
                local_blacklist.add(n)
                favorites.discard(n)
                reason = "非亚洲节点 (自动过滤)"
                blacklist_reasons[n] = reason
                ep = get_node_endpoint_fn(n) if get_node_endpoint_fn else None
                if ep:
                    local_blacklist.add(ep)
                    blacklist_reasons[ep] = reason
                newly_blacklisted.append(n)
    return len(newly_blacklisted), newly_blacklisted
