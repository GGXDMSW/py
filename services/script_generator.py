import glob
import json
import os
import re

from config.settings import BASE_DIR, DEFAULT_SCRIPT_JS, PARENT_DIR


def build_script_js(
    favorites,
    stars_nodes,
    all_nodes,
    node_details,
    group_interval="300",
    group_tolerance="20",
    star_group_interval="300",
    star_group_tolerance="20",
    target_nodes=None,
    is_asian_node_fn=None,
    get_node_endpoint_fn=None,
    resolve_node_to_current_fn=None,
    fission_proxies=None,
    cloud_endpoints=None,
    node_colo=None,
):
    """
    动态生成 Clash Verge Rev 策略组合并脚本 (Script.js)
    返回: (script_code: str, premium_tokens: list[str], star_tokens: list[str])
    """
    inter_val = str(group_interval).strip() if str(group_interval).strip().isdigit() else "300"
    tol_val = str(group_tolerance).strip() if str(group_tolerance).strip().isdigit() else "20"
    star_inter_val = str(star_group_interval).strip() if str(star_group_interval).strip().isdigit() else "300"
    star_tol_val = str(star_group_tolerance).strip() if str(star_group_tolerance).strip().isdigit() else "20"

    # 自动加载或对齐 cloud_endpoints 与 node_colo
    if cloud_endpoints is None or node_colo is None:
        try:
            from config.config_manager import safe_load_config
            from config.settings import CONFIG_STORAGE_PATH
            cfg_data = safe_load_config(CONFIG_STORAGE_PATH) or {}
            if cloud_endpoints is None:
                cloud_endpoints = cfg_data.get("cloud_endpoints", {})
            if node_colo is None:
                node_colo = cfg_data.get("node_colo", {})
        except Exception:
            pass
    if not cloud_endpoints or not isinstance(cloud_endpoints, dict):
        cloud_endpoints = {}
    if not node_colo or not isinstance(node_colo, dict):
        node_colo = {}

    # 汇聚所有优选候选清单
    if is_asian_node_fn:
        combined_favs = [n for n in favorites if is_asian_node_fn(n)]
    else:
        combined_favs = list(favorites)

    if target_nodes:
        if is_asian_node_fn:
            t_nodes = [n for n in target_nodes if is_asian_node_fn(n)]
        else:
            t_nodes = list(target_nodes)
        combined_favs = list(dict.fromkeys(t_nodes + combined_favs))

    if not resolve_node_to_current_fn:
        try:
            from services.subscription_service import resolve_node_to_current
            resolve_node_to_current_fn = lambda k: resolve_node_to_current(k, all_nodes, node_details)
        except Exception:
            pass

    # 构建全量池中 IP:Port -> 规范节点全名 的精准映射表
    ip_port_pattern = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}$")
    ep_to_name = {}
    for node in (all_nodes or []):
        if not node:
            continue
        ep = None
        if get_node_endpoint_fn:
            try:
                ep = get_node_endpoint_fn(node)
            except Exception:
                pass
        if not ep:
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", str(node))
            if m:
                ep = m.group(1)
        if ep and ep not in ep_to_name:
            ep_to_name[ep] = node

    # 构建物理端点 -> 规范命名映射表 (canonical_name_map)
    canonical_name_map = {}
    for ep, c_name in cloud_endpoints.items():
        if ep and c_name:
            canonical_name_map[str(ep).strip()] = str(c_name).strip()

    # 从 combined_favs 中提取已规范命名的端点补充入映射表
    for fav in combined_favs:
        if not fav:
            continue
        str_fav = str(fav).strip()
        ep = None
        if node_details and str_fav in node_details:
            info = node_details[str_fav]
            s = str(info.get("server", "")).strip()
            p = str(info.get("port", "443")).strip()
            if s:
                ep = f"{s}:{p}"
        if not ep:
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{2,5}))?", str_fav)
            if m:
                ep = f"{m.group(1)}:{m.group(2) or '443'}"
        if ep and ep not in canonical_name_map:
            canonical_name_map[ep] = str_fav
            if ":" in ep:
                canonical_name_map[ep.split(":")[0]] = str_fav

    # 构建物理香港与中国大陆端点黑名单 (hk_endpoints)，机房级物理一票否决
    from config.settings import EXCLUDE_HK_REGEX
    hk_endpoints_set = set()

    for k, v in node_colo.items():
        if not k or not v:
            continue
        v_str = str(v)
        if EXCLUDE_HK_REGEX.search(v_str) or any(x in v_str.upper() for x in ["HKG", "HONG KONG", "HONGKONG", "CN"]):
            str_k = str(k).strip()
            if ip_port_pattern.match(str_k):
                hk_endpoints_set.add(str_k)
                hk_endpoints_set.add(str_k.split(":")[0])
            elif node_details and str_k in node_details:
                s = str(node_details[str_k].get("server", "")).strip()
                p = str(node_details[str_k].get("port", "443")).strip()
                if s:
                    hk_endpoints_set.add(f"{s}:{p}")
                    hk_endpoints_set.add(s)

    for ep, c_name in canonical_name_map.items():
        if not ep or not c_name:
            continue
        if EXCLUDE_HK_REGEX.search(str(c_name)) or any(x in str(c_name).upper() for x in ["HKG", "HONG KONG", "HONGKONG"]):
            str_ep = str(ep).strip()
            hk_endpoints_set.add(str_ep)
            if ":" in str_ep:
                hk_endpoints_set.add(str_ep.split(":")[0])

    for n in (all_nodes or []):
        if not n:
            continue
        if EXCLUDE_HK_REGEX.search(str(n)):
            if node_details and n in node_details:
                s = str(node_details[n].get("server", "")).strip()
                p = str(node_details[n].get("port", "443")).strip()
                if s:
                    hk_endpoints_set.add(f"{s}:{p}")
                    hk_endpoints_set.add(s)

    hk_endpoints = sorted(list(hk_endpoints_set))
    formatted_hk_eps = ",\n".join([f"    {json.dumps(ep, ensure_ascii=False)}" for ep in hk_endpoints])
    canonical_map_json = json.dumps(canonical_name_map, ensure_ascii=False, indent=4)
    canonical_map_str = "\n".join("  " + line if i > 0 else line for i, line in enumerate(canonical_map_json.split("\n")))

    # 构建优选池精准特征清单（严格 1:1 对齐实际节点全名，彻底清洗并剔除冗余纯 IP 格式）
    premium_tokens = []
    for n in combined_favs:
        if not n:
            continue
        str_n = str(n).strip()
        # 1. 如果该项为纯 IP:Port 格式
        if ip_port_pattern.match(str_n):
            cand = canonical_name_map.get(str_n)
            if not cand and str_n in ep_to_name:
                cand = ep_to_name[str_n]
            elif not cand and resolve_node_to_current_fn:
                cand = resolve_node_to_current_fn(str_n)

            if cand:
                premium_tokens.append(cand)
            premium_tokens.append(str_n)
        else:
            # 2. 该项本身为节点名称，始终优先保留规范命名本身！
            premium_tokens.append(str_n)
            cand = None
            if resolve_node_to_current_fn:
                resolved = resolve_node_to_current_fn(str_n)
                if resolved and resolved != str_n:
                    cand = resolved
            if cand:
                premium_tokens.append(cand)
            # 补充端点特征
            ep = None
            if get_node_endpoint_fn:
                try:
                    ep = get_node_endpoint_fn(str_n)
                except Exception:
                    pass
            if not ep and node_details and str_n in node_details:
                s = str(node_details[str_n].get("server", "")).strip()
                p = str(node_details[str_n].get("port", "443")).strip()
                if s:
                    ep = f"{s}:{p}"
            if not ep:
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{2,5}))?", str_n)
                if m:
                    ep = f"{m.group(1)}:{m.group(2) or '443'}"
            if ep:
                premium_tokens.append(ep)

    premium_tokens = list(dict.fromkeys(premium_tokens))
    formatted_proxies = ",\n".join([f"    {json.dumps(tok, ensure_ascii=False)}" for tok in premium_tokens])

    # 典藏常青极品池端点清单
    star_tokens = []
    for item in stars_nodes:
        ep = item.get("endpoint", "")
        if ep:
            star_tokens.append(ep)
            if ":" in ep:
                star_tokens.append(ep.split(":")[0])
        m_name = item.get("matched_name", "")
        if m_name:
            star_tokens.append(m_name)
        rem = item.get("remark", "")
        if rem:
            star_tokens.append(rem)
    star_tokens = list(dict.fromkeys(star_tokens))
    formatted_star_eps = ",\n".join([f"    {json.dumps(ep, ensure_ascii=False)}" for ep in star_tokens])
    fission_json = json.dumps(fission_proxies or [], ensure_ascii=False)

    script_code = f"""function main(config) {{
  // ================= 策略组参数定义 (支持定向修改) =================
  const groupInterval = {inter_val};
  const groupTolerance = {tol_val};
  const starsGroupInterval = {star_inter_val};
  const starsGroupTolerance = {star_tol_val};

  const autoGroupName = '⚡ 自动选择';
  const autoGroupNoHkName = '⚡ 自动选择 (非香港)';
  const autoGroupStarsName = '⚡ 自动选择 (典藏)';

  // 优质优选节点规范命名映射 (物理端点 -> 规范化名称，共 {len(canonical_name_map)} 个)
  const canonicalNameMap = {canonical_map_str};

  // 物理香港与中国大陆端点黑名单 (机房级物理一票否决，共 {len(hk_endpoints)} 个)
  const hkEndpoints = [
{formatted_hk_eps}
  ];

  // 优选节点特征识别清单 (严格1:1对齐规范节点全名，共 {len(premium_tokens)} 个)
  const premiumTokens = [
{formatted_proxies}
  ];

  // 典藏常青极品池端点清单 (共 {len(star_tokens)} 个)
  const starTokens = [
{formatted_star_eps}
  ];

  // 香港与中国大陆特征排除规则 (严格过滤香港与大陆，保留台湾省 TW，排除 Google 送中)
  const excludeRegex = /(香港|HK|Hong\\s*Kong|HongKong|中国(?!\\s*台湾)|大陆|回国|\\bCN\\b|送中)/i;

  const allProxies = config.proxies || [];

  // ================= 步骤 0: 物理端点规范更名注入 (去广告、去牛皮癣，统一显示优质规范名) =================
  const usedProxyNames = new Set();
  allProxies.forEach(p => {{ if (p && p.name) usedProxyNames.add(p.name); }});
  const renamedMap = {{}};
  const canonicalAssignedEps = new Set();

  allProxies.forEach(p => {{
    if (!p || !p.server) return;
    const ep = `${{p.server}}:${{p.port}}`;
    const s = String(p.server || '');
    const targetCanonical = canonicalNameMap[ep] || canonicalNameMap[s];
    if (targetCanonical && !canonicalAssignedEps.has(ep)) {{
      canonicalAssignedEps.add(ep);
      const oldName = p.name;
      let newName = targetCanonical;
      if (usedProxyNames.has(newName) && oldName !== newName) {{
        let idx = 2;
        while (usedProxyNames.has(`${{newName}} ${{idx}}`)) {{ idx++; }}
        newName = `${{newName}} ${{idx}}`;
      }}
      usedProxyNames.delete(oldName);
      usedProxyNames.add(newName);
      p.name = newName;
      renamedMap[oldName] = newName;
    }}
  }});

  if (Object.keys(renamedMap).length > 0) {{
    (config['proxy-groups'] || []).forEach(group => {{
      if (group && Array.isArray(group.proxies)) {{
        group.proxies = group.proxies.map(name => renamedMap[name] || name);
      }}
    }});
  }}

  // 判断节点是否命中优选池特征 (节点全称与物理 IP:Port 双向精准匹配，彻底防止通配误吸附与更名遗漏)
  const isPremiumProxy = (p) => {{
    if (!p) return false;
    if (premiumTokens.length === 0) return true;
    const ep = `${{p.server}}:${{p.port}}`;
    const s = String(p.server || '');
    return premiumTokens.includes(p.name) || premiumTokens.includes(ep) || premiumTokens.includes(s);
  }};

  // 判断节点是否命中典藏常青池特征
  const isStarProxy = (p) => {{
    if (!p) return false;
    if (starTokens.length === 0) return false;
    const ep = `${{p.server}}:${{p.port}}`;
    const s = String(p.server || '');
    return starTokens.includes(p.name) || 
           starTokens.includes(ep) || 
           starTokens.includes(s);
  }};

  // 判断节点是否符合纯净非香港/非大陆规则 (物理机房端点 + 节点命名 双重硬核校验)
  const isNonHongKongProxy = (p) => {{
    if (!p) return false;
    const ep = `${{p.server}}:${{p.port}}`;
    const s = String(p.server || '');
    // 物理端点一票否决：无论名字起得多花哨，只要底层机房是香港/大陆，绝对禁止混入非港组
    if (hkEndpoints.includes(ep) || hkEndpoints.includes(s)) return false;
    // 节点命名特征一票否决
    const name = p.name || '';
    if (excludeRegex.test(name)) return false;
    return true;
  }};

  // ================= 规则执行：以云端精选为唯一准绳，严格1对1去重注入 =================

  // 1. 【⚡ 自动选择】：每个优质物理端点严格仅收录 1 个代表节点（优先云端保活节点，绝不多重收录同IP冗余节点）
  const seenAutoEps = new Set();
  let autoProxies = [];

  // 第一优先：如果订阅中存在含有 '优质保活' 或 'auto' 的云端专有节点，绝对优先录用
  allProxies.forEach(p => {{
    const ep = `${{p.server}}:${{p.port}}`;
    const isAutoNode = (p.name.includes('优质保活') || p.name.toLowerCase().includes('auto'));
    if (isAutoNode && isPremiumProxy(p) && !seenAutoEps.has(ep)) {{
      seenAutoEps.add(ep);
      autoProxies.push(p.name);
    }}
  }});

  // 第二优先：补充其他优质端点（若无专有保活节点，则严格只取第 1 个匹配该端点的节点，绝不把同IP其他别名重复塞入）
  allProxies.forEach(p => {{
    const ep = `${{p.server}}:${{p.port}}`;
    if (isPremiumProxy(p) && !seenAutoEps.has(ep)) {{
      seenAutoEps.add(ep);
      autoProxies.push(p.name);
    }}
  }});

  if (autoProxies.length === 0) {{
    autoProxies = allProxies.map(p => p.name);
  }}
  if (autoProxies.length === 0) autoProxies = ['DIRECT'];

  // 2. 【⚡ 自动选择 (非香港)】：严格按照非香港规则，每个非港优质端点同样严格只进 1 个节点！
  const seenNoHkEps = new Set();
  let autoNoHkProxies = [];

  allProxies.forEach(p => {{
    const ep = `${{p.server}}:${{p.port}}`;
    const isAutoNode = (p.name.includes('优质保活') || p.name.toLowerCase().includes('auto'));
    if (isAutoNode && isPremiumProxy(p) && isNonHongKongProxy(p) && !seenNoHkEps.has(ep)) {{
      seenNoHkEps.add(ep);
      autoNoHkProxies.push(p.name);
    }}
  }});

  allProxies.forEach(p => {{
    const ep = `${{p.server}}:${{p.port}}`;
    if (isPremiumProxy(p) && isNonHongKongProxy(p) && !seenNoHkEps.has(ep)) {{
      seenNoHkEps.add(ep);
      autoNoHkProxies.push(p.name);
    }}
  }});

  // 第二梯队【容灾保底】：如果第一梯队的非香港精选节点少于 4 个，自动从全量池中按高信誉地区（日本、新加坡、中国台湾、美国）精选优质备用节点兜底
  if (autoNoHkProxies.length < 4) {{
    const standbyRegions = [
      {{ key: 'JP', regex: /(JP|日本|东京|大阪)/i }},
      {{ key: 'SG', regex: /(SG|新加坡|狮城)/i }},
      {{ key: 'TW', regex: /(TW|台湾|台北)/i }},
      {{ key: 'US', regex: /(US|美国|美区)/i }}
    ];
    for (const reg of standbyRegions) {{
      if (autoNoHkProxies.length >= 4) break;
      let cand = allProxies.find(p => {{
        const ep = `${{p.server}}:${{p.port}}`;
        return isNonHongKongProxy(p) && reg.regex.test(p.name) && (p.name.includes('优选') || p.name.includes('高速')) && !seenNoHkEps.has(ep);
      }});
      if (!cand) {{
        cand = allProxies.find(p => {{
          const ep = `${{p.server}}:${{p.port}}`;
          return isNonHongKongProxy(p) && reg.regex.test(p.name) && !seenNoHkEps.has(ep);
        }});
      }}
      if (cand) {{
        const ep = `${{cand.server}}:${{cand.port}}`;
        seenNoHkEps.add(ep);
        autoNoHkProxies.push(cand.name);
      }}
    }}
  }}

  if (autoNoHkProxies.length === 0) {{
    autoNoHkProxies = allProxies
      .filter(p => isNonHongKongProxy(p))
      .map(p => p.name);
  }}
  if (autoNoHkProxies.length === 0) autoNoHkProxies = ['DIRECT'];

  // 3. 【⚡ 自动选择 (典藏)】：严格按典藏规则直接准入
  const seenStarEps = new Set();
  let starProxies = [];
  allProxies.forEach(p => {{
    const ep = `${{p.server}}:${{p.port}}`;
    if (isStarProxy(p) && !seenStarEps.has(ep)) {{
      seenStarEps.add(ep);
      starProxies.push(p.name);
    }}
  }});
  if (starProxies.length === 0) starProxies = ['DIRECT'];

  // ================= 策略组挂载与规则下发 =================
  const autoGroup = {{
    name: autoGroupName,
    type: 'select',
    proxies: autoProxies
  }};

  const autoGroupNoHk = {{
    name: autoGroupNoHkName,
    type: 'select',
    proxies: autoNoHkProxies
  }};

  const autoGroupStars = {{
    name: autoGroupStarsName,
    type: 'select',
    proxies: starProxies
  }};

  config['proxy-groups'] = config['proxy-groups'] || [];
  config['proxy-groups'] = config['proxy-groups'].filter(
    g => g.name !== autoGroupName && 
         g.name !== autoGroupNoHkName && 
         g.name !== autoGroupStarsName
  );
  config['proxy-groups'].unshift(autoGroupStars);
  config['proxy-groups'].unshift(autoGroup);
  config['proxy-groups'].unshift(autoGroupNoHk);

  // 策略组前置注入：将优选组置于首位作为系统级最强默认保底与快捷入口
  const targetGroups = [autoGroupNoHkName, autoGroupName, autoGroupStarsName];
  config['proxy-groups'].forEach(group => {{
    if (group.name === '☁️ CloudFlareCDN') return; // 保持 CF 专属组纯净
    if (!targetGroups.includes(group.name) && Array.isArray(group.proxies)) {{
      group.proxies = group.proxies.filter(p => !targetGroups.includes(p));
      group.proxies.unshift(...targetGroups);
    }}
  }});

  // ================= RFC-002: 裂变嫁接节点临时注入 (用于真实下行带宽测速) =================
  const fissionProxies = {fission_json};
  if (Array.isArray(fissionProxies) && fissionProxies.length > 0) {{
    config.proxies = config.proxies || [];
    for (let i = 0; i < fissionProxies.length; i++) {{
      config.proxies.push(fissionProxies[i]);
    }}
    const fissionNames = fissionProxies.map(p => p.name);
    (config['proxy-groups'] || []).forEach(group => {{
      if (group && (group.type === 'select' || group.type === 'selector' || group.name === 'GLOBAL' || group.name === '🚀 节点选择' || group.name === '☁️ CloudFlareCDN')) {{
        if (Array.isArray(group.proxies)) {{
          for (let i = 0; i < fissionNames.length; i++) {{
            group.proxies.push(fissionNames[i]);
          }}
        }}
      }}
    }});
  }}

  config.dns = config.dns || {{}};
  config.dns['enhanced-mode'] = 'fake-ip';
  config.dns['fake-ip-range'] = '198.18.0.1/16';

  config.rules = config.rules || [];

  // 反重力 (Antigravity & Gemini API & Google AI) 专属非香港路由规则 (全域顶级域与通配覆盖，绝无盲区)
  const antiGravityRules = [
    // 0. 本地回环与内网白名单直连 (彻底规避 Electron 与 Language Server 本地通讯 56960/65124 误入代理超时)
    'IP-CIDR,127.0.0.0/8,DIRECT,no-resolve',
    'IP-CIDR,192.168.0.0/16,DIRECT,no-resolve',
    'IP-CIDR,10.0.0.0/8,DIRECT,no-resolve',
    'IP-CIDR,172.16.0.0/12,DIRECT,no-resolve',

    // 1. 禁用 QUIC (UDP 443)：强制 Chrome/Edge 网页端使用高稳定的 TCP HTTP/2 连接，彻底根治网页版 Gemini 偶发断流卡死
    'AND,((DST-PORT,443),(NETWORK,UDP)),REJECT',

    // 1. 反重力客户端进程级绝对锁定 (全流量 100% 走非香港组，无论访问什么域名或裸 IP)
    `PROCESS-NAME,Antigravity.exe,${{autoGroupNoHkName}}`,
    `PROCESS-NAME,language_server.exe,${{autoGroupNoHkName}}`,

    // 1.5 YouTube & 视频流媒体极速出口直达 (100% 走香港高速，绝对置顶于任何 Google 规则前，杜绝误入非港组超时)
    `DOMAIN-KEYWORD,youtube,${{autoGroupName}}`,
    `DOMAIN-KEYWORD,googlevideo,${{autoGroupName}}`,
    `DOMAIN-KEYWORD,ytimg,${{autoGroupName}}`,
    `DOMAIN-SUFFIX,googlevideo.com,${{autoGroupName}}`,
    `DOMAIN-SUFFIX,youtube.com,${{autoGroupName}}`,
    `DOMAIN-SUFFIX,ytimg.com,${{autoGroupName}}`,
    `DOMAIN-SUFFIX,ggpht.com,${{autoGroupName}}`,
    `DOMAIN-SUFFIX,youtu.be,${{autoGroupName}}`,
    `DOMAIN-SUFFIX,yt.be,${{autoGroupName}}`,
    `DOMAIN-SUFFIX,youtube-nocookie.com,${{autoGroupName}}`,

    // 2. Antigravity & DeepMind 核心与专属顶级域
    `DOMAIN-KEYWORD,antigravity,${{autoGroupNoHkName}}`,
    `DOMAIN-KEYWORD,deepmind,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,antigravity.google,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,antigravity.dev,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,antigravity.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,deepmind.google,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,deepmind.com,${{autoGroupNoHkName}}`,

    // 3. Google Gemini & AI Studio 核心模型、开发平台与 Cloud Run 微服务
    `DOMAIN-KEYWORD,gemini,${{autoGroupNoHkName}}`,
    `DOMAIN-KEYWORD,makersuite,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,run.app,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,google.dev,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,gemini.google.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,aistudio.google.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,maker-suite.google,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,generativelanguage.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,daily-cloudcode-pa.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,cloudcode-pa.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,alkalimakersuite-pa.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,alkalimakersuiteapplets.pa.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,proactivebackend-pa.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,cloudaicompanion.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,developerprofiles.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,aiplatform.googleapis.com,${{autoGroupNoHkName}}`,

    // 3. Google 账户认证、底层通信服务、应用组件与全球网络基础设施 (全面锁定非香港)
    `DOMAIN-SUFFIX,google,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,goog,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,accounts.google.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,oauth2.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,google.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,gstatic.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,googleusercontent.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,googleprod.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,googlers.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,withgoogle.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,appspot.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,1e100.net,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,gvt0.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,gvt1.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,gvt2.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,gvt3.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,g.co,${{autoGroupNoHkName}}`,
    `DOMAIN-KEYWORD,google,${{autoGroupNoHkName}}`,
    `DOMAIN-KEYWORD,1e100,${{autoGroupNoHkName}}`
  ];

  // 4. 【原生规则深度净化重写引擎】
  // 遍历清理并纠正原生订阅中的 10,000+ 条规则，彻底拔除所有将 Google / AI 流量劫持流向 🚀 节点选择 或 GLOBAL 的旧规则
  const googleAiSanitizeRegex = /(google|gemini|antigravity|deepmind|makersuite|bard|run\\.app|1e100|gvt\\d|notebooklm)/i;
  if (Array.isArray(config.rules)) {{
    config.rules = config.rules.map(ruleStr => {{
      if (typeof ruleStr !== 'string') return ruleStr;
      const parts = ruleStr.split(',');
      if (parts.length >= 3) {{
        const payload = parts[1].trim();
        const target = parts[2].trim();
        if (payload.includes('googlevideo') || payload.includes('youtube') || payload.includes('ytimg') || payload.includes('ggpht') || payload.includes('youtu.be')) {{
          parts[2] = autoGroupName;
          return parts.join(',');
        }}
        if (googleAiSanitizeRegex.test(payload) && (target === '🚀 节点选择' || target === 'GLOBAL' || target === '☁️ CloudFlareCDN' || target === autoGroupName)) {{
          parts[2] = autoGroupNoHkName;
          return parts.join(',');
        }}
      }}
      return ruleStr;
    }});
  }}

  // 5. 【规则集严格去重与置顶压制】(确保 antiGravityRules 始终占据第 0~N 位最高优先级，且无多重冗余)
  const finalRules = [];
  const seenRuleSet = new Set();
  for (const r of antiGravityRules) {{
    if (!seenRuleSet.has(r)) {{
      seenRuleSet.add(r);
      finalRules.push(r);
    }}
  }}
  for (const r of (config.rules || [])) {{
    if (!seenRuleSet.has(r)) {{
      seenRuleSet.add(r);
      finalRules.push(r);
    }}
  }}
  config.rules = finalRules;

  return config;
}}"""

    return script_code, premium_tokens, star_tokens


