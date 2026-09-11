import glob
import json
import os
import re

from config.settings import BASE_DIR, DEFAULT_SCRIPT_JS


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
):
    """
    动态生成 Clash Verge Rev 策略组合并脚本 (Script.js)
    返回: (script_code: str, premium_tokens: list[str], star_tokens: list[str])
    """
    inter_val = str(group_interval).strip() if str(group_interval).strip().isdigit() else "300"
    tol_val = str(group_tolerance).strip() if str(group_tolerance).strip().isdigit() else "20"
    star_inter_val = str(star_group_interval).strip() if str(star_group_interval).strip().isdigit() else "300"
    star_tol_val = str(star_group_tolerance).strip() if str(star_group_tolerance).strip().isdigit() else "20"

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

    # 构建优选池精准特征清单（严格 1:1 对齐实际节点全名，彻底清洗并剔除冗余纯 IP 格式）
    premium_tokens = []
    for n in combined_favs:
        if not n:
            continue
        str_n = str(n).strip()
        # 1. 如果该项为纯 IP:Port 格式
        if ip_port_pattern.match(str_n):
            cand = None
            if str_n in ep_to_name:
                cand = ep_to_name[str_n]
            elif resolve_node_to_current_fn:
                cand = resolve_node_to_current_fn(str_n)

            if cand and cand in (all_nodes or []):
                premium_tokens.append(cand)
            elif cand:
                premium_tokens.append(cand)
            else:
                # 若全量池中确实无对应命名的节点，则保留原始端点
                premium_tokens.append(str_n)
        else:
            # 2. 该项本身为节点名称，必要时通过更名函数解析至当前最新全名
            cand = str_n
            if resolve_node_to_current_fn:
                resolved = resolve_node_to_current_fn(cand)
                if resolved and resolved in (all_nodes or []):
                    cand = resolved
            premium_tokens.append(cand)

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

  // 优选节点特征识别清单 (严格1:1对齐规范节点全名，共 {len(premium_tokens)} 个)
  const premiumTokens = [
{formatted_proxies}
  ];

  // 典藏常青极品池端点清单 (共 {len(star_tokens)} 个)
  const starTokens = [
{formatted_star_eps}
  ];

  // 香港与中国大陆特征排除规则 (严格过滤香港与大陆，保留台湾省 TW)
  const excludeRegex = /(香港|HK|Hong\\s*Kong|HongKong|中国(?!\\s*台湾)|大陆|回国|\\bCN\\b)/i;

  const allProxies = config.proxies || [];

  // 判断节点是否命中优选池特征 (节点全称与物理 IP:Port 双向精准匹配，彻底防止通配误吸附与更名遗漏)
  const isPremiumProxy = (p) => {{
    if (premiumTokens.length === 0) return true;
    const ep = `${{p.server}}:${{p.port}}`;
    return premiumTokens.includes(p.name) || premiumTokens.includes(ep);
  }};

  // 判断节点是否命中典藏常青池特征
  const isStarProxy = (p) => {{
    if (starTokens.length === 0) return false;
    const ep = `${{p.server}}:${{p.port}}`;
    const s = String(p.server || '');
    return starTokens.includes(p.name) || 
           starTokens.includes(ep) || 
           starTokens.includes(s);
  }};

  // 判断节点是否符合纯净非香港/非大陆规则
  const isNonHongKongProxy = (p) => {{
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
    type: 'url-test',
    url: 'https://www.apple.com/library/test/success.html',
    interval: groupInterval,
    lazy: false,
    tolerance: groupTolerance,
    proxies: autoProxies
  }};

  const autoGroupNoHk = {{
    name: autoGroupNoHkName,
    type: 'url-test',
    url: 'https://www.apple.com/library/test/success.html',
    interval: groupInterval,
    lazy: false,
    tolerance: groupTolerance,
    proxies: autoNoHkProxies
  }};

  const autoGroupStars = {{
    name: autoGroupStarsName,
    type: 'url-test',
    url: 'https://www.apple.com/library/test/success.html',
    interval: starsGroupInterval,
    lazy: false,
    tolerance: starsGroupTolerance,
    proxies: starProxies
  }};

  config['proxy-groups'] = config['proxy-groups'] || [];
  config['proxy-groups'] = config['proxy-groups'].filter(
    g => g.name !== autoGroupName && g.name !== autoGroupNoHkName && g.name !== autoGroupStarsName
  );
  config['proxy-groups'].unshift(autoGroupStars);
  config['proxy-groups'].unshift(autoGroup);
  config['proxy-groups'].unshift(autoGroupNoHk);

  // 策略组前置注入：将【非香港】置于首位作为系统级最强默认保底
  const targetGroups = [autoGroupNoHkName, autoGroupName, autoGroupStarsName];
  config['proxy-groups'].forEach(group => {{
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

  config.rules = config.rules || [];

  // 反重力 (Antigravity & Gemini API & Google AI) 专属非香港路由规则 (全域顶级域与通配覆盖，绝无盲区)
  const antiGravityRules = [
    // 1. Antigravity & DeepMind 核心与专属顶级域
    `DOMAIN-KEYWORD,antigravity,${{autoGroupNoHkName}}`,
    `DOMAIN-KEYWORD,deepmind,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,antigravity.google,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,antigravity.dev,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,antigravity.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,deepmind.google,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,deepmind.com,${{autoGroupNoHkName}}`,

    // 2. Google Gemini & AI Studio 核心模型、开发平台与 Cloud Run 微服务
    `DOMAIN-KEYWORD,gemini,${{autoGroupNoHkName}}`,
    `DOMAIN-KEYWORD,makersuite,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,run.app,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,google.dev,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,gemini.google.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,aistudio.google.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,maker-suite.google,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,generativelanguage.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,alkalimakersuite-pa.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,alkalimakersuiteapplets.pa.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,proactivebackend-pa.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,cloudaicompanion.googleapis.com,${{autoGroupNoHkName}}`,
    `DOMAIN-SUFFIX,cloudcode-pa.googleapis.com,${{autoGroupNoHkName}}`,
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


def write_script_js(script_code, target_path=DEFAULT_SCRIPT_JS, base_dir=BASE_DIR):
    """
    将生成的 JS 脚本写入目标路径，并同步写入 profiles 目录下的所有其他扩展 js 脚本
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
        return True, target_path
    except Exception as ex:
        return False, str(ex)
