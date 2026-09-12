import os
import re

# 清理系统代理环境变量，避免内部请求受本地代理死锁影响
for env_k in [
    "HTTP_PROXY",
    "http_proxy",
    "HTTPS_PROXY",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
]:
    os.environ.pop(env_k, None)

# 基础路径与注册表配置
BASE_DIR = os.path.join(
    os.environ.get("APPDATA", ""),
    "io.github.clash-verge-rev.clash-verge-rev",
    "profiles",
)
PARENT_DIR = os.path.dirname(BASE_DIR)
DEFAULT_SCRIPT_JS = os.path.join(BASE_DIR, "Script.js")
CONFIG_STORAGE_PATH = os.path.join(PARENT_DIR, "node_assistant_config.json")
RUN_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_APP_NAME = "ClashVergeNodeAssistant"

# 现代化深色主题配色方案
THEME = {
    "bg_main": "#151822",
    "bg_card": "#1e2230",
    "bg_hover": "#292f42",
    "bg_input": "#12141c",
    "border": "#2c3246",
    "text_main": "#f1f5f9",
    "text_muted": "#8d98af",
    "accent_blue": "#2563eb",
    "accent_blue_hover": "#1d4ed8",
    "accent_cyan": "#0284c7",
    "accent_cyan_hover": "#0369a1",
    "accent_green": "#10b981",
    "accent_green_hover": "#059669",
    "accent_yellow": "#f59e0b",
    "accent_yellow_hover": "#d97706",
    "accent_red": "#ef4444",
    "accent_red_hover": "#dc2626",
    "accent_purple": "#7c3aed",
    "accent_purple_hover": "#6d28d9",
    "tree_bg": "#181b26",
    "tree_selected": "#28334a",
    "log_bg": "#0f111a",
}

# 香港与中国大陆特征排除规则 (严格过滤香港与大陆，保留台湾省 TW)
EXCLUDE_HK_REGEX = re.compile(r"(香港|HK|Hong\s*Kong|HongKong|中国(?!\s*台湾)|大陆|回国|\bCN\b)", re.IGNORECASE)

# 严格非亚洲中文关键词（包含各大洲主要国家与城市）
NON_ASIA_CN_KEYWORDS = [
    # 美洲
    "美国", "美区", "洛杉矶", "圣何塞", "旧金山", "西雅图", "芝加哥", "纽约", "达拉斯", "硅谷",
    "迈阿密", "凤凰城", "波特兰", "亚特兰大", "华盛顿", "拉斯维加斯", "火奴鲁鲁", "夏威夷", "关岛",
    "加拿大", "多伦多", "温哥华", "蒙特利尔", "渥太华", "墨西哥",
    "巴西", "圣保罗", "里约", "阿根廷", "布宜诺斯艾利斯", "智利", "哥伦比亚", "秘鲁",
    # 欧洲
    "德国", "法兰克福", "柏林", "慕尼黑", "杜塞尔多夫",
    "英国", "伦敦", "曼彻斯特", "英格兰",
    "法国", "巴黎", "马赛",
    "荷兰", "阿姆斯特丹", "鹿特丹",
    "俄罗斯", "莫斯科", "圣彼得堡", "新西伯利亚",
    "瑞士", "苏黎世", "日内瓦",
    "瑞典", "斯德哥尔摩", "挪威", "奥斯陆", "芬兰", "赫尔辛基", "丹麦", "哥本哈根",
    "意大利", "米兰", "罗马", "西班牙", "马德里", "巴塞罗那",
    "爱尔兰", "都柏林", "波兰", "华沙", "奥地利", "维也纳", "比利时", "布鲁塞尔",
    "捷克", "布拉格", "罗马尼亚", "布加勒斯特", "乌克兰", "基辅", "希腊", "雅典",
    "葡萄牙", "里斯本", "匈牙利", "布达佩斯", "保加利亚", "冰岛", "卢森堡",
    # 大洋洲
    "澳大利亚", "澳洲", "悉尼", "墨尔本", "布里斯班", "珀斯", "堪培拉",
    "新西兰", "奥克兰", "惠灵顿",
    # 非洲与其他
    "南非", "约翰内斯堡", "开普敦", "埃及", "尼日利亚", "肯尼亚",
    "多哥共和国", "非洲多哥", "汤加王国", "大洋洲汤加", "斐济", "巴拿马",
]

