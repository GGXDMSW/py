import re
import time

from config.settings import (
    ASIA_CN_KEYWORDS,
    ASIA_CODE_SET,
    COLO_REGIONS,
    EXCLUDE_HK_REGEX,
    NON_ASIA_CN_KEYWORDS,
    NON_ASIA_CODE_SET,
)
from services.probe_service import detect_node_region


def get_colo_region(code):
    """
    获取 Colo 代码或国家二字码对应的宏观大区 (如 Asia_KR, Asia_JP, Asia_HK, NA, EU 等)
    全面兼容复合机房展示字符串（如 "东京 NRT"、"韩国 KR (SK)"、"首尔 ICN"、"日本 JP (Choopa)" 等）
    """
    if not code or code == "-":
        return "OTHER"
    code_str = str(code).strip()
    code_upper = code_str.upper()
    if code_upper in COLO_REGIONS:
        return COLO_REGIONS[code_upper]

    # 1. 优先从字符串中提取二至四位大写代号匹配 (如 NRT, ICN, SIN, SJC, FRA 等)
    tokens = re.findall(r"[A-Z]{2,4}", code_upper)
    for tok in tokens:
        if tok in COLO_REGIONS:
            return COLO_REGIONS[tok]

    # 2. 中文地名语义映射兜底
    CN_REGION_MAP = [
        ("日本", "Asia_JP"), ("东京", "Asia_JP"), ("大阪", "Asia_JP"), ("名古屋", "Asia_JP"), ("福冈", "Asia_JP"),
        ("韩国", "Asia_KR"), ("首尔", "Asia_KR"), ("仁川", "Asia_KR"), ("釜山", "Asia_KR"),
        ("香港", "Asia_HK"), ("澳门", "Asia_HK"),
        ("台湾", "Asia_TW"), ("台北", "Asia_TW"), ("高雄", "Asia_TW"),
        ("新加坡", "Asia_SG"), ("狮城", "Asia_SG"),
        ("马来西亚", "Asia_MY"), ("吉隆坡", "Asia_MY"),
        ("泰国", "Asia_TH"), ("曼谷", "Asia_TH"),
        ("越南", "Asia_VN"), ("河内", "Asia_VN"), ("胡志明", "Asia_VN"),
        ("印度", "Asia_IN"), ("孟买", "Asia_IN"), ("德里", "Asia_IN"),
        ("美国", "NA"), ("美区", "NA"), ("洛杉矶", "NA"), ("圣何塞", "NA"), ("旧金山", "NA"),
        ("西雅图", "NA"), ("芝加哥", "NA"), ("纽约", "NA"), ("加拿大", "NA"),
        ("德国", "EU"), ("法兰克福", "EU"), ("英国", "EU"), ("伦敦", "EU"), ("法国", "EU"), ("巴黎", "EU"),
        ("荷兰", "EU"), ("阿姆斯特丹", "EU"), ("俄罗斯", "EU"),
        ("澳大利亚", "OC"), ("悉尼", "OC"), ("墨尔本", "OC"),
    ]
    for kw, reg in CN_REGION_MAP:
        if kw in code_str:
            return reg

    return "OTHER"


def record_colo_sample(colo_history, node_name, endpoint, c_code, c_disp, now=None, node_colo_dict=None):
    """
    记录一次机房探测样本到 7 天滑动时序桶中，并同步更新最新 Colo 映射字典
    """
    if now is None:
        now = time.time()
    cutoff = now - 7 * 86400

    def _append_bucket(bucket_key):
        if not bucket_key:
            return
        if bucket_key not in colo_history:
            colo_history[bucket_key] = []
        samples = [
            item for item in colo_history[bucket_key]
            if isinstance(item, dict) and item.get("ts", 0) >= cutoff
        ]
        # 若最新一条记录距现在小于 15 分钟且结果完全一致，则刷新时间戳避免高频刷屏
        if (
            samples
            and samples[-1].get("colo") == c_code
            and (now - samples[-1].get("ts", 0)) < 900
        ):
            samples[-1]["ts"] = now
            samples[-1]["disp"] = c_disp
        else:
            samples.append({"ts": now, "colo": c_code, "disp": c_disp})
        colo_history[bucket_key] = samples[-30:]

    if node_name:
        _append_bucket(node_name)
    if endpoint and endpoint != node_name:
        _append_bucket(endpoint)

    if node_colo_dict is not None:
        disp_to_set = c_disp if (c_disp and c_disp != "-") else (c_code if c_code and c_code != "-" else "-")
        if endpoint:
            if disp_to_set != "-" or endpoint not in node_colo_dict:
                node_colo_dict[endpoint] = disp_to_set
        if node_name:
            if disp_to_set != "-" or node_name not in node_colo_dict:
                node_colo_dict[node_name] = disp_to_set


