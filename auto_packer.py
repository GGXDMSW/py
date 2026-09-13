import os

def is_ignored(path):
    ignored_dirs = {'.git', '__pycache__', '.idea', '.vscode', 'venv', 'env', 'node_modules', 'dist', 'build', 'gui', 'scratch'}
    ignored_exts = {'.pyc', '.pyd', '.exe', '.dll', '.so', '.dylib', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.ico', '.pdf', '.bak', '.json', '.txt', '.log'}
    
    parts = os.path.normpath(path).split(os.sep)
    if any(part in ignored_dirs for part in parts):
        return True
        
    ext = os.path.splitext(path)[1].lower()
    if ext in ignored_exts:
        return True
        
    if os.path.basename(path) == 'repo_context.md':
        return True
        
    return False

DIR_ANNOTATIONS = {
    'config': '全局静态配置与持久化管理器 (Settings & ConfigManager)',
    'core': '全局核心状态机与跨线程事件总线 (StateManager & SignalBus)',
    'gui_fluent': '现代 Fluent Design 风格桌面 UI 前端体系',
    'gui_fluent/components': 'UI 结构性卡片与基础组件 (TopBar, BottomBar, LogPanel, etc.)',
    'gui_fluent/pages': '各功能业务独立子页面 (Active, Favorites, Stars, Blacklists, etc.)',
    'gui_fluent/pipelines': 'UI 绑定的前台异步长任务工作流 (AutoPipeline, FavPipeline)',
    'gui_fluent/widgets': '高级复合数据表格与交互式对话框组件',
    'pipelines': '后台核心任务执行管线与定时自动优选调度器',
    'services': '底层领域算法服务 (ClashClient, Probe, Colo, Pool, ScriptGenerator, etc.)',
    'utils': '系统级 Win32 与底层通用支撑工具集'
}

FILE_ANNOTATIONS = {
    'AGENTS.md': '全局规则定义与 Bark 自动化通知指令',
    'auto_packer.py': '全局大地图与源码打包发布器（生成 repo_context.md）',
    'gemini-code-1788793285196.py': '单文件完整归档实现（历史原型与算法参考实现）',
    'main.py': '原生/经典 GUI 入口启动器（包含环境自检与引导）',
    'main_fluent.py': '现代 PyQt6 Fluent Design 桌面应用主启动入口',
    'temp_runner.js': '历史 Script.js 脚本测试运行样本',
    '代码审查报告.md': '系统工程代码审查与重构规划报告',
    'config/__init__.py': '配置模块包声明',
    'config/config_manager.py': 'node_assistant_config.json 线程安全持久化读写与原子写盘',
    'config/settings.py': '全局静态配置、默认参数、主题样式、测速常量与正则排除规则',
    'core/__init__.py': '核心状态与事件包声明',
    'core/signal_bus.py': 'PyQt6 SignalBus 全局事件解耦总线（跨线程 UI 信号传递）',
    'core/state_manager.py': 'StateManager 全局线程安全事实源（唯一状态中枢与并发互斥锁管理）',
    'gui_fluent/__init__.py': 'Fluent 界面包声明',
    'gui_fluent/app_controller.py': 'AppController 核心调度协调器（业务中枢、状态机流转、流水线与哨兵生命周期管理）',
    'gui_fluent/main_window.py': 'MainWindow 主窗口框架（Fluent 侧边导航栏、托盘气泡提示、日志与页签装配）',
    'gui_fluent/components/__init__.py': 'UI 组件包声明',
    'gui_fluent/components/bottom_action_bar.py': '底部快捷状态栏与启停联动按钮栏',
    'gui_fluent/components/log_panel.py': '终端式实时动态日志高亮输出控制面板',
    'gui_fluent/components/pipeline_card.py': '管道执行卡片与进度状态展示容器',
    'gui_fluent/components/top_bar.py': '顶部全局统计状态栏（节点数、自愈次数、延迟概览）',
    'gui_fluent/pages/__init__.py': '业务页面包声明',
    'gui_fluent/pages/page_active.py': '当前活跃节点监控与实时连接状态展示页',
    'gui_fluent/pages/page_cloud_text.py': '云端订阅与直连文本批量导入/同步管理页',
    'gui_fluent/pages/page_delay_black.py': '延迟超标与高抖动黑名单管理页',
    'gui_fluent/pages/page_favorites.py': '精选池管理页（包含一键检测当前目录送中状态、增量优选、手动自愈等）',
    'gui_fluent/pages/page_speed_black.py': '测速低速淘汰黑名单管理页',
    'gui_fluent/pages/page_stars.py': '典藏常青极品池管理与权重配置页',
    'gui_fluent/pages/page_verified.py': '候选已验证节点全量列表页',
    'gui_fluent/pipelines/__init__.py': 'Fluent 管道包声明',
    'gui_fluent/pipelines/auto_pipeline.py': 'AutoPipeline 全量大优选异步管道（多线程测速、机房探测、更名入池）',
    'gui_fluent/pipelines/fav_pipeline.py': 'FavPipeline 优质复测留任异步管道（增量测活、淘汰劣质、双引擎热更）',
    'gui_fluent/widgets/__init__.py': '复合控件包声明',
    'gui_fluent/widgets/c_miner_dialog.py': 'C 段矿机弹窗界面（设置扫描参数、启动并发探测并实时呈现扫描结果）',
    'gui_fluent/widgets/node_table.py': '通用节点数据表格控件（支持排序、筛选、批量操作与状态高亮）',
    'gui_fluent/widgets/stars_table.py': '典藏节点专用维护表格控件',
    'gui_fluent/widgets/verified_table.py': '已验证节点维护表格控件',
    'pipelines/__init__.py': '管道基类包声明',
    'pipelines/base_pipeline.py': '抽象管道基类（定义生命周期钩子、进度计算与安全取消机制）',
    'pipelines/scheduler.py': '后台定时任务调度器（定时自动触发全量大优选与精选复测）',
    'services/__init__.py': '领域服务包声明',
    'services/auto_heal_watcher.py': 'AutoHealWatcher 秒级无感自愈哨兵（单向发包黑洞感知、Google 429/HK 合规探针、12h 隔离冷冻、15s 开机保护）',
    'services/c_segment_miner.py': 'CSegmentMiner C 段矿机并发嗅探服务（高频端口扫描与存活发现）',
    'services/clash_client.py': 'ClashClient Mihomo/Clash Verge REST API 交互客户端（节点切换、延时测试、连接清理）',
    'services/colo_service.py': 'ColoService Cloudflare 物理机房嗅探与 7 天防漂移算法',
    'services/filter_service.py': 'FilterService 节点抖动过滤、超时判定与低速黑名单服务',
    'services/pool_service.py': 'PoolService 多池聚合计算服务（精选、典藏、黑名单配额与分组编排）',
    'services/probe_service.py': 'ProbeService HTTP 微探针与分段下行真实带宽测速引擎',
    'services/script_generator.py': 'ScriptGenerator Script.js 扩展脚本动态渲染引擎与双引擎热重载',
    'services/subscription_service.py': 'SubscriptionService 订阅拉取、物理端点提取去重与规范命名对齐',
    'utils/__init__.py': '工具库包声明',
    'utils/win32_utils.py': 'Windows Win32 API 辅助工具（快捷键模拟、注册表/端口探测、进程状态监控）'
}

def generate_directory_tree(dir_path='.', prefix=''):
    lines = []
    items = sorted(os.listdir(dir_path))
    valid_items = []
    for item in items:
        p = os.path.join(dir_path, item)
        norm_p = os.path.normpath(p).replace(os.sep, '/')
        if is_ignored(norm_p):
            continue
        valid_items.append((item, os.path.isdir(p), norm_p))
        
    for index, (name, is_dir, norm_p) in enumerate(valid_items):
        is_last = (index == len(valid_items) - 1)
        connector = '└── ' if is_last else '├── '
        child_prefix = '    ' if is_last else '│   '
        
        rel_key = norm_p[2:] if norm_p.startswith('./') else norm_p
        
        if is_dir:
            desc = DIR_ANNOTATIONS.get(rel_key, '')
            desc_str = f'  # {desc}' if desc else ''
            lines.append(f'{prefix}{connector}{name}/{desc_str}')
            lines.extend(generate_directory_tree(os.path.join(dir_path, name), prefix + child_prefix))
        else:
            desc = FILE_ANNOTATIONS.get(rel_key, '')
            desc_str = f'  # {desc}' if desc else ''
            lines.append(f'{prefix}{connector}{name}{desc_str}')
            
    return lines

GOD_VIEW_MAP_TEMPLATE = """# 🌌 反重力平台 py 项目「绝对上帝视角」架构总图 (God-View Architecture Map)

> **致下一任 AI 架构师 / 核心开发者**：
> 本文件是本项目的最高级别系统全景认知枢纽与全量源码大地图。
> 无论你是接手重构、排查疑难故障，还是新增扩展业务，请务必优先精读本文档。
> 本文档赋予你对整个代码库拓扑链路、并发锁分布、状态唯一事实源生命周期、双引擎内核热更、物理机房与送中合规判定机制、历史排雷纪要以及全量无遗漏源码的 **100% 绝对上帝视角**。阅读完毕后即可达到零认知损耗接手、精准决策与系统级架构治理。

---

## 一、 项目定位与全景蓝图 (System Mission & Architectural Overview)

本系统是一套专为 **Clash Verge Rev** 量身打造的高性能、自动化节点优选、全链路状态守护与秒级无感自愈中枢。整体遵循 **分层解耦、单向依赖、Controller中枢编排、双引擎热重载** 的企业级工程架构。

### 核心能力矩阵：
1. **真实下行带宽多线程并发压测**：基于微探针与真实测速文件分段下载，摒弃虚假 ICMP/TCP Ping 延迟，测定真实网络吞吐能力（MB/s）。
2. **Cloudflare 物理机房嗅探与防漂移**：并发嗅探端点真实机房（如 HKG、NRT、SIN、SJC），记录 7 天历史记录，精准剔除跨境漂移节点，确保落地合规。
3. **物理端点去重与全生命周期规范更名**：以 `IP:Port` 物理端点为核心键，对混乱的机场营销名称进行清洗，永久固化统一命名（如 `香港 HKG 22.56 MB/s`）。
4. **秒级无感断流自愈守护 (AutoHealWatcher)**：后台 1.0s 旁路轮询连接表，毫秒级发现单向发包黑洞（tx>0, rx==0）与软失速，自动顺位无感切换节点并熔断坏死连接。
5. **Google 429 验证码/人机拦截与香港送中主动合规探针**：双重检测 Google 阻断状态与送中重定向，阻断节点触发 12 小时冷冻隔离，彻底杜绝 Google/YouTube/IG 突发打不开。
6. **双引擎内核热重载 (Dual-Engine Hot-Reload)**：融合 `Script.js` 扩展脚本注入与运行时配置原子写盘 + REST API 重载通知，彻底攻克快捷键失效与配置穿透故障。

---

## 二、 全局代码库文件树状结构 (Directory Tree & Component Manifest)

以下为当前项目的完整目录与源文件全景树状图（所有活跃模块 100% 无遗漏呈现）：

```
py/
{DIRECTORY_TREE}
```

---

## 三、 全局拓扑链路与模块调用流向 (Global Topology & Cross-Layer Calls)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                    应用启动层 (Launchers)                                  │
│   main.py (环境自检/引导) ──► main_fluent.py (PyQt6 Fluent Design) ──► gemini-code (兼容层) │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │
                                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                               核心协调与编排层 (Orchestration)                             │
│                         gui_fluent/app_controller.py (AppController)                     │
│   ┌────────────────────────────────────────┼────────────────────────────────────────┐    │
│   ▼                                        ▼                                        ▼    │
│ [全局状态中枢]                      [业务管道流水线]                          [后台哨兵守护]  │
│ core/state_manager.py              gui_fluent/pipelines/                    services/    │
│ (StateManager 线程安全状态)        ├── auto_pipeline.py (全量大优选)       auto_heal_   │
│ core/signal_bus.py                 └── fav_pipeline.py  (优质复测留任)       watcher.py   │
│ (SignalBus 事件解耦总线)                                                    (秒级无感自愈)│
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │
                                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                 底层领域服务层 (Domain Services)                           │
│   services/clash_client.py         ─── Mihomo/Clash 核心 REST API (节点切换/延时/连接监控)     │
│   services/colo_service.py         ─── Cloudflare 物理机房嗅探、历史统计、防漂移与亚洲节点判定 │
│   services/script_generator.py     ─── Script.js 动态生成、物理端点拦截、规范更名、双引擎同步  │
│   services/subscription_service.py ─── 订阅 YAML 解析、物理端点去重提取、节点名称规范化对齐    │
│   services/pool_service.py         ─── 精选池、典藏池、黑名单多池聚合计算与配额分配算法       │
│   services/filter_service.py       ─── 抖动率过滤、健康度巡检、低速黑名单过滤                 │
│   services/probe_service.py        ─── HTTP 微探针、真实下行带宽测速引擎                     │
│   services/c_segment_miner.py      ─── C 段矿机嗅探器（同子网高频端口并发扫描发现潜伏端点）  │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │
                                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                配置、工具与外部内核交互层 (Infra)                          │
│   config/settings.py               ─── 路径定位、系统参数常量、深色主题、正则排除规则          │
│   config/config_manager.py         ─── node_assistant_config.json 原子保存与互斥锁安全读取    │
│   utils/win32_utils.py             ─── Win32 全局热键 Ctrl+Shift+F12 模拟、进程与注册表管理   │
│   外部系统对接                      ─── Mihomo Core (9097 API) & Clash Verge Rev (Script.js)  │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 四、 核心业务流水线运行闭环机制 (Four Execution Pipeline Lifecycles)

### 1. 全量大优选流水线 (AutoPipeline)
- **步骤 1（多源拉取与去重）**：从云端订阅 URL 或本地配置提取 YAML 原始节点列表，以 `IP:Port` 物理端点为核心键执行全量去重。
- **步骤 2（机房嗅探与防漂移）**：多线程并发请求 Trace 探针，解析真实机房三字码（HKG, NRT, SJC 等），比对 7 天机房历史漂移记录，过滤伪装或漂移节点。
- **步骤 3（真实带宽测速）**：使用 `ProbeService` 进行多段下行测速，计算真实 MB/s 吞吐，剔除低于阈值（如 5.0 MB/s）的劣质节点并记入测速黑名单。
- **步骤 4（规范冠名与入池）**：根据机房与带宽生成规范名（如 `香港 HKG 22.56 MB/s`），写入 `cloud_endpoints` 字典霸占命名权，沉淀入精选池。
- **步骤 5（双引擎热重载）**：生成包含 800+ 物理香港端点硬核拦截清单的 `Script.js`，原子覆盖 `clash-verge.yaml` 并通过 REST API 通知内核重载。

### 2. 优质复测留任流水线 (FavPipeline)
- **增量复测原则**：仅针对当前精选池 (`favorites`) 与典藏池 (`stars`) 进行健康巡检与速度复核。
- **淘汰与保底机制**：淘汰失活或下行突降节点；若达标节点不足，触发防雪崩保留机制，维持策略组基础可用性。
- **合规复检集成**：结合 Google 送中与 429 状态检查，对被污染节点执行打标与降级。

### 3. C 段矿机并发深挖流水线 (CSegmentMiner)
- **网段衍生算法**：提取已知优质端点所在的 `/24` C 段（如 `104.21.55.0/24`）。
- **多端口并发扫描**：并发探测常用安全端口（443, 8443, 2053, 2083, 2087, 2096），发现潜伏的高速干净 IP。
- **入池反哺**：经探针验证通过的新端点自动反哺至候选池。

### 4. 秒级无感自愈与合规隔离流水线 (AutoHealWatcher)
- **开机保护期 (Startup Grace Period)**：哨兵启动前 15 秒处于静默观测状态，等待系统网络堆栈与代理内核就绪，杜绝开机突发自愈。
- **旁路被动感知**：1.0s 间隔轮询 `/connections`，检测单向发包黑洞（`upload > 10KB` 且 `download == 0`）与软失速（60s 无任何流量增长）。
- **主动双向合规探针**：主动检测 Google 访问，捕获 HTTP 429、验证码（`sorry/index`）与重定向香港（`google.com.hk` 送中）。
- **12 小时冷冻隔离 (`google_hk_nodes`)**：被 Google 拦截或送中的节点被打上阻断标记，12 小时内严禁自愈再次切回。
- **500ms 二次复验防误切**：在执行节点切换前引入 500ms 重试确认，排除偶发网络突发延迟。
- **避让模式**：当检测到流水线正在执行优选测速时（`is_pipeline_running_fn()` 为 True），哨兵自动暂停节点切换，杜绝并发冲突。
- **显式原因通知**：自愈触发时在系统托盘 Toast 和控制台日志中明确标注具体触发原因（如 `触发原因：主动探针检测到Google被拦截/验证码/送中`）。

---

## 五、 状态与并发生命周期管控 (State & Concurrency Lifecycle & Locking Contracts)

### 1. StateManager 核心数据模型（全局唯一事实源）
- `favorites`: `set[str]` - 优质精选节点名称集合。
- `stars_nodes`: `list[dict]` - 典藏常青极品池清单。
- `all_nodes`: `list[str]` - 订阅中的物理端点去重全量节点名称列表。
- `node_details`: `dict[str, dict]` - 节点详情映射（包含 `server`, `port`, `type`, `uuid` 等原始物理参数）。
- `cloud_endpoints`: `dict[str, str]` - 物理端点 (`IP:Port`) -> 规范化名称（如 `"23.133.52.10:2053": "香港 HKG 22.56 MB/s"`），拥有全局最高命名霸占权。
- `node_colo`: `dict[str, str]` - 端点/节点 -> 物理机房代码（如 `"HKG"`, `"NRT"`）。
- `node_colo_history`: `dict[str, list]` - 7 天机房历史检测记录，用于长效防漂移。
- `local_blacklist` & `speed_blacklist`: `set[str]` - 延迟超标与下行低速黑名单集合。

### 2. 并发锁模型与快照分离黄金军规
系统涉及 GUI 主线程、Pipeline 工作线程 (QThread)、Sentinel 哨兵线程与定时调度线程等多线程并发。
1. **统一锁接口**：`StateManager` 暴露 `@property def lock(self): return self._global_lock`。所有模块统一使用 `with self.state.lock:`。
2. **锁内严禁阻塞 I/O**：绝对禁止在持有 `state.lock` 时调用网络请求（如测速、HTTP 请求、`time.sleep`）或弹出 GUI 阻塞对话框（`QMessageBox.exec()`）。
3. **快照分离模式 (Snapshot Pattern)**：
   ```python
   # 正确范式：锁内获取快照，锁外耗时操作，完成回写再短暂入锁
   with self.state.lock:
       fav_snapshot = set(self.state.favorites)
       details_snapshot = dict(self.state.node_details)
   
   results = perform_speed_tests(fav_snapshot, details_snapshot)
   
   with self.state.lock:
       self.state.favorites.update(results.qualified)
   ```
4. **协作式优雅终止 (Stop Event)**：严禁使用 `terminate()` 或系统级暴力杀线程。统一调用 `self.state.get_stop_event(name)` 获取 `threading.Event`，流水线内循环检测 `if stop_event.is_set(): break`。

---

## 六、 架构边界与不可违背的六大工程红线 (Architecture Red Lines & System Contracts)

- **红线 1（严格单向分层，严禁反向污染）**：
  `services` 和 `config` 属于纯粹的基础设施与算法层，**绝对严禁导入任何 GUI 模块**。基础模块必须能够在无任何 UI 的 Headless 环境下独立进行单元测试。
- **红线 2（View-Controller 严格隔离）**：
  所有界面层组件（`pages/`、`widgets/`、`components/`）只负责数据渲染与事件触发，**绝对严禁直接调用底层 `services` 或直接执行文件写盘**。所有业务操作必须通过委托 `self.controller.<method>()` 执行。
- **红线 3（物理机房级绝对防御契约）**：
  对非香港策略组（`⚡ 自动选择 (非香港)`）的过滤，**绝不允许仅依赖节点名称字符串正则**！必须将由 Python 端嗅探到的物理香港机房端点黑名单（`hkEndpoints`）注入脚本，在物理端点层实施一票否决。
- **红线 4（规范命名唯一霸占契约）**：
  由系统冠名并收录于 `cloud_endpoints` 的规范名称（如 `香港 HKG 22.56 MB/s`），在全局任何订阅解析（`load_nodes_from_profile`）与状态对齐（`reconcile_endpoints`）中**具备最高霸占优先级**，严禁逆向降级还原回机场原始未清洗的广告名称。
- **红线 5（严禁使用 Cloudflare 测速链接）**：
  严禁使用 Cloudflare 官方地址作为测速目标或探针，杜绝 Cloudflare IP 封禁与风控。
- **红线 6（协作式多线程优雅终止）**：
  严禁调用操作系统的强制终止或 Qt 的暴力 `terminate()`，必须使用 `threading.Event` 保证资源与套接字安全释放。

---

## 七、 关键技术攻坚与深度排雷纪要 (Comprehensive Bug Post-Mortems)

### 1. StateManager 缺少 lock 属性导致多线程崩溃闪退
- **事故现象**：在 Fluent 界面下启动大优选或复测时，程序瞬间闪退。
- **底层根因**：`StateManager` 私有锁命名为 `_global_lock`，但各模块广泛调用 `with self.state.lock:`，引发 `AttributeError: 'StateManager' object has no attribute 'lock'` 导致 Python 进程直接退出。
- **解决方案**：在 `core/state_manager.py` 中为 `StateManager` 添加 `@property def lock(self): return self._global_lock`，确保所有多线程上下文安全平滑受保护。

### 2. 香港节点因机场广告名伪装穿透「⚡ 自动选择 (非香港)」策略组
- **事故现象**：全量大优选后，非香港组首位赫然排着 `Mia优选 | 09-12 19:32 | BestCF.pages.dev`，物理机房实际为香港 HKG。
- **底层根因**：
  1. `Script.js` 中的 `isNonHongKongProxy` 纯粹依赖名称正则，而机场原始名字脱敏不带任何地区词，导致正则一票否决失效；
  2. 生成 `Script.js` 时未在 `config.proxies` 内存中覆盖 `p.name`；
  3. `reconcile_endpoints` 在对齐时把已命名的规范名反向还原为了原始怪名字。
- **解决方案**：
  1. **物理端点黑名单硬核拦截**：在 `services/script_generator.py` 中聚合已知香港端点注入 `hkEndpoints`（收录 800+ 端点），在 `isNonHongKongProxy` 中实施物理端点 `hkEndpoints.includes(ep)` 一票否决；
  2. **内存规范更名注入**：在 `Script.js` 步骤 0 中引入 `canonicalNameMap`，遍历 `config.proxies` 时自动将其覆盖更名为规范名称；
  3. **消除反向降级**：修复 `reconcile_endpoints`，锁定 `cloud_endpoints` 规范命名最高霸权。

### 3. YouTube Shorts 播放中途短暂断流转圈（DNS Fake-IP 与流媒体加固）
- **事故现象**：播放 YouTube 视频时前几秒秒开，随后第 10 秒发生卡顿转圈才继续复播。
- **底层根因**：Clash Verge 的 DNS 缺少 `enhanced-mode: fake-ip`，且 `fallback-filter` 缺少 `googlevideo.com` 等流媒体 CDN 域名，导致国内公共 DNS 解析分片域名时遭受 GFW 投毒返回 Facebook 虚假 IP（HTTP 404），引发播放器卡顿重试。
- **解决方案**：在 `services/script_generator.py` 的脚本模板与 `sync_runtime_clash_yaml_and_reload` 中固化 `enhanced-mode: fake-ip` 与完整流媒体白名单，实现 0 毫秒虚拟 IP 极速下发，彻底免疫 DNS 污染。

### 4. 开机初始化阶段突发假死误触自愈与优雅启动保护期
- **事故现象**：开机冷启动节点助手后，连续发生多次自愈切换，引发网络瞬时震荡。
- **底层根因**：Windows 开机后，系统网络堆栈、VPN TUN 适配器与 Mihomo 内核尚未完全建立套接字路由表。哨兵过早扫描连接，将刚发起的 TCP Handshake 识别为发包黑洞。
- **解决方案**：
  1. 引入 15 秒优雅启动保护期（`startup_grace_period = 15.0`），启动阶段仅观察不切换；
  2. 引入 500ms 二次重试复验（`_async_heal_worker`），确认断流持续才执行动作；
  3. 流水线避让模式：若后台正在执行优选测速，自动抑制哨兵切换动作，防止线程打架。

### 5. 谷歌 429 验证码/人机拦截与香港送中阻断
- **事故现象**：打开网页 Google/YouTube/IG 突然全部打不开，自愈不断发生甚至切入不可用节点。
- **底层根因**：部分被污染的节点受到 Google 严格风控，返回 HTTP 429 Too Many Requests 或重定向至 `sorry/index` 人机验证码页面；或者节点将 Google 重定向至 `google.com.hk`（送中）。旧代码吞没了 HTTP 异常，且切换节点时可能再次随机切中被污染节点。
- **解决方案**：
  1. 在 `AutoHealWatcher` 中增加 `_inspect_google_node_compliance()` 双向主动探针；
  2. 捕获 `urllib.error.HTTPError`（429）与人机验证重定向；
  3. 建立 12 小时冷冻隔离池 `google_hk_nodes`，一旦捕获异常，将该节点打标并隔离 12 小时，严禁自愈切换重新命中；
  4. 同步加固 `fav_pipeline.py` 与 `page_favorites.py` 的合规探针异常捕获。

### 6. 开机冷启动 Clash 客户端崩溃消失排查
- **事故现象**：开机后某次自愈后，用户发现任务栏中的 Clash Verge Rev 客户端不见了，客户端闪退。
- **底层根因**：经查验系统事件日志与崩溃日志，Windows 冷启动时期磁盘虚拟内存换页（In-Page I/O）发生 `0xc000001d` 非法指令/分页冲突，或者 Clash 内核在处理极端突发批量连接 reset 时遭遇系统级资源回收。
- **解决方案**：为外部 REST API 调用增加超时安全兜底与进程活性探活，在 Python 自愈逻辑中消除任何破坏性进程调用，并在断流时采用温柔的连接重置策略。

### 7. 界面参数自动存盘与二开复水
- **事故现象**：用户在 Fluent 界面上微调了并发线程数、测速超时、速度阈值等参数后，一旦重启应用，配置全部回退为默认值。
- **底层根因**：各页面控件缺少针对值的变动监听器（`valueChanged` / `toggled`），未联动持久化服务。
- **解决方案**：建立统一的响应式持久化监听体系，所有 SpinBox、Slider、Switch 发生变动时立即异步同步回写 `config_manager.save_config()`，二开启动时自动复水（Hydration），实现零配置丢失。

### 8. 自愈通知可观测性增强
- **事故现象**：用户只能看到“自愈成功”提示，无法得知到底是因为单向发包黑洞、60s 软失速还是 Google 429 拦截触发的。
- **解决方案**：`AutoHealWatcher` 传递显式触发原因字符串（如 `触发原因：主动探针检测到Google被拦截/验证码/送中`、`触发原因：检测到 1 条单向发包黑洞死连接`），通过 `SignalBus.auto_heal_triggered` 实时推送到 Windows 系统托盘气泡（Toast）与 UI 控制台日志面板。

---

## 八、 全局源码全量打包索引 (Source Manifest)

以下为当前代码库中所有有效源码文件的完整内容（未做任何截断与省略），供全局审阅与深度代码级追踪：

"""

def pack_repo():
    output_file = 'repo_context.md'
    
    print("Generating dynamic ASCII directory tree...")
    tree_lines = generate_directory_tree('.')
    tree_text = '\n'.join(tree_lines)
    
    god_view_content = GOD_VIEW_MAP_TEMPLATE.format(DIRECTORY_TREE=tree_text)
    
    print("Packing repository with God-View Architecture Map into repo_context.md...")
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # 写入上帝视角大地图
        out_f.write(god_view_content)
        out_f.write("\n\n")
        
        file_count = 0
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d))]
            
            for file in sorted(files):
                file_path = os.path.join(root, file)
                if is_ignored(file_path):
                    continue
                    
                display_path = os.path.normpath(file_path).replace(os.sep, '/')
                if display_path.startswith('./'):
                    display_path = display_path[2:]
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as in_f:
                        content = in_f.read()
                        
                    out_f.write(f"## File: `{display_path}`\n\n")
                    
                    ext = os.path.splitext(file)[1].lower()
                    lang = ext[1:] if ext else 'text'
                    if lang == 'py': 
                        lang = 'python'
                    elif lang == 'md': 
                        lang = 'markdown'
                    elif lang == 'js':
                        lang = 'javascript'
                    elif lang == 'json':
                        lang = 'json'
                    elif lang == 'yaml' or lang == 'yml':
                        lang = 'yaml'
                    
                    out_f.write(f"```{lang}\n")
                    out_f.write(content)
                    if content and not content.endswith('\n'):
                        out_f.write('\n')
                    out_f.write("```\n\n")
                    file_count += 1
                except Exception as e:
                    out_f.write(f"## File: `{display_path}`\n\n")
                    out_f.write(f"> Error reading file: {str(e)}\n\n")
                    file_count += 1

    print(f"Done! {file_count} files successfully packed into repo_context.md with complete God-View Architecture Map.")

if __name__ == '__main__':
    pack_repo()