# 严格非亚洲国家与机场三字码 (独立大写单词匹配)
# 注意：已彻底剔除容易与英文介词、代词、TG缩写发生灾难性碰撞的2字母代码 (如 TG=Telegram, TO=to, IS=is, AT=at, IT=IT科技/it, NO=No.)，
# 统一采用国际标准化组织 ISO 3字母代码 (TGO, TON, ISL, AUT, ITA, NOR)，消除全部语义误杀！
NON_ASIA_CODE_SET = {
    "US", "USA", "CA", "CAN", "MX", "MEX", "BR", "BRA", "AR", "ARG", "CL", "CHL",
    "DE", "DEU", "GB", "GBR", "UK", "FR", "FRA", "NL", "NLD", "RU", "RUS",
    "CH", "CHE", "SE", "SWE", "NOR", "FI", "FIN", "DK", "DNK",
    "ITA", "ES", "ESP", "IE", "IRL", "PL", "POL", "AUT",
    "BE", "BEL", "CZ", "CZE", "RO", "ROU", "UA", "UKR", "GR", "GRC",
    "PT", "PRT", "HU", "HUN", "BG", "BGR", "ISL", "LU", "LUX",
    "AU", "AUS", "NZ", "NZL", "ZA", "ZAF", "TGO", "TON", "FJ", "PA",
    "LAX", "SJC", "SFO", "SEA", "ORD", "DFW", "JFK", "EWR", "IAD", "ATL", "PHX", "PDX", "LAS",
    "YYZ", "YVR", "YUL", "LHR", "MAN", "CDG", "AMS", "FRA", "MUC", "BER", "ZRH", "GVA",
    "ARN", "OSL", "HEL", "CPH", "MXP", "FCO", "MAD", "BCN", "DUB", "WAW", "VIE", "BRU",
    "SVO", "DME", "LED", "SYD", "MEL", "BNE", "PER", "AKL", "GRU", "EZE", "JNB", "CPT",
}

# 严格亚洲中文关键词
ASIA_CN_KEYWORDS = [
    "香港", "港区", "深港", "沪港", "京港", "澳门", "台湾", "台北", "高雄", "新北", "台中", "台区", "中国", "大陆",
    "日本", "东京", "大阪", "名古屋", "福冈", "冲绳", "扎幌", "埼玉", "日区", "沪日", "京日",
    "韩国", "首尔", "仁川", "釜山", "韩区", "沪韩", "蒙古",
    "新加坡", "狮城", "星洲", "新区", "沪新",
    "马来西亚", "大马", "吉隆坡", "槟城", "柔佛",
    "泰国", "曼谷", "普吉",
    "越南", "河内", "胡志明", "岘港",
    "印度尼西亚", "印尼", "雅加达", "巴厘岛",
    "菲律宾", "马尼拉", "宿务",
    "柬埔寨", "金边", "老挝", "万象", "缅甸", "仰光", "文莱",
    "印度", "孟买", "德里", "新德里", "钦奈", "班加罗尔",
    "巴基斯坦", "卡拉奇", "伊斯兰堡", "孟加拉", "达卡", "尼泊尔", "斯里兰卡",
    "哈萨克斯坦", "哈萨克", "乌兹别克斯坦", "乌兹别克", "吉尔吉斯",
    "阿联酋", "迪拜", "阿布扎比", "土耳其", "伊斯坦布尔", "安卡拉",
    "沙特", "利雅得", "卡塔尔", "多哈", "巴林", "阿曼", "科威特", "以色列",
    "格鲁吉亚", "亚美尼亚", "阿塞拜疆",
]