def sync_runtime_clash_yaml_and_reload(
    fission_proxies=None,
    parent_dir=PARENT_DIR,
):
    """
    双引擎内核热同步：
    直接按照 Script.js 相同规则将优选节点、典藏节点同步写入 clash-verge.yaml，清理废弃策略组，
    并通过 PUT /configs?force=true 带真实文件路径通知 Mihomo 秒级重载。
    彻底解决快捷键无法穿透、必须手动在 Verge 内点击激活的问题。
    """
    runtime_yaml = os.path.join(parent_dir, "clash-verge.yaml")
    if not os.path.exists(runtime_yaml):
        return False, "未找到 clash-verge.yaml 运行时文件"

    try:
        import yaml
        with open(runtime_yaml, "r", encoding="utf-8") as f:
            rt_cfg = yaml.safe_load(f)

        if not rt_cfg or not isinstance(rt_cfg, dict):
            return False, "clash-verge.yaml 配置格式异常"

        rt_cfg["proxies"] = rt_cfg.get("proxies") or []

        # 0. 清理可能存在的非法加密方式节点（如未知 SS cipher 导致内核 400 报错）
        VALID_SS_CIPHERS = {
            "aes-128-gcm", "aes-192-gcm", "aes-256-gcm",
            "chacha20-ietf-poly1305", "xchacha20-ietf-poly1305",
            "aes-128-ctr", "aes-192-ctr", "aes-256-ctr",
            "aes-128-cfb", "aes-192-cfb", "aes-256-cfb",
            "rc4-md5", "chacha20-ietf",
            "2022-blake3-aes-128-gcm", "2022-blake3-aes-256-gcm", "2022-blake3-chacha20-poly1305",
        }
        sanitized_proxies = []
        seen_names = set()
        for p in rt_cfg["proxies"]:
            if not isinstance(p, dict) or "name" not in p:
                continue
            if p["name"] in seen_names:
                continue
            if str(p.get("type", "")).lower() == "ss":
                if str(p.get("cipher", "")).lower() not in VALID_SS_CIPHERS:
                    continue
            seen_names.add(p["name"])
            sanitized_proxies.append(p)
        rt_cfg["proxies"] = sanitized_proxies
        existing_names = set(seen_names)

        # 1. 注入临时裂变节点（若有）
        fission_names = []
        if fission_proxies and isinstance(fission_proxies, list):
            for fp in fission_proxies:
                if fp and fp.get("name"):
                    fission_names.append(fp["name"])
                    if fp["name"] not in existing_names:
                        rt_cfg["proxies"].append(fp)
                        existing_names.add(fp["name"])

        # 2. 清理特供非CF策略组与注入节点
        auto_native_name = "⚡ 自动选择 (特供非CF)"
        native_group_name = "💎 特供节点 (非CF)"

        # 清除可能残留的特供原生节点
        rt_cfg["proxies"] = [
            p for p in rt_cfg.get("proxies", [])
            if not (isinstance(p, dict) and ("特供" in str(p.get("name", "")) or "💎" in str(p.get("name", ""))))
        ]

        # 3. 更新策略组列表，彻底移除特供策略组
        groups = rt_cfg.get("proxy-groups", [])
        groups = [g for g in groups if g.get("name") not in (auto_native_name, native_group_name)]
        rt_cfg["proxy-groups"] = groups

        # 4. 从所有策略组中剔除特供策略组与特供节点引用，并将受守护策略组升级为 select 模式 (支持自愈秒级切节点)
        target_groups = ["⚡ 自动选择 (非香港)", "⚡ 自动选择", "⚡ 自动选择 (典藏)"]
        for g in rt_cfg["proxy-groups"]:
            if isinstance(g, dict):
                if g.get("name") in target_groups:
                    g["type"] = "select"
                    g.pop("url", None)
                    g.pop("interval", None)
                    g.pop("tolerance", None)
                    g.pop("lazy", None)
                if isinstance(g.get("proxies"), list):
                    g["proxies"] = [
                        p for p in g["proxies"]
                        if p not in (auto_native_name, native_group_name) and not ("特供" in str(p) or "💎" in str(p))
                    ]
            if g.get("name") in ("🚀 节点选择", "GLOBAL"):
                p_list = g.get("proxies", [])
                p_list = [p for p in p_list if p not in target_groups]
                p_list = target_groups + p_list
                for fn in fission_names:
                    if fn not in p_list:
                        p_list.append(fn)
                g["proxies"] = p_list

        # 同步对齐策略组与节点规范命名，彻底消除未改名与香港节点误入非港组
        try:
            cfg_path = os.path.join(parent_dir, "node_assistant_config.json")
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    asst_cfg = json.load(f)
                favs = asst_cfg.get("favorites", [])
                cloud_eps = asst_cfg.get("cloud_endpoints", {})
                node_colo = asst_cfg.get("node_colo", {})

                # 1. 规范化重命名 rt_cfg["proxies"]
                used_p_names = set(p["name"] for p in rt_cfg.get("proxies", []) if isinstance(p, dict) and "name" in p)
                name_replace_map = {}
                assigned_eps = set()
                for p in rt_cfg.get("proxies", []):
                    if not isinstance(p, dict) or "server" not in p:
                        continue
                    ep = f"{p['server']}:{p.get('port', 443)}"
                    s = str(p['server'])
                    target_c = cloud_eps.get(ep) or cloud_eps.get(s)
                    if target_c and ep not in assigned_eps:
                        assigned_eps.add(ep)
                        old_name = p.get("name", "")
                        new_name = target_c
                        if new_name in used_p_names and old_name != new_name:
                            idx = 2
                            while f"{new_name} {idx}" in used_p_names:
                                idx += 1
                            new_name = f"{new_name} {idx}"
                        used_p_names.discard(old_name)
                        used_p_names.add(new_name)
                        p["name"] = new_name
                        if old_name:
                            name_replace_map[old_name] = new_name

                # 同步更新策略组引用
                if name_replace_map:
                    for g in rt_cfg.get("proxy-groups", []):
                        if isinstance(g, dict) and isinstance(g.get("proxies"), list):
                            g["proxies"] = [name_replace_map.get(pn, pn) for pn in g["proxies"]]

                # 2. 构建香港物理端点黑名单
                from config.settings import EXCLUDE_HK_REGEX
                rt_hk_eps = set()
                for k, v in node_colo.items():
                    if v and (EXCLUDE_HK_REGEX.search(str(v)) or any(x in str(v).upper() for x in ["HKG", "HONG KONG", "CN"])):
                        rt_hk_eps.add(str(k).strip())
                        if ":" in str(k):
                            rt_hk_eps.add(str(k).split(":")[0])
                for ep, c_name in cloud_eps.items():
                    if c_name and (EXCLUDE_HK_REGEX.search(str(c_name)) or any(x in str(c_name).upper() for x in ["HKG", "HONG KONG"])):
                        rt_hk_eps.add(str(ep).strip())
                        if ":" in str(ep):
                            rt_hk_eps.add(str(ep).split(":")[0])

                # 3. 对齐 ⚡ 自动选择 和 ⚡ 自动选择 (非香港)
                p_set = set(p.get("name") for p in rt_cfg.get("proxies", []) if isinstance(p, dict))
                matched_favs = [f for f in favs if f in p_set]
                proxy_by_name = {p["name"]: p for p in rt_cfg.get("proxies", []) if isinstance(p, dict) and "name" in p}

                for g in rt_cfg.get("proxy-groups", []):
                    if not isinstance(g, dict):
                        continue
                    if g.get("name") == "⚡ 自动选择" and matched_favs:
                        g["proxies"] = matched_favs
                    elif g.get("name") == "⚡ 自动选择 (非香港)" and isinstance(g.get("proxies"), list):
                        # 剔除所有属于香港端点或名字含香港的代理
                        clean_nohk = []
                        for pn in g["proxies"]:
                            p_obj = proxy_by_name.get(pn)
                            if p_obj:
                                ep = f"{p_obj.get('server')}:{p_obj.get('port', 443)}"
                                s = str(p_obj.get('server', ''))
                                if ep in rt_hk_eps or s in rt_hk_eps:
                                    continue
                            if EXCLUDE_HK_REGEX.search(pn):
                                continue
                            clean_nohk.append(pn)
                        g["proxies"] = clean_nohk if clean_nohk else ["DIRECT"]
        except Exception:
            pass

        # 4.4 确保 DNS 开启 fake-ip 模式并加入流媒体 CDN 域名，杜绝本地污染导致的视频分片 404
        if "dns" in rt_cfg and isinstance(rt_cfg["dns"], dict):
            rt_cfg["dns"]["enhanced-mode"] = "fake-ip"
            rt_cfg["dns"]["fake-ip-range"] = "198.18.0.1/16"
            fb_filter = rt_cfg["dns"].get("fallback-filter") or {}
            fb_domains = fb_filter.get("domain") or []
            needed_domains = ["+.google.com", "+.youtube.com", "+.googlevideo.com", "+.ytimg.com", "+.ggpht.com"]
            for nd in needed_domains:
                if nd not in fb_domains:
                    fb_domains.append(nd)
            fb_filter["domain"] = fb_domains
            rt_cfg["dns"]["fallback-filter"] = fb_filter

        # 4.6 规则净化与 YouTube 极速出口锁定 (确保视频流与主站同在香港出口，彻底杜绝新加坡超时死锁)
        raw_rules = rt_cfg.get("rules") or []
        youtube_rules = [
            "DOMAIN-KEYWORD,youtube,⚡ 自动选择",
            "DOMAIN-KEYWORD,googlevideo,⚡ 自动选择",
            "DOMAIN-KEYWORD,ytimg,⚡ 自动选择",
            "DOMAIN-SUFFIX,googlevideo.com,⚡ 自动选择",
            "DOMAIN-SUFFIX,youtube.com,⚡ 自动选择",
            "DOMAIN-SUFFIX,ytimg.com,⚡ 自动选择",
            "DOMAIN,yt3.ggpht.com,⚡ 自动选择",
            "DOMAIN-SUFFIX,youtube-nocookie.com,⚡ 自动选择",
            "DOMAIN-SUFFIX,youtu.be,⚡ 自动选择",
            "DOMAIN-SUFFIX,yt.be,⚡ 自动选择",
        ]
        cleaned_rules = [
            r for r in raw_rules
            if isinstance(r, str) and not any(k in r.lower() for k in ["googlevideo", "youtube", "ytimg"])
        ]
        # 寻找本地网络直连与 UDP 443 拦截之后的最佳前置插入点
        prefix_idx = 0
        for i, r in enumerate(cleaned_rules):
            if "REJECT" in r or "127.0.0.0" in r or "192.168.0.0" in r:
                prefix_idx = i + 1
            else:
                break
        rt_cfg["rules"] = cleaned_rules[:prefix_idx] + youtube_rules + cleaned_rules[prefix_idx:]

        # 5. 原子写入 clash-verge.yaml
        tmp_file = runtime_yaml + ".tmp"
        with open(tmp_file, "w", encoding="utf-8") as f:
            yaml.dump(rt_cfg, f, allow_unicode=True, sort_keys=False)
        os.replace(tmp_file, runtime_yaml)

        # 6. 调用 Mihomo API 热重载
        try:
            import requests
            headers = {"Authorization": "Bearer set-your-secret", "Content-Type": "application/json"}
            payload = json.dumps({"path": runtime_yaml})
            r = requests.put("http://127.0.0.1:9097/configs?force=true", data=payload, headers=headers, timeout=3.0)
            if r.status_code in (200, 204):
                try:
                    requests.delete("http://127.0.0.1:9097/connections", headers=headers, timeout=1.0)
                except Exception:
                    pass
                return True, "Mihomo 秒级重载成功"
            else:
                return False, f"Mihomo API 返回状态码: {r.status_code}"
        except Exception as api_err:
            return False, f"Mihomo API 请求异常: {api_err}"

    except Exception as ex:
        return False, str(ex)