def analyze_colo_stats(history_list, now=None, node_name=None):
    """
    分析 7 天机房样本时序分布，进行长效锚定与防漂移审计
    返回: (dominant_colo: str, anchor_rate: float, has_severe_drift: bool, drift_tag: str)

    核心修复：
    二字国家码（如 KR）与三字机场机房码（如 ICN）在 COLO_REGIONS 中均映射为同一大区 (如 Asia_KR)，
    彻底消除 KR 与 ICN 同国被误判为跨洲漂移的问题！
    """
    if now is None:
        now = time.time()
    cutoff = now - 7 * 86400

    valid = [
        item for item in history_list
        if isinstance(item, dict) and item.get("ts", 0) >= cutoff
    ]
    if not valid:
        return "-", 0.0, False, "-"

    counts = {}
    for item in valid:
        c = item.get("colo", "-")
        if c != "-":
            counts[c] = counts.get(c, 0) + 1

    if not counts:
        return "-", 0.0, False, "-"

    total = sum(counts.values())
    sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    dominant, dom_cnt = sorted_counts[0]
    anchor_rate = (dom_cnt / total) * 100.0

    latest_sample = valid[-1].get("colo", "-")
    dom_region = get_colo_region(dominant)
    has_severe_drift = False
    drift_tag = ""

    # 1. 跨大区/跨洲漂移检测
    for c, _ in sorted_counts[1:]:
        c_region = get_colo_region(c)
        # 如果大区不同（如 Asia_HK vs Asia_JP 或 Asia_KR vs NA），判定为漂移
        if dom_region != c_region and dom_region != "OTHER" and c_region != "OTHER":
            has_severe_drift = True
            if (dom_region == "Asia_HK" and c_region != "Asia_HK") or (c_region == "Asia_HK" and dom_region != "Asia_HK"):
                drift_tag = "港区漂移"
            else:
                drift_tag = "跨洲漂移"
            break

    # 2. 针对最新样本的大区一致性检测
    if latest_sample != "-" and latest_sample != dominant:
        latest_reg = get_colo_region(latest_sample)
        # 仅当最新样本与主流大区真实不同时，才标记为漂移
        if dom_region != latest_reg and dom_region != "OTHER" and latest_reg != "OTHER":
            has_severe_drift = True
            if (latest_reg == "Asia_HK" and dom_region != "Asia_HK") or (dom_region == "Asia_HK" and latest_reg != "Asia_HK"):
                drift_tag = f"漂移至{latest_sample}"
            elif not drift_tag:
                drift_tag = f"偏移至{latest_sample}"

    # 3. 节点名称语义与实测机房冲突检测（如日韩节点伪装成香港出口）
    if node_name:
        n_reg = detect_node_region(node_name)
        if any(k in n_reg for k in ["日本", "韩国", "新加坡", "台湾"]) and latest_sample in ["HKG", "MFM", "HK"]:
            has_severe_drift = True
            drift_tag = "名实不符(港出)"

    display_info = f"{dominant} ({anchor_rate:.0f}%)" if anchor_rate < 100.0 else f"{dominant} 100%"
    if has_severe_drift and drift_tag:
        display_info = f"⚠️{drift_tag} [{dominant} {anchor_rate:.0f}% / {latest_sample}]"

    return dominant, anchor_rate, has_severe_drift, display_info


def is_node_hongkong(node_name):
    """
    判断节点是否为香港节点
    """
    if not node_name:
        return False
    return bool(EXCLUDE_HK_REGEX.search(node_name))


def is_asian_node(node_name, colo=None):
    """
    判断节点是否为亚洲节点（严格排除美区、欧洲、大洋洲、非洲等）
    实测物理机房 (Colo) 拥有最高真理层级 (Ground Truth)：
    - 若实测为亚洲机房 (Asia_*)，绝对判定为亚洲 (True)，物理数据最高，豁免一切文本关键词误判！
    - 若实测为非亚洲机房 (NA, EU, OC, SA, AF)，绝对判定为非亚洲 (False)！
    - 仅在未知 Colo 或 OTHER 时，退回文本关键词与国家码严谨排查。
    """
    if not node_name:
        return False

    # 0. 物理机房实测最高真理原则
    if colo and colo != "-":
        reg = get_colo_region(colo)
        if reg.startswith("Asia_"):
            return True
        if reg in ["NA", "EU", "OC", "SA", "AF"]:
            return False

    upper_name = node_name.upper()

    # 1. 严格非亚洲中文关键词排查
    for kw in NON_ASIA_CN_KEYWORDS:
        if kw in node_name:
            return False

    # 2. 严格非亚洲国家与机场独立代码排查
    tokens = set(re.findall(r"\b[A-Z]{2,4}\b", upper_name))
    for t in tokens:
        if t in NON_ASIA_CODE_SET and t not in ASIA_CODE_SET:
            return False

    # 3. 亚洲中文关键词正向匹配
    for ak in ASIA_CN_KEYWORDS:
        if ak in node_name:
            return True

    # 4. 亚洲三字码/国家代码正向匹配
    for t in tokens:
        if t in ASIA_CODE_SET:
            return True

    # 兜底：若节点名称不含明显非亚洲标志，默认保留
    return True