# 严格亚洲国家与机场三字码 (独立大写单词匹配)
ASIA_CODE_SET = {
    "HK", "HKG", "MO", "MAC", "MFM", "TW", "TWN", "TPE", "KHH", "CN", "CHN",
    "JP", "JPN", "TYO", "NRT", "HND", "KIX", "OSA", "FUK", "NGO", "CTS", "OKA",
    "KR", "KOR", "SEL", "ICN", "GMP", "PUS", "MN", "MNG",
    "SG", "SGP", "SIN",
    "MY", "MYS", "KUL", "PEN",
    "TH", "THA", "BKK", "DMK",
    "VN", "VNM", "HAN", "SGN", "DAD",
    "ID", "IDN", "CGK", "JKT", "DPS",
    "PH", "PHL", "MNL", "CEB",
    "KH", "KHM", "PNH", "LA", "LAO", "VTE", "MM", "MMR", "RGN", "BN", "BRN",
    "IN", "IND", "BOM", "DEL", "MAA", "BLR", "PK", "PAK", "KHI", "BD", "BGD", "DAC", "NP", "NPL", "LK", "LKA",
    "KZ", "KAZ", "ALA", "NQZ", "UZ", "UZB", "TAS",
    "AE", "ARE", "DXB", "AUH", "TR", "TUR", "IST", "SA", "SAU", "RUH",
    "QA", "QAT", "DOH", "BH", "BHR", "OM", "OMN", "KW", "KWT", "IL", "ISR", "TLV",
    "GE", "GEO", "TBS", "AM", "ARM", "EVN", "AZ", "AZE", "BAK",
}

COLO_NAME_MAP = {
    "HKG": "香港 HKG",
    "MFM": "澳门 MFM",
    "TPE": "台北 TPE",
    "KHH": "高雄 KHH",
    "NRT": "东京 NRT",
    "HND": "东京 HND",
    "KIX": "大阪 KIX",
    "SIN": "新加坡 SIN",
    "ICN": "首尔 ICN",
    "BKK": "曼谷 BKK",
    "KUL": "吉隆坡 KUL",
    "MNL": "马尼拉 MNL",
    "SJC": "圣何塞 SJC",
    "LAX": "洛杉矶 LAX",
    "SFO": "旧金山 SFO",
    "SEA": "西雅图 SEA",
    "ORD": "芝加哥 ORD",
    "DFW": "达拉斯 DFW",
    "JFK": "纽约 JFK",
    "EWR": "纽瓦克 EWR",
    "IAD": "华盛顿 IAD",
    "FRA": "法兰克福 FRA",
    "LHR": "伦敦 LHR",
    "AMS": "阿姆斯特丹 AMS",
    "CDG": "巴黎 CDG",
    "SYD": "悉尼 SYD",
    "MEL": "墨尔本 MEL",
}