def write_script_js(script_code, target_path=DEFAULT_SCRIPT_JS, base_dir=BASE_DIR, sync_runtime=True, fission_proxies=None):
    """
    将生成的 JS 脚本写入目标路径，并同步写入 profiles 目录下的所有其他扩展 js 脚本。
    默认自动触发 clash-verge.yaml 双引擎内核热重载。
    """
    if not target_path or not os.path.exists(target_path):
        js_files = glob.glob(os.path.join(base_dir, "*.js"))
        if js_files:
            target_path = js_files[0]
        else:
            target_path = DEFAULT_SCRIPT_JS

    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(script_code)

        for js_f in glob.glob(os.path.join(base_dir, "*.js")):
            if os.path.basename(js_f) != os.path.basename(target_path):
                try:
                    with open(js_f, "w", encoding="utf-8") as f:
                        f.write(script_code)
                except Exception:
                    pass

        if sync_runtime:
            try:
                sync_runtime_clash_yaml_and_reload(fission_proxies=fission_proxies)
            except Exception:
                pass

        return True, target_path
    except Exception as ex:
        return False, str(ex)


def generate_and_write_active_script(fission_proxies=None):
    """
    自动从 node_assistant_config.json 加载当前配置，动态生成 Script.js 并持久化同步至所有 profiles 脚本与内核 yaml。
    """
    from config.settings import CONFIG_STORAGE_PATH
    favorites = []
    stars_nodes = []
    all_nodes = []
    node_details = {}
    g_inter = "300"
    g_tol = "20"
    s_inter = "300"
    s_tol = "20"

    if os.path.exists(CONFIG_STORAGE_PATH):
        try:
            with open(CONFIG_STORAGE_PATH, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            favorites = cfg.get("favorites", [])
            stars_nodes = cfg.get("stars_nodes", [])
            all_nodes = cfg.get("all_nodes", [])
            node_details = cfg.get("node_details", {})
            g_inter = str(cfg.get("group_interval", "300"))
            g_tol = str(cfg.get("group_tolerance", "20"))
            s_inter = str(cfg.get("star_group_interval", "300"))
            s_tol = str(cfg.get("star_group_tolerance", "20"))
        except Exception:
            pass

    from services.colo_service import is_asian_node

    script_code, p_tokens, s_tokens = build_script_js(
        favorites=favorites,
        stars_nodes=stars_nodes,
        all_nodes=all_nodes,
        node_details=node_details,
        group_interval=g_inter,
        group_tolerance=g_tol,
        star_group_interval=s_inter,
        star_group_tolerance=s_tol,
        is_asian_node_fn=is_asian_node,
        fission_proxies=fission_proxies,
    )
    ok, res = write_script_js(script_code, sync_runtime=True, fission_proxies=fission_proxies)
    return ok, res, len(p_tokens), len(s_tokens)