# 洲际机房分区字典（包含二字国家码与三字机场码，彻底避免同国二字码/三字码误判为漂移）
COLO_REGIONS = {
    # 韩国 (KR 与 ICN, SEL, PUS, GMP 统一归入 Asia_KR)
    "KR": "Asia_KR", "ICN": "Asia_KR", "SEL": "Asia_KR", "PUS": "Asia_KR", "GMP": "Asia_KR",

    # 日本 (JP 与 NRT, HND, KIX, FUK, NGO, CTS, OKA 统一归入 Asia_JP)
    "JP": "Asia_JP", "NRT": "Asia_JP", "HND": "Asia_JP", "KIX": "Asia_JP", "FUK": "Asia_JP",
    "NGO": "Asia_JP", "CTS": "Asia_JP", "OKA": "Asia_JP",

    # 中国香港与澳门 (HK 与 HKG, MFM, MO 统一归入 Asia_HK)
    "HK": "Asia_HK", "HKG": "Asia_HK", "MO": "Asia_HK", "MFM": "Asia_HK",

    # 中国台湾 (TW 与 TPE, KHH 统一归入 Asia_TW)
    "TW": "Asia_TW", "TPE": "Asia_TW", "KHH": "Asia_TW",

    # 新加坡 (SG 与 SIN 统一归入 Asia_SG)
    "SG": "Asia_SG", "SIN": "Asia_SG",

    # 马来西亚 (MY 与 KUL, PEN 统一归入 Asia_MY)
    "MY": "Asia_MY", "KUL": "Asia_MY", "PEN": "Asia_MY",

    # 泰国 (TH 与 BKK, DMK 统一归入 Asia_TH)
    "TH": "Asia_TH", "BKK": "Asia_TH", "DMK": "Asia_TH",

    # 越南 (VN 与 HAN, SGN, DAD 统一归入 Asia_VN)
    "VN": "Asia_VN", "HAN": "Asia_VN", "SGN": "Asia_VN", "DAD": "Asia_VN",

    # 印度尼西亚 (ID 与 CGK, JKT, DPS 统一归入 Asia_ID)
    "ID": "Asia_ID", "CGK": "Asia_ID", "JKT": "Asia_ID", "DPS": "Asia_ID",

    # 菲律宾 (PH 与 MNL, CEB 统一归入 Asia_PH)
    "PH": "Asia_PH", "MNL": "Asia_PH", "CEB": "Asia_PH",

    # 印度 (IN 与 BOM, DEL, MAA, BLR 统一归入 Asia_IN)
    "IN": "Asia_IN", "BOM": "Asia_IN", "DEL": "Asia_IN", "MAA": "Asia_IN", "BLR": "Asia_IN",

    # 其他亚洲区域
    "PK": "Asia_Other", "KHI": "Asia_Other", "ISB": "Asia_Other",
    "BD": "Asia_Other", "DAC": "Asia_Other",
    "NP": "Asia_Other", "KTM": "Asia_Other",
    "LK": "Asia_Other", "CMB": "Asia_Other",
    "KZ": "Asia_Other", "ALA": "Asia_Other",
    "AE": "Asia_Other", "DXB": "Asia_Other", "AUH": "Asia_Other",
    "TR": "Asia_Other", "IST": "Asia_Other", "SA": "Asia_Other", "IL": "Asia_Other",

    # 北美洲 (NA: US, CA, MX 以及各大机场码统一归入 NA)
    "US": "NA", "USA": "NA", "CA": "NA", "CAN": "NA", "MX": "NA",
    "SJC": "NA", "LAX": "NA", "SFO": "NA", "SEA": "NA", "ORD": "NA",
    "DFW": "NA", "JFK": "NA", "EWR": "NA", "IAD": "NA", "ATL": "NA",
    "MIA": "NA", "PHX": "NA", "PDX": "NA", "LAS": "NA", "YYZ": "NA",
    "YVR": "NA", "YUL": "NA",

    # 欧洲 (EU: DE, GB, FR, NL 等以及各大机场码统一归入 EU)
    "DE": "EU", "GB": "EU", "UK": "EU", "FR": "EU", "NL": "EU", "RU": "EU",
    "CH": "EU", "SE": "EU", "NO": "EU", "FI": "EU", "DK": "EU", "IT": "EU",
    "ES": "EU", "IE": "EU", "PL": "EU", "AT": "EU", "BE": "EU", "CZ": "EU",
    "RO": "EU", "UA": "EU", "GR": "EU", "PT": "EU", "HU": "EU", "BG": "EU",
    "FRA": "EU", "LHR": "EU", "AMS": "EU", "CDG": "EU", "BER": "EU",
    "MUC": "EU", "ZRH": "EU", "GVA": "EU", "ARN": "EU", "OSL": "EU",
    "HEL": "EU", "CPH": "EU", "MXP": "EU", "FCO": "EU", "MAD": "EU",
    "BCN": "EU", "DUB": "EU", "WAW": "EU", "VIE": "EU", "BRU": "EU",
    "SVO": "EU", "DME": "EU", "LED": "EU",

    # 大洋洲 (OC: AU, NZ 等统一归入 OC)
    "AU": "OC", "AUS": "OC", "NZ": "OC", "NZL": "OC",
    "SYD": "OC", "MEL": "OC", "BNE": "OC", "PER": "OC", "AKL": "OC",

    # 南美洲与非洲
    "BR": "SA", "GRU": "SA", "AR": "SA", "EZE": "SA", "CL": "SA",
    "ZA": "AF", "JNB": "AF", "CPT": "AF", "EG": "AF",
}


COUNTRY_NAME_MAP = {
    "HK": "香港", "TW": "台湾", "JP": "日本", "SG": "新加坡", "KR": "韩国",
    "US": "美国", "DE": "德国", "GB": "英国", "UK": "英国", "FR": "法国",
    "CA": "加拿大", "AU": "澳大利亚", "MY": "马来西亚", "TH": "泰国", "ID": "印尼",
    "IN": "印度", "PH": "菲律宾", "RU": "俄罗斯", "NL": "荷兰", "VN": "越南",
}
