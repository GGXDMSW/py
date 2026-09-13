# 🌌 反重力平台 py 项目「绝对上帝视角」架构总图 (God-View Architecture Map)

> **致下一任 AI 架构师 / 核心开发者**：
> 本文件是本项目的最高级别系统全景认知枢纽与全量源码大地图。
> 无论你是接手重构、排查疑难故障，还是新增扩展业务，请务必优先精读本文档。
> 本文档赋予你对整个代码库拓扑链路、并发锁分布、状态唯一事实源生命周期、双引擎内核热更、物理机房与送中合规判定机制、历史排雷纪要以及全量无遗漏源码的 **100% 绝对上帝视角**。阅读完毕后即可达到零认知损耗接手、精准决策与系统级架构治理。

---

## 一、 项目定位与全景蓝图 (System Mission & Architectural Overview)

本系统是一套专为 **Clash Verge Rev** 量身打造的高性能、自动化节点优选、全链路状态守护与秒级无感自愈中枢。整体遵循 **分层解耦、单向依赖、Controller中枢编排、双引擎热重载** 的企业级工程架构。

### 核心能力矩阵：
1. **真实下行带宽多线程并发压测**：基于微探针与真实测速文件分段下载（严禁使用 Cloudflare 链接，统一使用 Google 官方分发包），摒弃虚假 ICMP/TCP Ping 延迟，测定真实网络吞吐能力（MB/s）。
2. **Cloudflare 物理机房嗅探与防漂移**：并发嗅探端点真实机房（如 HKG、NRT、SIN、SJC），记录 7 天历史记录，精准剔除跨境漂移节点，确保落地合规。
3. **物理端点去重与全生命周期规范更名**：以 `IP:Port` 物理端点为核心键，对混乱的机场营销名称进行清洗，永久固化统一命名（如 `香港 HKG 22.56 MB/s`）。
4. **秒级无感断流自愈守护 (AutoHealWatcher)**：后台 1.0s 旁路轮询连接表，毫秒级发现单向发包黑洞（tx>0, rx==0）与软失速，自动顺位无感切换节点并熔断坏死连接。
5. **Google 429 验证码/人机拦截与香港送中主动合规探针**：双重检测 Google 阻断状态与送中重定向，阻断节点触发 12 小时冷冻隔离，彻底杜绝 Google/YouTube/IG 突发打不开。
6. **双引擎内核热重载 (Dual-Engine Hot-Reload)**：融合 `Script.js` 扩展脚本注入与运行时配置原子写盘 + REST API 重载通知，彻底攻克快捷键失效与配置穿透故障。

### 三大多维启动入口定位：
- **`main_fluent.py`（主流现代入口）**：基于 PyQt6 + PyQt-Fluent-Widgets 现代桌面框架，构建 `MainWindow` 并挂载 `AppController` 协调器、`SignalBus` 总线与全套 Fluent 交互体验。
- **`main.py`（经典原生入口）**：基于 Python 原生 `tkinter` 框架构建，调用 `gui/app.py` 中的 `ClashVergeTabsManager`，为轻量免 Qt 依赖环境提供基础运行支持。
- **`gemini-code-1788793285196.py`（历史兼容代理）**：为早期桌面快捷方式与历史脚本提供平滑兼容层，实际透明转发至 `main.py`。

---

## 二、 全局代码库文件树状结构 (Directory Tree & Component Manifest)

以下为当前项目的完整目录与源文件全景树状图（所有有效模块 100% 无遗漏呈现）：

```
py/
├── .gitignore  # Git 版本控制忽略配置文件
├── AGENTS.md  # 全局规则定义与 Bark 自动化通知指令
├── auto_packer.py  # 全局大地图与源码打包发布器（生成 repo_context.md）
├── config/  # 全局静态配置与持久化管理器 (Settings & ConfigManager)
│   ├── __init__.py  # 配置模块包声明
│   ├── config_manager.py  # node_assistant_config.json 线程安全持久化读写与原子写盘
│   └── settings.py  # 全局静态配置、默认参数、主题样式、测速常量与正则排除规则
├── core/  # 全局核心状态机与跨线程事件总线 (StateManager & SignalBus)
│   ├── __init__.py  # 核心状态与事件包声明
│   ├── signal_bus.py  # PyQt6 SignalBus 全局事件解耦总线（跨线程 UI 信号传递）
│   └── state_manager.py  # StateManager 全局线程安全事实源（唯一状态中枢与并发互斥锁管理）
├── gemini-code-1788793285196.py  # 单文件历史兼容启动代理层（无缝转发调用 main.py）
├── gui/  # [经典兼容] 原生 Tkinter 经典版多标签页管理界面 (历史单体工程全量归档)
│   ├── __init__.py  # 经典版 Tkinter 界面包声明
│   └── app.py  # 经典版 ClashVergeTabsManager 6500+行全功能单体界面与历史算法全量实现
├── gui_fluent/  # 现代 Fluent Design 风格桌面 UI 前端体系
│   ├── __init__.py  # Fluent 界面包声明
│   ├── app_controller.py  # AppController 核心调度协调器（业务中枢、状态机流转、流水线与哨兵生命周期管理）
│   ├── components/  # UI 结构性卡片与基础组件 (TopBar, BottomBar, LogPanel, etc.)
│   │   ├── __init__.py  # UI 组件包声明
│   │   ├── bottom_action_bar.py  # 底部快捷状态栏与启停联动按钮栏
│   │   ├── log_panel.py  # 终端式实时动态日志高亮输出控制面板
│   │   ├── pipeline_card.py  # 管道执行卡片与进度状态展示容器
│   │   └── top_bar.py  # 顶部全局统计状态栏（节点数、自愈次数、延迟概览）
│   ├── main_window.py  # MainWindow 主窗口框架（Fluent 侧边导航栏、托盘气泡提示、日志与页签装配）
│   ├── pages/  # 各功能业务独立子页面 (Active, Favorites, Stars, Blacklists, etc.)
│   │   ├── __init__.py  # 业务页面包声明
│   │   ├── page_active.py  # 当前活跃节点监控与实时连接状态展示页
│   │   ├── page_cloud_text.py  # 云端订阅与直连文本批量导入/同步管理页
│   │   ├── page_delay_black.py  # 延迟超标与高抖动黑名单管理页
│   │   ├── page_favorites.py  # 精选池管理页（包含一键检测当前目录送中状态、增量优选、手动自愈等）
│   │   ├── page_speed_black.py  # 测速低速淘汰黑名单管理页
│   │   ├── page_stars.py  # 典藏常青极品池管理与权重配置页
│   │   └── page_verified.py  # 候选已验证节点全量列表页
│   ├── pipelines/  # UI 绑定的前台异步长任务工作流 (AutoPipeline, FavPipeline)
│   │   ├── __init__.py  # Fluent 管道包声明
│   │   ├── auto_pipeline.py  # AutoPipeline 全量大优选异步管道（多线程测速、机房探测、更名入池）
│   │   └── fav_pipeline.py  # FavPipeline 优质复测留任异步管道（增量测活、淘汰劣质、双引擎热更）
│   └── widgets/  # 高级复合数据表格与交互式对话框组件
│       ├── __init__.py  # 复合控件包声明
│       ├── c_miner_dialog.py  # C 段矿机弹窗界面（设置扫描参数、启动并发探测并实时呈现扫描结果）
│       ├── node_table.py  # 通用节点数据表格控件（支持排序、筛选、批量操作与状态高亮）
│       ├── stars_table.py  # 典藏节点专用维护表格控件
│       └── verified_table.py  # 已验证节点维护表格控件
├── main.py  # 经典版 GUI 原生 Tkinter 启动入口（构建并运行 ClashVergeTabsManager）
├── main_fluent.py  # 现代 PyQt6 Fluent Design 桌面应用主流启动入口（构建并运行 MainWindow）
├── pipelines/  # 后台核心任务执行管线与定时自动优选调度器
│   ├── __init__.py  # 管道基类包声明
│   ├── base_pipeline.py  # 抽象管道基类（定义生命周期钩子、进度计算与安全取消机制）
│   └── scheduler.py  # 后台定时任务调度器（定时自动触发全量大优选与精选复测）
├── services/  # 底层领域算法服务 (ClashClient, Probe, Colo, Pool, ScriptGenerator, etc.)
│   ├── __init__.py  # 领域服务包声明
│   ├── auto_heal_watcher.py  # AutoHealWatcher 秒级无感自愈哨兵（单向发包黑洞感知、Google 429/HK 合规探针、12h 隔离冷冻、15s 开机保护）
│   ├── c_segment_miner.py  # CSegmentMiner C 段矿机并发嗅探服务（高频端口扫描与存活发现）
│   ├── clash_client.py  # ClashClient Mihomo/Clash Verge REST API 交互客户端（节点切换、延时测试、连接清理）
│   ├── colo_service.py  # ColoService Cloudflare 物理机房嗅探与 7 天防漂移算法
│   ├── filter_service.py  # FilterService 节点抖动过滤、超时判定与低速黑名单服务
│   ├── pool_service.py  # PoolService 多池聚合计算服务（精选、典藏、黑名单配额与分组编排）
│   ├── probe_service.py  # ProbeService HTTP 微探针与分段下行真实带宽测速引擎
│   ├── script_generator.py  # ScriptGenerator Script.js 扩展脚本动态渲染引擎与双引擎热重载
│   └── subscription_service.py  # SubscriptionService 订阅拉取、物理端点提取去重与规范命名对齐
├── temp_runner.js  # 历史 Script.js 脚本测试运行样本
├── utils/  # 系统级 Win32 与底层通用支撑工具集
│   ├── __init__.py  # 工具库包声明
│   └── win32_utils.py  # Windows Win32 API 辅助工具（快捷键模拟、注册表/端口探测、进程状态监控）
└── 代码审查报告.md  # 系统工程代码审查与重构规划报告
```

---

## 三、 全局拓扑链路与模块调用流向 (Global Topology & Cross-Layer Calls)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                    应用启动层 (Launchers)                                  │
│   [主流现代入口] main_fluent.py ──► MainWindow (Fluent Design UI) ──► AppController      │
│   [经典原生入口] main.py        ──► ClashVergeTabsManager (Tkinter UI) ──► (gui/app.py)   │
│   [向后兼容入口] gemini-code... ──► 历史脚本与桌面快捷方式无缝代理 ──► 转发至 main.py    │
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
- **步骤 3（真实带宽测速）**：使用 `ProbeService` 进行多段下行测速，计算真实 MB/s 吞吐，剔除低于阈值（如 5.0 MB/s）的劣质节点并记入测速黑名单。严禁使用 Cloudflare 测速源，全面采用 Google 官方分发测速包。
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



## File: `.gitignore`

```text
__pycache__/
*.py[cod]
*$py.class
*.log
scratch/
```

## File: `AGENTS.md`

```markdown
# Bark 自动通知规则

每当当前任务完全结束、遇到报错中断、或者需要用户的输入/权限选择时，请立刻在后台静默运行以下 curl 命令发送 Bark 通知：
curl.exe --noproxy "*" -s "https://api.day.app/LRsc3PP2H5hkrBcBoxssd7/Antigravity%E9%80%9A%E7%9F%A5/%E4%BB%BB%E5%8A%A1%E7%8A%B6%E6%80%81%E5%B7%B2%E6%9B%B4%E6%96%B0%EF%BC%8C%E8%AF%B7%E5%9B%9EIDE%E5%A4%84%E7%90%86"
```

## File: `auto_packer.py`

```python
import os

def is_ignored(path):
    # 忽略非工程源码目录
    ignored_dirs = {'.git', '__pycache__', '.idea', '.vscode', 'venv', 'env', 'node_modules', 'dist', 'build', 'scratch'}
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
    'gui': '[经典兼容] 原生 Tkinter 经典版多标签页管理界面 (历史单体工程全量归档)',
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
    '.gitignore': 'Git 版本控制忽略配置文件',
    'AGENTS.md': '全局规则定义与 Bark 自动化通知指令',
    'auto_packer.py': '全局大地图与源码打包发布器（生成 repo_context.md）',
    'gemini-code-1788793285196.py': '单文件历史兼容启动代理层（无缝转发调用 main.py）',
    'main.py': '经典版 GUI 原生 Tkinter 启动入口（构建并运行 ClashVergeTabsManager）',
    'main_fluent.py': '现代 PyQt6 Fluent Design 桌面应用主流启动入口（构建并运行 MainWindow）',
    'temp_runner.js': '历史 Script.js 脚本测试运行样本',
    '代码审查报告.md': '系统工程代码审查与重构规划报告',
    'gui/__init__.py': '经典版 Tkinter 界面包声明',
    'gui/app.py': '经典版 ClashVergeTabsManager 6500+行全功能单体界面与历史算法全量实现',
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
1. **真实下行带宽多线程并发压测**：基于微探针与真实测速文件分段下载（严禁使用 Cloudflare 链接，统一使用 Google 官方分发包），摒弃虚假 ICMP/TCP Ping 延迟，测定真实网络吞吐能力（MB/s）。
2. **Cloudflare 物理机房嗅探与防漂移**：并发嗅探端点真实机房（如 HKG、NRT、SIN、SJC），记录 7 天历史记录，精准剔除跨境漂移节点，确保落地合规。
3. **物理端点去重与全生命周期规范更名**：以 `IP:Port` 物理端点为核心键，对混乱的机场营销名称进行清洗，永久固化统一命名（如 `香港 HKG 22.56 MB/s`）。
4. **秒级无感断流自愈守护 (AutoHealWatcher)**：后台 1.0s 旁路轮询连接表，毫秒级发现单向发包黑洞（tx>0, rx==0）与软失速，自动顺位无感切换节点并熔断坏死连接。
5. **Google 429 验证码/人机拦截与香港送中主动合规探针**：双重检测 Google 阻断状态与送中重定向，阻断节点触发 12 小时冷冻隔离，彻底杜绝 Google/YouTube/IG 突发打不开。
6. **双引擎内核热重载 (Dual-Engine Hot-Reload)**：融合 `Script.js` 扩展脚本注入与运行时配置原子写盘 + REST API 重载通知，彻底攻克快捷键失效与配置穿透故障。

### 三大多维启动入口定位：
- **`main_fluent.py`（主流现代入口）**：基于 PyQt6 + PyQt-Fluent-Widgets 现代桌面框架，构建 `MainWindow` 并挂载 `AppController` 协调器、`SignalBus` 总线与全套 Fluent 交互体验。
- **`main.py`（经典原生入口）**：基于 Python 原生 `tkinter` 框架构建，调用 `gui/app.py` 中的 `ClashVergeTabsManager`，为轻量免 Qt 依赖环境提供基础运行支持。
- **`gemini-code-1788793285196.py`（历史兼容代理）**：为早期桌面快捷方式与历史脚本提供平滑兼容层，实际透明转发至 `main.py`。

---

## 二、 全局代码库文件树状结构 (Directory Tree & Component Manifest)

以下为当前项目的完整目录与源文件全景树状图（所有有效模块 100% 无遗漏呈现）：

```
py/
{DIRECTORY_TREE}
```

---

## 三、 全局拓扑链路与模块调用流向 (Global Topology & Cross-Layer Calls)

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                    应用启动层 (Launchers)                                  │
│   [主流现代入口] main_fluent.py ──► MainWindow (Fluent Design UI) ──► AppController      │
│   [经典原生入口] main.py        ──► ClashVergeTabsManager (Tkinter UI) ──► (gui/app.py)   │
│   [向后兼容入口] gemini-code... ──► 历史脚本与桌面快捷方式无缝代理 ──► 转发至 main.py    │
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
- **步骤 3（真实带宽测速）**：使用 `ProbeService` 进行多段下行测速，计算真实 MB/s 吞吐，剔除低于阈值（如 5.0 MB/s）的劣质节点并记入测速黑名单。严禁使用 Cloudflare 测速源，全面采用 Google 官方分发测速包。
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
                    elif lang == 'gitignore':
                        lang = 'gitignore'
                    
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
```

## File: `gemini-code-1788793285196.py`

```python
"""
Clash Verge 节点管理助手 (7天Colo长效防漂移与C段挖掘版)
========================================================================
【向后兼容代理入口】
为了确保现有桌面快捷方式、自动化批处理脚本以及用户的双击启动习惯绝对不受影响，
保留此文件作为无缝转发层，实际功能已模块化解耦至 config/、core/、services/、pipelines/、gui/。

推荐的标准主程序入口为: main.py
========================================================================
"""
import sys

from config.settings import (
    BASE_DIR,
    PARENT_DIR,
    DEFAULT_SCRIPT_JS,
    CONFIG_STORAGE_PATH,
    RUN_REG_KEY,
    REG_APP_NAME,
    THEME,
    EXCLUDE_HK_REGEX,
    NON_ASIA_CN_KEYWORDS,
    NON_ASIA_CODE_SET,
    ASIA_CN_KEYWORDS,
    ASIA_CODE_SET,
    COLO_NAME_MAP,
    COLO_REGIONS,
    COUNTRY_NAME_MAP,
)
from config.config_manager import (
    atomic_save_config,
    safe_load_config,
    prune_expired_history,
)
from core.state_manager import StateManager
from services.probe_service import (
    get_ip_location_fallback,
    get_cf_colo_raw,
    tcp_ping,
    get_c_segment_ips,
    detect_node_region,
    measure_http_download_speed,
)
from services.clash_client import ClashClient, ClashModeGuard
from services.subscription_service import (
    extract_nodes_and_details_from_file,
    choose_canonical_node_name,
    get_node_endpoint,
    resolve_node_to_current,
    update_remote_subscription,
)
from services.colo_service import (
    get_colo_region,
    record_colo_sample,
    analyze_colo_stats,
    is_node_hongkong,
    is_asian_node,
)
from services.filter_service import (
    compute_delay_stats,
    check_node_jitter_blacklisted,
    auto_filter_and_blacklist_non_asia_nodes,
)
from services.pool_service import (
    get_pool_endpoint_sets,
    deduplicate_favorites_by_endpoint,
    align_favorites_with_current_subscription,
    clean_offline_favorites,
    process_verified_lifecycle,
    purge_invalid_and_blacklisted_from_all_pools,
)
from services.script_generator import build_script_js, write_script_js
from pipelines.scheduler import SchedulerDaemon
from pipelines.base_pipeline import BasePipeline
from utils.win32_utils import (
    send_system_notification,
    is_run_as_admin,
    trigger_verge_reactivate_hotkey,
    create_tray_icon_image,
    check_boot_startup_registry,
    set_boot_startup_registry,
    create_modern_btn,
)
from gui.app import ClashVergeTabsManager
from main import run_app

if __name__ == "__main__":
    run_app()
```

## File: `main.py`

```python
"""
Clash Verge 节点管理助手 (7天Colo长效防漂移与C段挖掘版)
规范化工程主启动入口
"""
import os
import sys
import tkinter as tk
import traceback
from tkinter import messagebox

from gui.app import ClashVergeTabsManager


def run_app(argv=None):
    """
    主程序启动器：
    处理命令行参数 (--tray 托盘静默启动)、构建主窗口与全局崩溃日志追踪
    """
    if argv is None:
        argv = sys.argv

    try:
        root = tk.Tk()
        app = ClashVergeTabsManager(root)
        if "--tray" in argv:
            root.withdraw()
        root.mainloop()
    except Exception:
        err_msg = traceback.format_exc()
        try:
            with open("error_startup.log", "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        try:
            messagebox.showerror("启动异常", f"程序启动失败：\n{err_msg}")
        except Exception:
            print(f"启动异常：\n{err_msg}")


if __name__ == "__main__":
    run_app()
```

## File: `main_fluent.py`

```python
import sys
import traceback

def global_exception_handler(exc_type, exc_value, exc_traceback):
    with open("crash_log.txt", "w", encoding="utf-8") as f:
        f.write("=== 软件闪退错误日志 ===\n")
        traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

sys.excepthook = global_exception_handler

"""
Clash Verge 节点管理助手 (Fluent 版)
规范化主启动入口
"""
import os

# 优先导入 qfluentwidgets 以确定加载的 Qt 运行时绑定 (PyQt5 或 PyQt6)
import qfluentwidgets

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QMessageBox
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QMessageBox

from gui_fluent.main_window import MainWindow


def run_fluent_app():
    """
    启动 Fluent UI 主程序
    """
    try:
        # 高分屏清晰渲染适配 (Win11)
        if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
            QApplication.setHighDpiScaleFactorRoundingPolicy(
                Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
            )

        if hasattr(Qt, "AA_EnableHighDpiScaling"):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, "AA_UseHighDpiPixmaps"):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setApplicationName("ClashVergeAssistantFluent")

        window = MainWindow()
        window.show()

        sys.exit(app.exec_() if hasattr(app, "exec_") else app.exec())
    except Exception:
        err_msg = traceback.format_exc()
        try:
            with open("error_fluent_startup.log", "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
        try:
            QMessageBox.critical(None, "启动异常", f"Fluent 版程序启动失败：\n{err_msg}")
        except Exception:
            print(f"Fluent 版程序启动失败：\n{err_msg}")


if __name__ == "__main__":
    run_fluent_app()
```

## File: `temp_runner.js`

```javascript

function main(config) {
  // ================= 策略组参数定义 =================
  const groupInterval = 300;
  const groupTolerance = 20;
  const starsGroupInterval = 300;
  const starsGroupTolerance = 20;

  const autoGroupName = '⚡ 自动选择';
  const autoGroupNoHkName = '⚡ 自动选择 (非香港)';
  const autoGroupStarsName = '⚡ 自动选择 (典藏)';

  // 优选节点特征识别清单 (全维度覆盖名称、IP:端口、纯IP，共 865 个)
  const premiumTokens = [
    "S5公益优选 | 小日本儿 | JP | 167.179.115.135:443",
    "167.179.115.135:443",
    "167.179.115.135",
    "辣子鸡优选 | 小日本儿 JP | 45.202.245.178:443",
    "45.202.245.178:443",
    "45.202.245.178",
    "辣子鸡优选 | 中国香港 HK | 64.90.28.28:443",
    "64.90.28.28:443",
    "64.90.28.28",
    "辣子鸡优选 | 美国 US | 45.202.240.107:443",
    "45.202.240.107:443",
    "45.202.240.107",
    "S5公益优选 | 印加坡县 | SG | 206.189.82.100:443",
    "206.189.82.100:443",
    "206.189.82.100",
    "辣子鸡优选 | 小日本儿 JP | 198.176.52.216:27001",
    "198.176.52.216:27001",
    "198.176.52.216",
    "辣子鸡优选 | 小日本儿 JP | 154.83.94.190:443",
    "154.83.94.190:443",
    "154.83.94.190",
    "S5公益优选 | 印加坡县 | SG | 152.42.232.41:443",
    "152.42.232.41:443",
    "152.42.232.41",
    "辣子鸡优选 | 中国香港 HK | 141.11.91.164:443",
    "141.11.91.164:443",
    "141.11.91.164",
    "S5公益优选 | 印加坡县 | SG | 152.42.235.119:443",
    "152.42.235.119:443",
    "152.42.235.119",
    "天诚优选1 | 战争贩子 | US | 166.62.104.98:2096",
    "166.62.104.98:2096",
    "166.62.104.98",
    "东京 NRT 10.55 MB/s",
    "172.64.229.75:443",
    "172.64.229.75",
    "麒麟优选 | 多线 | 104.18.42.108 | 69.29ms | 14.26mb/s",
    "104.18.42.108:443",
    "104.18.42.108",
    "MY 0.00 MB/s",
    "辣子鸡优选 | 中国台湾 TW | 83.147.13.49:443",
    "83.147.13.49:443",
    "83.147.13.49",
    "Mia优选 | 韩国 KR | 43.155.221.27:8443",
    "43.155.221.27:8443",
    "43.155.221.27",
    "- 0.00 MB/s",
    "202.144.195.86:443",
    "202.144.195.86",
    "Mia优选 | 印尼 ID | 43.229.254.71:443",
    "43.229.254.71:443",
    "43.229.254.71",
    "辣子鸡优选 | 小日本儿 JP | 154.83.95.6:443",
    "154.83.95.6:443",
    "154.83.95.6",
    "天诚优选1 | 小日本儿 | JP | 140.238.50.134:443",
    "140.238.50.134:443",
    "140.238.50.134",
    "天诚优选1 | 泡菜欧巴 | KR | 14.52.210.173:12312",
    "14.52.210.173:12312",
    "14.52.210.173",
    "东京 NRT 11.18 MB/s",
    "172.64.229.74:443",
    "172.64.229.74",
    "辣子鸡优选 | 中国香港 HK | 154.83.87.166:443",
    "154.83.87.166:443",
    "154.83.87.166",
    "KR [优选高速 173.72ms]",
    "43.200.87.5:443",
    "43.200.87.5",
    "东京 NRT 11.91 MB/s",
    "172.64.229.53:443",
    "172.64.229.53",
    "辣子鸡优选 | 小日本儿 JP | 156.246.92.90:443",
    "156.246.92.90:443",
    "156.246.92.90",
    "Mia优选 | 越南 VN | 160.25.75.40:443",
    "160.25.75.40:443",
    "160.25.75.40",
    "天诚优选1 | 战争贩子 | US | 199.119.137.109:2053",
    "199.119.137.109:2053",
    "199.119.137.109",
    "优质节点 0.00 MB/s 14",
    "43.159.12.233:443",
    "43.159.12.233",
    "东京 NRT 10.97 MB/s 2",
    "172.64.229.14:443",
    "172.64.229.14",
    "东京 NRT 11.16 MB/s",
    "172.64.229.11:443",
    "172.64.229.11",
    "麒麟优选 | 电信 | 172.64.157.148 | 43.16ms | 69.14mb/s",
    "172.64.157.148:443",
    "172.64.157.148",
    "优质节点 0.00 MB/s 7",
    "43.159.12.75:443",
    "43.159.12.75",
    "辣子鸡优选 | 小日本儿 JP | 45.202.245.7:443",
    "45.202.245.7:443",
    "45.202.245.7",
    "辣子鸡优选 | 新加坡 SG | 185.81.28.7:443",
    "185.81.28.7:443",
    "185.81.28.7",
    "微测优选 | 联通 | LAX | 104.17.191.7",
    "104.17.191.7:443",
    "104.17.191.7",
    "Gslege优选 | sg 【新加坡】 SG | 162.159.0.7",
    "162.159.0.7:443",
    "162.159.0.7",
    "Gslege优选 | sg 【新加坡】 SG | 108.162.192.7",
    "108.162.192.7:443",
    "108.162.192.7",
    "Gslege优选 | sg 【新加坡】 SG | 172.64.32.7",
    "172.64.32.7:443",
    "172.64.32.7",
    "vvHan优选 | 联通 | LAX | 104.17.191.7",
    "东京 NRT 10.99 MB/s",
    "172.64.229.7:443",
    "172.64.229.7",
    "辣子鸡优选 | 美国 US | 45.202.240.132:443",
    "45.202.240.132:443",
    "45.202.240.132",
    "辣子鸡优选 | 小日本儿 JP | 45.192.206.184:443",
    "45.192.206.184:443",
    "45.192.206.184",
    "Mia优选 | 马来西亚 MY | 168.93.198.146:8443",
    "168.93.198.146:8443",
    "168.93.198.146",
    "Mia优选 | 新加坡 SG | 43.160.203.174:443",
    "43.160.203.174:443",
    "43.160.203.174",
    "辣子鸡优选 | 中国香港 HK | 43.159.12.36:443",
    "43.159.12.36:443",
    "43.159.12.36",
    "辣子鸡优选 | 中国香港 HK | 154.16.10.93:443",
    "154.16.10.93:443",
    "154.16.10.93",
    "辣子鸡优选 | 美国 US | 216.23.123.64:30718",
    "216.23.123.64:30718",
    "216.23.123.64",
    "东京 NRT 10.87 MB/s 2",
    "172.64.229.24:443",
    "172.64.229.24",
    "S5公益优选 | 港岛茶记 | HK | 23.175.201.2:8443",
    "23.175.201.2:8443",
    "23.175.201.2",
    "Gslege优选 | sg 【新加坡】 SG | 172.64.32.2",
    "172.64.32.2:443",
    "172.64.32.2",
    "东京 NRT 11.40 MB/s",
    "172.64.229.2:443",
    "172.64.229.2",
    "优质节点 0.00 MB/s 25",
    "43.159.12.2:443",
    "43.159.12.2",
    "天诚优选1 | 战争贩子 | US | 77.110.114.56:443",
    "77.110.114.56:443",
    "77.110.114.56",
    "优质节点 0.00 MB/s 28",
    "43.159.12.204:443",
    "43.159.12.204",
    "东京 NRT 11.81 MB/s 2",
    "172.64.229.28:443",
    "172.64.229.28",
    "辣子鸡优选 | 中国香港 HK | 141.11.149.78:443",
    "141.11.149.78:443",
    "141.11.149.78",
    "香港 HKG 33.44 MB/s",
    "辣子鸡优选 | 小日本儿 JP | 23.249.25.142:21074",
    "23.249.25.142:21074",
    "23.249.25.142",
    "S5公益优选 | 印加坡县 | SG | 139.59.115.38:443",
    "139.59.115.38:443",
    "139.59.115.38",
    "S5公益优选 | 印加坡县 | SG | 47.82.155.79:8443",
    "47.82.155.79:8443",
    "47.82.155.79",
    "HK [优选高速 47.45ms]",
    "43.168.16.112:443",
    "43.168.16.112",
    "TW [高速 by Jz 24M]",
    "211.72.147.91:443",
    "211.72.147.91",
    "东京 NRT 10.77 MB/s",
    "172.64.229.42:443",
    "172.64.229.42",
    "Mia优选 | 韩国 KR | 43.155.202.169:443",
    "43.155.202.169:443",
    "43.155.202.169",
    "天诚优选1 | 印加坡县 | SG | 27.50.48.59:2096",
    "27.50.48.59:2096",
    "27.50.48.59",
    "辣子鸡优选 | 小日本儿 JP | 45.192.206.51:443",
    "45.192.206.51:443",
    "45.192.206.51",
    "东京 NRT 0.00 MB/s",
    "172.64.229.63:443",
    "172.64.229.63",
    "辣子鸡优选 | 中国澳门 MO | 45.202.247.152:443",
    "45.202.247.152:443",
    "45.202.247.152",
    "东京 NRT 0.00 MB/s 84",
    "Mia优选 | 韩国 KR | 129.154.50.72:8443",
    "129.154.50.72:8443",
    "129.154.50.72",
    "CF 电信优选 | 104.18.33.139",
    "104.18.33.139:443",
    "104.18.33.139",
    "麒麟优选 | 电信 | 172.64.152.106 | 43.36ms | 66.73mb/s",
    "172.64.152.106:443",
    "172.64.152.106",
    "优质节点 0.00 MB/s 2",
    "43.159.12.145:443",
    "43.159.12.145",
    "辣子鸡优选 | 汤加 TO | 45.147.49.149:443",
    "45.147.49.149:443",
    "45.147.49.149",
    "辣子鸡优选 | 小日本儿 JP | 45.192.249.158:443",
    "45.192.249.158:443",
    "45.192.249.158",
    "优质节点 0.00 MB/s 12",
    "43.159.12.37:443",
    "43.159.12.37",
    "- 0.00 MB/s 2",
    "172.64.229.12:443",
    "172.64.229.12",
    "优质节点 0.00 MB/s 13",
    "43.159.12.12:443",
    "43.159.12.12",
    "CF 电信优选 | 172.66.1.130",
    "172.66.1.130:443",
    "172.66.1.130",
    "- 0.00 MB/s 7",
    "191.222.219.124:2096",
    "191.222.219.124",
    "Mia优选 | 韩国 KR | 47.80.57.116:443",
    "47.80.57.116:443",
    "47.80.57.116",
    "东京 NRT 11.47 MB/s",
    "172.64.229.171:443",
    "172.64.229.171",
    "辣子鸡优选 | 小日本儿 JP | 177.5.52.32:40004",
    "177.5.52.32:40004",
    "177.5.52.32",
    "微测优选 | 电信 | SIN | 104.18.37.186",
    "104.18.37.186:443",
    "104.18.37.186",
    "辣子鸡优选 | 中国香港 HK | 141.11.148.138:443",
    "141.11.148.138:443",
    "141.11.148.138",
    "辣子鸡优选 | 多哥 TG | 83.147.15.86:443",
    "83.147.15.86:443",
    "83.147.15.86",
    "天诚优选1 | 泡菜欧巴 | KR | 121.166.39.76:12433",
    "121.166.39.76:12433",
    "121.166.39.76",
    "东京 NRT 9.92 MB/s",
    "152.175.38.45:443",
    "152.175.38.45",
    "东京 NRT 11.95 MB/s",
    "172.64.229.113:443",
    "172.64.229.113",
    "CFYes优选 | 电信 | 104.19.204.161",
    "104.19.204.161:443",
    "104.19.204.161",
    "微测优选 | 移动 | HKG | 104.16.155.70",
    "104.16.155.70:443",
    "104.16.155.70",
    "辣子鸡优选 | 中国香港 HK | 156.224.78.162:443",
    "156.224.78.162:443",
    "156.224.78.162",
    "Mia优选 | 韩国 KR | 43.155.209.83:2053",
    "43.155.209.83:2053",
    "43.155.209.83",
    "CFYes优选 | 移动 | 198.41.209.123",
    "198.41.209.123:443",
    "198.41.209.123",
    "天诚优选1 | 港岛茶记 | HK | 47.57.181.17:443",
    "47.57.181.17:443",
    "47.57.181.17",
    "麒麟优选 | 联通 | 104.26.2.26 | 66.88ms | 50.04mb/s",
    "104.26.2.26:443",
    "104.26.2.26",
    "S5公益优选 | 小日本儿 | JP | 149.28.18.65:8443",
    "149.28.18.65:8443",
    "149.28.18.65",
    "辣子鸡优选 | 新加坡 SG | 50.114.55.97:443",
    "50.114.55.97:443",
    "50.114.55.97",
    "Gslege优选 | sg 【新加坡】 SG | 108.162.192.3",
    "108.162.192.3:443",
    "108.162.192.3",
    "Mia优选 | 韩国 KR | 134.185.99.52:443",
    "134.185.99.52:443",
    "134.185.99.52",
    "天诚优选1 | 小日本儿 | JP | 158.101.131.94:2083",
    "158.101.131.94:2083",
    "158.101.131.94",
    "优质节点 0.00 MB/s 3",
    "43.159.12.178:443",
    "43.159.12.178",
    "Gslege优选 | sg 【新加坡】 SG | 162.159.0.3",
    "162.159.0.3:443",
    "162.159.0.3",
    "Gslege优选 | sg 【新加坡】 SG | 172.64.32.3",
    "172.64.32.3:443",
    "172.64.32.3",
    "辣子鸡优选 | 中国香港 HK | 141.11.149.89:443",
    "141.11.149.89:443",
    "141.11.149.89",
    "东京 NRT 10.41 MB/s",
    "172.64.229.122:443",
    "172.64.229.122",
    "SG",
    "157.230.248.19:443",
    "157.230.248.19",
    "辣子鸡优选 | 中国香港 HK | 156.224.76.187:443",
    "156.224.76.187:443",
    "156.224.76.187",
    "东京 NRT 11.24 MB/s",
    "172.64.229.176:443",
    "172.64.229.176",
    "Mia优选 | 韩国 KR | 43.108.46.150:8443",
    "43.108.46.150:8443",
    "43.108.46.150",
    "辣子鸡优选 | 中国香港 HK | 156.226.173.183:443",
    "156.226.173.183:443",
    "156.226.173.183",
    "Mia优选 | 马来西亚 MY | 149.118.144.163:443",
    "149.118.144.163:443",
    "149.118.144.163",
    "辣子鸡优选 | 小日本儿 JP | 154.83.93.23:443",
    "154.83.93.23:443",
    "154.83.93.23",
    "东京 NRT 13.31 MB/s",
    "172.64.229.43:443",
    "172.64.229.43",
    "辣子鸡优选 | 中国香港 HK | 185.155.235.39:443",
    "185.155.235.39:443",
    "185.155.235.39",
    "麒麟优选 | 联通 | 162.159.135.111 | 66.65ms | 51.23mb/s",
    "162.159.135.111:443",
    "162.159.135.111",
    "东京 NRT 11.37 MB/s",
    "172.64.229.34:443",
    "172.64.229.34",
    "东京 NRT 11.54 MB/s 2",
    "172.64.229.141:443",
    "172.64.229.141",
    "优质节点 0.00 MB/s 16",
    "43.159.12.83:443",
    "43.159.12.83",
    "辣子鸡优选 | 汤加 TO | 194.169.54.16:8443",
    "194.169.54.16:8443",
    "194.169.54.16",
    "辣子鸡优选 | 中国香港 HK | 141.11.91.16:443",
    "141.11.91.16:443",
    "141.11.91.16",
    "东京 NRT 11.29 MB/s",
    "172.64.229.16:443",
    "172.64.229.16",
    "天诚优选1 | 战争贩子 | US | 23.94.56.22:443",
    "23.94.56.22:443",
    "23.94.56.22",
    "JP [高速 by Jz 23M] 2",
    "183.60.61.118:2053",
    "183.60.61.118",
    "东京 NRT 10.27 MB/s",
    "172.64.229.151:443",
    "172.64.229.151",
    "东京 NRT 13.26 MB/s",
    "172.64.229.189:443",
    "172.64.229.189",
    "- 0.00 MB/s 3",
    "172.64.229.13:443",
    "172.64.229.13",
    "东京 NRT 11.66 MB/s",
    "172.64.229.44:443",
    "172.64.229.44",
    "辣子鸡优选 | 小日本儿 JP | 156.243.244.18:443",
    "156.243.244.18:443",
    "156.243.244.18",
    "优质节点 0.00 MB/s 19",
    "43.159.12.24:443",
    "43.159.12.24",
    "辣子鸡优选 | 中国香港 HK | 45.149.186.154:443",
    "45.149.186.154:443",
    "45.149.186.154",
    "优质节点 0.00 MB/s 10",
    "43.159.12.58:443",
    "43.159.12.58",
    "辣子鸡优选 | 美国 US | 45.202.241.10:443",
    "45.202.241.10:443",
    "45.202.241.10",
    "东京 NRT 11.44 MB/s",
    "172.64.229.10:443",
    "172.64.229.10",
    "东京 NRT 10.46 MB/s",
    "东京 NRT 11.56 MB/s",
    "172.64.229.96:443",
    "172.64.229.96",
    "优质节点 0.00 MB/s 6",
    "43.159.12.139:443",
    "43.159.12.139",
    "Gslege优选 | sg 【新加坡】 SG | 162.159.0.6",
    "162.159.0.6:443",
    "162.159.0.6",
    "Gslege优选 | sg 【新加坡】 SG | 172.64.32.6",
    "172.64.32.6:443",
    "172.64.32.6",
    "东京 NRT 13.02 MB/s",
    "172.64.229.6:443",
    "172.64.229.6",
    "S5公益优选 | 小日本儿 | JP | 150.230.2.165:443",
    "150.230.2.165:443",
    "150.230.2.165",
    "香港 HKG 26.04 MB/s",
    "Mia优选 | 中国香港 HK | 43.254.216.175:8443",
    "43.254.216.175:8443",
    "43.254.216.175",
    "Mia优选 | 马来西亚 MY | 56.69.183.8:443",
    "56.69.183.8:443",
    "56.69.183.8",
    "Mia优选 | 新加坡 SG | 207.148.127.157:8443",
    "207.148.127.157:8443",
    "207.148.127.157",
    "Mia优选 | 新加坡 SG | 45.77.174.69:443",
    "45.77.174.69:443",
    "45.77.174.69",
    "辣子鸡优选 | 新加坡 SG | 43.160.240.180:443",
    "43.160.240.180:443",
    "43.160.240.180",
    "辣子鸡优选 | 小日本儿 JP | 154.83.95.25:443",
    "154.83.95.25:443",
    "154.83.95.25",
    "香港 HKG 0.00 MB/s",
    "优质节点 0.00 MB/s 11",
    "43.159.12.248:443",
    "43.159.12.248",
    "辣子鸡优选 | 中国台湾 TW | 141.11.87.48:443",
    "141.11.87.48:443",
    "141.11.87.48",
    "辣子鸡优选 | 中国香港 HK | 185.155.235.35:40649",
    "185.155.235.35:40649",
    "185.155.235.35",
    "辣子鸡优选 | 中国香港 HK | 156.226.173.114:443",
    "156.226.173.114:443",
    "156.226.173.114",
    "优质节点 0.00 MB/s 23",
    "43.159.12.192:443",
    "43.159.12.192",
    "S5公益优选 | 小日本儿 | JP | 64.176.44.23:443",
    "64.176.44.23:443",
    "64.176.44.23",
    "东京 NRT 12.96 MB/s",
    "172.64.229.23:443",
    "172.64.229.23",
    "麒麟优选 | 移动 | 172.64.152.73 | 50.15ms | 0.18mb/s",
    "172.64.152.73:443",
    "172.64.152.73",
    "优质节点 0.00 MB/s 18",
    "43.159.12.227:443",
    "43.159.12.227",
    "天诚优选1 | 港岛茶记 | HK | 103.96.74.18:16000",
    "103.96.74.18:16000",
    "103.96.74.18",
    "S5公益优选 | 印加坡县 | SG | 172.104.186.18:8443",
    "172.104.186.18:8443",
    "172.104.186.18",
    "东京 NRT 11.59 MB/s",
    "172.64.229.18:443",
    "172.64.229.18",
    "辣子鸡优选 | 小日本儿 JP | 45.192.206.31:443",
    "45.192.206.31:443",
    "45.192.206.31",
    "Mia优选 | 新加坡 SG | 207.148.120.55:443",
    "207.148.120.55:443",
    "207.148.120.55",
    "辣子鸡优选 | 中国香港 HK | 45.207.156.131:443",
    "45.207.156.131:443",
    "45.207.156.131",
    "天诚优选1 | 港岛茶记 | HK | 47.243.54.45:18080",
    "47.243.54.45:18080",
    "47.243.54.45",
    "CF 0.00 MB/s",
    "Gslege优选 | sg 【新加坡】 SG | 172.64.32.4",
    "172.64.32.4:443",
    "172.64.32.4",
    "优质节点 0.00 MB/s 8",
    "43.159.12.136:443",
    "43.159.12.136",
    "洛璃优选 | 马来西亚 MY | 56.69.183.8:443",
    "辣子鸡优选 | 小日本儿 JP | 216.23.122.8:443",
    "216.23.122.8:443",
    "216.23.122.8",
    "辣子鸡优选 | 马来西亚 MY | 56.69.183.8:443",
    "MY [优选高速 101.11ms]",
    "天诚优选1 | 港岛茶记 | HK | 154.38.116.8:443",
    "154.38.116.8:443",
    "154.38.116.8",
    "Gslege优选 | sg 【新加坡】 SG | 172.64.32.8",
    "172.64.32.8:443",
    "172.64.32.8",
    "Gslege优选 | sg 【新加坡】 SG | 108.162.192.8",
    "108.162.192.8:443",
    "108.162.192.8",
    "东京 NRT 11.61 MB/s",
    "172.64.229.8:443",
    "172.64.229.8",
    "Mia优选 | 越南 VN | 160.30.54.63:443",
    "160.30.54.63:443",
    "160.30.54.63",
    "辣子鸡优选 | 中国香港 HK | 23.249.18.144:8581",
    "23.249.18.144:8581",
    "23.249.18.144",
    "优质节点 0.00 MB/s",
    "43.159.12.88:443",
    "43.159.12.88",
    "辣子鸡优选 | 印度 IN | 31.25.88.21:14239",
    "31.25.88.21:14239",
    "31.25.88.21",
    "东京 NRT 0.00 MB/s 61",
    "辣子鸡优选 | 小日本儿 JP | 45.192.207.188:443",
    "45.192.207.188:443",
    "45.192.207.188",
    "辣子鸡优选 | 美国 US | 45.202.242.128:443",
    "45.202.242.128:443",
    "45.202.242.128",
    "东京 NRT 7.17 MB/s",
    "172.64.229.140:443",
    "172.64.229.140",
    "HK [高速 by Jz 34M]",
    "43.132.231.159:443",
    "43.132.231.159",
    "CF 电信优选 | 104.17.147.68",
    "104.17.147.68:443",
    "104.17.147.68",
    "辣子鸡优选 | 小日本儿 JP | 151.242.164.101:443",
    "151.242.164.101:443",
    "151.242.164.101",
    "东京 NRT 11.24 MB/s 2",
    "172.64.229.168:443",
    "172.64.229.168",
    "天诚优选1 | 小日本儿 | JP | 140.83.54.126:34237",
    "140.83.54.126:34237",
    "140.83.54.126",
    "辣子鸡优选 | 美国 US | 23.158.136.185:443",
    "23.158.136.185:443",
    "23.158.136.185",
    "优质节点 0.00 MB/s 21",
    "43.159.12.104:443",
    "43.159.12.104",
    "辣子鸡优选 | 小日本儿 JP | 156.246.90.21:443",
    "156.246.90.21:443",
    "156.246.90.21",
    "CF 电信优选 | 104.18.33.21",
    "104.18.33.21:443",
    "104.18.33.21",
    "东京 NRT 12.56 MB/s",
    "172.64.229.21:443",
    "172.64.229.21",
    "S5公益优选 | 小日本儿 | JP | 142.91.108.54:443",
    "142.91.108.54:443",
    "142.91.108.54",
    "辣子鸡优选 | 中国香港 HK | 156.226.172.129:443",
    "156.226.172.129:443",
    "156.226.172.129",
    "Mia优选 | 韩国 KR | 43.155.134.179:443",
    "43.155.134.179:443",
    "43.155.134.179",
    "辣子鸡优选 | 德国 DE | 156.226.174.20:443",
    "156.226.174.20:443",
    "156.226.174.20",
    "微测优选 | 联通 | SJC | 104.17.155.156",
    "104.17.155.156:443",
    "104.17.155.156",
    "优质节点 0.00 MB/s 17",
    "43.159.12.156:443",
    "43.159.12.156",
    "天诚优选1 | 印加坡县 | SG | 129.150.48.17:443",
    "129.150.48.17:443",
    "129.150.48.17",
    "天诚优选1 | 战争贩子 | US | 96.44.160.17:8080",
    "96.44.160.17:8080",
    "96.44.160.17",
    "S5公益优选 | 小日本儿 | JP | 64.176.36.17:443",
    "64.176.36.17:443",
    "64.176.36.17",
    "CF 电信优选 | 104.18.33.17",
    "104.18.33.17:443",
    "104.18.33.17",
    "东京 NRT 10.97 MB/s",
    "172.64.229.17:443",
    "172.64.229.17",
    "Mia优选 | 中国台湾 TW | 60.249.101.167:443",
    "60.249.101.167:443",
    "60.249.101.167",
    "辣子鸡优选 | 中国香港 HK | 156.224.79.105:443",
    "156.224.79.105:443",
    "156.224.79.105",
    "辣子鸡优选 | 中国香港 HK | 151.242.125.29:443",
    "151.242.125.29:443",
    "151.242.125.29",
    "辣子鸡优选 | 新加坡 SG | 185.81.29.47:443",
    "185.81.29.47:443",
    "185.81.29.47",
    "辣子鸡优选 | 小日本儿 JP | 156.246.88.127:443",
    "156.246.88.127:443",
    "156.246.88.127",
    "麒麟优选 | 联通 | 172.67.71.153 | 65.99ms | 50.04mb/s",
    "172.67.71.153:443",
    "172.67.71.153",
    "CF 电信优选 | 188.164.248.110",
    "188.164.248.110:443",
    "188.164.248.110",
    "东京 NRT 11.60 MB/s",
    "172.64.229.147:443",
    "172.64.229.147",
    "Mia优选 | 韩国 KR | 43.131.225.115:443",
    "43.131.225.115:443",
    "43.131.225.115",
    "辣子鸡优选 | 小日本儿 JP | 154.83.91.181:443",
    "154.83.91.181:443",
    "154.83.91.181",
    "辣子鸡优选 | 小日本儿 JP | 154.83.95.77:443",
    "154.83.95.77:443",
    "154.83.95.77",
    "辣子鸡优选 | 小日本儿 JP | 156.231.112.80:443",
    "156.231.112.80:443",
    "156.231.112.80",
    "优质节点 0.00 MB/s 27",
    "43.159.12.38:443",
    "43.159.12.38",
    "洛璃优选 | 韩国 KR | 43.155.221.27:8443",
    "辣子鸡优选 | 韩国 KR | 43.155.221.27:8443",
    "KR [优选高速 76.84ms]",
    "CF 电信优选 | 8.35.211.27",
    "8.35.211.27:443",
    "8.35.211.27",
    "东京 NRT 12.25 MB/s",
    "172.64.229.27:443",
    "172.64.229.27",
    "辣子鸡优选 | 中国香港 HK | 156.226.169.60:443",
    "156.226.169.60:443",
    "156.226.169.60",
    "- 0.00 MB/s 6",
    "191.222.217.144:2083",
    "191.222.217.144",
    "优质节点 0.00 MB/s 24",
    "43.159.12.232:443",
    "43.159.12.232",
    "优质节点 0.00 MB/s 22",
    "43.159.12.234:443",
    "43.159.12.234",
    "麒麟优选 | 电信 | 172.64.158.22 | 43.75ms | 66.65mb/s",
    "172.64.158.22:443",
    "172.64.158.22",
    "东京 NRT 11.78 MB/s",
    "172.64.229.22:443",
    "172.64.229.22",
    "CF 电信优选 | 104.17.155.145",
    "104.17.155.145:443",
    "104.17.155.145",
    "麒麟优选 | 联通 | 172.67.65.103 | 66.34ms | 51.52mb/s",
    "172.67.65.103:443",
    "172.67.65.103",
    "辣子鸡优选 | 美国 US | 166.0.188.121:443",
    "166.0.188.121:443",
    "166.0.188.121",
    "天诚优选1 | 港岛茶记 | HK | 8.218.36.133:9010",
    "8.218.36.133:9010",
    "8.218.36.133",
    "辣子鸡优选 | 中国香港 HK | 45.202.248.172:443",
    "45.202.248.172:443",
    "45.202.248.172",
    "CF 电信优选 | 8.35.211.62",
    "8.35.211.62:443",
    "8.35.211.62",
    "CF 电信优选 | 8.35.211.160",
    "8.35.211.160:443",
    "8.35.211.160",
    "优质节点 0.00 MB/s 9",
    "43.159.12.163:443",
    "43.159.12.163",
    "S5公益优选 | 印加坡县 | SG | 5.223.59.9:443",
    "5.223.59.9:443",
    "5.223.59.9",
    "Gslege优选 | sg 【新加坡】 SG | 162.159.0.9",
    "162.159.0.9:443",
    "162.159.0.9",
    "Gslege优选 | sg 【新加坡】 SG | 108.162.192.9",
    "108.162.192.9:443",
    "108.162.192.9",
    "Gslege优选 | sg 【新加坡】 SG | 172.64.32.9",
    "172.64.32.9:443",
    "172.64.32.9",
    "东京 NRT 10.44 MB/s",
    "172.64.229.9:443",
    "172.64.229.9",
    "东京 NRT 12.09 MB/s",
    "172.64.229.143:443",
    "172.64.229.143",
    "优质节点 0.00 MB/s 20",
    "43.159.12.80:443",
    "43.159.12.80",
    "辣子鸡优选 | 中国香港 HK | 45.8.186.20:443",
    "45.8.186.20:443",
    "45.8.186.20",
    "辣子鸡优选 | 中国台湾 TW | 83.147.12.20:443",
    "83.147.12.20:443",
    "83.147.12.20",
    "东京 NRT 6.69 MB/s",
    "172.64.229.20:443",
    "172.64.229.20",
    "优质节点 0.00 MB/s 26",
    "43.159.12.190:443",
    "43.159.12.190",
    "CF 电信优选 | 8.35.211.26",
    "8.35.211.26:443",
    "8.35.211.26",
    "东京 NRT 12.85 MB/s",
    "172.64.229.26:443",
    "172.64.229.26",
    "辣子鸡优选 | 小日本儿 JP | 156.231.117.99:443",
    "156.231.117.99:443",
    "156.231.117.99",
    "优质节点 0.00 MB/s 15",
    "43.159.12.124:443",
    "43.159.12.124",
    "辣子鸡优选 | 美国 US | 23.158.136.15:443",
    "23.158.136.15:443",
    "23.158.136.15",
    "麒麟优选 | 电信 | 172.64.149.15 | 44.22ms | 58.46mb/s",
    "172.64.149.15:443",
    "172.64.149.15",
    "麒麟优选 | 多线 | 104.18.41.15 | 68.18ms | 0.13mb/s",
    "104.18.41.15:443",
    "104.18.41.15",
    "CF 电信优选 | 104.18.33.15",
    "104.18.33.15:443",
    "104.18.33.15",
    "东京 NRT 12.97 MB/s",
    "172.64.229.15:443",
    "172.64.229.15",
    "KR 2",
    "152.67.214.155:443",
    "152.67.214.155",
    "麒麟优选 | 移动 | 104.19.149.120 | 51.10ms | 0.28mb/s",
    "104.19.149.120:443",
    "104.19.149.120",
    "S5公益优选 | 印加坡县 | SG | 5.223.52.82:443",
    "5.223.52.82:443",
    "5.223.52.82",
    "辣子鸡优选 | 小日本儿 JP | 156.231.113.81:443",
    "156.231.113.81:443",
    "156.231.113.81",
    "辣子鸡优选 | 韩国 KR | 211.110.208.116:443",
    "211.110.208.116:443",
    "211.110.208.116",
    "Mia优选 | 新加坡 SG | 66.42.54.67:443",
    "66.42.54.67:443",
    "66.42.54.67",
    "优质节点 0.00 MB/s 4",
    "43.159.12.45:443",
    "43.159.12.45",
    "Gslege优选 | sg 【新加坡】 SG | 108.162.192.4",
    "108.162.192.4:443",
    "108.162.192.4",
    "KR [高速 by Jz 27M]",
    "168.107.40.4:8443",
    "168.107.40.4",
    "东京 NRT 11.56 MB/s 2",
    "172.64.229.4:443",
    "172.64.229.4",
    "东京 NRT 8.50 MB/s",
    "172.64.229.117:443",
    "172.64.229.117",
    "东京 NRT 11.02 MB/s",
    "172.64.229.191:443",
    "172.64.229.191",
    "辣子鸡优选 | 中国香港 HK | 151.242.125.102:443",
    "151.242.125.102:443",
    "151.242.125.102",
    "辣子鸡优选 | 小日本儿 JP | 156.231.117.95:443",
    "156.231.117.95:443",
    "156.231.117.95",
    "CF 电信优选 | 188.164.248.66",
    "188.164.248.66:443",
    "188.164.248.66",
    "Mia优选 | 越南 VN | 160.25.74.124:443",
    "160.25.74.124:443",
    "160.25.74.124",
    "Mia优选 | 新加坡 SG | 45.76.158.46:443",
    "45.76.158.46:443",
    "45.76.158.46",
    "JP [优选高速 96.75ms]",
    "202.144.194.170:443",
    "202.144.194.170",
    "辣子鸡优选 | 美国 US | 45.202.243.92:443",
    "45.202.243.92:443",
    "45.202.243.92",
    "辣子鸡优选 | 小日本儿 JP | 156.246.91.88:443",
    "156.246.91.88:443",
    "156.246.91.88",
    "麒麟优选 | 多线 | 104.18.43.57 | 68.51ms | 14.07mb/s",
    "104.18.43.57:443",
    "104.18.43.57",
    "辣子鸡优选 | 中国香港 HK | 185.155.235.58:443",
    "185.155.235.58:443",
    "185.155.235.58",
    "优质节点 0.00 MB/s 29",
    "43.159.12.216:443",
    "43.159.12.216",
    "辣子鸡优选 | 中国香港 HK | 193.134.211.85:6400",
    "193.134.211.85:6400",
    "193.134.211.85",
    "辣子鸡优选 | 小日本儿 JP | 45.192.206.50:443",
    "45.192.206.50:443",
    "45.192.206.50",
    "东京 NRT 0.00 MB/s 137",
    "- 0.00 MB/s 4",
    "Mia优选 | 印尼 ID | 43.229.254.182:443",
    "43.229.254.182:443",
    "43.229.254.182",
    "Mia优选 | 新加坡 SG | 140.245.38.33:2096",
    "140.245.38.33:2096",
    "140.245.38.33",
    "Mia优选 | 中国香港 HK | 43.175.131.30:443",
    "43.175.131.30:443",
    "43.175.131.30",
    "辣子鸡优选 | 中国香港 HK | 38.6.219.125:443",
    "38.6.219.125:443",
    "38.6.219.125",
    "辣子鸡优选 | 中国香港 HK | 43.175.131.30:443",
    "辣子鸡优选 | 小日本儿 JP | 45.202.245.177:443",
    "45.202.245.177:443",
    "45.202.245.177",
    "辣子鸡优选 | 中国香港 HK | 45.207.157.136:443",
    "45.207.157.136:443",
    "45.207.157.136",
    "辣子鸡优选 | 新加坡 SG | 43.159.4.80:443",
    "43.159.4.80:443",
    "43.159.4.80",
    "优质节点 0.00 MB/s 5",
    "43.159.12.235:443",
    "43.159.12.235",
    "Mia优选 | 韩国 KR | 43.200.87.5:443",
    "洛璃优选 | 韩国 KR | 43.200.87.5:443",
    "辣子鸡优选 | 韩国 KR | 43.200.87.5:443",
    "CFYes优选 | 电信 | 104.16.249.5",
    "104.16.249.5:443",
    "104.16.249.5",
    "麒麟优选 | 电信 | 172.64.148.5 | 44.33ms | 65.54mb/s",
    "172.64.148.5:443",
    "172.64.148.5",
    "Gslege优选 | sg 【新加坡】 SG | 162.159.0.5",
    "162.159.0.5:443",
    "162.159.0.5",
    "Gslege优选 | sg 【新加坡】 SG | 172.64.32.5",
    "172.64.32.5:443",
    "172.64.32.5",
    "vvHan优选 | 电信 | Default | 104.16.249.5",
    "东京 NRT 11.14 MB/s",
    "172.64.229.5:443",
    "172.64.229.5"
  ];

  // 典藏常青极品池端点清单 (共 0 个)
  const starTokens = [

  ];

  // 香港与中国大陆特征排除规则 (严格过滤香港与大陆，保留台湾省 TW)
  const excludeRegex = /(香港|HK|Hong\s*Kong|HongKong|中国(?!\s*台湾)|大陆|回国|\bCN\b)/i;

  const allProxies = config.proxies || [];

  // 判断节点是否命中优选池特征 (支持名称、IP:端口、纯IP任意命中)
  const isPremiumProxy = (p) => {
    if (premiumTokens.length === 0) return true;
    const ep = `${p.server}:${p.port}`;
    const s = String(p.server || '');
    return premiumTokens.includes(p.name) || 
           premiumTokens.includes(ep) || 
           premiumTokens.includes(s);
  };

  // 判断节点是否命中典藏常青池特征
  const isStarProxy = (p) => {
    if (starTokens.length === 0) return false;
    const ep = `${p.server}:${p.port}`;
    const s = String(p.server || '');
    return starTokens.includes(p.name) || 
           starTokens.includes(ep) || 
           starTokens.includes(s);
  };

  // 判断节点是否符合纯净非香港/非大陆规则
  const isNonHongKongProxy = (p) => {
    const name = p.name || '';
    if (excludeRegex.test(name)) return false;
    return true;
  };

  // ================= 规则执行：直接注入各策略组 (规则驱动，非兜底) =================

  // 1. 【⚡ 自动选择】：规则准入优选池的所有活跃节点
  let autoProxies = allProxies.filter(p => isPremiumProxy(p)).map(p => p.name);
  if (autoProxies.length === 0) {
    autoProxies = allProxies.map(p => p.name);
  }
  if (autoProxies.length === 0) autoProxies = ['DIRECT'];

  // 2. 【⚡ 自动选择 (非香港)】：严格按照非香港规则，准入优选池中所有非香港节点！
  // 规则标准：凡是属于优选池且名称与特征严格排除香港及中国大陆的节点，一律直接全量加入！
  let autoNoHkProxies = allProxies
    .filter(p => isPremiumProxy(p) && isNonHongKongProxy(p))
    .map(p => p.name);

  // 若优选池中暂未匹配到非港节点，则从当前订阅全量节点中直接按非港规则全量准入
  if (autoNoHkProxies.length === 0) {
    autoNoHkProxies = allProxies
      .filter(p => isNonHongKongProxy(p))
      .map(p => p.name);
  }
  if (autoNoHkProxies.length === 0) autoNoHkProxies = ['DIRECT'];

  // 3. 【⚡ 自动选择 (典藏)】：严格按典藏规则直接准入
  let starProxies = allProxies.filter(p => isStarProxy(p)).map(p => p.name);
  if (starProxies.length === 0) starProxies = ['DIRECT'];

  // ================= 策略组挂载与规则下发 =================
  const autoGroup = {
    name: autoGroupName,
    type: 'url-test',
    url: 'https://www.apple.com/library/test/success.html',
    interval: groupInterval,
    lazy: false,
    tolerance: groupTolerance,
    proxies: autoProxies
  };

  const autoGroupNoHk = {
    name: autoGroupNoHkName,
    type: 'url-test',
    url: 'https://www.apple.com/library/test/success.html',
    interval: groupInterval,
    lazy: false,
    tolerance: groupTolerance,
    proxies: autoNoHkProxies
  };

  const autoGroupStars = {
    name: autoGroupStarsName,
    type: 'url-test',
    url: 'https://www.apple.com/library/test/success.html',
    interval: starsGroupInterval,
    lazy: false,
    tolerance: starsGroupTolerance,
    proxies: starProxies
  };

  if (!config['proxy-groups']) {
    config['proxy-groups'] = [];
  }

  let groups = config['proxy-groups'];

  // 移除旧版本遗留重名组，防止重复
  groups = groups.filter(g => g.name !== autoGroupName && g.name !== autoGroupNoHkName && g.name !== autoGroupStarsName);

  // 插入到顶部策略组
  groups.unshift(autoGroupStars);
  groups.unshift(autoGroupNoHk);
  groups.unshift(autoGroup);

  // 级联注入上层业务分流策略组 (如 PROXY, 节点选择, 漏网之鱼 等)
  const masterGroups = ['PROXY', '节点选择', 'GLOBAL', '漏网之鱼', 'MATCH', 'Final'];
  groups.forEach(g => {
    if (masterGroups.includes(g.name)) {
      if (!g.proxies) g.proxies = [];
      if (!g.proxies.includes(autoGroupName)) g.proxies.unshift(autoGroupName);
      if (!g.proxies.includes(autoGroupNoHkName)) g.proxies.unshift(autoGroupNoHkName);
      if (starProxies.length > 0 && starProxies[0] !== 'DIRECT' && !g.proxies.includes(autoGroupStarsName)) {
        g.proxies.unshift(autoGroupStarsName);
      }
    }
  });

  config['proxy-groups'] = groups;
  return config;
}


const fs = require('fs');
const input = JSON.parse(fs.readFileSync('temp_input.json', 'utf8'));
const out = main(input);
console.log('Result auto group count:', out['proxy-groups'].find(g => g.name === '⚡ 自动选择').proxies.length);
console.log('Result auto no-hk group count:', out['proxy-groups'].find(g => g.name === '⚡ 自动选择 (非香港)').proxies.length);
console.log('Sample no-hk proxies:', out['proxy-groups'].find(g => g.name === '⚡ 自动选择 (非香港)').proxies.slice(0, 5));
```

## File: `代码审查报告.md`

```markdown
[老板，本次任务为静态审查阶段，暂不生成任何修改代码。以下为您要求的项目潜在 Bug 与风险审计报告主文]

=== 项目潜在 Bug 与风险审计报告 ===

1. 多线程安全隐患 (Thread Safety)
- 跨线程 UI 更新引发的崩溃风险：我们系统含有大量后台子线程任务（例如 services/probe_service.py 节点测速，以及 pipelines/scheduler.py 任务调度）。如果在这些非主线程中，直接尝试操作更新界面控件（如 gui_fluent/widgets/node_table.py 注入数据或 gui_fluent/components/log_panel.py 打印日志），而不严格通过 Qt 的信号槽（Signal/Slot）机制排队传递，将必定导致底层 C++ 段错误（Segfault），表现为软件在无任何报错提示的情况下瞬间闪退崩溃。
- 强制终止线程造成的全局死锁死局：在 auto_pipeline.py 及 pool_service.py 逻辑流转中，如果为了强制停止当前执行任务而暴力杀死底层线程，极容易导致 core/state_manager.py 中的全局状态互斥锁无法被正确释放。这将引发灾难性后果，导致下一次用户触发流转任务时，整个程序因等待被永久占用的锁而彻底卡死挂起。

2. 异常处理真空 (Exception Handling)
- 网络 IO 异常未兜底导致主线程断崖崩溃：在 services/clash_client.py （与 Clash 核心交互）及 services/subscription_service.py （拉取远端节点订阅）模块中，极易遇到网络波动、超时 (Timeout) 或连接被拒绝。如果网络请求的最外层没有严密的 try-except 捕获机制并引入重试或回退 (Fallback) 逻辑，这些未被拦截的网络异常会一直抛到最顶层，造成主线程直接崩盘。
- 并发读写造成配置文件彻底损毁：config/config_manager.py 在高频进行持久化写入配置序列化时，如果遭遇多线程抢占写入或软件突然意外关闭，且代码层未采用“先写入临时文件，成功后再进行原子替换 (Atomic Rename)”的安全策略，极易导致关键配置文件被清空为 0KB。这将造成用户本地数据完全丢失，且下一次打开软件直接呈现白屏瘫痪。

3. 数据一致性漏洞 (Data Consistency)
- 多池流转引发的“数据幽灵”与漏网之鱼：我们系统的核心竞争力包含多池流转机制（活跃、精选、黑名单 page_delay_black.py / page_speed_black.py、典藏 page_stars.py 等）。在节点从 A 池弹出并准备压入 B 池的极短内存操作间隙内，如果发生异常中断（例如内存操作抛错），该节点就会陷入“不在 A 也不在 B”的数据彻底蒸发状态，或者“既存在于黑名单又存在于活跃池”的错乱状态。多池与状态转换之间必须确保内存操作逻辑的原子事务性，要么全部流转成功，要么触发异常全部回滚。
```

## File: `config/__init__.py`

```python
"""
Clash Verge 节点管理助手 - 配置管理包
"""
```

## File: `config/config_manager.py`

```python
import json
import os
import shutil
import threading


def atomic_save_config(filepath, config_dict):
    """
    原子化持久保存配置字典：
    1. 先写入临时文件 .tmp 并刷新磁盘
    2. 校验文件写入完整无损
    3. 保留原文件为 .bak 作为灾备
    4. 执行原子重命名覆盖，杜绝断电/中断导致文件损坏清零
    """
    try:
        dir_name = os.path.dirname(filepath)
        if dir_name and not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)

        tmp_path = filepath + ".tmp"
        bak_path = filepath + ".bak"

        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())

        if os.path.exists(filepath):
            try:
                shutil.copyfile(filepath, bak_path)
            except Exception:
                pass

        os.replace(tmp_path, filepath)
        return True, ""
    except Exception as e:
        return False, str(e)


def safe_load_config(filepath):
    """
    安全读取配置文件，若主配置损坏则自动从 .bak 灾备副本中无缝自愈恢复
    """
    if not os.path.exists(filepath):
        bak_path = filepath + ".bak"
        if os.path.exists(bak_path):
            filepath = bak_path
        else:
            return {}

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        bak_path = filepath + ".bak"
        if os.path.exists(bak_path):
            try:
                with open(bak_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
    return {}


class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_config()
            return cls._instance

    def _init_config(self):
        self.config_path = "config.json"
        self.config_data = {}
        self.file_lock = threading.RLock()
        self.load_config()

    def load_config(self):
        with self.file_lock:
            self.config_data = safe_load_config(self.config_path)

    def save_config(self, new_data=None):
        if new_data is not None:
            self.config_data.update(new_data)
        with self.file_lock:
            atomic_save_config(self.config_path, self.config_data)

    def get(self, key, default=None):
        with self.file_lock:
            return self.config_data.get(key, default)

    def set(self, key, value):
        with self.file_lock:
            self.config_data[key] = value
            self.save_config()
```

## File: `config/settings.py`

```python
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

# 香港与中国大陆特征排除规则 (严格过滤香港与大陆，保留台湾省 TW，排除 Google 送中节点)
EXCLUDE_HK_REGEX = re.compile(
    r"(香港|HK|Hong\s*Kong|HongKong|中国(?!\s*台湾)|大陆|回国|\bCN\b|送中)",
    re.IGNORECASE
)

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
```

## File: `core/__init__.py`

```python
"""
Clash Verge 节点管理助手 - 核心状态与模型包
"""
```

## File: `core/signal_bus.py`

```python
from PyQt5.QtCore import QObject, pyqtSignal
import threading

class SignalBus(QObject):
    """
    全局信号总线，解决非主线程跨线程更新 UI 引发的崩溃隐患。
    所有子线程（探针测速、任务调度等），必须通过 emit 发送信号，严禁直接操作界面控件。
    """
    _instance = None
    _init_lock = threading.Lock()

    # 节点数据注入信号 (参数: 节点数据列表)
    node_table_update = pyqtSignal(list)
    # 日志面板打印信号 (参数: 日志级别, 日志内容)
    log_print = pyqtSignal(str, str)
    # 状态流转通知信号 (参数: 状态信息)
    pool_transition = pyqtSignal(str)

    def __new__(cls):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

# 全局单例实例化，供各多线程模块安全调用
global_signals = SignalBus()
```

## File: `core/state_manager.py`

```python
import threading


class StateManager:
    _instance = None
    _init_lock = threading.Lock()

    def __new__(cls):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_state()
            return cls._instance

    def _init_state(self):
        # 采用 RLock 允许重入，避免同一线程内多次请求产生的死锁
        self._global_lock = threading.RLock()
        self._thread_stop_events = {}

        # 核心业务状态容器（预置默认容器初值，彻底杜绝 AttributeError）
        self.all_nodes = []
        self.node_details = {}
        self.active_profile = ""
        self.favorites = set()
        self.local_blacklist = set()
        self.speed_blacklist = set()
        self.blacklist_reasons = {}
        self.fav_reasons = {}
        self.verified_nodes = {}
        self.stars_nodes = []
        self.auto_endpoints = {}
        self.cloud_endpoints = {}
        self.node_delays = {}
        self.node_speeds = {}
        self.node_colo = {}
        self.node_history = {}
        self.node_speed_history = {}
        self.node_delay_history = {}
        self.node_colo_history = {}
        self.blacklist_timestamps = {}

    @property
    def lock(self):
        return self._global_lock

    def get_stop_event(self, thread_name: str) -> threading.Event:
        with self._global_lock:
            if thread_name not in self._thread_stop_events:
                self._thread_stop_events[thread_name] = threading.Event()
            return self._thread_stop_events[thread_name]

    def request_stop(self, thread_name: str):
        # 优雅发出终止信号，替代系统级暴力 kill 线程
        with self._global_lock:
            if thread_name in self._thread_stop_events:
                self._thread_stop_events[thread_name].set()

    def clear_stop_request(self, thread_name: str):
        with self._global_lock:
            if thread_name in self._thread_stop_events:
                self._thread_stop_events[thread_name].clear()

    def safe_execute(self, func, *args, **kwargs):
        # 提供上下文环境安全执行，采用 timeout 拦截永久死锁，异常时绝对保证释放锁
        acquired = self._global_lock.acquire(timeout=5.0)
        if not acquired:
            raise TimeoutError("无法获取全局状态互斥锁，检测到潜在死锁残留。")
        try:
            return func(*args, **kwargs)
        finally:
            try:
                self._global_lock.release()
            except RuntimeError:
                pass

    def get_snapshot(self):
        """
        线程安全导出状态机全局快照
        """
        with self._global_lock:
            return {
                "favorites": list(self.favorites),
                "local_blacklist": list(self.local_blacklist),
                "speed_blacklist": list(self.speed_blacklist),
                "blacklist_reasons": dict(self.blacklist_reasons),
                "fav_reasons": dict(self.fav_reasons),
                "verified_nodes": dict(self.verified_nodes),
                "stars_nodes": list(self.stars_nodes),
                "node_delays": dict(self.node_delays),
                "node_speeds": dict(self.node_speeds),
                "node_colo": dict(self.node_colo),
                "node_history": dict(self.node_history),
                "node_speed_history": dict(self.node_speed_history),
                "node_delay_history": dict(self.node_delay_history),
                "node_colo_history": dict(self.node_colo_history),
                "blacklist_timestamps": dict(self.blacklist_timestamps),
                "cloud_endpoints": dict(self.cloud_endpoints),
                "all_nodes": list(self.all_nodes),
                "active_profile": str(self.active_profile),
            }
```

## File: `gui/__init__.py`

```python
"""
Clash Verge 节点管理助手 - GUI 界面包
"""
from gui.app import ClashVergeTabsManager

__all__ = ["ClashVergeTabsManager"]
```

## File: `gui/app.py`

```python
from concurrent.futures import ThreadPoolExecutor
import ctypes
import glob
import gzip
import hashlib
import json
import os
import re
import socket
import ssl
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import traceback
import urllib.error
import urllib.parse
import urllib.request
import winreg
import winsound

try:
    from PIL import Image, ImageDraw
    import pystray
    TRAY_SUPPORTED = True
except ImportError:
    TRAY_SUPPORTED = False

from config.settings import (
    BASE_DIR,
    PARENT_DIR,
    DEFAULT_SCRIPT_JS,
    CONFIG_STORAGE_PATH,
    RUN_REG_KEY,
    REG_APP_NAME,
    THEME,
    EXCLUDE_HK_REGEX,
    NON_ASIA_CN_KEYWORDS,
    NON_ASIA_CODE_SET,
    ASIA_CN_KEYWORDS,
    ASIA_CODE_SET,
    COLO_NAME_MAP,
    COLO_REGIONS,
    COUNTRY_NAME_MAP,
)
from config.config_manager import (
    atomic_save_config,
    safe_load_config,
    prune_expired_history,
)

from services.probe_service import (
    get_ip_location_fallback,
    get_cf_colo_raw,
    tcp_ping,
    get_c_segment_ips,
    detect_node_region,
    measure_http_download_speed,
)
from services.clash_client import ClashClient, ClashModeGuard
from core.state_manager import StateManager
from services.colo_service import (
    get_colo_region,
    record_colo_sample,
    analyze_colo_stats,
    is_node_hongkong,
    is_asian_node,
)
from services.filter_service import (
    compute_delay_stats,
    check_node_jitter_blacklisted,
    auto_filter_and_blacklist_non_asia_nodes,
)
from services.pool_service import (
    get_pool_endpoint_sets,
    deduplicate_favorites_by_endpoint,
    align_favorites_with_current_subscription,
    clean_offline_favorites,
    process_verified_lifecycle,
    purge_invalid_and_blacklisted_from_all_pools,
)
from services.script_generator import build_script_js, write_script_js
from pipelines.scheduler import SchedulerDaemon
from pipelines.base_pipeline import BasePipeline
from services.subscription_service import (
    extract_nodes_and_details_from_file,
    choose_canonical_node_name,
    get_node_endpoint,
    resolve_node_to_current,
    update_remote_subscription,
)

from utils.win32_utils import (
    send_system_notification,
    is_run_as_admin,
    trigger_verge_reactivate_hotkey,
    create_tray_icon_image,
    check_boot_startup_registry,
    set_boot_startup_registry,
    create_modern_btn,
)

class ClashVergeTabsManager:

    def __init__(self, root):
        self.root = root
        self.root.title("Clash Verge 节点管理助手 (7天Colo长效防漂移与C段挖掘版)")
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w = min(1480, max(1000, screen_w - 60))
        win_h = min(920, max(680, screen_h - 100))
        self.root.geometry(f"{win_w}x{win_h}")
        self.root.configure(bg=THEME["bg_main"])

        self.all_nodes = []
        self.favorites = set()
        self.local_blacklist = set()
        self.speed_blacklist = set()
        self.blacklist_reasons = {}
        self.fav_reasons = {}

        self.verified_nodes = {}
        self.stars_nodes = []

        self.node_delays = {}
        self.node_speeds = {}
        self.node_colo = {}
        # 核心：滑动7天时序桶结构 {key: [{"ts": 1725..., "colo": "HKG"}, ...]}
        self.node_colo_history = {}
        self.node_history = {}
        self.node_speed_history = {}
        self.node_delay_history = {}
        self.node_details = {}
        self.auto_endpoints = set()
        self.trees = {}
        self._delay_black_dirty = True
        self._speed_black_dirty = True

        self.is_pipeline_running = False
        self.has_shown_tray_tip = False
        self.tray_icon = None

        self.app_start_time = time.time()
        self.last_full_run_timestamp = 0.0
        self.last_fav_run_timestamp = 0.0

        # 控制变量
        self.port_var = tk.StringVar()
        self.secret_var = tk.StringVar()
        self._cached_port = "9097"
        self._cached_secret = ""
        self.search_var = tk.StringVar()

        self.max_delay_threshold_var = tk.StringVar(value="100")
        self.min_speed_threshold_var = tk.StringVar(value="5.0")
        self.target_node_count_var = tk.StringVar(value="")
        self.blacklist_threshold_var = tk.StringVar(value="130")

        self.speed_bl_threshold_var = tk.StringVar(value="1.0")
        self.speed_bl_rounds_var = tk.StringVar(value="4")

        self.jitter_min_delay_var = tk.StringVar(value="80")
        self.jitter_up_threshold_var = tk.StringVar(value="20")

        self.test_rounds_var = tk.StringVar(value="4")
        self.test_timeout_var = tk.StringVar(value="1500")
        self.speed_duration_var = tk.StringVar(value="3")

        self.test_url_var = tk.StringVar(value="http://www.msftconnecttest.com/connecttest.txt")
        self.speed_url_var = tk.StringVar(value="https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip")

        self.schedule_enabled_var = tk.BooleanVar(value=False)
        self.schedule_interval_var = tk.StringVar(value="120")
        self.schedule_times_var = tk.StringVar(value="08:00, 13:00, 20:00")
        self.boot_startup_var = tk.BooleanVar(value=check_boot_startup_registry())

        self.group_interval_var = tk.StringVar(value="300")
        self.group_tolerance_var = tk.StringVar(value="20")
        self.star_group_interval_var = tk.StringVar(value="300")
        self.star_group_tolerance_var = tk.StringVar(value="20")

        self.cf_worker_enabled_var = tk.BooleanVar(value=False)
        self.cf_worker_url_var = tk.StringVar(value="https://cf-nodes.douyutvshow.workers.dev/")
        self.cf_worker_token_var = tk.StringVar(value="MySecretToken2026")
        self._cached_cf_enabled = False
        self._cached_cf_url = "https://cf-nodes.douyutvshow.workers.dev/"
        self._cached_cf_token = "MySecretToken2026"
        self._is_initialized = False

        self.fav_max_delay_var = tk.StringVar(value="80")
        self.fav_min_speed_var = tk.StringVar(value="8.0")
        self.fav_rounds_var = tk.StringVar(value="2")
        self.fav_speed_duration_var = tk.StringVar(value="2")

        self.fav_jitter_min_delay_var = tk.StringVar(value="70")
        self.fav_jitter_up_threshold_var = tk.StringVar(value="15")

        self.fav_schedule_enabled_var = tk.BooleanVar(value=False)
        self.fav_schedule_interval_var = tk.StringVar(value="60")
        self.fav_target_hk_count_var = tk.StringVar(value="3")
        self.fav_target_nohk_count_var = tk.StringVar(value="5")

        self.fav_quota_early_stop_var = tk.BooleanVar(value=True)
        self.fav_fallback_enabled_var = tk.BooleanVar(value=True)

        self.incubate_hours_var = tk.StringVar(value="24")
        self.incubate_passes_var = tk.StringVar(value="5")

        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.clash_client = ClashClient(host="127.0.0.1", port=9097, secret="")
        self.state = StateManager()

        self.apply_theme_styles()
        self.setup_ui()
        self.setup_context_menus()
        self.load_persisted_config()
        self.auto_read_config()
        self.load_profile_data()
        self.align_favorites_with_current_subscription()
        self.purge_invalid_and_blacklisted_from_all_pools()
        self.save_persisted_config()
        self.do_write_script_file(list(self.favorites))

        self.root.protocol("WM_DELETE_WINDOW", self.hide_to_tray)

        self.test_connection(auto_sync=False)
        self.clear_test_history(silent=True)
        self.update_last_run_display()

        if TRAY_SUPPORTED:
            self.setup_tray_icon()
        else:
            self.sched_status_label.config(text="未检测到 pystray，托盘未加载", fg=THEME["accent_yellow"])

        self.log("系统就绪：已开启 7 天滑动 Colo 历史追踪与防漂移拦截。")
        self._is_initialized = True
        threading.Thread(target=self._scheduler_daemon_loop, daemon=True).start()

    def log(self, message):
        now_str = time.strftime("%H:%M:%S")
        formatted = f"[{now_str}] {message}"
        try:
            self.root.after(0, lambda: self._append_log_text(formatted))
        except Exception:
            pass

    def _append_log_text(self, text_line):
        if not hasattr(self, "log_text"):
            return
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, text_line + "\n")
        lines = int(self.log_text.index("end-1c").split(".")[0])
        if lines > 400:
            self.log_text.delete("1.0", "100.0")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    # ==================== 7 天滑动 Colo 历史桶与分析算法 ====================
    def record_colo_sample(self, node_name, endpoint, c_code, c_disp):
        record_colo_sample(
            self.node_colo_history,
            node_name,
            endpoint,
            c_code,
            c_disp,
            node_colo_dict=self.node_colo,
        )

        disp_to_set = c_disp if (c_disp and c_disp != "-") else (c_code if c_code and c_code != "-" else "-")

        # 确保所有共享该物理端点的同名/别名节点的最新 Colo 同步刷新
        if endpoint and hasattr(self, "all_nodes"):
            for n in self.all_nodes:
                if self.get_node_endpoint(n) == endpoint:
                    if disp_to_set != "-" or n not in self.node_colo:
                        self.node_colo[n] = disp_to_set

        # 同步更新沉淀孵化池与典藏管理池对应项
        if endpoint and hasattr(self, "verified_nodes") and endpoint in self.verified_nodes:
            if disp_to_set != "-" or self.verified_nodes[endpoint].get("colo", "-") == "-":
                self.verified_nodes[endpoint]["colo"] = disp_to_set

        if hasattr(self, "stars_nodes"):
            for s_node in self.stars_nodes:
                if s_node.get("endpoint") == endpoint or (node_name and s_node.get("matched_name") == node_name):
                    if disp_to_set != "-" or s_node.get("colo", "-") == "-":
                        s_node["colo"] = disp_to_set

    def analyze_colo_stats(self, history_list, now=None, node_name=None):
        return analyze_colo_stats(history_list, now=now, node_name=node_name)

    def is_node_hongkong(self, node_name):
        return is_node_hongkong(node_name)

    def is_asian_node(self, node_name, colo=None):
        if not colo:
            ep = self.get_node_endpoint(node_name)
            colo = self.node_colo.get(node_name, self.node_colo.get(ep, "-"))
        return is_asian_node(node_name, colo=colo)

    def auto_filter_and_blacklist_non_asia_nodes(self):
        cnt, _ = auto_filter_and_blacklist_non_asia_nodes(
            self.all_nodes,
            self.local_blacklist,
            self.favorites,
            self.blacklist_reasons,
            self.get_node_endpoint,
            self.is_asian_node,
            node_colo_dict=self.node_colo,
        )
        if cnt > 0:
            self.save_persisted_config()
            self.root.after(0, self.refresh_tables)

    def audit_untested_against_history(self):
        """全面审计待测池：对已有历史测试记录且未达标的节点进行合规归类，杜绝已测不合格节点滞留待测池。
        1. 若节点历史延迟均 > max_delay 或超时，直接归入延迟黑名单，并拉黑物理端点
        2. 若节点历史测速存在且 < min_speed，直接归入低速黑名单，并拉黑物理端点
        返回归类淘汰的节点数量
        """
        try:
            max_d = int(self.max_delay_threshold_var.get().strip()) if self.max_delay_threshold_var.get().strip().isdigit() else 100
        except Exception:
            max_d = 100
        try:
            min_s = float(self.min_speed_threshold_var.get().strip()) if self.min_speed_threshold_var.get().strip() else 5.0
        except Exception:
            min_s = 5.0

        fav_eps, bl_eps, sbl_eps, star_eps = self.get_pool_endpoint_sets()
        audited_delay_cnt = 0
        audited_speed_cnt = 0

        for n in list(self.all_nodes):
            ep = self.get_node_endpoint(n)
            # 已在精选、黑名单、孵化、典藏中的跳过
            if (n in self.favorites) or (ep and ep in fav_eps):
                continue
            if (n in self.local_blacklist) or (ep and ep in bl_eps):
                continue
            if (n in self.speed_blacklist) or (ep and ep in sbl_eps):
                continue
            if (n in getattr(self, "verified_nodes", {})) or (ep and ep in star_eps):
                continue

            # 检查是否有历史延迟记录 (优先物理端点)
            hist_d_items = []
            if ep and ep in self.node_delay_history:
                hist_d_items = self.node_delay_history[ep]
            elif n in self.node_delay_history:
                hist_d_items = self.node_delay_history[n]

            valid_d = [x.get("d") for x in hist_d_items if isinstance(x, dict) and 0 < x.get("d", 0) < 99999]
            if valid_d:
                best_d = min(valid_d)
                if best_d > max_d:
                    d_reason = f"延迟超标 ({best_d}ms > {max_d}ms)"
                    self.local_blacklist.add(n)
                    self.record_blacklist_reason(n, d_reason)
                    if ep:
                        self.local_blacklist.add(ep)
                        self.record_blacklist_reason(ep, d_reason)
                    audited_delay_cnt += 1
                    continue

            # 检查是否有历史下行测速记录
            spd_hist = self.node_speed_history.get(n, self.node_speed_history.get(ep, []))
            valid_s = [s for s in spd_hist if isinstance(s, (int, float))]
            if valid_s:
                best_s = max(valid_s)
                if best_s < min_s:
                    s_reason = "下行测速失败" if best_s < 0 else f"下行未达标 ({best_s:.2f} < {min_s} MB/s)"
                    self.speed_blacklist.add(n)
                    self.record_blacklist_reason(n, s_reason)
                    if ep:
                        self.speed_blacklist.add(ep)
                        self.record_blacklist_reason(ep, s_reason)
                    audited_speed_cnt += 1
                    continue

        tot_audited = audited_delay_cnt + audited_speed_cnt
        if tot_audited > 0:
            self.save_persisted_config()
            self.log(f"📋【待测池历史归类】已将历史不合格节点自动归入黑名单: 延迟超标 {audited_delay_cnt} 个，低速 {audited_speed_cnt} 个")
        return tot_audited

    def apply_theme_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("TNotebook", background=THEME["bg_main"], borderwidth=0)
        style.configure(
            "TNotebook.Tab",
            background=THEME["bg_card"],
            foreground=THEME["text_muted"],
            padding=[16, 8],
            font=("Microsoft YaHei UI", 9, "bold"),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", THEME["accent_blue"])],
            foreground=[("selected", "#ffffff")],
        )

        style.configure(
            "Treeview",
            background=THEME["tree_bg"],
            fieldbackground=THEME["tree_bg"],
            foreground=THEME["text_main"],
            rowheight=32,
            borderwidth=0,
            font=("Microsoft YaHei UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=THEME["bg_card"],
            foreground=THEME["text_muted"],
            relief="flat",
            padding=[8, 8],
            font=("Microsoft YaHei UI", 9, "bold"),
        )
        style.map(
            "Treeview.Heading",
            background=[("active", THEME["bg_hover"])],
            foreground=[("active", THEME["text_main"])],
        )
        style.map(
            "Treeview",
            background=[("selected", THEME["tree_selected"])],
            foreground=[("selected", "#38bdf8")],
        )

        style.configure(
            "Vertical.TScrollbar",
            background=THEME["bg_card"],
            troughcolor=THEME["bg_main"],
            borderwidth=0,
            arrowsize=10,
        )

        style.configure(
            "TCombobox",
            fieldbackground=THEME["bg_input"],
            background=THEME["bg_card"],
            foreground=THEME["text_main"],
            arrowcolor=THEME["text_muted"],
            borderwidth=1,
            relief="flat",
        )
        self.root.option_add("*TCombobox*Listbox.background", THEME["bg_card"])
        self.root.option_add("*TCombobox*Listbox.foreground", THEME["text_main"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", THEME["accent_blue"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        self.root.option_add("*TCombobox*Listbox.font", ("Microsoft YaHei UI", 9))

    def update_last_run_display(self):
        full_str = time.strftime("%m-%d %H:%M:%S", time.localtime(self.last_full_run_timestamp)) if self.last_full_run_timestamp > 0 else "未运行"
        fav_str = time.strftime("%m-%d %H:%M:%S", time.localtime(self.last_fav_run_timestamp)) if self.last_fav_run_timestamp > 0 else "未运行"
        self.last_time_label.config(text=f"🕒 上次检测  全量: {full_str}  |  复检: {fav_str}")

    def load_persisted_config(self):
        data = safe_load_config(CONFIG_STORAGE_PATH)
        if not data:
            return
        try:
            self.max_delay_threshold_var.set(data.get("max_delay", "100"))
            self.min_speed_threshold_var.set(data.get("min_speed", "5.0"))
            self.target_node_count_var.set(data.get("target_count", ""))
            self.blacklist_threshold_var.set(data.get("blacklist_threshold", "130"))

            self.speed_bl_threshold_var.set(data.get("speed_bl_threshold", "1.0"))
            self.speed_bl_rounds_var.set(data.get("speed_bl_rounds", "4"))
            self.jitter_min_delay_var.set(data.get("jitter_min_delay", "80"))
            self.jitter_up_threshold_var.set(data.get("jitter_up_threshold", "20"))

            self.test_rounds_var.set(data.get("test_rounds", "4"))
            self.test_timeout_var.set(data.get("test_timeout", "1500"))
            self.speed_duration_var.set(data.get("speed_duration", "3"))
            self.test_url_var.set(data.get("test_url", "http://www.msftconnecttest.com/connecttest.txt"))
            self.speed_url_var.set(data.get("speed_url", "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip"))
            self.schedule_enabled_var.set(data.get("schedule_enabled", False))
            self.schedule_interval_var.set(data.get("schedule_interval", "120"))
            self.schedule_times_var.set(data.get("schedule_times", "08:00, 13:00, 20:00"))

            self.group_interval_var.set(data.get("group_interval", "300"))
            self.group_tolerance_var.set(data.get("group_tolerance", "20"))
            self.star_group_interval_var.set(data.get("star_group_interval", "300"))
            self.star_group_tolerance_var.set(data.get("star_group_tolerance", "20"))

            cf_en = data.get("cf_worker_enabled", False)
            cf_u = data.get("cf_worker_url", "https://cf-nodes.douyutvshow.workers.dev/")
            cf_tok = data.get("cf_worker_token", "MySecretToken2026")
            self.cf_worker_enabled_var.set(cf_en)
            self.cf_worker_url_var.set(cf_u)
            self.cf_worker_token_var.set(cf_tok)
            self._cached_cf_enabled = bool(cf_en)
            self._cached_cf_url = str(cf_u).strip()
            self._cached_cf_token = str(cf_tok).strip()

            self.fav_max_delay_var.set(data.get("fav_max_delay", "80"))
            self.fav_min_speed_var.set(data.get("fav_min_speed", "8.0"))
            self.fav_rounds_var.set(data.get("fav_rounds", "2"))
            self.fav_speed_duration_var.set(data.get("fav_speed_duration", "2"))
            self.fav_jitter_min_delay_var.set(data.get("fav_jitter_min_delay", "70"))
            self.fav_jitter_up_threshold_var.set(data.get("fav_jitter_up_threshold", "15"))

            self.fav_schedule_enabled_var.set(data.get("fav_schedule_enabled", False))
            self.fav_schedule_interval_var.set(data.get("fav_schedule_interval", "60"))
            self.fav_target_hk_count_var.set(data.get("fav_target_hk_count", "3"))
            self.fav_target_nohk_count_var.set(data.get("fav_target_nohk_count", "5"))

            self.fav_quota_early_stop_var.set(data.get("fav_quota_early_stop", True))
            self.fav_fallback_enabled_var.set(data.get("fav_fallback_enabled", True))

            self.incubate_hours_var.set(data.get("incubate_hours", "24"))
            self.incubate_passes_var.set(data.get("incubate_passes", "5"))

            self.last_full_run_timestamp = float(data.get("last_full_run_timestamp", 0.0))
            self.last_fav_run_timestamp = float(data.get("last_fav_run_timestamp", 0.0))

            self.favorites = set(data.get("favorites", []))
            self.local_blacklist = set(data.get("local_blacklist", []))
            self.speed_blacklist = set(data.get("speed_blacklist", []))
            self.blacklist_reasons = data.get("blacklist_reasons", {})
            self.fav_reasons = data.get("fav_reasons", {})
            self.node_speed_history = data.get("node_speed_history", {})
            self.node_colo = data.get("node_colo", {})

            # 兼容并载入带时间戳的 7 天时序桶
            raw_colo_hist = data.get("node_colo_history", {})
            self.node_colo_history = {}
            now_ts = time.time()
            cutoff = now_ts - 7 * 86400
            for k, v in raw_colo_hist.items():
                if isinstance(v, list):
                    migrated = []
                    for item in v:
                        if isinstance(item, dict) and item.get("ts", 0) >= cutoff:
                            migrated.append(item)
                        elif isinstance(item, str) and item != "-":
                            migrated.append({"ts": now_ts, "colo": item})
                    self.node_colo_history[k] = migrated

            # 载入并清洗7天滑动延迟时序记录
            raw_delay_hist = data.get("node_delay_history", {})
            self.node_delay_history = {}
            for k, v in raw_delay_hist.items():
                if isinstance(v, list):
                    migrated_delays = [
                        item for item in v
                        if isinstance(item, dict) and item.get("ts", 0) >= cutoff and 0 < item.get("d", 0) < 99999
                    ]
                    if migrated_delays:
                        self.node_delay_history[k] = migrated_delays[-30:]

            self.verified_nodes = data.get("verified_nodes", {})
            self.stars_nodes = data.get("stars_nodes", [])
            self.auto_endpoints = set(data.get("auto_endpoints", []))
            self.node_details.update(data.get("node_details", {}))

            self.deduplicate_favorites_by_endpoint()
            self.purge_invalid_and_blacklisted_from_all_pools()
            self.refresh_verified_table()
            self.refresh_stars_table()
            self.audit_untested_against_history()

            self._on_schedule_toggle()
            self._on_fav_schedule_toggle()
        except Exception:
            pass

    def save_persisted_config(self):
        try:
            cfg = {
                "max_delay": self.max_delay_threshold_var.get().strip(),
                "min_speed": self.min_speed_threshold_var.get().strip(),
                "target_count": self.target_node_count_var.get().strip(),
                "blacklist_threshold": self.blacklist_threshold_var.get().strip(),
                "speed_bl_threshold": self.speed_bl_threshold_var.get().strip(),
                "speed_bl_rounds": self.speed_bl_rounds_var.get().strip(),
                "jitter_min_delay": self.jitter_min_delay_var.get().strip(),
                "jitter_up_threshold": self.jitter_up_threshold_var.get().strip(),
                "test_rounds": self.test_rounds_var.get().strip(),
                "test_timeout": self.test_timeout_var.get().strip(),
                "speed_duration": self.speed_duration_var.get().strip(),
                "test_url": self.test_url_var.get().strip(),
                "speed_url": self.speed_url_var.get().strip(),
                "schedule_enabled": self.schedule_enabled_var.get(),
                "schedule_interval": self.schedule_interval_var.get().strip(),
                "schedule_times": self.schedule_times_var.get().strip(),
                "group_interval": self.group_interval_var.get().strip(),
                "group_tolerance": self.group_tolerance_var.get().strip(),
                "star_group_interval": self.star_group_interval_var.get().strip(),
                "star_group_tolerance": self.star_group_tolerance_var.get().strip(),
                "cf_worker_enabled": self.cf_worker_enabled_var.get(),
                "cf_worker_url": self.cf_worker_url_var.get().strip(),
                "cf_worker_token": self.cf_worker_token_var.get().strip(),
                "fav_max_delay": self.fav_max_delay_var.get().strip(),
                "fav_min_speed": self.fav_min_speed_var.get().strip(),
                "fav_rounds": self.fav_rounds_var.get().strip(),
                "fav_speed_duration": self.fav_speed_duration_var.get().strip(),
                "fav_jitter_min_delay": self.fav_jitter_min_delay_var.get().strip(),
                "fav_jitter_up_threshold": self.fav_jitter_up_threshold_var.get().strip(),
                "fav_schedule_enabled": self.fav_schedule_enabled_var.get(),
                "fav_schedule_interval": self.fav_schedule_interval_var.get().strip(),
                "fav_target_hk_count": self.fav_target_hk_count_var.get().strip(),
                "fav_target_nohk_count": self.fav_target_nohk_count_var.get().strip(),
                "fav_quota_early_stop": self.fav_quota_early_stop_var.get(),
                "fav_fallback_enabled": self.fav_fallback_enabled_var.get(),
                "incubate_hours": self.incubate_hours_var.get().strip(),
                "incubate_passes": self.incubate_passes_var.get().strip(),
                "last_full_run_timestamp": self.last_full_run_timestamp,
                "last_fav_run_timestamp": self.last_fav_run_timestamp,
                "favorites": list(self.favorites),
                "local_blacklist": list(self.local_blacklist),
                "speed_blacklist": list(self.speed_blacklist),
                "blacklist_reasons": getattr(self, "blacklist_reasons", {}),
                "fav_reasons": getattr(self, "fav_reasons", {}),
                "node_speed_history": self.node_speed_history,
                "node_delay_history": self.node_delay_history,
                "node_colo": self.node_colo,
                "node_colo_history": self.node_colo_history,
                "verified_nodes": self.verified_nodes,
                "stars_nodes": self.stars_nodes,
                "auto_endpoints": list(self.auto_endpoints),
                "node_details": self.node_details,
            }
            ok, err = atomic_save_config(CONFIG_STORAGE_PATH, cfg)
            if not ok and hasattr(self, "log"):
                self.log(f"⚠️ 配置文件原子写入警告: {err}")
        except Exception:
            pass

    def on_boot_toggle(self):
        val = self.boot_startup_var.get()
        ok, err = set_boot_startup_registry(val)
        if ok:
            msg = "已开启开机静默后台运行！" if val else "已关闭开机自启动。"
            self.status_label.config(text=msg)
            self.log(msg)
        else:
            messagebox.showerror("设置失败", f"开机注册表设置失败：\n{err}")
            self.boot_startup_var.set(not val)

    def _safe_var_get(self, var_name, default=False):
        try:
            v = getattr(self, var_name, None)
            if v is not None:
                return bool(v.get())
        except Exception:
            pass
        return default

    def setup_tray_icon(self):
        menu = pystray.Menu(
            pystray.MenuItem("打开主窗口", self.show_from_tray, default=True),
            pystray.MenuItem("🚀 立即执行一次全局优选", lambda: self.root.after(0, self.start_full_auto_pipeline)),
            pystray.MenuItem("⚡ 立即执行优质池复检", lambda: self.root.after(0, self.start_fav_review_pipeline)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "开机静默自启",
                self._toggle_boot_from_tray,
                checked=lambda item: self._safe_var_get("boot_startup_var"),
            ),
            pystray.MenuItem(
                "全局定时优选",
                self._toggle_sched_from_tray,
                checked=lambda item: self._safe_var_get("schedule_enabled_var"),
            ),
            pystray.MenuItem(
                "优质定时复检",
                self._toggle_fav_sched_from_tray,
                checked=lambda item: self._safe_var_get("fav_schedule_enabled_var"),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("完全退出", self.quit_app),
        )
        self.tray_icon = pystray.Icon(
            "ClashVergeNodeAssistant",
            create_tray_icon_image(),
            "Clash Verge 节点助手",
            menu,
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _toggle_boot_from_tray(self):
        cur = self.boot_startup_var.get()
        self.root.after(0, lambda: [self.boot_startup_var.set(not cur), self.on_boot_toggle()])

    def _toggle_sched_from_tray(self):
        cur = self.schedule_enabled_var.get()
        self.root.after(0, lambda: [self.schedule_enabled_var.set(not cur), self.save_persisted_config(), self._on_schedule_toggle()])

    def _toggle_fav_sched_from_tray(self):
        cur = self.fav_schedule_enabled_var.get()
        self.root.after(0, lambda: [self.fav_schedule_enabled_var.set(not cur), self.save_persisted_config(), self._on_fav_schedule_toggle()])

    def hide_to_tray(self):
        self.save_persisted_config()
        if not TRAY_SUPPORTED:
            self.root.destroy()
            return

        self.root.withdraw()
        if not self.has_shown_tray_tip:
            self.has_shown_tray_tip = True
            send_system_notification("节点助手已隐藏到后台", "程序已最小化到系统托盘，后台监控中。双击托盘图标可打开窗口。")

    def show_from_tray(self):
        self.root.after(0, self._restore_window)

    def _restore_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_app(self):
        self.save_persisted_config()
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def auto_read_config(self):
        port, secret = ClashClient.auto_detect_credentials()
        self.port_var.set(str(port))
        self.secret_var.set(secret)
        self.clash_client.update_credentials(port, secret)

    def test_connection(self, auto_sync=False):
        port = self.port_var.get().strip()
        secret = self.secret_var.get().strip()
        self.clash_client.update_credentials(port, secret)
        ok, ver = self.clash_client.test_connection()
        if ok:
            self.conn_label.config(text=f"● 内核已联动 ({port})", fg=THEME["accent_green"])
            if auto_sync:
                threading.Thread(target=self.sync_existing_delays, daemon=True).start()
            return True
        self.conn_label.config(text="○ 未连接内核", fg=THEME["accent_red"])
        return False

    def _call_api(self, endpoint, timeout=2.5, method="GET", data=None):
        try:
            port = self.port_var.get().strip() if hasattr(self, "port_var") else "9097"
            self._cached_port = port
        except Exception:
            port = getattr(self, "_cached_port", "9097")
        try:
            secret = self.secret_var.get().strip() if hasattr(self, "secret_var") else ""
            self._cached_secret = secret
        except Exception:
            secret = getattr(self, "_cached_secret", "")

        self.clash_client.update_credentials(port, secret)
        return self.clash_client.call_api(endpoint, timeout=timeout, method=method, data=data)

    def get_clash_mixed_port(self):
        return self.clash_client.get_mixed_port(default=7897)

    def wait_for_kernel_reload(self, target_nodes, max_wait_sec=15):
        return self.clash_client.wait_for_kernel_reload(target_nodes, max_wait_sec=max_wait_sec)

    def extract_nodes_and_details_from_file(self, filepath):
        return extract_nodes_and_details_from_file(filepath)

    def resolve_node_to_current(self, target_key):
        return resolve_node_to_current(
            target_key,
            all_nodes=getattr(self, "all_nodes", []),
            node_details=getattr(self, "node_details", {}),
        )

    def choose_canonical_node_name(self, node_list):
        return choose_canonical_node_name(node_list)

    def get_node_endpoint(self, node_name):
        return get_node_endpoint(
            node_name,
            node_details=getattr(self, "node_details", None),
            all_nodes=getattr(self, "all_nodes", None),
            verified_nodes=getattr(self, "verified_nodes", None),
            clash_client=getattr(self, "clash_client", None),
        )
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

    def get_node_endpoint(self, node_name):
        if not node_name:
            return ""

        # 1. 节点名本身直接就是 IP:端口格式 (如 '1.2.3.4:443')
        node_name_clean = str(node_name).strip()
        if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}$", node_name_clean):
            return node_name_clean

        # 2. 如果包含 '#'（如 Worker 节点文本 '1.2.3.4:443#香港 10MB/s'）
        if "#" in node_name_clean:
            prefix = node_name_clean.split("#", 1)[0].strip()
            m_pre = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})$", prefix)
            if m_pre:
                return f"{m_pre.group(1)}:{m_pre.group(2)}"

        # 3. 从当前已解析的 node_details 字典查找
        info = self.node_details.get(node_name, {})
        server = info.get("server", "").strip()
        port = str(info.get("port", "443")).strip()
        if server:
            return f"{server}:{port}"

        # 4. 从节点名中正则直接提取完整 IPv4 及端口 (如 '辣子鸡优选 | 多哥 TG | 129.154.50.72:8443')
        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{2,5}))?", node_name_clean)
        if m:
            ip = m.group(1)
            p = m.group(2) if m.group(2) else "443"
            return f"{ip}:{p}"

        # 5. 检查沉淀孵化池/典藏常青池已有物理端点记录
        if node_name in getattr(self, "verified_nodes", {}):
            v_ep = self.verified_nodes[node_name].get("endpoint", "")
            if v_ep:
                return v_ep

        # 6. 仅当该节点活跃在当前 Clash 配置中时，尝试内核 API 查询并缓存
        if getattr(self, "all_nodes", None) and node_name in self.all_nodes:
            try:
                enc = urllib.parse.quote(node_name, safe="")
                res = self._call_api(f"/proxies/{enc}", timeout=0.3)
                if res and isinstance(res, dict):
                    s = res.get("server", "").strip()
                    p = str(res.get("port", "443")).strip()
                    if s:
                        self.node_details[node_name] = {"server": s, "port": p}
                        return f"{s}:{p}"
            except Exception:
                pass

        return ""

    def get_pool_endpoint_sets(self):
        return get_pool_endpoint_sets(
            self.favorites,
            self.local_blacklist,
            self.speed_blacklist,
            getattr(self, "auto_endpoints", set()),
            getattr(self, "verified_nodes", {}),
            getattr(self, "stars_nodes", []),
            self.get_node_endpoint,
        )

    def fetch_auto_endpoints_from_cloud(self):
        """尝试从 Worker /auto.txt 获取云端保活的端点集合"""
        try:
            _, base_url, token = self.get_cf_worker_config()
            if not base_url or not base_url.startswith("http"):
                return set()
            auto_url = f"{base_url.rstrip('/')}/auto.txt"
            mixed_port = self.get_clash_mixed_port()
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            proxy_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
            direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))

            headers = {
                "Authorization": f"Bearer {token}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            }
            req = urllib.request.Request(auto_url, headers=headers)
            for opener in [proxy_opener, direct_opener]:
                try:
                    with opener.open(req, timeout=5) as resp:
                        if resp.status == 200:
                            content = resp.read().decode("utf-8", errors="ignore")
                            eps = set()
                            for line in content.splitlines():
                                line = line.strip()
                                if not line or line.startswith("⏳") or line.startswith("Error"):
                                    continue
                                ep_part = line.split("#")[0].strip() if "#" in line else line.split()[0].strip()
                                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", ep_part)
                                if m:
                                    eps.add(m.group(1))
                            if eps:
                                return eps
                except Exception:
                    continue
        except Exception:
            pass
        return set()

    def get_cf_worker_config(self):
        """安全获取 Worker 配置，主线程与后台子线程均兼容，彻底避免 'main thread is not in main loop' 异常"""
        try:
            enabled = bool(self.cf_worker_enabled_var.get())
            self._cached_cf_enabled = enabled
        except Exception:
            enabled = getattr(self, "_cached_cf_enabled", False)

        try:
            url = self.cf_worker_url_var.get().strip()
            self._cached_cf_url = url
        except Exception:
            url = getattr(self, "_cached_cf_url", "https://cf-nodes.douyutvshow.workers.dev/")

        try:
            token = self.cf_worker_token_var.get().strip()
            self._cached_cf_token = token
        except Exception:
            token = getattr(self, "_cached_cf_token", "MySecretToken2026")

        return enabled, url, token

    def push_text_to_cf_worker(self, text_payload, subpath=""):
        _, base_url, token = self.get_cf_worker_config()
        base_url = base_url.rstrip("/")

        if not base_url or not base_url.startswith("http"):
            return False, "Worker 网址无效"

        # 安全防护：若内容为空或仅包含空白字符，避免向 Worker 发送空请求触发 HTTP 400 Bad Request
        if not text_payload or not text_payload.strip():
            return True, "内容为空，无需推送"

        target_url = f"{base_url}{subpath}" if subpath else f"{base_url}/"

        mixed_port = self.get_clash_mixed_port()
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        proxy_handler = urllib.request.ProxyHandler({
            "http": f"http://127.0.0.1:{mixed_port}",
            "https": f"http://127.0.0.1:{mixed_port}",
        })
        proxy_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
        direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "text/plain; charset=utf-8",
            "User-Agent": "ClashVergeNodeAssistant/1.0",
        }
        req = urllib.request.Request(target_url, data=text_payload.encode("utf-8"), headers=headers, method="POST")

        last_err = ""
        for attempt in range(1, 4):
            for use_proxy, opener in [(True, proxy_opener), (False, direct_opener)]:
                try:
                    with opener.open(req, timeout=10) as resp:
                        if resp.status in (200, 201, 204):
                            channel = f"代理端口:{mixed_port}" if use_proxy else "直连"
                            return True, f"成功推送至 {target_url} ({channel})"
                        last_err = f"Worker 返回状态码: {resp.status}"
                except urllib.error.HTTPError as ex:
                    if ex.code == 401:
                        return False, "认证失败(401)，请确认 AUTH_TOKEN 密钥！"
                    last_err = f"HTTP({ex.code}): {ex.reason}"
                except Exception as ex:
                    last_err = str(ex)
            time.sleep(1.0)

        return False, f"重试失败: {last_err}"

    def sync_premium_nodes_to_cf_worker(self, premium_nodes, subpath="/auto.txt"):
        lines = []
        seen_eps = set()
        for n in premium_nodes:
            endpoint = self.get_node_endpoint(n)
            if not endpoint or endpoint in seen_eps:
                continue
            seen_eps.add(endpoint)
            region = self.node_colo.get(n, detect_node_region(n))
            spd = self.node_speeds.get(n, 0.0)
            lines.append(f"{endpoint}#{region} {spd:.2f} MB/s")
        if not lines:
            return True, "本地优质池为空，跳过推送"
        return self.push_text_to_cf_worker("\r\n".join(lines) + "\r\n", subpath)

    def sync_all_pools_to_cf_worker(self):
        """
        全量同步推送当前三大池（优质精选池、沉淀孵化池、典藏常青池）至 Cloudflare Worker 远端文本。
        远端对应路径：
        1. /auto.txt      -> 优质精选池 (favorites)
        2. /verified.txt  -> 沉淀孵化池 (verified_nodes)
        3. /              -> 典藏常青池 (stars_nodes)
        任何不合规/被淘汰/拉黑的节点在此处均已被完全清洗排除，保证远端彻底同步净化。
        """
        enabled, base_url, token = self.get_cf_worker_config()
        if not enabled:
            return False, "Worker 推送开关未开启"
        if not base_url or not token:
            return False, "未配置 Worker 地址或授权密钥"

        # 1. 优质精选池 -> /auto.txt
        auto_ok, auto_msg = self.sync_premium_nodes_to_cf_worker(list(self.favorites), subpath="/auto.txt")
        self.log(f"Worker 优质池同步 (/auto.txt): {auto_msg}")

        # 2. 沉淀孵化池 -> /verified.txt
        ver_lines = []
        for v in self.verified_nodes.values():
            ep = v.get("endpoint", "")
            rem = v.get("remark", "优质沉淀")
            if ep:
                ver_lines.append(f"{ep}#{rem}")
        if ver_lines:
            ver_payload = "\r\n".join(ver_lines) + "\r\n"
            ver_ok, ver_msg = self.push_text_to_cf_worker(ver_payload, "/verified.txt")
            self.log(f"Worker 沉淀池同步 (/verified.txt): {ver_msg}")
        else:
            ver_ok = True
            self.log("Worker 沉淀池同步 (/verified.txt): 本地沉淀池为空，无需推送")

        # 3. 典藏常青池 -> / (根目录)
        star_lines = []
        for s in self.stars_nodes:
            ep = s.get("endpoint", "")
            rem = s.get("remark", "典藏常青")
            if ep:
                star_lines.append(f"{ep}#{rem}")
        if star_lines:
            star_payload = "\r\n".join(star_lines) + "\r\n"
            star_ok, star_msg = self.push_text_to_cf_worker(star_payload, "")
            self.log(f"Worker 典藏池同步 (/): {star_msg}")
        else:
            star_ok = True
            self.log("Worker 典藏池同步 (/): 本地典藏池为空，无需推送")

        all_ok = auto_ok and ver_ok and star_ok
        return all_ok, f"优质池:{auto_ok}, 沉淀池:{ver_ok}, 典藏池:{star_ok}"

    def record_blacklist_reason(self, name_or_ep, reason):
        if not hasattr(self, "blacklist_reasons") or not isinstance(self.blacklist_reasons, dict):
            self.blacklist_reasons = {}
        if not name_or_ep or not reason:
            return
        self.blacklist_reasons[name_or_ep] = reason
        ep = self.get_node_endpoint(name_or_ep) if hasattr(self, "get_node_endpoint") else ""
        if ep:
            self.blacklist_reasons[ep] = reason
            if ":" in ep:
                self.blacklist_reasons[ep.split(":")[0]] = reason

    def get_blacklist_reason(self, node_name, ep=None):
        if not hasattr(self, "blacklist_reasons") or not isinstance(self.blacklist_reasons, dict):
            self.blacklist_reasons = {}
        if not ep and node_name:
            ep = self.get_node_endpoint(node_name) if hasattr(self, "get_node_endpoint") else ""

        # 1. 优先从显式记录字典中提取
        if node_name and node_name in self.blacklist_reasons:
            return self.blacklist_reasons[node_name]
        if ep and ep in self.blacklist_reasons:
            return self.blacklist_reasons[ep]
        if ep and ":" in ep:
            ip = ep.split(":")[0]
            if ip in self.blacklist_reasons:
                return self.blacklist_reasons[ip]

        # 2. 智能自动推导（兜底历史遗留数据或未显式传参场景）
        ep_val = ep or (self.get_node_endpoint(node_name) if hasattr(self, "get_node_endpoint") else "")

        # 2.1 如果位于低速黑名单，优先推导下行测速原因
        is_s_black = (node_name in self.speed_blacklist) or (ep_val and ep_val in self.speed_blacklist)
        if is_s_black:
            s_val = self.node_speeds.get(node_name, None)
            if s_val is not None:
                if s_val < 0:
                    return "下行测速失败/中断"
                return f"下行过低 ({s_val:.2f} MB/s)"
            s_hist = self.node_speed_history.get(node_name, [])
            if s_hist:
                last_s = s_hist[-1]
                if last_s < 0:
                    return "下行测速中断"
                return f"下行过低 ({last_s:.2f} MB/s)"
            return "下行低速淘汰"

        # 2.2 检查机房漂移
        colo_hist = self.node_colo_history.get(node_name, self.node_colo_history.get(ep_val, []))
        if colo_hist:
            _, _, has_drift, drift_disp = self.analyze_colo_stats(colo_hist, time.time(), node_name=node_name)
            if has_drift:
                return f"机房漂移 ({drift_disp})"

        # 2.3 延迟数据判定（超时）
        d_val = self.node_delays.get(node_name, None)
        if d_val is not None and d_val >= 99999:
            return "延迟超时 (≥99999ms)"
        d_hist = self.node_history.get(node_name, [])
        if d_hist and d_hist[-1] >= 99999:
            return "延迟超时 (≥99999ms)"

        # 2.4 非亚洲地区/机房判定
        if node_name and not self.is_asian_node(node_name):
            colo_val = self.node_colo.get(ep_val, self.node_colo.get(node_name, ""))
            if colo_val and colo_val != "-":
                return f"非亚洲机房 ({colo_val})"
            return "非亚洲地区/命名"

        # 2.5 延迟黑名单其它超标情况
        is_d_black = (node_name in self.local_blacklist) or (ep_val and ep_val in self.local_blacklist)
        if is_d_black:
            if d_val is not None:
                return f"延迟超标 ({d_val}ms)"
            if d_hist:
                return f"延迟淘汰 ({d_hist[-1]}ms)"
            return "延迟超标淘汰"

        return "-"

    def record_fav_reason(self, name_or_ep, reason, ep=None):
        if not hasattr(self, "fav_reasons") or not isinstance(self.fav_reasons, dict):
            self.fav_reasons = {}
        if not name_or_ep or not reason:
            return
        self.fav_reasons[name_or_ep] = reason
        target_ep = ep or (self.get_node_endpoint(name_or_ep) if hasattr(self, "get_node_endpoint") else "")
        if target_ep:
            self.fav_reasons[target_ep] = reason
            if ":" in target_ep:
                self.fav_reasons[target_ep.split(":")[0]] = reason

    def get_fav_reason(self, node_name, ep=None):
        if not hasattr(self, "fav_reasons") or not isinstance(self.fav_reasons, dict):
            self.fav_reasons = {}
        if not ep and node_name:
            ep = self.get_node_endpoint(node_name) if hasattr(self, "get_node_endpoint") else ""

        # 1. 优先从显式记录字典中提取
        if node_name and node_name in self.fav_reasons:
            return self.fav_reasons[node_name]
        if ep and ep in self.fav_reasons:
            return self.fav_reasons[ep]
        if ep and ":" in ep:
            ip = ep.split(":")[0]
            if ip in self.fav_reasons:
                return self.fav_reasons[ip]

        # 2. 智能自动推导
        # 2.1 检查是否为典藏常青推荐
        star_eps = {st.get("endpoint", "") for st in getattr(self, "stars_nodes", []) if isinstance(st, dict)}
        if ep and ep in star_eps:
            return "典藏常青节点"

        # 2.2 检查是否在沉淀孵化池考核中
        if ep and ep in getattr(self, "verified_nodes", {}):
            v = self.verified_nodes[ep]
            passes = v.get("passes", 1)
            first_seen = v.get("first_seen", time.time())
            alive_h = round((time.time() - first_seen) / 3600.0, 1)
            return f"沉淀考核中 (达标{passes}次/{alive_h}h)"

        # 2.3 基于最新测速与延迟推导
        d_val = self.node_delays.get(node_name, self.node_delays.get(ep, None))
        s_val = self.node_speeds.get(node_name, self.node_speeds.get(ep, None))
        if s_val is not None and s_val > 0 and d_val is not None and d_val < 99999:
            return f"优选达标 ({d_val}ms / {s_val:.2f}MB/s)"
        elif d_val is not None and d_val < 99999:
            return f"延迟优选 ({d_val}ms)"

        return "优质精选"

    def purge_invalid_and_blacklisted_from_all_pools(self):
        return purge_invalid_and_blacklisted_from_all_pools(
            self.favorites,
            getattr(self, "verified_nodes", {}),
            getattr(self, "stars_nodes", []),
            self.local_blacklist,
            self.speed_blacklist,
            self.get_node_endpoint,
        )

    def test_cf_worker_upload(self):
        worker_url = self.cf_worker_url_var.get().strip()
        token = self.cf_worker_token_var.get().strip()

        if not worker_url or not token:
            messagebox.showwarning("提示", "请先填入 Cloudflare Worker 地址和授权密钥！")
            return

        self.save_persisted_config()

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text="正在测试 Cloudflare Worker (/auto.txt)..."))
            sample_nodes = list(self.favorites) if self.favorites else (self.all_nodes[:5] if self.all_nodes else ["测试节点"])
            ok, msg = self.sync_premium_nodes_to_cf_worker(sample_nodes, subpath="/auto.txt")
            if ok:
                auto_url = f"{worker_url.rstrip('/')}/auto.txt"
                self.log(f"Worker 自动池上传验证成功：{msg}")
                self.root.after(0, lambda: messagebox.showinfo(
                    "测试成功",
                    f"🎉 自动优选通道验证成功！\n\n详情：{msg}\n\n可在浏览器打开：\n{auto_url}\n查看纯文本输出。"
                ))
                self.root.after(0, lambda: self.status_label.config(text="Cloudflare Worker 测试成功！"))
            else:
                self.log(f"Worker 测试上传失败：{msg}")
                self.root.after(0, lambda: messagebox.showerror("测试失败", f"❌ 推送失败：\n\n{msg}"))
                self.root.after(0, lambda: self.status_label.config(text="Cloudflare Worker 测试失败"))

        threading.Thread(target=_worker, daemon=True).start()

    def resolve_star_matches(self):
        reverse_map = {}
        for name, info in self.node_details.items():
            s = info.get('server', '').strip()
            p = str(info.get('port', '')).strip()
            if s and p:
                reverse_map[f"{s}:{p}"] = name
                reverse_map[s] = name

        for n in self.all_nodes:
            info = self.node_details.get(n, {})
            s = info.get('server', '').strip()
            p = str(info.get('port', '')).strip()
            if s and p:
                reverse_map[f"{s}:{p}"] = n
                reverse_map[s] = n

        if not reverse_map:
            try:
                data = self._call_api("/proxies", timeout=0.3)
                if data and "proxies" in data:
                    for p_name, p_info in data["proxies"].items():
                        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{2,5}))?", p_name)
                        if m:
                            ip = m.group(1)
                            port = m.group(2) if m.group(2) else "443"
                            reverse_map[f"{ip}:{port}"] = p_name
                            reverse_map[ip] = p_name
            except Exception:
                pass

        return reverse_map

    # ==================== 🔍 C 段全量高并发极速挖掘引擎 ====================
    def open_c_segment_mining_dialog(self, seed_input):
        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?", seed_input)
        if not m:
            messagebox.showwarning("提示", f"未能从【{seed_input}】中识别出合法的 IPv4 地址！")
            return

        seed_ip = m.group(1)
        seed_port = m.group(2) if m.group(2) else "443"
        c_ips = get_c_segment_ips(seed_ip)
        if not c_ips:
            messagebox.showwarning("提示", "无法解析该 IP 的 C 段！")
            return

        c_segment_name = ".".join(seed_ip.split(".")[:3]) + ".0/24"

        dialog = tk.Toplevel(self.root)
        dialog.title(f"🔍 C 段全量极速深度挖掘 - {c_segment_name}")
        dialog.geometry("980x640")
        dialog.configure(bg=THEME["bg_card"])
        dialog.transient(self.root)

        top_f = tk.Frame(dialog, bg=THEME["bg_card"], padx=14, pady=10)
        top_f.pack(fill=tk.X)

        tk.Label(top_f, text=f"网段: {c_segment_name}", fg="#38bdf8", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 10, "bold")).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(top_f, text="端口:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        port_var = tk.StringVar(value=str(seed_port))
        tk.Entry(top_f, textvariable=port_var, width=5, bg=THEME["bg_input"], fg=THEME["text_main"], relief="flat", font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(3, 10))

        tk.Label(top_f, text="延迟门槛(≤ ms):", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        threshold_var = tk.StringVar(value="130")
        tk.Entry(top_f, textvariable=threshold_var, width=4, bg=THEME["bg_input"], fg=THEME["text_main"], relief="flat", font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(3, 10))

        status_lbl = tk.Label(top_f, text="准备就绪 (共 254 个 IP)", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9))
        status_lbl.pack(side=tk.LEFT, padx=10)

        cols = ("ip", "port", "rtt", "colo", "status")
        tree = ttk.Treeview(dialog, columns=cols, show="headings", selectmode="extended")
        tree.heading("ip", text="IP 地址 ↕")
        tree.heading("port", text="端口")
        tree.heading("rtt", text="TCP 握手延迟 ↕")
        tree.heading("colo", text="真实机房 (Colo)")
        tree.heading("status", text="评估状态")

        tree.column("ip", width=160, anchor="center")
        tree.column("port", width=70, anchor="center")
        tree.column("rtt", width=120, anchor="center")
        tree.column("colo", width=180, anchor="center")
        tree.column("status", width=120, anchor="center")

        tree.tag_configure("pass", foreground="#34d399")
        tree.tag_configure("fail", foreground="#f87171")

        btn_sel_none = tk.Button(top_f, text="清空选择", command=lambda: tree.selection_remove(tree.selection()), bg=THEME["bg_input"], fg=THEME["text_muted"], relief="flat", padx=8, pady=1, font=("Microsoft YaHei UI", 8))
        btn_sel_all = tk.Button(top_f, text="全选达标", command=lambda: tree.selection_set(tree.get_children()), bg=THEME["bg_input"], fg="#38bdf8", relief="flat", padx=8, pady=1, font=("Microsoft YaHei UI", 8))
        btn_sel_none.pack(side=tk.RIGHT, padx=4)
        btn_sel_all.pack(side=tk.RIGHT, padx=4)

        tree_frame = tk.Frame(dialog, bg=THEME["bg_main"], padx=2, pady=2)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview, style="Vertical.TScrollbar")
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        bottom_f = tk.Frame(dialog, bg=THEME["bg_card"], padx=14, pady=10)
        bottom_f.pack(fill=tk.X)

        is_running = [False]

        def _start_mining():
            if is_running[0]:
                return
            is_running[0] = True
            btn_start.config(state="disabled", bg=THEME["bg_hover"])
            btn_stop.config(state="normal")
            tree.delete(*tree.get_children())

            p_val = port_var.get().strip()
            t_val = int(threshold_var.get().strip()) if threshold_var.get().strip().isdigit() else 130

            def _worker():
                status_lbl.config(text="正在全并发 TCP 测延...", fg="#fbbf24")
                results = []
                completed = [0]

                def _scan_one(ip):
                    if not is_running[0]:
                        return
                    rtt = tcp_ping(ip, p_val, timeout=1.2)
                    results.append((ip, rtt))
                    completed[0] += 1
                    if completed[0] % 10 == 0 or completed[0] == len(c_ips):
                        dialog.after(0, lambda c=completed[0]: status_lbl.config(text=f"TCP 测延中: {c}/254"))

                with ThreadPoolExecutor(max_workers=50) as ex:
                    list(ex.map(_scan_one, c_ips))

                if not is_running[0]:
                    dialog.after(0, lambda: status_lbl.config(text="扫描已中止", fg=THEME["text_muted"]))
                    return

                alive_results = [r for r in results if r[1] <= t_val]
                status_lbl.config(text=f"TCP 达标 {len(alive_results)} 个，正在校准真实 Colo...", fg="#38bdf8")

                colo_map = {}
                def _colo_one(ip):
                    if not is_running[0]:
                        return
                    c_code, c_disp = get_cf_colo_raw(ip, p_val, timeout=1.5)
                    colo_map[ip] = (c_code, c_disp)

                with ThreadPoolExecutor(max_workers=20) as ex:
                    list(ex.map(_colo_one, [r[0] for r in alive_results]))

                alive_results.sort(key=lambda x: x[1])

                def _render():
                    for ip, rtt in alive_results:
                        _, c_disp = colo_map.get(ip, ("-", "-"))
                        tree.insert("", tk.END, values=(ip, p_val, f"{rtt} ms", c_disp, "✅ 极速达标"), tags=["pass"])
                    status_lbl.config(text=f"挖掘完成！共发现 {len(alive_results)} 个极速纯净 IP", fg=THEME["accent_green"])
                    btn_start.config(state="normal", bg=THEME["accent_green"])
                    btn_stop.config(state="disabled")
                    is_running[0] = False

                dialog.after(0, _render)

            threading.Thread(target=_worker, daemon=True).start()

        def _stop_mining():
            is_running[0] = False
            btn_stop.config(state="disabled")
            status_lbl.config(text="正在停止...", fg=THEME["text_muted"])

        def _import_to_pool(target="verified"):
            if is_running[0]:
                _stop_mining()
                time.sleep(0.3)

            all_children = tree.get_children()
            if not all_children:
                messagebox.showwarning("提示", "当前无挖掘结果可导入！", parent=dialog)
                return

            sel = tree.selection()
            if sel and len(sel) < len(all_children):
                ans = messagebox.askyesnocancel(
                    "导入范围确认",
                    f"检测到您当前选中了 {len(sel)} 行（全表共 {len(all_children)} 个达标节点）。\n\n"
                    f"• 点击【是 (Yes)】：仅导入当前选中的 {len(sel)} 个节点\n"
                    f"• 点击【否 (No)】：一键全选并导入全部 {len(all_children)} 个达标节点 (推荐)\n"
                    f"• 点击【取消】：取消本次导入",
                    parent=dialog
                )
                if ans is None:
                    return
                rows_to_import = sel if ans else all_children
            else:
                rows_to_import = all_children

            btn_import_fav.config(state="disabled")
            btn_import_verified.config(state="disabled")
            btn_import_stars.config(state="disabled")

            cnt = 0
            reverse_map = self.resolve_star_matches()
            now_ts = time.time()

            for r in rows_to_import:
                vals = tree.item(r, "values")
                ip, port, rtt, colo, _ = vals
                ep = f"{ip}:{port}"
                rem = f"{colo} [C段挖掘] {rtt}"

                is_asia = False
                if rem and self.is_asian_node(rem, colo):
                    is_asia = True
                elif colo and colo != "-" and self.is_asian_node(ep, colo):
                    is_asia = True
                elif ep and self.is_asian_node(ep, colo):
                    is_asia = True

                if not is_asia:
                    self.local_blacklist.add(ep)
                    continue

                try:
                    clean_rtt = int(rtt.replace(" ms", "").strip())
                except Exception:
                    clean_rtt = 0

                if colo and colo != "-":
                    c_code = colo.split()[-1] if " " in colo else colo
                    self.record_colo_sample(None, ep, c_code, colo)

                if target == "verified":
                    if ep not in self.verified_nodes:
                        self.verified_nodes[ep] = {
                            "endpoint": ep,
                            "colo": colo,
                            "remark": rem,
                            "first_seen": now_ts,
                            "passes": 1,
                            "fails": 0,
                            "delay": clean_rtt,
                            "speed": 0.0,
                            "reason": "批量手动导入",
                        }
                        cnt += 1
                elif target == "fav":
                    matched_name = reverse_map.get(ep, "")
                    if not matched_name and ":" in ep:
                        matched_name = reverse_map.get(ep.split(":")[0], "")
                    target_name = matched_name if matched_name else ep

                    if not self.is_asian_node(target_name, colo):
                        self.local_blacklist.add(target_name)
                        continue

                    if target_name not in self.favorites:
                        self.favorites.add(target_name)
                        cnt += 1
                    self.record_fav_reason(target_name, "批量手动导入")
                    self.local_blacklist.discard(target_name)
                    self.speed_blacklist.discard(target_name)
                    if ep:
                        self.local_blacklist.discard(ep)
                        self.speed_blacklist.discard(ep)
                    if clean_rtt > 0:
                        self.node_delays[target_name] = clean_rtt
                        self.node_history[target_name] = [clean_rtt]
                    if colo and colo != "-":
                        self.node_colo[target_name] = colo
                else:
                    existing_eps = {s["endpoint"] for s in self.stars_nodes}
                    if ep not in existing_eps:
                        self.stars_nodes.append({
                            "endpoint": ep,
                            "colo": colo,
                            "remark": rem,
                            "delay": clean_rtt,
                            "speed": 0.0,
                            "matched_name": "",
                            "reason": "批量手动导入",
                        })
                        cnt += 1

            if target == "fav":
                self.align_favorites_with_current_subscription()
                self.deduplicate_favorites_by_endpoint()

            self.save_persisted_config()
            self.refresh_tables()
            self.refresh_verified_table()
            self.refresh_stars_table()

            target_names = {
                "verified": "【⏳ 沉淀孵化池】",
                "fav": "【⭐ 优质精选池】",
                "stars": "【🏆 典藏管理池】"
            }
            target_name = target_names.get(target, "目标池")
            self.log(f"已从 C 段挖掘成果中批量收编 {cnt} 个极品 IP 至 {target_name}")

            # 后台全链路自动闭环：Worker 同步 -> 订阅更新 -> 写入 Script.js -> 热键热更新激活 -> 内核重载探测
            def _post_import_worker():
                logs_step = [f"✅ 本地收编: 成功收录 {cnt} 个极品 IP 至 {target_name}"]

                # 步骤 1: 尝试推送至 Cloudflare Worker 云端
                base_url = self.cf_worker_url_var.get().strip().rstrip("/")
                if base_url.startswith("http"):
                    dialog.after(0, lambda: status_lbl.config(text="[1/3] 正在同步推送至 Cloudflare Worker...", fg="#38bdf8"))
                    self.log(f"正在将收编节点同步发布至 Cloudflare Worker...")
                    if target == "verified":
                        lines = [f"{v['endpoint']}#{v['remark']}" for v in self.verified_nodes.values()]
                        ok_w, msg_w = self.push_text_to_cf_worker("\r\n".join(lines) + "\r\n", "/verified.txt")
                    elif target == "fav":
                        ok_w, msg_w = self.sync_premium_nodes_to_cf_worker(list(self.favorites), subpath="/auto.txt")
                    else:
                        lines = [f"{item.get('endpoint', '')}#{item.get('remark', '')}" for item in self.stars_nodes]
                        ok_w, msg_w = self.push_text_to_cf_worker("\r\n".join(lines) + "\r\n", "")

                    if ok_w:
                        logs_step.append("✅ 云端同步: 已成功推送到 Cloudflare Worker")
                        self.log(f"Worker 同步成功: {msg_w}")
                        time.sleep(1.0)
                    else:
                        logs_step.append(f"⚠️ 云端同步: {msg_w}")
                        self.log(f"Worker 同步提示: {msg_w}")
                else:
                    logs_step.append("ℹ️ 云端同步: 未配置 Cloudflare Worker 地址，已保存本地")

                # 步骤 2: 执行订阅更新 (拉取最新 profiles yaml 并重新解析)
                cur_idx = self.file_combo.current()
                cur_file_info = self.file_items[cur_idx] if (cur_idx >= 0 and cur_idx < len(self.file_items)) else None
                if cur_file_info and os.path.exists(cur_file_info["path"]):
                    dialog.after(0, lambda: status_lbl.config(text="[2/3] 正在执行订阅更新 (拉取最新节点)...", fg="#38bdf8"))
                    self.log("正在执行订阅更新拉取...")
                    up_ok, up_msg, content_changed = self.update_remote_subscription(cur_file_info["path"])
                    if up_ok:
                        new_nodes, new_details = self.extract_nodes_and_details_from_file(cur_file_info["path"])
                        if new_nodes:
                            self.all_nodes = new_nodes
                            self.node_details.update(new_details)
                            cur_file_info["nodes"] = new_nodes
                            cur_file_info["details"] = new_details
                            b_cnt = self.auto_filter_and_blacklist_non_asia_nodes()
                            if b_cnt > 0:
                                logs_step.append(f"🛡️ 自动拉黑非亚洲节点: 已直接拉黑淘汰 {b_cnt} 个非亚洲节点")
                            if target == "fav":
                                self.align_favorites_with_current_subscription()
                                self.deduplicate_favorites_by_endpoint()
                        logs_step.append(f"✅ 订阅更新: {up_msg}")
                        self.log(f"订阅更新成功: {up_msg}")
                    else:
                        logs_step.append(f"⚠️ 订阅更新: {up_msg}")
                        self.log(f"订阅更新提示: {up_msg}")
                else:
                    logs_step.append("ℹ️ 订阅更新: 未检测到远程订阅文件，跳过拉取")

                # 步骤 3: 写入 Script.js 并触发热键热更新激活订阅
                dialog.after(0, lambda: status_lbl.config(text="[3/3] 正在写入 Script.js 并热激活订阅...", fg="#38bdf8"))
                write_ok, write_err = self.do_write_script_file(list(self.favorites))
                if write_ok:
                    logs_step.append("✅ 脚本规则: 已重新生成并写入 Script.js 注入规则")
                else:
                    logs_step.append(f"⚠️ 脚本规则: {write_err}")

                time.sleep(0.3)
                hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()
                if hotkey_ok:
                    logs_step.append("✅ 热更激活: 已通过全局热键 (Ctrl+Shift+F12) 激活订阅")
                else:
                    logs_step.append(f"⚠️ 热更激活: {hotkey_msg}")

                # 探测内核重载
                if cur_file_info and self.all_nodes:
                    dialog.after(0, lambda: status_lbl.config(text="正在探测 Clash 内核装载状态...", fg="#38bdf8"))
                    loaded_ok, loaded_msg = self.wait_for_kernel_reload(self.all_nodes, max_wait_sec=10)
                    logs_step.append(f"{'✅' if loaded_ok else '⚠️'} 内核探测: {loaded_msg}")
                    self.log(f"内核探测反馈: {loaded_msg}")

                # 刷新 UI
                self.root.after(0, self.refresh_tables)
                self.root.after(0, self.refresh_verified_table)
                self.root.after(0, self.refresh_stars_table)

                def _finish_ui():
                    btn_import_fav.config(state="normal")
                    btn_import_verified.config(state="normal")
                    btn_import_stars.config(state="normal")
                    status_lbl.config(text=f"收编与热激活完成！共收编 {cnt} 个 IP", fg=THEME["accent_green"])
                    self.status_label.config(text=f"C段收编完成：已成功收编 {cnt} 个 IP 至 {target_name} 并完成热更激活")
                    messagebox.showinfo(
                        "收编与热激活成功",
                        f"🎉 批量收编与热更新全流程已顺利完成！\n\n" + "\n".join(logs_step) + "\n\n软件与 Clash Verge 已成功读取并装载最新的节点与订阅！",
                        parent=dialog
                    )

                dialog.after(0, _finish_ui)

            threading.Thread(target=_post_import_worker, daemon=True).start()

        btn_start = create_modern_btn(bottom_f, text="🚀 开始极速挖掘", command=_start_mining, bg=THEME["accent_green"], hover_bg=THEME["accent_green_hover"])
        btn_start.pack(side=tk.LEFT, padx=4)

        btn_stop = create_modern_btn(bottom_f, text="⏹ 停止", command=_stop_mining, bg=THEME["bg_hover"], hover_bg=THEME["accent_red"], state="disabled")
        btn_stop.pack(side=tk.LEFT, padx=4)

        btn_import_stars = create_modern_btn(bottom_f, text="📥 批量导入至【🏆 典藏管理池】", command=lambda: _import_to_pool("stars"), bg="#b45309", hover_bg="#d97706")
        btn_import_stars.pack(side=tk.RIGHT, padx=4)

        btn_import_verified = create_modern_btn(bottom_f, text="📥 批量导入至【⏳ 沉淀孵化池】", command=lambda: _import_to_pool("verified"), bg=THEME["accent_cyan"], hover_bg=THEME["accent_cyan_hover"])
        btn_import_verified.pack(side=tk.RIGHT, padx=4)

        btn_import_fav = create_modern_btn(bottom_f, text="📥 批量导入至【⭐ 优质精选池】", command=lambda: _import_to_pool("fav"), bg=THEME["accent_blue"], hover_bg=THEME["accent_blue_hover"])
        btn_import_fav.pack(side=tk.RIGHT, padx=4)

    # ==================== ⏳ 沉淀孵化池与防漂移考核闭环 ====================
    def refresh_verified_table(self):
        if "verified" not in self.trees:
            return
        tree = self.trees["verified"]
        tree.delete(*tree.get_children())

        # 核心铁律：沉淀孵化池必须是优质精选池的严格子集（沉淀孵化 ⊆ 优质精选）
        fav_eps = {self.get_node_endpoint(f) for f in self.favorites if f and self.get_node_endpoint(f)}
        fav_eps.discard("")
        fav_eps.discard("127.0.0.1:443")
        _, bl_eps, sbl_eps, _ = self.get_pool_endpoint_sets()

        ver_removed = False
        for ep in list(self.verified_nodes.keys()):
            if (ep not in fav_eps) or (ep in self.local_blacklist) or (ep in self.speed_blacklist) or (ep in bl_eps) or (ep in sbl_eps):
                self.verified_nodes.pop(ep, None)
                ver_removed = True

        if ver_removed:
            self.save_persisted_config()

        reverse_map = self.resolve_star_matches()
        now = time.time()

        for ep, item in self.verified_nodes.items():
            rem = item.get("remark", "")
            d_val = item.get("delay", None)
            s_val = item.get("speed", None)
            c_val = item.get("colo")
            colo_str = c_val if (c_val and c_val != "-") else self.node_colo.get(ep, "-")

            matched_name = reverse_map.get(ep, "")
            if not matched_name and ":" in ep:
                matched_name = reverse_map.get(ep.split(":")[0], "未在当前订阅匹配")
            elif not matched_name:
                matched_name = "未在当前订阅匹配"
            item["matched_name"] = matched_name

            colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep, []), now, node_name=matched_name)[3]

            d_str = f"{d_val} ms" if (d_val is not None and d_val < 99999) else ("超时" if d_val == 99999 else "-")
            s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else "-"

            first_seen = item.get("first_seen", now)
            hours_alive = round((now - first_seen) / 3600.0, 1)
            time_str = f"已存活 {hours_alive}h"

            passes = item.get("passes", 0)
            fails = item.get("fails", 0)
            stats_str = f"达标 {passes} 次 / 失败 {fails} 次"

            reason_str = item.get("reason", "")
            if not reason_str:
                if passes > 1:
                    reason_str = f"考核留任 (达标{passes}次/{hours_alive}h)"
                else:
                    reason_str = "优选初筛建档 (第1次达标)"

            tags = ["fav"] if passes >= 3 else []
            tree.insert("", tk.END, values=(ep, colo_str, colo_hist_str, reason_str, rem, d_str, s_str, time_str, stats_str, matched_name), tags=tags)


        self.notebook.tab(2, text=f"⏳ 沉淀孵化 ({len(self.verified_nodes)})")

    def process_verified_lifecycle(self, current_favs, stars_nodes=None):
        try:
            h_val = float(self.incubate_hours_var.get().strip())
        except Exception:
            h_val = 24.0
        try:
            p_val = int(self.incubate_passes_var.get().strip())
        except Exception:
            p_val = 5

        process_verified_lifecycle(
            self.verified_nodes,
            current_favs,
            self.stars_nodes if stars_nodes is None else stars_nodes,
            incubate_hours=h_val,
            incubate_passes=p_val,
        )
        self.save_persisted_config()

    def pull_verified_from_cloud(self):
        base_url = self.cf_worker_url_var.get().strip().rstrip("/")
        if not base_url.startswith("http"):
            messagebox.showwarning("提示", "请在上方配置有效的 Cloudflare Worker 地址！")
            return

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text="正在从 Cloudflare 拉取 /verified.txt..."))
            self.log("正在从 Cloudflare /verified.txt 拉取沉淀节点...")
            mixed_port = self.get_clash_mixed_port()
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

            try:
                req = urllib.request.Request(f"{base_url}/verified.txt", headers={"User-Agent": "ClashVergeNodeAssistant/1.0"})
                with opener.open(req, timeout=10) as resp:
                    raw_text = resp.read().decode("utf-8", errors="ignore")

                fav_eps = {self.get_node_endpoint(f) for f in self.favorites if f and self.get_node_endpoint(f)}
                fav_eps.discard("")
                fav_eps.discard("127.0.0.1:443")

                now = time.time()
                for line in raw_text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("⏳") or line.startswith("Error"):
                        continue
                    if "#" in line:
                        parts = line.split("#", 1)
                        ep = parts[0].strip()
                        rem = parts[1].strip()
                    else:
                        ep = line
                        rem = "优质沉淀"

                    # 严格层级规则：沉淀孵化池必须是优质精选池的严格子集！不在精选池的一律拒绝纳入
                    if ep not in fav_eps:
                        continue

                    if not (self.is_asian_node(ep) or (rem and self.is_asian_node(rem))):
                        self.local_blacklist.add(ep)
                        continue

                    if ep not in self.verified_nodes:
                        self.verified_nodes[ep] = {
                            "endpoint": ep,
                            "colo": "-",
                            "remark": rem,
                            "first_seen": now,
                            "passes": 1,
                            "fails": 0,
                            "delay": None,
                            "speed": None,
                            "reason": "云端同步拉取",
                        }

                self.purge_invalid_and_blacklisted_from_all_pools()
                self.save_persisted_config()
                self.root.after(0, self.refresh_verified_table)
                self.log(f"成功从云端同步沉淀节点，当前总计 {len(self.verified_nodes)} 个")
                self.root.after(0, lambda: messagebox.showinfo("同步成功", f"🎉 成功拉取云端沉淀节点！当前池内共 {len(self.verified_nodes)} 个。"))
                self.root.after(0, lambda: self.status_label.config(text="沉淀节点拉取成功"))
            except Exception as ex:
                self.log(f"拉取 /verified.txt 失败: {str(ex)}")
                self.root.after(0, lambda: messagebox.showerror("拉取失败", f"无法获取沉淀数据：\n{str(ex)}"))

        threading.Thread(target=_worker, daemon=True).start()

    def manual_push_verified_to_cloud(self):
        lines = [f"{v['endpoint']}#{v['remark']}" for v in self.verified_nodes.values()]
        payload = "\r\n".join(lines) + "\r\n"

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text="正在推送沉淀池到 /verified.txt..."))
            ok, msg = self.push_text_to_cf_worker(payload, "/verified.txt")
            if ok:
                self.log("手动同步沉淀池至 /verified.txt 成功")
                self.root.after(0, lambda: messagebox.showinfo("同步成功", "🎉 沉淀池节点已成功发布至 /verified.txt！"))
                self.root.after(0, lambda: self.status_label.config(text="沉淀池同步成功"))
            else:
                self.log(f"手动同步沉淀池失败: {msg}")
                self.root.after(0, lambda: messagebox.showerror("同步失败", f"推送失败：{msg}"))

        threading.Thread(target=_worker, daemon=True).start()

    def delete_selected_verified(self):
        tree = self.trees["verified"]
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要移除的沉淀节点！")
            return
        if messagebox.askyesno("删除确认", f"确定从沉淀孵化池移除选中的 {len(sels)} 个节点吗？"):
            for s in sels:
                ep = tree.item(s, "values")[0]
                self.verified_nodes.pop(ep, None)
            self.save_persisted_config()
            self.refresh_verified_table()
            self.log(f"已从沉淀池手动移除 {len(sels)} 个节点")

    def force_promote_verified_to_stars(self):
        tree = self.trees["verified"]
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要提前加冕的节点！")
            return

        cnt = 0
        existing_eps = {s.get("endpoint") for s in self.stars_nodes}
        for s in sels:
            ep = tree.item(s, "values")[0]
            if ep in self.verified_nodes and ep not in existing_eps:
                v = self.verified_nodes[ep]
                self.stars_nodes.append({
                    "endpoint": ep,
                    "colo": v.get("colo", "-"),
                    "remark": f"{v.get('remark', '')} [手动加冕]",
                    "delay": v.get("delay"),
                    "speed": v.get("speed"),
                    "matched_name": v.get("matched_name", ""),
                    "reason": f"沉淀池提前加冕 (已达标{v.get('passes', 0)}次)",
                })
                existing_eps.add(ep)
                cnt += 1

        self.save_persisted_config()
        self.refresh_stars_table()
        self.log(f"手动加冕 {cnt} 个沉淀节点至 🏆 典藏常青池")
        messagebox.showinfo("加冕成功", f"🎉 已将选中的 {cnt} 个节点直接移入 🏆 典藏常青池！")

    # ==================== 🏆 典藏常青池专属业务 ====================
    def refresh_stars_table(self):
        if "stars" not in self.trees:
            return
        tree = self.trees["stars"]
        tree.delete(*tree.get_children())

        reverse_map = self.resolve_star_matches()
        now = time.time()

        for item in self.stars_nodes:
            ep = item.get("endpoint", "")
            rem = item.get("remark", "")
            d_val = item.get("delay", None)
            s_val = item.get("speed", None)
            c_val = item.get("colo")
            colo_str = c_val if (c_val and c_val != "-") else self.node_colo.get(ep, "-")

            matched_name = reverse_map.get(ep, "")
            if not matched_name and ":" in ep:
                matched_name = reverse_map.get(ep.split(":")[0], "未在当前订阅匹配")
            elif not matched_name:
                matched_name = "未在当前订阅匹配"
            item["matched_name"] = matched_name

            colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep, []), now, node_name=matched_name)[3]

            d_str = f"{d_val} ms" if (d_val is not None and d_val < 99999) else ("超时" if d_val == 99999 else "-")
            s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else "-"

            reason_str = item.get("reason", "")
            if not reason_str:
                if "加冕" in rem:
                    reason_str = "沉淀池提前加冕"
                elif "手动" in rem or "录入" in rem:
                    reason_str = "手动录入典藏"
                else:
                    reason_str = "考核通关晋升 (长效极稳)"

            tags = ["fav"] if matched_name != "未在当前订阅匹配" else ["offline"]
            tree.insert("", tk.END, values=(ep, colo_str, colo_hist_str, reason_str, rem, d_str, s_str, matched_name), tags=tags)


        self.notebook.tab(3, text=f"🏆 典藏管理 ({len(self.stars_nodes)})")

    def pull_stars_from_cloud(self):
        base_url = self.cf_worker_url_var.get().strip().rstrip("/")
        if not base_url.startswith("http"):
            messagebox.showwarning("提示", "请在上方配置有效的 Cloudflare Worker 地址！")
            return

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text="正在从 Cloudflare 根目录拉取典藏常青节点..."))
            self.log("正在从 Cloudflare 根地址拉取典藏节点...")
            mixed_port = self.get_clash_mixed_port()
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

            try:
                req = urllib.request.Request(f"{base_url}/", headers={"User-Agent": "ClashVergeNodeAssistant/1.0"})
                with opener.open(req, timeout=10) as resp:
                    raw_text = resp.read().decode("utf-8", errors="ignore")

                new_stars = []
                for line in raw_text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("⏳") or line.startswith("Error"):
                        continue
                    if "#" in line:
                        parts = line.split("#", 1)
                        ep = parts[0].strip()
                        rem = parts[1].strip()
                    else:
                        ep = line
                        rem = "典藏节点"
                    new_stars.append({"endpoint": ep, "colo": "-", "remark": rem, "delay": None, "speed": None, "reason": "云端根目录同步"})

                self.stars_nodes = new_stars
                self.save_persisted_config()
                self.root.after(0, self.refresh_stars_table)
                self.log(f"成功拉取到 {len(new_stars)} 个云端典藏节点！")
                self.root.after(0, lambda: messagebox.showinfo("拉取成功", f"🎉 成功从云端拉取并同步 {len(new_stars)} 个典藏常青节点！"))
                self.root.after(0, lambda: self.status_label.config(text=f"成功拉取 {len(new_stars)} 个典藏节点"))
            except Exception as ex:
                self.log(f"从云端拉取典藏失败: {str(ex)}")
                self.root.after(0, lambda: messagebox.showerror("拉取失败", f"无法从云端获取典藏数据：\n{str(ex)}"))
                self.root.after(0, lambda: self.status_label.config(text="拉取云端典藏失败"))

        threading.Thread(target=_worker, daemon=True).start()

    def manual_push_stars_to_cloud(self):
        if not self.stars_nodes:
            if not messagebox.askyesno("确认推送", "当前典藏列表为空，推送将清空云端典藏池，确定继续吗？"):
                return

        lines = [f"{item.get('endpoint', '')}#{item.get('remark', '')}" for item in self.stars_nodes]
        payload = "\r\n".join(lines) + "\r\n"

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text="正在手动同步典藏常青池到 Cloudflare 根目录..."))
            ok, msg = self.push_text_to_cf_worker(payload, "")
            if ok:
                self.log(f"已手动将 {len(self.stars_nodes)} 个典藏常青节点同步到 Worker 根地址")
                self.root.after(0, lambda: messagebox.showinfo(
                    "同步成功",
                    f"🎉 成功同步！\n\n共 {len(self.stars_nodes)} 个极品节点已发布至 Worker 根目录，你的 Pages 订阅源已即时生效！"
                ))
                self.root.after(0, lambda: self.status_label.config(text=f"已成功同步 {len(self.stars_nodes)} 个典藏节点"))
            else:
                self.log(f"手动推送典藏失败: {msg}")
                self.root.after(0, lambda: messagebox.showerror("推送失败", f"推送发生错误：\n{msg}"))

        threading.Thread(target=_worker, daemon=True).start()

    def edit_selected_star_remark(self):
        tree = self.trees["stars"]
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先在列表中选中需要修改备注的典藏节点！")
            return
        ep = tree.item(sel[0], "values")[0]
        curr_item = next((s for s in self.stars_nodes if s.get("endpoint") == ep), None)
        if not curr_item:
            curr_item = self.stars_nodes[tree.index(sel[0])]
        old_rem = curr_item.get("remark", "")

        new_rem = simpledialog.askstring("修改备注", f"修改节点 [{curr_item.get('endpoint')}] 的备注信息：", initialvalue=old_rem)
        if new_rem is not None:
            curr_item["remark"] = new_rem.strip()
            self.save_persisted_config()
            self.refresh_stars_table()
            self.log(f"已修改典藏节点 [{curr_item.get('endpoint')}] 备注为: {new_rem.strip()}")

    def delete_selected_stars(self):
        tree = self.trees["stars"]
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要删除的典藏节点！")
            return
        if messagebox.askyesno("删除确认", f"确定从本地典藏池移除选中的 {len(sels)} 个节点吗？\n（注：点击保存上传前云端数据不会变动）"):
            sel_eps = {tree.item(s, "values")[0] for s in sels}
            self.stars_nodes = [s for s in self.stars_nodes if s.get("endpoint") not in sel_eps]
            self.save_persisted_config()
            self.refresh_stars_table()
            self.log(f"已从典藏池移除 {len(sels)} 个节点")

    def promote_selected_to_stars(self):
        tree = self.get_current_tree()
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要晋升为典藏的节点！")
            return

        added_cnt = 0
        existing_eps = {item.get("endpoint") for item in self.stars_nodes}

        for s in sels:
            node_name = tree.item(s, "values")[-1]
            if not self.is_asian_node(node_name):
                self.local_blacklist.add(node_name)
                continue
            ep = self.get_node_endpoint(node_name)
            if ep in existing_eps:
                continue

            region = self.node_colo.get(node_name, detect_node_region(node_name))
            spd = self.node_speeds.get(node_name, 0.0)
            rem = f"{region} [典藏] {spd:.2f} MB/s" if spd > 0 else f"{region} [典藏常青]"

            self.stars_nodes.append({
                "endpoint": ep,
                "colo": self.node_colo.get(node_name, "-"),
                "remark": rem,
                "delay": self.node_delays.get(node_name),
                "speed": self.node_speeds.get(node_name),
                "matched_name": node_name,
                "reason": "手动晋升典藏",
            })
            existing_eps.add(ep)
            added_cnt += 1

        self.save_persisted_config()
        self.refresh_stars_table()
        self.log(f"已成功将 {added_cnt} 个节点加冕至【🏆 典藏管理】池")
        messagebox.showinfo("晋升成功", f"🎉 已将 {added_cnt} 个极品节点加入典藏常青池！\n可前往【🏆 典藏管理】标签页查看、测速或点击手动上传。")

    def open_import_stars_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("手动填写 / 批量导入典藏节点")
        dialog.geometry("620x500")
        dialog.configure(bg=THEME["bg_card"])
        dialog.transient(self.root)
        dialog.grab_set()

        lbl_tip = tk.Label(
            dialog,
            text="请在此直接粘贴节点信息（支持单行或多行批量）：\n格式支持：IP:端口#备注信息  或直接粘贴  IP:端口\n例如：104.18.33.229:443#香港高速主力",
            justify=tk.LEFT,
            font=("Microsoft YaHei UI", 9),
            fg="#38bdf8",
            bg=THEME["bg_card"],
            pady=8
        )
        lbl_tip.pack(fill=tk.X, padx=16, pady=(10, 4))

        txt_frame = tk.Frame(dialog, bg=THEME["bg_main"], padx=2, pady=2)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=6)

        txt_box = tk.Text(
            txt_frame,
            bg=THEME["bg_input"],
            fg=THEME["text_main"],
            insertbackground="#38bdf8",
            relief="flat",
            bd=0,
            font=("Consolas", 10),
            wrap="none"
        )
        sb_y = ttk.Scrollbar(txt_frame, orient=tk.VERTICAL, command=txt_box.yview, style="Vertical.TScrollbar")
        txt_box.configure(yscrollcommand=sb_y.set)
        txt_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)

        btn_box = tk.Frame(dialog, bg=THEME["bg_card"], pady=10)
        btn_box.pack(fill=tk.X, padx=16)

        def _do_parse_and_add():
            raw_text = txt_box.get("1.0", tk.END).strip()
            if not raw_text:
                messagebox.showwarning("提示", "请输入或粘贴内容！", parent=dialog)
                return

            existing_eps = {item.get("endpoint") for item in self.stars_nodes}
            added = 0
            skipped_dup = 0
            invalid = 0

            for raw_line in raw_text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                if "#" in line:
                    parts = line.split("#", 1)
                    ep = parts[0].strip()
                    rem = parts[1].strip()
                else:
                    ep = line.strip()
                    rem = ""

                m = re.search(r"([a-zA-Z0-9\.\-]+:\d{1,5})", ep)
                if not m:
                    invalid += 1
                    continue

                clean_ep = m.group(1)

                if clean_ep in existing_eps:
                    skipped_dup += 1
                    continue

                if not rem:
                    reg = detect_node_region(clean_ep)
                    rem = f"{reg} [手动录入]"

                if not (self.is_asian_node(rem) or self.is_asian_node(clean_ep)):
                    self.local_blacklist.add(clean_ep)
                    continue

                self.stars_nodes.append({
                    "endpoint": clean_ep,
                    "colo": "-",
                    "remark": rem,
                    "delay": None,
                    "speed": None,
                    "matched_name": "",
                    "reason": "手动录入典藏",
                })
                existing_eps.add(clean_ep)
                added += 1

            self.save_persisted_config()
            self.refresh_stars_table()
            self.log(f"手动录入典藏节点：成功添加 {added} 个，跳过重复 {skipped_dup} 个，格式无效 {invalid} 个")

            msg = f"录入结果汇总：\n\n• 成功添加：{added} 个\n• 跳过重复：{skipped_dup} 个"
            if invalid > 0:
                msg += f"\n• 格式无效：{invalid} 个"
            messagebox.showinfo("录入完成", msg, parent=dialog)
            dialog.destroy()

        create_modern_btn(
            btn_box,
            text="✅ 立即识别并添加进典藏",
            command=_do_parse_and_add,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"],
            padx=16,
            pady=6
        ).pack(side=tk.RIGHT, padx=6)

        create_modern_btn(
            btn_box,
            text="取消",
            command=dialog.destroy,
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            padx=12,
            pady=6
        ).pack(side=tk.RIGHT, padx=6)

    def test_stars_pipeline(self, mode="delay"):
        tree = self.trees["stars"]
        sels = tree.selection()
        if sels:
            ep_map = {s.get("endpoint"): s for s in self.stars_nodes}
            targets = [ep_map[tree.item(s, "values")[0]] for s in sels if tree.item(s, "values")[0] in ep_map]
        else:
            targets = self.stars_nodes

        if not targets:
            messagebox.showinfo("提示", "当前典藏池没有节点！")
            return

        self.refresh_stars_table()

        testable = [t for t in targets if t.get("matched_name") and t.get("matched_name") != "未在当前订阅匹配"]
        if not testable:
            messagebox.showwarning(
                "未在内核中找到代理",
                "所选典藏节点尚未在 Clash 内核中找到对应的完整代理配置！\n\n"
                "【解决步骤】：\n"
                "1. 请先点击右侧【💾 保存并推送根目录 /】；\n"
                "2. 确保在 Clash Verge 中已添加并更新了您的 Pages 订阅链接（源自 Worker 根地址）；\n"
                "3. 在 Clash Verge 中激活该订阅后，回到此处点击【🔄 拉取云端】刷新状态，即可正常测速！"
            )
            return

        test_url = self.test_url_var.get().strip()
        speed_url = self.speed_url_var.get().strip()

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text=f"正在对 {len(testable)} 个典藏节点测试{mode}..."))
            self.log(f"开始测试 {len(testable)} 个典藏节点 (模式: {mode})...")

            if mode == "delay":
                for item in testable:
                    name = item["matched_name"]
                    enc_name = urllib.parse.quote(name, safe="")
                    enc_url = urllib.parse.quote(test_url, safe="")
                    res = self._call_api(f"/proxies/{enc_name}/delay?timeout=1500&url={enc_url}", timeout=2.2)
                    d_val = res["delay"] if (res and "delay" in res) else 99999
                    item["delay"] = d_val
                    ep_raw = item.get("endpoint", "")
                    if ":" in ep_raw:
                        s_ip, s_p = ep_raw.split(":", 1)
                        c_code, c_disp = get_cf_colo_raw(s_ip, s_p)
                        self.record_colo_sample(name, ep_raw, c_code, c_disp)
                        item["colo"] = c_disp
                    self.root.after(0, self.refresh_stars_table)
                self.log("典藏节点延迟测速完成")
            else:
                mode_guard = ClashModeGuard(self.clash_client, temporary_mode="global")
                mode_guard.__enter__()
                mixed_port = self.get_clash_mixed_port()
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

                proxy_handler = urllib.request.ProxyHandler({
                    "http": f"http://127.0.0.1:{mixed_port}",
                    "https": f"http://127.0.0.1:{mixed_port}",
                })
                speed_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

                try:
                    for item in testable:
                        name = item["matched_name"]
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self._call_api(f"/proxies/{enc_glb}", method="PUT", data=json.dumps({"name": name}).encode("utf-8"))
                        time.sleep(0.1)

                        speed_val = 0.0
                        total_bytes = 0
                        stars_deadline = time.time() + 3.5
                        try:
                            req = urllib.request.Request(speed_url, headers={"User-Agent": "Mozilla/5.0", "Connection": "close"})
                            with speed_opener.open(req, timeout=2.5) as resp:
                                st = time.time()
                                chunk_size = 16 * 1024
                                while time.time() - st < 2.5:
                                    if time.time() >= stars_deadline:
                                        break
                                    ch = resp.read(chunk_size)
                                    if not ch:
                                        break
                                    total_bytes += len(ch)
                                el = time.time() - st
                                speed_val = round((total_bytes / (1024 * 1024)) / el, 2) if (el > 0 and total_bytes > 0) else 0.0
                        except Exception:
                            speed_val = -1.0

                        item["speed"] = speed_val
                        self.root.after(0, self.refresh_stars_table)
                finally:
                    mode_guard.__exit__(None, None, None)

                self.log("典藏节点下行测速完成")

            self.save_persisted_config()
            self.root.after(0, lambda: self.status_label.config(text="典藏节点测速完毕"))

        threading.Thread(target=_worker, daemon=True).start()

    # ==================== 右键菜单 (支持 C 段溯源) ====================

    def test_selected_node_colo(self):
        tree = self.get_current_tree()
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要测试 Colo 的节点！")
            return
        
        row_vals = tree.item(sels[0], "values")
        current_tab_idx = self.notebook.index(self.notebook.select())
        if current_tab_idx in [2, 3]: # 沉淀孵化池 或 典藏管理池
            endpoint = row_vals[0]
            node_name = row_vals[-1] if (len(row_vals) >= 8 and row_vals[-1] != "未在当前订阅匹配") else ""
        else:
            node_name = row_vals[-1]
            endpoint = self.get_node_endpoint(node_name)
        
        if not endpoint and node_name and ":" in node_name:
            endpoint = node_name
        if not endpoint or ":" not in endpoint:
            messagebox.showwarning("提示", f"无法从【{endpoint or node_name}】中提取有效的 IP:端口！")
            return
            
        ip, port = endpoint.split(":", 1)
        target_iid = sels[0]
        
        def _worker():
            self.root.after(0, lambda: self.status_label.config(text=f"正在测试 {ip}:{port} 的实时 Colo..."))
            self.log(f"开始测试节点/IP [{ip}:{port}] 的实时机房 (Colo)...")
            
            c_code, c_disp = get_cf_colo_raw(ip, port, timeout=2.5)
            
            n_key = node_name if node_name else None
            self.record_colo_sample(n_key, endpoint, c_code, c_disp)

            colo_hist = self.node_colo_history.get(endpoint, self.node_colo_history.get(n_key, []))
            _, _, has_drift, drift_disp = self.analyze_colo_stats(colo_hist, time.time(), node_name=n_key)
            if has_drift:
                reason = f"机房漂移 ({drift_disp})"
                if n_key:
                    self.local_blacklist.add(n_key)
                    self.favorites.discard(n_key)
                    self.record_blacklist_reason(n_key, reason)
                if endpoint:
                    self.local_blacklist.add(endpoint)
                    self.record_blacklist_reason(endpoint, reason)
                    if endpoint in self.verified_nodes:
                        del self.verified_nodes[endpoint]
                self.purge_invalid_and_blacklisted_from_all_pools()
                self.do_write_script_file(list(self.favorites))
                trigger_verge_reactivate_hotkey()
                if self.get_cf_worker_config()[0]:
                    self.sync_all_pools_to_cf_worker()
                msg = f"节点/IP: {ip}:{port}\n实时机房 (Colo): {c_disp}\n\n⚠️【严苛规则触发：机房漂移 ({drift_disp})】\n该节点已按规则直接加入延迟黑名单淘汰，并已从优质精选池及远端 Worker 清除！"
                self.log(f"【漂移直接淘汰】{n_key or endpoint} 发生机房漂移 ({drift_disp})，直接拉黑淘汰并同步远端！")
            else:
                msg = f"节点/IP: {ip}:{port}\n实时机房 (Colo): {c_disp}"

            self.save_persisted_config()

            def _update_ui():
                # 1. 优先就地实时更新当前选中行的界面展示 (Colo 与 Colo稳定性)
                try:
                    if tree.exists(target_iid):
                        curr_vals = list(tree.item(target_iid, "values"))
                        if len(curr_vals) > 2:
                            curr_vals[1] = c_disp
                            curr_vals[2] = drift_disp
                            tree.item(target_iid, values=curr_vals)
                except Exception:
                    pass

                # 2. 全量刷新表格以联动所有相关池
                self.refresh_tables()
                self.refresh_verified_table()
                self.refresh_stars_table()
                if current_tab_idx == 4 and hasattr(self, "_render_delay_black_table"):
                    self._render_delay_black_table()
                elif current_tab_idx == 5 and hasattr(self, "_render_speed_black_table"):
                    self._render_speed_black_table()

                # 3. 刷新后尝试重新高亮定位该节点
                try:
                    for item_id in tree.get_children():
                        v = tree.item(item_id, "values")
                        if v and (v[0] == endpoint or (len(v) > 10 and v[10] == node_name) or (len(v) > 7 and v[-1] == node_name)):
                            tree.selection_set(item_id)
                            tree.focus(item_id)
                            tree.see(item_id)
                            break
                except Exception:
                    pass

                self.status_label.config(text=f"Colo 测试完成: {c_disp}")
                messagebox.showinfo("Colo 测试结果", msg)

            self.root.after(0, _update_ui)
            self.log(f"Colo 测试结果 -> {ip}:{port} : {c_disp}")
            
        threading.Thread(target=_worker, daemon=True).start()

    def clear_selected_node_colo_history(self):
        """清空右键选中的特定节点的机房(Colo)信息与历史"""
        tree = self.get_current_tree()
        sels = tree.selection()
        if not sels:
            messagebox.showinfo("提示", "请先在列表中选中要清空机房(Colo)记录的节点！")
            return

        current_tab_idx = self.notebook.index(self.notebook.select())
        cleared_cnt = 0
        for s in sels:
            row_vals = tree.item(s, "values")
            if not row_vals:
                continue
            if current_tab_idx in [2, 3]:
                ep = row_vals[0]
                n_key = row_vals[-1] if len(row_vals) >= 7 else ""
            else:
                n_key = row_vals[-1]
                ep = self.get_node_endpoint(n_key)

            keys_to_clean = [n_key, ep]
            if ep and ":" in ep:
                keys_to_clean.append(ep.split(":")[0])
            for k in keys_to_clean:
                if k and k != "-":
                    self.node_colo.pop(k, None)
                    self.node_colo_history.pop(k, None)

            if ep in self.verified_nodes:
                self.verified_nodes[ep]["colo"] = "-"
            for s_node in self.stars_nodes:
                if s_node.get("endpoint") == ep or (n_key and s_node.get("matched_name") == n_key):
                    s_node["colo"] = "-"
            cleared_cnt += 1

        self.save_persisted_config()
        self.refresh_tables()
        self.refresh_verified_table()
        self.refresh_stars_table()
        self.log(f"已清空选中的 {cleared_cnt} 个节点的机房(Colo)历史记录。")
        self.status_label.config(text=f"已清空选中的 {cleared_cnt} 个节点机房记录")

    def setup_context_menus(self):
        self.all_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.all_menu.add_command(label="⭐ 设为优质", command=self.set_favorite)
        self.all_menu.add_command(label="🏆 测速计分并晋升", command=lambda: self.rescore_and_promote_selected(self.trees["all"]))
        self.all_menu.add_command(label="🏆 晋升 / 加入典藏常青池", command=self.promote_selected_to_stars)
        self.all_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["all"]))
        self.all_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.all_menu.add_command(label="🧹 清空所选节点Colo历史", command=self.clear_selected_node_colo_history)
        self.all_menu.add_separator()
        self.all_menu.add_command(label="↩ 移出黑名单 (恢复待测)", command=lambda: self.remove_from_blacklist(self.trees["all"]))
        self.all_menu.add_command(label="🚫 延迟拉黑", command=self.manual_add_delay_blacklist)
        self.all_menu.add_command(label="🐌 低速拉黑", command=self.manual_add_speed_blacklist)

        def _on_all_right_click(event):
            tree = self.trees["all"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.all_menu.post(event.x_root, event.y_root)

        self.trees["all"].bind("<Button-3>", _on_all_right_click)

        self.fav_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.fav_menu.add_command(label="🏆 测速计分并晋升", command=lambda: self.rescore_and_promote_selected(self.trees["fav"]))
        self.fav_menu.add_command(label="🏆 晋升 / 加入典藏常青池", command=self.promote_selected_to_stars)
        self.fav_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["fav"]))
        self.fav_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.fav_menu.add_command(label="🧹 清空所选节点Colo历史", command=self.clear_selected_node_colo_history)
        self.fav_menu.add_separator()
        self.fav_menu.add_command(label="↩ 移出黑名单 (恢复待测)", command=lambda: self.remove_from_blacklist(self.trees["fav"]))
        self.fav_menu.add_command(label="🚫 延迟拉黑", command=self.manual_add_delay_blacklist)
        self.fav_menu.add_command(label="🐌 低速拉黑", command=self.manual_add_speed_blacklist)

        def _on_fav_right_click(event):
            tree = self.trees["fav"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.fav_menu.post(event.x_root, event.y_root)

        self.trees["fav"].bind("<Button-3>", _on_fav_right_click)

        self.delay_black_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.delay_black_menu.add_command(label="↩ 移出延迟黑名单 (恢复待测)", command=lambda: self.remove_from_blacklist(self.trees["delay_black"]))
        self.delay_black_menu.add_command(label="⭐ 移出黑名单并设为优质", command=lambda: self.remove_from_blacklist_and_set_favorite(self.trees["delay_black"]))
        self.delay_black_menu.add_command(label="🏆 移出并测速计分晋升", command=lambda: self.rescore_and_promote_selected(self.trees["delay_black"]))
        self.delay_black_menu.add_command(label="🏆 移出并直接晋升典藏", command=self.promote_selected_to_stars)
        self.delay_black_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["delay_black"]))
        self.delay_black_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.delay_black_menu.add_separator()
        self.delay_black_menu.add_command(label="🧹 清空当前延迟黑名单", command=self.clear_delay_blacklist)
        self.delay_black_menu.add_command(label="🧹 一键清空全部黑名单", command=self.clear_all_blacklists)

        def _on_delay_black_right_click(event):
            tree = self.trees["delay_black"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.delay_black_menu.post(event.x_root, event.y_root)

        self.trees["delay_black"].bind("<Button-3>", _on_delay_black_right_click)

        self.speed_black_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.speed_black_menu.add_command(label="↩ 移出低速黑名单 (恢复待测)", command=lambda: self.remove_from_blacklist(self.trees["speed_black"]))
        self.speed_black_menu.add_command(label="⭐ 移出黑名单并设为优质", command=lambda: self.remove_from_blacklist_and_set_favorite(self.trees["speed_black"]))
        self.speed_black_menu.add_command(label="🏆 移出并测速计分晋升", command=lambda: self.rescore_and_promote_selected(self.trees["speed_black"]))
        self.speed_black_menu.add_command(label="🏆 移出并直接晋升典藏", command=self.promote_selected_to_stars)
        self.speed_black_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["speed_black"]))
        self.speed_black_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.speed_black_menu.add_separator()
        self.speed_black_menu.add_command(label="🧹 清空当前低速黑名单", command=self.clear_speed_blacklist)
        self.speed_black_menu.add_command(label="🧹 一键清空全部黑名单", command=self.clear_all_blacklists)

        def _on_speed_black_right_click(event):
            tree = self.trees["speed_black"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.speed_black_menu.post(event.x_root, event.y_root)

        self.trees["speed_black"].bind("<Button-3>", _on_speed_black_right_click)

        self.stars_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.stars_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["stars"]))
        self.stars_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.stars_menu.add_command(label="🧹 清空所选节点Colo历史", command=self.clear_selected_node_colo_history)
        self.stars_menu.add_command(label="✏️ 修改备注", command=self.edit_selected_star_remark)
        self.stars_menu.add_command(label="🗑️ 移除此典藏", command=self.delete_selected_stars)

        def _on_stars_right_click(event):
            tree = self.trees["stars"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.stars_menu.post(event.x_root, event.y_root)

        self.trees["stars"].bind("<Button-3>", _on_stars_right_click)

        self.verified_menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=THEME["bg_card"],
            fg=THEME["text_main"],
            activebackground=THEME["accent_blue"],
            activeforeground="#ffffff",
            font=("Microsoft YaHei UI", 9)
        )
        self.verified_menu.add_command(label="🔍 深度挖掘此 IP 所在 C 段 (/24)", command=lambda: self._trigger_c_mining_from_tree(self.trees["verified"]))
        self.verified_menu.add_command(label="🧪 测试实时机房 (Colo)", command=self.test_selected_node_colo)
        self.verified_menu.add_command(label="🧹 清空所选节点Colo历史", command=self.clear_selected_node_colo_history)
        self.verified_menu.add_command(label="🏆 提前加冕至典藏", command=self.force_promote_verified_to_stars)
        self.verified_menu.add_command(label="🗑️ 移除沉淀", command=self.delete_selected_verified)

        def _on_verified_right_click(event):
            tree = self.trees["verified"]
            clicked_item = tree.identify_row(event.y)
            if clicked_item:
                if clicked_item not in tree.selection():
                    tree.selection_set(clicked_item)
                self.verified_menu.post(event.x_root, event.y_root)

        self.trees["verified"].bind("<Button-3>", _on_verified_right_click)

    def _trigger_c_mining_from_tree(self, tree):
        sel = tree.selection()
        if not sel:
            return
        row_vals = tree.item(sel[0], "values")
        if tree in [self.trees.get("verified"), self.trees.get("stars")]:
            target_str = row_vals[0]
        else:
            node_name = row_vals[-1]
            target_str = self.get_node_endpoint(node_name)

        self.open_c_segment_mining_dialog(target_str)

    # ==================== 界面布局与初始化 ====================
    def setup_ui(self):
        def _make_entry(parent, textvariable, width, **kwargs):
            return tk.Entry(
                parent,
                textvariable=textvariable,
                width=width,
                bg=THEME["bg_input"],
                fg=THEME["text_main"],
                insertbackground="#38bdf8",
                relief="flat",
                highlightthickness=1,
                highlightbackground=THEME["border"],
                highlightcolor=THEME["accent_blue"],
                font=("Microsoft YaHei UI", 9),
                **kwargs,
            )

        top_card = tk.Frame(
            self.root, bg=THEME["bg_card"], padx=14, pady=8, highlightthickness=1, highlightbackground=THEME["border"]
        )
        top_card.pack(fill=tk.X, padx=12, pady=(10, 5))

        tk.Label(
            top_card,
            text="当前订阅:",
            font=("Microsoft YaHei UI", 9, "bold"),
            fg=THEME["text_main"],
            bg=THEME["bg_card"],
        ).pack(side=tk.LEFT)

        self.file_combo = ttk.Combobox(top_card, width=34, state="readonly")
        self.file_combo.pack(side=tk.LEFT, padx=8)
        self.file_combo.bind("<<ComboboxSelected>>", self.on_file_changed)

        create_modern_btn(
            top_card,
            text="🔄 更新当前订阅",
            command=self.manual_update_subscription_and_reactivate,
            bg=THEME["bg_hover"],
            hover_bg=THEME["accent_blue"],
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.conn_label = tk.Label(
            top_card,
            text="● 正在连接内核...",
            font=("Microsoft YaHei UI", 9, "bold"),
            fg=THEME["accent_yellow"],
            bg=THEME["bg_card"],
        )
        self.conn_label.pack(side=tk.LEFT, padx=(6, 12))

        self.last_time_label = tk.Label(
            top_card,
            text="🕒 上次检测  全量: 未运行  |  复检: 未运行",
            font=("Microsoft YaHei UI", 9, "bold"),
            fg="#38bdf8",
            bg=THEME["bg_card"],
        )
        self.last_time_label.pack(side=tk.LEFT, padx=8)

        create_modern_btn(
            top_card,
            text="🗑️ 清空测速记录",
            command=lambda: self.clear_test_history(silent=False),
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
        ).pack(side=tk.RIGHT, padx=4)

        create_modern_btn(
            top_card,
            text="🧹 清当前页Colo",
            command=self.clear_current_tab_colo_history,
            bg=THEME["bg_hover"],
            hover_bg=THEME["accent_red"],
        ).pack(side=tk.RIGHT, padx=4)

        create_modern_btn(
            top_card,
            text="🌍 测当前页Colo",
            command=lambda: threading.Thread(target=self.test_all_nodes_colo, daemon=True).start(),
            bg=THEME["accent_cyan"],
            hover_bg=THEME["accent_cyan_hover"],
        ).pack(side=tk.RIGHT, padx=4)

        create_modern_btn(
            top_card,
            text="🔄 同步内核延迟",
            command=lambda: threading.Thread(target=self.sync_existing_delays, daemon=True).start(),
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
        ).pack(side=tk.RIGHT, padx=4)

        pipeline_card = tk.Frame(
            self.root, bg=THEME["bg_card"], padx=14, pady=10, highlightthickness=1, highlightbackground=THEME["border"]
        )
        pipeline_card.pack(fill=tk.X, padx=12, pady=(0, 5))

        r1 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r1.pack(fill=tk.X, pady=(0, 6))

        tk.Label(r1, text="⚡ 全局优选门槛:", fg="#38bdf8", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(r1, text="最低延迟(≤ ms):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r1, self.max_delay_threshold_var, 5).pack(side=tk.LEFT, padx=(4, 10))

        tk.Label(r1, text="优质下行(≥ MB/s):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r1, self.min_speed_threshold_var, 5).pack(side=tk.LEFT, padx=(4, 10))

        tk.Label(r1, text="🎯 达标目标(留空全测):", fg="#fbbf24", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r1, self.target_node_count_var, 4).pack(side=tk.LEFT, padx=(4, 10))

        tk.Label(r1, text="轮数:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r1, self.test_rounds_var, 3).pack(side=tk.LEFT, padx=(4, 6))

        tk.Label(r1, text="超时(ms):", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r1, self.test_timeout_var, 5).pack(side=tk.LEFT, padx=(4, 6))

        tk.Label(r1, text="采样:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r1, self.speed_duration_var, 4).pack(side=tk.LEFT, padx=(4, 2))
        tk.Label(r1, text="秒", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)

        r2 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r2.pack(fill=tk.X, pady=(0, 6))

        tk.Label(r2, text="🚫 自动拉黑规则:", fg="#f87171", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(r2, text="延迟拉黑(≥ ms):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r2, self.blacklist_threshold_var, 5).pack(side=tk.LEFT, padx=(4, 14))

        tk.Label(r2, text="低速拉黑(< MB/s):", fg="#fca5a5", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r2, self.speed_bl_threshold_var, 5).pack(side=tk.LEFT, padx=(4, 6))

        tk.Label(r2, text="连续低速次数:", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r2, self.speed_bl_rounds_var, 3).pack(side=tk.LEFT, padx=(4, 2))
        tk.Label(r2, text="次", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(r2, text="抖动基准(≥ ms):", fg="#fca5a5", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(4, 0))
        _make_entry(r2, self.jitter_min_delay_var, 4).pack(side=tk.LEFT, padx=(3, 6))

        tk.Label(r2, text="向上抖动(≥ ms):", fg="#fca5a5", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r2, self.jitter_up_threshold_var, 4).pack(side=tk.LEFT, padx=(3, 6))

        r3 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r3.pack(fill=tk.X, pady=(0, 6))

        tk.Label(r3, text="延迟源:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r3, self.test_url_var, 25).pack(side=tk.LEFT, padx=(4, 8))

        tk.Label(r3, text="带宽源:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r3, self.speed_url_var, 28).pack(side=tk.LEFT, padx=(4, 12))

        self.btn_run_pipeline = create_modern_btn(
            r3,
            text="🚀 启动一整套全自动优选与热键生效",
            command=self.start_full_auto_pipeline,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"],
        )
        self.btn_run_pipeline.pack(side=tk.LEFT, padx=3)

        self.btn_stop_pipeline = create_modern_btn(
            r3,
            text="⏹ 终止任务",
            command=self.stop_pipeline,
            bg=THEME["bg_hover"],
            hover_bg=THEME["accent_red"],
            state="disabled",
        )
        self.btn_stop_pipeline.pack(side=tk.LEFT, padx=3)

        r4 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r4.pack(fill=tk.X, pady=(0, 6))

        tk.Checkbutton(
            r4,
            text="🚀 开机静默自启",
            variable=self.boot_startup_var,
            bg=THEME["bg_card"],
            fg="#10b981",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#10b981",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=self.on_boot_toggle,
        ).pack(side=tk.LEFT, padx=(0, 12))

        tk.Checkbutton(
            r4,
            text="⏰ 启用全局定时优选 (按上次运行时间计)",
            variable=self.schedule_enabled_var,
            bg=THEME["bg_card"],
            fg="#38bdf8",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#38bdf8",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=lambda: [self._on_schedule_toggle(), self.save_persisted_config()],
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(r4, text="循环间隔(分钟):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r4, self.schedule_interval_var, 5).pack(side=tk.LEFT, padx=(4, 12))

        tk.Label(r4, text="固定时刻(HH:MM):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r4, self.schedule_times_var, 22).pack(side=tk.LEFT, padx=(4, 8))

        self.sched_status_label = tk.Label(
            r4,
            text="(全局定时未启动)",
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            font=("Microsoft YaHei UI", 9),
        )
        self.sched_status_label.pack(side=tk.LEFT, padx=6)

        r5 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r5.pack(fill=tk.X, pady=(0, 6))

        tk.Label(r5, text="⚙️ 策略组测速配置:", fg="#a78bfa", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 4))

        tk.Label(r5, text="常规间隔(s):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r5, self.group_interval_var, 4).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(r5, text="常规容差(ms):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r5, self.group_tolerance_var, 3).pack(side=tk.LEFT, padx=(2, 8))

        tk.Label(r5, text="典藏间隔(s):", fg="#fbbf24", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r5, self.star_group_interval_var, 4).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(r5, text="典藏容差(ms):", fg="#fbbf24", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT)
        _make_entry(r5, self.star_group_tolerance_var, 3).pack(side=tk.LEFT, padx=(2, 8))

        create_modern_btn(
            r5,
            text="💾 保存测速设置并热更",
            command=self.save_group_config_and_reload,
            bg=THEME["accent_purple"],
            hover_bg=THEME["accent_purple_hover"],
            pady=3,
            font_size=9,
        ).pack(side=tk.LEFT, padx=4)

        r6 = tk.Frame(pipeline_card, bg=THEME["bg_card"])
        r6.pack(fill=tk.X)

        tk.Checkbutton(
            r6,
            text="☁️ 自动同步推送 Worker 三大文本 (/auto.txt, /verified.txt, /)",
            variable=self.cf_worker_enabled_var,
            bg=THEME["bg_card"],
            fg="#38bdf8",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#38bdf8",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=self.save_persisted_config,
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(r6, text="Worker 根地址:", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r6, self.cf_worker_url_var, 30).pack(side=tk.LEFT, padx=(3, 8))

        tk.Label(r6, text="授权密钥:", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(r6, self.cf_worker_token_var, 15, show="*").pack(side=tk.LEFT, padx=(3, 8))

        create_modern_btn(
            r6,
            text="🧪 测试自动通道",
            command=self.test_cf_worker_upload,
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            pady=3,
            font_size=9,
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            r6,
            text="☁️ 同步auto.txt优质",
            command=lambda: self.sync_favorites_from_auto_text(show_notify=True),
            bg=THEME["accent_blue"],
            hover_bg=THEME["accent_blue_hover"],
            pady=3,
            font_size=9,
        ).pack(side=tk.LEFT, padx=3)

        tk.Label(r6, text="[典藏池:/ | 沉淀池:/verified.txt | 自动优选:/auto.txt]", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 8)).pack(side=tk.LEFT, padx=4)

        param_card = tk.Frame(
            self.root, bg=THEME["bg_card"], padx=14, pady=8, highlightthickness=1, highlightbackground=THEME["border"]
        )
        param_card.pack(fill=tk.X, padx=12, pady=(0, 8))

        tk.Label(param_card, text="端口:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(param_card, self.port_var, 6).pack(side=tk.LEFT, padx=(4, 8))

        tk.Label(param_card, text="密钥:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(param_card, self.secret_var, 14).pack(side=tk.LEFT, padx=(4, 8))

        create_modern_btn(
            param_card,
            text="重连",
            command=lambda: self.test_connection(auto_sync=False),
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            pady=3,
            font_size=8,
        ).pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(param_card, text="快速过滤:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        self.search_var.trace_add("write", lambda *args: self.refresh_tables())
        _make_entry(param_card, self.search_var, 18).pack(side=tk.LEFT, padx=(4, 10))

        self.status_label = tk.Label(
            param_card,
            text="",
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            font=("Microsoft YaHei UI", 9),
        )
        self.status_label.pack(side=tk.RIGHT)

        # 选项卡区域 (先创建实例，待底部固定栏布局完毕后再 pack 铺满剩余空间)
        self.notebook = ttk.Notebook(self.root)

        self.tab_all = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_fav = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_verified = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_stars = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_delay_black = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_speed_black = tk.Frame(self.notebook, bg=THEME["tree_bg"])
        self.tab_cloud_text = tk.Frame(self.notebook, bg=THEME["tree_bg"])

        self.notebook.add(self.tab_all, text="📋 活跃待测 (0)")
        self.notebook.add(self.tab_fav, text="⭐ 优质精选 (0)")
        self.notebook.add(self.tab_verified, text="⏳ 沉淀孵化 (0)")
        self.notebook.add(self.tab_stars, text="🏆 典藏管理 (0)")
        self.notebook.add(self.tab_delay_black, text="🚫 延迟黑名单 (0)")
        self.notebook.add(self.tab_speed_black, text="🐌 低速黑名单 (0)")
        self.notebook.add(self.tab_cloud_text, text="☁️ 云端文本查看")
        self.setup_cloud_text_ui()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_notebook_tab_changed)

        # 优质精选工具栏
        fav_tool_bar = tk.Frame(self.tab_fav, bg=THEME["bg_card"], padx=10, pady=8)
        fav_tool_bar.pack(fill=tk.X, padx=4, pady=(4, 4))

        ft_row1 = tk.Frame(fav_tool_bar, bg=THEME["bg_card"])
        ft_row1.pack(fill=tk.X, pady=(0, 6))

        tk.Label(ft_row1, text="⭐ 优质复检标准:", fg="#fbbf24", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(ft_row1, text="生效延迟(≤ ms):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row1, self.fav_max_delay_var, 4).pack(side=tk.LEFT, padx=(3, 8))

        tk.Label(ft_row1, text="生效下行(≥ MB/s):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row1, self.fav_min_speed_var, 4).pack(side=tk.LEFT, padx=(3, 8))

        tk.Label(ft_row1, text="轮数:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row1, self.fav_rounds_var, 3).pack(side=tk.LEFT, padx=(3, 6))

        tk.Label(ft_row1, text="采样:", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row1, self.fav_speed_duration_var, 4).pack(side=tk.LEFT, padx=(3, 2))
        tk.Label(ft_row1, text="秒", fg=THEME["text_muted"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(ft_row1, text="抖动基准(≥ ms):", fg="#fca5a5", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT, padx=(4, 0))
        _make_entry(ft_row1, self.fav_jitter_min_delay_var, 4).pack(side=tk.LEFT, padx=(3, 6))

        tk.Label(ft_row1, text="向上抖动(≥ ms):", fg="#fca5a5", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row1, self.fav_jitter_up_threshold_var, 4).pack(side=tk.LEFT, padx=(3, 8))

        create_modern_btn(
            ft_row1,
            text="⚡ 优质池双轨复检并写入",
            command=self.start_fav_review_pipeline,
            bg="#b45309",
            hover_bg="#d97706",
            font_size=9,
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            ft_row1,
            text="☁️ 同步auto.txt优质",
            command=lambda: self.sync_favorites_from_auto_text(show_notify=True),
            bg=THEME["accent_blue"],
            hover_bg=THEME["accent_blue_hover"],
            font_size=9,
        ).pack(side=tk.RIGHT, padx=3)

        create_modern_btn(
            ft_row1,
            text="⚡ 一键同步至 Verge",
            command=lambda: self.sync_favorites_to_verge(show_notify=True),
            bg="#16a34a",
            hover_bg="#15803d",
            font_size=9,
        ).pack(side=tk.RIGHT, padx=3)

        create_modern_btn(
            ft_row1,
            text="🛡️ 精选保活状态",
            command=self.clean_offline_favorites,
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            font_size=9,
        ).pack(side=tk.RIGHT, padx=3)

        ft_row2 = tk.Frame(fav_tool_bar, bg=THEME["bg_card"])
        ft_row2.pack(fill=tk.X)

        tk.Checkbutton(
            ft_row2,
            text="🔄 启用优质定时复检",
            variable=self.fav_schedule_enabled_var,
            bg=THEME["bg_card"],
            fg="#fbbf24",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#fbbf24",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=lambda: [self._on_fav_schedule_toggle(), self.save_persisted_config()],
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(ft_row2, text="间隔(m):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row2, self.fav_schedule_interval_var, 3).pack(side=tk.LEFT, padx=(2, 8))

        tk.Checkbutton(
            ft_row2,
            text="🎯 启用达标即停(取消则全测)",
            variable=self.fav_quota_early_stop_var,
            bg=THEME["bg_card"],
            fg="#38bdf8",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#38bdf8",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=self.save_persisted_config,
        ).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(ft_row2, text="香港目标:", fg="#38bdf8", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row2, self.fav_target_hk_count_var, 3).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(ft_row2, text="非香港目标:", fg="#34d399", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(ft_row2, self.fav_target_nohk_count_var, 3).pack(side=tk.LEFT, padx=(2, 10))

        tk.Checkbutton(
            ft_row2,
            text="⚠️ 不足唤醒全量优选",
            variable=self.fav_fallback_enabled_var,
            bg=THEME["bg_card"],
            fg="#f87171",
            selectcolor=THEME["bg_input"],
            activebackground=THEME["bg_card"],
            activeforeground="#f87171",
            font=("Microsoft YaHei UI", 9, "bold"),
            command=self.save_persisted_config,
        ).pack(side=tk.LEFT, padx=(2, 8))

        self.fav_sched_status_label = tk.Label(
            ft_row2,
            text="(优质定时未启动)",
            fg=THEME["text_muted"],
            bg=THEME["bg_card"],
            font=("Microsoft YaHei UI", 9),
        )
        self.fav_sched_status_label.pack(side=tk.LEFT, padx=4)

        # 沉淀孵化池工具栏
        verified_tool_bar = tk.Frame(self.tab_verified, bg=THEME["bg_card"], padx=10, pady=8)
        verified_tool_bar.pack(fill=tk.X, padx=4, pady=(4, 4))

        tk.Label(verified_tool_bar, text="⏳ 沉淀孵化 (发布至 /verified.txt):", fg="#34d399", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        tk.Label(verified_tool_bar, text="考核满存活(h):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(verified_tool_bar, self.incubate_hours_var, 3).pack(side=tk.LEFT, padx=(2, 6))

        tk.Label(verified_tool_bar, text="连续达标(次):", fg=THEME["text_main"], bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9)).pack(side=tk.LEFT)
        _make_entry(verified_tool_bar, self.incubate_passes_var, 3).pack(side=tk.LEFT, padx=(2, 8))

        create_modern_btn(
            verified_tool_bar,
            text="🔄 拉取云端沉淀",
            command=self.pull_verified_from_cloud,
            bg=THEME["accent_cyan"],
            hover_bg=THEME["accent_cyan_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            verified_tool_bar,
            text="🏆 提前晋升典藏",
            command=self.force_promote_verified_to_stars,
            bg="#b45309",
            hover_bg="#d97706",
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            verified_tool_bar,
            text="🗑️ 移除选中",
            command=self.delete_selected_verified,
            bg="#991b1b",
            hover_bg="#b91c1c",
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            verified_tool_bar,
            text="💾 同步推送 /verified.txt",
            command=self.manual_push_verified_to_cloud,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.RIGHT, padx=2)

        # 典藏常青池工具栏
        stars_tool_bar = tk.Frame(self.tab_stars, bg=THEME["bg_card"], padx=10, pady=8)
        stars_tool_bar.pack(fill=tk.X, padx=4, pady=(4, 4))

        tk.Label(stars_tool_bar, text="🏆 典藏常青管理 (发布至根目录 /):", fg="#fbbf24", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        create_modern_btn(
            stars_tool_bar,
            text="➕ 录入/粘贴",
            command=self.open_import_stars_dialog,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="🔄 拉取云端",
            command=self.pull_stars_from_cloud,
            bg=THEME["accent_cyan"],
            hover_bg=THEME["accent_cyan_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="⚡ 测延迟",
            command=lambda: self.test_stars_pipeline(mode="delay"),
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="🚀 测下行",
            command=lambda: self.test_stars_pipeline(mode="speed"),
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="✏️ 备注",
            command=self.edit_selected_star_remark,
            bg=THEME["accent_blue"],
            hover_bg=THEME["accent_blue_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="🗑️ 删除",
            command=self.delete_selected_stars,
            bg="#991b1b",
            hover_bg="#b91c1c",
            pady=2,
            font_size=8,
        ).pack(side=tk.LEFT, padx=2)

        create_modern_btn(
            stars_tool_bar,
            text="💾 保存并推送根目录 /",
            command=self.manual_push_stars_to_cloud,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"],
            pady=2,
            font_size=8,
        ).pack(side=tk.RIGHT, padx=2)

        self.trees["all"] = self.create_tree_widget(self.tab_all)
        self.trees["fav"] = self.create_tree_widget(self.tab_fav)
        self.trees["verified"] = self.create_verified_tree_widget(self.tab_verified)
        self.trees["stars"] = self.create_stars_tree_widget(self.tab_stars)
        self.trees["delay_black"] = self.create_tree_widget(self.tab_delay_black)
        self.trees["speed_black"] = self.create_tree_widget(self.tab_speed_black)

        log_card = tk.Frame(
            self.root, bg=THEME["bg_card"], padx=14, pady=6, highlightthickness=1, highlightbackground=THEME["border"]
        )

        log_head = tk.Frame(log_card, bg=THEME["bg_card"])
        log_head.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            log_head,
            text="📜 操作动态与实时运行日志:",
            font=("Microsoft YaHei UI", 9, "bold"),
            fg="#38bdf8",
            bg=THEME["bg_card"],
        ).pack(side=tk.LEFT)

        create_modern_btn(
            log_head,
            text="清屏",
            command=lambda: [self.log_text.config(state="normal"), self.log_text.delete("1.0", tk.END), self.log_text.config(state="disabled")],
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            pady=1,
            padx=8,
            font_size=8,
        ).pack(side=tk.RIGHT)

        log_inner = tk.Frame(log_card, bg=THEME["log_bg"])
        log_inner.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(
            log_inner,
            height=4,
            bg=THEME["log_bg"],
            fg="#94a3b8",
            insertbackground="#38bdf8",
            relief="flat",
            bd=0,
            font=("Consolas", 9),
            state="disabled",
            wrap="word",
        )
        log_scroll = ttk.Scrollbar(log_inner, orient=tk.VERTICAL, command=self.log_text.yview, style="Vertical.TScrollbar")
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        btn_card = tk.Frame(
            self.root, bg=THEME["bg_card"], padx=14, pady=8, highlightthickness=1, highlightbackground=THEME["border"]
        )
        # 底部栏永久锚定窗口最底部，彻底解决小分辨率或表格行过多时被挤出屏幕的问题
        btn_card.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 8))
        log_card.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(0, 4))
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=(0, 5))

        create_modern_btn(
            btn_card,
            text="⭐ 设为优质",
            command=self.set_favorite,
            bg="#854d0e",
            hover_bg="#a16207",
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="🏆 晋升为典藏",
            command=self.promote_selected_to_stars,
            bg="#b45309",
            hover_bg="#d97706",
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="🚫 延迟拉黑",
            command=self.manual_add_delay_blacklist,
            bg="#991b1b",
            hover_bg="#b91c1c",
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="🐌 低速拉黑",
            command=self.manual_add_speed_blacklist,
            bg="#c2410c",
            hover_bg="#ea580c",
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="↩ 移出黑名单",
            command=self.remove_from_blacklist,
            bg=THEME["accent_cyan"],
            hover_bg=THEME["accent_cyan_hover"],
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="🧹 一键清空所有黑名单",
            command=self.clear_all_blacklists,
            bg=THEME["bg_hover"],
            hover_bg=THEME["accent_red"],
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="🏆 重新计分与晋升",
            command=self.trigger_rescore_and_promote,
            bg="#d97706",
            hover_bg="#b45309",
        ).pack(side=tk.LEFT, padx=3)

        create_modern_btn(
            btn_card,
            text="⚡ 手动写入并热键刷新 Verge (Ctrl+Shift+F12)",
            command=self.manual_write_and_trigger_hotkey,
            bg=THEME["accent_blue"],
            hover_bg=THEME["accent_blue_hover"],
        ).pack(side=tk.RIGHT, padx=3)

    def create_tree_widget(self, parent_tab):
        columns = ("status", "colo", "colo_hist", "reason", "delay", "avg_delay", "delay_hist", "hist_avg", "speed", "speed_hist", "name")
        tree = ttk.Treeview(parent_tab, columns=columns, show="headings", selectmode="extended")

        tree.heading("status", text="状态 ↕", command=lambda: self.sort_tree(tree, "status", False))
        tree.heading("colo", text="最新Colo ↕", command=lambda: self.sort_tree(tree, "colo", False))
        tree.heading("colo_hist", text="Colo稳定性 (7天)")
        tree.heading("reason", text="入选/拉黑原因 ↕", command=lambda: self.sort_tree(tree, "reason", False))
        tree.heading("delay", text="最新延迟 ↕", command=lambda: self.sort_tree(tree, "delay", False))
        tree.heading("avg_delay", text="本轮均值 ↕", command=lambda: self.sort_tree(tree, "avg_delay", False))
        tree.heading("delay_hist", text="延迟轨迹 (轮数)")
        tree.heading("hist_avg", text="历史均值/稳定度 ↕", command=lambda: self.sort_tree(tree, "hist_avg", False))
        tree.heading("speed", text="最新下行 ↕", command=lambda: self.sort_tree(tree, "speed", False))
        tree.heading("speed_hist", text="下行轨迹 (近4次)")
        tree.heading("name", text="节点名称 (鼠标按住可直接上下多选)")

        tree.column("status", width=90, anchor="center")
        tree.column("colo", width=85, anchor="center")
        tree.column("colo_hist", width=160, anchor="center")
        tree.column("reason", width=170, anchor="center")
        tree.column("delay", width=75, anchor="center")
        tree.column("avg_delay", width=95, anchor="center")
        tree.column("delay_hist", width=130, anchor="center")
        tree.column("hist_avg", width=155, anchor="center")
        tree.column("speed", width=80, anchor="center")
        tree.column("speed_hist", width=130, anchor="center")
        tree.column("name", width=340, anchor="w")

        tree.tag_configure("fast", foreground="#34d399")
        tree.tag_configure("medium", foreground="#fbbf24")
        tree.tag_configure("timeout", foreground="#f87171")
        tree.tag_configure("fav", background="#1a2e26", foreground="#38bdf8")
        tree.tag_configure("offline", background="#1e293b", foreground="#94a3b8")
        tree.tag_configure("black_delay", background="#2b181b", foreground="#f87171")
        tree.tag_configure("black_speed", background="#2b2018", foreground="#fb923c")

        scrollbar = ttk.Scrollbar(parent_tab, orient=tk.VERTICAL, command=tree.yview, style="Vertical.TScrollbar")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.bind_drag_selection(tree)
        return tree

    def create_verified_tree_widget(self, parent_tab):
        columns = ("endpoint", "colo", "colo_hist", "reason", "remark", "delay", "speed", "time", "stats", "match")
        tree = ttk.Treeview(parent_tab, columns=columns, show="headings", selectmode="extended")

        tree.heading("endpoint", text="IP:端口 ↕", command=lambda: self.sort_tree(tree, "endpoint", False))
        tree.heading("colo", text="最新Colo ↕", command=lambda: self.sort_tree(tree, "colo", False))
        tree.heading("colo_hist", text="Colo稳定性 (7天)")
        tree.heading("reason", text="入孵原因 / 考核状态 ↕", command=lambda: self.sort_tree(tree, "reason", False))
        tree.heading("remark", text="备注信息 ↕", command=lambda: self.sort_tree(tree, "remark", False))
        tree.heading("delay", text="最新延迟 ↕", command=lambda: self.sort_tree(tree, "delay", False))
        tree.heading("speed", text="最新下行 ↕", command=lambda: self.sort_tree(tree, "speed", False))
        tree.heading("time", text="存活时长 ↕", command=lambda: self.sort_tree(tree, "time", False))
        tree.heading("stats", text="考核统计 ↕", command=lambda: self.sort_tree(tree, "stats", False))
        tree.heading("match", text="本地订阅关联")

        tree.column("endpoint", width=125, anchor="center")
        tree.column("colo", width=85, anchor="center")
        tree.column("colo_hist", width=150, anchor="center")
        tree.column("reason", width=170, anchor="center")
        tree.column("remark", width=155, anchor="w")
        tree.column("delay", width=75, anchor="center")
        tree.column("speed", width=80, anchor="center")
        tree.column("time", width=90, anchor="center")
        tree.column("stats", width=130, anchor="center")
        tree.column("match", width=220, anchor="w")

        tree.tag_configure("fav", foreground="#34d399")
        scrollbar = ttk.Scrollbar(parent_tab, orient=tk.VERTICAL, command=tree.yview, style="Vertical.TScrollbar")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.bind_drag_selection(tree)
        return tree

    def create_stars_tree_widget(self, parent_tab):
        columns = ("endpoint", "colo", "colo_hist", "reason", "remark", "delay", "speed", "match")
        tree = ttk.Treeview(parent_tab, columns=columns, show="headings", selectmode="extended")

        tree.heading("endpoint", text="IP:端口 ↕", command=lambda: self.sort_tree(tree, "endpoint", False))
        tree.heading("colo", text="最新Colo ↕", command=lambda: self.sort_tree(tree, "colo", False))
        tree.heading("colo_hist", text="Colo稳定性 (7天)")
        tree.heading("reason", text="典藏入选原因 ↕", command=lambda: self.sort_tree(tree, "reason", False))
        tree.heading("remark", text="备注信息 (可双击修改) ↕", command=lambda: self.sort_tree(tree, "remark", False))
        tree.heading("delay", text="最新延迟 ↕", command=lambda: self.sort_tree(tree, "delay", False))
        tree.heading("speed", text="最新下行 ↕", command=lambda: self.sort_tree(tree, "speed", False))
        tree.heading("match", text="本地订阅关联状态")

        tree.column("endpoint", width=130, anchor="center")
        tree.column("colo", width=85, anchor="center")
        tree.column("colo_hist", width=150, anchor="center")
        tree.column("reason", width=190, anchor="center")
        tree.column("remark", width=200, anchor="w")
        tree.column("delay", width=75, anchor="center")
        tree.column("speed", width=85, anchor="center")
        tree.column("match", width=250, anchor="w")

        tree.tag_configure("fav", foreground="#38bdf8")
        tree.tag_configure("offline", foreground="#94a3b8")

        scrollbar = ttk.Scrollbar(parent_tab, orient=tk.VERTICAL, command=tree.yview, style="Vertical.TScrollbar")
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        tree.bind("<Double-1>", lambda e: self.edit_selected_star_remark())
        self.bind_drag_selection(tree)
        return tree

    def bind_drag_selection(self, tree):
        tree._drag_start_item = None
        tree._base_selection = set()

        def on_press(event):
            item = tree.identify_row(event.y)
            if not item:
                return
            tree._drag_start_item = item
            if event.state & 0x0004:
                tree._base_selection = set(tree.selection())
            else:
                tree._base_selection = set()
                tree.selection_set(item)

        def on_drag(event):
            if not tree._drag_start_item:
                return
            cur_item = tree.identify_row(event.y)
            if not cur_item:
                return

            children = list(tree.get_children(""))
            if tree._drag_start_item in children and cur_item in children:
                idx_start = children.index(tree._drag_start_item)
                idx_cur = children.index(cur_item)
                low, high = min(idx_start, idx_cur), max(idx_start, idx_cur)
                drag_selected = set(children[low : high + 1])

                if event.state & 0x0004:
                    tree.selection_set(list(tree._base_selection | drag_selected))
                else:
                    tree.selection_set(list(drag_selected))

        def on_release(event):
            tree._drag_start_item = None

        tree.bind("<ButtonPress-1>", on_press, add="+")
        tree.bind("<B1-Motion>", on_drag, add="+")
        tree.bind("<ButtonRelease-1>", on_release, add="+")

    def get_current_tree(self):
        idx = self.notebook.index(self.notebook.select())
        mapping = [self.trees["all"], self.trees["fav"], self.trees["verified"], self.trees["stars"], self.trees["delay_black"], self.trees["speed_black"]]
        return mapping[idx] if idx < len(mapping) else self.trees["all"]

    def load_profile_data(self):
        profiles_yaml = os.path.join(PARENT_DIR, "profiles.yaml")
        profile_names_map = {}
        current_active_id = ""

        if os.path.exists(profiles_yaml):
            try:
                with open(profiles_yaml, "r", encoding="utf-8", errors="ignore") as f:
                    p_content = f.read()

                m_cur = re.search(r"current:\s*['\"]?([^'\"\r\n]+)['\"]?", p_content)
                if m_cur:
                    current_active_id = m_cur.group(1).strip()

                items = re.split(r"\n\s*-\s+", p_content)
                for itm in items:
                    m_id = re.search(r"(?:id|uid):\s*['\"]?([^'\"\r\n]+)['\"]?", itm)
                    m_name = re.search(r"name:\s*['\"]?([^'\"\r\n]+)['\"]?", itm)
                    if m_id and m_name:
                        profile_names_map[m_id.group(1).strip()] = m_name.group(1).strip()
            except Exception:
                pass

        yaml_files = glob.glob(os.path.join(BASE_DIR, "*.yaml"))
        self.file_items = []

        for fpath in yaml_files:
            fname = os.path.basename(fpath)
            if fname == "verge_filter_rules.yaml":
                continue
            nodes, details = self.extract_nodes_and_details_from_file(fpath)
            self.node_details.update(details)

            f_stem = os.path.splitext(fname)[0]
            display_title = profile_names_map.get(f_stem, fname)

            self.file_items.append(
                {
                    "display": f"{display_title} [{fname}] ({len(nodes)} 节点)",
                    "path": fpath,
                    "nodes": nodes,
                    "details": details,
                    "stem": f_stem,
                    "fname": fname,
                }
            )

        if not self.file_items:
            return

        active_idx = 0
        if current_active_id:
            curr_stem = os.path.splitext(current_active_id)[0]
            for idx, itm in enumerate(self.file_items):
                if itm["stem"] == curr_stem or itm["fname"] == current_active_id:
                    active_idx = idx
                    break

        self.file_combo["values"] = [item["display"] for item in self.file_items]
        self.file_combo.current(active_idx)
        self.apply_profile_selection(active_idx)

    def on_file_changed(self, event):
        idx = self.file_combo.current()
        if idx >= 0:
            self.apply_profile_selection(idx)

    def apply_profile_selection(self, idx):
        self.all_nodes = self.file_items[idx]["nodes"]
        self.node_details.update(self.file_items[idx].get("details", {}))
        self.auto_filter_and_blacklist_non_asia_nodes()
        self.align_favorites_with_current_subscription()
        self.refresh_tables()
        self.refresh_verified_table()
        self.refresh_stars_table()

    def update_remote_subscription(self, target_yaml_path):
        mixed_port = self.get_clash_mixed_port()
        return update_remote_subscription(
            target_yaml_path,
            mixed_port=mixed_port,
            on_step_callback=lambda txt: self.root.after(0, lambda: self.status_label.config(text=txt)),
        )

    def update_subscription_and_reactivate(self, on_step_callback=None, on_finish_callback=None):
        """通用订阅更新与热激活闭环：拉取最新远程订阅 -> 重新解析节点 -> 写入Script.js -> 触发热键 -> 探测内核装载"""
        def _worker():
            cur_idx = self.file_combo.current()
            cur_file_info = self.file_items[cur_idx] if (cur_idx >= 0 and cur_idx < len(self.file_items)) else None

            if not cur_file_info or not os.path.exists(cur_file_info["path"]):
                err_msg = "未检测到当前选中的有效订阅配置文件！"
                self.log(f"⚠️ {err_msg}")
                if on_step_callback:
                    self.root.after(0, lambda: on_step_callback("error", err_msg))
                if on_finish_callback:
                    self.root.after(0, lambda: on_finish_callback(False, err_msg, []))
                return

            logs_step = []
            if on_step_callback:
                self.root.after(0, lambda: on_step_callback("step", "正在拉取远程最新订阅 (多通道重试)..."))

            up_ok, up_msg, content_changed = self.update_remote_subscription(cur_file_info["path"])
            if not up_ok:
                logs_step.append(f"⚠️ 订阅拉取提示: {up_msg}")
                self.log(f"订阅拉取提示: {up_msg}")
            else:
                logs_step.append(f"✅ 订阅更新成功: {up_msg}")
                self.log(f"订阅更新成功: {up_msg}")

            new_nodes, new_details = self.extract_nodes_and_details_from_file(cur_file_info["path"])
            if new_nodes:
                self.all_nodes = new_nodes
                self.node_details.update(new_details)
                cur_file_info["nodes"] = new_nodes
                cur_file_info["details"] = new_details
                logs_step.append(f"✅ 解析出 {len(new_nodes)} 个代理节点")
                b_cnt = self.auto_filter_and_blacklist_non_asia_nodes()
                if b_cnt > 0:
                    logs_step.append(f"🛡️ 自动拉黑非亚洲节点: 已直接拉黑淘汰 {b_cnt} 个非亚洲节点")
                # 仅对齐本地优质精选池至当前订阅更名，坚决不从远端旧文件覆写本地复检成果
                self.align_favorites_with_current_subscription()
                logs_step.append(f"⭐ 优质精选池更名对齐: 当前有效存活 {len(self.favorites)} 个节点")

            # 写入 Script.js
            write_ok, write_err = self.do_write_script_file(list(self.favorites))
            if write_ok:
                logs_step.append("✅ 已重新生成并写入 Script.js 脚本规则")
            else:
                logs_step.append(f"⚠️ 写入 Script.js: {write_err}")

            # 触发热键
            if on_step_callback:
                self.root.after(0, lambda: on_step_callback("step", "正在触发热键通知内核装载新节点..."))
            time.sleep(0.3)
            hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()
            if hotkey_ok:
                logs_step.append("✅ 已模拟全局热键 (Ctrl+Shift+F12) 激活 Clash Verge")
            else:
                logs_step.append(f"⚠️ 触发快捷键提示: {hotkey_msg}")

            # 探测内核装载
            loaded_ok = False
            loaded_msg = ""
            if self.all_nodes:
                if on_step_callback:
                    self.root.after(0, lambda: on_step_callback("step", "正在探测内核装载状态..."))
                loaded_ok, loaded_msg = self.wait_for_kernel_reload(self.all_nodes, max_wait_sec=10)
                logs_step.append(f"{'✅' if loaded_ok else '⚠️'} 内核装载: {loaded_msg}")
                self.log(f"内核装载探测: {loaded_msg}")

            self.root.after(0, self.refresh_tables)
            self.root.after(0, self.refresh_verified_table)
            self.root.after(0, self.refresh_stars_table)

            final_ok = up_ok or loaded_ok
            if on_finish_callback:
                self.root.after(0, lambda: on_finish_callback(final_ok, up_msg, logs_step))

        threading.Thread(target=_worker, daemon=True).start()

    def manual_update_subscription_and_reactivate(self):
        """用户手动点击【🔄 更新当前订阅】触发的闭环处理"""
        cur_idx = self.file_combo.current()
        cur_file_info = self.file_items[cur_idx] if (cur_idx >= 0 and cur_idx < len(self.file_items)) else None
        if not cur_file_info:
            messagebox.showwarning("提示", "未找到当前选中的有效订阅文件！")
            return

        self.status_label.config(text="正在拉取最新订阅并触发热更新激活...")
        self.log("手动触发订阅更新与热激活闭环...")

        def _on_step(mode, text):
            self.status_label.config(text=text)

        def _on_finish(ok, msg, steps):
            if ok:
                full_msg = f"🎉 订阅更新与热更新激活成功！\n\n" + "\n".join(steps)
                self.status_label.config(text="订阅更新与热激活成功！")
                messagebox.showinfo("更新成功", full_msg)
            else:
                self.status_label.config(text="订阅更新或激活未完全成功")
                messagebox.showwarning("更新提示", f"订阅拉取或激活未完全成功：\n\n{msg}\n\n" + "\n".join(steps))

        self.update_subscription_and_reactivate(on_step_callback=_on_step, on_finish_callback=_on_finish)

    def clear_test_history(self, silent=False):
        if not silent:
            if not self.node_delays and not self.node_history and not self.node_speeds:
                messagebox.showinfo("提示", "当前没有测速记录！")
                return
            if not messagebox.askyesno(
                "清空确认",
                "确定要清空所有测速数据与延迟趋势记录吗？\n（不会清空您的黑名单及下行带宽历史）",
            ):
                return

        self.node_delays.clear()
        self.node_history.clear()
        self.node_speeds.clear()

        threading.Thread(
            target=lambda: self._call_api("/configs?force=true", method="PUT", data=b'{"path":""}'),
            daemon=True,
        ).start()

        self.status_label.config(text="测速记录已归零")
        self.log("所有测速与延迟记录已手动清空。")
        if getattr(self, "_is_initialized", False) or not silent:
            self.refresh_tables()

    def sync_existing_delays(self):
        data = self._call_api("/proxies")
        if not data or "proxies" not in data:
            return

        proxies = data["proxies"]
        updated = False

        try:
            target_rounds = max(1, int(self.test_rounds_var.get().strip())) if self.test_rounds_var.get().strip().isdigit() else 4
        except Exception:
            target_rounds = 4

        for name, info in proxies.items():
            history = info.get("history", [])
            if history:
                delays = [
                    h.get("delay", 0)
                    for h in history
                    if isinstance(h.get("delay"), int)
                ]
                normalized = [d if d > 0 else 99999 for d in delays]
                if normalized:
                    self.node_history[name] = normalized[-target_rounds:]
                    self.node_delays[name] = normalized[-1]
                    updated = True

        if updated:
            self.root.after(0, self.refresh_tables)
            self.log("已成功从内核同步现有节点延迟历史。")

    def stop_pipeline(self):
        self.is_pipeline_running = False
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 正在停止...")
        self.status_label.config(text="已发送停止指令，正在安全收尾...")
        self.log("已收到手动中止指令，正在收尾...")

    def _on_schedule_toggle(self):
        if self.schedule_enabled_var.get():
            self.sched_status_label.config(text="● 全局定时运行中", fg=THEME["accent_green"])
        else:
            self.sched_status_label.config(text="(全局定时未启动)", fg=THEME["text_muted"])

    def _on_fav_schedule_toggle(self):
        if self.fav_schedule_enabled_var.get():
            self.fav_sched_status_label.config(text="● 优质定时运行中", fg=THEME["accent_green"])
        else:
            self.fav_sched_status_label.config(text="(优质定时未启动)", fg=THEME["text_muted"])

    def _scheduler_daemon_loop(self):
        self.scheduler = SchedulerDaemon(
            get_config_fn=lambda: {
                "is_pipeline_running": self.is_pipeline_running,
                "schedule_enabled": self.schedule_enabled_var.get(),
                "schedule_times": self.schedule_times_var.get(),
                "schedule_interval": self.schedule_interval_var.get(),
                "fav_schedule_enabled": self.fav_schedule_enabled_var.get(),
                "fav_schedule_interval": self.fav_schedule_interval_var.get(),
            },
            on_trigger_full=lambda reason: self.root.after(0, lambda r=reason: self._trigger_scheduled_full_pipeline(r)),
            on_trigger_fav=lambda reason: self.root.after(0, lambda r=reason: self._trigger_scheduled_fav_pipeline(r)),
        )
        self.scheduler.update_last_run(self.last_full_run_timestamp, self.last_fav_run_timestamp)
        self.scheduler.start()

    def _trigger_scheduled_full_pipeline(self, reason):
        if not self.is_pipeline_running:
            self.log(f"⏰ 全局定时触发（{reason}），启动全自动优选")
            self.status_label.config(text=f"⏰ 全局定时触发（{reason}），启动全自动优选...")
            self.start_full_auto_pipeline()

    def _trigger_scheduled_fav_pipeline(self, reason):
        if not self.is_pipeline_running:
            self.log(f"⏰ 优质复检触发（{reason}），启动优质池测试")
            self.status_label.config(text=f"⏰ 优质复检触发（{reason}），启动优质池测试...")
            self.start_fav_review_pipeline()

    def save_group_config_and_reload(self):
        inter_str = self.group_interval_var.get().strip()
        tol_str = self.group_tolerance_var.get().strip()
        star_inter_str = self.star_group_interval_var.get().strip()
        star_tol_str = self.star_group_tolerance_var.get().strip()

        for val, name in [
            (inter_str, "常规间隔"),
            (tol_str, "常规容差"),
            (star_inter_str, "典藏间隔"),
            (star_tol_str, "典藏容差"),
        ]:
            if not val.isdigit() or int(val) < 0:
                messagebox.showerror("参数错误", f"{name} 必须为纯正整数！")
                return

        self.save_persisted_config()

        script_path = DEFAULT_SCRIPT_JS
        if not os.path.exists(script_path):
            js_files = glob.glob(os.path.join(BASE_DIR, "*.js"))
            if js_files:
                script_path = js_files[0]

        if not os.path.exists(script_path):
            ok, err = self.do_write_script_file(list(self.favorites))
            if ok:
                time.sleep(0.2)
                trigger_verge_reactivate_hotkey()
                self.log(f"策略组配置已更新 (常规:{inter_str}s, 典藏:{star_inter_str}s)")
                messagebox.showinfo("成功", "已生成新脚本并应用三代理组测速设置！")
            else:
                messagebox.showerror("失败", f"生成脚本失败: {err}")
            return

        try:
            with open(script_path, "r", encoding="utf-8") as f:
                content = f.read()

            new_content = re.sub(r"const groupInterval = \d+;", f"const groupInterval = {inter_str};", content)
            new_content = re.sub(r"const groupTolerance = \d+;", f"const groupTolerance = {tol_str};", new_content)
            new_content = re.sub(r"const starsGroupInterval = \d+;", f"const starsGroupInterval = {star_inter_str};", new_content)
            new_content = re.sub(r"const starsGroupTolerance = \d+;", f"const starsGroupTolerance = {star_tol_str};", new_content)

            if "autoGroupStars" not in new_content:
                ok, err = self.do_write_script_file(list(self.favorites))
                if not ok:
                    messagebox.showerror("更新失败", f"更新 Script.js 失败：{err}")
                    return
            else:
                with open(script_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                self.root.clipboard_clear()
                self.root.clipboard_append(new_content)

            time.sleep(0.2)
            hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()

            msg = (
                f"✅ 三大策略组测速配置已更新成功！\n\n"
                f"• 常规组 (自动/非香港)：间隔 {inter_str}s，容差 {tol_str}ms\n"
                f"• 典藏专属组 (典藏)：间隔 {star_inter_str}s，容差 {star_tol_str}ms\n\n"
            )
            if hotkey_ok:
                msg += "⚡ 已通过全局热键触发 Verge 即时热更生效！全部节点列表完好保留。"
            else:
                msg += f"⚠️ 已修改脚本，热键模拟触发失败({hotkey_msg})，请手动按 Ctrl+Shift+F12 刷新。"

            self.status_label.config(text=f"策略组测速参数已更新 (常规:{inter_str}s, 典藏:{star_inter_str}s)")
            self.log(f"策略组测速参数已更新 (常规:{inter_str}s, 典藏:{star_inter_str}s) 并热键重载")
            messagebox.showinfo("保存并热更成功", msg)
        except Exception as ex:
            messagebox.showerror("更新失败", f"修改 Script.js 失败：\n{str(ex)}")

    # ==================== 全量大优选 (含 7 天 Colo 轨迹更新) ====================
    def start_full_auto_pipeline(self):
        if self.is_pipeline_running:
            return

        self.last_full_run_timestamp = time.time()
        self.save_persisted_config()
        self.update_last_run_display()
        self.log("🚀 启动一整套全自动大优选流程...")

        try:
            max_delay = int(self.max_delay_threshold_var.get().strip()) if self.max_delay_threshold_var.get().strip().isdigit() else 100
            min_speed = float(self.min_speed_threshold_var.get().strip()) if self.min_speed_threshold_var.get().strip() else 5.0
            rounds = max(1, int(self.test_rounds_var.get().strip())) if self.test_rounds_var.get().strip().isdigit() else 4
            timeout_ms = int(self.test_timeout_var.get().strip()) if hasattr(self, "test_timeout_var") and self.test_timeout_var.get().strip().isdigit() else 1500
            try:
                duration = max(0.5, float(self.speed_duration_var.get().strip()))
            except Exception:
                duration = 3.0

            bl_delay_threshold = int(self.blacklist_threshold_var.get().strip()) if self.blacklist_threshold_var.get().strip().isdigit() else 130
            speed_bl_threshold = float(self.speed_bl_threshold_var.get().strip()) if self.speed_bl_threshold_var.get().strip() else 1.0
            speed_bl_rounds = max(1, int(self.speed_bl_rounds_var.get().strip())) if self.speed_bl_rounds_var.get().strip().isdigit() else 4
            jitter_min_d = int(self.jitter_min_delay_var.get().strip()) if hasattr(self, "jitter_min_delay_var") and self.jitter_min_delay_var.get().strip().isdigit() else 80
            jitter_up_th = int(self.jitter_up_threshold_var.get().strip()) if hasattr(self, "jitter_up_threshold_var") and self.jitter_up_threshold_var.get().strip().isdigit() else 20

            test_url = self.test_url_var.get().strip()
            speed_url = self.speed_url_var.get().strip()

            target_cnt_str = self.target_node_count_var.get().strip() if hasattr(self, "target_node_count_var") else ""
            target_node_limit = int(target_cnt_str) if (target_cnt_str.isdigit() and int(target_cnt_str) > 0) else 0
        except Exception as err:
            if not self.root.winfo_viewable():
                send_system_notification("优选启动异常", f"参数错误: {str(err)}")
            else:
                messagebox.showerror("参数格式错误", f"请检查输入参数是否正确：\n{str(err)}")
            return

        if not test_url.startswith("http") or not speed_url.startswith("http"):
            if self.root.winfo_viewable():
                messagebox.showerror("参数格式错误", "测试地址与测速源必须以 http:// 或 https:// 开头！")
            return

        if not self.test_connection(auto_sync=False):
            if self.root.winfo_viewable():
                messagebox.showwarning("提示", "无法连接内核！")
            return

        self.is_pipeline_running = True
        self.btn_run_pipeline.config(state="disabled")
        self.btn_stop_pipeline.config(state="normal", text="⏹ 终止任务")
        self.file_combo.config(state="disabled")

        def _pipeline_worker():
            try:
                cur_idx = self.file_combo.current()
                cur_file_info = self.file_items[cur_idx] if (cur_idx >= 0 and cur_idx < len(self.file_items)) else None

                if not cur_file_info:
                    self.root.after(0, lambda: self._on_fetch_failed_abort("未检测到当前有效的订阅文件！"))
                    return

                self.root.after(0, lambda: self.status_label.config(text="[步骤 1/4] 正在拉取远程最新订阅 (多通道重试)..."))
                up_ok, up_msg, content_changed = self.update_remote_subscription(cur_file_info["path"])

                if not up_ok:
                    self.root.after(0, lambda m=up_msg: self._on_fetch_failed_abort(m))
                    return

                new_nodes, new_details = self.extract_nodes_and_details_from_file(cur_file_info["path"])
                if not new_nodes:
                    self.root.after(0, lambda: self._on_fetch_failed_abort("订阅文件拉取成功，但未能解析出任何代理节点！"))
                    return

                self.all_nodes = new_nodes
                self.node_details.update(new_details)
                cur_file_info["nodes"] = new_nodes
                cur_file_info["details"] = new_details
                self.auto_filter_and_blacklist_non_asia_nodes()
                self.root.after(0, self.refresh_tables)
                self.root.after(0, self.refresh_verified_table)
                self.root.after(0, self.refresh_stars_table)

                if content_changed:
                    self.log("订阅内容已更新(MD5变动)，触发热键通知内核装载新节点...")
                    self.root.after(0, lambda: self.status_label.config(text="[步骤 1/4] 订阅更新(MD5变动)，正在触发热键并检测内核装载..."))
                    trigger_verge_reactivate_hotkey()

                    loaded_ok, loaded_msg = self.wait_for_kernel_reload(new_nodes, max_wait_sec=15)
                    self.log(f"内核指纹探针反馈: {loaded_msg}")
                    if loaded_ok:
                        self.root.after(0, lambda m=loaded_msg: self.status_label.config(text=f"[步骤 1/4] {m}"))
                    else:
                        self.root.after(0, lambda m=loaded_msg: self.status_label.config(text=f"[步骤 1/4] ⚠️ 警告：{m}"))
                    time.sleep(0.8)
                else:
                    self.log("订阅源内容未发生任何改变 (MD5一致)，跳过热键与内核重载，无缝开测！")
                    self.root.after(0, lambda: self.status_label.config(text="[步骤 1/4] 订阅MD5一致，跳过重载直接开测"))
                    time.sleep(0.2)

                # 尝试从 /auto.txt 获取云端优质保活端点，双重确保绝对去重
                cloud_eps = self.fetch_auto_endpoints_from_cloud()
                if cloud_eps:
                    self.auto_endpoints.update(cloud_eps)

                fav_eps, bl_eps, sbl_eps, star_eps = self.get_pool_endpoint_sets()

                ep_to_untested = {}
                fav_sk = 0
                d_sk = 0
                s_sk = 0
                ver_sk = 0

                for n in self.all_nodes:
                    if not self.is_asian_node(n):
                        if n not in self.local_blacklist:
                            self.local_blacklist.add(n)
                        continue

                    ep = self.get_node_endpoint(n)
                    if n in self.local_blacklist or (ep and ep in self.local_blacklist):
                        d_sk += 1
                        continue
                    if n in self.speed_blacklist or (ep and ep in self.speed_blacklist):
                        s_sk += 1
                        continue
                    # 核心去重：命中优质精选、auto.txt 云端保活或孵化端点，一律跳过初测（绝不多重收录同端点冗余马甲）
                    if n in self.favorites or (ep and ep in fav_eps):
                        # ★ 新增：精选节点快速漂移/非亚洲审查
                        _should_purge = False
                        _purge_reason = ""
                        if not self.is_asian_node(n):
                            _should_purge = True
                            _purge_reason = "非亚洲地区/命名"
                        else:
                            colo_hist = self.node_colo_history.get(n, self.node_colo_history.get(ep, []))
                            if colo_hist:
                                _dom, _, _has_drift, _drift_disp = self.analyze_colo_stats(colo_hist, time.time(), node_name=n)
                                if _has_drift or not self.is_asian_node(n, colo=_dom):
                                    _should_purge = True
                                    _purge_reason = f"机房漂移 ({_drift_disp})"
                        if _should_purge:
                            self.local_blacklist.add(n)
                            self.favorites.discard(n)
                            self.record_blacklist_reason(n, _purge_reason)
                            if ep:
                                self.local_blacklist.add(ep)
                                self.record_blacklist_reason(ep, _purge_reason)
                                fav_eps.discard(ep)
                                for f in list(self.favorites):
                                    if self.get_node_endpoint(f) == ep:
                                        self.favorites.discard(f)
                            if ep and hasattr(self, "verified_nodes") and ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                            self.log(f"【精选审查淘汰】节点 {n} 命中规则：{_purge_reason}，已从精选清除并加入黑名单！")
                            continue  # 已拉黑，无需进测试队列
                        # ★ 未触发审查的精选节点，正常跳过
                        fav_sk += 1
                        continue
                    if (n in getattr(self, "verified_nodes", {})) or (ep and ep in star_eps):
                        ver_sk += 1
                        continue

                    ep_to_untested.setdefault(ep, []).append(n)

                unique_eps = list(ep_to_untested.keys())
                test_targets = [self.choose_canonical_node_name(ep_to_untested[ep]) for ep in unique_eps]
                total_untested_nodes = sum(len(nodes) for nodes in ep_to_untested.values())

                self.log(f"全量节点: {len(new_nodes)} 个 | 严格限制亚洲节点 | 跳过已知精选: {fav_sk} | 跳过延迟黑名单: {d_sk} | 跳过低速黑名单: {s_sk} | 待测独立节点: {len(test_targets)} 个 (同源马甲已自动聚合)")

                if not self.is_pipeline_running:
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                if not test_targets:
                    self.root.after(0, lambda: self._on_pipeline_error("所有节点均位于精选、黑名单或沉淀池中，无新的待测节点！"))
                    return

                self.log(f"开始执行 {rounds} 轮延迟初筛 (独立端点纯净版: 共 {len(unique_eps)} 个)...")
                for r in range(1, rounds + 1):
                    if not self.is_pipeline_running:
                        break

                    total = len(unique_eps)
                    done = [0]
                    round_ep_delays = {}

                    def _single_delay(endpoint):
                        if not self.is_pipeline_running:
                            return
                        rep_node = self.choose_canonical_node_name(ep_to_untested[endpoint])
                        enc_name = urllib.parse.quote(rep_node, safe="")
                        enc_url = urllib.parse.quote(test_url, safe="")
                        endpoint_url = f"/proxies/{enc_name}/delay?timeout={timeout_ms}&url={enc_url}"
                        res = self._call_api(endpoint_url, timeout=(timeout_ms / 1000.0) + 0.6)

                        cur_delay = res["delay"] if (res and "delay" in res) else 99999
                        round_ep_delays[endpoint] = cur_delay
                        if cur_delay < 99999:
                            self.record_delay_sample(endpoint, cur_delay)

                        for n in ep_to_untested[endpoint]:
                            self.node_delays[n] = cur_delay
                            if n not in self.node_history:
                                self.node_history[n] = []
                            self.node_history[n].append(cur_delay)
                            self.node_history[n] = self.node_history[n][-rounds:]
                            if cur_delay < 99999:
                                self.record_delay_sample(n, cur_delay)

                        done[0] += 1
                        if done[0] % 5 == 0 or done[0] >= total:
                            self.root.after(
                                0,
                                lambda: self.status_label.config(
                                    text=f"[步骤 2/4] 延迟初筛中: 第 {r}/{rounds} 轮 ({min(done[0], total)}/{total})"
                                ),
                            )

                    with ThreadPoolExecutor(max_workers=10) as executor:
                        list(executor.map(_single_delay, unique_eps))

                    self.root.after(0, self.refresh_tables)
                    if not self.is_pipeline_running:
                        break
                    time.sleep(1)

                if not self.is_pipeline_running:
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                candidates = []
                newly_delay_blacklisted = 0

                for n in test_targets:
                    hist = self.node_history.get(n, [])
                    best_delay = min(hist[-rounds:]) if hist else 99999

                    # 严格拉黑淘汰：延迟未达到设定要求(> max_delay)或超时(>= 99999)，直接加入延迟黑名单并淘汰
                    if best_delay > max_delay or best_delay >= bl_delay_threshold or best_delay >= 99999:
                        if best_delay >= 99999:
                            d_reason = "延迟超时 (≥99999ms)"
                        elif best_delay >= bl_delay_threshold:
                            d_reason = f"延迟超标 ({best_delay}ms ≥ {bl_delay_threshold}ms)"
                        else:
                            d_reason = f"延迟淘汰 ({best_delay}ms > {max_delay}ms)"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, d_reason)
                        ep = self.get_node_endpoint(n)
                        if ep:
                            self.local_blacklist.add(ep)
                            self.record_blacklist_reason(ep, d_reason)
                        for same_n in ep_to_untested.get(ep, []):
                            self.local_blacklist.add(same_n)
                            self.favorites.discard(same_n)
                            self.record_blacklist_reason(same_n, d_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        newly_delay_blacklisted += 1
                        continue

                    # 节点抖动拉黑机制：最低延迟≥设定值且向上抖动≥设定值，立即拉黑淘汰（最高延迟<设定最低延迟则豁免）
                    is_j_bad, j_min, j_up = self.check_node_jitter_blacklisted(
                        hist[-rounds:], jitter_min_d, jitter_up_th
                    )
                    if is_j_bad:
                        j_reason = f"延迟抖动淘汰 (底{j_min}ms 抖动+{j_up}ms)"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, j_reason)
                        ep = self.get_node_endpoint(n)
                        if ep:
                            self.local_blacklist.add(ep)
                            self.record_blacklist_reason(ep, j_reason)
                        for same_n in ep_to_untested.get(ep, []):
                            self.local_blacklist.add(same_n)
                            self.favorites.discard(same_n)
                            self.record_blacklist_reason(same_n, j_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        newly_delay_blacklisted += 1
                        self.log(f"【抖动直接淘汰】节点 {n} 最低延迟 {j_min}ms (≥{jitter_min_d}ms)，向上抖动 +{j_up}ms (≥{jitter_up_th}ms)，立即拉黑淘汰！")
                        continue

                    candidates.append(n)

                if newly_delay_blacklisted > 0:
                    self.save_persisted_config()

                self.root.after(0, self.refresh_tables)
                self.log(f"延迟初筛完成：{len(candidates)} 个候选节点达到 ≤{max_delay}ms (新增延迟拉黑淘汰: {newly_delay_blacklisted} 个)")

                if not candidates:
                    self.root.after(0, lambda: send_system_notification("优选结束", f"待测节点延迟均未达到 ≤{max_delay}ms。"))
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                candidates.sort(key=lambda n: min(self.node_history.get(n, [99999])))

                # 自动采集 Colo 并记入 7 天滑动桶
                self.log(f"正在对 {len(candidates)} 个候选节点校准真实 Colo 并录入 7 天时序桶...")
                def _probe_colo(n):
                    ep = self.get_node_endpoint(n)
                    if ":" in ep:
                        ip, port = ep.split(":", 1)
                        c_code, c_disp = get_cf_colo_raw(ip, port, timeout=1.5)
                        self.record_colo_sample(n, ep, c_code, c_disp)

                with ThreadPoolExecutor(max_workers=15) as ex:
                    list(ex.map(_probe_colo, candidates))
                self.root.after(0, self.refresh_tables)

                # 严格漂移检测：发生机房漂移一次即直接拉黑淘汰！
                drift_passed_candidates = []
                now_pipe_t = time.time()
                for n in candidates:
                    ep = self.get_node_endpoint(n)
                    colo_hist = self.node_colo_history.get(n, self.node_colo_history.get(ep, []))
                    _, _, has_drift, drift_disp = self.analyze_colo_stats(colo_hist, now_pipe_t, node_name=n)
                    if has_drift:
                        drift_reason = f"机房漂移 ({drift_disp})"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, drift_reason)
                        if ep:
                            self.local_blacklist.add(ep)
                            self.record_blacklist_reason(ep, drift_reason)
                        for same_n in ep_to_untested.get(ep, []):
                            self.local_blacklist.add(same_n)
                            self.favorites.discard(same_n)
                            self.record_blacklist_reason(same_n, drift_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        newly_delay_blacklisted += 1
                        self.log(f"【漂移直接淘汰】节点 {n} 发生机房漂移 ({drift_disp})，直接拉黑并清除！")
                    else:
                        drift_passed_candidates.append(n)

                candidates = [n for n in drift_passed_candidates if self.is_asian_node(n)]
                if newly_delay_blacklisted > 0:
                    self.save_persisted_config()
                self.root.after(0, self.refresh_tables)

                if not candidates:
                    self.root.after(0, lambda: send_system_notification("优选结束", "候选节点均发生机房漂移已被全部淘汰。"))
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                proxies_data = self._call_api("/proxies") or {}
                proxies_map = proxies_data.get("proxies", {})
                global_info = proxies_map.get("GLOBAL", {})
                orig_global = global_info.get("now", "")
                global_all = global_info.get("all", [])

                mixed_port = self.get_clash_mixed_port()
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

                proxy_handler = urllib.request.ProxyHandler({
                    "http": f"http://127.0.0.1:{mixed_port}",
                    "https": f"http://127.0.0.1:{mixed_port}",
                })
                https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
                speed_opener = urllib.request.build_opener(proxy_handler, https_handler)

                total_cand = len(candidates)
                orig_group_selections = {}
                premium_nodes = []
                tested_endpoint_speeds = {}
                hit_target_early = False
                newly_speed_blacklisted = 0

                mode_guard = ClashModeGuard(self.clash_client, temporary_mode="global")
                mode_guard.__enter__()
                try:

                    for idx, node_name in enumerate(candidates, 1):
                        if not self.is_pipeline_running:
                            break

                        ep = self.get_node_endpoint(node_name)
                        target_str = f" [已集齐: {len(premium_nodes)}/{target_node_limit}]" if target_node_limit > 0 else f" [全测模式: 已集齐 {len(premium_nodes)} 个]"
                        self.root.after(
                            0,
                            lambda i=idx, n=node_name, ts=target_str: self.status_label.config(
                                text=f"[步骤 3/4] 带宽精测: [{i}/{total_cand}]{ts} {n[:18]}..."
                            ),
                        )

                        if ep in tested_endpoint_speeds:
                            speed_val = tested_endpoint_speeds[ep]
                            self.node_speeds[node_name] = speed_val
                            if node_name not in self.node_speed_history:
                                self.node_speed_history[node_name] = []
                            self.node_speed_history[node_name].append(max(0.0, speed_val))
                            self.node_speed_history[node_name] = self.node_speed_history[node_name][-4:]

                            if speed_val >= min_speed and node_name not in self.speed_blacklist and self.is_asian_node(node_name):
                                premium_nodes.append(node_name)
                                self.favorites.add(node_name)
                                d_val = self.node_delays.get(node_name, 0)
                                self.record_fav_reason(node_name, f"全量优选达标 ({d_val}ms / {speed_val:.2f}MB/s)")
                                self.root.after(0, self.refresh_tables)
                            else:
                                spd_reason = "下行测速中断/失败" if speed_val < 0 else f"下行未达标 ({speed_val:.2f} < {min_speed} MB/s)"
                                self.speed_blacklist.add(node_name)
                                self.favorites.discard(node_name)
                                self.record_blacklist_reason(node_name, spd_reason)
                                if ep:
                                    self.speed_blacklist.add(ep)
                                    self.record_blacklist_reason(ep, spd_reason)
                                for same_n in ep_to_untested.get(ep, []):
                                    self.speed_blacklist.add(same_n)
                                    self.favorites.discard(same_n)
                                    self.record_blacklist_reason(same_n, spd_reason)
                                if ep in self.verified_nodes:
                                    del self.verified_nodes[ep]
                                newly_speed_blacklisted += 1
                                self.log(f"【低速直接淘汰】节点 {node_name} 速度 {speed_val:.2f} MB/s 未达标(≥{min_speed} MB/s)，直接拉黑！")
                            continue

                        target_group = None
                        if "🚀 节点选择" in proxies_map and node_name in proxies_map["🚀 节点选择"].get("all", []):
                            target_group = "🚀 节点选择"
                        elif node_name in global_all:
                            target_group = "GLOBAL"
                        else:
                            for g_name, g_info in proxies_map.items():
                                if g_info.get("type", "").lower() == "selector" and g_name != "GLOBAL":
                                    if node_name in g_info.get("all", []):
                                        target_group = g_name
                                        break

                        if not target_group:
                            self.node_speeds[node_name] = -1.0
                            self.speed_blacklist.add(node_name)
                            self.favorites.discard(node_name)
                            self.record_blacklist_reason(node_name, "未找到代理选择策略组")
                            if ep:
                                self.speed_blacklist.add(ep)
                                self.record_blacklist_reason(ep, "未找到代理选择策略组")
                            for same_n in ep_to_untested.get(ep, []):
                                self.speed_blacklist.add(same_n)
                                self.favorites.discard(same_n)
                                self.record_blacklist_reason(same_n, "未找到代理选择策略组")
                            if ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                            newly_speed_blacklisted += 1
                            continue

                        if target_group not in orig_group_selections:
                            orig_group_selections[target_group] = proxies_map.get(target_group, {}).get("now", "")

                        enc_tg = urllib.parse.quote(target_group, safe="")
                        self._call_api(f"/proxies/{enc_tg}", method="PUT", data=json.dumps({"name": node_name}).encode("utf-8"))

                        if target_group != "GLOBAL" and target_group in global_all:
                            enc_glb = urllib.parse.quote("GLOBAL", safe="")
                            self._call_api(f"/proxies/{enc_glb}", method="PUT", data=json.dumps({"name": target_group}).encode("utf-8"))

                        time.sleep(0.1)

                        speed_val = -1.0
                        total_bytes = 0
                        speed_timeout = max(1.5, min(2.5, round(duration + 0.5, 1)))
                        node_deadline = time.time() + duration + 1.0
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
                                    if time.time() >= node_deadline or not self.is_pipeline_running:
                                        break
                                    chunk = resp.read(chunk_size)
                                    if not chunk:
                                        break
                                    total_bytes += len(chunk)

                                elapsed = time.time() - start_time
                                if elapsed > 0 and total_bytes > 0:
                                    speed_val = round((total_bytes / (1024 * 1024)) / elapsed, 2)
                                else:
                                    speed_val = 0.0
                        except Exception:
                            speed_val = -1.0

                        tested_endpoint_speeds[ep] = speed_val
                        self.node_speeds[node_name] = speed_val

                        if node_name not in self.node_speed_history:
                            self.node_speed_history[node_name] = []
                        self.node_speed_history[node_name].append(max(0.0, speed_val))
                        self.node_speed_history[node_name] = self.node_speed_history[node_name][-4:]

                        # 严格拉黑淘汰：单次测速不达标(< min_speed)或失败(<0)直接加入低速黑名单！
                        if speed_val >= min_speed and node_name not in self.speed_blacklist and self.is_asian_node(node_name):
                            premium_nodes.append(node_name)
                            self.favorites.add(node_name)
                            d_val = self.node_delays.get(node_name, 0)
                            self.record_fav_reason(node_name, f"全量优选达标 ({d_val}ms / {speed_val:.2f}MB/s)")
                            self.root.after(0, self.refresh_tables)

                            if target_node_limit > 0 and len(premium_nodes) >= target_node_limit:
                                hit_target_early = True
                                break
                        else:
                            spd_reason = "下行测速中断/失败" if speed_val < 0 else f"下行未达标 ({speed_val:.2f} < {min_speed} MB/s)"
                            self.speed_blacklist.add(node_name)
                            self.favorites.discard(node_name)
                            self.record_blacklist_reason(node_name, spd_reason)
                            if ep:
                                self.speed_blacklist.add(ep)
                                self.record_blacklist_reason(ep, spd_reason)
                            for same_n in ep_to_untested.get(ep, []):
                                self.speed_blacklist.add(same_n)
                                self.favorites.discard(same_n)
                                self.record_blacklist_reason(same_n, spd_reason)
                            if ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                            newly_speed_blacklisted += 1
                            self.log(f"【低速直接淘汰】节点 {node_name} 速度 {speed_val:.2f} MB/s 未达标(≥{min_speed} MB/s)，直接拉黑！")

                finally:
                    for g_name, orig_choice in orig_group_selections.items():
                        if orig_choice:
                            enc = urllib.parse.quote(g_name, safe="")
                            self._call_api(f"/proxies/{enc}", method="PUT", data=json.dumps({"name": orig_choice}).encode("utf-8"))

                    if orig_global:
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self._call_api(f"/proxies/{enc_glb}", method="PUT", data=json.dumps({"name": orig_global}).encode("utf-8"))

                    mode_guard.__exit__(None, None, None)

                if not self.is_pipeline_running:
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                self.root.after(0, lambda: self.status_label.config(text="[步骤 4/4] 写入 Script.js 并触发热键秒级刷新..."))

                self.favorites.update(premium_nodes)
                self.deduplicate_favorites_by_endpoint()
                self.process_verified_lifecycle(list(self.favorites), [])
                self.purge_invalid_and_blacklisted_from_all_pools()
                self.save_persisted_config()
                self.root.after(0, self.refresh_tables)
                self.root.after(0, self.refresh_verified_table)
                self.root.after(0, self.refresh_stars_table)

                write_ok, err_msg = self.do_write_script_file(list(self.favorites))

                hotkey_ok = False
                hotkey_msg = ""
                if write_ok:
                    time.sleep(0.5)
                    hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()

                loaded_ok = False
                loaded_msg = ""
                target_check_nodes = list(self.favorites) if self.favorites else self.all_nodes
                if target_check_nodes:
                    self.root.after(0, lambda: self.status_label.config(text="正在探测 Clash Verge 内核装载状态..."))
                    loaded_ok, loaded_msg = self.wait_for_kernel_reload(target_check_nodes, max_wait_sec=10)
                    self.log(f"内核装载探测: {loaded_msg}")

                cf_ok, cf_msg = False, ""
                if self.get_cf_worker_config()[0]:
                    self.root.after(0, lambda: self.status_label.config(text="正在推送并净化 Cloudflare Worker 三大池..."))
                    cf_ok, cf_msg = self.sync_all_pools_to_cf_worker()
                    self.log(f"Cloudflare Worker 三池全量净化同步: {cf_msg}")

                self.log(f"全量大优选结束：共入选 {len(premium_nodes)} 个优质极速节点，Script.js 规则已写入并触发热重载生效！")

                self.root.after(
                    0,
                    lambda: self._on_pipeline_finished(
                        newly_delay_blacklisted, newly_speed_blacklisted, len(candidates), premium_nodes, max_delay, min_speed, bl_delay_threshold, speed_bl_threshold, speed_bl_rounds, write_ok, err_msg, hotkey_ok, hotkey_msg, hit_target_early, target_node_limit, cf_ok, cf_msg
                    ),
                )

            except Exception as e:
                err_detail = traceback.format_exc()
                self.log(f"执行发生异常：\n{err_detail}")
                self.root.after(0, lambda: self._on_pipeline_error(err_detail))

        threading.Thread(target=_pipeline_worker, daemon=True).start()

    # ==================== 优质池复检 (Colo 轨迹更新) ====================
    def start_fav_review_pipeline(self):
        if self.is_pipeline_running:
            return

        self.last_fav_run_timestamp = time.time()
        self.save_persisted_config()
        self.update_last_run_display()
        self.log("⚡ 启动优质精选池复检流程...")

        try:
            f_max_d = int(self.fav_max_delay_var.get().strip()) if self.fav_max_delay_var.get().strip().isdigit() else 80
            f_min_s = float(self.fav_min_speed_var.get().strip()) if self.fav_min_speed_var.get().strip() else 8.0
            f_rounds = max(1, int(self.fav_rounds_var.get().strip())) if self.fav_rounds_var.get().strip().isdigit() else 2
            try:
                f_duration = max(0.5, float(self.fav_speed_duration_var.get().strip()))
            except Exception:
                f_duration = 2.0
            f_jitter_min_d = int(self.fav_jitter_min_delay_var.get().strip()) if hasattr(self, "fav_jitter_min_delay_var") and self.fav_jitter_min_delay_var.get().strip().isdigit() else 70
            f_jitter_up_th = int(self.fav_jitter_up_threshold_var.get().strip()) if hasattr(self, "fav_jitter_up_threshold_var") and self.fav_jitter_up_threshold_var.get().strip().isdigit() else 15

            target_hk = int(self.fav_target_hk_count_var.get().strip()) if self.fav_target_hk_count_var.get().strip().isdigit() else 3
            target_nohk = int(self.fav_target_nohk_count_var.get().strip()) if self.fav_target_nohk_count_var.get().strip().isdigit() else 5

            test_url = self.test_url_var.get().strip()
            speed_url = self.speed_url_var.get().strip()
            timeout_ms = int(self.test_timeout_var.get().strip()) if self.test_timeout_var.get().strip().isdigit() else 1500
        except Exception as err:
            messagebox.showerror("参数错误", f"优质池专属参数格式错误：\n{str(err)}")
            return

        self.align_favorites_with_current_subscription()
        self.auto_filter_and_blacklist_non_asia_nodes()
        active_fav_targets = [n for n in self.favorites if n in self.all_nodes and self.is_asian_node(n)]

        if not active_fav_targets:
            if self.fav_fallback_enabled_var.get():
                self.root.after(0, lambda: self._trigger_fallback_regeneration("优质池中无存活节点"))
            else:
                self.log("优质池中无存活节点，且已关闭自动唤醒全量大优选。")
                messagebox.showinfo("提示", "优质精选池中暂无可用的存活节点。")
            return

        if not self.test_connection(auto_sync=False):
            messagebox.showwarning("提示", "无法连接内核！")
            return

        for n in active_fav_targets:
            self.node_delays[n] = None
            self.node_history[n] = []
        self.refresh_tables()

        self.is_pipeline_running = True
        self.btn_run_pipeline.config(state="disabled")
        self.btn_stop_pipeline.config(state="normal", text="⏹ 终止任务")
        self.file_combo.config(state="disabled")

        def _fav_worker():
            try:
                tot = len(active_fav_targets)
                self.log(f"优质池待复测节点共 {tot} 个 (端点去重版 | 达标即停={self.fav_quota_early_stop_var.get()})")
                self.root.after(0, lambda: self.status_label.config(text=f"[优质池复测] 正在快速检测 {tot} 个优质候选延迟..."))

                for r in range(1, f_rounds + 1):
                    if not self.is_pipeline_running:
                        break

                    ep_to_nodes = {}
                    for n in active_fav_targets:
                        ep = self.get_node_endpoint(n)
                        ep_to_nodes.setdefault(ep, []).append(n)

                    def _fav_delay(endpoint):
                        if not self.is_pipeline_running:
                            return
                        rep_node = ep_to_nodes[endpoint][0]
                        enc_name = urllib.parse.quote(rep_node, safe="")
                        enc_url = urllib.parse.quote(test_url, safe="")
                        res = self._call_api(f"/proxies/{enc_name}/delay?timeout={timeout_ms}&url={enc_url}", timeout=(timeout_ms / 1000.0) + 0.6)
                        cur_d = res["delay"] if (res and "delay" in res) else 99999
                        if cur_d < 99999:
                            self.record_delay_sample(endpoint, cur_d)

                        for n in ep_to_nodes[endpoint]:
                            self.node_delays[n] = cur_d
                            if n not in self.node_history:
                                self.node_history[n] = []
                            self.node_history[n].append(cur_d)
                            self.node_history[n] = self.node_history[n][-f_rounds:]
                            if cur_d < 99999:
                                self.record_delay_sample(n, cur_d)

                    with ThreadPoolExecutor(max_workers=8) as ex:
                        list(ex.map(_fav_delay, list(ep_to_nodes.keys())))

                    self.root.after(0, self.refresh_tables)
                    if not self.is_pipeline_running:
                        break
                    time.sleep(0.5)

                if not self.is_pipeline_running:
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                # 达标初筛候选先进行实时 Colo 校准与 7 天滑动桶记录
                temp_passed = []
                for n in active_fav_targets:
                    hist = self.node_history.get(n, [99999])
                    best_d = min(hist[-f_rounds:]) if hist else 99999
                    if best_d > f_max_d or best_d >= 99999:
                        d_reason = "延迟超时 (≥99999ms)" if best_d >= 99999 else f"复测延迟淘汰 ({best_d}ms > {f_max_d}ms)"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, d_reason)
                        ep = self.get_node_endpoint(n)
                        if ep:
                            self.record_blacklist_reason(ep, d_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        self.log(f"【优质淘汰-延迟超标】节点 {n} 延迟 {best_d}ms 未达门槛(≤{f_max_d}ms)，直接拉黑淘汰！")
                        continue

                    # 节点抖动拉黑机制：最低延迟≥设定值且向上抖动≥设定值，直接淘汰（最高延迟<设定最低延迟则豁免）
                    is_j_bad, j_min, j_up = self.check_node_jitter_blacklisted(
                        hist[-f_rounds:], f_jitter_min_d, f_jitter_up_th
                    )
                    if is_j_bad:
                        j_reason = f"复测抖动淘汰 (底{j_min}ms 抖动+{j_up}ms)"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, j_reason)
                        ep = self.get_node_endpoint(n)
                        if ep:
                            self.record_blacklist_reason(ep, j_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        self.log(f"【优质淘汰-抖动超标】节点 {n} 最低延迟 {j_min}ms (≥{f_jitter_min_d}ms)，向上抖动 +{j_up}ms (≥{f_jitter_up_th}ms)，直接拉黑淘汰！")
                        continue

                    temp_passed.append(n)

                def _probe_fav_colo(n):
                    ep = self.get_node_endpoint(n)
                    if ":" in ep:
                        ip, port = ep.split(":", 1)
                        c_code, c_disp = get_cf_colo_raw(ip, port, timeout=1.5)
                        self.record_colo_sample(n, ep, c_code, c_disp)

                with ThreadPoolExecutor(max_workers=10) as ex:
                    list(ex.map(_probe_fav_colo, temp_passed))
                self.root.after(0, self.refresh_tables)

                # 严格漂移检测：发生机房漂移一次即直接拉黑淘汰
                drift_passed = []
                now_fav_t = time.time()
                for n in temp_passed:
                    ep = self.get_node_endpoint(n)
                    colo_hist = self.node_colo_history.get(n, self.node_colo_history.get(ep, []))
                    _, _, has_drift, drift_disp = self.analyze_colo_stats(colo_hist, now_fav_t, node_name=n)
                    if has_drift:
                        drift_reason = f"机房漂移 ({drift_disp})"
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, drift_reason)
                        if ep:
                            self.record_blacklist_reason(ep, drift_reason)
                        if ep in self.verified_nodes:
                            del self.verified_nodes[ep]
                        self.log(f"【优质淘汰-机房漂移】节点 {n} 发生机房漂移 ({drift_disp})，直接拉黑淘汰！")
                    else:
                        drift_passed.append(n)
                temp_passed = drift_passed

                hk_candidates = []
                nohk_candidates = []

                for n in temp_passed:
                    if not self.is_asian_node(n):
                        self.local_blacklist.add(n)
                        self.favorites.discard(n)
                        self.record_blacklist_reason(n, "非亚洲地区/命名")
                        continue
                    if self.is_node_hongkong(n):
                        hk_candidates.append(n)
                    else:
                        nohk_candidates.append(n)

                hk_candidates.sort(key=lambda n: min(self.node_history.get(n, [99999])))
                nohk_candidates.sort(key=lambda n: min(self.node_history.get(n, [99999])))
                self.log(f"优质复检初筛通过（经Colo物理核验）：香港候选 {len(hk_candidates)} 个，非香港候选 {len(nohk_candidates)} 个")


                proxies_data = self._call_api("/proxies") or {}
                proxies_map = proxies_data.get("proxies", {})
                global_info = proxies_map.get("GLOBAL", {})
                orig_global = global_info.get("now", "")
                global_all = global_info.get("all", [])

                mixed_port = self.get_clash_mixed_port()
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE
                speed_opener = urllib.request.build_opener(
                    urllib.request.ProxyHandler({
                        "http": f"http://127.0.0.1:{mixed_port}",
                        "https": f"http://127.0.0.1:{mixed_port}",
                    }),
                    urllib.request.HTTPSHandler(context=ssl_ctx)
                )

                qualified_hk = []
                qualified_nohk = []
                tested_ep_speeds = {}
                orig_group_selections = {}
                early_stop_enabled = self.fav_quota_early_stop_var.get()

                fav_mode_guard = ClashModeGuard(self.clash_client, temporary_mode="global")
                fav_mode_guard.__enter__()
                try:

                    def _test_single_speed(n, track_label, cur_cnt, tgt_cnt):
                        ep = self.get_node_endpoint(n)
                        if ep in tested_ep_speeds:
                            spd = tested_ep_speeds[ep]
                            self.node_speeds[n] = spd
                            if n not in self.node_speed_history:
                                self.node_speed_history[n] = []
                            self.node_speed_history[n].append(max(0.0, spd))
                            self.node_speed_history[n] = self.node_speed_history[n][-4:]
                            return spd

                        tgt_text = f"{tgt_cnt}" if early_stop_enabled else "全测"
                        self.root.after(0, lambda: self.status_label.config(
                            text=f"[优质复测-{track_label}] 目标:{cur_cnt}/{tgt_text} | 测速: {n[:18]}..."
                        ))

                        target_group = None
                        if "🚀 节点选择" in proxies_map and n in proxies_map["🚀 节点选择"].get("all", []):
                            target_group = "🚀 节点选择"
                        elif n in global_all:
                            target_group = "GLOBAL"
                        else:
                            for g_name, g_info in proxies_map.items():
                                if g_info.get("type", "").lower() == "selector" and g_name != "GLOBAL":
                                    if n in g_info.get("all", []):
                                        target_group = g_name
                                        break

                        if not target_group:
                            return 0.0

                        if target_group not in orig_group_selections:
                            orig_group_selections[target_group] = proxies_map.get(target_group, {}).get("now", "")

                        enc_tg = urllib.parse.quote(target_group, safe="")
                        self._call_api(f"/proxies/{enc_tg}", method="PUT", data=json.dumps({"name": n}).encode("utf-8"))

                        if target_group != "GLOBAL" and target_group in global_all:
                            enc_glb = urllib.parse.quote("GLOBAL", safe="")
                            self._call_api(f"/proxies/{enc_glb}", method="PUT", data=json.dumps({"name": target_group}).encode("utf-8"))

                        time.sleep(0.1)

                        speed_val = 0.0
                        total_bytes = 0
                        fav_speed_timeout = max(1.5, min(2.5, round(f_duration + 0.5, 1)))
                        fav_node_deadline = time.time() + f_duration + 1.0
                        try:
                            req = urllib.request.Request(
                                speed_url,
                                headers={"User-Agent": "Mozilla/5.0", "Connection": "close"}
                            )
                            with speed_opener.open(req, timeout=fav_speed_timeout) as resp:
                                st = time.time()
                                chunk_size = 16 * 1024
                                while time.time() - st < f_duration:
                                    if time.time() >= fav_node_deadline or not self.is_pipeline_running:
                                        break
                                    ch = resp.read(chunk_size)
                                    if not ch:
                                        break
                                    total_bytes += len(ch)
                                el = time.time() - st
                                speed_val = round((total_bytes / (1024 * 1024)) / el, 2) if (el > 0 and total_bytes > 0) else 0.0
                        except Exception:
                            speed_val = -1.0

                        tested_ep_speeds[ep] = speed_val
                        self.node_speeds[n] = speed_val

                        if n not in self.node_speed_history:
                            self.node_speed_history[n] = []
                        self.node_speed_history[n].append(max(0.0, speed_val))
                        self.node_speed_history[n] = self.node_speed_history[n][-4:]

                        return speed_val

                    for n in hk_candidates:
                        if not self.is_pipeline_running:
                            break
                        if early_stop_enabled and target_hk > 0 and len(qualified_hk) >= target_hk:
                            self.log(f"优质复测-香港队列已达目标 ({len(qualified_hk)}/{target_hk})，早停")
                            break
                        spd = _test_single_speed(n, "香港", len(qualified_hk), target_hk)
                        if spd >= f_min_s:
                            qualified_hk.append(n)
                            cur_d = self.node_delays.get(n, 0)
                            self.record_fav_reason(n, f"复测考核留任 ({cur_d}ms / {spd:.2f}MB/s)")
                            self.root.after(0, self.refresh_tables)
                        else:
                            spd_reason = "下行测速中断/失败" if spd < 0 else f"复测下行淘汰 ({spd:.2f} < {f_min_s} MB/s)"
                            self.speed_blacklist.add(n)
                            self.favorites.discard(n)
                            self.record_blacklist_reason(n, spd_reason)
                            ep = self.get_node_endpoint(n)
                            if ep:
                                self.record_blacklist_reason(ep, spd_reason)
                            if ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                            self.log(f"【优质淘汰-低速淘汰】香港节点 {n} 下行 {spd:.2f} MB/s 未达标(≥{f_min_s} MB/s)，直接拉黑淘汰！")

                    for n in nohk_candidates:
                        if not self.is_pipeline_running:
                            break
                        if early_stop_enabled and target_nohk > 0 and len(qualified_nohk) >= target_nohk:
                            self.log(f"优质复测-非香港队列已达目标 ({len(qualified_nohk)}/{target_nohk})，早停")
                            break
                        spd = _test_single_speed(n, "非香港", len(qualified_nohk), target_nohk)
                        if spd >= f_min_s:
                            qualified_nohk.append(n)
                            cur_d = self.node_delays.get(n, 0)
                            self.record_fav_reason(n, f"复测考核留任 ({cur_d}ms / {spd:.2f}MB/s)")
                            self.root.after(0, self.refresh_tables)
                        else:
                            spd_reason = "下行测速中断/失败" if spd < 0 else f"复测下行淘汰 ({spd:.2f} < {f_min_s} MB/s)"
                            self.speed_blacklist.add(n)
                            self.favorites.discard(n)
                            self.record_blacklist_reason(n, spd_reason)
                            ep = self.get_node_endpoint(n)
                            if ep:
                                self.record_blacklist_reason(ep, spd_reason)
                            if ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                            self.log(f"【优质淘汰-低速淘汰】非香港节点 {n} 下行 {spd:.2f} MB/s 未达标(≥{f_min_s} MB/s)，直接拉黑淘汰！")

                finally:
                    for g_name, orig_choice in orig_group_selections.items():
                        if orig_choice:
                            enc = urllib.parse.quote(g_name, safe="")
                            self._call_api(f"/proxies/{enc}", method="PUT", data=json.dumps({"name": orig_choice}).encode("utf-8"))

                    if orig_global:
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self._call_api(f"/proxies/{enc_glb}", method="PUT", data=json.dumps({"name": orig_global}).encode("utf-8"))

                    fav_mode_guard.__exit__(None, None, None)

                if not self.is_pipeline_running:
                    self.root.after(0, self._on_pipeline_aborted)
                    return

                total_final_selected = qualified_hk + qualified_nohk
                self.save_persisted_config()

                self.process_verified_lifecycle(total_final_selected, active_fav_targets)

                self.root.after(
                    0,
                    lambda: self._on_fav_review_finished(
                        tot, len(qualified_hk), len(qualified_nohk), target_hk, target_nohk, total_final_selected, f_max_d, f_min_s
                    ),
                )

            except Exception as e:
                err_detail = traceback.format_exc()
                self.log(f"优质池复测异常：\n{err_detail}")
                self.root.after(0, lambda: self._on_pipeline_error(err_detail))

        threading.Thread(target=_fav_worker, daemon=True).start()

    def _on_fav_review_finished(self, total_tested, qual_hk_cnt, qual_nohk_cnt, target_hk, target_nohk, total_nodes, f_max_d, f_min_s):
        self.is_pipeline_running = False
        self.btn_run_pipeline.config(state="normal")
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 终止任务")
        self.file_combo.config(state="readonly")
        self.sort_tree(self.trees["fav"], "speed", True)

        self.log(f"优质复检统计：香港达标 {qual_hk_cnt}/{target_hk}，非香港达标 {qual_nohk_cnt}/{target_nohk} (已同步沉淀池)")

        fallback_enabled = self.fav_fallback_enabled_var.get()
        hk_lack = (target_hk > 0 and qual_hk_cnt < target_hk)
        nohk_lack = (target_nohk > 0 and qual_nohk_cnt < target_nohk)

        if fallback_enabled and (hk_lack or nohk_lack):
            reasons = []
            if hk_lack:
                reasons.append(f"香港达标({qual_hk_cnt}/{target_hk})")
            if nohk_lack:
                reasons.append(f"非香港达标({qual_nohk_cnt}/{target_nohk})")
            reason_str = "、".join(reasons)

            if len(total_nodes) > 0:
                self.do_write_script_file(total_nodes)
                trigger_verge_reactivate_hotkey()

            self.log(f"检测到配额不足且已开启唤醒开关，触发自愈大优选：{reason_str}")
            self._trigger_fallback_regeneration(f"优质复测不足：{reason_str}")
            return

        write_ok, err_msg = self.do_write_script_file(total_nodes)
        hotkey_ok = False
        if write_ok:
            time.sleep(0.5)
            hotkey_ok, _ = trigger_verge_reactivate_hotkey()

        target_check_favs = total_nodes if total_nodes else self.all_nodes
        if target_check_favs:
            loaded_ok, loaded_msg = self.wait_for_kernel_reload(target_check_favs, max_wait_sec=10)
            self.log(f"优质复测内核装载探测: {loaded_msg}")

        status_txt = f"优质复测完毕！主力 {qual_hk_cnt} 个香港 + {qual_nohk_cnt} 个非香港已生效"
        self.status_label.config(text=status_txt)
        self.log(f"优质复检已写入 Script.js 并触发热键生效 (香港:{qual_hk_cnt}, 非港:{qual_nohk_cnt})")

        notify_msg = f"优质复检完毕：精选香港 {qual_hk_cnt} 个 + 非香港 {qual_nohk_cnt} 个，热键已刷新生效！"
        send_system_notification("优质复测完毕", notify_msg)

        # 全量同步净化推送远端 Worker 三大池 (/auto.txt, /verified.txt, /)
        if self.get_cf_worker_config()[0]:
            self.sync_all_pools_to_cf_worker()

        if self.root.winfo_viewable():
            mode_desc = "达标即停模式" if self.fav_quota_early_stop_var.get() else "全测获取全部合格模式"
            fallback_desc = "已开启" if fallback_enabled else "已关闭 (不足不唤醒)"
            msg = (
                f"🎯【优质池双轨复检完毕】\n\n"
                f"• 当前运行模式：{mode_desc}\n"
                f"• 不足唤醒大优选：{fallback_desc}\n\n"
                f"• 香港极速主力：{qual_hk_cnt} / {target_hk} 个\n"
                f"• 非香港主力：{qual_nohk_cnt} / {target_nohk} 个\n"
                f"• 标准门槛：[延迟≤{f_max_d}ms 且 下行≥{f_min_s}MB/s]\n\n"
                f"⏳ 达标节点已自动传送至【沉淀孵化池】并记入 7 天滑动 Colo 时序桶追踪考核！\n\n"
            )
            if write_ok and hotkey_ok:
                msg += "✅ 这批极速主力已自动写入 Script.js 并通过热键瞬间刷新 Verge！"
            elif not write_ok:
                msg += f"❌ 自动写入 Script.js 失败：{err_msg}"
            else:
                msg += "⚠️ 已写入 Script.js，热键模拟失败，请手动按下 Ctrl+Shift+F12。"
            messagebox.showinfo("优质复测结果", msg)

    def _trigger_fallback_regeneration(self, reason_detail):
        msg = f"检测到【{reason_detail}】，自动启动全量订阅大优选补充节点池..."
        self.status_label.config(text=f"🔄 自愈闭环触发：{msg}")
        self.log(f"🔄 唤醒动作执行：{msg}")
        send_system_notification("自愈闭环触发", msg)
        self.root.after(800, self.start_full_auto_pipeline)

    def align_favorites_with_current_subscription(self):
        return align_favorites_with_current_subscription(self.favorites, self.all_nodes, self.resolve_node_to_current)

    def deduplicate_favorites_by_endpoint(self):
        favs, _ = deduplicate_favorites_by_endpoint(
            self.favorites,
            self.all_nodes,
            self.node_details,
            self.get_node_endpoint,
            self.choose_canonical_node_name,
        )
        return favs

    def clean_offline_favorites(self):
        return clean_offline_favorites(
            self.favorites,
            self.all_nodes,
            self.local_blacklist,
            self.speed_blacklist,
            self.get_node_endpoint,
        )

    def sync_favorites_to_verge(self, show_notify=True):
        """
        一键双向对齐并即时同步精选池到 Clash Verge 策略组
        """
        self.align_favorites_with_current_subscription()
        self.purge_invalid_and_blacklisted_from_all_pools()
        self.save_persisted_config()
        self.refresh_tables()
        self.refresh_verified_table()
        self.refresh_stars_table()

        fav_list = list(self.favorites)
        write_ok, err_msg = self.do_write_script_file(fav_list)
        if write_ok:
            time.sleep(0.2)
            trigger_verge_reactivate_hotkey()

        if show_notify:
            if write_ok:
                msg = f"✅ 已成功将精选池 {len(fav_list)} 个节点即时写入 Script.js 并热激活 Clash Verge！\n\nClash 策略组【⚡ 自动选择】已完全对齐。"
                self.log(f"一键同步: {len(fav_list)} 个精选节点已写入 Script.js 并热激活 Verge")
                self.status_label.config(text=f"已同步 {len(fav_list)} 个精选节点至 Clash Verge")
                messagebox.showinfo("同步成功", msg)
            else:
                self.log(f"一键同步失败: {err_msg}")
                messagebox.showerror("同步失败", f"写入 Script.js 失败：\n{err_msg}")

    def _on_fetch_failed_abort(self, err_reason):
        self.is_pipeline_running = False
        self.btn_run_pipeline.config(state="normal")
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 终止任务")
        self.file_combo.config(state="readonly")

        tip_msg = f"❌ 远程最新订阅同步失败（{err_reason}），已终止任务，拒绝使用陈旧缓存！"
        self.status_label.config(text=tip_msg)
        self.log(f"订阅同步失败任务中止: {err_reason}")
        send_system_notification("优选终止 (拒绝旧缓存)", f"无法拉取远程最新订阅: {err_reason}。\n已按要求终止任务。")

        if self.root.winfo_viewable():
            messagebox.showerror(
                "订阅同步失败 (任务已终止)",
                f"未能拉取到远程最新订阅节点：\n\n【错误详情】：{err_reason}\n\n已按要求终止后续流程，未对任何本地旧缓存节点进行无效测试！"
            )

    def _on_pipeline_error(self, err_text):
        self.is_pipeline_running = False
        self.btn_run_pipeline.config(state="normal")
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 终止任务")
        self.file_combo.config(state="readonly")
        self.status_label.config(text="执行异常，任务停止")
        self.log(f"流水线异常中止: {err_text}")
        if self.root.winfo_viewable():
            messagebox.showerror("运行异常", f"执行流水线时出现错误：\n\n{err_text}")
        else:
            send_system_notification("优选异常停止", "流水线运行捕获到异常")

    def _on_pipeline_aborted(self):
        self.is_pipeline_running = False
        self.btn_run_pipeline.config(state="normal")
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 终止任务")
        self.file_combo.config(state="readonly")
        self.status_label.config(text="任务已手动中止，正在保护成果并同步至 Verge...")
        self.log("任务已手动中止，正在保护并同步已测精选节点至 Verge...")
        self.align_favorites_with_current_subscription()
        self.purge_invalid_and_blacklisted_from_all_pools()
        self.save_persisted_config()
        self.refresh_tables()
        write_ok, _ = self.do_write_script_file(list(self.favorites))
        if write_ok:
            time.sleep(0.2)
            trigger_verge_reactivate_hotkey()
        self.status_label.config(text="任务已中止，已测成果已安全同步写入 Verge")

    def _on_pipeline_finished(self, new_delay_bl, new_speed_bl, cand_cnt, premium_nodes, max_d, min_s, d_bl_th, s_bl_th, s_bl_rounds, write_ok, err_msg, hotkey_ok, hotkey_msg, hit_early, target_limit, cf_ok, cf_msg):
        self.is_pipeline_running = False
        self.btn_run_pipeline.config(state="normal")
        self.btn_stop_pipeline.config(state="disabled", text="⏹ 终止任务")
        self.file_combo.config(state="readonly")
        self.sort_tree(self.get_current_tree(), "speed", True)

        p_count = len(premium_nodes)
        extra_note = f"（已集齐 {target_limit} 个达标节点提前完成）" if hit_early else "（已全测完毕待测池所有候选）"
        self.status_label.config(text=f"优选完成！精选优质 {p_count} 个并已生效 {extra_note}")

        cf_note = "已同步至 Cloudflare" if cf_ok else (f"Cloudflare 同步失败({cf_msg})" if self.cf_worker_enabled_var.get() else "未开启 Cloudflare 同步")
        notify_msg = f"本次拉黑: 延迟淘汰 {new_delay_bl} 个, 低速淘汰 {new_speed_bl} 个。精选优质 {p_count} 个已生效！({cf_note})"
        send_system_notification("Clash Verge 优选刷新成功", notify_msg)

        if self.root.winfo_viewable():
            msg = (
                f"🎯【全自动优选与热键生效完毕】\n\n"
                f"1. 订阅同步：通过 MD5 哈希校验，确认最新订阅就绪且装载完成。\n"
                f"2. 延迟淘汰：新增 {new_delay_bl} 个节点延迟未达标(>{max_d}ms)或超时抖动，已直接拉黑淘汰(未测速)。\n"
                f"3. 低速淘汰：新增 {new_speed_bl} 个节点测速下行未达标(<{min_s}MB/s)或失败，已直接拉黑淘汰。\n"
                f"4. 优质精选：精选出 {p_count} 个双达标极速节点{extra_note}。\n\n"
            )
            if write_ok and hotkey_ok:
                msg += "✅ 已自动写入 Script.js 并通过热键瞬间激活 Verge！\n"
            elif not write_ok:
                msg += f"❌ 自动写入 Script.js 失败：{err_msg}\n"
            else:
                msg += f"⚠️ 已写入 Script.js，热键模拟触发失败: {hotkey_msg}\n"

            if self.cf_worker_enabled_var.get():
                if cf_ok:
                    msg += f"☁️ Cloudflare Worker 自动池(/auto.txt)推送成功！({cf_msg})\n"
                else:
                    msg += f"⚠️ Cloudflare Worker 推送失败：{cf_msg}\n"

            messagebox.showinfo("优选结果", msg)

    def sync_runtime_clash_yaml_and_reload(self, premium_tokens, star_tokens=None):
        """
        双保险内核热同步：
        直接按照 Script.js 相同规则把优选优质节点更新至 clash-verge.yaml，
        并通过 PUT /configs?force=true 带真实文件路径通知 Mihomo 秒级重载。
        彻底解决 Windows UIPI 权限隔离导致快捷键无法穿透、必须手动在 Verge 内点击激活的问题。
        """
        clash_runtime_yaml = os.path.join(PARENT_DIR, "clash-verge.yaml")
        if not os.path.exists(clash_runtime_yaml):
            return False, "未找到 clash-verge.yaml 运行时文件"

        try:
            import yaml
            with open(clash_runtime_yaml, "r", encoding="utf-8") as f_y:
                rt_cfg = yaml.safe_load(f_y)

            if not rt_cfg or not isinstance(rt_cfg, dict):
                return False, "clash-verge.yaml 配置格式异常"

            rt_proxies = rt_cfg.get("proxies", [])

            def is_premium(p):
                if not premium_tokens:
                    return True
                name = p.get("name", "")
                ep = f"{p.get('server', '')}:{p.get('port', '')}"
                return name in premium_tokens or ep in premium_tokens

            ex_re = re.compile(r"(香港|HK|Hong\s*Kong|HongKong|中国(?!\s*台湾)|大陆|回国|\bCN\b)", re.IGNORECASE)

            # 1. 【⚡ 自动选择】
            seen_auto = set()
            live_auto_proxies = []
            for p in rt_proxies:
                if not isinstance(p, dict):
                    continue
                ep = f"{p.get('server', '')}:{p.get('port', '')}"
                name = p.get("name", "")
                is_auto_node = ("优质保活" in name) or ("auto" in name.lower())
                if is_auto_node and is_premium(p) and ep not in seen_auto:
                    seen_auto.add(ep)
                    live_auto_proxies.append(name)

            for p in rt_proxies:
                if not isinstance(p, dict):
                    continue
                ep = f"{p.get('server', '')}:{p.get('port', '')}"
                name = p.get("name", "")
                if is_premium(p) and ep not in seen_auto:
                    seen_auto.add(ep)
                    live_auto_proxies.append(name)

            if not live_auto_proxies:
                live_auto_proxies = [p["name"] for p in rt_proxies if isinstance(p, dict) and "name" in p]
            if not live_auto_proxies:
                live_auto_proxies = ["DIRECT"]

            # 2. 【⚡ 自动选择 (非香港)】
            seen_nohk = set()
            live_nohk_proxies = []
            for p in rt_proxies:
                if not isinstance(p, dict):
                    continue
                ep = f"{p.get('server', '')}:{p.get('port', '')}"
                name = p.get("name", "")
                is_auto_node = ("优质保活" in name) or ("auto" in name.lower())
                if is_auto_node and is_premium(p) and not ex_re.search(name) and ep not in seen_nohk:
                    seen_nohk.add(ep)
                    live_nohk_proxies.append(name)

            for p in rt_proxies:
                if not isinstance(p, dict):
                    continue
                ep = f"{p.get('server', '')}:{p.get('port', '')}"
                name = p.get("name", "")
                if is_premium(p) and not ex_re.search(name) and ep not in seen_nohk:
                    seen_nohk.add(ep)
                    live_nohk_proxies.append(name)

            if not live_nohk_proxies:
                live_nohk_proxies = [p["name"] for p in rt_proxies if isinstance(p, dict) and "name" in p and not ex_re.search(p["name"])]
            if not live_nohk_proxies:
                live_nohk_proxies = ["DIRECT"]

            # 3. 【⚡ 自动选择 (典藏)】
            live_star_proxies = []
            rt_names = {p.get("name") for p in rt_proxies if isinstance(p, dict)}
            for item in getattr(self, "stars_nodes", []):
                m_n = item.get("matched_name", "")
                rem = item.get("remark", "")
                if m_n and m_n in rt_names:
                    live_star_proxies.append(m_n)
                elif rem and rem in rt_names:
                    live_star_proxies.append(rem)
            live_star_proxies = list(dict.fromkeys(live_star_proxies))
            if not live_star_proxies:
                live_star_proxies = ["DIRECT"]

            auto_group_name = "⚡ 自动选择"
            auto_group_nohk_name = "⚡ 自动选择 (非香港)"
            auto_group_stars_name = "⚡ 自动选择 (典藏)"

            for g in rt_cfg.get("proxy-groups", []):
                g_name = g.get("name", "")
                if g_name == auto_group_name:
                    g["proxies"] = live_auto_proxies
                elif g_name == auto_group_nohk_name:
                    g["proxies"] = live_nohk_proxies
                elif g_name == auto_group_stars_name:
                    g["proxies"] = live_star_proxies

            # 原子写入防并发写坏
            temp_file = clash_runtime_yaml + ".tmp"
            with open(temp_file, "w", encoding="utf-8") as f_out:
                yaml.dump(rt_cfg, f_out, allow_unicode=True, sort_keys=False)
            os.replace(temp_file, clash_runtime_yaml)

            # 热调用内核重载配置（明确传入真实文件路径）
            reload_payload = json.dumps({"path": clash_runtime_yaml}).encode("utf-8")
            self._call_api("/configs?force=true", method="PUT", data=reload_payload)
            return True, f"已热同步至内核，【⚡ 自动选择】生效 {len(live_auto_proxies)} 个优质节点"
        except Exception as y_err:
            return False, str(y_err)

    # ==================== 三代理组 Script.js 生成 ====================
    def do_write_script_file(self, target_nodes=None):
        script_code, premium_tokens, star_tokens = build_script_js(
            favorites=self.favorites,
            stars_nodes=getattr(self, "stars_nodes", []),
            all_nodes=getattr(self, "all_nodes", []),
            node_details=getattr(self, "node_details", {}),
            group_interval=self.group_interval_var.get(),
            group_tolerance=self.group_tolerance_var.get(),
            star_group_interval=self.star_group_interval_var.get(),
            star_group_tolerance=self.star_group_tolerance_var.get(),
            target_nodes=target_nodes,
            is_asian_node_fn=self.is_asian_node,
            get_node_endpoint_fn=self.get_node_endpoint,
            resolve_node_to_current_fn=self.resolve_node_to_current,
            cloud_endpoints=getattr(self, "cloud_endpoints", None),
            node_colo=getattr(self, "node_colo", None),
        )

        ok, write_res = write_script_js(script_code)
        if not ok:
            return False, write_res

        # 核心增强：双引擎热同步 —— 直接原子写入 clash-verge.yaml 并通知 Mihomo API 秒级重载
        sync_ok, sync_msg = self.sync_runtime_clash_yaml_and_reload(premium_tokens, star_tokens)
        if sync_ok:
            self.log(f"双保险内核热同步: {sync_msg}")
        else:
            self.log(f"运行时 YAML 同步提示: {sync_msg}")

        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(script_code)
        except Exception:
            pass
        return True, ""

    def manual_write_and_trigger_hotkey(self):
        target_nodes = list(self.favorites)
        if not target_nodes:
            tree = self.get_current_tree()
            selections = tree.selection()
            if selections:
                target_nodes = [tree.item(s, "values")[-1] for s in selections]

        if not target_nodes:
            messagebox.showwarning("提示", "当前没有选定优质节点，请先设为优质或在列表中多选！")
            return

        ok, err = self.do_write_script_file(target_nodes)
        if ok:
            time.sleep(0.2)
            hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()
            if hotkey_ok:
                messagebox.showinfo(
                    "写入并刷新成功",
                    f"已成功将选中的 {len(target_nodes)} 个节点写入 Script.js，并通过全局热键秒级触发 Verge 重新激活！",
                )
            else:
                messagebox.showinfo(
                    "写入成功",
                    f"已写入 Script.js，热键模拟失败（{hotkey_msg}），请手动在键盘按下 Ctrl+Shift+F12 激活刷新。",
                )
            self.status_label.config(text=f"已成功写入 {len(target_nodes)} 个节点并触发热键")
            self.log(f"手动写入 {len(target_nodes)} 个节点至 Script.js 并触发热键生效")
        else:
            messagebox.showerror("写入失败", f"写入失败：{err}")

    def format_history_chain(self, delays):
        if not delays:
            return "-"
        formatted = []
        for d in delays:
            if d >= 99999 or d <= 0:
                formatted.append("✕超时")
            else:
                formatted.append(f"{d}ms")
        return " → ".join(formatted)

    def format_speed_history_chain(self, speeds):
        if not speeds:
            return "-"
        return " → ".join([f"{s:.2f}M" for s in speeds[-4:]])

    def record_delay_sample(self, key_or_name, delay):
        if not delay or delay >= 99999 or delay <= 0:
            return
        now_ts = time.time()
        ep = self.get_node_endpoint(key_or_name) if key_or_name else ""
        keys_to_update = {key_or_name}
        if ep and ep != "127.0.0.1:443":
            keys_to_update.add(ep)
        cutoff = now_ts - 7 * 86400
        for k in keys_to_update:
            if not k:
                continue
            if k not in self.node_delay_history:
                self.node_delay_history[k] = []
            self.node_delay_history[k].append({"ts": now_ts, "d": int(delay)})
            self.node_delay_history[k] = [
                x for x in self.node_delay_history[k] if isinstance(x, dict) and x.get("ts", 0) >= cutoff
            ][-30:]

    def compute_delay_stats(self, node_name, ep=None):
        return compute_delay_stats(
            node_name,
            ep=ep,
            node_history=getattr(self, "node_history", {}),
            node_delays=getattr(self, "node_delays", {}),
            node_delay_history=getattr(self, "node_delay_history", {}),
            get_node_endpoint_fn=self.get_node_endpoint,
        )

    def check_node_jitter_blacklisted(self, delays, jitter_min_delay=80, jitter_up_threshold=20, min_delay_threshold=None, up_jitter_threshold=None):
        return check_node_jitter_blacklisted(
            delays,
            jitter_min_delay=jitter_min_delay,
            jitter_up_threshold=jitter_up_threshold,
            min_delay_threshold=min_delay_threshold,
            up_jitter_threshold=up_jitter_threshold,
        )




    def test_all_nodes_colo(self):
        # 获取当前选中的标签页索引
        current_tab_idx = self.notebook.index(self.notebook.select())
        tree = self.get_current_tree()
        
        # 从当前标签页的 Treeview 中提取所有行显示的节点/IP
        nodes_to_test = []
        for item_id in tree.get_children(""):
            row_vals = tree.item(item_id, "values")
            if not row_vals:
                continue
            # 依据不同标签页的表格结构提取对应的节点名称或IP
            if current_tab_idx in [2, 3]: # 沉淀孵化池 (2) 或 典藏管理池 (3)
                ep = row_vals[0] # 第一列是 IP:端口
                if ep and ep != "-":
                    nodes_to_test.append(ep)
            else: # 活跃待测、优质精选、黑名单等，最后一列是节点名称
                name = row_vals[-1]
                if name and name != "-":
                    nodes_to_test.append(name)
                    
        if not nodes_to_test:
            tab_names = ["📋 活跃待测", "⭐ 优质精选", "⏳ 沉淀孵化", "🏆 典藏管理", "🚫 延迟黑名单", "🐌 低速黑名单"]
            curr_name = tab_names[current_tab_idx] if current_tab_idx < len(tab_names) else "当前"
            messagebox.showinfo("提示", f"【{curr_name}】标签页当前没有可测速的节点！")
            return
        
        def _worker():
            tab_names = ["📋 活跃待测", "⭐ 优质精选", "⏳ 沉淀孵化", "🏆 典藏管理", "🚫 延迟黑名单", "🐌 低速黑名单"]
            curr_name = tab_names[current_tab_idx] if current_tab_idx < len(tab_names) else "当前标签页"
            
            self.root.after(0, lambda: self.status_label.config(text=f"正在测试【{curr_name}】中 {len(nodes_to_test)} 个节点的实时机房 (Colo)..."))
            self.log(f"开始测试【{curr_name}】标签页下的 {len(nodes_to_test)} 个节点的实时机房 (Colo)...")
            
            completed = [0]
            total = len(nodes_to_test)
            
            def _test_one(target_item):
                if ":" in target_item and any(c.isdigit() for c in target_item.split(":")[0]):
                    ep = target_item
                    n_key = None
                else:
                    n_key = target_item
                    ep = self.get_node_endpoint(n_key)
                    
                if ep and ":" in ep:
                    ip, port = ep.split(":", 1)
                    c_code, c_disp = get_cf_colo_raw(ip, port, timeout=1.8)
                    self.record_colo_sample(n_key, ep, c_code, c_disp)
                    
                completed[0] += 1
                if completed[0] % 5 == 0 or completed[0] == total:
                    self.root.after(0, lambda c=completed[0]: self.status_label.config(text=f"当前页测Colo: {c}/{total}"))
            
            with ThreadPoolExecutor(max_workers=20) as ex:
                list(ex.map(_test_one, nodes_to_test))
                
            # 严格漂移检测：当前页测试后，凡发生机房漂移的节点直接拉黑淘汰并移出所有池
            drift_purged_count = 0
            now_t = time.time()
            for target_item in nodes_to_test:
                if ":" in target_item and any(c.isdigit() for c in target_item.split(":")[0]):
                    ep = target_item
                    n_key = self.resolve_star_matches().get(ep, None)
                else:
                    n_key = target_item
                    ep = self.get_node_endpoint(n_key)
                
                colo_hist = self.node_colo_history.get(n_key, self.node_colo_history.get(ep, []))
                if colo_hist:
                    _, _, has_drift, drift_disp = self.analyze_colo_stats(colo_hist, now_t, node_name=n_key)
                    if has_drift:
                        drift_reason = f"机房漂移 ({drift_disp})"
                        if n_key:
                            self.local_blacklist.add(n_key)
                            self.favorites.discard(n_key)
                            self.record_blacklist_reason(n_key, drift_reason)
                        if ep:
                            self.local_blacklist.add(ep)
                            self.record_blacklist_reason(ep, drift_reason)
                            if ep in self.verified_nodes:
                                del self.verified_nodes[ep]
                        drift_purged_count += 1
                        self.log(f"【页面Colo测定-漂移淘汰】{n_key or ep} 发生机房漂移 ({drift_disp})，直接拉黑并清除！")

            if drift_purged_count > 0:
                self.purge_invalid_and_blacklisted_from_all_pools()
                self.do_write_script_file(list(self.favorites))
                trigger_verge_reactivate_hotkey()
                if self.get_cf_worker_config()[0]:
                    self.sync_all_pools_to_cf_worker()

            self.save_persisted_config()
            self.root.after(0, self.refresh_tables)
            self.root.after(0, self.refresh_verified_table)
            self.root.after(0, self.refresh_stars_table)
            
            self.log(f"【{curr_name}】标签页节点实时机房 (Colo) 检测完成！(漂移淘汰: {drift_purged_count} 个)")
            self.root.after(0, lambda: self.status_label.config(text=f"当前标签页 Colo 检测完成！(漂移淘汰:{drift_purged_count})"))
            finish_msg = f"🎉 已成功完成【{curr_name}】中 {total} 个节点的实时机房 (Colo) 测定！"
            if drift_purged_count > 0:
                finish_msg += f"\n\n⚠️ 检测到 {drift_purged_count} 个节点发生机房漂移，已按超严规则直接拉黑淘汰并从所有池及远端 Worker 彻底清除！"
            self.root.after(0, lambda: messagebox.showinfo("完成", finish_msg))
            
        threading.Thread(target=_worker, daemon=True).start()

    def clear_current_tab_colo_history(self):
        """一键清空当前标签页中所有节点的实时机房(Colo)与7天滑动历史数据"""
        current_tab_idx = self.notebook.index(self.notebook.select())
        if current_tab_idx == 6:
            messagebox.showinfo("提示", "【☁️ 云端文本查看】标签页不支持清空机房记录！")
            return

        tree = self.get_current_tree()
        tab_names = ["📋 活跃待测", "⭐ 优质精选", "⏳ 沉淀孵化", "🏆 典藏管理", "🚫 延迟黑名单", "🐌 低速黑名单", "☁️ 云端文本查看"]
        curr_name = tab_names[current_tab_idx] if current_tab_idx < len(tab_names) else "当前页面"

        items = tree.get_children("")
        if not items:
            messagebox.showinfo("提示", f"【{curr_name}】标签页当前没有节点！")
            return

        if not messagebox.askyesno(
            "确认清空机房(Colo)历史",
            f"确定要清空【{curr_name}】中全部 {len(items)} 个节点的机房(Colo)信息与历史采样记录吗？\n\n"
            "• 该操作将清除最新 Colo 结果与 7 天滑动时序数据；\n"
            "• 归零后可点击【🌍 测当前页Colo】从零开始重新记录，以便精准考核与晋升。"
        ):
            return

        cleared_count = 0
        for item_id in items:
            row_vals = tree.item(item_id, "values")
            if not row_vals:
                continue
            if current_tab_idx in [2, 3]:
                ep = row_vals[0]
                n_key = row_vals[-1] if len(row_vals) >= 7 else ""
            else:
                n_key = row_vals[-1]
                ep = self.get_node_endpoint(n_key)

            keys_to_clean = [n_key, ep]
            if ep and ":" in ep:
                keys_to_clean.append(ep.split(":")[0])

            for k in keys_to_clean:
                if k and k != "-":
                    self.node_colo.pop(k, None)
                    self.node_colo_history.pop(k, None)

            if ep in self.verified_nodes:
                self.verified_nodes[ep]["colo"] = "-"
            for s_node in self.stars_nodes:
                if s_node.get("endpoint") == ep or (n_key and s_node.get("matched_name") == n_key):
                    s_node["colo"] = "-"
            cleared_count += 1

        self.save_persisted_config()
        self.refresh_tables()
        self.refresh_verified_table()
        self.refresh_stars_table()

        msg = f"已清空【{curr_name}】共 {cleared_count} 个节点的机房(Colo)记录与7天历史。"
        self.log(f"🧹 {msg} 可点击【🌍 测当前页Colo】重新录入。")
        self.status_label.config(text=msg)
        messagebox.showinfo("清空成功", f"🎉 {msg}\n\n历史采样数据已归零，现在你可以点击【🌍 测当前页Colo】重新采集纯净数据！")

    def sync_favorites_from_auto_text(self, show_notify=False, source_text=None):
        """
        全量同步 Worker 云端 /auto.txt 优质端点至本地【⭐ 优质精选】：
        1. 获取 Worker 远端 /auto.txt 内容（若传入 source_text 则优先使用，否则从 Worker 拉取，无网络则取云端文本框内容）
        2. 提取有效端点 (IP:端口)，在当前订阅中精准匹配所有对应活跃的亚洲节点加入 favorites
        3. 对比迁移现有 favorites 中更名存活的节点，清除下线失效及非亚洲/黑名单节点
        4. 精准写入 Script.js (严格按节点全名匹配，消除通配误差，确保节点管理器与 Clash Verge 自动选择 1:1 绝对对齐)
        5. 触发全局热键 (Ctrl+Shift+F12) 通知 Clash Verge 即刻重载生效
        6. 同步刷新 UI 表格与状态
        """
        raw_text = source_text if source_text else ""
        fetch_err = ""
        base_url = self.cf_worker_url_var.get().strip().rstrip("/")

        if not raw_text and base_url:
            auto_url = f"{base_url}/auto.txt"
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            mixed_port = self.get_clash_mixed_port()
            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            proxy_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
            direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))

            for opener in [proxy_opener, direct_opener]:
                try:
                    req = urllib.request.Request(auto_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                    with opener.open(req, timeout=6) as resp:
                        raw_text = resp.read().decode("utf-8", errors="ignore")
                        if raw_text:
                            break
                except Exception as e:
                    fetch_err = str(e)

        if not raw_text or "❌ 读取失败" in raw_text or "错误：" in raw_text:
            box_text = self.cloud_text_box.get("1.0", tk.END).strip()
            if box_text and "❌ 读取失败" not in box_text and "错误：" not in box_text:
                raw_text = box_text

        if not raw_text or "❌ 读取失败" in raw_text or "错误：" in raw_text:
            if show_notify:
                messagebox.showwarning("同步提示", f"未能获取到 /auto.txt 的有效内容！\n(Worker 请求提示: {fetch_err})")
            return 0, 0

        # 提取端点集合
        auto_eps = set()
        for line in raw_text.splitlines():
            line = line.strip()
            if not line or line.startswith("⏳") or line.startswith("Error") or line.startswith("❌"):
                continue
            if "#" in line:
                ep_part = line.split("#", 1)[0].strip()
            else:
                ep_part = line.split()[0].strip()
            m = re.search(r"([a-zA-Z0-9\.\-]+:\d{1,5})", ep_part)
            if m:
                auto_eps.add(m.group(1))

        self.auto_endpoints.update(auto_eps)

        # 建立端点 -> 当前订阅活跃亚洲节点映射
        ep_to_nodes = {}
        for n in self.all_nodes:
            if not self.is_asian_node(n):
                continue
            ep = self.get_node_endpoint(n)
            if ep and ep != "127.0.0.1:443":
                ep_to_nodes.setdefault(ep, []).append(n)

        # 将 auto.txt 中命中的活跃亚洲节点加入（严格 1 对 1 端点唯一代表录用）
        for ep in auto_eps:
            if ep in ep_to_nodes:
                cands = ep_to_nodes[ep]
                auto_cands = [c for c in cands if "优质保活" in c or "auto" in c.lower()]
                rep_node = auto_cands[0] if auto_cands else cands[0]
                for n in cands:
                    self.local_blacklist.discard(n)
                    self.speed_blacklist.discard(n)
                synced_favs.add(rep_node)

        # 迁移与保留现有存活且为亚洲的优质节点
        for f in list(self.favorites):
            if not self.is_asian_node(f):
                continue
            if f in self.all_nodes:
                self.local_blacklist.discard(f)
                self.speed_blacklist.discard(f)
                synced_favs.add(f)
            else:
                resolved = self.resolve_node_to_current(f)
                if resolved and resolved in self.all_nodes and self.is_asian_node(resolved):
                    self.local_blacklist.discard(resolved)
                    self.speed_blacklist.discard(resolved)
                    synced_favs.add(resolved)

        self.favorites = synced_favs
        self.deduplicate_favorites_by_endpoint()
        self.save_persisted_config()

        # 写入 Script.js 并触发热键激活
        write_ok, err_msg = self.do_write_script_file(list(self.favorites))
        hotkey_ok = False
        if write_ok:
            time.sleep(0.3)
            hotkey_ok, _ = trigger_verge_reactivate_hotkey()

        # 刷新 UI 表格
        self.refresh_tables()
        self.log(f"☁️ 同步 auto.txt 优质池完成：当前优质精选池共 {len(self.favorites)} 个节点")

        if show_notify:
            msg = (
                f"🎉 【auto.txt 优质池同步完成】！\n\n"
                f"• 从 auto.txt 解析出物理端点: {len(auto_eps)} 个\n"
                f"• 当前订阅匹配活跃亚洲优质节点: {len(self.favorites)} 个\n"
                f"• 【📋 活跃待测】页面已完全过滤排除全部优质候选，仅展示未测试纯净节点\n\n"
            )
            if write_ok and hotkey_ok:
                msg += "✅ 已写入 Script.js 并通过热键瞬间刷新激活 Clash Verge！\n优质精选节点与 Clash【⚡ 自动选择】已实现 1:1 绝对对齐。"
            elif not write_ok:
                msg += f"⚠️ 写入 Script.js 失败: {err_msg}"
            else:
                msg += "⚠️ 已写入 Script.js，热键模拟未生效，请手动按下 Ctrl+Shift+F12。"
            messagebox.showinfo("同步成功", msg)

        return len(auto_eps), len(self.favorites)

    def import_cloud_text_to_favorites(self):
        raw_text = self.cloud_text_box.get("1.0", tk.END).strip()
        if not raw_text or "❌ 读取失败" in raw_text or "错误：" in raw_text:
            messagebox.showwarning("提示", "当前文本框没有可导入的有效节点内容！")
            return
        self.sync_favorites_from_auto_text(show_notify=True, source_text=raw_text)


    def _on_notebook_tab_changed(self, event=None):
        try:
            tab_idx = self.notebook.index(self.notebook.select())
            if tab_idx == 2:
                self.refresh_verified_table()
            elif tab_idx == 3:
                self.refresh_stars_table()
            elif tab_idx == 4 and getattr(self, "_delay_black_dirty", True):
                self._render_delay_black_table()
            elif tab_idx == 5 and getattr(self, "_speed_black_dirty", True):
                self._render_speed_black_table()
        except Exception:
            pass

    def _render_delay_black_table(self):
        if "delay_black" not in self.trees:
            return
        tree = self.trees["delay_black"]
        tree.delete(*tree.get_children())
        kw = self.search_var.get().strip().lower()

        seen_d_eps = set()

        for name in self.all_nodes:
            if kw and kw not in name.lower():
                continue
            ep_val = self.get_node_endpoint(name)
            is_asian = self.is_asian_node(name)
            if is_asian:
                is_d_black = (name in self.local_blacklist) or (ep_val and ep_val in self.local_blacklist)
            else:
                is_d_black = True
            if is_d_black:
                ep_key = ep_val if ep_val else name
                if ep_key in seen_d_eps:
                    continue
                seen_d_eps.add(ep_key)

                d_val = self.node_delays.get(name, None)
                if d_val is None:
                    d_str = "已跳过"
                elif d_val >= 99999:
                    d_str = "超时 / 失败"
                else:
                    d_str = f"{d_val} ms"
                colo_str = self.node_colo.get(ep_val, self.node_colo.get(name, "-"))
                colo_hist = self.node_colo_history.get(ep_val, self.node_colo_history.get(name, []))
                colo_hist_str = self.analyze_colo_stats(colo_hist, time.time(), node_name=name)[3]
                cur_avg_str, hist_avg_str = self.compute_delay_stats(name, ep_val)
                delay_hist_str = self.format_history_chain(self.node_history.get(name, []))
                speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(name, []))
                reason_str = self.get_blacklist_reason(name, ep_val)
                row_data = ("🚫 延迟黑名单", colo_str, colo_hist_str, reason_str, d_str, cur_avg_str, delay_hist_str, hist_avg_str, "-", speed_hist_str, name)
                tree.insert("", tk.END, values=row_data, tags=["black_delay"])

        for b_name in self.local_blacklist:
            if b_name not in self.all_nodes:
                if kw and kw not in b_name.lower():
                    continue
                b_ep = self.get_node_endpoint(b_name)
                ep_key = b_ep if b_ep else b_name
                if ep_key in seen_d_eps:
                    continue
                seen_d_eps.add(ep_key)

                s_hist = self.format_speed_history_chain(self.node_speed_history.get(b_name, []))
                cur_avg, hist_avg = self.compute_delay_stats(b_name)
                b_reason = self.get_blacklist_reason(b_name, b_ep)
                row_data = ("🚫 历史黑名单", "-", "-", b_reason, "已跳过", cur_avg, "-", hist_avg, "-", s_hist, b_name)
                tree.insert("", tk.END, values=row_data, tags=["black_delay"])
        self._delay_black_dirty = False

    def _render_speed_black_table(self):
        if "speed_black" not in self.trees:
            return
        tree = self.trees["speed_black"]
        tree.delete(*tree.get_children())
        kw = self.search_var.get().strip().lower()

        seen_s_eps = set()

        for name in self.all_nodes:
            if kw and kw not in name.lower():
                continue
            ep_val = self.get_node_endpoint(name)
            is_s_black = (name in self.speed_blacklist) or (ep_val and ep_val in self.speed_blacklist)
            if is_s_black:
                ep_key = ep_val if ep_val else name
                if ep_key in seen_s_eps:
                    continue
                seen_s_eps.add(ep_key)

                s_val = self.node_speeds.get(name, None)
                s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else ("测速失败" if s_val is not None else "-")
                colo_str = self.node_colo.get(ep_val, self.node_colo.get(name, "-"))
                colo_hist = self.node_colo_history.get(ep_val, self.node_colo_history.get(name, []))
                colo_hist_str = self.analyze_colo_stats(colo_hist, time.time(), node_name=name)[3]
                cur_avg_str, hist_avg_str = self.compute_delay_stats(name, ep_val)
                delay_hist_str = self.format_history_chain(self.node_history.get(name, []))
                speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(name, []))
                reason_str = self.get_blacklist_reason(name, ep_val)
                row_data = ("🐌 低速黑名单", colo_str, colo_hist_str, reason_str, "-", cur_avg_str, delay_hist_str, hist_avg_str, s_str, speed_hist_str, name)
                tree.insert("", tk.END, values=row_data, tags=["black_speed"])

        for s_name in self.speed_blacklist:
            if s_name not in self.all_nodes:
                if kw and kw not in s_name.lower():
                    continue
                s_ep = self.get_node_endpoint(s_name)
                ep_key = s_ep if s_ep else s_name
                if ep_key in seen_s_eps:
                    continue
                seen_s_eps.add(ep_key)

                s_hist = self.format_speed_history_chain(self.node_speed_history.get(s_name, []))
                cur_avg, hist_avg = self.compute_delay_stats(s_name)
                s_reason = self.get_blacklist_reason(s_name, s_ep)
                row_data = ("🐌 历史低速", "-", "-", s_reason, "已跳过", cur_avg, "-", hist_avg, "-", s_hist, s_name)
                tree.insert("", tk.END, values=row_data, tags=["black_speed"])
        self._speed_black_dirty = False

    def refresh_tables(self):
        self.align_favorites_with_current_subscription()
        self.purge_invalid_and_blacklisted_from_all_pools()
        kw = self.search_var.get().strip().lower()
        now = time.time()

        curr_tab = -1
        try:
            curr_tab = self.notebook.index(self.notebook.select())
        except Exception:
            curr_tab = 0

        for tab_k in ["all", "fav"]:
            if tab_k in self.trees:
                self.trees[tab_k].delete(*self.trees[tab_k].get_children())

        if curr_tab == 4:
            if "delay_black" in self.trees:
                self.trees["delay_black"].delete(*self.trees["delay_black"].get_children())
            self._delay_black_dirty = False
        else:
            self._delay_black_dirty = True

        if curr_tab == 5:
            if "speed_black" in self.trees:
                self.trees["speed_black"].delete(*self.trees["speed_black"].get_children())
            self._speed_black_dirty = False
        else:
            self._speed_black_dirty = True

        fav_eps, bl_eps, sbl_eps, star_eps = self.get_pool_endpoint_sets()

        # 1. 待测池节点按端点聚合（严格1对1去重，纯净展示）
        untested_groups = {}
        seen_d_eps = set()
        seen_s_eps = set()

        for name in self.all_nodes:
            ep_val = self.get_node_endpoint(name)
            is_asian = self.is_asian_node(name)
            if not is_asian:
                if name not in self.local_blacklist:
                    self.local_blacklist.add(name)
                is_d_black = True
                is_s_black = False
            else:
                is_d_black = (name in self.local_blacklist) or (ep_val and ep_val in self.local_blacklist)
                is_s_black = not is_d_black and ((name in self.speed_blacklist) or (ep_val and ep_val in self.speed_blacklist))

            # 严格对齐：精选池仅准入 self.favorites 中的代表节点，同端点其他马甲作为别名隔离，绝不重复塞入精选表
            is_fav = not is_d_black and not is_s_black and (name in self.favorites)
            is_fav_alias = not is_d_black and not is_s_black and not is_fav and (ep_val and ep_val in fav_eps)
            is_ver_star = not is_d_black and not is_s_black and not is_fav and not is_fav_alias and ((name in self.verified_nodes) or (ep_val and ep_val in star_eps))

            # 归集待测池
            if not is_d_black and not is_s_black and not is_fav and not is_fav_alias and not is_ver_star:
                key = ep_val if ep_val else name
                untested_groups.setdefault(key, []).append(name)

            # 渲染精选池
            if is_fav:
                if kw and kw not in name.lower():
                    continue
                d_val = self.node_delays.get(name, None)
                tags = ["fav"]
                if d_val is None:
                    d_str = "未测速"
                elif d_val >= 99999:
                    d_str = "超时 / 失败"
                    tags.append("timeout")
                else:
                    d_str = f"{d_val} ms"
                    tags.append("fast" if d_val < 150 else "medium")

                s_val = self.node_speeds.get(name, None)
                s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else ("测速失败" if s_val is not None else "-")
                colo_str = self.node_colo.get(ep_val, self.node_colo.get(name, "-"))
                colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep_val, self.node_colo_history.get(name, [])), now, node_name=name)[3]
                cur_avg_str, hist_avg_str = self.compute_delay_stats(name, ep_val)
                delay_hist_str = self.format_history_chain(self.node_history.get(name, []))
                speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(name, []))
                reason_str = self.get_fav_reason(name, ep_val)
                row_data = ("⭐ 优质候选", colo_str, colo_hist_str, reason_str, d_str, cur_avg_str, delay_hist_str, hist_avg_str, s_str, speed_hist_str, name)
                self.trees["fav"].insert("", tk.END, values=row_data, tags=tags)

            # 延迟黑名单 (按端点去重)
            if is_d_black and curr_tab == 4:
                ep_key = ep_val if ep_val else name
                if ep_key not in seen_d_eps:
                    seen_d_eps.add(ep_key)
                    if not kw or (kw in name.lower()):
                        d_val = self.node_delays.get(name, None)
                        tags = ["black_delay"]
                        if d_val is None:
                            d_str = "已跳过"
                        elif d_val >= 99999:
                            d_str = "超时 / 失败"
                            tags.append("timeout")
                        else:
                            d_str = f"{d_val} ms"
                        colo_str = self.node_colo.get(ep_val, self.node_colo.get(name, "-"))
                        colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep_val, self.node_colo_history.get(name, [])), now, node_name=name)[3]
                        cur_avg_str, hist_avg_str = self.compute_delay_stats(name, ep_val)
                        delay_hist_str = self.format_history_chain(self.node_history.get(name, []))
                        speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(name, []))
                        reason_str = self.get_blacklist_reason(name, ep_val)
                        row_data = ("🚫 延迟黑名单", colo_str, colo_hist_str, reason_str, d_str, cur_avg_str, delay_hist_str, hist_avg_str, "-", speed_hist_str, name)
                        self.trees["delay_black"].insert("", tk.END, values=row_data, tags=tags)

            # 低速黑名单 (按端点去重)
            if is_s_black and curr_tab == 5:
                ep_key = ep_val if ep_val else name
                if ep_key not in seen_s_eps:
                    seen_s_eps.add(ep_key)
                    if not kw or (kw in name.lower()):
                        s_val = self.node_speeds.get(name, None)
                        tags = ["black_speed"]
                        s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else ("测速失败" if s_val is not None else "-")
                        colo_str = self.node_colo.get(ep_val, self.node_colo.get(name, "-"))
                        colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep_val, self.node_colo_history.get(name, [])), now, node_name=name)[3]
                        cur_avg_str, hist_avg_str = self.compute_delay_stats(name, ep_val)
                        delay_hist_str = self.format_history_chain(self.node_history.get(name, []))
                        speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(name, []))
                        reason_str = self.get_blacklist_reason(name, ep_val)
                        row_data = ("🐌 低速黑名单", colo_str, colo_hist_str, reason_str, "-", cur_avg_str, delay_hist_str, hist_avg_str, s_str, speed_hist_str, name)
                        self.trees["speed_black"].insert("", tk.END, values=row_data, tags=tags)

        # 渲染待测池 (对每个唯一端点仅渲染1个主代表节点，彻底杜绝重复)
        display_active_count = 0
        for ep_key, group_nodes in untested_groups.items():
            canonical_name = self.choose_canonical_node_name(group_nodes)
            if kw:
                matched_kw = (kw in canonical_name.lower()) or any(kw in n.lower() for n in group_nodes)
                if not matched_kw:
                    continue

            d_val = self.node_delays.get(canonical_name, self.node_delays.get(ep_key, None))
            tags = []
            if d_val is None:
                d_str = "未测速"
            elif d_val >= 99999:
                d_str = "超时 / 失败"
                tags.append("timeout")
            else:
                d_str = f"{d_val} ms"
                tags.append("fast" if d_val < 150 else "medium")

            s_val = self.node_speeds.get(canonical_name, self.node_speeds.get(ep_key, None))
            if s_val is None:
                s_str = "-"
            elif s_val < 0:
                s_str = "测速失败"
            else:
                s_str = f"{s_val:.2f} MB/s"

            colo_str = self.node_colo.get(ep_key, self.node_colo.get(canonical_name, "-"))
            colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(ep_key, self.node_colo_history.get(canonical_name, [])), now, node_name=canonical_name)[3]

            cur_avg_str, hist_avg_str = self.compute_delay_stats(canonical_name, ep_key)
            delay_hist_str = self.format_history_chain(self.node_history.get(canonical_name, []))
            speed_hist_str = self.format_speed_history_chain(self.node_speed_history.get(canonical_name, []))
            reason_str = "-"

            row_data = ("⚪ 活跃待测", colo_str, colo_hist_str, reason_str, d_str, cur_avg_str, delay_hist_str, hist_avg_str, s_str, speed_hist_str, canonical_name)
            self.trees["all"].insert("", tk.END, values=row_data, tags=tags)
            display_active_count += 1

        for fav_name in self.favorites:
            if fav_name not in self.all_nodes:
                curr_active = self.resolve_node_to_current(fav_name)
                if curr_active and curr_active in self.all_nodes:
                    continue
                if kw and kw not in fav_name.lower():
                    continue
                s_hist = self.format_speed_history_chain(self.node_speed_history.get(fav_name, []))
                colo_str = self.node_colo.get(fav_name, "-")
                colo_hist_str = self.analyze_colo_stats(self.node_colo_history.get(fav_name, []), now, node_name=fav_name)[3]
                cur_avg, hist_avg = self.compute_delay_stats(fav_name)
                off_reason = self.get_fav_reason(fav_name)
                off_reason_str = f"{off_reason} (已下线)" if off_reason and off_reason != "优质精选" else "订阅已下线"
                row_data = ("⚠️ 订阅已下线", colo_str, colo_hist_str, off_reason_str, "-", cur_avg, "-", hist_avg, "-", s_hist, fav_name)
                self.trees["fav"].insert("", tk.END, values=row_data, tags=["offline"])

        if curr_tab == 4 and "delay_black" in self.trees:
            for b_name in self.local_blacklist:
                if b_name not in self.all_nodes:
                    if kw and kw not in b_name.lower():
                        continue
                    b_ep = self.get_node_endpoint(b_name)
                    ep_key = b_ep if b_ep else b_name
                    if ep_key in seen_d_eps:
                        continue
                    seen_d_eps.add(ep_key)

                    s_hist = self.format_speed_history_chain(self.node_speed_history.get(b_name, []))
                    cur_avg, hist_avg = self.compute_delay_stats(b_name)
                    b_reason = self.get_blacklist_reason(b_name, b_ep)
                    row_data = ("🚫 历史黑名单", "-", "-", b_reason, "已跳过", cur_avg, "-", hist_avg, "-", s_hist, b_name)
                    self.trees["delay_black"].insert("", tk.END, values=row_data, tags=["black_delay"])

        if curr_tab == 5 and "speed_black" in self.trees:
            for s_name in self.speed_blacklist:
                if s_name not in self.all_nodes:
                    if kw and kw not in s_name.lower():
                        continue
                    s_ep = self.get_node_endpoint(s_name)
                    ep_key = s_ep if s_ep else s_name
                    if ep_key in seen_s_eps:
                        continue
                    seen_s_eps.add(ep_key)

                    s_hist = self.format_speed_history_chain(self.node_speed_history.get(s_name, []))
                    cur_avg, hist_avg = self.compute_delay_stats(s_name)
                    s_reason = self.get_blacklist_reason(s_name, s_ep)
                    row_data = ("🐌 历史低速", "-", "-", s_reason, "已跳过", cur_avg, "-", hist_avg, "-", s_hist, s_name)
                    self.trees["speed_black"].insert("", tk.END, values=row_data, tags=["black_speed"])

        fav_tree_count = len(self.trees["fav"].get_children())
        self.notebook.tab(0, text=f"📋 活跃待测 ({display_active_count})")
        self.notebook.tab(1, text=f"⭐ 优质精选 ({fav_tree_count})")
        self.notebook.tab(2, text=f"⏳ 沉淀孵化 ({len(self.verified_nodes)})")
        self.notebook.tab(3, text=f"🏆 典藏管理 ({len(self.stars_nodes)})")
        self.notebook.tab(4, text=f"🚫 延迟黑名单 ({len(bl_eps) if bl_eps else len(self.local_blacklist)})")
        self.notebook.tab(5, text=f"🐌 低速黑名单 ({len(sbl_eps) if sbl_eps else len(self.speed_blacklist)})")

        if not self.is_pipeline_running:
            self.status_label.config(
                text=f"待测: {display_active_count}  |  优质: {fav_tree_count}  |  孵化: {len(self.verified_nodes)}  |  典藏: {len(self.stars_nodes)}"
            )

    def sort_tree(self, tree, col, reverse):
        items = [(tree.set(k, col), k) for k in tree.get_children("")]
        if col == "delay":

            def _sort_key(x):
                txt = x[0]
                m = re.search(r"(\d+)", txt)
                if m:
                    return int(m.group(1))
                elif "超时" in txt:
                    return 999999
                elif "已跳过" in txt or "-" in txt:
                    return 999997
                return 999998

            items.sort(key=_sort_key, reverse=reverse)
        elif col == "avg_delay":

            def _sort_avg(x):
                txt = x[0]
                m = re.search(r"(\d+)\s*ms", txt)
                if m:
                    return int(m.group(1))
                elif "超时" in txt:
                    return 999999
                return 999998

            items.sort(key=_sort_avg, reverse=reverse)
        elif col == "hist_avg":

            def _sort_hist(x):
                txt = x[0]
                m = re.search(r"(\d+)\s*ms", txt)
                if m:
                    return int(m.group(1))
                return 999998

            items.sort(key=_sort_hist, reverse=reverse)
        elif col == "speed":

            def _sort_speed(x):
                txt = x[0]
                if "MB/s" in txt:
                    try:
                        return float(txt.replace(" MB/s", ""))
                    except Exception:
                        return -1.0
                elif "失败" in txt:
                    return -2.0
                return -3.0

            items.sort(key=_sort_speed, reverse=reverse)
        else:
            items.sort(reverse=reverse)

        for idx, (_, k) in enumerate(items):
            tree.move(k, "", idx)
        tree.heading(col, command=lambda: self.sort_tree(tree, col, not reverse))

    def set_favorite(self):
        tree = self.get_current_tree()
        non_asia_blocked = 0
        added_cnt = 0
        for sel in tree.selection():
            name = tree.item(sel, "values")[-1]
            if not self.is_asian_node(name):
                self.local_blacklist.add(name)
                self.favorites.discard(name)
                non_asia_blocked += 1
                continue
            self.local_blacklist.discard(name)
            self.speed_blacklist.discard(name)
            self.favorites.add(name)
            self.record_fav_reason(name, "手动设为优质")
            added_cnt += 1
        self.deduplicate_favorites_by_endpoint()
        self.save_persisted_config()
        self.refresh_tables()
        if non_asia_blocked > 0:
            self.log(f"⚠️ 已拦截并直接拉黑 {non_asia_blocked} 个非亚洲节点（仅限亚洲节点加入精选）")
        if added_cnt > 0:
            self.log(f"已手动设为优质：{added_cnt} 个亚洲节点")

    def manual_add_delay_blacklist(self):
        tree = self.get_current_tree()
        selections = tree.selection()
        if not selections:
            messagebox.showinfo("提示", "请先在列表中选中需要拉黑的节点！")
            return

        for sel in selections:
            name = tree.item(sel, "values")[-1]
            self.favorites.discard(name)
            self.speed_blacklist.discard(name)
            self.local_blacklist.add(name)
            self.record_blacklist_reason(name, "手动加入延迟黑名单")
            ep = self.get_node_endpoint(name)
            if ep:
                self.local_blacklist.add(ep)
                self.record_blacklist_reason(ep, "手动加入延迟黑名单")
                self.verified_nodes.pop(ep, None)
        self.purge_invalid_and_blacklisted_from_all_pools()
        self.save_persisted_config()
        self.refresh_tables()
        self.refresh_verified_table()
        self.status_label.config(text=f"已手动将选中的 {len(selections)} 个节点加入【延迟黑名单】")
        self.log(f"手动加入延迟黑名单：{len(selections)} 个节点")

    def manual_add_speed_blacklist(self):
        tree = self.get_current_tree()
        selections = tree.selection()
        if not selections:
            messagebox.showinfo("提示", "请先在列表中选中需要拉黑的节点！")
            return

        for sel in selections:
            name = tree.item(sel, "values")[-1]
            self.favorites.discard(name)
            self.local_blacklist.discard(name)
            self.speed_blacklist.add(name)
            self.record_blacklist_reason(name, "手动加入低速黑名单")
            ep = self.get_node_endpoint(name)
            if ep:
                self.speed_blacklist.add(ep)
                self.record_blacklist_reason(ep, "手动加入低速黑名单")
                self.verified_nodes.pop(ep, None)
        self.purge_invalid_and_blacklisted_from_all_pools()
        self.save_persisted_config()
        self.refresh_tables()
        self.refresh_verified_table()
        self.status_label.config(text=f"已手动将选中的 {len(selections)} 个节点加入【低速黑名单】")
        self.log(f"手动加入低速黑名单：{len(selections)} 个节点")

    def remove_from_blacklist(self, tree=None):
        if tree is None:
            tree = self.get_current_tree()
        selections = tree.selection()
        if not selections:
            messagebox.showinfo("提示", "请先在列表中选中要移出黑名单的节点！")
            return

        removed_names = []
        for sel in selections:
            vals = tree.item(sel, "values")
            name = vals[-1] if vals else ""
            if not name:
                continue
            removed_names.append(name)
            self.local_blacklist.discard(name)
            self.speed_blacklist.discard(name)
            if hasattr(self, "blacklist_reasons"):
                self.blacklist_reasons.pop(name, None)

            # 同时彻底拔除物理端点与纯 IP 记录，包括包含该 IP 的历史条目
            ep = self.get_node_endpoint(name)
            if ep:
                self.local_blacklist.discard(ep)
                self.speed_blacklist.discard(ep)
                if hasattr(self, "blacklist_reasons"):
                    self.blacklist_reasons.pop(ep, None)
                if ":" in ep:
                    ip = ep.split(":")[0]
                    self.local_blacklist.discard(ip)
                    self.speed_blacklist.discard(ip)
                    if hasattr(self, "blacklist_reasons"):
                        self.blacklist_reasons.pop(ip, None)
                    for b in list(self.local_blacklist):
                        if ip in b:
                            self.local_blacklist.discard(b)
                            if hasattr(self, "blacklist_reasons"):
                                self.blacklist_reasons.pop(b, None)
                    for s in list(self.speed_blacklist):
                        if ip in s:
                            self.speed_blacklist.discard(s)
                            if hasattr(self, "blacklist_reasons"):
                                self.blacklist_reasons.pop(s, None)

            if name in self.node_speed_history:
                self.node_speed_history[name].clear()
            if ep and ep in self.node_speed_history:
                self.node_speed_history[ep].clear()

        self._all_nodes_set = None
        self.save_persisted_config()
        self.refresh_tables()
        self.status_label.config(text=f"已成功将选中的 {len(removed_names)} 个节点移出黑名单并恢复待测")
        self.log(f"已移出黑名单恢复活跃：{len(removed_names)} 个节点 ({', '.join(removed_names[:3])}{'...' if len(removed_names)>3 else ''})")

    def remove_from_blacklist_and_set_favorite(self, tree=None):
        if tree is None:
            tree = self.get_current_tree()
        selections = tree.selection()
        if not selections:
            messagebox.showinfo("提示", "请先在列表中选中节点！")
            return

        added_cnt = 0
        non_asia_blocked = 0
        for sel in selections:
            vals = tree.item(sel, "values")
            name = vals[-1] if vals else ""
            if not name:
                continue
            if not self.is_asian_node(name):
                self.local_blacklist.add(name)
                non_asia_blocked += 1
                continue

            self.local_blacklist.discard(name)
            self.speed_blacklist.discard(name)
            if hasattr(self, "blacklist_reasons"):
                self.blacklist_reasons.pop(name, None)
            ep = self.get_node_endpoint(name)
            if ep:
                self.local_blacklist.discard(ep)
                self.speed_blacklist.discard(ep)
                if hasattr(self, "blacklist_reasons"):
                    self.blacklist_reasons.pop(ep, None)
                if ":" in ep:
                    ip = ep.split(":")[0]
                    self.local_blacklist.discard(ip)
                    self.speed_blacklist.discard(ip)
                    if hasattr(self, "blacklist_reasons"):
                        self.blacklist_reasons.pop(ip, None)
                    for b in list(self.local_blacklist):
                        if ip in b:
                            self.local_blacklist.discard(b)
                            if hasattr(self, "blacklist_reasons"):
                                self.blacklist_reasons.pop(b, None)
                    for s in list(self.speed_blacklist):
                        if ip in s:
                            self.speed_blacklist.discard(s)
                            if hasattr(self, "blacklist_reasons"):
                                self.blacklist_reasons.pop(s, None)

            self.favorites.add(name)
            self.record_fav_reason(name, "移出黑名单设为优质")
            added_cnt += 1

        self._all_nodes_set = None
        self.deduplicate_favorites_by_endpoint()
        self.save_persisted_config()
        self.refresh_tables()
        if non_asia_blocked > 0:
            self.log(f"⚠️ 已拦截并保持拉黑 {non_asia_blocked} 个非亚洲节点")
        if added_cnt > 0:
            self.status_label.config(text=f"已将选中的 {added_cnt} 个节点移出黑名单并加入精选池")
            self.log(f"已移出黑名单并加入精选：{added_cnt} 个节点")

    def clear_all_blacklists(self):
        tot_d = len(self.local_blacklist)
        tot_s = len(self.speed_blacklist)
        if tot_d == 0 and tot_s == 0:
            messagebox.showinfo("提示", "当前所有黑名单均为空，无需清空！")
            return

        if not messagebox.askyesno(
            "一键清空黑名单确认",
            f"确定要一键清空全部黑名单吗？\n\n"
            f"• 延迟黑名单：{tot_d} 条\n"
            f"• 低速黑名单：{tot_s} 条\n\n"
            f"清空后所有被拉黑的节点将重置状态，并全部恢复至【📋 活跃待测】池，\n"
            f"可重新进行全量测速、计分与典藏晋升！"
        ):
            return

        self.local_blacklist.clear()
        self.speed_blacklist.clear()
        if hasattr(self, "blacklist_timestamps") and isinstance(self.blacklist_timestamps, dict):
            self.blacklist_timestamps.clear()
        if hasattr(self, "blacklist_reasons") and isinstance(self.blacklist_reasons, dict):
            self.blacklist_reasons.clear()

        # 重置测速记录，让节点纯净重新参与计分
        for n in list(self.node_speed_history.keys()):
            self.node_speed_history[n].clear()

        self._all_nodes_set = None
        self.save_persisted_config()
        self.refresh_tables()
        self.status_label.config(text=f"🎉 已成功一键清空所有黑名单，恢复全部节点至待测区！")
        self.log(f"🎉【一键清空黑名单】已清空 {tot_d} 条延迟黑名单与 {tot_s} 条低速黑名单，全量节点已恢复活跃待测！")
        messagebox.showinfo("清空成功", f"🎉 已成功清空全部黑名单！\n\n当前共有 {len(self.all_nodes)} 个节点已恢复待测，\n可立即点击【全量优选】或右键重新给节点测速、计分与晋升！")

    def clear_delay_blacklist(self):
        if not self.local_blacklist:
            messagebox.showinfo("提示", "延迟黑名单为空！")
            return
        if messagebox.askyesno("清空确认", f"确定清空全部 {len(self.local_blacklist)} 个延迟黑名单吗？"):
            if hasattr(self, "blacklist_reasons") and isinstance(self.blacklist_reasons, dict):
                for b in list(self.local_blacklist):
                    self.blacklist_reasons.pop(b, None)
            self.local_blacklist.clear()
            self._all_nodes_set = None
            self.save_persisted_config()
            self.refresh_tables()
            self.log("已清空延迟黑名单。")

    def clear_speed_blacklist(self):
        if not self.speed_blacklist:
            messagebox.showinfo("提示", "低速黑名单为空！")
            return
        if messagebox.askyesno("清空确认", f"确定清空全部 {len(self.speed_blacklist)} 个低速黑名单并重置测速记录吗？"):
            if hasattr(self, "blacklist_reasons") and isinstance(self.blacklist_reasons, dict):
                for s in list(self.speed_blacklist):
                    self.blacklist_reasons.pop(s, None)
            for n in self.speed_blacklist:
                if n in self.node_speed_history:
                    self.node_speed_history[n].clear()
            self.speed_blacklist.clear()
            self._all_nodes_set = None
            self.save_persisted_config()
            self.refresh_tables()
            self.log("已清空低速黑名单。")

    def clear_current_tab_blacklist(self):
        idx = self.notebook.index(self.notebook.select())
        if idx == 4:
            self.clear_delay_blacklist()
        elif idx == 5:
            self.clear_speed_blacklist()
        else:
            self.clear_all_blacklists()

    def trigger_rescore_and_promote(self):
        if self.is_pipeline_running:
            messagebox.showinfo("提示", "当前已有优选流水线正在运行，请等待完成后再试！")
            return

        if not messagebox.askyesno(
            "重新计分晋升确认",
            "是否立即对所有待测节点启动【全量重新计分与晋升流水线】？\n\n"
            "流水线将依次进行：\n"
            "1. 延迟多轮精测与抖动评分考核\n"
            "2. 高速带宽并发下行压测与计分\n"
            "3. 筛选达标最优节点晋升入【⭐ 优质精选池】\n"
            "4. 同步计分纳入【⏳ 沉淀孵化池】并评定【🏆 典藏常青池】晋升\n"
            "5. 一键热生效写入 Clash 内核\n\n"
            "点击【是】立即启动！"
        ):
            return

        self.start_full_auto_pipeline()

    def rescore_and_promote_selected(self, tree=None):
        if tree is None:
            tree = self.get_current_tree()
        selections = tree.selection()
        if not selections:
            messagebox.showinfo("提示", "请先在列表中选中需要测速计分并晋升的节点！")
            return

        sel_nodes = []
        for sel in selections:
            vals = tree.item(sel, "values")
            name = vals[-1] if vals else ""
            if name:
                sel_nodes.append(name)

        if not sel_nodes:
            return

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text=f"正在对选中的 {len(sel_nodes)} 个节点进行测速计分与晋升评定..."))
            promoted_cnt = 0
            for idx, name in enumerate(sel_nodes, 1):
                # 1. 移出黑名单
                self.local_blacklist.discard(name)
                self.speed_blacklist.discard(name)
                if hasattr(self, "blacklist_reasons"):
                    self.blacklist_reasons.pop(name, None)
                ep = self.get_node_endpoint(name)
                if ep:
                    self.local_blacklist.discard(ep)
                    self.speed_blacklist.discard(ep)
                    if hasattr(self, "blacklist_reasons"):
                        self.blacklist_reasons.pop(ep, None)
                    if ":" in ep:
                        ip = ep.split(":")[0]
                        self.local_blacklist.discard(ip)
                        self.speed_blacklist.discard(ip)
                        if hasattr(self, "blacklist_reasons"):
                            self.blacklist_reasons.pop(ip, None)

                # 2. 延迟多轮采样测速计分
                test_url = self.test_url_var.get().strip() or "http://www.gstatic.com/generate_204"
                enc_n = urllib.parse.quote(name, safe="")
                enc_u = urllib.parse.quote(test_url, safe="")
                delays = []
                for _ in range(3):
                    res = self._call_api(f"/proxies/{enc_n}/delay?timeout=2500&url={enc_u}", timeout=3.0)
                    if res and "delay" in res:
                        delays.append(res["delay"])
                    time.sleep(0.1)

                if not delays:
                    self.log(f"⚠️ 节点 {name} 延迟测试失败，无法计分")
                    continue

                avg_d = round(sum(delays) / len(delays))
                self.node_delays[name] = avg_d
                self.record_delay_sample(name, avg_d)
                if ep:
                    self.record_delay_sample(ep, avg_d)

                # 3. Colo 实时机房探测
                if ep and ":" in ep:
                    ip, port = ep.split(":", 1)
                    c_code, c_disp = get_cf_colo_raw(ip, port, timeout=1.5)
                    self.record_colo_sample(name, ep, c_code, c_disp)

                # 4. 下行带宽测速
                speed_url = self.speed_url_var.get().strip()
                spd = -1.0
                if speed_url and speed_url.startswith("http"):
                    try:
                        proxies_data = self._call_api("/proxies") or {}
                        proxies_map = proxies_data.get("proxies", {})
                        tg = "🚀 节点选择" if "🚀 节点选择" in proxies_map else "GLOBAL"
                        enc_tg = urllib.parse.quote(tg, safe="")
                        orig_choice = proxies_map.get(tg, {}).get("now", "")
                        self._call_api(f"/proxies/{enc_tg}", method="PUT", data=json.dumps({"name": name}).encode("utf-8"))
                        time.sleep(0.1)

                        mixed_port = self.get_clash_mixed_port()
                        proxy_handler = urllib.request.ProxyHandler({
                            "http": f"http://127.0.0.1:{mixed_port}",
                            "https": f"http://127.0.0.1:{mixed_port}",
                        })
                        opener = urllib.request.build_opener(proxy_handler)
                        req = urllib.request.Request(speed_url, headers={"User-Agent": "Mozilla/5.0"})
                        t_start = time.time()
                        total_b = 0
                        with opener.open(req, timeout=3.0) as resp:
                            while time.time() - t_start < 2.0:
                                chunk = resp.read(65536)
                                if not chunk:
                                    break
                                total_b += len(chunk)
                        dur = max(0.1, time.time() - t_start)
                        spd = round((total_b / dur) / (1024 * 1024), 2)

                        if orig_choice:
                            self._call_api(f"/proxies/{enc_tg}", method="PUT", data=json.dumps({"name": orig_choice}).encode("utf-8"))
                    except Exception:
                        spd = 0.0

                if spd >= 0:
                    self.node_speeds[name] = spd
                    self.node_speed_history.setdefault(name, []).append(spd)
                    self.node_speed_history[name] = self.node_speed_history[name][-4:]

                # 5. 晋升考核判定
                try:
                    max_d = int(self.max_delay_var.get().strip())
                except Exception:
                    max_d = 400
                try:
                    min_s = float(self.min_speed_var.get().strip())
                except Exception:
                    min_s = 2.0

                is_pass = (avg_d <= max_d) and (spd >= min_s if spd >= 0 else True) and self.is_asian_node(name)
                if is_pass:
                    self.favorites.add(name)
                    self.record_fav_reason(name, f"计分晋升 ({avg_d}ms / {spd:.2f}MB/s)")
                    promoted_cnt += 1
                    self.log(f"🎉【计分晋升】节点 {name} 计分通过（延迟 {avg_d}ms，下行 {spd} MB/s），已晋升至优质精选！")

            self._all_nodes_set = None
            self.deduplicate_favorites_by_endpoint()
            self.process_verified_lifecycle(list(self.favorites), [])
            self.save_persisted_config()
            self.root.after(0, self.refresh_tables)
            self.root.after(0, self.refresh_verified_table)
            self.root.after(0, self.refresh_stars_table)
            self.root.after(0, lambda: self.status_label.config(text=f"测速计分完成：成功晋升 {promoted_cnt}/{len(sel_nodes)} 个节点！"))

        threading.Thread(target=_worker, daemon=True).start()



    def setup_cloud_text_ui(self):
        toolbar = tk.Frame(self.tab_cloud_text, bg=THEME["bg_card"], padx=10, pady=8)
        toolbar.pack(fill=tk.X, padx=4, pady=(4, 4))

        tk.Label(toolbar, text="选择查看的云端文本:", fg="#38bdf8", bg=THEME["bg_card"], font=("Microsoft YaHei UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))

        self.cloud_file_var = tk.StringVar(value="/auto.txt (自动优选池)")
        self.cloud_combo = ttk.Combobox(
            toolbar,
            textvariable=self.cloud_file_var,
            values=["/auto.txt (自动优选池)", "/verified.txt (沉淀孵化池)", "/ (根目录典藏池)"],
            state="readonly",
            width=28
        )
        self.cloud_combo.pack(side=tk.LEFT, padx=6)
        self.cloud_combo.bind("<<ComboboxSelected>>", lambda e: self.load_cloud_text())

        create_modern_btn(
            toolbar,
            text="🔄 实时读取刷新",
            command=self.load_cloud_text,
            bg=THEME["accent_cyan"],
            hover_bg=THEME["accent_cyan_hover"] if "accent_cyan_hover" in THEME else THEME["accent_cyan"],
            font_size=9,
        ).pack(side=tk.LEFT, padx=6)

        create_modern_btn(
            toolbar,
            text="📥 导入至【优质精选】",
            command=self.import_cloud_text_to_favorites,
            bg=THEME["accent_green"],
            hover_bg=THEME["accent_green_hover"] if "accent_green_hover" in THEME else THEME["accent_green"],
            font_size=9,
        ).pack(side=tk.RIGHT, padx=4)

        create_modern_btn(
            toolbar,
            text="📋 复制全文",
            command=self.copy_cloud_text,
            bg=THEME["bg_hover"],
            hover_bg=THEME["border"],
            font_size=9,
        ).pack(side=tk.RIGHT, padx=4)

        text_frame = tk.Frame(self.tab_cloud_text, bg=THEME["tree_bg"], padx=4, pady=4)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        self.cloud_text_box = tk.Text(
            text_frame,
            bg=THEME["bg_input"],
            fg=THEME["text_main"],
            insertbackground="#38bdf8",
            relief="flat",
            bd=0,
            font=("Consolas", 10),
            wrap="word"
        )
        sb_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.cloud_text_box.yview, style="Vertical.TScrollbar")
        self.cloud_text_box.configure(yscrollcommand=sb_y.set)
        self.cloud_text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)

        # 默认加载一次
        self.root.after(600, self.load_cloud_text)

    def load_cloud_text(self):
        base_url = self.cf_worker_url_var.get().strip().rstrip("/")
        if not base_url.startswith("http"):
            self.cloud_text_box.config(state="normal")
            self.cloud_text_box.delete("1.0", tk.END)
            self.cloud_text_box.insert(tk.END, "错误：请先在上方配置有效的 Cloudflare Worker 根地址！")
            self.cloud_text_box.config(state="disabled")
            return

        selection = self.cloud_file_var.get()
        if "auto.txt" in selection:
            subpath = "/auto.txt"
        elif "verified.txt" in selection:
            subpath = "/verified.txt"
        else:
            subpath = "/"

        target_url = f"{base_url}{subpath}" if subpath != "/" else f"{base_url}/"

        def _worker():
            self.root.after(0, lambda: self.status_label.config(text=f"正在实时读取云端 {subpath} ..."))
            self.log(f"正在从云端读取文本: {target_url}")
            
            mixed_port = self.get_clash_mixed_port()
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            proxy_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
            direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))

            content_str = ""
            success = False
            last_err = ""

            for opener in [proxy_opener, direct_opener]:
                try:
                    req = urllib.request.Request(target_url, headers={"User-Agent": "ClashVergeNodeAssistant/1.0"})
                    with opener.open(req, timeout=10) as resp:
                        content_str = resp.read().decode("utf-8", errors="ignore")
                        success = True
                        break
                except Exception as ex:
                    last_err = str(ex)

            def _update_ui():
                self.cloud_text_box.config(state="normal")
                self.cloud_text_box.delete("1.0", tk.END)
                if success:
                    self.cloud_text_box.insert(tk.END, content_str)
                    self.status_label.config(text=f"成功读取云端 {subpath} ({len(content_str)} 字节)")
                    self.log(f"成功读取云端 {subpath}")
                else:
                    self.cloud_text_box.insert(tk.END, f"❌ 读取失败 ({target_url})\n错误原因: {last_err}\n\n请检查 Worker 地址是否正确、网络是否畅通或是否已成功推送过该文本。")
                    self.status_label.config(text=f"读取云端 {subpath} 失败")
                self.cloud_text_box.config(state="disabled")

            self.root.after(0, _update_ui)

        threading.Thread(target=_worker, daemon=True).start()

    def copy_cloud_text(self):
        txt = self.cloud_text_box.get("1.0", tk.END).strip()
        if not txt:
            messagebox.showinfo("提示", "当前文本框为空！")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(txt)
        messagebox.showinfo("复制成功", "🎉 已将当前云端文本内容复制到剪贴板！")


```

## File: `gui_fluent/__init__.py`

```python
"""
Clash Verge 节点管理助手 - Fluent UI 组件库
"""
```

## File: `gui_fluent/app_controller.py`

```python
"""
Clash Verge 节点管理助手 - Fluent UI 中枢控制器
作为所有页面和前端组件调用核心业务逻辑的唯一网关
"""
import sys

# 动态判断使用的 Qt 绑定以确保兼容
if "PyQt5" in sys.modules:
    from PyQt5.QtCore import QObject, pyqtSignal
else:
    from PyQt6.QtCore import QObject, pyqtSignal

import json
import os
import re
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from core.state_manager import StateManager
import config.config_manager
from pipelines.scheduler import SchedulerDaemon
from services.auto_heal_watcher import AutoHealWatcher
from services.clash_client import ClashClient
from services.subscription_service import (
    SubscriptionService,
    extract_nodes_and_details_from_file,
    choose_canonical_node_name,
    get_node_endpoint,
    resolve_node_to_current,
    update_remote_subscription,
)
from services.colo_service import is_asian_node, analyze_colo_stats
from services.filter_service import compute_delay_stats
from services.pool_service import (
    get_pool_endpoint_sets,
    deduplicate_favorites_by_endpoint,
    align_favorites_with_current_subscription,
    clean_offline_favorites,
    process_verified_lifecycle,
    purge_invalid_and_blacklisted_from_all_pools,
)
from services.script_generator import build_script_js, write_script_js
from utils.win32_utils import trigger_verge_reactivate_hotkey


class AppController(QObject):
    """
    中枢控制器：持有全局状态容器、Clash 客户端实例与配置持久化接口，
    向 UI 暴露线程安全的信号与方法。
    """
    log_signal = pyqtSignal(str)
    data_changed = pyqtSignal()
    pipeline_rows_updated = pyqtSignal(list)
    pipeline_status_updated = pyqtSignal(str)
    pipeline_finished = pyqtSignal(bool, str)

    fav_pipeline_status_updated = pyqtSignal(str)
    fav_pipeline_finished = pyqtSignal(bool, str)
    fav_pipeline_fallback_needed = pyqtSignal(str)

    scheduler_trigger_full_signal = pyqtSignal(str)
    scheduler_trigger_fav_signal = pyqtSignal(str)

    auto_heal_status_updated = pyqtSignal(dict)
    auto_heal_event_triggered = pyqtSignal(str, str, dict)

    @property
    def pending_pool_lock(self):
        if not hasattr(self, "_pending_pool_lock"):
            self._pending_pool_lock = threading.Lock()
        return self._pending_pool_lock

    def __init__(self, parent=None):
        super().__init__(parent)
        self.state = StateManager()
        self.state.blacklist_timestamps = {}
        self.state.cloud_endpoints = {}
        self.clash_client = ClashClient(base_url="http://127.0.0.1:9097")
        self._pipeline_worker = None
        self._fav_pipeline_worker = None
        self._is_checking_google_hk = False
        self._scheduler_config_provider = None
        self._load_persisted_into_state()

        # 启动后台常驻定时调度守护进程
        self._scheduler = SchedulerDaemon(
            get_config_fn=self._get_scheduler_config,
            on_trigger_full=self._on_scheduler_trigger_full,
            on_trigger_fav=self._on_scheduler_trigger_fav,
        )
        self._scheduler.start()

        # 启动后台秒级链路感知与无感自愈守护服务
        self.auto_heal_watcher = AutoHealWatcher(
            client=self.clash_client,
            get_candidates_fn=self._get_auto_heal_candidates,
            on_heal_event=self._on_auto_heal_event,
            on_status_update=self._on_auto_heal_status_update,
            log_fn=self.log,
            is_pipeline_running_fn=self.is_pipeline_running,
        )
        self.auto_heal_watcher.start()

    def _on_auto_heal_event(self, dead_node: str, backup_node: str, info: dict):
        self.auto_heal_event_triggered.emit(dead_node, backup_node, info)

    def _on_auto_heal_status_update(self, status: dict):
        self.auto_heal_status_updated.emit(status)

    def _get_auto_heal_candidates(self, is_non_hk: bool = False) -> list:
        """
        按实测下载速度与延迟综合排序精选池中的健康候选节点，
        若 is_non_hk 为 True，严格排除所有香港与大陆节点，确保 Gemini/反重力 100% 纯净分流。
        """
        from config.settings import EXCLUDE_HK_REGEX

        with self.state.lock:
            favs = list(self.state.favorites)
            speeds = dict(self.state.node_speeds)
            delays = dict(self.state.node_delays)

        if not favs:
            try:
                proxies_map = self.clash_client.get_proxies()
                grp_key = "⚡ 自动选择 (非香港)" if is_non_hk else "⚡ 自动选择"
                favs = list(proxies_map.get(grp_key, {}).get("all", []))
            except Exception:
                favs = []

        if is_non_hk:
            ghk_nodes = set()
            if hasattr(self, "auto_heal_watcher") and hasattr(self.auto_heal_watcher, "google_hk_nodes"):
                now = time.time()
                ghk_nodes = {k for k, v in self.auto_heal_watcher.google_hk_nodes.items() if v > now}
            favs = [n for n in favs if n and not EXCLUDE_HK_REGEX.search(n) and n not in ghk_nodes]

        def sort_key(name):
            sp = speeds.get(name, 0.0)
            if sp <= 0.0:
                m = re.search(r"([\d.]+)\s*MB/s", name)
                if m:
                    try:
                        sp = float(m.group(1))
                    except Exception:
                        pass
            dl = delays.get(name, 9999)
            return (-sp, dl)

        favs.sort(key=sort_key)
        return favs

    def toggle_auto_heal(self, enabled: bool):
        if hasattr(self, "auto_heal_watcher"):
            self.auto_heal_watcher.update_config(enabled=enabled)
            status_text = "开启" if enabled else "关闭"
            self.log(f"🛡️ [自愈引擎] 已手动{status_text}断流秒级自愈守护")

    def diagnose_current_link(self) -> dict:
        if hasattr(self, "auto_heal_watcher"):
            res = self.auto_heal_watcher.diagnose_current_link()
            self.log(
                f"🩺 [双通道诊断] 全量出口: 【{res.get('active_node')}】(延迟: {res.get('delay_ms')}ms) | "
                f"非港出口(Gemini/AI): 【{res.get('active_nohk_node')}】(延迟: {res.get('delay_nohk_ms')}ms) | "
                f"活跃连接: {res.get('total_connections')}条"
            )
            return res
        return {}


    def set_scheduler_config_provider(self, provider_fn):
        """
        注册动态定时配置提供者回调 (通常绑定自 MainWindow)
        """
        self._scheduler_config_provider = provider_fn

    def _get_scheduler_config(self) -> dict:
        """
        动态提取定时调度器所需的当前配置字典
        """
        cfg = {}
        if callable(self._scheduler_config_provider):
            try:
                cfg = self._scheduler_config_provider() or {}
            except Exception:
                cfg = {}
        if not cfg:
            cfg = self.load_config() or {}
        cfg["is_pipeline_running"] = self.is_pipeline_running()
        return cfg

    def _on_scheduler_trigger_full(self, reason: str):
        """
        后台定时调度触发全自动大优选
        """
        self.log(f"⏰ [定时调度] 触发全量大优选: {reason}")
        self.scheduler_trigger_full_signal.emit(reason)

    def _on_scheduler_trigger_fav(self, reason: str):
        """
        后台定时调度触发优质精选池复检
        """
        self.log(f"⏰ [定时调度] 触发优质精选复检: {reason}")
        self.scheduler_trigger_fav_signal.emit(reason)

    def _load_persisted_into_state(self):
        """
        启动时自动载入磁盘持久化数据到 StateManager
        """
        data = self.load_config()
        if not data:
            return
        with self.state.lock:
            self.state.favorites = set(data.get("favorites", []))
            self.state.local_blacklist = set(data.get("local_blacklist", []))
            self.state.speed_blacklist = set(data.get("speed_blacklist", []))
            self.state.blacklist_reasons = dict(data.get("blacklist_reasons", {}))
            self.state.fav_reasons = dict(data.get("fav_reasons", {}))
            self.state.verified_nodes = dict(data.get("verified_nodes", {}))
            self.state.stars_nodes = list(data.get("stars_nodes", []))
            self.state.node_delays = dict(data.get("node_delays", {}))
            self.state.node_speeds = dict(data.get("node_speeds", {}))
            self.state.node_colo = dict(data.get("node_colo", {}))
            self.state.node_history = dict(data.get("node_history", {}))
            self.state.node_speed_history = dict(data.get("node_speed_history", {}))
            self.state.node_delay_history = dict(data.get("node_delay_history", {}))
            self.state.node_colo_history = dict(data.get("node_colo_history", {}))
            self.state.blacklist_timestamps = dict(data.get("blacklist_timestamps", {}))
            self.state.cloud_endpoints = dict(data.get("cloud_endpoints", {}))
        self.clean_favorites_ghost_tokens()
        self.heal_falsely_blacklisted_nodes()

    def heal_falsely_blacklisted_nodes(self):
        """
        历史误判节点智能自愈程序：
        若节点拉黑原因为“非亚洲节点 (自动过滤)”，但在新净化规则或其实测物理Colo下确认为亚洲节点，
        自动将其从 local_blacklist 和 blacklist_reasons 中移出释放，拯救误杀节点重回待测池！
        """
        with self.state.lock:
            healed = []
            for bl_node in list(self.state.local_blacklist):
                reason = self.state.blacklist_reasons.get(bl_node, "")
                if "非亚洲" in reason:
                    ep = self._get_ep(bl_node)
                    c = self.state.node_colo.get(bl_node, self.state.node_colo.get(ep, "-"))
                    if is_asian_node(bl_node, colo=c):
                        self.state.local_blacklist.discard(bl_node)
                        self.state.blacklist_reasons.pop(bl_node, None)
                        if ep:
                            self.state.local_blacklist.discard(ep)
                            self.state.blacklist_reasons.pop(ep, None)
                        healed.append(bl_node)
            if healed:
                self.log(f"🌿 [智能自愈] 已成功将 {len(healed)} 个误判为非亚洲的历史节点从黑名单中释放恢复！")
                self.save_config({
                    "local_blacklist": list(self.state.local_blacklist),
                    "blacklist_reasons": self.state.blacklist_reasons,
                })


    def log(self, msg: str):
        """
        统一日志记录：控制台输出并触发 Qt 信号通知 LogPanel
        """
        try:
            print(f"[Fluent Controller] {msg}")
        except UnicodeEncodeError:
            try:
                enc = sys.stdout.encoding or "gbk"
                safe_msg = str(msg).encode(enc, errors="replace").decode(enc, errors="replace")
                print(f"[Fluent Controller] {safe_msg}")
            except Exception:
                pass
        except Exception:
            pass
        self.log_signal.emit(str(msg))


    def get_state_snapshot(self) -> dict:
        """
        获取当前核心数据池的只读快照
        """
        snap = self.state.get_snapshot()
        for k, v in list(snap.items()):
            if isinstance(v, (set, frozenset)):
                snap[k] = list(v)
        snap["blacklist_timestamps"] = dict(getattr(self.state, "blacklist_timestamps", {}))
        snap["cloud_endpoints"] = dict(getattr(self.state, "cloud_endpoints", {}))
        return snap

    def clean_favorites_ghost_tokens(self):
        """
        清洗 favorites 幽灵节点：
        若某 Endpoint 已存在正常的节点名，则务必剔除 favorites 集合中该 Endpoint 的纯 IP 字符串形式，
        确保 Script.js 和状态里只存正确名称，不存纯 IP。
        """
        with self.state.lock:
            ep_to_names = {}
            all_nodes_list = getattr(self.state, "all_nodes", []) or []
            stars_nodes_list = getattr(self.state, "stars_nodes", []) or []
            for item in list(all_nodes_list) + [s.get("matched_name", "") for s in stars_nodes_list if isinstance(s, dict)]:
                if not item:
                    continue
                ep = self._get_ep(item)
                if ep and ep != item and not re.match(r"^[\w\.\-]+\:\d+$", str(item).strip()):
                    ep_to_names.setdefault(ep, set()).add(item)

            for f in list(self.state.favorites):
                ep = self._get_ep(f)
                if ep and ep != f and not re.match(r"^[\w\.\-]+\:\d+$", str(f).strip()):
                    ep_to_names.setdefault(ep, set()).add(f)

            to_discard = []
            for item in list(self.state.favorites):
                str_item = str(item).strip()
                if re.match(r"^[\w\.\-]+\:\d+$", str_item):
                    if str_item in ep_to_names and len(ep_to_names[str_item]) > 0:
                        to_discard.append(item)

            if to_discard:
                for d in to_discard:
                    self.state.favorites.discard(d)
                self.log(f"🧹 清洗 favorites 幽灵节点: 剔除了 {len(to_discard)} 个同端点纯 IP 冗余项")
            return len(to_discard)

    def generate_script_and_reload(self):
        """
        生成 Script.js 策略组配置并触发 Win32 系统热键刷新 Verge（等同 trigger_verge_reload）
        """
        return self.trigger_verge_reload()

    def get_clash_connection_status(self) -> tuple[bool, str]:
        """
        检测与 Clash 内核的连接状态。
        返回: (is_connected: bool, version_str: str)
        直接调用 self.clash_client.test_connection()
        """
        return self.clash_client.test_connection()

    def update_clash_credentials(self, port: int, secret: str):
        """
        更新 Clash API 连接参数（端口与密钥）。
        调用 self.clash_client.update_credentials(port=port, secret=secret)
        """
        self.clash_client.update_credentials(port=port, secret=secret)

    def get_all_yaml_profiles(self) -> list[str]:
        """
        扫描 Clash Verge 的 profiles 目录，返回所有 .yaml 配置文件的文件名列表。
        直接读取 config.settings.BASE_DIR 目录，返回所有 *.yaml 文件名（只取文件名，不含路径）。
        """
        import glob
        import os
        from config.settings import BASE_DIR
        yamls = glob.glob(os.path.join(BASE_DIR, "*.yaml"))
        return [os.path.basename(f) for f in yamls]

    def load_nodes_from_profile(self, yaml_filename: str, cloud_endpoints: dict = None) -> tuple[list, dict]:
        """
        解析指定的 Clash 订阅 YAML 文件，返回节点名称列表与详情字典。
        调用 services.subscription_service.extract_nodes_and_details_from_file()。
        支持物理端点 (IP:Port) 绝对去重，且云端专属名称 (cloud_endpoints) 具备最高霸占优先级。
        """
        import os
        from config.settings import BASE_DIR
        from services.subscription_service import extract_nodes_and_details_from_file, get_node_endpoint
        filepath = os.path.join(BASE_DIR, yaml_filename)
        nodes, details = extract_nodes_and_details_from_file(filepath)

        # 获取或更新 cloud_endpoints
        if cloud_endpoints is not None:
            setattr(self.state, "cloud_endpoints", cloud_endpoints)
        else:
            cloud_endpoints = getattr(self.state, "cloud_endpoints", {})

        ep_to_info = {}
        non_ep_nodes = []
        used_names = set()

        for n in nodes:
            d = details.get(n, {})
            ep = get_node_endpoint(n, details)
            if not ep:
                non_ep_nodes.append((n, d))
                continue

            cloud_name = ""
            if cloud_endpoints:
                if ep in cloud_endpoints and cloud_endpoints[ep]:
                    cloud_name = cloud_endpoints[ep]
                elif ":" in ep:
                    ip_only = ep.split(":", 1)[0]
                    if ip_only in cloud_endpoints and cloud_endpoints[ip_only]:
                        cloud_name = cloud_endpoints[ip_only]

            if ep not in ep_to_info:
                target_name = cloud_name if cloud_name else n
                ep_to_info[ep] = {
                    "final_name": target_name,
                    "original_name": n,
                    "detail": d,
                    "has_cloud": bool(cloud_name),
                }
            else:
                # 若已有该端点记录，但当前节点命中云端专属名称而前一个未命中，则优先采用云端名称
                if cloud_name and not ep_to_info[ep]["has_cloud"]:
                    ep_to_info[ep] = {
                        "final_name": cloud_name,
                        "original_name": n,
                        "detail": d,
                        "has_cloud": True,
                    }

        final_nodes = []
        final_details = {}

        # 整理去重后的端点映射
        for ep, info in ep_to_info.items():
            base_name = info["final_name"]
            orig_name = info["original_name"]
            node_d = dict(info["detail"])

            # 云端专属保活规范名具备最高霸占优先级，彻底去牛皮癣并统一全局命名规范
            if info.get("has_cloud") and base_name:
                target_name = base_name
                suffix_idx = 1
                while target_name in used_names:
                    suffix_idx += 1
                    target_name = f"{base_name} {suffix_idx}"
            elif orig_name and orig_name not in used_names:
                target_name = orig_name
            else:
                target_name = base_name
                suffix_idx = 1
                while target_name in used_names:
                    suffix_idx += 1
                    target_name = f"{base_name} {suffix_idx}"

            used_names.add(target_name)
            node_d["name"] = target_name
            final_nodes.append(target_name)
            final_details[target_name] = node_d
            if orig_name and orig_name != target_name:
                final_details[orig_name] = dict(node_d)

        for n, d in non_ep_nodes:
            target_name = n
            suffix_idx = 1
            while target_name in used_names:
                suffix_idx += 1
                target_name = f"{n} ({suffix_idx})"
            used_names.add(target_name)
            node_d = dict(d)
            node_d["name"] = target_name
            final_nodes.append(target_name)
            final_details[target_name] = node_d

        with self.state.lock:
            self.state.all_nodes = final_nodes
            # 采用增量更新，保留历史节点端点映射，供 reconcile_endpoints 精准迁移历史精选/黑名单
            self.state.node_details.update(final_details)
            self.state.active_profile = yaml_filename

        self.reconcile_endpoints()
        return final_nodes, final_details

    def save_config(self, config_dict: dict, filepath: str = None):
        """
        持久化保存配置字典到磁盘。
        合并现有配置并调用 config.config_manager.atomic_save_config
        """
        from config.settings import CONFIG_STORAGE_PATH
        from config.config_manager import atomic_save_config, safe_load_config
        target_path = filepath or CONFIG_STORAGE_PATH
        current = {}
        try:
            current = safe_load_config(target_path) or {}
        except Exception:
            current = {}

        if "blacklist_timestamps" not in config_dict and hasattr(self.state, "blacklist_timestamps"):
            config_dict["blacklist_timestamps"] = dict(getattr(self.state, "blacklist_timestamps", {}))
        if "cloud_endpoints" not in config_dict and hasattr(self.state, "cloud_endpoints"):
            config_dict["cloud_endpoints"] = dict(getattr(self.state, "cloud_endpoints", {}))

        # 深度转换集合为列表
        clean_dict = {}
        for k, v in config_dict.items():
            if isinstance(v, (set, frozenset)):
                clean_dict[k] = list(v)
            else:
                clean_dict[k] = v

        current.update(clean_dict)
        ok, err = atomic_save_config(target_path, current)
        if not ok:
            self.log(f"❌ [持久化致命错误] 配置文件写入失败: {err}")
        else:
            # self.log("💾 配置已安全同步存盘")
            pass

    def load_config(self, filepath: str = None) -> dict:
        """
        从磁盘加载持久化配置。
        调用 config.config_manager.safe_load_config()，失败返回空 dict。
        """
        from config.settings import CONFIG_STORAGE_PATH
        from config.config_manager import safe_load_config
        target_path = filepath or CONFIG_STORAGE_PATH
        try:
            return safe_load_config(target_path) or {}
        except Exception:
            return {}

    def is_pipeline_running(self) -> bool:
        """
        判断流水线或单项核验当前是否正在后台运行 (全自动大优选/精选池复测/送中核验)
        """
        auto_running = self._pipeline_worker is not None and self._pipeline_worker.isRunning()
        fav_running = self._fav_pipeline_worker is not None and self._fav_pipeline_worker.isRunning()
        hk_check_running = getattr(self, "_is_checking_google_hk", False)
        return auto_running or fav_running or hk_check_running

    def start_auto_pipeline(self, config: dict) -> bool:
        """
        启动全自动优选流水线
        """
        if self.is_pipeline_running():
            self.log("⚠️ 当前已有正在运行的优选流水线，请先终止或等待完成！")
            return False

        from gui_fluent.pipelines.auto_pipeline import AutoPipelineWorker

        if self._pipeline_worker is not None:
            self._pipeline_worker.wait(500)

        self._pipeline_worker = AutoPipelineWorker(self, config, parent=self)
        self._pipeline_worker.log_signal.connect(self.log)
        self._pipeline_worker.status_signal.connect(self.pipeline_status_updated)
        self._pipeline_worker.rows_updated.connect(self.pipeline_rows_updated)

        def _on_auto_finished(ok, desc):
            if ok and hasattr(self, "_scheduler") and self._scheduler:
                self._scheduler.update_last_run(full_ts=time.time())
            if hasattr(self, "auto_heal_watcher") and self.auto_heal_watcher:
                self.auto_heal_watcher.last_heal_timestamp = time.time() - self.auto_heal_watcher.min_switch_interval
                self.auto_heal_watcher.current_status_summary = "正常守护中"
                self.auto_heal_watcher._notify_status()
            self.pipeline_finished.emit(ok, desc)

        self._pipeline_worker.finished_signal.connect(_on_auto_finished)
        self._pipeline_worker.start()
        return True

    def stop_auto_pipeline(self):
        """
        请求终止全自动优选流水线
        """
        if self._pipeline_worker is not None and self._pipeline_worker.isRunning():
            self.log("⏹ 正在请求终止全量大优选流水线...")
            self._pipeline_worker.stop()
            self._pipeline_worker.wait(2000)

    def start_fav_pipeline(self, config: dict) -> bool:
        """
        启动优质精选池复测流水线
        """
        if self.is_pipeline_running():
            self.log("⚠️ 当前已有正在运行的优选流水线，请先终止或等待完成！")
            return False

        from gui_fluent.pipelines.fav_pipeline import FavPipelineWorker

        if self._fav_pipeline_worker is not None:
            self._fav_pipeline_worker.wait(500)

        self._fav_pipeline_worker = FavPipelineWorker(self, config, parent=self)
        self._fav_pipeline_worker.log_signal.connect(self.log)
        self._fav_pipeline_worker.status_signal.connect(self.fav_pipeline_status_updated)

        def _on_fav_finished(ok, desc):
            if ok and hasattr(self, "_scheduler") and self._scheduler:
                self._scheduler.update_last_run(fav_ts=time.time())
            if hasattr(self, "auto_heal_watcher") and self.auto_heal_watcher:
                self.auto_heal_watcher.last_heal_timestamp = time.time() - self.auto_heal_watcher.min_switch_interval
                self.auto_heal_watcher.current_status_summary = "正常守护中"
                self.auto_heal_watcher._notify_status()
            self.fav_pipeline_finished.emit(ok, desc)

        self._fav_pipeline_worker.finished_signal.connect(_on_fav_finished)
        self._fav_pipeline_worker.fallback_needed.connect(self.fav_pipeline_fallback_needed)
        self._fav_pipeline_worker.start()
        return True

    def stop_fav_pipeline(self):
        """
        请求终止精选池复测流水线
        """
        if self._fav_pipeline_worker is not None and self._fav_pipeline_worker.isRunning():
            self.log("⏹ 正在请求终止精选池复测流水线...")
            self._fav_pipeline_worker.stop()
            self._fav_pipeline_worker.wait(2000)

    # ==================== 辅助数据转换函数 ====================

    def _get_ep(self, n: str) -> str:
        """
        统一获取节点的物理 IP:Port 端点
        """
        return get_node_endpoint(
            n,
            node_details=self.state.node_details,
            all_nodes=self.state.all_nodes,
            verified_nodes=self.state.verified_nodes,
            clash_client=self.clash_client,
        )

    def _format_hist(self, delays: list) -> str:
        """
        格式化延迟轨迹：10ms → 20ms → ✕超时
        """
        if not delays:
            return "-"
        formatted = []
        for d in delays:
            if d >= 99999 or d <= 0:
                formatted.append("✕超时")
            else:
                formatted.append(f"{d}ms")
        return " → ".join(formatted)

    def _format_speed_hist(self, speeds: list) -> str:
        """
        格式化测速历史：10.50M → 12.00M
        """
        if not speeds:
            return "-"
        return " → ".join([f"{s:.2f}M" for s in speeds[-4:]])

    def _migrate_node_name(self, old_name: str, new_name: str, ep: str = None):
        """
        当检测到节点的物理端点 (IP:Port) 存在但订阅中名称更新时，热更新本地状态容器
        """
        if not old_name or not new_name or old_name == new_name:
            return

        # 1. 精选池与原因迁移
        if old_name in self.state.favorites:
            self.state.favorites.discard(old_name)
            self.state.favorites.add(new_name)
        if old_name in self.state.fav_reasons:
            self.state.fav_reasons[new_name] = self.state.fav_reasons.pop(old_name)

        # 2. 黑名单与原因迁移
        if old_name in self.state.local_blacklist:
            self.state.local_blacklist.discard(old_name)
            self.state.local_blacklist.add(new_name)
        if old_name in self.state.speed_blacklist:
            self.state.speed_blacklist.discard(old_name)
            self.state.speed_blacklist.add(new_name)
        if old_name in self.state.blacklist_reasons:
            self.state.blacklist_reasons[new_name] = self.state.blacklist_reasons.pop(old_name)

        # 3. 实时测速与 Colo 状态迁移
        if old_name in self.state.node_delays and new_name not in self.state.node_delays:
            self.state.node_delays[new_name] = self.state.node_delays.pop(old_name)
        if old_name in self.state.node_speeds and new_name not in self.state.node_speeds:
            self.state.node_speeds[new_name] = self.state.node_speeds.pop(old_name)
        if old_name in self.state.node_colo and new_name not in self.state.node_colo:
            self.state.node_colo[new_name] = self.state.node_colo.pop(old_name)

        # 4. 历史时序数据迁移
        if old_name in self.state.node_history:
            old_h = self.state.node_history.pop(old_name)
            if new_name not in self.state.node_history:
                self.state.node_history[new_name] = old_h
        if old_name in self.state.node_delay_history:
            old_dh = self.state.node_delay_history.pop(old_name)
            if new_name not in self.state.node_delay_history:
                self.state.node_delay_history[new_name] = old_dh
        if old_name in self.state.node_speed_history:
            old_sh = self.state.node_speed_history.pop(old_name)
            if new_name not in self.state.node_speed_history:
                self.state.node_speed_history[new_name] = old_sh
        if old_name in self.state.node_colo_history:
            old_ch = self.state.node_colo_history.pop(old_name)
            if new_name not in self.state.node_colo_history:
                self.state.node_colo_history[new_name] = old_ch

    def reconcile_endpoints(self) -> int:
        """
        根据当前订阅中所有节点的物理端点 (IP:Port)，智能对齐迁移并净化：
        1. 精选池 favorites (支持云端双向免死白名单，自动清理彻底灭绝的过期时间戳幽灵马甲)
        2. 延迟黑名单 local_blacklist
        3. 低速黑名单 speed_blacklist
        4. 规范化 verified_nodes 键名
        返回迁移成功的节点数量。
        """
        with self.state.lock:
            if not self.state.all_nodes:
                return 0

            current_endpoints = {}
            current_ip_map = {}
            for n in self.state.all_nodes:
                ep = get_node_endpoint(n, self.state.node_details)
                if ep:
                    current_endpoints[ep] = n
                    if ":" in ep:
                        ip_only = ep.split(":", 1)[0]
                        if ip_only not in current_ip_map:
                            current_ip_map[ip_only] = n

            if not current_endpoints:
                return 0

            migrated_count = 0
            # 1. 对齐精选池 (支持云端绝对免死白名单与历史废弃马甲安全清洗)
            cloud_eps = getattr(self.state, "cloud_endpoints", {})
            for old_name in list(self.state.favorites):
                old_ep = get_node_endpoint(old_name, self.state.node_details)
                # 补充保护：若无法从 node_details 解析端点，尝试通过云端双向映射（Key与Value）反查物理端点
                if not old_ep and cloud_eps:
                    if old_name in cloud_eps:
                        old_ep = old_name
                    else:
                        for c_ep, c_rem in cloud_eps.items():
                            if c_rem and (c_rem == old_name or str(old_name).startswith(c_rem)):
                                old_ep = c_ep
                                break

                # 优先检查云端/优选规范命名，确保规范名称最高优先级，绝不降级回生硬机场名
                canonical_cand = None
                if old_ep and cloud_eps:
                    canonical_cand = cloud_eps.get(old_ep)
                    if not canonical_cand and ":" in old_ep:
                        canonical_cand = cloud_eps.get(old_ep.split(":", 1)[0])

                if canonical_cand:
                    if canonical_cand != old_name:
                        self._migrate_node_name(old_name, canonical_cand, old_ep)
                        migrated_count += 1
                elif old_name not in self.state.all_nodes:
                    if old_ep:
                        new_name = current_endpoints.get(old_ep)
                        if not new_name and ":" in old_ep:
                            new_name = current_ip_map.get(old_ep.split(":", 1)[0])
                        if new_name and new_name != old_name:
                            self._migrate_node_name(old_name, new_name, old_ep)
                            migrated_count += 1
                        # 若当前订阅中该端点暂时缺席，但它是云端保活节点，绝对保留，绝不误删！
                    elif old_name not in cloud_eps and old_name not in cloud_eps.values():
                        # 既无物理端点、也不在当前订阅、且在云端无任何登记的彻底失效历史马甲（如过期时间戳），安全移除，消除“订阅缺失”
                        self.state.favorites.discard(old_name)
                        self.state.fav_reasons.pop(old_name, None)
                        self.log(f"🧹 自动清除无有效端点的历史废弃马甲: {old_name}")

            # 2. 对齐延迟黑名单
            for old_name in list(self.state.local_blacklist):
                if old_name not in self.state.all_nodes:
                    old_ep = get_node_endpoint(old_name, self.state.node_details)
                    if old_ep:
                        new_name = current_endpoints.get(old_ep)
                        if not new_name and ":" in old_ep:
                            new_name = current_ip_map.get(old_ep.split(":", 1)[0])
                        if new_name and new_name != old_name:
                            self._migrate_node_name(old_name, new_name, old_ep)
                            migrated_count += 1

            # 3. 对齐低速黑名单
            for old_name in list(self.state.speed_blacklist):
                if old_name not in self.state.all_nodes:
                    old_ep = get_node_endpoint(old_name, self.state.node_details)
                    if old_ep:
                        new_name = current_endpoints.get(old_ep)
                        if not new_name and ":" in old_ep:
                            new_name = current_ip_map.get(old_ep.split(":", 1)[0])
                        if new_name and new_name != old_name:
                            self._migrate_node_name(old_name, new_name, old_ep)
                            migrated_count += 1

            # 4. 深度规范化沉淀孵化池 verified_nodes 的 Key，确保严格为纯 IP:Port
            for k in list(self.state.verified_nodes.keys()):
                clean_k = str(k).strip()
                if "#" in clean_k:
                    clean_k = clean_k.split("#")[0].strip()
                pure_ep = None
                if re.match(r"^[\w\.\-]+\:\d+$", clean_k):
                    pure_ep = clean_k
                elif clean_k in current_endpoints:
                    pure_ep = clean_k
                elif clean_k in self.state.node_details:
                    pure_ep = get_node_endpoint(clean_k, self.state.node_details)

                if pure_ep and pure_ep != k:
                    val = self.state.verified_nodes.pop(k)
                    val["endpoint"] = pure_ep
                    self.state.verified_nodes[pure_ep] = val

            return migrated_count

    def _resolve_star_matches(self) -> dict:
        """
        建立物理端点到当前订阅节点名的逆向映射 (IP:Port -> 最新节点名)
        """
        reverse_map = {}
        for n in self.state.all_nodes:
            ep = get_node_endpoint(n, self.state.node_details)
            if ep:
                reverse_map[ep] = n
                if ":" in ep:
                    reverse_map[ep.split(":", 1)[0]] = n
        return reverse_map

    # ==================== 核心表格数据装配 ====================

    @staticmethod
    def _format_node_row_names(raw_name: str, ep: str, cloud_map: dict = None) -> tuple[str, str]:
        """
        拆分物理端点与节点名称。
        - IP:端口 列：必须清洗为规范的纯 IP:Port（如 177.3.89.22:443）。
        - 节点名称 列：优先显示用户云端专属规范名 {Colo} {Speed} MB/s。如果原名为机场长广告，一律被该规范名覆盖替换，彻底去牛皮癣化。
        """
        clean_name = str(raw_name).strip() if raw_name else ""
        clean_ep = str(ep).strip() if ep else ""
        if "#" in clean_ep:
            clean_ep = clean_ep.split("#")[0].strip()

        if not clean_ep and clean_name:
            if re.match(r"^[\w\.\-]+\:\d+$", clean_name):
                clean_ep = clean_name
            else:
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", clean_name)
                if m:
                    clean_ep = m.group(1)
                elif re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", clean_name):
                    clean_ep = clean_name
        elif clean_ep:
            if not re.match(r"^[\w\.\-]+\:\d+$", clean_ep):
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", clean_ep)
                if m:
                    clean_ep = m.group(1)

        ep_disp = clean_ep if clean_ep else "-"

        # 优先从 cloud_map 获取云端专属规范名，彻底抹除原机场长广告名
        cloud_name = ""
        if cloud_map:
            if clean_ep and clean_ep in cloud_map:
                cloud_name = cloud_map[clean_ep]
            elif clean_ep and ":" in clean_ep and clean_ep.split(":", 1)[0] in cloud_map:
                cloud_name = cloud_map[clean_ep.split(":", 1)[0]]
            elif clean_name and clean_name in cloud_map:
                cloud_name = cloud_map[clean_name]

        if cloud_name:
            name_disp = cloud_name
        elif not clean_name or clean_name == "-" or clean_name == ep_disp or re.match(r"^[\w\.\-]+\:\d+$", clean_name) or re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", clean_name):
            name_disp = "无"
        else:
            name_disp = clean_name
        return ep_disp, name_disp

    def get_table_rows(self, tab_type: str) -> list[dict]:
        """
        根据 tab_type 装配对应表格的数据行字典列表
        严格对齐 NodeTableView (12列), VerifiedTableView (10列), StarsTableView (8列)
        以物理端点 (IP:Port) 为核心基准追踪匹配，支持自动热迁移改名节点
        """
        # 先行做一次端点对齐热更新
        self.reconcile_endpoints()

        with self.state.lock:
            now = time.time()
            current_endpoints = {}
            current_ip_map = {}
            for n in self.state.all_nodes:
                ep = get_node_endpoint(n, self.state.node_details)
                if ep:
                    current_endpoints[ep] = n
                    if ":" in ep:
                        ip_only = ep.split(":", 1)[0]
                        if ip_only not in current_ip_map:
                            current_ip_map[ip_only] = n

            fav_eps, bl_eps, sbl_eps, star_eps = get_pool_endpoint_sets(
                self.state.favorites,
                self.state.local_blacklist,
                self.state.speed_blacklist,
                self.state.auto_endpoints,
                self.state.verified_nodes,
                self.state.stars_nodes,
                self._get_ep,
            )

            if tab_type == "active":
                untested_groups = {}
                for name in self.state.all_nodes:
                    ep_val = self._get_ep(name)
                    c_val = self.state.node_colo.get(ep_val, self.state.node_colo.get(name, "-"))
                    is_asian = is_asian_node(name, colo=c_val)
                    if not is_asian:
                        is_d_black = True
                        is_s_black = False
                    else:
                        is_d_black = (name in self.state.local_blacklist) or (ep_val and ep_val in self.state.local_blacklist)
                        is_s_black = not is_d_black and ((name in self.state.speed_blacklist) or (ep_val and ep_val in self.state.speed_blacklist))

                    is_fav = not is_d_black and not is_s_black and (name in self.state.favorites)
                    is_fav_alias = not is_d_black and not is_s_black and not is_fav and (ep_val and ep_val in fav_eps)
                    is_ver_star = not is_d_black and not is_s_black and not is_fav and not is_fav_alias and ((name in self.state.verified_nodes) or (ep_val and ep_val in star_eps))

                    if not is_d_black and not is_s_black and not is_fav and not is_fav_alias and not is_ver_star:
                        key = ep_val if ep_val else name
                        untested_groups.setdefault(key, []).append(name)

                rows = []
                for ep_key, group_nodes in untested_groups.items():
                    canonical_name = choose_canonical_node_name(group_nodes)
                    d_val = self.state.node_delays.get(canonical_name, self.state.node_delays.get(ep_key, None))
                    if d_val is None:
                        d_str = "未测速"
                    elif d_val >= 99999:
                        d_str = "超时 / 失败"
                    else:
                        d_str = f"{d_val} ms"

                    s_val = self.state.node_speeds.get(canonical_name, self.state.node_speeds.get(ep_key, None))
                    if s_val is None:
                        s_str = "-"
                    elif s_val < 0:
                        s_str = "测速失败"
                    else:
                        s_str = f"{s_val:.2f} MB/s"

                    colo_str = self.state.node_colo.get(ep_key, self.state.node_colo.get(canonical_name, "-"))
                    colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(ep_key, self.state.node_colo_history.get(canonical_name, [])), now, node_name=canonical_name)[3]
                    cur_avg_str, hist_avg_str = compute_delay_stats(canonical_name, ep_key, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                    delay_hist_str = self._format_hist(self.state.node_history.get(canonical_name, []))
                    speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(canonical_name, []))

                    ep_disp, name_disp = self._format_node_row_names(canonical_name, ep_key, self.state.cloud_endpoints)

                    rows.append({
                        "status": "⚪ 活跃待测",
                        "colo": colo_str,
                        "colo_hist": colo_hist_str,
                        "reason": "-",
                        "delay": d_str,
                        "avg_delay": cur_avg_str,
                        "delay_hist": delay_hist_str,
                        "hist_avg": hist_avg_str,
                        "speed": s_str,
                        "speed_hist": speed_hist_str,
                        "endpoint": ep_disp,
                        "IP:端口": ep_disp,
                        "name": name_disp,
                        "节点名称": name_disp,
                        "raw_name": canonical_name or ep_key,
                    })
                return rows

            elif tab_type == "favorites":
                rows = []
                seen_fav_eps = set()
                # 1. 订阅内的精选节点 (包含通过 endpoint 追踪已热对齐的节点)
                for name in self.state.all_nodes:
                    ep_val = self._get_ep(name)
                    is_d_black = (name in self.state.local_blacklist) or (ep_val and ep_val in self.state.local_blacklist)
                    is_s_black = not is_d_black and ((name in self.state.speed_blacklist) or (ep_val and ep_val in self.state.speed_blacklist))
                    if not is_d_black and not is_s_black and (name in self.state.favorites or (ep_val and ep_val in fav_eps)):
                        ep_key = ep_val if ep_val else name
                        if ep_key in seen_fav_eps:
                            continue
                        seen_fav_eps.add(ep_key)

                        d_val = self.state.node_delays.get(name, None)
                        if d_val is None:
                            d_str = "未测速"
                        elif d_val >= 99999:
                            d_str = "超时 / 失败"
                        else:
                            d_str = f"{d_val} ms"

                        s_val = self.state.node_speeds.get(name, None)
                        s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else ("测速失败" if s_val is not None else "-")
                        colo_str = self.state.node_colo.get(ep_val, self.state.node_colo.get(name, "-"))
                        colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(ep_val, self.state.node_colo_history.get(name, [])), now, node_name=name)[3]
                        cur_avg_str, hist_avg_str = compute_delay_stats(name, ep_val, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        delay_hist_str = self._format_hist(self.state.node_history.get(name, []))
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(name, []))
                        reason_str = self.state.fav_reasons.get(name, self.state.fav_reasons.get(ep_val, "优质精选"))

                        ep_disp, name_disp = self._format_node_row_names(name, ep_val, self.state.cloud_endpoints)

                        colo_c = colo_str if (colo_str and colo_str != "-") else "JP"
                        if not colo_c or colo_c == "-":
                            colo_c = "亚洲"
                        spd_num = s_val if (s_val is not None and s_val > 0) else 0.0
                        d_num = d_val if (d_val is not None and d_val < 99999 and d_val > 0) else 0
                        reason_val = self.state.fav_reasons.get(name, self.state.fav_reasons.get(ep_val, ""))

                        # 严禁带有延迟毫秒
                        if spd_num and spd_num > 0.1:
                            uniform_name = f"{colo_c} {spd_num:.2f} MB/s"
                        elif "C段" in reason_val:
                            uniform_name = f"{colo_c} [C段挖掘]"
                        else:
                            uniform_name = colo_c

                        # 下载速度最高优先级，若未测速则取清洗后的云端备注或标准规范名
                        if spd_num and spd_num > 0.1:
                            name_disp = uniform_name
                        elif ep_disp in self.state.cloud_endpoints:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(self.state.cloud_endpoints[ep_disp]))
                        elif ep_val and ep_val in self.state.cloud_endpoints:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(self.state.cloud_endpoints[ep_val]))
                        elif ":" in ep_disp and ep_disp.split(":")[0] in self.state.cloud_endpoints:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(self.state.cloud_endpoints[ep_disp.split(":")[0]]))
                        else:
                            name_disp = uniform_name

                        rows.append({
                            "status": "⭐ 优质精选",
                            "colo": colo_str,
                            "colo_hist": colo_hist_str,
                            "reason": reason_str,
                            "入选/拉黑原因": reason_str,
                            "delay": d_str,
                            "avg_delay": cur_avg_str,
                            "delay_hist": delay_hist_str,
                            "hist_avg": hist_avg_str,
                            "speed": s_str,
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": name or ep_val,
                        })

                # 2. 离线精选节点 (其物理 Endpoint 确实不存在于当前订阅中)
                cloud_eps = getattr(self.state, "cloud_endpoints", {})
                for fav_name in self.state.favorites:
                    if fav_name not in self.state.all_nodes:
                        ep_val = self._get_ep(fav_name)
                        ep_key = ep_val if ep_val else fav_name
                        if ep_key in seen_fav_eps:
                            continue
                        seen_fav_eps.add(ep_key)

                        cur_avg_str, hist_avg_str = compute_delay_stats(fav_name, ep_val, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(fav_name, []))
                        colo_str = self.state.node_colo.get(fav_name, self.state.node_colo.get(ep_key, "-"))
                        colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(fav_name, self.state.node_colo_history.get(ep_key, [])), now, node_name=fav_name)[3]

                        # 云端免死金牌判定
                        is_cloud = False
                        if ep_val and ep_val in cloud_eps:
                            is_cloud = True
                        elif ep_key in cloud_eps:
                            is_cloud = True
                        elif ":" in str(ep_key) and str(ep_key).split(":", 1)[0] in cloud_eps:
                            is_cloud = True
                        elif ":" in str(ep_val) and str(ep_val).split(":", 1)[0] in cloud_eps:
                            is_cloud = True

                        off_reason = self.state.fav_reasons.get(fav_name, self.state.fav_reasons.get(ep_key, "优质精选"))
                        is_c_miner = (
                            ("C段" in str(off_reason))
                            or (str(fav_name).count(".") == 3 and ":" in str(fav_name))
                            or (str(ep_val).count(".") == 3 and ":" in str(ep_val))
                            or (str(ep_key).count(".") == 3 and ":" in str(ep_key))
                        )

                        # C 段挖掘与有效端点节点，严禁误报“当前订阅缺失”错误！
                        if is_c_miner:
                            status_str = "⭐ 优质精选 (☁️云端已存)" if is_cloud else "⭐ 优质精选 (C段独立端点)"
                            reason_str = "C段深度挖掘 (☁️已同步云端)" if is_cloud else "C段深度挖掘"
                        elif is_cloud:
                            status_str = "☁️ 云端已保活 (等待订阅下发)"
                            reason_str = "☁️ 云端已保活 (等待订阅下发)"
                        elif ep_val:
                            # 能够解析出物理端点，赋予独立端点优质精选身份
                            status_str = "⭐ 优质精选 (待下发/独立端点)"
                            reason_str = f"{off_reason} (独立端点)" if off_reason and off_reason != "优质精选" else "优质独立端点"
                        else:
                            status_str = "⚠️ 当前订阅缺失(Endpoint不存在)"
                            reason_str = f"{off_reason} (当前订阅缺失)" if off_reason and off_reason != "优质精选" else "当前订阅缺失(Endpoint不存在)"

                        d_val = self.state.node_delays.get(fav_name, self.state.node_delays.get(ep_key, None))
                        d_str = f"{d_val} ms" if (d_val is not None and d_val < 99999) else "-"
                        s_val = self.state.node_speeds.get(fav_name, self.state.node_speeds.get(ep_key, None))
                        s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else "-"

                        ep_disp, name_disp = self._format_node_row_names(fav_name, ep_val, cloud_eps)

                        colo_c = colo_str if (colo_str and colo_str != "-") else "JP"
                        if not colo_c or colo_c == "-":
                            colo_c = "亚洲"
                        spd_num = s_val if (s_val is not None and s_val > 0) else 0.0
                        reason_val = self.state.fav_reasons.get(fav_name, self.state.fav_reasons.get(ep_val, ""))

                        if spd_num and spd_num > 0.1:
                            uniform_name = f"{colo_c} {spd_num:.2f} MB/s"
                        elif is_c_miner or "C段" in reason_val:
                            uniform_name = f"{colo_c} [C段挖掘]"
                        else:
                            uniform_name = colo_c

                        # 节点名称显示规则：有下行速度优先显示速度，其余按清洗后的云端备注或标准名显示，绝无延迟毫秒
                        if spd_num and spd_num > 0.1:
                            name_disp = uniform_name
                        elif ep_disp in cloud_eps:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(cloud_eps[ep_disp]))
                        elif ep_val and ep_val in cloud_eps:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(cloud_eps[ep_val]))
                        elif ":" in ep_disp and ep_disp.split(":")[0] in cloud_eps:
                            name_disp = re.sub(r"\s+\d+ms$", "", str(cloud_eps[ep_disp.split(":")[0]]))
                        else:
                            name_disp = uniform_name

                        row = {
                            "status": status_str,
                            "colo": colo_str,
                            "colo_hist": colo_hist_str,
                            "reason": reason_str,
                            "入选/拉黑原因": reason_str,
                            "delay": d_str,
                            "avg_delay": cur_avg_str,
                            "delay_hist": "-",
                            "hist_avg": hist_avg_str,
                            "speed": s_str,
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": fav_name or ep_val,
                        }

                        rows.append(row)
                return rows

            elif tab_type == "delay_black":
                rows = []
                seen_d_eps = set()
                # 订阅内的延迟黑名单
                for name in self.state.all_nodes:
                    ep_val = self._get_ep(name)
                    c_val = self.state.node_colo.get(ep_val, self.state.node_colo.get(name, "-"))
                    is_asian = is_asian_node(name, colo=c_val)
                    is_d_black = (not is_asian) or (name in self.state.local_blacklist) or (ep_val and ep_val in self.state.local_blacklist)
                    if is_d_black:
                        ep_key = ep_val if ep_val else name
                        if ep_key in seen_d_eps:
                            continue
                        seen_d_eps.add(ep_key)

                        d_val = self.state.node_delays.get(name, None)
                        if d_val is None:
                            d_str = "已跳过"
                        elif d_val >= 99999:
                            d_str = "超时 / 失败"
                        else:
                            d_str = f"{d_val} ms"

                        colo_str = self.state.node_colo.get(ep_val, self.state.node_colo.get(name, "-"))
                        colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(ep_val, self.state.node_colo_history.get(name, [])), now, node_name=name)[3]
                        cur_avg_str, hist_avg_str = compute_delay_stats(name, ep_val, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        delay_hist_str = self._format_hist(self.state.node_history.get(name, []))
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(name, []))
                        reason_str = self.state.blacklist_reasons.get(name, self.state.blacklist_reasons.get(ep_val, "非亚洲节点 (自动过滤)" if not is_asian else "延迟淘汰"))

                        ts = self.state.blacklist_timestamps.get(name, self.state.blacklist_timestamps.get(ep_val, 0.0))
                        ep_disp, name_disp = self._format_node_row_names(name, ep_val, self.state.cloud_endpoints)

                        rows.append({
                            "status": "🚫 延迟黑名单",
                            "colo": colo_str,
                            "colo_hist": colo_hist_str,
                            "reason": reason_str,
                            "delay": d_str,
                            "avg_delay": cur_avg_str,
                            "delay_hist": delay_hist_str,
                            "hist_avg": hist_avg_str,
                            "speed": "-",
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": name or ep_val,
                            "_ts": ts,
                        })

                # 离线延迟黑名单
                for b_name in self.state.local_blacklist:
                    if b_name not in self.state.all_nodes:
                        b_ep = self._get_ep(b_name)
                        ep_key = b_ep if b_ep else b_name
                        if ep_key in seen_d_eps:
                            continue
                        seen_d_eps.add(ep_key)

                        cur_avg_str, hist_avg_str = compute_delay_stats(b_name, b_ep, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(b_name, []))
                        b_reason = self.state.blacklist_reasons.get(b_name, self.state.blacklist_reasons.get(b_ep, "历史黑名单"))

                        ts = self.state.blacklist_timestamps.get(b_name, self.state.blacklist_timestamps.get(b_ep, 0.0))
                        ep_disp, name_disp = self._format_node_row_names(b_name, b_ep, self.state.cloud_endpoints)

                        rows.append({
                            "status": "🚫 当前订阅缺失(Endpoint不存在)",
                            "colo": "-",
                            "colo_hist": "-",
                            "reason": f"{b_reason} (历史黑名单)",
                            "delay": "已跳过",
                            "avg_delay": cur_avg_str,
                            "delay_hist": "-",
                            "hist_avg": hist_avg_str,
                            "speed": "-",
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": b_name or b_ep,
                            "_ts": ts,
                        })

                rows.sort(key=lambda x: x.get("_ts", 0.0), reverse=True)
                return rows

            elif tab_type == "speed_black":
                rows = []
                seen_s_eps = set()
                # 订阅内的低速黑名单
                for name in self.state.all_nodes:
                    ep_val = self._get_ep(name)
                    c_val = self.state.node_colo.get(ep_val, self.state.node_colo.get(name, "-"))
                    is_asian = is_asian_node(name, colo=c_val)
                    is_d_black = (not is_asian) or (name in self.state.local_blacklist) or (ep_val and ep_val in self.state.local_blacklist)
                    is_s_black = not is_d_black and ((name in self.state.speed_blacklist) or (ep_val and ep_val in self.state.speed_blacklist))
                    if is_s_black:
                        ep_key = ep_val if ep_val else name
                        if ep_key in seen_s_eps:
                            continue
                        seen_s_eps.add(ep_key)

                        s_val = self.state.node_speeds.get(name, None)
                        s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else ("测速失败" if s_val is not None else "-")
                        colo_str = self.state.node_colo.get(ep_val, self.state.node_colo.get(name, "-"))
                        colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(ep_val, self.state.node_colo_history.get(name, [])), now, node_name=name)[3]
                        cur_avg_str, hist_avg_str = compute_delay_stats(name, ep_val, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        delay_hist_str = self._format_hist(self.state.node_history.get(name, []))
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(name, []))
                        reason_str = self.state.blacklist_reasons.get(name, self.state.blacklist_reasons.get(ep_val, "低速淘汰"))

                        ts = self.state.blacklist_timestamps.get(name, self.state.blacklist_timestamps.get(ep_val, 0.0))
                        ep_disp, name_disp = self._format_node_row_names(name, ep_val, self.state.cloud_endpoints)

                        rows.append({
                            "status": "🐌 低速黑名单",
                            "colo": colo_str,
                            "colo_hist": colo_hist_str,
                            "reason": reason_str,
                            "delay": "-",
                            "avg_delay": cur_avg_str,
                            "delay_hist": delay_hist_str,
                            "hist_avg": hist_avg_str,
                            "speed": s_str,
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": name or ep_val,
                            "_ts": ts,
                        })

                # 离线低速黑名单
                for s_name in self.state.speed_blacklist:
                    if s_name not in self.state.all_nodes:
                        s_ep = self._get_ep(s_name)
                        ep_key = s_ep if s_ep else s_name
                        if ep_key in seen_s_eps:
                            continue
                        seen_s_eps.add(ep_key)

                        cur_avg_str, hist_avg_str = compute_delay_stats(s_name, s_ep, node_history=self.state.node_history, node_delays=self.state.node_delays, node_delay_history=self.state.node_delay_history, get_node_endpoint_fn=self._get_ep)
                        speed_hist_str = self._format_speed_hist(self.state.node_speed_history.get(s_name, []))
                        s_reason = self.state.blacklist_reasons.get(s_name, self.state.blacklist_reasons.get(s_ep, "历史低速黑名单"))

                        ts = self.state.blacklist_timestamps.get(s_name, self.state.blacklist_timestamps.get(s_ep, 0.0))
                        ep_disp, name_disp = self._format_node_row_names(s_name, s_ep, self.state.cloud_endpoints)

                        rows.append({
                            "status": "🐌 当前订阅缺失(Endpoint不存在)",
                            "colo": "-",
                            "colo_hist": "-",
                            "reason": f"{s_reason} (历史低速黑名单)",
                            "delay": "-",
                            "avg_delay": cur_avg_str,
                            "delay_hist": "-",
                            "hist_avg": hist_avg_str,
                            "speed": "低速",
                            "speed_hist": speed_hist_str,
                            "endpoint": ep_disp,
                            "IP:端口": ep_disp,
                            "name": name_disp,
                            "节点名称": name_disp,
                            "raw_name": s_name or s_ep,
                            "_ts": ts,
                        })

                rows.sort(key=lambda x: x.get("_ts", 0.0), reverse=True)
                return rows

            elif tab_type == "verified":
                # VerifiedTableView (10 列)
                rows = []
                for ep, item in self.state.verified_nodes.items():
                    rem = item.get("remark", "")
                    d_val = item.get("delay", None)
                    s_val = item.get("speed", None)
                    c_val = item.get("colo")

                    # 清洗端点为严格纯 IP:Port，杜绝机场名错位在第一列
                    clean_ep = str(item.get("endpoint", ep)).strip()
                    if "#" in clean_ep:
                        clean_ep = clean_ep.split("#")[0].strip()
                    if not re.match(r"^[\w\.\-]+\:\d+$", clean_ep):
                        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", clean_ep)
                        if m:
                            clean_ep = m.group(1)

                    colo_str = c_val if (c_val and c_val != "-") else self.state.node_colo.get(clean_ep, self.state.node_colo.get(ep, "-"))

                    # 构建统一规范名 {Colo} {Speed} MB/s
                    colo_c = colo_str if (colo_str and colo_str != "-") else "JP"
                    if not colo_c or colo_c == "-":
                        colo_c = "亚洲"
                    spd_num = s_val if (s_val is not None and s_val > 0) else self.state.node_speeds.get(clean_ep, self.state.node_speeds.get(ep, 0.0))
                    d_num = d_val if (d_val is not None and d_val < 99999 and d_val > 0) else self.state.node_delays.get(clean_ep, self.state.node_delays.get(ep, 0))
                    ver_reason = item.get("reason", "")

                    if spd_num and spd_num > 0.1:
                        calc_uniform = f"{colo_c} {spd_num:.2f} MB/s"
                    elif "C段" in ver_reason:
                        if d_num and 0 < d_num < 99999:
                            calc_uniform = f"{colo_c} [C段挖掘] {d_num}ms"
                        else:
                            calc_uniform = f"{colo_c} [C段挖掘]"
                    else:
                        if d_num and 0 < d_num < 99999:
                            calc_uniform = f"{colo_c} {d_num}ms"
                        else:
                            calc_uniform = colo_c

                    # 优先获取用户云端专属规范名
                    cloud_rem = self.state.cloud_endpoints.get(clean_ep, "")
                    if not cloud_rem and ":" in clean_ep:
                        cloud_rem = self.state.cloud_endpoints.get(clean_ep.split(":")[0], "")
                    if not cloud_rem and rem and not rem.startswith("精选拉入"):
                        cloud_rem = rem

                    uniform_name = cloud_rem if cloud_rem else calc_uniform

                    # 物理端点追踪匹配当前订阅中的最新节点名
                    matched_name = current_endpoints.get(clean_ep, "")
                    if not matched_name and ":" in clean_ep:
                        matched_name = current_ip_map.get(clean_ep.split(":")[0], "")
                    if not matched_name:
                        ep_res = get_node_endpoint(clean_ep, self.state.node_details)
                        if ep_res:
                            matched_name = current_endpoints.get(ep_res, "")

                    # 节点名称优先显示用户云端专属规范名，彻底去牛皮癣化覆盖原机场名
                    if matched_name and matched_name != "当前订阅缺失(Endpoint不存在)":
                        display_name = uniform_name
                    else:
                        display_name = f"{uniform_name} (☁️云端已存)"

                    colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(clean_ep, self.state.node_colo_history.get(ep, [])), now, node_name=display_name)[3]
                    d_str = f"{d_val} ms" if (d_val is not None and d_val < 99999) else ("超时" if d_val == 99999 else "-")
                    s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else "-"

                    first_seen = item.get("first_seen", now)
                    hours_alive = round((now - first_seen) / 3600.0, 1)
                    time_str = f"已存活 {hours_alive}h"

                    passes = item.get("passes", item.get("pass_count", 0))
                    fails = item.get("fails", 0)
                    stats_str = f"达标 {passes} 次 / 失败 {fails} 次"

                    reason_str = item.get("reason", "")
                    if not reason_str:
                        if passes > 1:
                            reason_str = f"考核留任 (达标{passes}次/{hours_alive}h)"
                        else:
                            reason_str = "优选初筛建档 (第1次达标)"

                    rows.append({
                        "endpoint": clean_ep,
                        "IP:端口": clean_ep,
                        "name": display_name,
                        "节点名称": display_name,
                        "colo": colo_str,
                        "colo_hist": colo_hist_str,
                        "reason": reason_str,
                        "remark": rem if (rem and not rem.startswith("精选拉入")) else display_name,
                        "delay": d_str,
                        "speed": s_str,
                        "time": time_str,
                        "stats": stats_str,
                        "match": display_name,
                    })
                return rows

            elif tab_type == "stars":
                # StarsTableView (8 列)
                rows = []
                for item in self.state.stars_nodes:
                    ep = item.get("endpoint", "")
                    rem = item.get("remark", "")
                    d_val = item.get("delay", None)
                    s_val = item.get("speed", None)
                    c_val = item.get("colo")
                    colo_str = c_val if (c_val and c_val != "-") else self.state.node_colo.get(ep, "-")

                    # 物理端点追踪匹配当前订阅中的最新节点名
                    matched_name = current_endpoints.get(ep, "")
                    if not matched_name and ":" in ep:
                        matched_name = current_ip_map.get(ep.split(":")[0], "")
                    if not matched_name:
                        ep_res = get_node_endpoint(ep, self.state.node_details)
                        if ep_res:
                            matched_name = current_endpoints.get(ep_res, "")

                    # 终极免死金牌：如果在当前订阅中缺失，但在云端映射中已存在，则正常显示云端命名并标注云端保活
                    if not matched_name or matched_name == "当前订阅缺失(Endpoint不存在)":
                        cloud_rem = self.state.cloud_endpoints.get(ep, "")
                        if not cloud_rem and ":" in ep:
                            cloud_rem = self.state.cloud_endpoints.get(ep.split(":")[0], "")

                        if cloud_rem:
                            matched_name = f"{cloud_rem} (☁️云端已存)"
                        else:
                            matched_name = "当前订阅缺失(Endpoint不存在)"

                    colo_hist_str = analyze_colo_stats(self.state.node_colo_history.get(ep, []), now, node_name=matched_name)[3]
                    d_str = f"{d_val} ms" if (d_val is not None and d_val < 99999) else ("超时" if d_val == 99999 else "-")
                    s_str = f"{s_val:.2f} MB/s" if (s_val is not None and s_val >= 0) else "-"

                    reason_str = item.get("reason", "")
                    if not reason_str:
                        if "加冕" in rem:
                            reason_str = "沉淀池提前加冕"
                        elif "手动" in rem or "录入" in rem:
                            reason_str = "手动录入典藏"
                        else:
                            reason_str = "考核通关晋升 (长效极稳)"

                    rows.append({
                        "endpoint": ep,
                        "colo": colo_str,
                        "colo_hist": colo_hist_str,
                        "reason": reason_str,
                        "remark": rem,
                        "delay": d_str,
                        "speed": s_str,
                        "match": matched_name,
                    })
                return rows

            return []

    # ==================== 业务流转与节点操作 ====================

    def get_node_endpoint(self, n: str) -> str:
        """
        公开接口：获取节点的物理端点 (IP:Port)
        """
        return self._get_ep(n)

    def test_nodes_delay(self, nodes: list[str], callback=None):
        """
        并发快速测试指定节点列表的实时延迟
        """
        if not nodes:
            return
        cfg = self.load_config()
        test_url = cfg.get("test_url", "http://www.msftconnecttest.com/connecttest.txt")
        timeout_ms = int(cfg.get("test_timeout", 1500)) if str(cfg.get("test_timeout", "")).isdigit() else 1500

        # 如果传入的是端点，尝试解析出实际节点名称
        resolved_nodes = []
        reverse_map = {}
        with self.state.lock:
            for item in self.state.all_nodes:
                ep = self._get_ep(item)
                if ep:
                    reverse_map[ep] = item

        for item in nodes:
            if item in self.state.all_nodes:
                resolved_nodes.append(item)
            elif item in reverse_map:
                resolved_nodes.append(reverse_map[item])
            else:
                resolved_nodes.append(item)

        def _worker():
            self.log(f"⚡ 开始测试 {len(resolved_nodes)} 个选定节点的延迟...")
            results = {}

            def _query(node_name):
                try:
                    d = self.clash_client.query_proxy_delay(node_name, test_url, timeout_ms=timeout_ms)
                    return node_name, d
                except Exception:
                    return node_name, 99999

            with ThreadPoolExecutor(max_workers=min(16, max(1, len(resolved_nodes)))) as executor:
                for n_name, d_val in executor.map(_query, resolved_nodes):
                    results[n_name] = d_val

            with self.state.lock:
                for n_name, d_val in results.items():
                    if d_val > 0:
                        self.state.node_delays[n_name] = d_val
                        hist = self.state.node_history.setdefault(n_name, [])
                        hist.append(d_val)
                        self.state.node_history[n_name] = hist[-30:]
                        ep = self._get_ep(n_name)
                        if ep:
                            self.state.node_delays[ep] = d_val

            self.data_changed.emit()
            self.log(f"✅ {len(resolved_nodes)} 个选定节点延迟测试完成！")
            if callback:
                callback(results)

        threading.Thread(target=_worker, daemon=True).start()

    def test_nodes_colo(self, nodes: list[str], callback=None):
        """
        并发检测指定节点列表的实时物理机房 (Colo) 与严格防漂移审查
        """
        from services.probe_service import get_cf_colo_raw
        from services.colo_service import record_colo_sample
        from services.pool_service import purge_invalid_and_blacklisted_from_all_pools

        if not nodes:
            return

        targets = []
        with self.state.lock:
            for item in nodes:
                n_name = item
                ep = self._get_ep(item)
                if not ep and ":" in item:
                    ep = item
                targets.append((n_name, ep))

        def _worker():
            self.log(f"🌍 开始并发测试选中的 {len(targets)} 个节点的物理机房(Colo)...")

            def _probe(item):
                n_name, n_ep = item
                if n_ep and ":" in n_ep:
                    raw_ip, raw_port = n_ep.rsplit(":", 1)
                    c_code, c_disp = get_cf_colo_raw(raw_ip, raw_port, timeout=1.8)
                    with self.state.lock:
                        record_colo_sample(self.state.node_colo_history, n_name, n_ep, c_code, c_disp)
                        if n_name:
                            self.state.node_colo[n_name] = c_disp
                        if n_ep:
                            self.state.node_colo[n_ep] = c_disp

            with ThreadPoolExecutor(max_workers=min(15, max(1, len(targets)))) as ex:
                list(ex.map(_probe, targets))

            # 严格防漂移审查
            drift_count = 0
            now_t = time.time()
            with self.state.lock:
                for n_name, n_ep in targets:
                    colo_hist = self.state.node_colo_history.get(n_name, self.state.node_colo_history.get(n_ep, []))
                    if colo_hist:
                        _, _, has_drift, drift_disp = analyze_colo_stats(colo_hist, now_t, node_name=n_name)
                        if has_drift:
                            reason = f"机房漂移 ({drift_disp})"
                            if n_name:
                                self.state.local_blacklist.add(n_name)
                                self.state.favorites.discard(n_name)
                                self.state.blacklist_reasons[n_name] = reason
                            if n_ep:
                                self.state.local_blacklist.add(n_ep)
                                self.state.blacklist_reasons[n_ep] = reason
                                if n_ep in self.state.verified_nodes:
                                    del self.state.verified_nodes[n_ep]
                            drift_count += 1
                            self.log(f"【Colo测定-漂移淘汰】{n_name or n_ep} 发生机房漂移 ({drift_disp})，直接拉黑并清除！")

                if drift_count > 0:
                    purge_invalid_and_blacklisted_from_all_pools(
                        self.state.favorites,
                        self.state.verified_nodes,
                        self.state.stars_nodes,
                        self.state.local_blacklist,
                        self.state.speed_blacklist,
                        self._get_ep,
                    )
                    self.trigger_verge_reload()

            self.save_config(self.get_state_snapshot())
            self.data_changed.emit()
            self.log(f"✅ 选中节点 Colo 检测完成，共测定 {len(targets)} 个节点，漂移淘汰 {drift_count} 个。")
            if callback:
                callback(len(targets), drift_count)

        threading.Thread(target=_worker, daemon=True).start()

    def mine_c_subnet(self, selected_nodes=None, parent=None):
        """
        基于选中的节点/端点打开 C 段全量高并发深度挖掘对话框
        """
        seed_ip = "172.64.229.1"
        seed_port = 443

        if selected_nodes:
            if isinstance(selected_nodes, (list, tuple, set)):
                target = next(iter(selected_nodes), "")
            else:
                target = str(selected_nodes)

            ep = self._get_ep(target) or str(target)
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?", ep)
            if not m:
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?", str(target))
            if m:
                seed_ip = m.group(1)
                if m.group(2):
                    seed_port = int(m.group(2))

        # 正常打开对话框 (即使无选中也打开默认对话框)
        try:
            from gui_fluent.widgets.c_miner_dialog import CSegmentMinerDialog
            win = parent or (self.parent() if hasattr(self, "parent") else None)
            if win is None:
                if "PyQt5" in sys.modules:
                    from PyQt5.QtWidgets import QApplication
                else:
                    from PyQt6.QtWidgets import QApplication
                win = QApplication.activeWindow()

            dlg = CSegmentMinerDialog(seed_ip=seed_ip, seed_port=seed_port, controller=self, parent=win)
            dlg.exec()
        except Exception as e:
            self.log(f"❌ 启动 C 段挖掘对话框失败: {e}")

    def remove_nodes_from_favorites(self, nodes: list[str]):
        """
        将指定节点从精选池中移出
        """
        if not nodes:
            return
        with self.state.lock:
            for n in nodes:
                self.state.favorites.discard(n)
                self.state.fav_reasons.pop(n, None)
                ep = self._get_ep(n) or str(n)
                if ep:
                    self.state.favorites.discard(ep)
                    self.state.fav_reasons.pop(ep, None)
                    # 同步从云端缓存中剔除，防止被逆向复活
                    self.state.auto_endpoints.discard(ep)
                    self.state.cloud_endpoints.pop(ep, None)
                    if ":" in ep:
                        self.state.cloud_endpoints.pop(ep.split(":")[0], None)
                    for f in list(self.state.favorites):
                        if self._get_ep(f) == ep:
                            self.state.favorites.discard(f)
                            self.state.fav_reasons.pop(f, None)
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🗑️ 已从精选池移出 {len(nodes)} 个节点")
        self.sync_favorites_to_cloud()

    def clear_all_favorites(self):
        """
        清空优质精选池
        """
        with self.state.lock:
            self.state.favorites.clear()
            self.state.fav_reasons.clear()
            self.state.auto_endpoints.clear()
            self.state.cloud_endpoints.clear()
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log("🗑️ 优质精选池已全部清空。")
        self.sync_favorites_to_cloud()

    def move_nodes_to_favorites(self, nodes: list[str]):
        """
        将指定节点加入优质精选池，并同步清除对应物理端点 (IP:Port) 的所有衍生黑名单
        """
        if not nodes:
            return
        with self.state.lock:
            for n in nodes:
                ep = self._get_ep(n)
                self.state.favorites.add(n)
                self.state.fav_reasons[n] = "手动设为优质"
                self.state.local_blacklist.discard(n)
                self.state.speed_blacklist.discard(n)
                self.state.blacklist_reasons.pop(n, None)
                if ep:
                    self.state.local_blacklist.discard(ep)
                    self.state.speed_blacklist.discard(ep)
                    self.state.blacklist_reasons.pop(ep, None)
                    # 清除共享相同 IP:Port 的衍生命名节点
                    for b in list(self.state.local_blacklist):
                        if self._get_ep(b) == ep:
                            self.state.local_blacklist.discard(b)
                            self.state.blacklist_reasons.pop(b, None)
                    for s in list(self.state.speed_blacklist):
                        if self._get_ep(s) == ep:
                            self.state.speed_blacklist.discard(s)
                            self.state.blacklist_reasons.pop(s, None)

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"⭐ 已手动将 {len(nodes)} 个节点加入优质精选池 (并同步清除同端点黑名单)")

    def promote_nodes_to_stars(self, nodes: list[str]):
        """
        将指定节点晋升至典藏管理池
        """
        if not nodes:
            return
        added_count = 0
        with self.state.lock:
            existing_eps = {s.get("endpoint", "") for s in self.state.stars_nodes}
            for n in nodes:
                ep = self._get_ep(n) or n
                if ep not in existing_eps:
                    colo = self.state.node_colo.get(ep, self.state.node_colo.get(n, "-"))
                    d_val = self.state.node_delays.get(n, self.state.node_delays.get(ep, None))
                    s_val = self.state.node_speeds.get(n, self.state.node_speeds.get(ep, None))
                    self.state.stars_nodes.append({
                        "endpoint": ep,
                        "remark": f"手动晋升 ({n})",
                        "reason": "手动晋升典藏",
                        "colo": colo,
                        "delay": d_val,
                        "speed": s_val,
                    })
                    existing_eps.add(ep)
                    added_count += 1
                self.state.favorites.add(n)
                if ep:
                    self.state.local_blacklist.discard(ep)
                    self.state.speed_blacklist.discard(ep)
                    self.state.blacklist_reasons.pop(ep, None)
                    for b in list(self.state.local_blacklist):
                        if self._get_ep(b) == ep:
                            self.state.local_blacklist.discard(b)
                            self.state.blacklist_reasons.pop(b, None)
                    for s in list(self.state.speed_blacklist):
                        if self._get_ep(s) == ep:
                            self.state.speed_blacklist.discard(s)
                            self.state.blacklist_reasons.pop(s, None)

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🏆 已将 {len(nodes)} 个节点晋升至典藏管理池 (新增 {added_count} 个独立端点)")

    def blacklist_nodes(self, nodes: list[str], reason: str = "手动拉黑", bl_type: str = "delay"):
        """
        将指定节点加入延迟或低速黑名单，同时拉黑共享相同 IP:Port 端点的所有衍生节点，并从精选池与孵化池彻底移出
        """
        if not nodes:
            return
        now_t = time.time()
        with self.state.lock:
            if not hasattr(self.state, "blacklist_timestamps"):
                self.state.blacklist_timestamps = {}

            for n in nodes:
                ep = self._get_ep(n)
                target_names = {n}
                if ep:
                    for item_name in list(self.state.all_nodes) + list(self.state.favorites):
                        if self._get_ep(item_name) == ep:
                            target_names.add(item_name)

                for t_name in target_names:
                    if bl_type == "speed":
                        self.state.speed_blacklist.add(t_name)
                    else:
                        self.state.local_blacklist.add(t_name)
                    self.state.blacklist_reasons[t_name] = reason
                    self.state.blacklist_timestamps[t_name] = now_t
                    self.state.favorites.discard(t_name)

                if ep:
                    if bl_type == "speed":
                        self.state.speed_blacklist.add(ep)
                    else:
                        self.state.local_blacklist.add(ep)
                    self.state.blacklist_reasons[ep] = reason
                    self.state.blacklist_timestamps[ep] = now_t
                    self.state.favorites.discard(ep)
                    for f in list(self.state.favorites):
                        if self._get_ep(f) == ep:
                            self.state.favorites.discard(f)
                    if ep in self.state.verified_nodes:
                        del self.state.verified_nodes[ep]

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        tag = "低速黑名单" if bl_type == "speed" else "延迟黑名单"
        self.log(f"🚫 已手动将 {len(nodes)} 个节点加入{tag} (原因: {reason})，并关联处理了同端点衍生节点")

    def remove_nodes_from_blacklist(self, nodes: list[str]):
        """
        将指定节点从黑名单中移出，恢复至活跃池。
        同时确保清除了共享相同 IP:Port 物理端点的所有衍生命名节点。
        """
        if not nodes:
            return
        with self.state.lock:
            ts_map = getattr(self.state, "blacklist_timestamps", {})
            for n in nodes:
                ep = self._get_ep(n)
                self.state.local_blacklist.discard(n)
                self.state.speed_blacklist.discard(n)
                self.state.blacklist_reasons.pop(n, None)
                ts_map.pop(n, None)
                if ep:
                    self.state.local_blacklist.discard(ep)
                    self.state.speed_blacklist.discard(ep)
                    self.state.blacklist_reasons.pop(ep, None)
                    ts_map.pop(ep, None)
                    # 清除共享相同 IP:Port 的所有衍生命名节点
                    for b in list(self.state.local_blacklist):
                        if self._get_ep(b) == ep:
                            self.state.local_blacklist.discard(b)
                            self.state.blacklist_reasons.pop(b, None)
                            ts_map.pop(b, None)
                    for s in list(self.state.speed_blacklist):
                        if self._get_ep(s) == ep:
                            self.state.speed_blacklist.discard(s)
                            self.state.blacklist_reasons.pop(s, None)
                            ts_map.pop(s, None)

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"↩ 已将 {len(nodes)} 个节点及其同端点别名从黑名单移出，恢复至活跃待测池")

        # 移出黑名单的节点自动上传至云端待测池 (/pending.txt)，确保全量优选能再次纳测
        unblacklisted_eps = []
        for n in nodes:
            ep = self._get_ep(n)
            if ep and ep != "127.0.0.1:443":
                unblacklisted_eps.append((ep, f"{self.state.node_colo.get(n, '亚洲')} [解黑恢复待测]"))
        if unblacklisted_eps:
            import threading
            threading.Thread(
                target=self.append_pending_endpoints_to_cloud,
                args=(unblacklisted_eps,),
                daemon=True
            ).start()

    def clear_all_blacklists(self):
        """
        一键清空所有延迟与低速黑名单
        """
        with self.state.lock:
            d_count = len(self.state.local_blacklist)
            s_count = len(self.state.speed_blacklist)
            self.state.local_blacklist.clear()
            self.state.speed_blacklist.clear()
            self.state.blacklist_reasons.clear()
            if hasattr(self.state, "blacklist_timestamps"):
                self.state.blacklist_timestamps.clear()

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🧹 已清空所有黑名单记录 (清理延迟黑名单 {d_count} 项，低速黑名单 {s_count} 项)")

    def trigger_verge_reload(self):
        """
        生成 Script.js 策略组配置并触发 Win32 系统热键刷新 Verge
        """
        return self.reload_verge_with_fission(None)

    def reload_verge_with_fission(self, fission_proxies=None):
        """
        生成包含临时裂变节点的 Script.js 并触发热更 (fission_proxies=None 时物理恢复纯净配置)
        """
        with self.state.lock:
            favs = set(self.state.favorites)
            stars = list(self.state.stars_nodes)
            all_n = list(self.state.all_nodes)
            n_det = dict(self.state.node_details)

        cfg = self.load_config() or {}
        g_inter = str(cfg.get("group_interval", "300"))
        g_tol = str(cfg.get("group_tolerance", "20"))
        s_inter = str(cfg.get("star_group_interval", "300"))
        s_tol = str(cfg.get("star_group_tolerance", "20"))

        script_code, p_tokens, s_tokens = build_script_js(
            favorites=favs,
            stars_nodes=stars,
            all_nodes=all_n,
            node_details=n_det,
            group_interval=g_inter,
            group_tolerance=g_tol,
            star_group_interval=s_inter,
            star_group_tolerance=s_tol,
            is_asian_node_fn=is_asian_node,
            get_node_endpoint_fn=self._get_ep,
            fission_proxies=fission_proxies,
            cloud_endpoints=getattr(self.state, "cloud_endpoints", None),
            node_colo=getattr(self.state, "node_colo", None),
        )
        ok, res = write_script_js(script_code)
        if ok:
            fiss_cnt = len(fission_proxies) if fission_proxies else 0
            if fiss_cnt > 0:
                self.log(f"⚡ Script.js 临时裂变注入成功 (裂变节点: {fiss_cnt} 个，优选: {len(p_tokens)} 个)")
            else:
                self.log(f"✅ Script.js 纯净策略组恢复成功 (优选: {len(p_tokens)} 个，典藏: {len(s_tokens)} 个)")
        else:
            self.log(f"⚠️ Script.js 写入失败: {res}")

        hk_ok, hk_msg = trigger_verge_reactivate_hotkey()
        if hk_ok:
            self.log(f"⚡ 热键通知成功: {hk_msg}")
        else:
            self.log(f"⚠️ 热键触发反馈: {hk_msg}")

        # 双引擎保障：直接同步 runtime clash-verge.yaml 并热载内核
        try:
            from services.script_generator import sync_runtime_clash_yaml_and_reload
            sync_runtime_clash_yaml_and_reload(fission_proxies=fission_proxies)
        except Exception:
            pass

        return hk_ok

    # ==================== TopBar 顶部工具栏业务 ====================

    def update_remote_subscription_sync(self, yaml_filename: str = None) -> tuple[bool, str]:
        """
        同步在线拉取并更新指定（或当前）订阅 YAML 文件，更新后重新解析加载节点
        """
        from config.settings import BASE_DIR
        from services.subscription_service import update_remote_subscription

        target_name = yaml_filename or getattr(self.state, "active_profile", "")
        if not target_name:
            profiles = self.get_all_yaml_profiles()
            target_name = profiles[0] if profiles else ""

        if not target_name:
            msg = "未定位到可更新的订阅配置文件！"
            self.log(f"⚠️ {msg}")
            return False, msg

        target_path = os.path.join(BASE_DIR, target_name)
        mixed_port = self.clash_client.get_mixed_port(default=7897)

        self.log(f"🔄 开始在线拉取更新订阅: {target_name}...")
        try:
            ok, msg, changed = update_remote_subscription(target_path, mixed_port=mixed_port)
            if ok:
                self.log(f"✅ 订阅更新成功: {msg}")
                self.load_nodes_from_profile(target_name)
                self.data_changed.emit()
                return True, msg
            else:
                self.log(f"⚠️ 订阅更新失败: {msg}")
                return False, msg
        except Exception as e:
            err_msg = f"更新订阅异常: {e}"
            self.log(f"❌ {err_msg}")
            return False, err_msg

    def update_current_subscription(self, yaml_filename: str = None, callback=None):
        """
        在线拉取并更新指定（或当前）订阅 YAML 文件，并自动执行 Script.js 写入与热更探测闭环（异步后台线程）
        """
        def _worker():
            ok, msg = self.update_remote_subscription_sync(yaml_filename)
            if ok:
                self.log("⚡ 订阅拉取完成，正在重新生成 Script.js 策略组并触发热更...")
                self.generate_script_and_reload()
                time.sleep(0.5)
                loaded_ok, loaded_msg = self.clash_client.wait_for_kernel_reload(
                    self.state.all_nodes, max_wait_sec=10
                )
                self.log(f"内核装载探测: {loaded_msg}")
            if callback:
                callback(ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    def test_current_page_colo(self, page_key: str = "active", callback=None):
        """
        并发检测指定页面中所有节点的实时物理机房 (Colo) 与严格防漂移审查
        """
        from services.probe_service import get_cf_colo_raw
        from services.colo_service import record_colo_sample
        from services.pool_service import purge_invalid_and_blacklisted_from_all_pools

        rows = self.get_table_rows(page_key)
        if not rows:
            self.log(f"⚠️ 当前页面 [{page_key}] 暂无节点可供测试 Colo")
            if callback:
                callback(0, 0)
            return

        targets = []
        for r in rows:
            name = r.get("name") or r.get("matched_name", "")
            ep = r.get("endpoint", "")
            if not ep and name:
                ep = self._get_ep(name)
            targets.append((name, ep))

        def _worker():
            self.log(f"🌍 开始并发测试当前页面 [{page_key}] 共 {len(targets)} 个节点的物理机房(Colo)...")

            def _probe(item):
                n_name, n_ep = item
                if n_ep and ":" in n_ep:
                    raw_ip, raw_port = n_ep.rsplit(":", 1)
                    c_code, c_disp = get_cf_colo_raw(raw_ip, raw_port, timeout=1.8)
                    with self.state.lock:
                        record_colo_sample(self.state.node_colo_history, n_name, n_ep, c_code, c_disp)
                        if n_name:
                            self.state.node_colo[n_name] = c_disp
                        if n_ep:
                            self.state.node_colo[n_ep] = c_disp

            with ThreadPoolExecutor(max_workers=15) as ex:
                list(ex.map(_probe, targets))

            # 严格防漂移审查
            drift_count = 0
            now_t = time.time()
            with self.state.lock:
                for n_name, n_ep in targets:
                    colo_hist = self.state.node_colo_history.get(n_name, self.state.node_colo_history.get(n_ep, []))
                    if colo_hist:
                        _, _, has_drift, drift_disp = analyze_colo_stats(colo_hist, now_t, node_name=n_name)
                        if has_drift:
                            reason = f"机房漂移 ({drift_disp})"
                            if n_name:
                                self.state.local_blacklist.add(n_name)
                                self.state.favorites.discard(n_name)
                                self.state.blacklist_reasons[n_name] = reason
                            if n_ep:
                                self.state.local_blacklist.add(n_ep)
                                self.state.blacklist_reasons[n_ep] = reason
                                if n_ep in self.state.verified_nodes:
                                    del self.state.verified_nodes[n_ep]
                            drift_count += 1
                            self.log(f"【页面Colo测定-漂移淘汰】{n_name or n_ep} 发生机房漂移 ({drift_disp})，直接拉黑并清除！")

                if drift_count > 0:
                    purge_invalid_and_blacklisted_from_all_pools(
                        self.state.favorites,
                        self.state.verified_nodes,
                        self.state.stars_nodes,
                        self.state.local_blacklist,
                        self.state.speed_blacklist,
                        self._get_ep,
                    )
                    self.trigger_verge_reload()

            self.save_config(self.get_state_snapshot())
            self.data_changed.emit()
            self.log(f"✅ 当前页面 Colo 检测完成，共测定 {len(targets)} 个节点，漂移淘汰 {drift_count} 个。")
            if callback:
                callback(len(targets), drift_count)

        threading.Thread(target=_worker, daemon=True).start()

    def clear_current_page_colo(self, page_key: str = "active") -> int:
        """
        清空指定页面中所有节点的实时 Colo 及历史记录
        """
        rows = self.get_table_rows(page_key)
        if not rows:
            return 0
        cleared_count = 0
        with self.state.lock:
            for r in rows:
                name = r.get("name") or r.get("matched_name", "")
                ep = r.get("endpoint", "")
                if not ep and name:
                    ep = self._get_ep(name)
                keys_to_clean = [name, ep]
                if ep and ":" in ep:
                    keys_to_clean.append(ep.split(":")[0])
                for k in keys_to_clean:
                    if k:
                        self.state.node_colo.pop(k, None)
                        self.state.node_colo_history.pop(k, None)
                if ep in self.state.verified_nodes:
                    self.state.verified_nodes[ep]["colo"] = "-"
                for s in self.state.stars_nodes:
                    if s.get("endpoint") == ep or (name and s.get("matched_name") == name):
                        s["colo"] = "-"
                cleared_count += 1

        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🧹 已清空页面 [{page_key}] 共 {cleared_count} 个节点的机房 (Colo) 记录与时序历史")
        return cleared_count

    def sync_kernel_delays(self) -> bool:
        """
        从内核 /proxies 同步所有节点延迟与时延历史
        """
        data = self.clash_client.call_api("/proxies")
        if not data or "proxies" not in data:
            self.log("⚠️ 无法从 Clash 内核获取代理节点列表")
            return False

        proxies = data["proxies"]
        updated = 0
        with self.state.lock:
            for name, info in proxies.items():
                history = info.get("history", [])
                if history:
                    delays = [h.get("delay", 0) for h in history if isinstance(h.get("delay"), int)]
                    normalized = [d if d > 0 else 99999 for d in delays]
                    if normalized:
                        self.state.node_history[name] = normalized[-4:]
                        self.state.node_delays[name] = normalized[-1]
                        updated += 1
        if updated > 0:
            self.data_changed.emit()
            self.log(f"🔄 已成功从 Clash 内核同步 {updated} 个节点的实时延迟与历史记录")
            return True
        else:
            self.log("ℹ️ 内核中暂无可同步的节点延迟历史")
            return False

    def clear_speed_records(self, silent=False):
        """
        清空所有测速数据与延迟趋势记录
        """
        with self.state.lock:
            self.state.node_delays.clear()
            self.state.node_history.clear()
            self.state.node_speeds.clear()

        threading.Thread(
            target=lambda: self.clash_client.call_api("/configs?force=true", method="PUT", data={"path": ""}),
            daemon=True,
        ).start()

        self.data_changed.emit()
        self.log("🗑️ 所有节点测速记录与延迟轨迹已全部重置归零。")

    # ==================== 优质精选池专属业务 ====================

    def clean_stale_favorites(self):
        """
        清理精选池中已过期（不在当前订阅中）或已在黑名单中的失效节点
        """
        with self.state.lock:
            stale = [
                n for n in self.state.favorites
                if n not in self.state.all_nodes
                or n in self.state.local_blacklist
                or n in self.state.speed_blacklist
            ]
            for n in stale:
                self.state.favorites.discard(n)
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🧹 已清理 {len(stale)} 个过期/失效/已拉黑的精选节点")

    def sync_favorites_to_active(self):
        """
        将精选池节点名称与当前活跃订阅进行双向对齐映射
        """
        from services.pool_service import align_favorites_with_current_subscription
        from services.subscription_service import resolve_node_to_current

        with self.state.lock:
            migrated = align_favorites_with_current_subscription(
                self.state.favorites,
                self.state.all_nodes,
                lambda k: resolve_node_to_current(k, self.state.all_nodes, self.state.node_details),
            )
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"⚡ 精选池已与当前活跃订阅完成双向对齐映射 (迁移更名: {migrated} 个)！")

    # ==================== Cloudflare Worker 同步与纯文本推送 ====================

    def get_cf_worker_config(self) -> tuple[bool, str, str]:
        """
        获取 Cloudflare Worker 配置: (enabled, url, token)
        """
        cfg = self.load_config() or {}
        enabled = bool(cfg.get("cf_worker_enabled", False))
        url = str(cfg.get("worker_url") or cfg.get("cf_worker_url", "https://cf-nodes.douyutvshow.workers.dev/")).strip()
        token = str(cfg.get("worker_token") or cfg.get("cf_worker_token", "MySecretToken2026")).strip()
        return enabled, url, token

    def fetch_cloud_text(self, subpath: str = "", base_url: str = None, token: str = None) -> tuple[bool, str]:
        """
        从 Cloudflare Worker 拉取指定子路径的纯文本内容。
        支持双通道回退（优先 Clash 代理，失败回退直连）。
        """
        cfg = self.load_config()
        b_url = (base_url or cfg.get("worker_url") or cfg.get("cf_worker_url", "")).rstrip("/")
        tok = token or cfg.get("worker_token") or cfg.get("cf_worker_token", "")

        if not b_url or not b_url.startswith("http"):
            return False, "Worker 网址无效"

        target_url = f"{b_url}{subpath}" if subpath else f"{b_url}/"
        mixed_port = self.clash_client.get_mixed_port(default=7897)

        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        proxy_handler = urllib.request.ProxyHandler({
            "http": f"http://127.0.0.1:{mixed_port}",
            "https": f"http://127.0.0.1:{mixed_port}",
        })
        proxy_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
        direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))

        headers = {
            "Authorization": f"Bearer {tok}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        }
        req = urllib.request.Request(target_url, headers=headers)

        last_err = ""
        for attempt in range(1, 4):
            for use_proxy, opener in [(True, proxy_opener), (False, direct_opener)]:
                try:
                    with opener.open(req, timeout=10) as resp:
                        if resp.status == 200:
                            content = resp.read().decode("utf-8", errors="ignore")
                            return True, content
                        last_err = f"Worker 返回状态码: {resp.status}"
                except urllib.error.HTTPError as ex:
                    if ex.code == 401:
                        return False, "认证失败(401)，请确认 AUTH_TOKEN 密钥！"
                    last_err = f"HTTP({ex.code}): {ex.reason}"
                except Exception as ex:
                    last_err = str(ex)
            time.sleep(0.5)

        return False, f"拉取失败: {last_err}"

    def push_cloud_text(self, subpath: str = "", text: str = "", base_url: str = None, token: str = None) -> tuple[bool, str]:
        """
        推送纯文本内容至 Cloudflare Worker（别名包装）
        """
        return self.push_text_to_cf_worker(text_payload=text, subpath=subpath, base_url=base_url, token=token)

    def fetch_cloud_endpoints_sync(self) -> dict[str, str]:
        """
        同步从 Cloudflare Worker 拉取 /auto.txt，并解析端点与专属备注映射字典。
        支持纯 IPv4:Port 以及 域名(FQDN):Port (如 saas.sin.fan:443)
        返回: { "Endpoint": "云端专属备注名", "Host": "云端专属备注名" }
        """
        ok, content = self.fetch_cloud_text("/auto.txt")
        cloud_map = {}
        if not ok or not content:
            self.log(f"⚠️ 未能从云端获取 auto.txt: {content if not ok else '内容为空'}")
            return cloud_map

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//") or line.startswith("⏳") or line.startswith("Error"):
                continue
            if "#" in line:
                parts = line.split("#", 1)
                ep_str = parts[0].strip()
                remark_str = parts[1].strip()
            else:
                parts = line.split(None, 1)
                ep_str = parts[0].strip()
                remark_str = parts[1].strip() if len(parts) > 1 else ""

            # 优先匹配规范的主机:端口 (支持 IPv4、IPv6及 FQDN 域名)
            m = re.match(r"^([\w\.\-]+):(\d{1,5})$", ep_str)
            if not m:
                # 兼容文本中嵌有 IPv4:Port 的情况
                m_ip = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?", ep_str)
                if m_ip:
                    ip = m_ip.group(1)
                    port = m_ip.group(2) if m_ip.group(2) else "443"
                    endpoint = f"{ip}:{port}"
                    host = ip
                else:
                    continue
            else:
                host = m.group(1)
                port = m.group(2)
                endpoint = f"{host}:{port}"

            effective_rem = remark_str if remark_str else "云端精选"
            cloud_map[endpoint] = effective_rem
            if host not in cloud_map:
                cloud_map[host] = effective_rem

        with self.state.lock:
            self.state.cloud_endpoints = cloud_map
            self.state.auto_endpoints = set(cloud_map.keys())
        valid_lines_count = len([line for line in content.splitlines() if line.strip() and not line.strip().startswith(("#", "//", "⏳", "Error"))])
        self.log(f"☁️ 从云端 auto.txt 成功同步 {valid_lines_count} 个精选节点 (已建立 {len(cloud_map)} 条多键映射)")
        return cloud_map

    def fetch_pending_endpoints_sync(self) -> dict[str, str]:
        """
        同步从 Cloudflare Worker 拉取 /pending.txt，获取待测归收池节点
        支持纯 IPv4:Port 与 域名(FQDN):Port
        返回: { "Endpoint": "待测备注名" }
        """
        ok, content = self.fetch_cloud_text("/pending.txt")
        pending_map = {}
        if not ok or not content:
            return pending_map

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//") or line.startswith("Error"):
                continue
            if "#" in line:
                parts = line.split("#", 1)
                ep_str = parts[0].strip()
                rem_str = parts[1].strip()
            else:
                parts = line.split(None, 1)
                ep_str = parts[0].strip()
                rem_str = parts[1].strip() if len(parts) > 1 else "待测节点"

            m = re.match(r"^([\w\.\-]+):(\d{1,5})$", ep_str)
            if not m:
                m_ip = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{1,5}))?", ep_str)
                if m_ip:
                    ip = m_ip.group(1)
                    port = m_ip.group(2) if m_ip.group(2) else "443"
                    endpoint = f"{ip}:{port}"
                else:
                    continue
            else:
                endpoint = f"{m.group(1)}:{m.group(2)}"

            pending_map[endpoint] = rem_str

        with self.state.lock:
            self.state.pending_endpoints = pending_map
        if pending_map:
            self.log(f"☁️ 从云端 pending.txt 成功同步 {len(pending_map)} 个待测节点")
        return pending_map

    def append_pending_endpoints_to_cloud(self, endpoints_with_remarks: list[tuple[str, str]]):
        if not endpoints_with_remarks:
            return
        with self.pending_pool_lock:
            current_map = self.fetch_pending_endpoints_sync()
            for ep, rem in endpoints_with_remarks:
                if ep and ep != "127.0.0.1:443":
                    current_map[ep] = rem or "待测候选"

            lines = [f"{ep}#{rem}" for ep, rem in current_map.items()]
            payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
            ok, msg = self.push_text_to_cf_worker(payload, subpath="/pending.txt")
            if ok:
                self.log(f"☁️ 成功同步 {len(endpoints_with_remarks)} 个节点至云端待测池 (/pending.txt，现有总量: {len(current_map)})")
            else:
                self.log(f"⚠️ 同步云端待测池 /pending.txt 失败: {msg}")

    def append_pending_endpoints_to_cloud_sync(self, endpoints_with_remarks: list[tuple[str, str]]) -> tuple[bool, str]:
        if not endpoints_with_remarks:
            return True, "无待测节点需要同步"
        with self.pending_pool_lock:
            current_map = self.fetch_pending_endpoints_sync()
            with self.state.lock:
                excluded = set()
                for n in (self.state.favorites | self.state.local_blacklist | self.state.speed_blacklist):
                    ep = self._get_ep(n)
                    if ep:
                        excluded.add(ep)
                        if ":" in ep:
                            excluded.add(ep.split(":")[0])
                    else:
                        excluded.add(str(n).strip())
                for star in self.state.stars_nodes:
                    s_ep = star.get("endpoint", "") if isinstance(star, dict) else ""
                    if s_ep:
                        excluded.add(s_ep)
                        if ":" in s_ep:
                            excluded.add(s_ep.split(":")[0])
                for v_ep in self.state.verified_nodes:
                    excluded.add(str(v_ep).strip())
                    if ":" in str(v_ep):
                        excluded.add(str(v_ep).split(":")[0])

            new_added = 0
            for ep, rem in endpoints_with_remarks:
                if not ep or ep == "127.0.0.1:443" or ep.startswith("1.1.1.1"):
                    continue
                ip_only = ep.split(":")[0] if ":" in ep else ep
                if ep not in excluded and ip_only not in excluded:
                    current_map[ep] = rem or "待测候选"
                    new_added += 1

            lines = [f"{ep}#{rem}" for ep, rem in current_map.items() if ep and not ep.startswith("1.1.1.1")]
            payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
            ok, msg = self.push_text_to_cf_worker(payload, subpath="/pending.txt")
            if ok:
                with self.state.lock:
                    self.state.pending_endpoints = current_map
                return True, f"成功同步待测池 (/pending.txt，本次新增 {new_added} 个，现有总量: {len(current_map)})"
            return False, f"同步待测池失败: {msg}"

    def purge_pending_endpoints_from_cloud(self) -> int:
        with self.pending_pool_lock:
            try:
                pending_map = self.fetch_pending_endpoints_sync()
                if not pending_map:
                    return 0

                forbidden_eps = set()
                with self.state.lock:
                    for s in (self.state.local_blacklist | self.state.speed_blacklist | self.state.favorites):
                        ep = self._get_ep(s)
                        if ep:
                            forbidden_eps.add(ep)
                            if ":" in ep:
                                forbidden_eps.add(ep.split(":")[0])
                        else:
                            forbidden_eps.add(str(s).strip())

                    for v_ep in self.state.verified_nodes:
                        forbidden_eps.add(str(v_ep).strip())
                        if ":" in str(v_ep):
                            forbidden_eps.add(str(v_ep).split(":")[0])

                    for star in self.state.stars_nodes:
                        s_ep = star.get("endpoint", "") if isinstance(star, dict) else ""
                        if s_ep:
                            forbidden_eps.add(s_ep)
                            if ":" in s_ep:
                                forbidden_eps.add(s_ep.split(":")[0])

                cleaned_map = {}
                purged_cnt = 0
                for ep, rem in pending_map.items():
                    if not ep or ep.startswith("1.1.1.1"):
                        purged_cnt += 1
                        continue
                    ip_only = ep.split(":")[0] if ":" in ep else ep
                    if ep in forbidden_eps or ip_only in forbidden_eps:
                        purged_cnt += 1
                        continue
                    cleaned_map[ep] = rem

                if purged_cnt > 0:
                    lines = [f"{ep}#{rem}" for ep, rem in cleaned_map.items()]
                    payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
                    ok, msg = self.push_text_to_cf_worker(payload, subpath="/pending.txt")
                    if ok:
                        with self.state.lock:
                            self.state.pending_endpoints = cleaned_map
                        self.log(f"🧹 已成功清洗云端待测池 (/pending.txt)：剔除已入黑名单/精选/孵化/典藏节点 {purged_cnt} 个，待测剩余 {len(cleaned_map)} 个")
                        return purged_cnt
                    else:
                        self.log(f"⚠️ 清洗云端待测池未回执成功: {msg}，已挂起后台自动补救自愈！")
                        self._schedule_pending_purge_retry()
                        return -1
                else:
                    self.log("☁️ 云端待测池当前已是纯净状态，无已判决的淘汰节点需要清洗。")
                    return 0
            except Exception as ex:
                self.log(f"❌ 清洗云端待测池异常: {ex}")
                self._schedule_pending_purge_retry()
                return -1

    def _schedule_pending_purge_retry(self):
        """后台挂起 20 秒延迟自动自愈重试清洗"""
        def _delay_worker():
            time.sleep(20)
            self.log("🔄 [后台自愈] 正在执行挂起的云端待测池清洗重试任务...")
            self.purge_pending_endpoints_from_cloud()
        import threading
        threading.Thread(target=_delay_worker, daemon=True).start()

    def trigger_cloud_sync_and_purge_safely(self):
        """
        在 Clash 内核稳定就绪后，以专属线程平稳执行精选池推云与待测池清洗
        """
        def _worker():
            try:
                # 1. 安全同步精选池至云端
                self.sync_favorites_to_cloud()
                time.sleep(1.0)
                # 2. 全池联动清洗待测池
                self.purge_pending_endpoints_from_cloud()
            except Exception as ex:
                self.log(f"❌ 平稳推云与清洗线程异常: {ex}")
        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def push_text_to_cf_worker(self, text_payload: str, subpath: str = "", base_url: str = None, token: str = None) -> tuple[bool, str]:
        """
        推送纯文本内容至 Cloudflare Worker。
        具备【urllib + 系统原生 curl.exe】双引擎强力容灾保底机制，彻底解决 SSL 握手超时痛点。
        """
        import os
        import subprocess
        import tempfile

        cfg = self.load_config()
        b_url = (base_url or cfg.get("worker_url") or cfg.get("cf_worker_url", "")).rstrip("/")
        tok = token or cfg.get("worker_token") or cfg.get("cf_worker_token", "")

        if not b_url or not b_url.startswith("http"):
            return False, "Worker 网址无效"

        if not text_payload or not text_payload.strip():
            text_payload = "# empty\r\n"

        target_url = f"{b_url}{subpath}" if subpath else f"{b_url}/"
        mixed_port = self.clash_client.get_mixed_port(default=7897)

        # 引擎 1: Python 原生 urllib (优先代理，失败回退直连，超时放宽至 15s)
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE

        proxy_handler = urllib.request.ProxyHandler({
            "http": f"http://127.0.0.1:{mixed_port}",
            "https": f"http://127.0.0.1:{mixed_port}",
        })
        proxy_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))
        direct_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=ssl_ctx))

        headers = {
            "Authorization": f"Bearer {tok}",
            "Content-Type": "text/plain; charset=utf-8",
            "User-Agent": "ClashVergeNodeAssistant/1.0",
        }
        req_data = text_payload.encode("utf-8")

        urllib_err = ""
        for attempt in range(1, 3):
            for use_proxy, opener in [(True, proxy_opener), (False, direct_opener)]:
                try:
                    req = urllib.request.Request(target_url, data=req_data, headers=headers, method="POST")
                    with opener.open(req, timeout=15) as resp:
                        if resp.status in (200, 201, 204):
                            channel = f"代理端口:{mixed_port}" if use_proxy else "直连"
                            return True, f"成功推送至 {target_url} ({channel})"
                        urllib_err = f"Worker 状态码: {resp.status}"
                except urllib.error.HTTPError as ex:
                    if ex.code == 401:
                        return False, "认证失败(401)，请确认 AUTH_TOKEN 密钥！"
                    urllib_err = f"HTTP({ex.code}): {ex.reason}"
                except Exception as ex:
                    urllib_err = str(ex)
            time.sleep(0.5)

        # 引擎 2 (终极保底): 自动唤醒 Windows 系统底层原生 curl.exe 执行强力穿透
        self.log(f"⚠️ [双引擎自愈] urllib 握手异常 ({urllib_err})，自动唤醒系统原生 curl.exe 强力保底...")
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="wb", delete=False) as tf:
                tf.write(req_data)
                temp_file_path = tf.name

            for curl_proxy in [f"http://127.0.0.1:{mixed_port}", None]:
                curl_cmd = [
                    "curl.exe", "-s",
                    "--max-time", "15",
                    "--retry", "2",
                    "-X", "POST",
                    "-H", f"Authorization: Bearer {tok}",
                    "-H", "Content-Type: text/plain; charset=utf-8",
                    "--data-binary", f"@{temp_file_path}",
                    target_url
                ]
                if curl_proxy:
                    curl_cmd.extend(["--proxy", curl_proxy])
                else:
                    curl_cmd.append("--noproxy", "*")

                res = subprocess.run(curl_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if res.returncode == 0:
                    out_msg = res.stdout.decode("utf-8", errors="ignore").strip()
                    self.log(f"✅ [双引擎自愈] curl.exe 保底成功: {out_msg or '写入成功'}")
                    return True, f"curl.exe 保底成功: {out_msg or '写入成功'}"
        except Exception as curl_ex:
            self.log(f"❌ [双引擎自愈] curl.exe 执行异常: {curl_ex}")
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

        return False, f"双引擎重试失败: {urllib_err}"

    def sync_premium_nodes_to_cf_worker(self, premium_nodes: list[str] = None, subpath: str = "/auto.txt") -> tuple[bool, str]:
        """
        将指定优质节点列表（默认全量 favorites）同步格式化推送到 Worker 指定子路径
        """
        with self.state.lock:
            nodes_to_push = list(premium_nodes) if premium_nodes is not None else list(self.state.favorites)
            lines = []
            seen_eps = set()
            for n in nodes_to_push:
                ep = self._get_ep(n) or n
                if not ep or ep == "127.0.0.1:443" or ep in seen_eps:
                    continue
                seen_eps.add(ep)
                colo = self.state.node_colo.get(n, self.state.node_colo.get(ep, "JP"))
                if not colo or colo == "-":
                    colo = "亚洲"
                spd = self.state.node_speeds.get(n, self.state.node_speeds.get(ep, 0.0))
                d = self.state.node_delays.get(n, self.state.node_delays.get(ep, 0))
                reason = self.state.fav_reasons.get(n, self.state.fav_reasons.get(ep, ""))

                is_sz = ("[送中]" in n) or ("[送中]" in ep) or ("[送中]" in reason)
                sz_tag = " [送中]" if is_sz and "[送中]" not in colo else ""

                if spd and spd > 0.1:
                    remark = f"{colo}{sz_tag} {spd:.2f} MB/s"
                elif "C段" in reason:
                    remark = f"{colo}{sz_tag} [C段挖掘]"
                else:
                    remark = f"{colo}{sz_tag}"
                lines.append(f"{ep}#{remark}")

        if not lines:
            return True, "本地优质池为空，跳过推送"
        payload = "\r\n".join(lines) + "\r\n"
        return self.push_text_to_cf_worker(payload, subpath=subpath)

    def push_favorites_to_cloud(self, base_url: str = None, token: str = None, callback=None):
        """
        异步推送优质精选池节点至 Cloudflare Worker /auto.txt
        """
        def _worker():
            with self.state.lock:
                fav_count = len(self.state.favorites)
            self.log(f"☁️ 正在推送 {fav_count} 个优质精选节点至 /auto.txt...")
            ok, msg = self.sync_premium_nodes_to_cf_worker(subpath="/auto.txt")
            if ok:
                self.log(f"✅ 同步优质精选池至 /auto.txt 成功: {msg}")
            else:
                self.log(f"❌ 同步优质精选池失败: {msg}")
            if callback:
                callback(ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    def sync_favorites_to_cloud(self):
        """
        将当前最新的 favorites 精选池全量覆写至 Cloudflare Worker /auto.txt 并重载映射
        (严格核验有效物理端点，彻底禁绝无端点纯文本马甲被误推上云污染云端)
        """
        def _worker():
            try:
                fav_lines = []
                seen_eps = set()
                with self.state.lock:
                    for f in list(self.state.favorites):
                        ep_val = self._get_ep(f)
                        if not ep_val:
                            # 尝试从 cloud_endpoints 或名称中反查有效端点
                            if re.match(r"^[\w\.\-]+:\d+$", str(f).strip()):
                                ep_val = str(f).strip()
                            else:
                                for c_ep, c_rem in self.state.cloud_endpoints.items():
                                    if c_rem and (c_rem == f or str(f).startswith(c_rem)):
                                        if ":" in c_ep:
                                            ep_val = c_ep
                                            break
                        # 强校验：必须为有效的 host:port 格式，且排除本地回环与重复项
                        if not ep_val or not re.match(r"^[\w\.\-]+:\d+$", ep_val) or ep_val in seen_eps or ep_val == "127.0.0.1:443":
                            continue
                        seen_eps.add(ep_val)

                        colo = self.state.node_colo.get(f, self.state.node_colo.get(ep_val, "JP"))
                        if not colo or colo == "-":
                            colo = "亚洲"

                        spd = self.state.node_speeds.get(f, self.state.node_speeds.get(ep_val, 0.0))
                        d = self.state.node_delays.get(f, self.state.node_delays.get(ep_val, 0))
                        reason = self.state.fav_reasons.get(f, self.state.fav_reasons.get(ep_val, ""))

                        # 优先级 1：只要有真实测速带宽 (>0.1)，必须以真实下载速度加冕！
                        if spd and spd > 0.1:
                            uniform_name = f"{colo} {spd:.2f} MB/s"
                        # 优先级 2：仅当该节点确系 C 段挖掘导入、且尚未测速时，显示 [C段挖掘]，绝不带毫秒延迟
                        elif "C段" in reason:
                            uniform_name = f"{colo} [C段挖掘]"
                        # 优先级 3：其他未测速的常规节点，仅显示归属地
                        else:
                            uniform_name = colo

                        fav_lines.append(f"{ep_val}#{uniform_name}")
                        self.state.cloud_endpoints[ep_val] = uniform_name
                        if ":" in ep_val:
                            self.state.cloud_endpoints[ep_val.split(":")[0]] = uniform_name
                        if f != uniform_name:
                            self._migrate_node_name(f, uniform_name, ep_val)

                payload = ("\r\n".join(fav_lines) + "\r\n") if fav_lines else "# empty\r\n"
                ok, msg = self.push_text_to_cf_worker(payload, subpath="/auto.txt")
                if ok:
                    self.log(f"☁️ 已自动同步最新精选池 ({len(fav_lines)} 个) 至云端 /auto.txt")
                else:
                    self.log(f"⚠️ 自动同步云端 /auto.txt 失败: {msg}")

                self.fetch_cloud_endpoints_sync()
                self.save_config(self.get_state_snapshot())
                self.data_changed.emit()
            except Exception as e:
                self.log(f"❌ 同步精选至云端异常: {e}")

        import threading
        threading.Thread(target=_worker, daemon=True).start()

    def test_worker_connection(self, worker_url: str = None, token: str = None, callback=None):
        """
        测试 Cloudflare Worker 通道连通性与权限认证
        """
        def _worker():
            self.log("🌐 正在测试 Cloudflare Worker 通信连接与鉴权...")
            ok, content = self.fetch_cloud_text(subpath="/auto.txt", base_url=worker_url, token=token)
            if ok:
                msg = f"Worker 通信正常！成功获取云端响应 (内容长度: {len(content)} 字符)"
                self.log(f"✅ {msg}")
            else:
                msg = f"Worker 通信测试失败: {content}"
                self.log(f"❌ {msg}")
            if callback:
                callback(ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    # ==================== 沉淀孵化池专属业务 ====================

    def pull_verified_from_cloud(self, base_url: str = None, callback=None):
        """
        从 Cloudflare Worker 拉取 /verified.txt 沉淀节点
        """
        cfg = self.load_config()
        b_url = (base_url or cfg.get("worker_url") or cfg.get("cf_worker_url", "")).rstrip("/")
        if not b_url.startswith("http"):
            msg = "请配置有效的 Cloudflare Worker 地址！"
            self.log(f"⚠️ {msg}")
            if callback:
                callback(False, msg)
            return

        def _worker():
            self.log("正在从 Cloudflare /verified.txt 拉取沉淀节点...")
            mixed_port = self.clash_client.get_mixed_port(default=7897)
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

            try:
                req = urllib.request.Request(f"{b_url}/verified.txt", headers={"User-Agent": "ClashVergeNodeAssistant/1.0"})
                with opener.open(req, timeout=10) as resp:
                    raw_text = resp.read().decode("utf-8", errors="ignore")

                now = time.time()
                with self.state.lock:
                    fav_eps = {self._get_ep(f) for f in self.state.favorites if f and self._get_ep(f)}
                    fav_eps.discard("")
                    fav_eps.discard("127.0.0.1:443")

                    added_count = 0
                    for line in raw_text.splitlines():
                        line = line.strip()
                        if not line or line.startswith("⏳") or line.startswith("Error"):
                            continue
                        if "#" in line:
                            parts = line.split("#", 1)
                            ep = parts[0].strip()
                            rem = parts[1].strip()
                        else:
                            ep = line
                            rem = "优质沉淀"

                        # 沉淀孵化池必须是优质精选池的严格子集
                        if ep not in fav_eps:
                            continue

                        c_val = self.state.node_colo.get(ep, "-")
                        if not (is_asian_node(ep, colo=c_val) or (rem and is_asian_node(rem, colo=c_val))):
                            self.state.local_blacklist.add(ep)
                            continue

                        if ep not in self.state.verified_nodes:
                            self.state.verified_nodes[ep] = {
                                "endpoint": ep,
                                "colo": "-",
                                "remark": rem,
                                "first_seen": now,
                                "passes": 1,
                                "fails": 0,
                                "delay": None,
                                "speed": None,
                                "reason": "云端同步拉取",
                            }
                            added_count += 1

                self.save_config(self.get_state_snapshot())
                self.data_changed.emit()
                msg = f"成功拉取云端沉淀节点！当前池内共 {len(self.state.verified_nodes)} 个。"
                self.log(f"✅ {msg}")
                if callback:
                    callback(True, msg)
            except Exception as ex:
                err_msg = f"拉取 /verified.txt 失败: {str(ex)}"
                self.log(f"❌ {err_msg}")
                if callback:
                    callback(False, err_msg)

        threading.Thread(target=_worker, daemon=True).start()

    def push_verified_to_cloud(self, base_url: str = None, token: str = None, callback=None):
        """
        推送沉淀池至 Cloudflare Worker /verified.txt
        """
        with self.state.lock:
            lines = [f"{v['endpoint']}#{v.get('remark', '')}" for v in self.state.verified_nodes.values() if v.get("endpoint")]
        payload = "\r\n".join(lines) + "\r\n"

        def _worker():
            self.log(f"正在推送 {len(lines)} 个沉淀节点至 /verified.txt...")
            ok, msg = self.push_text_to_cf_worker(payload, "/verified.txt", base_url=base_url, token=token)
            if ok:
                self.log(f"✅ 手动同步沉淀池至 /verified.txt 成功: {msg}")
            else:
                self.log(f"❌ 手动同步沉淀池失败: {msg}")
            if callback:
                callback(ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    def delete_selected_verified(self, endpoints: list[str]):
        """
        从沉淀池移除选定端点
        """
        if not endpoints:
            return
        with self.state.lock:
            for ep in endpoints:
                self.state.verified_nodes.pop(ep, None)
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🗑️ 已从沉淀孵化池移除 {len(endpoints)} 个节点")
        self.push_verified_to_cloud()

    def force_promote_verified_to_stars(self, endpoints: list[str]) -> int:
        """
        将选定沉淀节点提前加冕至典藏常青池
        """
        if not endpoints:
            return 0
        cnt = 0
        with self.state.lock:
            existing_eps = {s.get("endpoint") for s in self.state.stars_nodes}
            for ep in endpoints:
                if ep in self.state.verified_nodes and ep not in existing_eps:
                    v = self.state.verified_nodes[ep]
                    self.state.stars_nodes.append({
                        "endpoint": ep,
                        "colo": v.get("colo", "-"),
                        "remark": f"{v.get('remark', '')} [手动加冕]",
                        "delay": v.get("delay"),
                        "speed": v.get("speed"),
                        "matched_name": v.get("matched_name", ""),
                        "reason": f"沉淀池提前加冕 (已达标{v.get('passes', 0)}次)",
                    })
                    existing_eps.add(ep)
                    cnt += 1
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🏆 手动加冕 {cnt} 个沉淀节点至典藏常青池")
        return cnt

    def sync_favorites_to_verified(self):
        """
        从精选池手工纳入新端点至沉淀孵化池
        """
        now = time.time()
        cnt = 0
        with self.state.lock:
            for f in self.state.favorites:
                ep = self._get_ep(f)
                if not ep or ep == "127.0.0.1:443":
                    continue
                if ep not in self.state.verified_nodes:
                    self.state.verified_nodes[ep] = {
                        "endpoint": ep,
                        "colo": self.state.node_colo.get(f, "-"),
                        "remark": f"精选拉入 [{f}]",
                        "first_seen": now,
                        "passes": 1,
                        "fails": 0,
                        "delay": self.state.node_delays.get(f),
                        "speed": self.state.node_speeds.get(f),
                        "matched_name": f,
                        "reason": "从精选池手工纳入",
                    }
                    cnt += 1
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"📥 已将精选池中 {cnt} 个新端点纳入沉淀孵化池")

    # ==================== 典藏管理池专属业务 ====================

    def pull_stars_from_cloud(self, base_url: str = None, callback=None):
        """
        从 Cloudflare Worker 根目录拉取典藏常青节点
        """
        cfg = self.load_config()
        b_url = (base_url or cfg.get("worker_url") or cfg.get("cf_worker_url", "")).rstrip("/")
        if not b_url.startswith("http"):
            msg = "请配置有效的 Cloudflare Worker 地址！"
            self.log(f"⚠️ {msg}")
            if callback:
                callback(False, msg)
            return

        def _worker():
            self.log("正在从 Cloudflare 根目录拉取典藏常青节点...")
            mixed_port = self.clash_client.get_mixed_port(default=7897)
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

            try:
                req = urllib.request.Request(f"{b_url}/", headers={"User-Agent": "ClashVergeNodeAssistant/1.0"})
                with opener.open(req, timeout=10) as resp:
                    raw_text = resp.read().decode("utf-8", errors="ignore")

                new_stars = []
                for line in raw_text.splitlines():
                    line = line.strip()
                    if not line or line.startswith("⏳") or line.startswith("Error"):
                        continue
                    if "#" in line:
                        parts = line.split("#", 1)
                        ep = parts[0].strip()
                        rem = parts[1].strip()
                    else:
                        ep = line
                        rem = "典藏节点"
                    new_stars.append({
                        "endpoint": ep,
                        "colo": "-",
                        "remark": rem,
                        "delay": None,
                        "speed": None,
                        "reason": "云端根目录同步",
                    })

                with self.state.lock:
                    self.state.stars_nodes = new_stars
                self.save_config(self.get_state_snapshot())
                self.data_changed.emit()
                msg = f"成功从云端拉取并同步 {len(new_stars)} 个典藏常青节点！"
                self.log(f"✅ {msg}")
                if callback:
                    callback(True, msg)
            except Exception as ex:
                err_msg = f"从云端拉取典藏失败: {str(ex)}"
                self.log(f"❌ {err_msg}")
                if callback:
                    callback(False, err_msg)

        threading.Thread(target=_worker, daemon=True).start()

    def push_stars_to_cloud(self, base_url: str = None, token: str = None, callback=None):
        """
        手动同步典藏常青池到 Cloudflare 根目录
        """
        with self.state.lock:
            lines = [f"{s.get('endpoint', '')}#{s.get('remark', '')}" for s in self.state.stars_nodes if s.get("endpoint")]
        payload = "\r\n".join(lines) + "\r\n"

        def _worker():
            self.log(f"正在手动推送 {len(lines)} 个典藏常青节点至 Cloudflare 根目录...")
            ok, msg = self.push_text_to_cf_worker(payload, "", base_url=base_url, token=token)
            if ok:
                self.log(f"✅ 手动同步典藏常青池到根目录成功: {msg}")
            else:
                self.log(f"❌ 手动同步典藏常青池失败: {msg}")
            if callback:
                callback(ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    def add_star_node(self, endpoint: str, remark: str = "典藏节点") -> bool:
        """
        手动录入单个典藏节点
        """
        ep = endpoint.strip()
        if not ep:
            return False
        with self.state.lock:
            for s in self.state.stars_nodes:
                if s.get("endpoint") == ep:
                    s["remark"] = remark
                    self.save_config(self.get_state_snapshot())
                    self.data_changed.emit()
                    return True
            self.state.stars_nodes.append({
                "endpoint": ep,
                "colo": "-",
                "remark": remark,
                "delay": None,
                "speed": None,
                "reason": "手动录入典藏",
            })
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"➕ 已成功将节点 [{ep}] 录入典藏池")
        return True

    def update_star_remark(self, endpoint: str, new_remark: str):
        """
        修改典藏节点备注
        """
        with self.state.lock:
            for s in self.state.stars_nodes:
                if s.get("endpoint") == endpoint:
                    s["remark"] = new_remark.strip()
                    break
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"✏️ 已更新典藏节点 [{endpoint}] 的备注为: {new_remark.strip()}")

    def delete_selected_stars(self, endpoints: list[str]):
        """
        从典藏池移除选定端点
        """
        if not endpoints:
            return
        ep_set = set(endpoints)
        with self.state.lock:
            self.state.stars_nodes = [s for s in self.state.stars_nodes if s.get("endpoint") not in ep_set]
        self.save_config(self.get_state_snapshot())
        self.data_changed.emit()
        self.log(f"🗑️ 已从典藏池移除 {len(endpoints)} 个节点")
        self.push_stars_to_cloud()

    def test_stars_pipeline(self, mode="delay", endpoints: list[str] = None, callback=None):
        """
        对典藏节点执行延迟或带宽测速
        """
        with self.state.lock:
            stars = list(self.state.stars_nodes)
            all_n = list(self.state.all_nodes)

        if endpoints:
            ep_set = set(endpoints)
            targets = [s for s in stars if s.get("endpoint") in ep_set]
        else:
            targets = stars

        if not targets:
            self.log("⚠️ 当前典藏池没有节点可测！")
            if callback:
                callback(False, "无待测节点")
            return

        reverse_map = {}
        for n in all_n:
            ep = self._get_ep(n)
            if ep:
                reverse_map[ep] = n

        testable = []
        for t in targets:
            ep = t.get("endpoint", "")
            m_name = reverse_map.get(ep, "")
            if not m_name and ":" in ep:
                m_name = reverse_map.get(ep.split(":")[0], "")
            if m_name:
                t["matched_name"] = m_name
                testable.append(t)

        if not testable:
            msg = "所选典藏节点尚未在当前订阅/Clash内核中找到对应的匹配节点！"
            self.log(f"⚠️ {msg}")
            if callback:
                callback(False, msg)
            return

        cfg = self.load_config()
        test_url = cfg.get("test_url", "https://www.google.com/generate_204")
        speed_url = cfg.get("speed_url", "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip")
        if not speed_url or "speed.cloudflare.com" in speed_url:
            speed_url = "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip"

        def _worker():
            self.log(f"开始测试 {len(testable)} 个典藏节点 (模式: {mode})...")
            if mode == "delay":
                from services.probe_service import get_cf_colo_raw
                from services.colo_service import record_colo_sample
                for item in testable:
                    name = item["matched_name"]
                    d_val = self.clash_client.query_proxy_delay(name, test_url, timeout_ms=1500)
                    item["delay"] = d_val
                    ep_raw = item.get("endpoint", "")
                    if ":" in ep_raw:
                        s_ip, s_p = ep_raw.rsplit(":", 1)
                        c_code, c_disp = get_cf_colo_raw(s_ip, s_p)
                        with self.state.lock:
                            record_colo_sample(self.state.node_colo_history, name, ep_raw, c_code, c_disp)
                            item["colo"] = c_disp
                            self.state.node_colo[name] = c_disp
                            self.state.node_colo[ep_raw] = c_disp
                self.save_config(self.get_state_snapshot())
                self.data_changed.emit()
                self.log("✅ 典藏节点延迟测速完成！")
                if callback:
                    callback(True, "延迟测速完成")
            else:
                mode_guard = ClashModeGuard(self.clash_client, temporary_mode="global")
                mode_guard.__enter__()
                mixed_port = self.clash_client.get_mixed_port(default=7897)
                ssl_ctx = ssl.create_default_context()
                ssl_ctx.check_hostname = False
                ssl_ctx.verify_mode = ssl.CERT_NONE

                proxy_handler = urllib.request.ProxyHandler({
                    "http": f"http://127.0.0.1:{mixed_port}",
                    "https": f"http://127.0.0.1:{mixed_port}",
                })
                speed_opener = urllib.request.build_opener(proxy_handler, urllib.request.HTTPSHandler(context=ssl_ctx))

                try:
                    for item in testable:
                        name = item["matched_name"]
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": name})
                        time.sleep(0.1)

                        speed_val = 0.0
                        total_bytes = 0
                        st = time.time()
                        try:
                            req = urllib.request.Request(speed_url, headers={"User-Agent": "Mozilla/5.0", "Connection": "close"})
                            with speed_opener.open(req, timeout=2.5) as resp:
                                chunk_size = 16 * 1024
                                while time.time() - st < 2.0:
                                    ch = resp.read(chunk_size)
                                    if not ch:
                                        break
                                    total_bytes += len(ch)
                                el = time.time() - st
                                speed_val = round((total_bytes / (1024 * 1024)) / el, 2) if (el > 0 and total_bytes > 0) else 0.0
                        except Exception:
                            speed_val = -1.0
                        item["speed"] = speed_val
                finally:
                    mode_guard.__exit__(None, None, None)

                self.save_config(self.get_state_snapshot())
                self.data_changed.emit()
                self.log("✅ 典藏节点带宽测速完成！")
                if callback:
                    callback(True, "带宽测速完成")

        threading.Thread(target=_worker, daemon=True).start()
```

## File: `gui_fluent/main_window.py`

```python
"""
Clash Verge 节点管理助手 - Fluent 风格主窗口
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QStackedWidget,
        QSystemTrayIcon,
        QMenu,
        QAction,
        QStyle,
    )
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon, QAction
    from PyQt6.QtWidgets import (
        QApplication,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QStackedWidget,
        QSystemTrayIcon,
        QMenu,
        QStyle,
    )

from qfluentwidgets import (
    SegmentedWidget,
    MessageBox,
    setTheme,
    Theme,
    PushButton,
)

from gui_fluent.app_controller import AppController
from gui_fluent.components.top_bar import TopBar
from gui_fluent.components.log_panel import LogPanel
from gui_fluent.components.bottom_action_bar import BottomActionBar
from gui_fluent.components.pipeline_card import PipelineCard

from gui_fluent.pages.page_active import PageActive
from gui_fluent.pages.page_favorites import PageFavorites
from gui_fluent.pages.page_verified import PageVerified
from gui_fluent.pages.page_stars import PageStars
from gui_fluent.pages.page_delay_black import PageDelayBlack
from gui_fluent.pages.page_speed_black import PageSpeedBlack
from gui_fluent.pages.page_cloud_text import PageCloudText

from gui_fluent.widgets.c_miner_dialog import CSegmentMinerDialog


class MainWindow(QWidget):
    """
    基于 PyQt-Fluent-Widgets 构建的全新横向顶部导航 Fluent 主窗口
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_app()

    def init_app(self):
        # 1. 基础属性与 Windows 11 深色主题
        self.setWindowTitle("Clash Verge 节点管理助手 (Fluent 版)")
        setTheme(Theme.DARK)
        self.setStyleSheet("""
            MainWindow {
                background-color: #1a1a1a;
                color: #f1f5f9;
            }
        """)

        self.setMinimumSize(1200, 760)
        self.resize(1260, 800)
        self.center_on_screen()

        # 2. 实例化中枢控制器
        self.controller = AppController(self)

        # 3. 组装自上而下的整体垂直布局结构
        self.init_layout_structure()

        # 4. 初始化 7 个子页面并添加到 stackedWidget 和顶部横向 SegmentedWidget
        self.init_sub_pages()

        # 5. 绑定控制器日志信号至界面日志面板
        self.controller.log_signal.connect(self.log_panel.append_log)
        self.controller.log("欢迎使用 Clash Verge 节点管理助手 (Fluent UI 现代版)！")

        # 6. 绑定流水线控制卡信号
        self._bind_pipeline_signals()

        # 7. 绑定底部操作栏业务动作
        self._bind_bottom_actions()

        # 8. 接入后台定时调度守护与精选自愈降级
        self.controller.set_scheduler_config_provider(self._get_scheduler_config)
        self.controller.scheduler_trigger_full_signal.connect(self._on_scheduler_trigger_full)
        self.controller.scheduler_trigger_fav_signal.connect(self._on_scheduler_trigger_fav)
        self.controller.fav_pipeline_fallback_needed.connect(self._on_fav_fallback_needed)

        # 9. 恢复初始配置与历史回显
        cfg = self.controller.load_config() or {}
        self.restore_ui_config(cfg)

        # 10. 初始化 Windows 系统托盘与自愈守护信号
        self._init_system_tray()
        self._bind_auto_heal_signals()

        # 11. 绑定全界面控件实时编辑自动存盘
        self._bind_auto_save_signals()

    def init_layout_structure(self):
        """
        构建主窗体自上而下的整体布局结构：
        - SegmentedWidget (横向菜单，靠左排列)
        - self.top_bar (包含订阅与右侧一排测速按钮)
        - self.pipeline_card (流水线参数卡片)
        - self.stackedWidget (核心表格区，设置 stretch=1)
        - self.log_panel (日志区)
        - self.bottom_action_bar (底部按键)
        """
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(16, 12, 16, 10)
        self.main_layout.setSpacing(8)

        # 1. 顶部横向 SegmentedWidget 与 C段挖掘入口
        self.nav_layout = QHBoxLayout()
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.segment = SegmentedWidget(self)
        self.nav_layout.addWidget(self.segment)
        self.nav_layout.addStretch(1)
        
        self.btn_c_miner = PushButton("🔍 C段深度挖掘", self)
        self.btn_c_miner.clicked.connect(self._on_c_miner_clicked)
        self.nav_layout.addWidget(self.btn_c_miner)

        self.main_layout.addLayout(self.nav_layout)

        # 2. 上：TopBar (~68px)
        self.top_bar = TopBar(self)
        self.top_bar.setFixedHeight(68)
        self.main_layout.addWidget(self.top_bar)

        # 3. 中上：PipelineCard（流水线参数控制卡）
        self.pipeline_card = PipelineCard(self)
        self.main_layout.addWidget(self.pipeline_card)

        # 4. 中：StackedWidget (核心表格区，自适应伸展 stretch=1)
        self.stackedWidget = QStackedWidget(self)
        self.main_layout.addWidget(self.stackedWidget, 1)

        # 5. 下：LogPanel (~120px)
        self.log_panel = LogPanel(self)
        self.log_panel.setFixedHeight(120)
        self.main_layout.addWidget(self.log_panel)

        # 6. 下：BottomActionBar (~50px)
        self.bottom_action_bar = BottomActionBar(self)
        self.bottom_action_bar.setFixedHeight(50)
        self.main_layout.addWidget(self.bottom_action_bar)

    def init_sub_pages(self):
        """
        创建 7 个功能页面，装配进 stackedWidget，并在顶部横排 SegmentedWidget 中注册标签项
        """
        self.page_active = PageActive(self.controller, self)
        self.page_favorites = PageFavorites(self.controller, self)
        self.page_verified = PageVerified(self.controller, self)
        self.page_stars = PageStars(self.controller, self)
        self.page_delay_black = PageDelayBlack(self.controller, self)
        self.page_speed_black = PageSpeedBlack(self.controller, self)
        self.page_cloud_text = PageCloudText(self.controller, self)

        # 页面加入 QStackedWidget
        self.stackedWidget.addWidget(self.page_active)
        self.stackedWidget.addWidget(self.page_favorites)
        self.stackedWidget.addWidget(self.page_verified)
        self.stackedWidget.addWidget(self.page_stars)
        self.stackedWidget.addWidget(self.page_delay_black)
        self.stackedWidget.addWidget(self.page_speed_black)
        self.stackedWidget.addWidget(self.page_cloud_text)

        # 顶部横排菜单注册项
        self.segment.addItem(
            routeKey="active",
            text="📋 活跃待测",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_active),
        )
        self.segment.addItem(
            routeKey="favorites",
            text="⭐ 优质精选",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_favorites),
        )
        self.segment.addItem(
            routeKey="verified",
            text="⏳ 沉淀孵化",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_verified),
        )
        self.segment.addItem(
            routeKey="stars",
            text="🏆 典藏管理",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_stars),
        )
        self.segment.addItem(
            routeKey="delay_black",
            text="🚫 延迟黑名单",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_delay_black),
        )
        self.segment.addItem(
            routeKey="speed_black",
            text="🐌 低速黑名单",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_speed_black),
        )
        self.segment.addItem(
            routeKey="cloud_text",
            text="☁️ 云端文本",
            onClick=lambda: self.stackedWidget.setCurrentWidget(self.page_cloud_text),
        )

        self.segment.setCurrentItem("active")

        # 监听标签页切换事件，切换时自动刷新目标页面数据
        self.stackedWidget.currentChanged.connect(self._on_page_changed)
        self.controller.data_changed.connect(self.update_tab_badges)
        self.update_tab_badges()

    def update_tab_badges(self):
        """
        动态更新顶部导航栏各标签后的实时节点数量角标
        """
        try:
            cnt_active = len(self.controller.get_table_rows("active"))
            cnt_fav = len(self.controller.get_table_rows("favorites"))
            cnt_ver = len(self.controller.get_table_rows("verified"))
            cnt_stars = len(self.controller.get_table_rows("stars"))
            cnt_delay_bl = len(self.controller.get_table_rows("delay_black"))
            cnt_speed_bl = len(self.controller.get_table_rows("speed_black"))

            self.segment.setItemText("active", f"📋 活跃待测 ({cnt_active})")
            self.segment.setItemText("favorites", f"⭐ 优质精选 ({cnt_fav})")
            self.segment.setItemText("verified", f"⏳ 沉淀孵化 ({cnt_ver})")
            self.segment.setItemText("stars", f"🏆 典藏管理 ({cnt_stars})")
            self.segment.setItemText("delay_black", f"🚫 延迟黑名单 ({cnt_delay_bl})")
            self.segment.setItemText("speed_black", f"🐌 低速黑名单 ({cnt_speed_bl})")
            self.segment.setItemText("cloud_text", "☁️ 云端文本")
        except Exception:
            pass

    def center_on_screen(self):
        """
        窗口居中显示于当前屏幕
        """
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = (geo.width() - self.width()) // 2
            y = (geo.height() - self.height()) // 2
            self.move(max(0, x), max(0, y))

    def _bind_pipeline_signals(self):
        pc = self.pipeline_card
        # 重连按钮：调用 AppController 检测连接状态并更新状态标签
        pc.btn_reconnect.clicked.connect(self._on_reconnect_clicked)

        # 启动与终止流水线按钮
        pc.btn_run_pipeline.clicked.connect(self._on_run_pipeline_clicked)
        pc.btn_stop_pipeline.clicked.connect(self._on_stop_pipeline_clicked)

        # 核心设置卡片操作按钮
        pc.btn_save_group.clicked.connect(self._on_save_group_clicked)
        pc.btn_test_worker.clicked.connect(self._on_test_worker_clicked)
        pc.btn_sync_auto.clicked.connect(self._on_sync_auto_clicked)

        # 第 6 行：自愈守护与诊断控件绑定
        pc.chk_auto_heal.stateChanged.connect(self._on_auto_heal_toggled)
        pc.btn_diagnose_link.clicked.connect(self._on_diagnose_link_clicked)
        pc.auto_heal_threshold.textChanged.connect(self._update_auto_heal_params)
        pc.auto_heal_cooldown.textChanged.connect(self._update_auto_heal_params)
        pc.chk_minimize_to_tray.stateChanged.connect(self._on_tray_pref_changed)

        # 绑定流水线结束与状态信号
        self.controller.pipeline_finished.connect(self._on_pipeline_finished)
        self.controller.pipeline_status_updated.connect(self._on_pipeline_status_updated)

        # 顶部 TopBar 快捷操作组按钮绑定
        self.top_bar.btn_update_sub.clicked.connect(self._on_update_sub_clicked)
        self.top_bar.btn_test_page_colo.clicked.connect(self._on_test_page_colo_clicked)
        self.top_bar.btn_clear_page_colo.clicked.connect(self._on_clear_page_colo_clicked)
        self.top_bar.btn_sync_kernel_delay.clicked.connect(self._on_sync_kernel_delay_clicked)
        self.top_bar.btn_clear_speed_records.clicked.connect(self._on_clear_speed_records_clicked)

        # 订阅下拉框加载可用 YAML 文件
        try:
            yamls = self.controller.get_all_yaml_profiles()
            self.top_bar.sub_combo.addItems(yamls)
            self.top_bar.sub_combo.currentTextChanged.connect(self._on_sub_combo_changed)
        except Exception:
            pass

    def _on_sub_combo_changed(self, yaml_name: str):
        if not yaml_name:
            return
        try:
            nodes, _ = self.controller.load_nodes_from_profile(yaml_name)
            setattr(self.controller.state, "active_profile", yaml_name)
            self.controller.save_config({"last_selected_yaml": yaml_name, "active_profile": yaml_name})
            self.controller.log(f"已切换订阅配置 [{yaml_name}]，加载了 {len(nodes)} 个节点")
            self.controller.data_changed.emit()
        except Exception as e:
            self.controller.log(f"加载订阅配置 [{yaml_name}] 失败: {str(e)}")

    def _on_run_pipeline_clicked(self):
        pc = self.pipeline_card
        current_yaml = self.top_bar.sub_combo.currentText().strip()
        if current_yaml and not self.controller.state.all_nodes:
            self._on_sub_combo_changed(current_yaml)

        config = {
            "max_delay": pc.max_delay.text().strip(),
            "min_speed": pc.min_speed.text().strip(),
            "target_count": pc.target_count.text().strip(),
            "test_rounds": pc.test_rounds.text().strip(),
            "test_timeout": pc.test_timeout.text().strip(),
            "speed_duration": pc.speed_duration.text().strip(),
            "blacklist_threshold": pc.blacklist_threshold.text().strip(),
            "speed_bl_threshold": pc.speed_bl_threshold.text().strip(),
            "speed_bl_rounds": pc.speed_bl_rounds.text().strip(),
            "jitter_min_delay": pc.jitter_min_delay.text().strip(),
            "jitter_up_threshold": pc.jitter_up_threshold.text().strip(),
            "test_url": pc.test_url.text().strip(),
            "speed_url": pc.speed_url.text().strip(),
            "schedule_interval": pc.schedule_interval.text().strip(),
            "schedule_times": pc.schedule_times.text().strip(),
            "group_interval": pc.group_interval.text().strip(),
            "group_tolerance": pc.group_tolerance.text().strip(),
            "star_group_interval": pc.star_group_interval.text().strip(),
            "star_group_tolerance": pc.star_group_tolerance.text().strip(),
            "worker_url": pc.worker_url.text().strip(),
            "worker_token": pc.worker_token.text().strip(),
            "clash_port": pc.clash_port.text().strip(),
            "clash_secret": pc.clash_secret.text().strip(),
        }

        started = self.controller.start_auto_pipeline(config)
        if started:
            pc.btn_run_pipeline.setEnabled(False)
            pc.btn_stop_pipeline.setEnabled(True)

    def _on_stop_pipeline_clicked(self):
        self.controller.stop_auto_pipeline()
        pc = self.pipeline_card
        pc.btn_stop_pipeline.setEnabled(False)

    def _on_pipeline_finished(self, success: bool, desc: str):
        pc = self.pipeline_card
        pc.btn_run_pipeline.setEnabled(True)
        pc.btn_stop_pipeline.setEnabled(False)
        self.controller.log(f"流水线运行结束: {'成功' if success else '中断/失败'} - {desc}")
        if hasattr(self, 'controller') and self.controller:
            self.controller.save_config(self.controller.state.get_snapshot())

        # 弹窗汇报大优选完成总结
        title = "🎉 全量大优选任务完成" if success else "⚠️ 流水线结束"
        fav_count = len(self.controller.state.favorites)
        star_count = len(self.controller.state.stars_nodes)
        d_bl_count = len(self.controller.state.local_blacklist)
        s_bl_count = len(self.controller.state.speed_blacklist)

        content = (
            f"【执行状态】: {desc}\n\n"
            f"📊 核心池最新统计：\n"
            f"  • ⭐ 优质精选池: {fav_count} 个\n"
            f"  • 🏆 典藏常青池: {star_count} 个\n"
            f"  • 🚫 延迟黑名单: {d_bl_count} 个\n"
            f"  • 🐌 低速黑名单: {s_bl_count} 个\n\n"
            f"✅ 最新策略组已自动写入 Script.js 并生效。"
        )
        msg_box = MessageBox(title, content, self)
        if hasattr(msg_box, "cancelButton") and msg_box.cancelButton:
            msg_box.cancelButton.hide()
        msg_box.exec()

    def _on_pipeline_status_updated(self, status_text: str):
        self.pipeline_card.lbl_sched_status.setText(status_text)

    def _on_reconnect_clicked(self):
        pc = self.pipeline_card
        port_text = pc.clash_port.text().strip()
        secret_text = pc.clash_secret.text().strip()
        try:
            port = int(port_text) if port_text else 9097
        except ValueError:
            port = 9097
        self.controller.update_clash_credentials(port=port, secret=secret_text)
        ok, ver = self.controller.get_clash_connection_status()
        if ok:
            pc.lbl_conn_status.setText(f"● 已连接 v{ver}")
            pc.lbl_conn_status.setStyleSheet("color: #10b981; font-weight: bold;")
            self.top_bar.lbl_status.setText(f"● 内核已连接 v{ver}")
            self.top_bar.lbl_status.setStyleSheet("color: #10b981; font-weight: bold;")
        else:
            pc.lbl_conn_status.setText("● 连接失败")
            pc.lbl_conn_status.setStyleSheet("color: #f87171; font-weight: bold;")
            self.top_bar.lbl_status.setText("● 内核未连接")
            self.top_bar.lbl_status.setStyleSheet("color: #f87171; font-weight: bold;")
        self.controller.log(f"Clash 连接检测: {'成功' if ok else '失败'} {ver}")

    def _on_save_group_clicked(self):
        pc = self.pipeline_card
        cfg = {
            "group_interval": pc.group_interval.text().strip(),
            "group_tolerance": pc.group_tolerance.text().strip(),
            "star_group_interval": pc.star_group_interval.text().strip(),
            "star_group_tolerance": pc.star_group_tolerance.text().strip(),
        }
        self.controller.save_config(cfg)
        self.controller.generate_script_and_reload()
        self.controller.log("💾 策略组配置已保存并重新写入 Script.js！")

    def _on_test_worker_clicked(self):
        pc = self.pipeline_card
        w_url = pc.worker_url.text().strip()
        w_tok = pc.worker_token.text().strip()
        self.controller.save_config({"worker_url": w_url, "worker_token": w_tok})
        self.controller.test_worker_connection(worker_url=w_url, token=w_tok)

    def _on_sync_auto_clicked(self):
        pc = self.pipeline_card
        w_url = pc.worker_url.text().strip()
        w_tok = pc.worker_token.text().strip()
        self.controller.save_config({"worker_url": w_url, "worker_token": w_tok})
        self.controller.push_favorites_to_cloud(base_url=w_url, token=w_tok)

    def _on_page_changed(self, index: int):
        """
        导航标签页切换时，同步顶部菜单高亮并主动刷新目标页面的表格数据
        """
        page = self.stackedWidget.currentWidget()
        route_map = {
            self.page_active: "active",
            self.page_favorites: "favorites",
            self.page_verified: "verified",
            self.page_stars: "stars",
            self.page_delay_black: "delay_black",
            self.page_speed_black: "speed_black",
            self.page_cloud_text: "cloud_text",
        }
        route_key = route_map.get(page)
        if route_key and self.segment.currentRouteKey() != route_key:
            self.segment.setCurrentItem(route_key)

        if page and hasattr(page, "refresh_data"):
            page.refresh_data()
        self.update_tab_badges()

    # ==================== 底部快捷操作栏绑定 ====================

    def _bind_bottom_actions(self):
        """
        绑定底部操作栏按钮的点击事件
        """
        bar = self.bottom_action_bar
        try:
            bar.btn_fav.clicked.disconnect()
        except Exception:
            pass
        bar.btn_fav.clicked.connect(self._on_btn_fav_clicked)

        try:
            bar.btn_promote.clicked.disconnect()
        except Exception:
            pass
        bar.btn_promote.clicked.connect(self._on_btn_promote_clicked)

        try:
            bar.btn_delay_black.clicked.disconnect()
        except Exception:
            pass
        bar.btn_delay_black.clicked.connect(self._on_btn_delay_black_clicked)

        try:
            bar.btn_speed_black.clicked.disconnect()
        except Exception:
            pass
        bar.btn_speed_black.clicked.connect(self._on_btn_speed_black_clicked)

        try:
            bar.btn_unblack.clicked.disconnect()
        except Exception:
            pass
        bar.btn_unblack.clicked.connect(self._on_btn_unblack_clicked)

        try:
            bar.btn_clear_bl.clicked.disconnect()
        except Exception:
            pass
        bar.btn_clear_bl.clicked.connect(self._on_btn_clear_bl_clicked)

        try:
            bar.btn_rescore.clicked.disconnect()
        except Exception:
            pass
        bar.btn_rescore.clicked.connect(self._on_btn_rescore_clicked)

        try:
            bar.btn_hotkey_sync.clicked.disconnect()
        except Exception:
            pass
        bar.btn_hotkey_sync.clicked.connect(self._on_btn_hotkey_sync_clicked)

    def _get_current_selected_nodes(self) -> list[str]:
        """
        获取当前激活页面中表格选中的节点名称或物理端点列表
        """
        page = self.stackedWidget.currentWidget()
        if not page or not hasattr(page, "table"):
            return []
        t = page.table
        if hasattr(t, "get_selected_node_names"):
            names = t.get_selected_node_names()
            if names:
                return names
        if hasattr(t, "get_selected_endpoints"):
            eps = t.get_selected_endpoints()
            if eps:
                return eps
        return []

    def _on_c_miner_clicked(self):
        """
        呼出 C 段全量极速深度挖掘对话框
        """
        seed_ip = "172.64.229.1"
        nodes = self._get_current_selected_nodes()
        if nodes:
            ep = nodes[0]
            if ":" in ep:
                seed_ip = ep.split(":")[0]
            else:
                seed_ip = ep
        dialog = CSegmentMinerDialog(seed_ip=seed_ip, seed_port=443, controller=self.controller, parent=self)
        dialog.exec()

    def _on_btn_fav_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要设为优质的节点！")
            return
        self.controller.move_nodes_to_favorites(nodes)

    def _on_btn_promote_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要晋升典藏的节点！")
            return
        self.controller.promote_nodes_to_stars(nodes)

    def _on_btn_delay_black_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要加入延迟黑名单的节点！")
            return
        self.controller.blacklist_nodes(nodes, reason="手动拉黑", bl_type="delay")

    def _on_btn_speed_black_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要加入低速黑名单的节点！")
            return
        self.controller.blacklist_nodes(nodes, reason="手动拉黑", bl_type="speed")

    def _on_btn_unblack_clicked(self):
        nodes = self._get_current_selected_nodes()
        if not nodes:
            self.controller.log("⚠️ 请先在当前表格中选中要移出黑名单的节点！")
            return
        self.controller.remove_nodes_from_blacklist(nodes)

    def _on_btn_clear_bl_clicked(self):
        w = MessageBox("确认清空黑名单", "确定要清空所有延迟黑名单与低速黑名单记录吗？\n清空后所有被拉黑的节点将重新回到待测活跃池。", self)
        if w.exec():
            self.controller.clear_all_blacklists()

    def _on_btn_rescore_clicked(self):
        page = self.stackedWidget.currentWidget()
        if hasattr(page, "refresh_table"):
            page.refresh_table()
        elif hasattr(page, "refresh_data"):
            page.refresh_data()
        self.controller.log("📊 已重新计算综合评分与节点晋升状态！")

    def _on_btn_hotkey_sync_clicked(self):
        self.controller.trigger_verge_reload()

    # ==================== TopBar 顶部工具栏动作 ====================

    def _get_current_page_key(self) -> str:
        """
        获取当前激活页面的 key
        """
        curr = self.stackedWidget.currentWidget()
        if curr == self.page_favorites:
            return "favorites"
        elif curr == self.page_verified:
            return "verified"
        elif curr == self.page_stars:
            return "stars"
        elif curr == self.page_delay_black:
            return "delay_black"
        elif curr == self.page_speed_black:
            return "speed_black"
        elif curr == self.page_cloud_text:
            return "cloud_text"
        return "active"

    def _on_update_sub_clicked(self):
        curr_yaml = self.top_bar.sub_combo.currentText().strip()
        if not curr_yaml:
            self.controller.log("⚠️ 请先在下拉框选择要更新的订阅配置！")
            return
        self.controller.update_current_subscription(curr_yaml)

    def _on_test_page_colo_clicked(self):
        page_key = self._get_current_page_key()
        self.controller.test_current_page_colo(page_key)

    def _on_clear_page_colo_clicked(self):
        page_key = self._get_current_page_key()
        w = MessageBox(
            "确认清空机房记录",
            f"确定要清空当前标签页中所有节点的实时机房(Colo)与历史采样记录吗？\n\n"
            "• 该操作将清除最新 Colo 结果与 7 天滑动时序数据；\n"
            "• 归零后可点击【🌍 测当前页Colo】重新采集纯净数据。",
            self,
        )
        if w.exec():
            self.controller.clear_current_page_colo(page_key)

    def _on_sync_kernel_delay_clicked(self):
        self.controller.sync_kernel_delays()

    def _on_clear_speed_records_clicked(self):
        w = MessageBox(
            "清空确认",
            "确定要清空所有测速数据与延迟趋势记录吗？\n（不会清空您的黑名单及下行带宽历史）",
            self,
        )
        if w.exec():
            self.controller.clear_speed_records()

    # ==================== 后台定时调度与自愈降级 ====================

    def _get_scheduler_config(self) -> dict:
        """
        提供给 SchedulerDaemon 的动态定时参数字典
        """
        pc = self.pipeline_card
        pf = self.page_favorites
        return {
            "schedule_enabled": pc.chk_schedule.isChecked(),
            "schedule_times": pc.schedule_times.text().strip(),
            "schedule_interval": pc.schedule_interval.text().strip(),
            "fav_schedule_enabled": pf.chk_fav_schedule.isChecked(),
            "fav_schedule_interval": pf.fav_sched_interval.text().strip(),
        }

    def _on_scheduler_trigger_full(self, reason: str):
        self.controller.log(f"⏰ [定时调度] 触发全量大优选: {reason}")
        self._on_run_pipeline_clicked()

    def _on_scheduler_trigger_fav(self, reason: str):
        self.controller.log(f"⏰ [定时调度] 触发优质精选复检: {reason}")
        self.page_favorites._on_run_fav_clicked()

    def _on_fav_fallback_needed(self, reason: str):
        self.controller.log(f"⚡ 收到优质池自愈降级请求: {reason}，自动启动全量大优选...")
        self._on_run_pipeline_clicked()

    # ==================== Windows 系统托盘与断流秒级自愈 ====================

    def _init_system_tray(self):
        """
        初始化 Windows 系统托盘与右键菜单
        """
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        icon = self.windowIcon()
        if not icon or icon.isNull():
            icon = QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DriveNetIcon)

        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_icon.setToolTip("Clash Verge 节点管理助手 (断流秒级自愈守护中)")

        tray_menu = QMenu()
        act_show = tray_menu.addAction("显示主界面")
        act_show.triggered.connect(self._show_window)

        act_diag = tray_menu.addAction("⚡ 诊断当前链路")
        act_diag.triggered.connect(self._on_diagnose_link_clicked)

        self.act_tray_heal_toggle = tray_menu.addAction("🛡️ 断流秒级自愈")
        self.act_tray_heal_toggle.setCheckable(True)
        self.act_tray_heal_toggle.setChecked(self.pipeline_card.chk_auto_heal.isChecked())
        self.act_tray_heal_toggle.triggered.connect(lambda chk: self.pipeline_card.chk_auto_heal.setChecked(chk))

        tray_menu.addSeparator()
        act_quit = tray_menu.addAction("退出应用")
        act_quit.triggered.connect(self._force_quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
        self._tray_balloon_shown = False

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self._show_window()

    def _show_window(self):
        self.showNormal()
        self.activateWindow()

    def _force_quit(self):
        if hasattr(self, 'controller') and self.controller:
            self.save_all_ui_settings()
            self.controller.save_config(self.controller.state.get_snapshot())
            self.controller.log("💾 正在退出并保存所有状态...")
        QApplication.quit()

    def _bind_auto_heal_signals(self):
        self.controller.auto_heal_status_updated.connect(self._on_auto_heal_status_updated)
        self.controller.auto_heal_event_triggered.connect(self._on_auto_heal_event_triggered)

    def _on_auto_heal_status_updated(self, status: dict):
        if not status:
            return
        healed_count = status.get("healed_count", 0)
        enabled = status.get("enabled", True)
        act_node = status.get("active_node", "")
        nohk_node = status.get("active_nohk_node", "")

        def _fmt(n):
            if not n:
                return "无"
            return n if len(n) <= 14 else n[:12] + ".."

        pc = self.pipeline_card
        yc_count = status.get("yellow_cards_count", 0)
        yc_str = f" | 🟨预警: {yc_count}" if yc_count > 0 else ""
        if not enabled:
            pc.lbl_auto_heal_status.setText(f"⏸ 自愈已暂停")
            pc.lbl_auto_heal_status.setStyleSheet("color: #94a3b8; font-weight: bold;")
        else:
            pc.lbl_auto_heal_status.setText(f"🟢 链路守卫中 (全量: {_fmt(act_node)} | 非港: {_fmt(nohk_node)} | 自愈: {healed_count}次{yc_str})")
            pc.lbl_auto_heal_status.setStyleSheet("color: #34d399; font-weight: bold;")

        if hasattr(self, "tray_icon") and self.tray_icon:
            yc_tip = f"\n黄牌预警: {yc_count}个" if yc_count > 0 else ""
            self.tray_icon.setToolTip(f"Clash Verge 节点助手\n全量: {act_node}\n非港AI: {nohk_node}\n今日自愈: {healed_count}次{yc_tip}")

    def _on_auto_heal_event_triggered(self, dead_node: str, backup_node: str, info: dict):
        grp = info.get("group", "⚡ 自动选择")
        is_non_hk = info.get("is_non_hk", False)
        cost_ms = info.get("cost_ms", 0)
        evicted = info.get("evicted", 0)
        reason = info.get("reason", "检测到链路断流异常")
        tag = "非港AI" if is_non_hk else "全量出口"
        title = f"🛡️ 【{tag}】秒级自愈已触发"
        tip = "\n✨ 严格继承非港限制，Gemini/反重力不受影响" if is_non_hk else ""
        msg = (
            f"触发原因：{reason}\n"
            f"目标策略组：【{grp}】\n"
            f"已将坏死节点 【{dead_node}】 顺移至 【{backup_node}】\n"
            f"(耗时 {cost_ms}ms，清理 {evicted} 条僵尸连接){tip}"
        )
        if hasattr(self, "tray_icon") and self.tray_icon:
            self.tray_icon.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Information, 5000)

        # 同步在主程序控制台日志中显式输出高亮审计条目
        self.controller.log(
            f"🔔 [自愈通知] 触发原因: {reason} | 策略组: 【{grp}】 | 节点切换: 【{dead_node}】 -> 【{backup_node}】 (耗时: {cost_ms}ms)"
        )

    def _on_auto_heal_toggled(self, state: int):
        enabled = bool(state == 2 or (hasattr(Qt, "CheckState") and state == Qt.CheckState.Checked.value) or bool(state))
        self.controller.toggle_auto_heal(enabled)
        if hasattr(self, "act_tray_heal_toggle"):
            self.act_tray_heal_toggle.setChecked(enabled)
        self.controller.save_config({"auto_heal_enabled": enabled})

    def _on_diagnose_link_clicked(self):
        res = self.controller.diagnose_current_link()
        node = res.get("active_node", "未知")
        nohk_node = res.get("active_nohk_node", "未知")
        delay = res.get("delay_ms", "超时")
        nohk_delay = res.get("delay_nohk_ms", "超时")
        healthy = res.get("is_healthy", False)
        conns = res.get("total_connections", 0)
        status_str = "双通道全部正常畅通" if healthy else "检测到部分通道异常"
        MessageBox(
            "双通道链路深度诊断结果",
            f"⚡ 全量出口 (常规/视频): {node}\n"
            f"   延迟测定: {delay} ms\n\n"
            f"⚡ 非港出口 (Gemini/反重力/AI): {nohk_node}\n"
            f"   延迟测定: {nohk_delay} ms\n\n"
            f"综合状态: {status_str}\n"
            f"活跃连接: {conns} 条\n"
            f"今日自愈: {res.get('healed_count', 0)} 次",
            self
        ).exec()

    def _update_auto_heal_params(self):
        pc = self.pipeline_card
        try:
            th = float(pc.auto_heal_threshold.text().strip())
        except ValueError:
            th = 3.5
        try:
            cd = float(pc.auto_heal_cooldown.text().strip()) * 60.0
        except ValueError:
            cd = 900.0
        if hasattr(self.controller, "auto_heal_watcher"):
            self.controller.auto_heal_watcher.update_config(
                blackhole_timeout=th,
                cooldown_duration=cd
            )
        self.controller.save_config({
            "auto_heal_threshold": th,
            "auto_heal_cooldown": cd / 60.0
        })

    def _on_tray_pref_changed(self, state: int):
        enabled = bool(state == 2 or (hasattr(Qt, "CheckState") and state == Qt.CheckState.Checked.value) or bool(state))
        self.controller.save_config({"minimize_to_tray_enabled": enabled})

    # ==================== 界面配置自动采集、实时持久化与记忆回显 ====================

    def collect_all_ui_config(self) -> dict:
        """
        全面采集主界面所有输入框、复选框、调度与订阅的最新设置字典
        """
        pc = getattr(self, "pipeline_card", None)
        pf = getattr(self, "page_favorites", None)
        pv = getattr(self, "page_verified", None)
        cfg = {}

        if pc:
            cfg.update({
                "max_delay": pc.max_delay.text().strip(),
                "min_speed": pc.min_speed.text().strip(),
                "target_count": pc.target_count.text().strip(),
                "test_rounds": pc.test_rounds.text().strip(),
                "test_timeout": pc.test_timeout.text().strip(),
                "speed_duration": pc.speed_duration.text().strip(),
                "blacklist_threshold": pc.blacklist_threshold.text().strip(),
                "speed_bl_threshold": pc.speed_bl_threshold.text().strip(),
                "speed_bl_rounds": pc.speed_bl_rounds.text().strip(),
                "jitter_min_delay": pc.jitter_min_delay.text().strip(),
                "jitter_up_threshold": pc.jitter_up_threshold.text().strip(),
                "test_url": pc.test_url.text().strip(),
                "speed_url": pc.speed_url.text().strip(),
                "schedule_enabled": pc.chk_schedule.isChecked(),
                "schedule_interval": pc.schedule_interval.text().strip(),
                "schedule_times": pc.schedule_times.text().strip(),
                "group_interval": pc.group_interval.text().strip(),
                "group_tolerance": pc.group_tolerance.text().strip(),
                "star_group_interval": pc.star_group_interval.text().strip(),
                "star_group_tolerance": pc.star_group_tolerance.text().strip(),
                "cf_worker_enabled": getattr(pc, "chk_worker_enabled", None) and pc.chk_worker_enabled.isChecked(),
                "worker_url": pc.worker_url.text().strip(),
                "worker_token": pc.worker_token.text().strip(),
                "clash_port": pc.clash_port.text().strip(),
                "clash_secret": pc.clash_secret.text().strip(),
                "auto_heal_enabled": pc.chk_auto_heal.isChecked(),
                "auto_heal_threshold": pc.auto_heal_threshold.text().strip(),
                "auto_heal_cooldown": pc.auto_heal_cooldown.text().strip(),
                "minimize_to_tray_enabled": pc.chk_minimize_to_tray.isChecked(),
            })

        if pf:
            cfg.update({
                "fav_max_delay": pf.fav_max_delay.text().strip(),
                "fav_min_speed": pf.fav_min_speed.text().strip(),
                "fav_rounds": pf.fav_rounds.text().strip(),
                "fav_speed_duration": pf.fav_speed_duration.text().strip(),
                "fav_jitter_min_delay": pf.fav_jitter_min.text().strip(),
                "fav_jitter_up_threshold": pf.fav_jitter_up.text().strip(),
                "fav_schedule_enabled": pf.chk_fav_schedule.isChecked(),
                "fav_schedule_interval": pf.fav_sched_interval.text().strip(),
                "fav_target_hk_count": pf.fav_target_hk.text().strip(),
                "fav_target_nohk_count": pf.fav_target_nohk.text().strip(),
                "fav_quota_early_stop": pf.chk_fav_early_stop.isChecked(),
                "fav_fallback_enabled": pf.chk_fav_fallback.isChecked(),
            })

        if pv:
            cfg.update({
                "incubate_hours": pv.incubate_hours.text().strip(),
                "incubate_passes": pv.incubate_passes.text().strip(),
            })

        if hasattr(self, "top_bar") and hasattr(self.top_bar, "sub_combo"):
            current_sub = self.top_bar.sub_combo.currentText().strip()
            if current_sub:
                cfg["last_selected_yaml"] = current_sub
                cfg["active_profile"] = current_sub

        return cfg

    def save_all_ui_settings(self):
        """
        统一存盘调度：采集所有控件数据并原子化持久化到磁盘
        """
        if hasattr(self, "controller") and self.controller:
            ui_cfg = self.collect_all_ui_config()
            self.controller.save_config(ui_cfg)

    def _bind_auto_save_signals(self):
        """
        为所有参数输入框 (editingFinished)、复选框 (stateChanged) 及订阅切换绑定静默实时自动存盘
        """
        pc = getattr(self, "pipeline_card", None)
        pf = getattr(self, "page_favorites", None)
        pv = getattr(self, "page_verified", None)

        if pc:
            pc_line_edits = [
                getattr(pc, "max_delay", None),
                getattr(pc, "min_speed", None),
                getattr(pc, "target_count", None),
                getattr(pc, "test_rounds", None),
                getattr(pc, "test_timeout", None),
                getattr(pc, "speed_duration", None),
                getattr(pc, "blacklist_threshold", None),
                getattr(pc, "speed_bl_threshold", None),
                getattr(pc, "speed_bl_rounds", None),
                getattr(pc, "jitter_min_delay", None),
                getattr(pc, "jitter_up_threshold", None),
                getattr(pc, "test_url", None),
                getattr(pc, "speed_url", None),
                getattr(pc, "schedule_interval", None),
                getattr(pc, "schedule_times", None),
                getattr(pc, "group_interval", None),
                getattr(pc, "group_tolerance", None),
                getattr(pc, "star_group_interval", None),
                getattr(pc, "star_group_tolerance", None),
                getattr(pc, "worker_url", None),
                getattr(pc, "worker_token", None),
                getattr(pc, "clash_port", None),
                getattr(pc, "clash_secret", None),
                getattr(pc, "auto_heal_threshold", None),
                getattr(pc, "auto_heal_cooldown", None),
            ]
            for le in pc_line_edits:
                if le and hasattr(le, "editingFinished"):
                    le.editingFinished.connect(self.save_all_ui_settings)

            pc_checkboxes = [
                getattr(pc, "chk_schedule", None),
                getattr(pc, "chk_worker_enabled", None),
                getattr(pc, "chk_auto_heal", None),
                getattr(pc, "chk_minimize_to_tray", None),
            ]
            for cb in pc_checkboxes:
                if cb and hasattr(cb, "stateChanged"):
                    cb.stateChanged.connect(lambda _st=None: self.save_all_ui_settings())

        if pf:
            pf_line_edits = [
                getattr(pf, "fav_max_delay", None),
                getattr(pf, "fav_min_speed", None),
                getattr(pf, "fav_rounds", None),
                getattr(pf, "fav_speed_duration", None),
                getattr(pf, "fav_jitter_min", None),
                getattr(pf, "fav_jitter_up", None),
                getattr(pf, "fav_sched_interval", None),
                getattr(pf, "fav_target_hk", None),
                getattr(pf, "fav_target_nohk", None),
            ]
            for le in pf_line_edits:
                if le and hasattr(le, "editingFinished"):
                    le.editingFinished.connect(self.save_all_ui_settings)

            pf_checkboxes = [
                getattr(pf, "chk_fav_schedule", None),
                getattr(pf, "chk_fav_early_stop", None),
                getattr(pf, "chk_fav_fallback", None),
            ]
            for cb in pf_checkboxes:
                if cb and hasattr(cb, "stateChanged"):
                    cb.stateChanged.connect(lambda _st=None: self.save_all_ui_settings())

        if pv:
            pv_line_edits = [
                getattr(pv, "incubate_hours", None),
                getattr(pv, "incubate_passes", None),
            ]
            for le in pv_line_edits:
                if le and hasattr(le, "editingFinished"):
                    le.editingFinished.connect(self.save_all_ui_settings)

        if hasattr(self, "top_bar") and hasattr(self.top_bar, "sub_combo"):
            self.top_bar.sub_combo.currentTextChanged.connect(lambda _txt=None: self.save_all_ui_settings())

    def restore_ui_config(self, cfg: dict):
        """
        根据磁盘持久化配置恢复界面各项输入框、复选框与选中的订阅
        """
        if not cfg or not isinstance(cfg, dict):
            return

        pc = self.pipeline_card
        # 1. 恢复 PipelineCard 配置
        if "max_delay" in cfg:
            pc.max_delay.setText(str(cfg["max_delay"]))
        if "min_speed" in cfg:
            pc.min_speed.setText(str(cfg["min_speed"]))
        if "target_count" in cfg:
            pc.target_count.setText(str(cfg["target_count"]))
        if "test_rounds" in cfg:
            pc.test_rounds.setText(str(cfg["test_rounds"]))
        if "test_timeout" in cfg:
            pc.test_timeout.setText(str(cfg["test_timeout"]))
        if "speed_duration" in cfg:
            pc.speed_duration.setText(str(cfg["speed_duration"]))
        if "blacklist_threshold" in cfg:
            pc.blacklist_threshold.setText(str(cfg["blacklist_threshold"]))
        if "speed_bl_threshold" in cfg:
            pc.speed_bl_threshold.setText(str(cfg["speed_bl_threshold"]))
        if "speed_bl_rounds" in cfg:
            pc.speed_bl_rounds.setText(str(cfg["speed_bl_rounds"]))
        if "jitter_min_delay" in cfg:
            pc.jitter_min_delay.setText(str(cfg["jitter_min_delay"]))
        if "jitter_up_threshold" in cfg:
            pc.jitter_up_threshold.setText(str(cfg["jitter_up_threshold"]))
        if "test_url" in cfg:
            pc.test_url.setText(str(cfg["test_url"]))
        if "speed_url" in cfg:
            pc.speed_url.setText(str(cfg["speed_url"]))
        if "schedule_enabled" in cfg:
            pc.chk_schedule.setChecked(bool(cfg["schedule_enabled"]))
        if "schedule_interval" in cfg:
            pc.schedule_interval.setText(str(cfg["schedule_interval"]))
        if "schedule_times" in cfg:
            pc.schedule_times.setText(str(cfg["schedule_times"]))
        if "group_interval" in cfg:
            pc.group_interval.setText(str(cfg["group_interval"]))
        if "group_tolerance" in cfg:
            pc.group_tolerance.setText(str(cfg["group_tolerance"]))
        if "star_group_interval" in cfg:
            pc.star_group_interval.setText(str(cfg["star_group_interval"]))
        if "star_group_tolerance" in cfg:
            pc.star_group_tolerance.setText(str(cfg["star_group_tolerance"]))
        if "cf_worker_enabled" in cfg and hasattr(pc, "chk_worker_enabled"):
            pc.chk_worker_enabled.setChecked(bool(cfg["cf_worker_enabled"]))

        worker_url_val = cfg.get("worker_url") or cfg.get("cf_worker_url", "")
        if worker_url_val:
            pc.worker_url.setText(str(worker_url_val))
        worker_token_val = cfg.get("worker_token") or cfg.get("cf_worker_token", "")
        if worker_token_val:
            pc.worker_token.setText(str(worker_token_val))

        # 2. 恢复 PageFavorites 配置
        pf = self.page_favorites
        if "fav_max_delay" in cfg:
            pf.fav_max_delay.setText(str(cfg["fav_max_delay"]))
        if "fav_min_speed" in cfg:
            pf.fav_min_speed.setText(str(cfg["fav_min_speed"]))
        if "fav_rounds" in cfg:
            pf.fav_rounds.setText(str(cfg["fav_rounds"]))
        if "fav_speed_duration" in cfg:
            pf.fav_speed_duration.setText(str(cfg["fav_speed_duration"]))
        if "fav_jitter_min_delay" in cfg:
            pf.fav_jitter_min.setText(str(cfg["fav_jitter_min_delay"]))
        if "fav_jitter_up_threshold" in cfg:
            pf.fav_jitter_up.setText(str(cfg["fav_jitter_up_threshold"]))
        if "fav_schedule_enabled" in cfg:
            pf.chk_fav_schedule.setChecked(bool(cfg["fav_schedule_enabled"]))
        if "fav_schedule_interval" in cfg:
            pf.fav_sched_interval.setText(str(cfg["fav_schedule_interval"]))
        if "fav_target_hk_count" in cfg:
            pf.fav_target_hk.setText(str(cfg["fav_target_hk_count"]))
        if "fav_target_nohk_count" in cfg:
            pf.fav_target_nohk.setText(str(cfg["fav_target_nohk_count"]))
        if "fav_quota_early_stop" in cfg:
            pf.chk_fav_early_stop.setChecked(bool(cfg["fav_quota_early_stop"]))
        if "fav_fallback_enabled" in cfg:
            pf.chk_fav_fallback.setChecked(bool(cfg["fav_fallback_enabled"]))

        # 3. 恢复 PageVerified 配置
        pv = self.page_verified
        if "incubate_hours" in cfg:
            pv.incubate_hours.setText(str(cfg["incubate_hours"]))
        if "incubate_passes" in cfg:
            pv.incubate_passes.setText(str(cfg["incubate_passes"]))

        secret_val = cfg.get("clash_secret", "").strip() if cfg else ""
        if not secret_val:
            secret_val = "set-your-secret"
        pc.clash_secret.setText(secret_val)

        port_val = cfg.get("clash_port", "") if cfg else ""
        if not port_val:
            port_val = "9097"
        pc.clash_port.setText(str(port_val))

        # 4. 订阅选择与触发加载 (优先记忆上次选中的 profile/yaml)
        saved_sub = cfg.get("last_selected_yaml") or cfg.get("active_profile") or "Rw0nNFlVIbnA.yaml"
        all_items = [self.top_bar.sub_combo.itemText(i) for i in range(self.top_bar.sub_combo.count())]
        active_sub = saved_sub if saved_sub in all_items else (all_items[0] if all_items else "")
        if active_sub:
            self.top_bar.sub_combo.setCurrentText(active_sub)
            self.controller.load_nodes_from_profile(active_sub)
            setattr(self.controller.state, "active_profile", active_sub)
            self.controller.data_changed.emit()

        self._on_reconnect_clicked()

        # 5. 恢复自愈与托盘设置
        if "auto_heal_enabled" in cfg:
            pc.chk_auto_heal.setChecked(bool(cfg["auto_heal_enabled"]))
            self.controller.toggle_auto_heal(bool(cfg["auto_heal_enabled"]))
        if "auto_heal_threshold" in cfg:
            pc.auto_heal_threshold.setText(str(cfg["auto_heal_threshold"]))
        if "auto_heal_cooldown" in cfg:
            pc.auto_heal_cooldown.setText(str(cfg["auto_heal_cooldown"]))
        if "minimize_to_tray_enabled" in cfg:
            pc.chk_minimize_to_tray.setChecked(bool(cfg["minimize_to_tray_enabled"]))
        self._update_auto_heal_params()

    def closeEvent(self, event):
        pc = self.pipeline_card
        if (
            hasattr(pc, "chk_minimize_to_tray")
            and pc.chk_minimize_to_tray.isChecked()
            and hasattr(self, "tray_icon")
            and self.tray_icon.isVisible()
        ):
            event.ignore()
            self.hide()
            if not getattr(self, "_tray_balloon_shown", False):
                self.tray_icon.showMessage(
                    "Clash Verge 节点管理助手",
                    "助手已最小化至系统托盘，后台保持秒级自愈与定时优选守护中...",
                    QSystemTrayIcon.MessageIcon.Information,
                    3000
                )
                self._tray_balloon_shown = True
            return

        # 真正退出前强制存盘
        if hasattr(self, 'controller') and self.controller:
            self.save_all_ui_settings()
            self.controller.save_config(self.controller.state.get_snapshot())
            self.controller.log("💾 退出前已自动保存所有数据至 config...")
        super().closeEvent(event)
```

## File: `gui_fluent/components/__init__.py`

```python
"""
Fluent UI 通用界面组件模块
"""
from gui_fluent.components.top_bar import TopBar
from gui_fluent.components.log_panel import LogPanel
from gui_fluent.components.bottom_action_bar import BottomActionBar
from gui_fluent.components.pipeline_card import PipelineCard

__all__ = ["TopBar", "LogPanel", "BottomActionBar", "PipelineCard"]

```

## File: `gui_fluent/components/bottom_action_bar.py`

```python
"""
底部快捷操作栏组件
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QHBoxLayout
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QHBoxLayout

from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
)


class BottomActionBar(QWidget):
    """
    底部高频操作栏：提供节点晋升、拉黑、恢复与配置热刷新的快捷动作入口
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(8)

        # 常用操作按钮
        self.btn_fav = PushButton("⭐ 设为优质", self)
        layout.addWidget(self.btn_fav)

        self.btn_promote = PushButton("🏆 晋升为典藏", self)
        layout.addWidget(self.btn_promote)

        self.btn_delay_black = PushButton("🚫 延迟拉黑", self)
        layout.addWidget(self.btn_delay_black)

        self.btn_speed_black = PushButton("🐌 低速拉黑", self)
        layout.addWidget(self.btn_speed_black)

        self.btn_unblack = PushButton("↩ 移出黑名单", self)
        layout.addWidget(self.btn_unblack)

        self.btn_clear_bl = PushButton("🧹 一键清空所有黑名单", self)
        layout.addWidget(self.btn_clear_bl)

        self.btn_rescore = PushButton("🏆 重新计分与晋升", self)
        layout.addWidget(self.btn_rescore)

        # 弹性空白隔断
        layout.addStretch(1)

        # 右侧重点操作按钮
        self.btn_hotkey_sync = PrimaryPushButton("⚡ 手动写入并热键刷新 Verge", self)
        layout.addWidget(self.btn_hotkey_sync)

        self.setStyleSheet("""
            BottomActionBar {
                background-color: rgba(30, 41, 59, 0.45);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
```

## File: `gui_fluent/components/log_panel.py`

```python
"""
实时日志面板组件
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
else:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    BodyLabel,
    PlainTextEdit,
    PushButton,
)


class LogPanel(QWidget):
    """
    底部日志监控面板：支持线程安全追加日志文本与一键清屏
    """
    _append_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self._append_signal.connect(self._do_append_log)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(4)

        # 顶部工具条：标题 + 右对齐清屏按钮
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_title = BodyLabel("📜 操作动态与实时运行日志:", self)
        self.lbl_title.setStyleSheet("font-weight: bold; color: #38bdf8;")
        top_layout.addWidget(self.lbl_title)

        top_layout.addStretch(1)

        self.btn_clear = PushButton("清屏", self)
        self.btn_clear.setFixedWidth(64)
        self.btn_clear.clicked.connect(self.clear_log)
        top_layout.addWidget(self.btn_clear)
        layout.addLayout(top_layout)

        # 主体文本区域
        self.text_edit = PlainTextEdit(self)
        self.text_edit.setReadOnly(True)
        font = QFont("Consolas", 9)
        self.text_edit.setFont(font)
        self.text_edit.setStyleSheet("""
            PlainTextEdit {
                background-color: #0f111a;
                color: #e2e8f0;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.text_edit)

        self.setStyleSheet("""
            LogPanel {
                background-color: rgba(30, 41, 59, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
            }
        """)

    def append_log(self, text: str):
        """
        公开方法：线程安全追加日志
        """
        self._append_signal.emit(str(text))

    def _do_append_log(self, text: str):
        self.text_edit.appendPlainText(text)
        bar = self.text_edit.verticalScrollBar()
        if bar:
            bar.setValue(bar.maximum())

    def clear_log(self):
        self.text_edit.clear()
```

## File: `gui_fluent/components/pipeline_card.py`

```python
"""
流水线控制卡组件 (PipelineCard)
集中配置全自动优选门槛、拉黑规则、测速源、定时调度与内核连接参数
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit
    PASSWORD_ECHO_MODE = QLineEdit.Password
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit
    PASSWORD_ECHO_MODE = QLineEdit.EchoMode.Password

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CheckBox,
    LineEdit,
    PushButton,
    PrimaryPushButton,
)


class PipelineCard(QWidget):
    """
    流水线控制卡：提供 5 行紧凑参数配置与操作控制
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("PipelineCard")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ──────── 第 1 行：全局优选门槛 ────────
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(8)

        lbl_r1 = BodyLabel("⚡ 全局优选门槛:", self)
        lbl_r1.setStyleSheet("color: #38bdf8; font-weight: bold;")
        row1.addWidget(lbl_r1)

        row1.addWidget(CaptionLabel("最低延迟(≤ ms):", self))
        self.max_delay = LineEdit(self)
        self.max_delay.setObjectName("max_delay")
        self.max_delay.setText("100")
        self.max_delay.setFixedWidth(55)
        self.max_delay.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.max_delay)

        row1.addWidget(CaptionLabel("优质下行(≥ MB/s):", self))
        self.min_speed = LineEdit(self)
        self.min_speed.setObjectName("min_speed")
        self.min_speed.setText("5.0")
        self.min_speed.setFixedWidth(50)
        self.min_speed.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.min_speed)

        lbl_target = CaptionLabel("达标目标(留空全测):", self)
        lbl_target.setStyleSheet("color: #fbbf24;")
        row1.addWidget(lbl_target)

        self.target_count = LineEdit(self)
        self.target_count.setObjectName("target_count")
        self.target_count.setText("")
        self.target_count.setFixedWidth(45)
        self.target_count.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.target_count)

        row1.addWidget(CaptionLabel("轮数:", self))
        self.test_rounds = LineEdit(self)
        self.test_rounds.setObjectName("test_rounds")
        self.test_rounds.setText("4")
        self.test_rounds.setFixedWidth(36)
        self.test_rounds.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.test_rounds)

        row1.addWidget(CaptionLabel("超时(ms):", self))
        self.test_timeout = LineEdit(self)
        self.test_timeout.setObjectName("test_timeout")
        self.test_timeout.setText("1500")
        self.test_timeout.setFixedWidth(50)
        self.test_timeout.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.test_timeout)

        row1.addWidget(CaptionLabel("采样:", self))
        self.speed_duration = LineEdit(self)
        self.speed_duration.setObjectName("speed_duration")
        self.speed_duration.setText("3")
        self.speed_duration.setFixedWidth(36)
        self.speed_duration.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.speed_duration)
        row1.addWidget(CaptionLabel("秒", self))

        self.btn_run_pipeline = PrimaryPushButton("🚀 启动一整套全自动优选与热键生效", self)
        self.btn_run_pipeline.setObjectName("btn_run_pipeline")
        self.btn_run_pipeline.setStyleSheet("""
            PrimaryPushButton {
                background-color: #10b981;
                border: 1px solid #10b981;
            }
            PrimaryPushButton:hover {
                background-color: #059669;
                border: 1px solid #059669;
            }
            PrimaryPushButton:pressed {
                background-color: #047857;
                border: 1px solid #047857;
            }
        """)
        row1.addWidget(self.btn_run_pipeline)

        self.btn_stop_pipeline = PushButton("⏹ 终止任务", self)
        self.btn_stop_pipeline.setObjectName("btn_stop_pipeline")
        self.btn_stop_pipeline.setEnabled(False)
        row1.addWidget(self.btn_stop_pipeline)

        layout.addLayout(row1)

        # ──────── 第 2 行：自动拉黑规则 ────────
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(8)

        lbl_r2 = BodyLabel("🚫 自动拉黑规则:", self)
        lbl_r2.setStyleSheet("color: #f87171; font-weight: bold;")
        row2.addWidget(lbl_r2)

        row2.addWidget(CaptionLabel("延迟拉黑(≥ ms):", self))
        self.blacklist_threshold = LineEdit(self)
        self.blacklist_threshold.setObjectName("blacklist_threshold")
        self.blacklist_threshold.setText("130")
        self.blacklist_threshold.setFixedWidth(55)
        self.blacklist_threshold.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.blacklist_threshold)

        row2.addWidget(CaptionLabel("低速拉黑(< MB/s):", self))
        self.speed_bl_threshold = LineEdit(self)
        self.speed_bl_threshold.setObjectName("speed_bl_threshold")
        self.speed_bl_threshold.setText("1.0")
        self.speed_bl_threshold.setFixedWidth(50)
        self.speed_bl_threshold.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.speed_bl_threshold)

        row2.addWidget(CaptionLabel("连续低速次数:", self))
        self.speed_bl_rounds = LineEdit(self)
        self.speed_bl_rounds.setObjectName("speed_bl_rounds")
        self.speed_bl_rounds.setText("4")
        self.speed_bl_rounds.setFixedWidth(36)
        self.speed_bl_rounds.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.speed_bl_rounds)
        row2.addWidget(CaptionLabel("次", self))

        row2.addWidget(CaptionLabel("抖动基准(≥ ms):", self))
        self.jitter_min_delay = LineEdit(self)
        self.jitter_min_delay.setObjectName("jitter_min_delay")
        self.jitter_min_delay.setText("80")
        self.jitter_min_delay.setFixedWidth(45)
        self.jitter_min_delay.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.jitter_min_delay)

        row2.addWidget(CaptionLabel("向上抖动(≥ ms):", self))
        self.jitter_up_threshold = LineEdit(self)
        self.jitter_up_threshold.setObjectName("jitter_up_threshold")
        self.jitter_up_threshold.setText("20")
        self.jitter_up_threshold.setFixedWidth(45)
        self.jitter_up_threshold.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.jitter_up_threshold)

        row2.addStretch(1)
        layout.addLayout(row2)

        # ──────── 第 3 行：测速 URL 与策略组配置 ────────
        row3 = QHBoxLayout()
        row3.setContentsMargins(0, 0, 0, 0)
        row3.setSpacing(8)

        lbl_test_url = CaptionLabel("延迟源:", self)
        lbl_test_url.setStyleSheet("color: #8d98af;")
        row3.addWidget(lbl_test_url)

        self.test_url = LineEdit(self)
        self.test_url.setObjectName("test_url")
        self.test_url.setText("http://www.msftconnecttest.com/connecttest.txt")
        self.test_url.setFixedWidth(220)
        row3.addWidget(self.test_url)

        lbl_speed_url = CaptionLabel("带宽源:", self)
        lbl_speed_url.setStyleSheet("color: #8d98af;")
        row3.addWidget(lbl_speed_url)

        self.speed_url = LineEdit(self)
        self.speed_url.setObjectName("speed_url")
        self.speed_url.setText("https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip")
        self.speed_url.setFixedWidth(220)
        row3.addWidget(self.speed_url)

        row3.addStretch(1)
        layout.addLayout(row3)

        # ──────── 第 4 行：定时调度 + 策略组间隔 ────────
        row4 = QHBoxLayout()
        row4.setContentsMargins(0, 0, 0, 0)
        row4.setSpacing(8)

        self.chk_schedule = CheckBox("⏰ 启用全局定时优选", self)
        self.chk_schedule.setObjectName("chk_schedule")
        row4.addWidget(self.chk_schedule)

        row4.addWidget(CaptionLabel("循环间隔(分钟):", self))
        self.schedule_interval = LineEdit(self)
        self.schedule_interval.setObjectName("schedule_interval")
        self.schedule_interval.setText("120")
        self.schedule_interval.setFixedWidth(45)
        self.schedule_interval.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.schedule_interval)

        row4.addWidget(CaptionLabel("固定时刻(HH:MM):", self))
        self.schedule_times = LineEdit(self)
        self.schedule_times.setObjectName("schedule_times")
        self.schedule_times.setText("08:00, 13:00, 20:00")
        self.schedule_times.setFixedWidth(140)
        self.schedule_times.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.schedule_times)

        self.lbl_sched_status = CaptionLabel("(全局定时未启动)", self)
        self.lbl_sched_status.setObjectName("lbl_sched_status")
        self.lbl_sched_status.setStyleSheet("color: #94a3b8;")
        row4.addWidget(self.lbl_sched_status)

        row4.addStretch(1)

        lbl_grp = BodyLabel("⚙️ 策略组:", self)
        lbl_grp.setStyleSheet("color: #a78bfa; font-weight: bold;")
        row4.addWidget(lbl_grp)

        row4.addWidget(CaptionLabel("常规间隔(s):", self))
        self.group_interval = LineEdit(self)
        self.group_interval.setObjectName("group_interval")
        self.group_interval.setText("300")
        self.group_interval.setFixedWidth(45)
        self.group_interval.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.group_interval)

        row4.addWidget(CaptionLabel("容差(ms):", self))
        self.group_tolerance = LineEdit(self)
        self.group_tolerance.setObjectName("group_tolerance")
        self.group_tolerance.setText("20")
        self.group_tolerance.setFixedWidth(36)
        self.group_tolerance.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.group_tolerance)

        row4.addWidget(CaptionLabel("典藏间隔(s):", self))
        self.star_group_interval = LineEdit(self)
        self.star_group_interval.setObjectName("star_group_interval")
        self.star_group_interval.setText("300")
        self.star_group_interval.setFixedWidth(45)
        self.star_group_interval.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.star_group_interval)

        row4.addWidget(CaptionLabel("容差(ms):", self))
        self.star_group_tolerance = LineEdit(self)
        self.star_group_tolerance.setObjectName("star_group_tolerance")
        self.star_group_tolerance.setText("20")
        self.star_group_tolerance.setFixedWidth(36)
        self.star_group_tolerance.setAlignment(Qt.AlignCenter)
        row4.addWidget(self.star_group_tolerance)

        self.btn_save_group = PushButton("💾 保存并热更", self)
        self.btn_save_group.setObjectName("btn_save_group")
        row4.addWidget(self.btn_save_group)

        layout.addLayout(row4)

        # ──────── 第 5 行：Worker 云端同步 + Clash 连接参数 ────────
        row5 = QHBoxLayout()
        row5.setContentsMargins(0, 0, 0, 0)
        row5.setSpacing(8)

        self.chk_worker_enabled = CheckBox("☁️ 自动推送 Worker", self)
        self.chk_worker_enabled.setObjectName("chk_worker_enabled")
        row5.addWidget(self.chk_worker_enabled)

        row5.addWidget(CaptionLabel("根地址:", self))
        self.worker_url = LineEdit(self)
        self.worker_url.setObjectName("worker_url")
        self.worker_url.setText("https://cf-nodes.douyutvshow.workers.dev/")
        self.worker_url.setFixedWidth(200)
        row5.addWidget(self.worker_url)

        row5.addWidget(CaptionLabel("密钥:", self))
        self.worker_token = LineEdit(self)
        self.worker_token.setObjectName("worker_token")
        self.worker_token.setText("MySecretToken2026")
        self.worker_token.setFixedWidth(120)
        self.worker_token.setEchoMode(PASSWORD_ECHO_MODE)
        row5.addWidget(self.worker_token)

        self.btn_test_worker = PushButton("🧪 测试通道", self)
        self.btn_test_worker.setObjectName("btn_test_worker")
        row5.addWidget(self.btn_test_worker)

        self.btn_sync_auto = PushButton("☁️ 同步auto.txt", self)
        self.btn_sync_auto.setObjectName("btn_sync_auto")
        row5.addWidget(self.btn_sync_auto)

        row5.addStretch(1)

        row5.addWidget(CaptionLabel("端口:", self))
        self.clash_port = LineEdit(self)
        self.clash_port.setObjectName("clash_port")
        self.clash_port.setText("9097")
        self.clash_port.setFixedWidth(55)
        self.clash_port.setAlignment(Qt.AlignCenter)
        row5.addWidget(self.clash_port)

        row5.addWidget(CaptionLabel("密钥:", self))
        self.clash_secret = LineEdit(self)
        self.clash_secret.setObjectName("clash_secret")
        self.clash_secret.setText("")
        self.clash_secret.setFixedWidth(100)
        row5.addWidget(self.clash_secret)

        self.btn_reconnect = PushButton("重连", self)
        self.btn_reconnect.setObjectName("btn_reconnect")
        row5.addWidget(self.btn_reconnect)

        row5.addWidget(CaptionLabel("快速过滤:", self))
        self.search_box = LineEdit(self)
        self.search_box.setObjectName("search_box")
        self.search_box.setText("")
        self.search_box.setFixedWidth(130)
        row5.addWidget(self.search_box)

        self.lbl_conn_status = CaptionLabel("● 未连接", self)
        self.lbl_conn_status.setObjectName("lbl_conn_status")
        self.lbl_conn_status.setStyleSheet("color: #fbbf24; font-weight: bold;")
        row5.addWidget(self.lbl_conn_status)

        layout.addLayout(row5)

        # ──────── 第 6 行：链路秒级自愈与托盘常驻 ────────
        row6 = QHBoxLayout()
        row6.setContentsMargins(0, 0, 0, 0)
        row6.setSpacing(8)

        lbl_heal = BodyLabel("🛡️ 链路秒级自愈:", self)
        lbl_heal.setStyleSheet("color: #34d399; font-weight: bold;")
        row6.addWidget(lbl_heal)

        self.chk_auto_heal = CheckBox("启用断流秒级无感自愈", self)
        self.chk_auto_heal.setObjectName("chk_auto_heal")
        self.chk_auto_heal.setChecked(True)
        row6.addWidget(self.chk_auto_heal)

        row6.addWidget(CaptionLabel("黑洞阈值(s):", self))
        self.auto_heal_threshold = LineEdit(self)
        self.auto_heal_threshold.setObjectName("auto_heal_threshold")
        self.auto_heal_threshold.setText("2.0")
        self.auto_heal_threshold.setFixedWidth(40)
        self.auto_heal_threshold.setAlignment(Qt.AlignCenter)
        row6.addWidget(self.auto_heal_threshold)

        row6.addWidget(CaptionLabel("熔断隔离(分):", self))
        self.auto_heal_cooldown = LineEdit(self)
        self.auto_heal_cooldown.setObjectName("auto_heal_cooldown")
        self.auto_heal_cooldown.setText("15")
        self.auto_heal_cooldown.setFixedWidth(36)
        self.auto_heal_cooldown.setAlignment(Qt.AlignCenter)
        row6.addWidget(self.auto_heal_cooldown)

        self.chk_minimize_to_tray = CheckBox("关闭窗口时最小化至托盘静默守护", self)
        self.chk_minimize_to_tray.setObjectName("chk_minimize_to_tray")
        self.chk_minimize_to_tray.setChecked(True)
        row6.addWidget(self.chk_minimize_to_tray)

        self.btn_diagnose_link = PushButton("⚡ 诊断当前链路", self)
        self.btn_diagnose_link.setObjectName("btn_diagnose_link")
        row6.addWidget(self.btn_diagnose_link)

        row6.addStretch(1)

        self.lbl_auto_heal_status = CaptionLabel("🟢 链路守卫中 (今日自愈: 0 次)", self)
        self.lbl_auto_heal_status.setObjectName("lbl_auto_heal_status")
        self.lbl_auto_heal_status.setStyleSheet("color: #34d399; font-weight: bold;")
        row6.addWidget(self.lbl_auto_heal_status)

        layout.addLayout(row6)

        self.setStyleSheet("""
            PipelineCard {
                background-color: rgba(30, 34, 50, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
```

## File: `gui_fluent/components/top_bar.py`

```python
"""
顶部信息栏与快捷工具组组件
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QHBoxLayout
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QHBoxLayout

from qfluentwidgets import (
    BodyLabel,
    ComboBox,
    PushButton,
    CaptionLabel,
)


class TopBar(QWidget):
    """
    顶部信息栏：包含当前订阅选择、内核连接状态、上次更新时间及右侧快捷操作工具组
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(12)

        # 1. 订阅选择下拉框 (本阶段空列表占位)
        self.sub_combo = ComboBox(self)
        self.sub_combo.setPlaceholderText("选择或加载订阅配置文件...")
        self.sub_combo.setMinimumWidth(220)
        layout.addWidget(self.sub_combo)

        # 2. 更新当前订阅按钮
        self.btn_update_sub = PushButton("🔄 更新当前订阅", self)
        layout.addWidget(self.btn_update_sub)

        # 3. 内核连接状态标签 (文字："● 正在连接内核..."，颜色 #fbbf24)
        self.lbl_status = BodyLabel("● 正在连接内核...", self)
        self.lbl_status.setStyleSheet("color: #fbbf24; font-weight: bold;")
        layout.addWidget(self.lbl_status)

        # 4. 上次检测时间标签
        self.lbl_last_check = CaptionLabel("上次检测: 未执行", self)
        self.lbl_last_check.setStyleSheet("color: #94a3b8;")
        layout.addWidget(self.lbl_last_check)

        # 弹性空白隔断
        layout.addStretch(1)

        # 5. 右侧工具按钮组
        self.btn_test_page_colo = PushButton("🌍 测当前页Colo", self)
        layout.addWidget(self.btn_test_page_colo)

        self.btn_sync_kernel_delay = PushButton("🔄 同步内核延迟", self)
        layout.addWidget(self.btn_sync_kernel_delay)

        self.btn_clear_page_colo = PushButton("🧹 清当前页Colo", self)
        layout.addWidget(self.btn_clear_page_colo)

        self.btn_clear_speed_records = PushButton("🗑️ 清空测速记录", self)
        layout.addWidget(self.btn_clear_speed_records)

        self.setStyleSheet("""
            TopBar {
                background-color: rgba(30, 41, 59, 0.45);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 8px;
            }
        """)
```

## File: `gui_fluent/pages/__init__.py`

```python
"""
Fluent UI 各功能页面模块导出
"""
from gui_fluent.pages.page_active import PageActive
from gui_fluent.pages.page_favorites import PageFavorites
from gui_fluent.pages.page_verified import PageVerified
from gui_fluent.pages.page_stars import PageStars
from gui_fluent.pages.page_delay_black import PageDelayBlack
from gui_fluent.pages.page_speed_black import PageSpeedBlack
from gui_fluent.pages.page_cloud_text import PageCloudText

__all__ = [
    "PageActive",
    "PageFavorites",
    "PageVerified",
    "PageStars",
    "PageDelayBlack",
    "PageSpeedBlack",
    "PageCloudText",
]
```

## File: `gui_fluent/pages/page_active.py`

```python
"""
活跃待测页面
完整表格视图，展示聚合去重后的独立端点活跃待测节点
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout
else:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout

from gui_fluent.app_controller import AppController
from gui_fluent.widgets.node_table import NodeTableView


class PageActive(QWidget):
    """
    活跃待测页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageActive")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 核心通用节点表格
        self.table = NodeTableView(self, controller=self.controller, page_type="active")
        layout.addWidget(self.table, 1)

        # 绑定中枢控制器的流水线数据实时更新信号
        self.controller.pipeline_rows_updated.connect(self.table.populate)

        # 绑定全局数据变化信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)
        self.refresh_data()

    def refresh_data(self):
        """
        重新装配活跃待测池数据并刷新表格
        """
        rows = self.controller.get_table_rows("active")
        self.table.populate(rows)


```

## File: `gui_fluent/pages/page_cloud_text.py`

```python
"""
云端文本管理页面 (PageCloudText)
管理 Cloudflare Worker 远端分发的三大核心文本（/auto.txt、/verified.txt、/）
支持独立及批量拉取、在线编辑、格式统计与强推覆盖。
"""
import sys
import time
import threading
import re

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QFrame,
    )
else:
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QFrame,
    )

from qfluentwidgets import (
    TitleLabel,
    SubtitleLabel,
    BodyLabel,
    CaptionLabel,
    PushButton,
    PrimaryPushButton,
    SimpleCardWidget,
    PlainTextEdit,
    MessageBox,
    InfoBar,
    InfoBarPosition,
)
from gui_fluent.app_controller import AppController


class CloudTextCard(SimpleCardWidget):
    """
    单个云端分发文本管理卡片
    """
    fetch_requested = pyqtSignal(str)          # subpath
    push_requested = pyqtSignal(str, str)      # (subpath, text)

    def __init__(self, title: str, subpath: str, desc: str = "", parent=None):
        super().__init__(parent)
        self.subpath = subpath
        self.title_text = title
        self.desc_text = desc
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # 1. 顶部标题栏与独立操作按钮
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        self.title_label = SubtitleLabel(self.title_text, self)
        top_bar.addWidget(self.title_label)
        top_bar.addStretch(1)

        self.btn_fetch = PushButton("📥 拉取", self)
        self.btn_fetch.setToolTip(f"从云端拉取最新的 {self.subpath} 内容")
        self.btn_fetch.clicked.connect(lambda: self.fetch_requested.emit(self.subpath))
        top_bar.addWidget(self.btn_fetch)

        if self.subpath == "/pending.txt":
            self.btn_purge = PushButton("🧹 联动清洗", self)
            self.btn_purge.setToolTip("立即比对黑名单与精选池，从云端待测池中清除所有已淘汰或已入选的节点")
            top_bar.addWidget(self.btn_purge)

        self.btn_push = PrimaryPushButton("📤 强推", self)
        self.btn_push.setToolTip(f"将当前编辑的内容强推覆盖至云端 {self.subpath}")
        self.btn_push.clicked.connect(lambda: self.push_requested.emit(self.subpath, self.get_text()))
        top_bar.addWidget(self.btn_push)

        layout.addLayout(top_bar)

        # 2. 功能说明标签
        if self.desc_text:
            self.desc_label = CaptionLabel(self.desc_text, self)
            self.desc_label.setStyleSheet("color: #94a3b8;")
            layout.addWidget(self.desc_label)

        # 3. 核心大文本编辑器
        self.editor = PlainTextEdit(self)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self.editor.setFont(font)
        self.editor.setPlaceholderText(
            f"IP:Port#备注名\n示例：\n1.1.1.1:443#优质香港 12.5MB/s\n8.8.8.8:443#备选日本 8.2MB/s"
        )
        # 兼容 PyQt5 / PyQt6 的 NoWrap 设置
        if hasattr(PlainTextEdit, "LineWrapMode"):
            self.editor.setLineWrapMode(PlainTextEdit.LineWrapMode.NoWrap)
        elif hasattr(PlainTextEdit, "NoWrap"):
            self.editor.setLineWrapMode(PlainTextEdit.NoWrap)

        self.editor.textChanged.connect(self._update_stats)
        layout.addWidget(self.editor, 1)

        # 4. 底部统计与状态栏
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 0, 0, 0)
        self.lbl_stats = CaptionLabel("共 0 行 | 0 字符", self)
        self.lbl_stats.setStyleSheet("color: #94a3b8;")
        bottom_bar.addWidget(self.lbl_stats)

        bottom_bar.addStretch(1)

        self.lbl_status = CaptionLabel("就绪", self)
        self.lbl_status.setStyleSheet("color: #64748b;")
        bottom_bar.addWidget(self.lbl_status)

        layout.addLayout(bottom_bar)

    def set_text(self, text: str):
        """更新文本内容"""
        self.editor.setPlainText(text or "")
        self._update_stats()

    def get_text(self) -> str:
        """获取当前编辑器文本"""
        return self.editor.toPlainText()

    def set_status(self, status: str, is_error: bool = False):
        """更新状态词"""
        self.lbl_status.setText(status)
        if is_error:
            self.lbl_status.setStyleSheet("color: #ef4444;")
        else:
            self.lbl_status.setStyleSheet("color: #10b981;")

    def set_loading(self, is_loading: bool):
        """切换加载状态"""
        self.btn_fetch.setEnabled(not is_loading)
        self.btn_push.setEnabled(not is_loading)
        if hasattr(self, "btn_purge"):
            self.btn_purge.setEnabled(not is_loading)
        if is_loading:
            self.btn_fetch.setText("⏳ 同步中...")
        else:
            self.btn_fetch.setText("📥 拉取")

    def _update_stats(self):
        """实时统计行数与字符数"""
        text = self.editor.toPlainText()
        non_empty_lines = [l for l in text.splitlines() if l.strip()]
        self.lbl_stats.setText(f"共 {len(non_empty_lines)} 行 | {len(text)} 字符")



class PageCloudText(QWidget):
    """
    云端文本页面：管理向远端 Cloudflare Worker 自动推送/拉取的三个核心分发文本
    （/auto.txt、/verified.txt、/）
    """
    fetch_done_signal = pyqtSignal(str, bool, str)   # (subpath, success, content_or_err)
    push_done_signal = pyqtSignal(str, bool, str)    # (subpath, success, message)

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageCloudText")
        self.cards = {}
        self._initial_loaded = False

        self.init_ui()
        self._connect_signals()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(14)

        # 1. 顶部 Header 区域
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        self.title_label = TitleLabel("☁️ 云端文本管理", self)
        title_box.addWidget(self.title_label)

        self.desc_label = BodyLabel(
            "查看与编辑 Cloudflare Worker 远端分发的三大核心文本（优质精选 /auto.txt、沉淀孵化 /verified.txt、典藏常青 /）。支持在线双向同步与手动强推覆盖。",
            self,
        )
        self.desc_label.setStyleSheet("color: #94a3b8;")
        title_box.addWidget(self.desc_label)
        header_layout.addLayout(title_box, 1)

        # 全局操作按钮组
        self.btn_fetch_all = PushButton("📥 一键拉取所有", self)
        self.btn_fetch_all.clicked.connect(self._on_fetch_all_clicked)
        header_layout.addWidget(self.btn_fetch_all)

        self.btn_push_all = PrimaryPushButton("📤 一键强推所有", self)
        self.btn_push_all.clicked.connect(self._on_push_all_clicked)
        header_layout.addWidget(self.btn_push_all)

        main_layout.addLayout(header_layout)

        # 2. 三列分栏卡片布局
        columns_layout = QHBoxLayout()
        columns_layout.setSpacing(14)

        # 卡片 1: /auto.txt (优质精选)
        card_auto = CloudTextCard(
            title="⭐ 优质精选池 (/auto.txt)",
            subpath="/auto.txt",
            desc="大优选产出的优质精选节点，直接下发自适应策略组",
            parent=self,
        )
        self.cards["/auto.txt"] = card_auto
        columns_layout.addWidget(card_auto, 1)

        # 卡片 2: /verified.txt (沉淀孵化)
        card_ver = CloudTextCard(
            title="⏳ 沉淀孵化池 (/verified.txt)",
            subpath="/verified.txt",
            desc="连续多轮测速达标的稳定节点，处于孵化培育状态",
            parent=self,
        )
        self.cards["/verified.txt"] = card_ver
        columns_layout.addWidget(card_ver, 1)

        # 卡片 3: / (典藏常青)
        card_root = CloudTextCard(
            title="🏆 典藏常青池 (/)",
            subpath="/",
            desc="高频考核历练出的极品常青树节点，顶级优先级直通",
            parent=self,
        )
        self.cards["/"] = card_root
        columns_layout.addWidget(card_root, 1)

        # 卡片 4: /pending.txt (待测归收池)
        card_pending = CloudTextCard(
            title="⚪ 待测归收池 (/pending.txt)",
            subpath="/pending.txt",
            desc="存放 C 段挖掘与移出黑名单节点，全量大优选启动时自动读取重新纳测",
            parent=self,
        )
        self.cards["/pending.txt"] = card_pending
        columns_layout.addWidget(card_pending, 1)

        main_layout.addLayout(columns_layout, 1)

    def _connect_signals(self):
        """绑定内部信号"""
        for subpath, card in self.cards.items():
            card.fetch_requested.connect(self._handle_card_fetch)
            card.push_requested.connect(self._handle_card_push)
            if hasattr(card, "btn_purge"):
                card.btn_purge.clicked.connect(self._on_manual_purge_clicked)

        self.fetch_done_signal.connect(self._on_fetch_done)
        self.push_done_signal.connect(self._on_push_done)

    def showEvent(self, event):
        """初次切入页面时自动静默拉取三大文本"""
        super().showEvent(event)
        if not self._initial_loaded:
            self._initial_loaded = True
            self._on_fetch_all_clicked(silent=True)

    # ==================== 单卡片操作 ====================

    def _handle_card_fetch(self, subpath: str):
        """单卡片拉取请求"""
        card = self.cards.get(subpath)
        if card:
            card.set_loading(True)
            card.set_status("正在从云端拉取...")

        def _worker():
            ok, content = self.controller.fetch_cloud_text(subpath=subpath)
            self.fetch_done_signal.emit(subpath, ok, content)

        threading.Thread(target=_worker, daemon=True).start()

    def _handle_card_push(self, subpath: str, text: str):
        """单卡片强推请求"""
        card = self.cards.get(subpath)
        title = card.title_text if card else subpath

        # 强推前二次确认
        w = MessageBox(
            "确认强推覆盖云端",
            f"确定要将当前编辑的内容强推覆盖至云端 {subpath} 吗？\n\n"
            f"⚠️ 目标模块：{title}\n"
            "该操作将立即直接覆盖远端 Cloudflare Worker 文本存储，不可撤销！",
            self.window(),
        )
        if not w.exec():
            return

        if card:
            card.set_loading(True)
            card.set_status("正在强推至云端...")

        def _worker():
            ok, msg = self.controller.push_cloud_text(subpath=subpath, text=text)
            self.push_done_signal.emit(subpath, ok, msg)

        threading.Thread(target=_worker, daemon=True).start()

    # ==================== 批量全局操作 ====================

    def _on_fetch_all_clicked(self, silent: bool = False):
        """一键拉取全部"""
        if not silent:
            InfoBar.info("正在拉取", "正在向 Cloudflare Worker 并发拉取三大分发文本...", duration=2000, parent=self.window())
        for subpath in self.cards:
            self._handle_card_fetch(subpath)

    def _on_push_all_clicked(self):
        """一键强推全部"""
        w = MessageBox(
            "确认批量强推全部云端文本",
            "确定要将当前编辑的全部 3 个文本（/auto.txt、/verified.txt、/）强推覆盖至云端吗？\n\n"
            "⚠️ 该操作将同时重写远端 Cloudflare Worker 全部数据，不可撤销！",
            self.window(),
        )
        if not w.exec():
            return

        InfoBar.info("正在强推", "正在向 Cloudflare Worker 批量推送三大分发文本...", duration=2000, parent=self.window())
        for subpath, card in self.cards.items():
            card.set_loading(True)
            card.set_status("正在强推至云端...")
            text = card.get_text()

            def _worker(sp=subpath, t=text):
                ok, msg = self.controller.push_cloud_text(subpath=sp, text=t)
                self.push_done_signal.emit(sp, ok, msg)

            threading.Thread(target=_worker, daemon=True).start()

    # ==================== 信号回调处理 ====================

    def _on_fetch_done(self, subpath: str, ok: bool, content: str):
        """拉取完成回调"""
        card = self.cards.get(subpath)
        if not card:
            return
        card.set_loading(False)
        if ok:
            card.set_text(content)
            card.set_status(f"拉取成功 ({time.strftime('%H:%M:%S')})", is_error=False)
            InfoBar.success("拉取成功", f"已成功拉取并更新 {subpath}", duration=2500, parent=self.window())
        else:
            card.set_status("拉取失败", is_error=True)
            InfoBar.error("拉取失败", f"{subpath}: {content}", duration=4000, parent=self.window())

    def _on_push_done(self, subpath: str, ok: bool, msg: str):
        """强推完成回调"""
        card = self.cards.get(subpath)
        if not card:
            return
        card.set_loading(False)
        if ok:
            card.set_status(f"强推成功 ({time.strftime('%H:%M:%S')})", is_error=False)
            InfoBar.success("强推成功", f"{subpath} 文本已成功写入远端 Worker！", duration=3000, parent=self.window())
        else:
            card.set_status("强推失败", is_error=True)
            InfoBar.error("强推失败", f"{subpath}: {msg}", duration=4500, parent=self.window())

    def _on_manual_purge_clicked(self):
        """用户在待测卡片上手动点击【🧹 联动清洗】的一键自愈操作"""
        card = self.cards.get("/pending.txt")
        if card:
            card.set_loading(True)
            card.set_status("正在比对全池清洗云端待测池...")

        def _worker():
            purged = self.controller.purge_pending_endpoints_from_cloud()
            time.sleep(0.5)
            # 清洗后自动重拉最新内容刷新编辑器
            ok, content = self.controller.fetch_cloud_text("/pending.txt")
            self.fetch_done_signal.emit("/pending.txt", ok, content)

        import threading
        threading.Thread(target=_worker, daemon=True).start()



```

## File: `gui_fluent/pages/page_delay_black.py`

```python
"""
延迟黑名单页面
展示因超时、高延迟、向上抖动剧烈或机房跨洲漂移被淘汰的节点与端点
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout
else:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout

from gui_fluent.app_controller import AppController
from gui_fluent.widgets.node_table import NodeTableView


class PageDelayBlack(QWidget):
    """
    延迟黑名单页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageDelayBlack")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 核心通用节点表格
        self.table = NodeTableView(self, controller=self.controller, page_type="delay_black")
        layout.addWidget(self.table, 1)

        # 绑定数据变更信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)
        self.refresh_data()

    def refresh_data(self):
        """
        重新装配延迟黑名单数据并刷新表格
        """
        rows = self.controller.get_table_rows("delay_black")
        self.table.populate(rows)

```

## File: `gui_fluent/pages/page_favorites.py`

```python
"""
优质精选页面
包含两行精选参数控制与操作工具栏 (FavToolBar) 以及核心节点表格 (NodeTableView)
"""
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
else:
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CheckBox,
    LineEdit,
    PushButton,
    PrimaryPushButton,
)
from gui_fluent.app_controller import AppController
from gui_fluent.widgets.node_table import NodeTableView


class GoogleHkCheckWorker(QThread):
    progress_signal = pyqtSignal(str, int, int)      # (提示文本, 当前索引, 总数)
    finished_signal = pyqtSignal(bool, dict)         # (成功与否, 汇总统计字典)

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller

    def run(self):
        self.controller._is_checking_google_hk = True
        orig_selections = {}
        orig_global = ""
        nodes_to_test = []
        with self.controller.state.lock:
            nodes_to_test = list(self.controller.state.favorites)
        total = len(nodes_to_test)
        if total == 0:
            self.controller._is_checking_google_hk = False
            self.finished_signal.emit(False, {"msg": "当前精选池为空，无需核验"})
            return
        tagged_nodes = []
        untagged_nodes = []
        clean_nodes = []
        failed_nodes = []
        try:
            # 1. 记录原各策略组当前选中项
            proxies_map = self.controller.clash_client.get_proxies()
            for g_name, g_info in proxies_map.items():
                if g_info.get("type", "").lower() in ["selector", "fallback"]:
                    orig_selections[g_name] = g_info.get("now", "")
            orig_global = proxies_map.get("GLOBAL", {}).get("now", "")
            # 2. 构造本地代理客户端
            mix_port = self.controller.clash_client.get_mixed_port(default=7897)
            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mix_port}",
                "https": f"http://127.0.0.1:{mix_port}",
            })
            opener = urllib.request.build_opener(proxy_handler)
            # 3. 逐个切组探测 Google
            for idx, n in enumerate(nodes_to_test, 1):
                self.progress_signal.emit(f"正在核验 [{idx}/{total}]: {n[:22]}", idx, total)
                # 切 GLOBAL 策略组直连当前节点
                enc_glb = urllib.parse.quote("GLOBAL", safe="")
                self.controller.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": n})
                time.sleep(0.15)
                is_hk = False
                success = False
                try:
                    req = urllib.request.Request(
                        "https://www.google.com",
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    )
                    with opener.open(req, timeout=3.0) as resp:
                        final_url = resp.geturl()
                        is_hk = ("google.com.hk" in final_url) or ("sorry" in final_url)
                        success = True
                except urllib.error.HTTPError as he:
                    if he.code in (429, 403) or "sorry" in getattr(he, "url", "") or "google.com.hk" in getattr(he, "url", ""):
                        is_hk = True
                        success = True
                    else:
                        success = False
                except Exception:
                    success = False
                if not success:
                    failed_nodes.append(n)
                    continue
                ep = self.controller._get_ep(n) or n
                if is_hk:
                    # 遭遇送中：若尚未打标，则规范重命名注入 [送中]
                    if "[送中]" not in n:
                        m = re.search(r"([\d.]+\s*MB/s)", n)
                        new_name = f"{n[:m.start()]}[送中] {n[m.start():]}" if m else f"{n} [送中]"
                        with self.controller.state.lock:
                            orig_f = n
                            self.controller._migrate_node_name(orig_f, new_name, ep)
                            self.controller.state.fav_reasons[new_name] = "一键核验打标[送中]"
                        tagged_nodes.append(new_name)
                    else:
                        tagged_nodes.append(n)
                else:
                    # 原生洁净：若此前曾被标记 [送中]，自动摘标平反！
                    if "[送中]" in n:
                        clean_name = n.replace(" [送中]", "").replace("[送中] ", "").replace("[送中]", "").strip()
                        with self.controller.state.lock:
                            orig_f = n
                            self.controller._migrate_node_name(orig_f, clean_name, ep)
                            self.controller.state.fav_reasons[clean_name] = "一键核验摘标平反"
                        untagged_nodes.append(clean_name)
                    else:
                        clean_nodes.append(n)
        finally:
            # 4. 百分之百原样恢复各策略组初始状态
            for g_name, orig_choice in orig_selections.items():
                if orig_choice:
                    enc = urllib.parse.quote(g_name, safe="")
                    self.controller.clash_client.call_api(f"/proxies/{enc}", method="PUT", data={"name": orig_choice})
            if orig_global:
                enc_glb = urllib.parse.quote("GLOBAL", safe="")
                self.controller.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": orig_global})
            self.controller._is_checking_google_hk = False
        # 5. 若发生打标或摘标更名：触发存盘、Script.js 0ms热更与云端 Worker 异步推送
        if tagged_nodes or untagged_nodes:
            self.controller.save_config(self.controller.get_state_snapshot())
            self.controller.generate_script_and_reload()
            self.controller.push_favorites_to_cloud()
            self.controller.data_changed.emit()
        res = {
            "total": total,
            "tagged_count": len(tagged_nodes),
            "untagged_count": len(untagged_nodes),
            "clean_count": len(clean_nodes),
            "failed_count": len(failed_nodes),
            "tagged_nodes": tagged_nodes,
            "untagged_nodes": untagged_nodes,
        }
        self.finished_signal.emit(True, res)


class FavToolBar(QWidget):
    """
    优质精选工具栏 (包含两行控制项)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(6)

        # 第一行：测速指标门槛与控制按钮
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 0, 0, 0)
        row1.setSpacing(6)

        row1.addWidget(BodyLabel("精选标准 延迟<", self))
        self.fav_max_delay = LineEdit(self)
        self.fav_max_delay.setText("80")
        self.fav_max_delay.setFixedWidth(40)
        self.fav_max_delay.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_max_delay)
        row1.addWidget(BodyLabel("ms", self))

        row1.addWidget(BodyLabel("测速>", self))
        self.fav_min_speed = LineEdit(self)
        self.fav_min_speed.setText("8.0")
        self.fav_min_speed.setFixedWidth(40)
        self.fav_min_speed.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_min_speed)
        row1.addWidget(BodyLabel("MB/s", self))

        row1.addWidget(BodyLabel("轮数", self))
        self.fav_rounds = LineEdit(self)
        self.fav_rounds.setText("2")
        self.fav_rounds.setFixedWidth(30)
        self.fav_rounds.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_rounds)

        row1.addWidget(BodyLabel("时长", self))
        self.fav_speed_duration = LineEdit(self)
        self.fav_speed_duration.setText("2")
        self.fav_speed_duration.setFixedWidth(30)
        self.fav_speed_duration.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_speed_duration)
        row1.addWidget(BodyLabel("s", self))

        row1.addWidget(BodyLabel("抖动基线<", self))
        self.fav_jitter_min = LineEdit(self)
        self.fav_jitter_min.setText("70")
        self.fav_jitter_min.setFixedWidth(35)
        self.fav_jitter_min.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_jitter_min)
        row1.addWidget(BodyLabel("ms", self))

        row1.addWidget(BodyLabel("抬升<", self))
        self.fav_jitter_up = LineEdit(self)
        self.fav_jitter_up.setText("15")
        self.fav_jitter_up.setFixedWidth(30)
        self.fav_jitter_up.setAlignment(Qt.AlignCenter)
        row1.addWidget(self.fav_jitter_up)
        row1.addWidget(BodyLabel("ms", self))

        self.btn_fav_run = PrimaryPushButton("▶ 启动精选全自动测速", self)
        row1.addWidget(self.btn_fav_run)

        row1.addStretch(1)

        self.btn_fav_reload_history = PushButton("重载历史", self)
        row1.addWidget(self.btn_fav_reload_history)

        self.btn_fav_clean_stale = PushButton("清理过期", self)
        row1.addWidget(self.btn_fav_clean_stale)

        self.btn_fav_clear_all = PushButton("清空精选", self)
        row1.addWidget(self.btn_fav_clear_all)

        self.btn_fav_sync_now = PushButton("⚡ 立即同步到活跃池", self)
        row1.addWidget(self.btn_fav_sync_now)

        self.btn_check_google_hk = PushButton("🌐 一键送中核验", self)
        row1.addWidget(self.btn_check_google_hk)

        main_layout.addLayout(row1)

        # 第二行：定时与达标即停配置
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)
        row2.setSpacing(6)

        self.chk_fav_schedule = CheckBox("定时运行精选 (分):", self)
        row2.addWidget(self.chk_fav_schedule)

        self.fav_sched_interval = LineEdit(self)
        self.fav_sched_interval.setText("60")
        self.fav_sched_interval.setFixedWidth(45)
        self.fav_sched_interval.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.fav_sched_interval)

        self.chk_fav_early_stop = CheckBox("达标即停 (HK:", self)
        self.chk_fav_early_stop.setChecked(True)
        row2.addWidget(self.chk_fav_early_stop)

        self.fav_target_hk = LineEdit(self)
        self.fav_target_hk.setText("3")
        self.fav_target_hk.setFixedWidth(30)
        self.fav_target_hk.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.fav_target_hk)

        row2.addWidget(BodyLabel("非HK:", self))

        self.fav_target_nohk = LineEdit(self)
        self.fav_target_nohk.setText("5")
        self.fav_target_nohk.setFixedWidth(30)
        self.fav_target_nohk.setAlignment(Qt.AlignCenter)
        row2.addWidget(self.fav_target_nohk)

        row2.addWidget(BodyLabel(")", self))

        self.chk_fav_fallback = CheckBox("HK不足降级", self)
        row2.addWidget(self.chk_fav_fallback)

        self.lbl_fav_sched_status = CaptionLabel("状态: 未运行", self)
        self.lbl_fav_sched_status.setStyleSheet("color: #888888; font-weight: bold;")
        row2.addWidget(self.lbl_fav_sched_status)

        row2.addStretch(1)

        main_layout.addLayout(row2)

        self.setStyleSheet("""
            FavToolBar {
                background-color: #202020;
                border-bottom: 1px solid #333333;
            }
        """)


class PageFavorites(QWidget):
    """
    优质精选页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageFavorites")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部工具栏
        self.toolbar = FavToolBar(self)
        layout.addWidget(self.toolbar)

        # 核心通用节点表格
        self.table = NodeTableView(self, controller=self.controller, page_type="favorites")
        layout.addWidget(self.table, 1)

        # 便于外部直接通过页面对象访问工具栏控件
        self.fav_max_delay = self.toolbar.fav_max_delay
        self.fav_min_speed = self.toolbar.fav_min_speed
        self.fav_rounds = self.toolbar.fav_rounds
        self.fav_speed_duration = self.toolbar.fav_speed_duration
        self.fav_jitter_min = self.toolbar.fav_jitter_min
        self.fav_jitter_up = self.toolbar.fav_jitter_up
        self.btn_fav_run = self.toolbar.btn_fav_run
        self.btn_fav_reload_history = self.toolbar.btn_fav_reload_history
        self.btn_fav_clean_stale = self.toolbar.btn_fav_clean_stale
        self.btn_fav_clear_all = self.toolbar.btn_fav_clear_all
        self.btn_fav_sync_now = self.toolbar.btn_fav_sync_now
        self.btn_check_google_hk = self.toolbar.btn_check_google_hk
        self.chk_fav_schedule = self.toolbar.chk_fav_schedule
        self.fav_sched_interval = self.toolbar.fav_sched_interval
        self.chk_fav_early_stop = self.toolbar.chk_fav_early_stop
        self.fav_target_hk = self.toolbar.fav_target_hk
        self.fav_target_nohk = self.toolbar.fav_target_nohk
        self.chk_fav_fallback = self.toolbar.chk_fav_fallback
        self.lbl_fav_sched_status = self.toolbar.lbl_fav_sched_status

        # 绑定数据变更信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)
        self.controller.fav_pipeline_status_updated.connect(self.lbl_fav_sched_status.setText)
        self.controller.fav_pipeline_finished.connect(self._on_fav_pipeline_finished)

        # 绑定工具栏按钮业务
        self.btn_fav_run.clicked.connect(self._on_run_fav_clicked)
        self.btn_fav_reload_history.clicked.connect(self._on_reload_history_clicked)
        self.btn_fav_clean_stale.clicked.connect(self._on_clean_stale_clicked)
        self.btn_fav_clear_all.clicked.connect(self._on_clear_all_clicked)
        self.btn_fav_sync_now.clicked.connect(self._on_sync_now_clicked)
        self.toolbar.btn_check_google_hk.clicked.connect(self._on_check_google_hk_clicked)
        self._hk_worker = None

        self.refresh_data()

    def refresh_data(self):
        """
        重新装配优质精选池数据并刷新表格
        """
        rows = self.controller.get_table_rows("favorites")
        self.table.populate(rows)

    def _on_reload_history_clicked(self):
        self.controller.reconcile_endpoints()
        self.controller.data_changed.emit()

    def _on_clean_stale_clicked(self):
        self.controller.clean_stale_favorites()
        self.controller.data_changed.emit()

    def _on_sync_now_clicked(self):
        self.controller.sync_favorites_to_active()
        self.controller.data_changed.emit()

    def _on_run_fav_clicked(self):
        """
        启动或终止精选池复测流水线
        """
        if self.controller.is_pipeline_running():
            self.controller.stop_fav_pipeline()
            self.btn_fav_run.setText("▶ 启动精选全自动测速")
            return

        cfg = self.get_fav_config()
        started = self.controller.start_fav_pipeline(cfg)
        if started:
            self.btn_fav_run.setText("⏹ 终止精选测速")

    def _on_fav_pipeline_finished(self, success: bool, msg: str):
        self.btn_fav_run.setText("▶ 启动精选全自动测速")
        self.lbl_fav_sched_status.setText(f"完成: {msg[:25]}")
        if hasattr(self, 'controller') and self.controller:
            self.controller.save_config(self.controller.state.get_snapshot())

    def _on_clear_all_clicked(self):
        from qfluentwidgets import MessageBox
        w = MessageBox("确认清空精选池", "确定要清空优质精选池中所有节点吗？\n清空后需重新运行全量优选或手动添加节点。", self)
        if w.exec():
            self.controller.clear_all_favorites()
            self.controller.data_changed.emit()

    def get_fav_config(self) -> dict:
        """
        提取当前精选页面的配置字典
        """
        cfg_storage = self.controller.load_config() if hasattr(self, 'controller') and self.controller else {}
        speed_url = str(cfg_storage.get("speed_url", "")).strip() or "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip"
        return {
            "speed_url": speed_url,
            "fav_max_delay": self.fav_max_delay.text().strip(),
            "fav_min_speed": self.fav_min_speed.text().strip(),
            "fav_rounds": self.fav_rounds.text().strip(),
            "fav_speed_duration": self.fav_speed_duration.text().strip(),
            "fav_jitter_min_delay": self.fav_jitter_min.text().strip(),
            "fav_jitter_up_threshold": self.fav_jitter_up.text().strip(),
            "fav_schedule_enabled": self.chk_fav_schedule.isChecked(),
            "fav_schedule_interval": self.fav_sched_interval.text().strip(),
            "fav_target_hk_count": self.fav_target_hk.text().strip(),
            "fav_target_nohk_count": self.fav_target_nohk.text().strip(),
            "fav_quota_early_stop": self.chk_fav_early_stop.isChecked(),
            "fav_fallback_enabled": self.chk_fav_fallback.isChecked(),
        }

    def _on_check_google_hk_clicked(self):
        if self.controller.is_pipeline_running():
            from qfluentwidgets import InfoBar, InfoBarPosition
            InfoBar.warning("任务互斥", "当前已有流水线或核验任务在运行，请稍候！", parent=self, position=InfoBarPosition.TOP)
            return
        self.toolbar.btn_check_google_hk.setEnabled(False)
        self.toolbar.lbl_fav_sched_status.setText("状态: 正在核验送中...")
        self._hk_worker = GoogleHkCheckWorker(self.controller, self)
        self._hk_worker.progress_signal.connect(lambda msg, cur, tot: self.toolbar.lbl_fav_sched_status.setText(f"状态: [{cur}/{tot}] 核验中"))

        def _on_finished(success, res):
            self.toolbar.btn_check_google_hk.setEnabled(True)
            if not success:
                self.toolbar.lbl_fav_sched_status.setText("状态: 核验终止")
                return
            tot = res.get("total", 0)
            tagged = res.get("tagged_count", 0)
            untagged = res.get("untagged_count", 0)
            clean = res.get("clean_count", 0)
            self.toolbar.lbl_fav_sched_status.setText(f"状态: 送中核验完成 ({tagged}送中/{clean}洁净)")
            # 弹窗汇报详细核验结果
            from qfluentwidgets import MessageBox
            title = "🌐 Google 送中状态核验总结"
            content = (
                f"共核验精选池节点 {tot} 个：\n\n"
                f"  • ✅ 原生洁净节点: {clean} 个\n"
                f"  • 🚨 新标记 [送中] 节点: {tagged} 个\n"
                f"  • 🕊️ 平反摘除 [送中] 节点: {untagged} 个\n\n"
                f"💡 调整已即刻写入 Script.js 生效，并已自动同步至云端 Worker！"
            )
            MessageBox(title, content, self).exec()

        self._hk_worker.finished_signal.connect(_on_finished)
        self._hk_worker.start()


```

## File: `gui_fluent/pages/page_speed_black.py`

```python
"""
低速黑名单页面
展示因下载实测带宽低于设定淘汰门槛或连续测速失败而被淘汰的节点与端点
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtWidgets import QWidget, QVBoxLayout
else:
    from PyQt6.QtWidgets import QWidget, QVBoxLayout

from gui_fluent.app_controller import AppController
from gui_fluent.widgets.node_table import NodeTableView


class PageSpeedBlack(QWidget):
    """
    低速黑名单页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageSpeedBlack")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 核心通用节点表格
        self.table = NodeTableView(self, controller=self.controller, page_type="speed_black")
        layout.addWidget(self.table, 1)

        # 绑定数据变更信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)
        self.refresh_data()

    def refresh_data(self):
        """
        重新装配低速黑名单数据并刷新表格
        """
        rows = self.controller.get_table_rows("speed_black")
        self.table.populate(rows)

```

## File: `gui_fluent/pages/page_stars.py`

```python
"""
典藏管理池页面
包含典藏节点操作工具栏 (StarsToolBar) 以及典藏专用表格 (StarsTableView)
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
)
from gui_fluent.app_controller import AppController
from gui_fluent.widgets.stars_table import StarsTableView


class StarsToolBar(QWidget):
    """
    典藏管理池工具栏
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        self.btn_add = PushButton("➕ 录入节点", self)
        layout.addWidget(self.btn_add)

        self.btn_pull_favorites = PushButton("📥 从精选池拉取", self)
        layout.addWidget(self.btn_pull_favorites)

        self.btn_test_delay = PushButton("⚡ 测延迟", self)
        layout.addWidget(self.btn_test_delay)

        self.btn_test_speed = PushButton("🚀 测速度", self)
        layout.addWidget(self.btn_test_speed)

        self.btn_remark = PushButton("✏️ 修改备注", self)
        layout.addWidget(self.btn_remark)

        self.btn_delete = PushButton("🗑️ 删除", self)
        layout.addWidget(self.btn_delete)

        layout.addStretch(1)

        self.btn_sync_root = PrimaryPushButton("💾 保存并推送根目录 /", self)
        layout.addWidget(self.btn_sync_root)

        self.setStyleSheet("""
            StarsToolBar {
                background-color: #202020;
                border-bottom: 1px solid #333333;
            }
        """)


class PageStars(QWidget):
    """
    典藏管理池页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageStars")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 工具栏
        self.toolbar = StarsToolBar(self)
        layout.addWidget(self.toolbar)

        # 典藏专用表格
        self.table = StarsTableView(self, controller=self.controller)
        layout.addWidget(self.table, 1)

        # 便于外部直接通过页面对象访问工具栏控件
        self.btn_add = self.toolbar.btn_add
        self.btn_pull_favorites = self.toolbar.btn_pull_favorites
        self.btn_test_delay = self.toolbar.btn_test_delay
        self.btn_test_speed = self.toolbar.btn_test_speed
        self.btn_remark = self.toolbar.btn_remark
        self.btn_delete = self.toolbar.btn_delete
        self.btn_sync_root = self.toolbar.btn_sync_root

        # 绑定数据变更信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)

        # 绑定工具栏按钮业务与双击修改备注
        self.table.double_clicked.connect(lambda ep: self._on_remark_clicked())
        self.btn_add.clicked.connect(self._on_add_clicked)
        self.btn_pull_favorites.clicked.connect(self._on_pull_favorites_clicked)
        self.btn_test_delay.clicked.connect(lambda: self.controller.test_stars_pipeline(mode="delay", endpoints=self.table.get_selected_endpoints() or None))
        self.btn_test_speed.clicked.connect(lambda: self.controller.test_stars_pipeline(mode="speed", endpoints=self.table.get_selected_endpoints() or None))
        self.btn_remark.clicked.connect(self._on_remark_clicked)
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        self.btn_sync_root.clicked.connect(lambda: self.controller.push_stars_to_cloud())

        self.refresh_data()

    def refresh_data(self):
        """
        重新装配典藏管理池数据并刷新表格
        """
        rows = self.controller.get_table_rows("stars")
        self.table.populate(rows)

    def _on_pull_favorites_clicked(self):
        favs = list(self.controller.state.favorites)
        if not favs:
            self.controller.log("⚠️ 优质精选池当前暂无节点可拉入！")
            return
        self.controller.promote_nodes_to_stars(favs)
        self.controller.data_changed.emit()

    def _on_add_clicked(self):
        if "PyQt5" in sys.modules:
            from PyQt5.QtWidgets import QInputDialog
        else:
            from PyQt6.QtWidgets import QInputDialog

        text, ok = QInputDialog.getText(self, "录入典藏节点", "请输入节点端点及备注 (格式: IP:端口#备注 或 IP:端口):")
        if ok and text and text.strip():
            raw = text.strip()
            if "#" in raw:
                parts = raw.split("#", 1)
                ep = parts[0].strip()
                rem = parts[1].strip() or "手动录入"
            else:
                ep = raw
                rem = "手动录入"
            self.controller.add_star_node(ep, rem)

    def _on_remark_clicked(self):
        eps = self.table.get_selected_endpoints()
        if not eps:
            self.controller.log("⚠️ 请先在列表中选中需要修改备注的典藏节点！")
            return
        if "PyQt5" in sys.modules:
            from PyQt5.QtWidgets import QInputDialog
        else:
            from PyQt6.QtWidgets import QInputDialog

        ep = eps[0]
        text, ok = QInputDialog.getText(self, "修改备注", f"修改典藏节点 [{ep}] 的备注信息:")
        if ok and text is not None:
            self.controller.update_star_remark(ep, text.strip())

    def _on_delete_clicked(self):
        eps = self.table.get_selected_endpoints()
        if not eps:
            self.controller.log("⚠️ 请先在列表中选中要删除的典藏节点！")
            return
        from qfluentwidgets import MessageBox
        w = MessageBox("删除确认", f"确定从本地典藏池移除选中的 {len(eps)} 个节点吗？\n（注：点击保存推送前云端数据不会变动）", self)
        if w.exec():
            self.controller.delete_selected_stars(eps)

```

## File: `gui_fluent/pages/page_verified.py`

```python
"""
沉淀孵化池页面
包含孵化考核阈值与流转工具栏 (VerifiedToolBar) 以及孵化表格 (VerifiedTableView)
"""
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
else:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from qfluentwidgets import (
    BodyLabel,
    LineEdit,
    PushButton,
    PrimaryPushButton,
)
from gui_fluent.app_controller import AppController
from gui_fluent.widgets.verified_table import VerifiedTableView


class VerifiedToolBar(QWidget):
    """
    沉淀孵化池工具栏
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)

        layout.addWidget(BodyLabel("孵化达标要求: 连续合格时长 >", self))
        self.incubate_hours = LineEdit(self)
        self.incubate_hours.setText("24")
        self.incubate_hours.setFixedWidth(40)
        self.incubate_hours.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.incubate_hours)
        layout.addWidget(BodyLabel("小时", self))

        layout.addWidget(BodyLabel("达标轮数 >=", self))
        self.incubate_passes = LineEdit(self)
        self.incubate_passes.setText("5")
        self.incubate_passes.setFixedWidth(35)
        self.incubate_passes.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.incubate_passes)
        layout.addWidget(BodyLabel("轮", self))

        self.btn_pull_favorites = PushButton("📥 从精选池拉入", self)
        layout.addWidget(self.btn_pull_favorites)

        self.btn_promote = PushButton("⚡ 立即晋升达标节点", self)
        layout.addWidget(self.btn_promote)

        self.btn_remove = PushButton("🗑️ 从观察池移出", self)
        layout.addWidget(self.btn_remove)

        layout.addStretch(1)

        self.btn_sync_verified = PrimaryPushButton("💾 同步推送 /verified.txt", self)
        layout.addWidget(self.btn_sync_verified)

        self.setStyleSheet("""
            VerifiedToolBar {
                background-color: #202020;
                border-bottom: 1px solid #333333;
            }
        """)


class PageVerified(QWidget):
    """
    沉淀孵化池页面
    """

    def __init__(self, controller: AppController, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.setObjectName("PageVerified")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 工具栏
        self.toolbar = VerifiedToolBar(self)
        layout.addWidget(self.toolbar)

        # 沉淀孵化池专用表格
        self.table = VerifiedTableView(self, controller=self.controller)
        layout.addWidget(self.table, 1)

        # 便于外部直接通过页面对象访问工具栏控件
        self.incubate_hours = self.toolbar.incubate_hours
        self.incubate_passes = self.toolbar.incubate_passes
        self.btn_pull_favorites = self.toolbar.btn_pull_favorites
        self.btn_promote = self.toolbar.btn_promote
        self.btn_remove = self.toolbar.btn_remove
        self.btn_sync_verified = self.toolbar.btn_sync_verified

        # 绑定数据变更信号自动刷新
        self.controller.data_changed.connect(self.refresh_data)

        # 绑定工具栏按钮业务
        self.btn_pull_favorites.clicked.connect(self.controller.sync_favorites_to_verified)
        self.btn_promote.clicked.connect(self._on_promote_clicked)
        self.btn_remove.clicked.connect(self._on_remove_clicked)
        self.btn_sync_verified.clicked.connect(lambda: self.controller.push_verified_to_cloud())

        self.refresh_data()

    def refresh_data(self):
        """
        重新装配沉淀孵化池数据并刷新表格
        """
        rows = self.controller.get_table_rows("verified")
        self.table.populate(rows)

    def _on_promote_clicked(self):
        eps = self.table.get_selected_endpoints()
        if not eps:
            self.controller.log("⚠️ 请先在表格中选中要加冕的沉淀节点！")
            return
        self.controller.force_promote_verified_to_stars(eps)

    def _on_remove_clicked(self):
        eps = self.table.get_selected_endpoints()
        if not eps:
            self.controller.log("⚠️ 请先在表格中选中要移出的沉淀节点！")
            return
        from qfluentwidgets import MessageBox
        w = MessageBox("确认移出", f"确定要从沉淀池移出选中的 {len(eps)} 个节点吗？", self)
        if w.exec():
            self.controller.delete_selected_verified(eps)

    def get_verified_config(self) -> dict:
        """
        提取当前沉淀孵化池配置字典
        """
        return {
            "incubate_hours": self.incubate_hours.text().strip(),
            "incubate_passes": self.incubate_passes.text().strip(),
        }

```

## File: `gui_fluent/pipelines/__init__.py`

```python
"""
Fluent 流水线模块
"""
from gui_fluent.pipelines.auto_pipeline import AutoPipelineWorker
from gui_fluent.pipelines.fav_pipeline import FavPipelineWorker

__all__ = ["AutoPipelineWorker", "FavPipelineWorker"]
```

## File: `gui_fluent/pipelines/auto_pipeline.py`

```python
"""
全自动优选流水线工作线程 (AutoPipelineWorker)
基于 QThread 运行，完全解耦 UI 渲染，1:1 接入真实测速、Colo校准、漂移过滤与 Script.js 生成逻辑
"""
import json
import ssl
import sys
import time
import threading
import traceback
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import QThread, pyqtSignal
else:
    from PyQt6.QtCore import QThread, pyqtSignal

from services.subscription_service import get_node_endpoint, choose_canonical_node_name
from services.colo_service import is_asian_node, analyze_colo_stats, record_colo_sample
from services.probe_service import get_cf_colo_raw
from services.clash_client import ClashClient, ClashModeGuard, find_cf_donor_node, fission_clean_ips
from services.script_generator import build_script_js, write_script_js
from services.pool_service import (
    purge_invalid_and_blacklisted_from_all_pools,
    get_pool_endpoint_sets,
    deduplicate_favorites_by_endpoint,
    process_verified_lifecycle,
)
from services.filter_service import (
    compute_delay_stats,
    check_node_jitter_blacklisted,
    auto_filter_and_blacklist_non_asia_nodes,
)
from utils.win32_utils import trigger_verge_reactivate_hotkey


def _record_delay_sample(node_delay_history, key_or_name, delay, ep=None, now_ts=None):
    """
    记录时延样本至 7 天时序桶中
    """
    if not delay or delay >= 99999 or delay <= 0:
        return
    if now_ts is None:
        now_ts = time.time()
    keys_to_update = {key_or_name}
    if ep and ep != "127.0.0.1:443":
        keys_to_update.add(ep)
    cutoff = now_ts - 7 * 86400
    for k in keys_to_update:
        if not k:
            continue
        hist = node_delay_history.setdefault(k, [])
        hist.append({"ts": now_ts, "d": int(delay)})
        node_delay_history[k] = [
            x for x in hist if isinstance(x, dict) and x.get("ts", 0) >= cutoff
        ][-30:]


class AutoPipelineWorker(QThread):
    """
    全自动优选后台工作线程：
    提取当前订阅待测节点，执行多轮并发测延、Colo时序探测、防漂移审查、下行带宽实测与策略组热重载
    """

    status_signal = pyqtSignal(str)           # 进度状态更新 (如 "延迟初筛: 第1/4轮 (10/50)")
    log_signal = pyqtSignal(str)              # 日志文本输出
    rows_updated = pyqtSignal(list)           # 表格行实时全量刷新
    finished_signal = pyqtSignal(bool, str)   # (是否成功, 结果描述)

    def __init__(self, controller, config: dict, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.config = dict(config)
        self.thread = self

    def log(self, msg: str):
        """发射日志信号的统一快捷方法"""
        self.log_signal.emit(msg)

    def stop(self):
        # 将原有的 self.thread.terminate() 精准替换为以下平滑退出机制：
        if self.thread and self.thread.isRunning():
            self.thread.requestInterruption()
            self.thread.quit()
            if not self.thread.wait(2000):
                self.thread.terminate()
                self.thread.wait()

    def run(self):
        self.log_signal.emit("🚀 启动一整套全自动大优选流程 (Fluent 后台线程)...")
        try:
            # 0. 解析配置参数（严格依据 UI 面板设置决定初筛轮数与超时，严禁硬编码与截断）
            max_delay = int(self.config.get("max_delay", 100)) if str(self.config.get("max_delay", "")).isdigit() else 100
            try:
                min_speed = float(self.config.get("min_speed", 5.0))
            except Exception:
                min_speed = 5.0

            # 严格恢复按 UI 设置的轮数与超时（不再硬编码 rounds=2 与 500ms 超时）
            rounds = max(1, int(self.config.get("test_rounds", 4))) if str(self.config.get("test_rounds", "")).isdigit() else 4
            timeout_ms = max(200, int(self.config.get("test_timeout", 1500))) if str(self.config.get("test_timeout", "")).isdigit() else 1500
            try:
                duration = max(0.5, float(self.config.get("speed_duration", 3.0)))
            except Exception:
                duration = 3.0

            bl_delay_threshold = int(self.config.get("blacklist_threshold", 130)) if str(self.config.get("blacklist_threshold", "")).isdigit() else 130
            try:
                speed_bl_threshold = float(self.config.get("speed_bl_threshold", 1.0))
            except Exception:
                speed_bl_threshold = 1.0
            speed_bl_rounds = max(1, int(self.config.get("speed_bl_rounds", 4))) if str(self.config.get("speed_bl_rounds", "")).isdigit() else 4
            jitter_min_d = int(self.config.get("jitter_min_delay", 80)) if str(self.config.get("jitter_min_delay", "")).isdigit() else 80
            jitter_up_th = int(self.config.get("jitter_up_threshold", 20)) if str(self.config.get("jitter_up_threshold", "")).isdigit() else 20

            test_url = str(self.config.get("test_url", "")).strip() or "http://www.msftconnecttest.com/connecttest.txt"
            speed_url = str(self.config.get("speed_url", "")).strip() or "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip"

            target_cnt_str = str(self.config.get("target_count", "")).strip()
            target_node_limit = int(target_cnt_str) if (target_cnt_str.isdigit() and int(target_cnt_str) > 0) else 0

            group_interval = str(self.config.get("group_interval", "300")).strip()
            group_tolerance = str(self.config.get("group_tolerance", "20")).strip()
            star_group_interval = str(self.config.get("star_group_interval", "300")).strip()
            star_group_tolerance = str(self.config.get("star_group_tolerance", "20")).strip()

            # 校验并同步内核凭据
            clash_port_cfg = self.config.get("clash_port", "")
            clash_secret_cfg = self.config.get("clash_secret", "")
            if clash_port_cfg or clash_secret_cfg:
                self.controller.clash_client.update_credentials(
                    port=clash_port_cfg if str(clash_port_cfg).isdigit() else None,
                    secret=clash_secret_cfg if clash_secret_cfg is not None else None,
                )

            is_conn, ver_info = self.controller.clash_client.test_connection()
            if not is_conn:
                auto_p, auto_s = ClashClient.auto_detect_credentials()
                if auto_p:
                    self.controller.clash_client.update_credentials(port=auto_p, secret=auto_s)
                    is_conn, ver_info = self.controller.clash_client.test_connection()

            if not is_conn:
                self.log_signal.emit("❌ 无法连接 Clash 内核，请检查端口与密钥设置！")
                self.finished_signal.emit(False, "无法连接 Clash 内核！")
                return

            # 前置准备 1：强制更新远程订阅
            self.log_signal.emit("🔄 [前置准备] 正在强制更新远程订阅...")
            ok_sub, msg_sub = self.controller.update_remote_subscription_sync()
            self.log_signal.emit(f"🔄 [前置准备] 远程订阅更新结果: {msg_sub}")

            # 前置准备 2：拉取云端 auto.txt 专属节点名称与 pending.txt 待测清单
            self.log_signal.emit("☁️ [前置准备] 正在拉取云端 auto.txt 与 pending.txt 待测清单...")
            cloud_endpoints = self.controller.fetch_cloud_endpoints_sync()
            pending_endpoints = self.controller.fetch_pending_endpoints_sync()
            self.log_signal.emit(f"☁️ [前置准备] 云端同步完毕：精选端点 {len(cloud_endpoints)} 个，待测端点 {len(pending_endpoints)} 个")

            # 前置准备 3：重载本地内存与界面数据 (按云端专属名称霸占并严格绝对去重)
            self.log_signal.emit("📦 [前置准备] 正在重载本地内存与界面数据...")
            active_sub = getattr(self.controller.state, "active_profile", "") or self.config.get("profile_yaml", "") or "Rw0nNFlVIbnA.yaml"
            self.controller.load_nodes_from_profile(active_sub, cloud_endpoints=cloud_endpoints)
            # 触发一次强刷新，让 UI 的“活跃待测”立刻显示新抓取的节点
            self.controller.data_changed.emit()

            # 前置准备 4：热更激活 Clash 核心加载新节点
            self.log_signal.emit("⚡ [前置准备] 正在热更激活 Clash 核心加载新节点...")
            self.controller.generate_script_and_reload()

            # 延长休眠时间，确保 Clash 核心完全解析数百个节点并开放 RESTful API
            self.log_signal.emit("⏳ 等待内核重载完毕 (5秒)...")
            time.sleep(5)

            def _get_ep(n):
                return get_node_endpoint(
                    n,
                    node_details=self.controller.state.node_details,
                    all_nodes=self.controller.state.all_nodes,
                    verified_nodes=self.controller.state.verified_nodes,
                    clash_client=self.controller.clash_client,
                )

            # 1. 节点排查、去重与分组
            with self.controller.state.lock:
                auto_filter_and_blacklist_non_asia_nodes(
                    self.controller.state.all_nodes,
                    self.controller.state.local_blacklist,
                    self.controller.state.favorites,
                    self.controller.state.blacklist_reasons,
                    _get_ep,
                    is_asian_node,
                    node_colo_dict=self.controller.state.node_colo,
                )

                fav_eps, bl_eps, sbl_eps, star_eps = get_pool_endpoint_sets(
                    self.controller.state.favorites,
                    self.controller.state.local_blacklist,
                    self.controller.state.speed_blacklist,
                    self.controller.state.auto_endpoints,
                    self.controller.state.verified_nodes,
                    self.controller.state.stars_nodes,
                    _get_ep,
                )

                ep_to_untested = {}
                fav_sk = 0
                d_sk = 0
                s_sk = 0
                ver_sk = 0

                for n in self.controller.state.all_nodes:
                    ep = _get_ep(n)
                    c_val = self.controller.state.node_colo.get(n, self.controller.state.node_colo.get(ep, "-"))
                    if not is_asian_node(n, colo=c_val):
                        if n not in self.controller.state.local_blacklist:
                            self.controller.state.local_blacklist.add(n)
                            self.controller.state.blacklist_reasons[n] = "非亚洲节点 (自动过滤)"
                        continue

                    if n in self.controller.state.local_blacklist or (ep and ep in self.controller.state.local_blacklist):
                        d_sk += 1
                        continue
                    if n in self.controller.state.speed_blacklist or (ep and ep in self.controller.state.speed_blacklist):
                        s_sk += 1
                        continue

                    # 核心去重：命中精选池审查
                    if n in self.controller.state.favorites or (ep and ep in fav_eps):
                        _should_purge = False
                        _purge_reason = ""
                        if not is_asian_node(n, colo=c_val):
                            _should_purge = True
                            _purge_reason = "非亚洲地区/命名"
                        else:
                            colo_hist = self.controller.state.node_colo_history.get(n, self.controller.state.node_colo_history.get(ep, []))
                            if colo_hist:
                                _dom, _, _has_drift, _drift_disp = analyze_colo_stats(colo_hist, time.time(), node_name=n)
                                if _has_drift or not is_asian_node(n, colo=_dom):
                                    _should_purge = True
                                    _purge_reason = f"机房漂移 ({_drift_disp})"
                        if _should_purge:
                            self.controller.state.local_blacklist.add(n)
                            self.controller.state.favorites.discard(n)
                            self.controller.state.blacklist_reasons[n] = _purge_reason
                            if ep:
                                self.controller.state.local_blacklist.add(ep)
                                self.controller.state.blacklist_reasons[ep] = _purge_reason
                                fav_eps.discard(ep)
                                for f in list(self.controller.state.favorites):
                                    if _get_ep(f) == ep:
                                        self.controller.state.favorites.discard(f)
                            if ep and ep in self.controller.state.verified_nodes:
                                del self.controller.state.verified_nodes[ep]
                            self.log_signal.emit(f"【精选审查淘汰】节点 {n} 命中规则：{_purge_reason}，已从精选清除并加入黑名单！")
                            continue

                        fav_sk += 1
                        continue

                    if (n in self.controller.state.verified_nodes) or (ep and ep in star_eps):
                        ver_sk += 1
                        continue

                    ep_to_untested.setdefault(ep, []).append(n)

            # 融合云端 pending.txt 待测端点（严格物理端点 1:1 去重，绝不重复测速）
            for p_ep, p_rem in pending_endpoints.items():
                if p_ep not in ep_to_untested and p_ep not in fav_eps and p_ep not in bl_eps and p_ep not in sbl_eps:
                    ep_to_untested.setdefault(p_ep, []).append(p_ep)

            unique_eps = list(ep_to_untested.keys())
            test_targets = [choose_canonical_node_name(ep_to_untested[ep]) for ep in unique_eps if ep]

            self.log_signal.emit(
                f"全量节点: {len(self.controller.state.all_nodes)} 个 | 严格限制亚洲节点 | "
                f"跳过精选: {fav_sk} | 跳过延迟黑名单: {d_sk} | 跳过低速黑名单: {s_sk} | "
                f"待测独立节点: {len(test_targets)} 个 (同源马甲已自动聚合)"
            )

            if not test_targets:
                self.status_signal.emit("无须测速")
                self.finished_signal.emit(True, "所有节点均位于精选、黑名单或沉淀池中，无新的待测节点！")
                return

            # 初始化待测表格行
            ep_to_row = {}
            test_rows = []
            with self.controller.state.lock:
                for ep in unique_eps:
                    rep_name = choose_canonical_node_name(ep_to_untested[ep])
                    c_hist = self.controller.state.node_colo_history.get(rep_name, self.controller.state.node_colo_history.get(ep, []))
                    c_disp = "-"
                    if c_hist:
                        _, _, _, c_disp = analyze_colo_stats(c_hist, time.time(), node_name=rep_name)

                    row = {
                        "status": "排队中...",
                        "colo": self.controller.state.node_colo.get(rep_name, self.controller.state.node_colo.get(ep, "-")),
                        "colo_hist": c_disp,
                        "reason": "-",
                        "delay": "-",
                        "avg_delay": "-",
                        "delay_hist": "-",
                        "hist_avg": "-",
                        "speed": "-",
                        "speed_hist": "-",
                        "name": rep_name,
                        "endpoint": ep,
                    }
                    ep_to_row[ep] = row
                    test_rows.append(row)

            self.rows_updated.emit([dict(r) for r in test_rows])
            self.status_signal.emit(f"待测节点: {len(test_rows)} 个")

            # 2. 多轮真实代理延迟初筛 (严格按设置参数 rounds 与 timeout_ms 执行真实链路测试)
            self.log_signal.emit(
                f"⚡ 开始执行 {rounds} 轮真实代理延迟初筛 (独立端点共 {len(unique_eps)} 个，单次超时上限: {timeout_ms}ms)..."
            )

            # 建立物理端点 -> 内核代理节点映射表，确保 100% 真实代理应用层测速
            core_proxies = self.controller.clash_client.get_proxies()
            ep_to_core_node = {}
            for p_name, p_info in core_proxies.items():
                if isinstance(p_info, dict):
                    s = p_info.get("server", "").strip()
                    p = str(p_info.get("port", "443")).strip()
                    if s:
                        ep_to_core_node[f"{s}:{p}"] = p_name

            all_known_nodes = set(self.controller.state.all_nodes)

            for r in range(1, rounds + 1):
                if self.isInterruptionRequested():
                    break

                total_eps = len(unique_eps)
                done_cnt = 0
                alive_cnt = 0
                done_lock = threading.Lock()
                last_log_t = 0.0
                last_status_t = 0.0

                def _single_delay(endpoint):
                    if self.isInterruptionRequested():
                        return
                    rep_node = choose_canonical_node_name(ep_to_untested[endpoint])
                    target_proxy_name = None
                    if rep_node in core_proxies:
                        target_proxy_name = rep_node
                    elif rep_node in all_known_nodes and rep_node in core_proxies:
                        target_proxy_name = rep_node
                    elif endpoint in ep_to_core_node:
                        target_proxy_name = ep_to_core_node[endpoint]

                    if target_proxy_name:
                        # 100% 真实代理链路测速：调用内核 RESTful API 发起真实 HTTP/HTTPS 延迟探测
                        cur_delay = self.controller.clash_client.query_proxy_delay(target_proxy_name, test_url, timeout_ms=timeout_ms)
                    else:
                        # 纯正测速原则：严禁使用 TCP ping 降级伪造代理延迟！内核未挂载的端点直接判定超时
                        cur_delay = 99999

                    with self.controller.state.lock:
                        if cur_delay < 99999:
                            _record_delay_sample(self.controller.state.node_delay_history, endpoint, cur_delay)
                        for n in ep_to_untested[endpoint]:
                            self.controller.state.node_delays[n] = cur_delay
                            hist = self.controller.state.node_history.setdefault(n, [])
                            hist.append(cur_delay)
                            self.controller.state.node_history[n] = hist[-rounds:]
                            if cur_delay < 99999:
                                _record_delay_sample(self.controller.state.node_delay_history, n, cur_delay)

                    row_ref = ep_to_row.get(endpoint)
                    if row_ref:
                        row_ref["delay"] = f"{cur_delay}ms" if cur_delay < 99999 else "超时"
                        h_vals = self.controller.state.node_history.get(rep_node, [])
                        row_ref["delay_hist"] = "/".join(str(v) if v < 99999 else "超时" for v in h_vals)
                        valid_vals = [v for v in h_vals if v < 99999]
                        if valid_vals:
                            row_ref["avg_delay"] = f"{int(sum(valid_vals)/len(valid_vals))} ms"

                    nonlocal done_cnt, alive_cnt, last_log_t, last_status_t
                    with done_lock:
                        done_cnt += 1
                        if cur_delay < 99999:
                            alive_cnt += 1
                        now_t = time.time()
                        # 每 50 个节点步长，或经过 1 秒，或最后一批时输出透明平滑进度
                        step_cond = (done_cnt % 50 == 0) or (now_t - last_log_t >= 1.0) or (done_cnt == total_eps)
                        if step_cond:
                            last_log_t = now_t
                            pct = int(done_cnt * 100 / total_eps)
                            cur_d_str = f"{cur_delay}ms" if cur_delay < 99999 else "超时"
                            self.log(
                                f"⚡ [初筛第 {r}/{rounds} 轮] 进度: {done_cnt}/{total_eps} ({pct}%) | "
                                f"实时存活: {alive_cnt} 个 | 最新端点: {endpoint} ({cur_d_str})"
                            )
                        if (now_t - last_status_t >= 0.5) or done_cnt == total_eps:
                            last_status_t = now_t
                            self.status_signal.emit(f"延迟初筛中: 第 {r}/{rounds} 轮 ({done_cnt}/{total_eps}) 存活:{alive_cnt}")

                with ThreadPoolExecutor(max_workers=min(20, len(unique_eps))) as executor:
                    list(executor.map(_single_delay, unique_eps))

                self.rows_updated.emit([dict(x) for x in test_rows])
                if self.isInterruptionRequested():
                    break
                time.sleep(0.5)

            if self.isInterruptionRequested():
                self.log("⏹ 用户已终止流水线任务")
                self.finished_signal.emit(False, "任务已被用户手动终止")
                return

            # 3. 达标排查与淘汰审计 (全部轮次完整跑完后，结合最佳延迟门槛、黑名单门槛与抖动机制综合审计)
            candidates = []
            newly_delay_blacklisted = 0
            for n in test_targets:
                if self.isInterruptionRequested():
                    break
                ep = _get_ep(n)
                hist = self.controller.state.node_history.get(n, [])
                best_delay = min(hist[-rounds:]) if hist else 99999

                # 延迟未达到设定要求 (> max_delay) 或超时 (>= 99999) 或超标 (>= bl_delay_threshold) 淘汰拉黑
                if best_delay > max_delay or best_delay >= bl_delay_threshold or best_delay >= 99999:
                    if best_delay >= 99999:
                        d_reason = "延迟超时 (≥99999ms)"
                    elif best_delay >= bl_delay_threshold:
                        d_reason = f"延迟超标 ({best_delay}ms ≥ {bl_delay_threshold}ms)"
                    else:
                        d_reason = f"延迟淘汰 ({best_delay}ms > {max_delay}ms)"

                    now_bl_t = time.time()
                    with self.controller.state.lock:
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = d_reason
                        self.controller.state.blacklist_timestamps[n] = now_bl_t
                        if ep:
                            self.controller.state.local_blacklist.add(ep)
                            self.controller.state.blacklist_reasons[ep] = d_reason
                            self.controller.state.blacklist_timestamps[ep] = now_bl_t
                        for same_n in ep_to_untested.get(ep, []):
                            self.controller.state.local_blacklist.add(same_n)
                            self.controller.state.favorites.discard(same_n)
                            self.controller.state.blacklist_reasons[same_n] = d_reason
                            self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]

                    if ep in ep_to_row:
                        ep_to_row[ep]["status"] = "延迟淘汰"
                        ep_to_row[ep]["reason"] = d_reason

                    newly_delay_blacklisted += 1
                    continue

                # 节点抖动拉黑机制：最低延迟≥设定值且向上抖动≥设定值，立即拉黑淘汰（最高延迟<设定最低延迟则豁免）
                is_j_bad, j_min, j_up = check_node_jitter_blacklisted(
                    hist[-rounds:], jitter_min_d, jitter_up_th
                )
                if is_j_bad:
                    j_reason = f"延迟抖动淘汰 (底{j_min}ms 抖动+{j_up}ms)"
                    now_bl_t = time.time()
                    with self.controller.state.lock:
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = j_reason
                        self.controller.state.blacklist_timestamps[n] = now_bl_t
                        if ep:
                            self.controller.state.local_blacklist.add(ep)
                            self.controller.state.blacklist_reasons[ep] = j_reason
                            self.controller.state.blacklist_timestamps[ep] = now_bl_t
                        for same_n in ep_to_untested.get(ep, []):
                            self.controller.state.local_blacklist.add(same_n)
                            self.controller.state.favorites.discard(same_n)
                            self.controller.state.blacklist_reasons[same_n] = j_reason
                            self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]

                    if ep in ep_to_row:
                        ep_to_row[ep]["status"] = "抖动淘汰"
                        ep_to_row[ep]["reason"] = j_reason

                    newly_delay_blacklisted += 1
                    self.log(f"【抖动淘汰】节点 {n} 最低延迟 {j_min}ms (≥{jitter_min_d}ms)，向上抖动 +{j_up}ms (≥{jitter_up_th}ms)，拉黑淘汰！")
                    continue

                cur_avg, hist_avg = compute_delay_stats(
                    n,
                    ep=ep,
                    node_history=self.controller.state.node_history,
                    node_delays=self.controller.state.node_delays,
                    node_delay_history=self.controller.state.node_delay_history,
                    get_node_endpoint_fn=_get_ep,
                )
                if ep in ep_to_row:
                    ep_to_row[ep]["status"] = "初筛达标"
                    ep_to_row[ep]["reason"] = f"延迟达标 ({best_delay}ms ≤ {max_delay}ms)"
                    ep_to_row[ep]["avg_delay"] = cur_avg
                    ep_to_row[ep]["hist_avg"] = hist_avg

                candidates.append(n)

            self.log(
                f"🏁 [延迟初筛完毕] 共 {len(candidates)} 个候选节点达标 (≤{max_delay}ms，淘汰超标/抖动: {newly_delay_blacklisted} 个)，立即转入真实 Colo 测定与测速..."
            )

            # 仅保留通过延迟考核合格的端点行，单次通知 UI 表格装配
            surviving_eps = { _get_ep(c) for c in candidates if _get_ep(c) }
            test_rows = [r for r in test_rows if r.get("endpoint") in surviving_eps]
            ep_to_row = { r["endpoint"]: r for r in test_rows if "endpoint" in r }
            self.rows_updated.emit([dict(x) for x in test_rows])
            self.status_signal.emit(f"初筛完毕: 合格 {len(candidates)} 个")

            if not candidates:
                self.status_signal.emit("无达标节点")
                self.finished_signal.emit(True, f"延迟初筛结束：所有待测节点延迟均未达到 ≤{max_delay}ms。")
                return

            # 3. 真实 Colo 测定与防漂移审计 (Step 3/4)
            candidates.sort(key=lambda n: min(self.controller.state.node_history.get(n, [99999])))
            self.log_signal.emit(f"正在对 {len(candidates)} 个候选节点校准真实 Colo 并录入 7 天时序桶...")
            self.status_signal.emit(f"Colo 校准: {len(candidates)} 个节点")

            def _probe_colo(n):
                if self.isInterruptionRequested():
                    return
                ep = _get_ep(n)
                if ":" in ep:
                    if ep.startswith("[") and "]:" in ep:
                        ip, port_str = ep[1:].split("]:", 1)
                    elif ep.count(":") > 1:
                        ip, port_str = ep.rsplit(":", 1)
                    else:
                        ip, port_str = ep.split(":", 1)
                    try:
                        port = int(port_str)
                    except (ValueError, TypeError):
                        port = 443
                    try:
                        c_code, c_disp = get_cf_colo_raw(ip, port, timeout=1.5)
                    except Exception:
                        c_code, c_disp = "UNKNOWN", "未知机房"
                    with self.controller.state.lock:
                        record_colo_sample(
                            self.controller.state.node_colo_history,
                            n,
                            ep,
                            c_code,
                            c_disp,
                            now=time.time(),
                            node_colo_dict=self.controller.state.node_colo,
                        )
                    if ep in ep_to_row:
                        ep_to_row[ep]["colo"] = c_disp
                        c_hist = self.controller.state.node_colo_history.get(n, self.controller.state.node_colo_history.get(ep, []))
                        if c_hist:
                            _, _, _, disp_str = analyze_colo_stats(c_hist, time.time(), node_name=n)
                            ep_to_row[ep]["colo_hist"] = disp_str

            with ThreadPoolExecutor(max_workers=min(16, len(candidates))) as ex:
                list(ex.map(_probe_colo, candidates))

            self.rows_updated.emit([dict(x) for x in test_rows])

            # 机房漂移排查
            drift_passed_candidates = []
            now_pipe_t = time.time()
            for n in candidates:
                if self.isInterruptionRequested():
                    break
                ep = _get_ep(n)
                colo_hist = self.controller.state.node_colo_history.get(n, self.controller.state.node_colo_history.get(ep, []))
                _, _, has_drift, drift_disp = analyze_colo_stats(colo_hist, now_pipe_t, node_name=n)
                if has_drift:
                    drift_reason = f"机房漂移 ({drift_disp})"
                    now_bl_t = time.time()
                    with self.controller.state.lock:
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = drift_reason
                        self.controller.state.blacklist_timestamps[n] = now_bl_t
                        if ep:
                            self.controller.state.local_blacklist.add(ep)
                            self.controller.state.blacklist_reasons[ep] = drift_reason
                            self.controller.state.blacklist_timestamps[ep] = now_bl_t
                        for same_n in ep_to_untested.get(ep, []):
                            self.controller.state.local_blacklist.add(same_n)
                            self.controller.state.favorites.discard(same_n)
                            self.controller.state.blacklist_reasons[same_n] = drift_reason
                            self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]

                    if ep in ep_to_row:
                        ep_to_row[ep]["status"] = "漂移淘汰"
                        ep_to_row[ep]["reason"] = drift_reason
                    self.log_signal.emit(f"【漂移直接淘汰】节点 {n} 发生机房漂移 ({drift_disp})，直接拉黑并清除！")
                else:
                    drift_passed_candidates.append(n)

            candidates = [n for n in drift_passed_candidates if is_asian_node(n, colo=self.controller.state.node_colo.get(n, self.controller.state.node_colo.get(_get_ep(n))))]
            surviving_eps = { _get_ep(c) for c in candidates if _get_ep(c) }
            test_rows = [r for r in test_rows if r.get("endpoint") in surviving_eps]
            ep_to_row = { r["endpoint"]: r for r in test_rows if "endpoint" in r }
            self.rows_updated.emit([dict(x) for x in test_rows])
            self.controller.data_changed.emit()

            if not candidates:
                self.status_signal.emit("候选节点已漂移淘汰")
                self.finished_signal.emit(True, "候选节点均发生机房漂移或非亚洲已被全部淘汰。")
                return

            # 4. 协议嫁接与真实下行带宽测速 (Step 4/4)
            all_known_nodes = set(self.controller.state.all_nodes)
            clean_endpoints_to_graft = []
            for n in candidates:
                ep = _get_ep(n)
                if n not in all_known_nodes and ep:
                    clean_endpoints_to_graft.append(ep)

            clean_endpoints_to_graft = list(dict.fromkeys(clean_endpoints_to_graft))
            graft_map = {}
            has_fission = False

            if clean_endpoints_to_graft:
                active_sub = getattr(self.controller.state, "active_profile", "") or self.config.get("profile_yaml", "") or "Rw0nNFlVIbnA.yaml"
                donor = find_cf_donor_node(active_profile=active_sub, verified_nodes=self.controller.state.verified_nodes)
                if donor:
                    self.log_signal.emit(f"🧬 [协议嫁接] 成功锁定 Cloudflare 协议母体 [{donor.get('name', 'CF-Donor')} / {donor.get('type')}]，为 {len(clean_endpoints_to_graft)} 个纯净端点实施换头裂变...")
                    fission_proxies = fission_clean_ips(donor, clean_endpoints_to_graft)
                    for p in fission_proxies:
                        graft_map[f"{p['server']}:{p['port']}"] = p["name"]

                    self.log_signal.emit("⚡ [协议嫁接] 正在将裂变代理注入 Script.js 并触发内核热加载...")
                    self.controller.reload_verge_with_fission(fission_proxies)
                    has_fission = True
                    self.log_signal.emit("⏳ 等待裂变节点热加载就绪 (3秒)...")
                    time.sleep(3.0)
                else:
                    self.log_signal.emit("⚠️ [协议嫁接] 未在订阅中寻获具备有效 TLS/SNI 凭证的 Cloudflare 协议母体，跳过协议裂变，保留探活结果。")

            proxies_data = self.controller.clash_client.get_proxies() or {}
            proxies_map = proxies_data if isinstance(proxies_data, dict) else {}
            global_info = proxies_map.get("GLOBAL", {})
            orig_global = global_info.get("now", "")
            global_all = global_info.get("all", [])

            mixed_port = self.controller.clash_client.get_mixed_port(default=7897)

            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE

            proxy_handler = urllib.request.ProxyHandler({
                "http": f"http://127.0.0.1:{mixed_port}",
                "https": f"http://127.0.0.1:{mixed_port}",
            })
            https_handler = urllib.request.HTTPSHandler(context=ssl_ctx)
            speed_opener = urllib.request.build_opener(proxy_handler, https_handler)

            total_cand = len(candidates)
            orig_group_selections = {}
            premium_nodes = []
            tested_endpoint_speeds = {}
            hit_target_early = False
            newly_speed_blacklisted = 0

            self.log_signal.emit(f"启动带宽精测 (共 {total_cand} 个候选节点，下行门槛 ≥{min_speed} MB/s)...")

            try:
                with ClashModeGuard(self.controller.clash_client, temporary_mode="global"):
                    for idx, node_name in enumerate(candidates, 1):
                        if self.isInterruptionRequested():
                            break

                        ep = _get_ep(node_name)
                        clash_node_name = graft_map.get(ep, node_name)
                        row_ref = ep_to_row.get(ep)
                        target_str = f" [已集齐: {len(premium_nodes)}/{target_node_limit}]" if target_node_limit > 0 else f" [已入选 {len(premium_nodes)} 个]"
                        self.status_signal.emit(f"带宽精测: [{idx}/{total_cand}]{target_str} {node_name[:16]}...")

                        if row_ref:
                            row_ref["status"] = f"带宽测速中 [{idx}/{total_cand}]"
                            self.rows_updated.emit([dict(r) for r in test_rows])
                        self.log(f"🌐 [真实带宽测速 {idx}/{total_cand}] 正在测试节点真实下行: {node_name} (采样 {duration}s)...")

                        if ep in tested_endpoint_speeds:
                            speed_val = tested_endpoint_speeds[ep]
                        else:
                            target_group = None
                            if "🚀 节点选择" in proxies_map and clash_node_name in proxies_map["🚀 节点选择"].get("all", []):
                                target_group = "🚀 节点选择"
                            elif clash_node_name in global_all:
                                target_group = "GLOBAL"
                            else:
                                for g_name, g_info in proxies_map.items():
                                    if isinstance(g_info, dict) and g_info.get("type", "").lower() == "selector" and g_name != "GLOBAL":
                                        if clash_node_name in g_info.get("all", []):
                                            target_group = g_name
                                            break

                            if not target_group:
                                speed_val = -1.0
                            else:
                                if target_group not in orig_group_selections:
                                    orig_group_selections[target_group] = proxies_map.get(target_group, {}).get("now", "")

                                enc_tg = urllib.parse.quote(target_group, safe="")
                                self.controller.clash_client.call_api(f"/proxies/{enc_tg}", method="PUT", data={"name": clash_node_name})

                                if target_group != "GLOBAL" and target_group in global_all:
                                    enc_glb = urllib.parse.quote("GLOBAL", safe="")
                                    self.controller.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": target_group})

                                time.sleep(0.1)

                                speed_val = -1.0
                                total_bytes = 0
                                speed_timeout = max(1.5, min(3.5, round(duration + 0.5, 1)))
                                node_deadline = time.time() + duration + 1.0
                                try:
                                    req = urllib.request.Request(
                                        speed_url,
                                        headers={
                                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                                            "Connection": "close",
                                        },
                                    )
                                    with speed_opener.open(req, timeout=speed_timeout) as resp:
                                        start_time = time.time()
                                        chunk_size = 16 * 1024
                                        while time.time() - start_time < duration:
                                            if time.time() >= node_deadline or self.isInterruptionRequested():
                                                break
                                            chunk = resp.read(chunk_size)
                                            if not chunk:
                                                break
                                            total_bytes += len(chunk)

                                        elapsed = time.time() - start_time
                                        if elapsed > 0 and total_bytes > 0:
                                            speed_val = round((total_bytes / (1024 * 1024)) / elapsed, 2)
                                        else:
                                            speed_val = 0.0
                                except Exception:
                                    speed_val = -1.0

                                tested_endpoint_speeds[ep] = speed_val

                        with self.controller.state.lock:
                            self.controller.state.node_speeds[node_name] = speed_val
                            if ep:
                                self.controller.state.node_speeds[ep] = speed_val
                            s_hist = self.controller.state.node_speed_history.setdefault(node_name, [])
                            s_hist.append(max(0.0, speed_val))
                            self.controller.state.node_speed_history[node_name] = s_hist[-4:]
                            if ep and ep != node_name:
                                s_hist_ep = self.controller.state.node_speed_history.setdefault(ep, [])
                                s_hist_ep.append(max(0.0, speed_val))
                                self.controller.state.node_speed_history[ep] = s_hist_ep[-4:]

                        if row_ref:
                            row_ref["speed"] = f"{speed_val:.2f} MB/s" if speed_val >= 0 else "失败"
                            s_vals = self.controller.state.node_speed_history.get(node_name, [])
                            row_ref["speed_hist"] = "/".join(f"{s:.1f}" for s in s_vals)

                        colo = self.controller.state.node_colo.get(node_name, self.controller.state.node_colo.get(ep, "JP"))
                        if not colo or colo == "-":
                            colo = "亚洲"

                        if speed_val >= min_speed and is_asian_node(node_name, colo=colo):
                            coronated_name = f"{colo} {speed_val:.2f} MB/s"
                            fav_target_name = coronated_name if coronated_name else node_name
                            premium_nodes.append(fav_target_name)
                            with self.controller.state.lock:
                                self.controller.state.favorites.add(fav_target_name)
                                if node_name != fav_target_name:
                                    self.controller.state.favorites.discard(node_name)
                                    self.controller._migrate_node_name(node_name, fav_target_name, ep)
                                d_val = self.controller.state.node_delays.get(fav_target_name, self.controller.state.node_delays.get(node_name, 0))
                                self.controller.state.fav_reasons[fav_target_name] = f"真实测速达标 ({speed_val:.2f}MB/s)"
                                if ep:
                                    self.controller.state.cloud_endpoints[ep] = coronated_name
                                    if ":" in ep:
                                        self.controller.state.cloud_endpoints[ep.split(":")[0]] = coronated_name

                            if row_ref:
                                row_ref["name"] = coronated_name
                                row_ref["status"] = "优质精选"
                                row_ref["reason"] = f"下行 {speed_val:.2f} MB/s ≥ {min_speed} MB/s"

                            self.log_signal.emit(f"⭐ [优质入选] 节点入选精选: {coronated_name} ({ep}) (实测下行: {speed_val:.2f} MB/s ≥ {min_speed} MB/s)")
                            test_rows = [r for r in test_rows if r.get("endpoint") != ep and r.get("name") not in (node_name, fav_target_name)]
                            self.rows_updated.emit([dict(r) for r in test_rows])
                            self.controller.data_changed.emit()

                            if target_node_limit > 0 and len(premium_nodes) >= target_node_limit:
                                hit_target_early = True
                                self.log_signal.emit(f"🎯 已集齐目标节点数 ({target_node_limit} 个)，提前结束测速！")
                                break
                        else:
                            spd_reason = "下行测速中断/失败" if speed_val < 0 else f"下行未达标 ({speed_val:.2f} < {min_speed} MB/s)"
                            now_bl_t = time.time()
                            with self.controller.state.lock:
                                self.controller.state.speed_blacklist.add(node_name)
                                self.controller.state.favorites.discard(node_name)
                                self.controller.state.blacklist_reasons[node_name] = spd_reason
                                self.controller.state.blacklist_timestamps[node_name] = now_bl_t
                                if ep:
                                    self.controller.state.speed_blacklist.add(ep)
                                    self.controller.state.blacklist_reasons[ep] = spd_reason
                                    self.controller.state.blacklist_timestamps[ep] = now_bl_t
                                for same_n in ep_to_untested.get(ep, []):
                                    self.controller.state.speed_blacklist.add(same_n)
                                    self.controller.state.favorites.discard(same_n)
                                    self.controller.state.blacklist_reasons[same_n] = spd_reason
                                    self.controller.state.blacklist_timestamps[same_n] = now_bl_t
                                if ep in self.controller.state.verified_nodes:
                                    del self.controller.state.verified_nodes[ep]

                            if row_ref:
                                row_ref["status"] = "低速淘汰"
                                row_ref["reason"] = spd_reason

                            newly_speed_blacklisted += 1
                            self.log_signal.emit(f"【低速淘汰】节点 {node_name} 实测下行 {speed_val:.2f} MB/s 未达标 (门槛 ≥{min_speed} MB/s)")
                            test_rows = [r for r in test_rows if r.get("endpoint") != ep and r.get("name") != node_name]
                            self.rows_updated.emit([dict(r) for r in test_rows])
                            self.controller.data_changed.emit()

            finally:
                # 恢复原策略组选择与全局选择
                for g_name, orig_choice in orig_group_selections.items():
                    if orig_choice:
                        enc = urllib.parse.quote(g_name, safe="")
                        self.controller.clash_client.call_api(f"/proxies/{enc}", method="PUT", data={"name": orig_choice})

                if orig_global:
                    enc_glb = urllib.parse.quote("GLOBAL", safe="")
                    self.controller.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": orig_global})

                # 任务收尾物理自愈：若注入了裂变节点，无条件恢复纯净 Script.js 并热重载，彻底抹除临时裂变代理
                if has_fission:
                    self.log_signal.emit("🧹 [物理自愈] 正在清除临时裂变代理，恢复纯净策略组配置...")
                    self.controller.reload_verge_with_fission(None)

            if self.isInterruptionRequested():
                self.log_signal.emit("⏹ 用户已终止流水线任务")
                self.finished_signal.emit(False, "任务已被用户手动终止")
                return

            # 5. 收尾：多池聚合、生成 Script.js 并触发热重载
            self.status_signal.emit("写入 Script.js 并热更...")
            self.log_signal.emit("正在同步更新多池状态、写入 Script.js 策略组配置...")

            with self.controller.state.lock:
                self.controller.state.favorites.update(premium_nodes)
                deduplicate_favorites_by_endpoint(
                    self.controller.state.favorites,
                    self.controller.state.all_nodes,
                    self.controller.state.node_details,
                    _get_ep,
                    choose_canonical_node_name,
                )
                # 剥离越权入孵：全量大优选仅负责将达标节点纳入 favorites，绝对禁止自动塞入 verified_nodes 沉淀孵化池！
                # process_verified_lifecycle(
                #     self.controller.state.verified_nodes,
                #     list(self.controller.state.favorites),
                #     self.controller.state.stars_nodes,
                # )
                purge_invalid_and_blacklisted_from_all_pools(
                    self.controller.state.favorites,
                    self.controller.state.verified_nodes,
                    self.controller.state.stars_nodes,
                    self.controller.state.local_blacklist,
                    self.controller.state.speed_blacklist,
                    _get_ep,
                )

            # 固化配置
            self.controller.save_config(self.controller.get_state_snapshot())

            # 生成并写入 Script.js
            script_code, p_tokens, s_tokens = build_script_js(
                favorites=self.controller.state.favorites,
                stars_nodes=self.controller.state.stars_nodes,
                all_nodes=self.controller.state.all_nodes,
                node_details=self.controller.state.node_details,
                group_interval=group_interval,
                group_tolerance=group_tolerance,
                star_group_interval=star_group_interval,
                star_group_tolerance=star_group_tolerance,
                is_asian_node_fn=is_asian_node,
                get_node_endpoint_fn=_get_ep,
                cloud_endpoints=self.controller.state.cloud_endpoints,
                node_colo=self.controller.state.node_colo,
            )
            write_ok, write_res = write_script_js(script_code)
            if write_ok:
                self.log_signal.emit(f"✅ Script.js 策略组写入成功，生效优选节点 {len(p_tokens)} 个，典藏节点 {len(s_tokens)} 个")
            else:
                self.log_signal.emit(f"⚠️ Script.js 写入失败: {write_res}")

            # 触发系统级热键通知 Clash Verge 重新激活
            time.sleep(0.5)
            hotkey_ok, hotkey_msg = trigger_verge_reactivate_hotkey()
            if hotkey_ok:
                self.log_signal.emit(f"⚡ 热键通知成功: {hotkey_msg}")
            else:
                self.log_signal.emit(f"⚠️ 热键触发反馈: {hotkey_msg}")

            # 避开内核刚重载时的代理端口震荡期（静置 2 秒），确保代理隧道建立
            self.log_signal.emit("⏳ 等待内核网络通道平稳就绪 (2秒)...")
            time.sleep(2.0)

            # 在专属后台自愈通道中平稳执行精选池推云与待测池全量联动清洗（配备 curl 双引擎保底）
            self.controller.trigger_cloud_sync_and_purge_safely()

            summary_msg = f"全量大优选结束：新增入选 {len(premium_nodes)} 个优质极速节点，Script.js 规则已写入并触发热重载生效！"
            self.status_signal.emit("优选流程执行完成")
            self.log_signal.emit(f"🎯 {summary_msg}")
            self.finished_signal.emit(True, summary_msg)

        except Exception as e:
            err_tb = traceback.format_exc()
            self.log_signal.emit(f"流水线执行异常:\n{err_tb}")
            self.status_signal.emit("执行异常")
            self.finished_signal.emit(False, f"执行异常: {str(e)}")
```

## File: `gui_fluent/pipelines/fav_pipeline.py`

```python
"""
优质精选池复测流水线工作线程 (FavPipelineWorker)
基于 QThread 运行，完全解耦 UI 渲染，1:1 平移 gui/app.py 中 start_fav_review_pipeline 核心业务逻辑
"""
import json
import ssl
import sys
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import QThread, pyqtSignal
else:
    from PyQt6.QtCore import QThread, pyqtSignal

from services.subscription_service import get_node_endpoint, choose_canonical_node_name
from services.colo_service import is_asian_node, is_node_hongkong, analyze_colo_stats, record_colo_sample
from services.probe_service import get_cf_colo_raw
from services.clash_client import ClashClient, ClashModeGuard
from services.script_generator import build_script_js, write_script_js
from services.pool_service import (
    purge_invalid_and_blacklisted_from_all_pools,
    process_verified_lifecycle,
)
from services.filter_service import (
    check_node_jitter_blacklisted,
    auto_filter_and_blacklist_non_asia_nodes,
)
from utils.win32_utils import trigger_verge_reactivate_hotkey


def _record_delay_sample(node_delay_history, key_or_name, delay, ep=None, now_ts=None):
    """
    记录时延样本至 7 天时序桶中
    """
    if not delay or delay >= 99999 or delay <= 0:
        return
    if now_ts is None:
        now_ts = time.time()
    keys_to_update = {key_or_name}
    if ep and ep != "127.0.0.1:443":
        keys_to_update.add(ep)
    cutoff = now_ts - 7 * 86400
    for k in keys_to_update:
        if not k:
            continue
        hist = node_delay_history.setdefault(k, [])
        hist.append({"ts": now_ts, "d": int(delay)})
        node_delay_history[k] = [
            x for x in hist if isinstance(x, dict) and x.get("ts", 0) >= cutoff
        ][-30:]


class FavPipelineWorker(QThread):
    """
    优质精选池复检工作线程：
    对当前精选池候选节点执行端点去重、多轮延迟复测、实时机房(Colo)探测、严格机房防漂移审查、
    以及双轨分流(香港/非香港)下行带宽实测与达标早停。
    """

    log_signal = pyqtSignal(str)              # 过程日志
    status_signal = pyqtSignal(str)           # 简短状态词
    rows_updated = pyqtSignal(list)           # 返回当前待测/测试中的 dict 列表
    finished_signal = pyqtSignal(bool, str)   # (是否成功, 结果描述)
    fallback_needed = pyqtSignal(str)         # 触发大优选自愈信号 (原因)

    def __init__(self, controller, config: dict, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.config = dict(config)
        self._stop_requested = False

    def stop(self):
        self._stop_requested = True
        self.requestInterruption()

    def run(self):
        self.log_signal.emit("⚡ 启动优质精选池复检流程 (Fluent 后台线程)...")
        try:
            # 0. 解析配置参数
            f_max_d = int(self.config.get("fav_max_delay", 80)) if str(self.config.get("fav_max_delay", "")).isdigit() else 80
            try:
                f_min_s = float(self.config.get("fav_min_speed", 8.0))
            except Exception:
                f_min_s = 8.0
            f_rounds = max(1, int(self.config.get("fav_rounds", 2))) if str(self.config.get("fav_rounds", "")).isdigit() else 2
            try:
                f_duration = max(0.5, float(self.config.get("fav_speed_duration", 2.0)))
            except Exception:
                f_duration = 2.0
            f_jitter_min_d = int(self.config.get("fav_jitter_min_delay", 70)) if str(self.config.get("fav_jitter_min_delay", "")).isdigit() else 70
            f_jitter_up_th = int(self.config.get("fav_jitter_up_threshold", 15)) if str(self.config.get("fav_jitter_up_threshold", "")).isdigit() else 15

            target_hk = int(self.config.get("fav_target_hk_count", 3)) if str(self.config.get("fav_target_hk_count", "")).isdigit() else 3
            target_nohk = int(self.config.get("fav_target_nohk_count", 5)) if str(self.config.get("fav_target_nohk_count", "")).isdigit() else 5
            early_stop_enabled = bool(self.config.get("fav_quota_early_stop", True))
            fallback_enabled = bool(self.config.get("fav_fallback_enabled", True))

            cfg_global = self.controller.load_config() if hasattr(self.controller, "load_config") else {}
            test_url = str(self.config.get("test_url") or cfg_global.get("test_url") or "https://www.google.com/generate_204").strip()
            speed_url = str(self.config.get("speed_url") or cfg_global.get("speed_url") or "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip").strip()
            # 严格拦截阻断已被 Cloudflare 边缘防火墙掐断 TLS 握手的失效测速源，全面切换为全球极速稳定之 Google CDN 测速源
            if not speed_url or "speed.cloudflare.com" in speed_url:
                speed_url = "https://dl.google.com/android/repository/platform-tools_r34.0.5-windows.zip"
            timeout_ms = int(self.config.get("test_timeout", 1500)) if str(self.config.get("test_timeout", "")).isdigit() else 1500

            group_interval = str(self.config.get("group_interval", "300")).strip() or "300"
            group_tolerance = str(self.config.get("group_tolerance", "20")).strip() or "20"
            star_group_interval = str(self.config.get("star_group_interval", "300")).strip() or "300"
            star_group_tolerance = str(self.config.get("star_group_tolerance", "20")).strip() or "20"

            # 1. 前置准备：拉取远程订阅与云端文本，并热更内核
            self.log_signal.emit("🔄 [前置准备] 正在强制更新远程订阅与云端文本...")
            self.controller.update_remote_subscription_sync()
            self.controller.fetch_cloud_endpoints_sync()

            active_sub = self.controller.state.active_profile or "Rw0nNFlVIbnA.yaml"
            self.controller.load_nodes_from_profile(active_sub)
            self.controller.generate_script_and_reload()
            time.sleep(3)  # 给予内核重载缓冲

            def _get_ep(node_name):
                return get_node_endpoint(node_name, node_details=self.controller.state.node_details)

            # 建立当前订阅中 IP:Port -> 订阅中可用代理节点名的逆向映射表
            current_ep_to_proxy = {}
            for node in self.controller.state.all_nodes:
                ep = _get_ep(node)
                if ep and ep not in current_ep_to_proxy:
                    current_ep_to_proxy[ep] = node

            # 穿透提取待复测的真实代理节点
            active_fav_targets = []
            seen_targets = set()
            fav_origin_map = {}

            with self.controller.state.lock:
                # 优先执行非亚洲节点过滤
                auto_filter_and_blacklist_non_asia_nodes(
                    all_nodes=list(self.controller.state.favorites),
                    local_blacklist=self.controller.state.local_blacklist,
                    favorites=self.controller.state.favorites,
                    blacklist_reasons=self.controller.state.blacklist_reasons,
                    get_node_endpoint_fn=_get_ep,
                    is_asian_node_fn=is_asian_node,
                    node_colo_dict=self.controller.state.node_colo,
                )

                for f in list(self.controller.state.favorites):
                    target_ep = _get_ep(f) or str(f)
                    # 如果能在当前订阅中找到该物理端点对应的实体节点
                    matched_proxy = current_ep_to_proxy.get(target_ep)
                    if matched_proxy:
                        c_val = self.controller.state.node_colo.get(matched_proxy, self.controller.state.node_colo.get(target_ep, "-"))
                        if matched_proxy not in seen_targets and is_asian_node(matched_proxy, colo=c_val):
                            active_fav_targets.append(matched_proxy)
                            seen_targets.add(matched_proxy)
                            fav_origin_map[matched_proxy] = f
                    elif f in self.controller.state.all_nodes:
                        c_val = self.controller.state.node_colo.get(f, self.controller.state.node_colo.get(target_ep, "-"))
                        if is_asian_node(f, colo=c_val):
                            if f not in seen_targets:
                                active_fav_targets.append(f)
                                seen_targets.add(f)
                                fav_origin_map[f] = f

            tot = len(active_fav_targets)
            self.log_signal.emit(f"优质池待复测节点共 {tot} 个 (已穿透对齐 C 段端点 | 达标即停={early_stop_enabled})")

            if not active_fav_targets:
                self.log_signal.emit("优质精选池中暂无可用的存活节点。")
                if fallback_enabled:
                    self.log_signal.emit("⚡ 优质池无存活节点，触发自愈大优选...")
                    self.fallback_needed.emit("优质池中无存活节点")
                    self.finished_signal.emit(False, "优质池无存活节点，已触发自愈大优选")
                else:
                    self.finished_signal.emit(False, "优质精选池中暂无可用的存活节点")
                return

            # 2. 内核连通性校验
            conn_ok, conn_ver = self.controller.get_clash_connection_status()
            if not conn_ok:
                self.log_signal.emit("❌ 无法连接 Clash 内核！")
                self.status_signal.emit("内核未连接")
                self.finished_signal.emit(False, "无法连接 Clash 内核")
                return

            # 3. 初始化待测节点延迟状态
            with self.controller.state.lock:
                for n in active_fav_targets:
                    self.controller.state.node_delays[n] = None
                    self.controller.state.node_history[n] = []

            self.controller.data_changed.emit()

            self.status_signal.emit(f"[优质复测] 检测 {tot} 个优质候选延迟...")

            # 4. 多轮并发延迟测试 (端点去重)
            for r in range(1, f_rounds + 1):
                if self._stop_requested or self.isInterruptionRequested():
                    self.log_signal.emit("优质池复测已被手动终止。")
                    self.status_signal.emit("已终止")
                    self.finished_signal.emit(False, "用户手动终止任务")
                    return

                ep_to_nodes = {}
                for n in active_fav_targets:
                    ep = _get_ep(n)
                    ep_to_nodes.setdefault(ep, []).append(n)

                def _fav_delay(endpoint):
                    if self._stop_requested or self.isInterruptionRequested():
                        return
                    rep_node = ep_to_nodes[endpoint][0]
                    cur_d = self.controller.clash_client.query_proxy_delay(rep_node, test_url, timeout_ms=timeout_ms)
                    with self.controller.state.lock:
                        if cur_d < 99999:
                            _record_delay_sample(self.controller.state.node_delay_history, endpoint, cur_d)
                        for n in ep_to_nodes[endpoint]:
                            self.controller.state.node_delays[n] = cur_d
                            hist = self.controller.state.node_history.setdefault(n, [])
                            hist.append(cur_d)
                            self.controller.state.node_history[n] = hist[-f_rounds:]
                            if cur_d < 99999:
                                _record_delay_sample(self.controller.state.node_delay_history, n, cur_d)

                with ThreadPoolExecutor(max_workers=8) as ex:
                    list(ex.map(_fav_delay, list(ep_to_nodes.keys())))

                self.controller.data_changed.emit()
                if self._stop_requested or self.isInterruptionRequested():
                    self.log_signal.emit("优质池复测已被手动终止。")
                    self.status_signal.emit("已终止")
                    self.finished_signal.emit(False, "用户手动终止任务")
                    return
                time.sleep(0.5)

            # 5. 达标初筛：延迟门槛与抖动淘汰
            temp_passed = []
            with self.controller.state.lock:
                for n in active_fav_targets:
                    hist = self.controller.state.node_history.get(n, [99999])
                    best_d = min(hist[-f_rounds:]) if hist else 99999
                    if best_d > f_max_d or best_d >= 99999:
                        d_reason = "延迟超时 (≥99999ms)" if best_d >= 99999 else f"复测延迟淘汰 ({best_d}ms > {f_max_d}ms)"
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = d_reason
                        ep = _get_ep(n)
                        if ep:
                            self.controller.state.blacklist_reasons[ep] = d_reason
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]
                        self.log_signal.emit(f"【优质淘汰-延迟超标】节点 {n} 延迟 {best_d}ms 未达门槛(≤{f_max_d}ms)，直接拉黑淘汰！")
                        continue

                    is_j_bad, j_min, j_up = check_node_jitter_blacklisted(
                        hist[-f_rounds:], f_jitter_min_d, f_jitter_up_th
                    )
                    if is_j_bad:
                        j_reason = f"复测抖动淘汰 (底{j_min}ms 抖动+{j_up}ms)"
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = j_reason
                        ep = _get_ep(n)
                        if ep:
                            self.controller.state.blacklist_reasons[ep] = j_reason
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]
                        self.log_signal.emit(f"【优质淘汰-抖动超标】节点 {n} 最低延迟 {j_min}ms (≥{f_jitter_min_d}ms)，向上抖动 +{j_up}ms (≥{f_jitter_up_th}ms)，直接拉黑淘汰！")
                        continue

                    temp_passed.append(n)

            if self._stop_requested or self.isInterruptionRequested():
                self.status_signal.emit("已终止")
                self.finished_signal.emit(False, "用户手动终止任务")
                return

            # 6. 实时机房 (Colo) 物理探测与采样
            self.status_signal.emit(f"[优质复测] 正在核验 {len(temp_passed)} 个候选的物理机房(Colo)...")

            def _probe_fav_colo(n):
                ep = _get_ep(n)
                if ":" in ep:
                    raw_ip, raw_port = ep.rsplit(":", 1)
                    c_code, c_disp = get_cf_colo_raw(raw_ip, raw_port, timeout=1.5)
                    with self.controller.state.lock:
                        record_colo_sample(self.controller.state.node_colo_history, n, ep, c_code, c_disp)
                        self.controller.state.node_colo[n] = c_disp
                        if ep:
                            self.controller.state.node_colo[ep] = c_disp

            with ThreadPoolExecutor(max_workers=10) as ex:
                list(ex.map(_probe_fav_colo, temp_passed))

            self.controller.data_changed.emit()

            # 7. 严格机房漂移审查：发生机房漂移一次即直接拉黑淘汰
            drift_passed = []
            now_fav_t = time.time()
            with self.controller.state.lock:
                for n in temp_passed:
                    ep = _get_ep(n)
                    colo_hist = self.controller.state.node_colo_history.get(n, self.controller.state.node_colo_history.get(ep, []))
                    _, _, has_drift, drift_disp = analyze_colo_stats(colo_hist, now_fav_t, node_name=n)
                    if has_drift:
                        drift_reason = f"机房漂移 ({drift_disp})"
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = drift_reason
                        if ep:
                            self.controller.state.blacklist_reasons[ep] = drift_reason
                        if ep in self.controller.state.verified_nodes:
                            del self.controller.state.verified_nodes[ep]
                        self.log_signal.emit(f"【优质淘汰-机房漂移】节点 {n} 发生机房漂移 ({drift_disp})，直接拉黑淘汰！")
                    else:
                        drift_passed.append(n)
            temp_passed = drift_passed

            # 8. 分流香港候选与非香港候选
            hk_candidates = []
            nohk_candidates = []
            with self.controller.state.lock:
                for n in temp_passed:
                    c_val = self.controller.state.node_colo.get(n, self.controller.state.node_colo.get(_get_ep(n), "-"))
                    if not is_asian_node(n, colo=c_val):
                        self.controller.state.local_blacklist.add(n)
                        self.controller.state.favorites.discard(n)
                        self.controller.state.blacklist_reasons[n] = "非亚洲地区/命名"
                        continue
                    if is_node_hongkong(n):
                        hk_candidates.append(n)
                    else:
                        nohk_candidates.append(n)

                hk_candidates.sort(key=lambda n: min(self.controller.state.node_history.get(n, [99999])))
                nohk_candidates.sort(key=lambda n: min(self.controller.state.node_history.get(n, [99999])))

            self.log_signal.emit(f"优质复检初筛通过（经Colo物理核验）：香港候选 {len(hk_candidates)} 个，非香港候选 {len(nohk_candidates)} 个")

            if self._stop_requested or self.isInterruptionRequested():
                self.status_signal.emit("已终止")
                self.finished_signal.emit(False, "用户手动终止任务")
                return

            # 9. 下行真实带宽测速 (ClashModeGuard 保护下切换全局模式)
            proxies_map = self.controller.clash_client.get_proxies()
            global_info = proxies_map.get("GLOBAL", {})
            orig_global = global_info.get("now", "")
            global_all = global_info.get("all", [])

            mixed_port = self.controller.clash_client.get_mixed_port(default=7897)
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            speed_opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({
                    "http": f"http://127.0.0.1:{mixed_port}",
                    "https": f"http://127.0.0.1:{mixed_port}",
                }),
                urllib.request.HTTPSHandler(context=ssl_ctx)
            )

            qualified_hk = []
            qualified_nohk = []
            tested_ep_speeds = {}
            orig_group_selections = {}
            google_hk_detected_nodes = set()

            fav_mode_guard = ClashModeGuard(self.controller.clash_client, temporary_mode="global")
            fav_mode_guard.__enter__()
            try:
                def _test_single_speed(n, track_label, cur_cnt, tgt_cnt):
                    ep = _get_ep(n)
                    if ep in tested_ep_speeds:
                        spd = tested_ep_speeds[ep]
                        with self.controller.state.lock:
                            self.controller.state.node_speeds[n] = spd
                            h = self.controller.state.node_speed_history.setdefault(n, [])
                            h.append(max(0.0, spd))
                            self.controller.state.node_speed_history[n] = h[-4:]
                        return spd

                    tgt_text = f"{tgt_cnt}" if early_stop_enabled else "全测"
                    self.status_signal.emit(f"[优质复测-{track_label}] 目标:{cur_cnt}/{tgt_text} | 测速: {n[:18]}...")

                    target_group = None
                    if "🚀 节点选择" in proxies_map and n in proxies_map["🚀 节点选择"].get("all", []):
                        target_group = "🚀 节点选择"
                    elif n in global_all:
                        target_group = "GLOBAL"
                    else:
                        for g_name, g_info in proxies_map.items():
                            if g_info.get("type", "").lower() == "selector" and g_name != "GLOBAL":
                                if n in g_info.get("all", []):
                                    target_group = g_name
                                    break

                    if not target_group:
                        return 0.0

                    if target_group not in orig_group_selections:
                        orig_group_selections[target_group] = proxies_map.get(target_group, {}).get("now", "")

                    enc_tg = urllib.parse.quote(target_group, safe="")
                    self.controller.clash_client.call_api(
                        f"/proxies/{enc_tg}", method="PUT", data={"name": n}
                    )

                    # 在 global 模式下，直接切换 GLOBAL 策略组指向当前节点，实现 100% 物理直达穿透
                    if n in global_all:
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self.controller.clash_client.call_api(
                            f"/proxies/{enc_glb}", method="PUT", data={"name": n}
                        )
                    elif target_group != "GLOBAL" and target_group in global_all:
                        enc_glb = urllib.parse.quote("GLOBAL", safe="")
                        self.controller.clash_client.call_api(
                            f"/proxies/{enc_glb}", method="PUT", data={"name": target_group}
                        )

                    time.sleep(0.15)

                    # 非香港赛道专属：Google 送中与官方拦截洁净度感知探测 (打标分流，不粗暴判 0)
                    if track_label == "非香港":
                        try:
                            g_req = urllib.request.Request(
                                "https://www.google.com",
                                headers={"User-Agent": "Mozilla/5.0"}
                            )
                            with speed_opener.open(g_req, timeout=2.5) as g_resp:
                                final_gurl = g_resp.geturl()
                                if "google.com.hk" in final_gurl or "sorry" in final_gurl:
                                    google_hk_detected_nodes.add(n)
                                    tag_label = "送中重定向" if "google.com.hk" in final_gurl else "官方验证拦截"
                                    self.log_signal.emit(
                                        f"🏷️ [Google合规打标] 节点 {n} 遭{tag_label} ({final_gurl})，将打上 [送中] 标并转入常规优选组！"
                                    )
                        except urllib.error.HTTPError as he:
                            if he.code in (429, 403) or "sorry" in getattr(he, "url", ""):
                                google_hk_detected_nodes.add(n)
                                self.log_signal.emit(
                                    f"🏷️ [Google合规打标] 节点 {n} 遭官方风控拦截 (HTTP {he.code})，将打上 [送中] 标并转入常规优选组！"
                                )
                        except Exception:
                            pass

                    speed_val = 0.0
                    total_bytes = 0
                    # 消除 2.5s 硬编码截断 Bug，给予网络握手与下载充足裕量
                    fav_speed_timeout = max(5.0, round(f_duration + 3.0, 1))
                    fav_node_deadline = time.time() + f_duration + 3.0
                    try:
                        req = urllib.request.Request(
                            speed_url,
                            headers={"User-Agent": "Mozilla/5.0", "Connection": "close"}
                        )
                        with speed_opener.open(req, timeout=fav_speed_timeout) as resp:
                            st = time.time()
                            chunk_size = 64 * 1024
                            while time.time() - st < f_duration:
                                if time.time() >= fav_node_deadline or self._stop_requested or self.isInterruptionRequested():
                                    break
                                ch = resp.read(chunk_size)
                                if not ch:
                                    break
                                total_bytes += len(ch)
                            el = time.time() - st
                            speed_val = round((total_bytes / (1024 * 1024)) / el, 2) if (el > 0 and total_bytes > 0) else 0.0
                    except Exception as e:
                        self.log_signal.emit(f"⚠️ 节点 {n[:18]} 测速网络异常 ({type(e).__name__}: {e})")
                        speed_val = -1.0

                    tested_ep_speeds[ep] = speed_val
                    with self.controller.state.lock:
                        self.controller.state.node_speeds[n] = speed_val
                        h = self.controller.state.node_speed_history.setdefault(n, [])
                        h.append(max(0.0, speed_val))
                        self.controller.state.node_speed_history[n] = h[-4:]

                    return speed_val

                # 测试香港队列
                for n in hk_candidates:
                    if self._stop_requested or self.isInterruptionRequested():
                        break
                    if early_stop_enabled and target_hk > 0 and len(qualified_hk) >= target_hk:
                        self.log_signal.emit(f"优质复测-香港队列已达目标 ({len(qualified_hk)}/{target_hk})，早停")
                        break
                    spd = _test_single_speed(n, "香港", len(qualified_hk), target_hk)
                    if spd >= f_min_s:
                        qualified_hk.append(n)
                        cur_d = self.controller.state.node_delays.get(n, 0)
                        self.controller.state.fav_reasons[n] = f"复测考核留任 ({cur_d}ms / {spd:.2f}MB/s)"
                        with self.controller.state.lock:
                            orig_f = fav_origin_map.get(n, n)
                            if orig_f != n:
                                self.controller._migrate_node_name(orig_f, n, _get_ep(n))
                            self.controller.state.favorites.add(n)
                        self.controller.data_changed.emit()
                    else:
                        spd_reason = "下行测速中断/失败" if spd < 0 else f"复测下行淘汰 ({spd:.2f} < {f_min_s} MB/s)"
                        with self.controller.state.lock:
                            orig_f = fav_origin_map.get(n, n)
                            self.controller.state.speed_blacklist.add(n)
                            self.controller.state.favorites.discard(n)
                            if orig_f != n:
                                self.controller.state.speed_blacklist.add(orig_f)
                                self.controller.state.favorites.discard(orig_f)
                                self.controller.state.blacklist_reasons[orig_f] = spd_reason
                            self.controller.state.blacklist_reasons[n] = spd_reason
                            ep = _get_ep(n)
                            if ep:
                                self.controller.state.blacklist_reasons[ep] = spd_reason
                            if ep in self.controller.state.verified_nodes:
                                del self.controller.state.verified_nodes[ep]
                        self.log_signal.emit(f"【优质淘汰-低速淘汰】香港节点 {n} 下行 {spd:.2f} MB/s 未达标(≥{f_min_s} MB/s)，直接拉黑淘汰！")

                # 测试非香港队列
                for n in nohk_candidates:
                    if self._stop_requested or self.isInterruptionRequested():
                        break
                    if early_stop_enabled and target_nohk > 0 and len(qualified_nohk) >= target_nohk:
                        self.log_signal.emit(f"优质复测-非香港队列已达目标 ({len(qualified_nohk)}/{target_nohk})，早停")
                        break
                    spd = _test_single_speed(n, "非香港", len(qualified_nohk), target_nohk)
                    if spd >= f_min_s:
                        cur_d = self.controller.state.node_delays.get(n, 0)
                        if n in google_hk_detected_nodes:
                            # 打上 [送中] 标签并更名
                            if "[送中]" not in n:
                                m = re.search(r"([\d.]+\s*MB/s)", n)
                                target_name = f"{n[:m.start()]}[送中] {n[m.start():]}" if m else f"{n} [送中]"
                            else:
                                target_name = n

                            with self.controller.state.lock:
                                orig_f = fav_origin_map.get(n, n)
                                if orig_f != target_name:
                                    self.controller._migrate_node_name(orig_f, target_name, _get_ep(n))
                                self.controller.state.favorites.add(target_name)
                                self.controller.state.fav_reasons[target_name] = f"Google送中打标留任常规组 ({cur_d}ms / {spd:.2f}MB/s)"
                                self.controller.state.node_speeds[target_name] = spd
                                self.controller.state.node_delays[target_name] = cur_d
                            self.controller.data_changed.emit()
                            self.log_signal.emit(f"✅ 节点 【{target_name}】 达标留任！由于带有 [送中] 标记，将自动服务于【常规自动组】，不占用非港名额。")
                            # 注意：不加入 qualified_nohk，让非香港队列继续测试其他纯净节点，直到凑齐 target_nohk
                        else:
                            # 纯净非香港节点，正常进入非香港配额
                            qualified_nohk.append(n)
                            self.controller.state.fav_reasons[n] = f"复测考核留任 ({cur_d}ms / {spd:.2f}MB/s)"
                            with self.controller.state.lock:
                                orig_f = fav_origin_map.get(n, n)
                                if orig_f != n:
                                    self.controller._migrate_node_name(orig_f, n, _get_ep(n))
                                self.controller.state.favorites.add(n)
                            self.controller.data_changed.emit()
                    else:
                        spd_reason = "下行测速中断/失败" if spd < 0 else f"复测下行淘汰 ({spd:.2f} < {f_min_s} MB/s)"
                        with self.controller.state.lock:
                            orig_f = fav_origin_map.get(n, n)
                            self.controller.state.speed_blacklist.add(n)
                            self.controller.state.favorites.discard(n)
                            if orig_f != n:
                                self.controller.state.speed_blacklist.add(orig_f)
                                self.controller.state.favorites.discard(orig_f)
                                self.controller.state.blacklist_reasons[orig_f] = spd_reason
                            self.controller.state.blacklist_reasons[n] = spd_reason
                            ep = _get_ep(n)
                            if ep:
                                self.controller.state.blacklist_reasons[ep] = spd_reason
                            if ep in self.controller.state.verified_nodes:
                                del self.controller.state.verified_nodes[ep]
                        self.log_signal.emit(f"【优质淘汰-低速淘汰】非香港节点 {n} 下行 {spd:.2f} MB/s 未达标(≥{f_min_s} MB/s)，直接拉黑淘汰！")

            finally:
                # 恢复原策略组选择
                for g_name, orig_choice in orig_group_selections.items():
                    if orig_choice:
                        enc = urllib.parse.quote(g_name, safe="")
                        self.controller.clash_client.call_api(f"/proxies/{enc}", method="PUT", data={"name": orig_choice})

                if orig_global:
                    enc_glb = urllib.parse.quote("GLOBAL", safe="")
                    self.controller.clash_client.call_api(f"/proxies/{enc_glb}", method="PUT", data={"name": orig_global})

                fav_mode_guard.__exit__(None, None, None)

            if self._stop_requested or self.isInterruptionRequested():
                self.status_signal.emit("已终止")
                self.finished_signal.emit(False, "用户手动终止任务")
                return

            total_final_selected = qualified_hk + qualified_nohk

            # 10. 沉淀池与生命周期维护
            # 仅对本次复测达标存活的节点建档/累加考核
            qualified_endpoints = []
            with self.controller.state.lock:
                for node in total_final_selected:
                    ep = _get_ep(node) or str(node)
                    if ep and ep != "127.0.0.1:443":
                        qualified_endpoints.append(ep)

                process_verified_lifecycle(
                    self.controller.state.verified_nodes,
                    qualified_endpoints,
                    self.controller.state.stars_nodes,
                )
                purge_invalid_and_blacklisted_from_all_pools(
                    self.controller.state.favorites,
                    self.controller.state.verified_nodes,
                    self.controller.state.stars_nodes,
                    self.controller.state.local_blacklist,
                    self.controller.state.speed_blacklist,
                    _get_ep,
                )

            # 持久化
            self.controller.save_config(self.controller.get_state_snapshot())
            self.controller.data_changed.emit()

            self.log_signal.emit(f"优质复检统计：香港达标 {len(qualified_hk)}/{target_hk}，非香港达标 {len(qualified_nohk)}/{target_nohk} (已同步沉淀池)")

            hk_lack = (target_hk > 0 and len(qualified_hk) < target_hk)
            nohk_lack = (target_nohk > 0 and len(qualified_nohk) < target_nohk)

            # 11. 自愈大优选降级判断
            if fallback_enabled and (hk_lack or nohk_lack):
                reasons = []
                if hk_lack:
                    reasons.append(f"香港达标({len(qualified_hk)}/{target_hk})")
                if nohk_lack:
                    reasons.append(f"非香港达标({len(qualified_nohk)}/{target_nohk})")
                reason_str = "、".join(reasons)

                if len(total_final_selected) > 0:
                    script_code, p_toks, s_toks = build_script_js(
                        favorites=self.controller.state.favorites,
                        stars_nodes=self.controller.state.stars_nodes,
                        all_nodes=self.controller.state.all_nodes,
                        node_details=self.controller.state.node_details,
                        group_interval=group_interval,
                        group_tolerance=group_tolerance,
                        star_group_interval=star_group_interval,
                        star_group_tolerance=star_group_tolerance,
                        is_asian_node_fn=is_asian_node,
                        get_node_endpoint_fn=_get_ep,
                        cloud_endpoints=self.controller.state.cloud_endpoints,
                        node_colo=self.controller.state.node_colo,
                    )
                    write_script_js(script_code)
                    trigger_verge_reactivate_hotkey()

                # 精选复测结束后自动推送到云端 /verified.txt
                self.controller.push_verified_to_cloud()
                self.log_signal.emit(f"⚡ 检测到配额不足且已开启唤醒开关，触发自愈大优选：{reason_str}")
                self.fallback_needed.emit(f"优质复测不足：{reason_str}")
                self.finished_signal.emit(True, f"优质复测配额不足 ({reason_str})，已触发自愈大优选")
                return

            # 正常写入 Script.js 并触发热键生效
            script_code, p_toks, s_toks = build_script_js(
                favorites=self.controller.state.favorites,
                stars_nodes=self.controller.state.stars_nodes,
                all_nodes=self.controller.state.all_nodes,
                node_details=self.controller.state.node_details,
                group_interval=group_interval,
                group_tolerance=group_tolerance,
                star_group_interval=star_group_interval,
                star_group_tolerance=star_group_tolerance,
                is_asian_node_fn=is_asian_node,
                get_node_endpoint_fn=_get_ep,
                cloud_endpoints=self.controller.state.cloud_endpoints,
                node_colo=self.controller.state.node_colo,
            )
            write_ok, write_res = write_script_js(script_code)
            if write_ok:
                self.log_signal.emit(f"✅ Script.js 策略组写入成功 (留任优选: {len(p_toks)} 个，典藏: {len(s_toks)} 个)")
                hk_ok, hk_msg = trigger_verge_reactivate_hotkey()
                if hk_ok:
                    self.log_signal.emit(f"⚡ 热键通知成功: {hk_msg}")
            else:
                self.log_signal.emit(f"⚠️ Script.js 写入失败: {write_res}")

            # 精选复测结束后自动推送到云端 /verified.txt
            self.controller.push_verified_to_cloud()

            summary_msg = f"优质池复测完成：留任优质节点 {len(total_final_selected)} 个 (香港 {len(qualified_hk)}，非香港 {len(qualified_nohk)})"
            self.status_signal.emit("优质复测执行完成")
            self.log_signal.emit(f"🎯 {summary_msg}")
            self.finished_signal.emit(True, summary_msg)

        except Exception as e:
            err_tb = traceback.format_exc()
            self.log_signal.emit(f"优质池复测异常:\n{err_tb}")
            self.status_signal.emit("执行异常")
            self.finished_signal.emit(False, f"执行异常: {str(e)}")
```

## File: `gui_fluent/widgets/__init__.py`

```python
"""
自定义 Fluent 风格小部件模块
"""
from gui_fluent.widgets.node_table import NodeTableView
from gui_fluent.widgets.verified_table import VerifiedTableView
from gui_fluent.widgets.stars_table import StarsTableView

__all__ = ["NodeTableView", "VerifiedTableView", "StarsTableView"]
```

## File: `gui_fluent/widgets/c_miner_dialog.py`

```python
"""
C 段全量高并发极速深度挖掘对话框 (CSegmentMinerDialog)
基于 PyQt-Fluent-Widgets 构建，支持对 /24 网段 254 个 IP 进行并发 TCP 测延与真实 Colo 机房判定，
并提供一键批量导入至优质精选池、沉淀孵化池或典藏常青池。
"""
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QColor, QBrush, QFont
    from PyQt5.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QWidget,
        QProgressDialog,
    )
else:
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QColor, QBrush, QFont
    from PyQt6.QtWidgets import (
        QDialog,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QWidget,
        QProgressDialog,
    )

from qfluentwidgets import (
    PushButton,
    PrimaryPushButton,
    LineEdit,
    InfoBar,
    MessageBox,
    FluentIcon,
)

from services.probe_service import get_c_segment_ips, tcp_ping, get_cf_colo_raw
from services.colo_service import is_asian_node


class CSegmentMinerWorker(QThread):
    """
    C 段深度挖掘后台扫描线程：
    分两阶段进行：
      阶段 1: 50 线程高并发全网段 TCP Ping，快速筛选延迟 <= 门槛的活跃 IP
      阶段 2: 20 线程对达标 IP 进行 Cloudflare 真实机房 (Colo) 测定
    """
    progress_signal = pyqtSignal(int, int)  # (done, total)
    stage_signal = pyqtSignal(str)          # 阶段提示文本
    finished_signal = pyqtSignal(list)      # 扫描结果 list[dict]

    def __init__(self, c_ips: list[str], port: int = 443, threshold: int = 130, parent=None):
        super().__init__(parent)
        self.c_ips = list(c_ips)
        self.port = port
        self.threshold = threshold
        self._is_stopped = False

    def stop(self):
        self._is_stopped = True
        self.requestInterruption()

    def run(self):
        total = len(self.c_ips)
        if total == 0:
            self.finished_signal.emit([])
            return

        # 阶段 1: 全并发 TCP 测延
        self.stage_signal.emit(f"正在全并发 TCP 测延 (共 {total} 个 IP)...")
        results = []
        done_cnt = [0]

        def _scan_one(ip):
            if self._is_stopped or self.isInterruptionRequested():
                return None
            rtt = tcp_ping(ip, port=self.port, timeout=1.2)
            done_cnt[0] += 1
            if done_cnt[0] % 10 == 0 or done_cnt[0] >= total:
                self.progress_signal.emit(done_cnt[0], total)
            if rtt < 99999 and rtt <= self.threshold:
                return (ip, rtt)
            return None

        with ThreadPoolExecutor(max_workers=50) as ex:
            for res in ex.map(_scan_one, self.c_ips):
                if res:
                    results.append(res)
                if self._is_stopped or self.isInterruptionRequested():
                    break

        if self._is_stopped or self.isInterruptionRequested():
            self.stage_signal.emit("扫描已中止")
            self.finished_signal.emit([])
            return

        if not results:
            self.stage_signal.emit(f"TCP 测延完成：未发现延迟 ≤ {self.threshold}ms 的 IP")
            self.finished_signal.emit([])
            return

        # 阶段 2: 真实 Colo 机房校准 (严禁降级回退至普通地理属地，杜绝非 CF 服务器伪充优选)
        self.stage_signal.emit(f"TCP 达标 {len(results)} 个，正在严格鉴权 Cloudflare 真实机房...")
        colo_map = {}

        def _probe_colo(ip):
            if self._is_stopped or self.isInterruptionRequested():
                return
            # 严格关闭地理降级回退 (enable_geo_fallback=False)，确保只有真正响应 /cdn-cgi/trace 的 Cloudflare 机房才算达标
            c_code, c_disp = get_cf_colo_raw(ip, port=self.port, timeout=1.8, enable_geo_fallback=False)
            colo_map[ip] = (c_code, c_disp)

        with ThreadPoolExecutor(max_workers=20) as ex:
            for _ in ex.map(_probe_colo, [r[0] for r in results]):
                if self._is_stopped or self.isInterruptionRequested():
                    break

        # 按延迟从小到大排序
        results.sort(key=lambda x: x[1])

        final_rows = []
        valid_cf_count = 0
        for ip, rtt in results:
            c_code, c_disp = colo_map.get(ip, ("-", "-"))
            # 必须严格具备 Cloudflare Anycast 数据中心三字代码才视为达标
            is_cf = bool(c_code and c_code != "-" and c_code != "ANY")
            if is_cf:
                colo_label = c_disp
                status_text = "✅ 极速达标"
                valid_cf_count += 1
            else:
                colo_label = "非CF机房" if not c_disp or c_disp == "-" else f"{c_disp} (非CF)"
                status_text = "❌ 非CF机房"

            final_rows.append({
                "ip": ip,
                "port": self.port,
                "delay": rtt,
                "delay_str": f"{rtt} ms",
                "colo_code": c_code if is_cf else "-",
                "colo": colo_label,
                "status": status_text,
                "is_valid_cf": is_cf,
            })

        self.finished_signal.emit(final_rows)


class PostImportWorker(QThread):
    """
    C 段导入后全链路闭环专职工作线程：
    继承 QThread 并通过 pyqtSignal 跨线程安全通信，彻底杜绝 UI 假死与 QObject 亲和性冲突。
    """
    step_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, list)

    def __init__(self, controller, target: str, count: int, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.target = target
        self.count = count

    def run(self):
        pool_names = {
            "fav": "【⭐ 优质精选池】",
            "verified": "【⏳ 沉淀孵化池】",
            "stars": "【🏆 典藏管理池】",
            "pending": "【⚪ 活跃待测池】",
        }
        target_name = pool_names.get(self.target, "目标池")
        logs_step = [f"✅ 本地收编: 成功收录 {self.count} 个极速 IP 至 {target_name}"]
        try:
            # 步骤 1: 尝试推送至 Cloudflare Worker 云端
            self.step_signal.emit("[1/4] 正在同步推送至 Cloudflare Worker...")
            ok_w = False
            msg_w = ""
            if self.target == "fav":
                fav_lines = []
                seen_eps = set()
                with self.controller.state.lock:
                    for f in list(self.controller.state.favorites):
                        ep_val = self.controller._get_ep(f) or str(f)
                        if not ep_val or ep_val in seen_eps or ep_val == "127.0.0.1:443":
                            continue
                        seen_eps.add(ep_val)
                        colo = self.controller.state.node_colo.get(f, self.controller.state.node_colo.get(ep_val, "JP"))
                        if not colo or colo == "-":
                            colo = "亚洲"
                        spd = self.controller.state.node_speeds.get(f, self.controller.state.node_speeds.get(ep_val, 0.0))
                        reason = self.controller.state.fav_reasons.get(f, self.controller.state.fav_reasons.get(ep_val, ""))
                        if spd and spd > 0.1:
                            uniform_name = f"{colo} {spd:.2f} MB/s"
                        elif "C段" in reason:
                            uniform_name = f"{colo} [C段挖掘]"
                        else:
                            uniform_name = colo
                        fav_lines.append(f"{ep_val}#{uniform_name}")
                        self.controller.state.cloud_endpoints[ep_val] = uniform_name
                        if ":" in ep_val:
                            self.controller.state.cloud_endpoints[ep_val.split(":")[0]] = uniform_name
                payload = ("\r\n".join(fav_lines) + "\r\n") if fav_lines else "# empty\r\n"
                ok_w, msg_w = self.controller.push_text_to_cf_worker(payload, subpath="/auto.txt")
            elif self.target == "verified":
                with self.controller.state.lock:
                    lines = [f"{v['endpoint']}#{v.get('remark', '')}" for v in self.controller.state.verified_nodes.values() if v.get("endpoint")]
                payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
                ok_w, msg_w = self.controller.push_text_to_cf_worker(payload, subpath="/verified.txt")
            elif self.target == "stars":
                with self.controller.state.lock:
                    lines = [f"{item.get('endpoint', '')}#{item.get('remark', '')}" for item in self.controller.state.stars_nodes if item.get('endpoint')]
                payload = ("\r\n".join(lines) + "\r\n") if lines else "# empty\r\n"
                ok_w, msg_w = self.controller.push_text_to_cf_worker(payload, subpath="")
            elif self.target == "pending":
                # 同步追加推送到 /pending.txt 并自动排查已存在的精选与黑名单
                pending_items = getattr(self, "pending_items", [])
                ok_w, msg_w = self.controller.append_pending_endpoints_to_cloud_sync(pending_items)

            if ok_w:
                logs_step.append("✅ 云端同步: 已成功推送到 Cloudflare Worker")
                self.controller.log(f"Worker 同步成功: {msg_w}")
            else:
                logs_step.append(f"⚠️ 云端同步: {msg_w}")
                self.controller.log(f"Worker 同步提示: {msg_w}")

            # 重新拉取云端映射
            self.controller.fetch_cloud_endpoints_sync()
            self.controller.fetch_pending_endpoints_sync()
            time.sleep(0.5)

            # 步骤 2: 在线拉取更新订阅 (拉取最新 profiles yaml 并重新解析)
            self.step_signal.emit("[2/4] 正在拉取远程最新订阅并解析节点...")
            up_ok, up_msg = self.controller.update_remote_subscription_sync()
            if up_ok:
                logs_step.append(f"✅ 订阅更新: {up_msg}")
            else:
                logs_step.append(f"⚠️ 订阅更新: {up_msg}")

            # 步骤 3: 写入 Script.js 并触发热键热更激活订阅
            self.step_signal.emit("[3/4] 正在写入 Script.js 并触发热更激活...")
            self.controller.generate_script_and_reload()
            logs_step.append("✅ 热更激活: 已生成 Script.js 并模拟热键激活")

            # 步骤 4: 探测 Clash 内核装载状态
            self.step_signal.emit("[4/4] 正在探测 Clash 内核装载状态...")
            loaded_ok, loaded_msg = self.controller.clash_client.wait_for_kernel_reload(
                self.controller.state.all_nodes, max_wait_sec=10
            )
            logs_step.append(f"{'✅' if loaded_ok else '⚠️'} 内核装载: {loaded_msg}")
            self.controller.log(f"内核探测反馈: {loaded_msg}")

            # 保存状态与触发 UI 刷新
            self.controller.save_config(self.controller.get_state_snapshot())
            self.controller.data_changed.emit()

            final_ok = ok_w or up_ok or loaded_ok
            self.finished_signal.emit(final_ok, f"已成功收编 {self.count} 个 IP 并完成热更闭环！", logs_step)

        except Exception as ex:
            err_msg = f"收编后闭环处理异常: {ex}"
            self.controller.log(f"❌ {err_msg}")
            self.finished_signal.emit(False, err_msg, logs_step)


class CSegmentMinerDialog(QDialog):
    """
    Fluent 风格 C 段全量深度挖掘对话框
    """

    COLUMN_HEADERS = ["IP 地址", "端口", "TCP 握手延迟", "真实机房 (Colo)", "评估状态"]
    COLUMN_WIDTHS = [180, 75, 130, 200, 130]

    def __init__(self, seed_ip: str, seed_port: int = 443, controller=None, parent=None):
        super().__init__(parent)
        self.controller = controller
        self.seed_ip = seed_ip
        self.seed_port = seed_port
        self.c_ips = get_c_segment_ips(seed_ip)
        self.c_segment_name = ".".join(seed_ip.split(".")[:3]) + ".0/24" if "." in seed_ip else seed_ip
        self.worker = None
        self._post_worker = None
        self._current_results = []

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"🔍 C 段全量极速深度挖掘 - {self.c_segment_name}")
        self.setMinimumSize(920, 600)
        self.resize(960, 640)

        # 深色窗口风格
        self.setStyleSheet("""
            QDialog {
                background-color: #151822;
                color: #e2e8f0;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 13px;
            }
            QTableWidget {
                background-color: #181b26;
                color: #e2e8f0;
                gridline-color: rgba(255, 255, 255, 0.06);
                border: 1px solid #2c3246;
                border-radius: 6px;
                selection-background-color: #28334a;
                selection-color: #ffffff;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1e2230;
                color: #8d98af;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 4px;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 1. 顶部控制栏
        top_layout = QHBoxLayout()
        top_layout.setSpacing(10)

        top_layout.addWidget(QLabel("目标 IP / 种子 IP:", self))
        self.ip_edit = LineEdit(self)
        self.ip_edit.setText(self.seed_ip)
        self.ip_edit.setFixedWidth(160)
        self.ip_edit.setPlaceholderText("输入 IPv4 地址，如 172.64.229.1")
        self.ip_edit.textChanged.connect(self._on_ip_input_changed)
        top_layout.addWidget(self.ip_edit)

        self.lbl_seg_info = QLabel(f"({self.c_segment_name})", self)
        self.lbl_seg_info.setStyleSheet("color: #38bdf8; font-size: 12px;")
        top_layout.addWidget(self.lbl_seg_info)

        top_layout.addWidget(QLabel("端口:", self))
        self.port_edit = LineEdit(self)
        self.port_edit.setText(str(self.seed_port))
        self.port_edit.setFixedWidth(65)
        top_layout.addWidget(self.port_edit)

        top_layout.addWidget(QLabel("延迟门槛(≤ ms):", self))
        self.threshold_edit = LineEdit(self)
        self.threshold_edit.setText("130")
        self.threshold_edit.setFixedWidth(65)
        top_layout.addWidget(self.threshold_edit)

        self.lbl_status = QLabel(f"准备就绪 (共 {len(self.c_ips)} 个 IP)", self)
        self.lbl_status.setStyleSheet("color: #8d98af;")
        top_layout.addWidget(self.lbl_status)

        top_layout.addStretch()

        self.btn_sel_all = PushButton("全选达标", self)
        self.btn_sel_all.clicked.connect(self._select_all_rows)
        top_layout.addWidget(self.btn_sel_all)

        self.btn_sel_none = PushButton("清空选择", self)
        self.btn_sel_none.clicked.connect(self._clear_selection)
        top_layout.addWidget(self.btn_sel_none)

        layout.addLayout(top_layout)

        # 2. 中间结果表格
        self.table = QTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(28)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        layout.addWidget(self.table)

        # 3. 底部操作栏
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(10)

        self.btn_start = PrimaryPushButton("🚀 开始极速挖掘", self)
        self.btn_start.clicked.connect(self._start_mining)
        bottom_layout.addWidget(self.btn_start)

        self.btn_stop = PushButton("⏹ 停止", self)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_mining)
        bottom_layout.addWidget(self.btn_stop)

        bottom_layout.addStretch()

        self.btn_import_pending = PushButton("📥 导入【⚪ 活跃待测池】", self)
        self.btn_import_pending.clicked.connect(lambda: self._import_to_pool("pending"))
        bottom_layout.addWidget(self.btn_import_pending)

        self.btn_import_fav = PushButton("📥 导入【⭐ 优质精选池】", self)
        self.btn_import_fav.clicked.connect(lambda: self._import_to_pool("fav"))
        bottom_layout.addWidget(self.btn_import_fav)

        self.btn_import_verified = PushButton("📥 导入【⏳ 沉淀孵化池】", self)
        self.btn_import_verified.clicked.connect(lambda: self._import_to_pool("verified"))
        bottom_layout.addWidget(self.btn_import_verified)

        self.btn_import_stars = PushButton("📥 导入【🏆 典藏管理池】", self)
        self.btn_import_stars.clicked.connect(lambda: self._import_to_pool("stars"))
        bottom_layout.addWidget(self.btn_import_stars)

        layout.addLayout(bottom_layout)

    def _select_all_rows(self):
        """全选所有真正属于 Cloudflare 的达标行"""
        self.table.clearSelection()
        for row_idx, r in enumerate(self._current_results):
            if r.get("status") == "✅ 极速达标":
                self.table.selectRow(row_idx)

    def _clear_selection(self):
        self.table.clearSelection()

    def _on_ip_input_changed(self, text: str):
        ip = text.strip()
        parts = ip.split(".")
        if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
            seg = f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
            self.lbl_seg_info.setText(f"({seg})")
        else:
            self.lbl_seg_info.setText("(无效 IP 格式)")

    def _start_mining(self):
        if self.worker and self.worker.isRunning():
            return

        target_ip = self.ip_edit.text().strip()
        m = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3})$", target_ip)
        if not m:
            InfoBar.warning("输入错误", "请输入合法的 IPv4 格式地址（如 172.64.229.1）！", parent=self)
            return

        # 动态重新生成 254 个 C 段 IP 列表
        self.c_ips = get_c_segment_ips(target_ip)
        self.c_segment_name = ".".join(target_ip.split(".")[:3]) + ".0/24"
        self.setWindowTitle(f"🔍 C 段全量极速深度挖掘 - {self.c_segment_name}")

        port_str = self.port_edit.text().strip()
        port = int(port_str) if port_str.isdigit() else 443
        th_str = self.threshold_edit.text().strip()
        threshold = int(th_str) if th_str.isdigit() else 130

        self.table.clearContents()
        self.table.setRowCount(0)
        self._current_results = []

        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.lbl_status.setText("正在准备并发测延...")

        self.worker = CSegmentMinerWorker(self.c_ips, port=port, threshold=threshold, parent=self)
        self.worker.progress_signal.connect(self._on_worker_progress)
        self.worker.stage_signal.connect(self._on_worker_stage)
        self.worker.finished_signal.connect(self._on_worker_finished)
        self.worker.start()

    def _stop_mining(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.btn_stop.setEnabled(False)
            self.lbl_status.setText("正在中止扫描...")

    def _on_worker_progress(self, done: int, total: int):
        self.lbl_status.setText(f"TCP 测延中: {done}/{total}")

    def _on_worker_stage(self, stage_text: str):
        self.lbl_status.setText(stage_text)

    def _on_worker_finished(self, results: list):
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._current_results = list(results)

        self.table.clearContents()
        self.table.setRowCount(len(results))

        for row_idx, r in enumerate(results):
            ip_item = QTableWidgetItem(r.get("ip", ""))
            ip_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, ip_item)

            port_item = QTableWidgetItem(str(r.get("port", 443)))
            port_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 1, port_item)

            delay_item = QTableWidgetItem(r.get("delay_str", ""))
            delay_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            delay_item.setForeground(QBrush(QColor("#38bdf8")))
            self.table.setItem(row_idx, 2, delay_item)

            colo_item = QTableWidgetItem(r.get("colo", "-"))
            colo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 3, colo_item)

            status_item = QTableWidgetItem(r.get("status", ""))
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            color = "#34d399" if r.get("status") == "✅ 极速达标" else "#f87171"
            status_item.setForeground(QBrush(QColor(color)))
            self.table.setItem(row_idx, 4, status_item)

        valid_cnt = sum(1 for r in results if r.get("status") == "✅ 极速达标")
        self.lbl_status.setText(f"挖掘完成！共发现 {valid_cnt} 个极速达标 IP")

    def _get_target_rows(self) -> list[dict]:
        """获取需要导入的行数据（自动过滤掉非 CF 节点，确保流入池中的都是可用代理）"""
        if not self._current_results:
            return []

        selected_row_indices = sorted({idx.row() for idx in self.table.selectedIndexes()})
        if selected_row_indices:
            candidates = [self._current_results[i] for i in selected_row_indices if i < len(self._current_results)]
        else:
            candidates = list(self._current_results)

        # 强力阻断非 CF 节点流入优质池
        valid_targets = [r for r in candidates if r.get("status") == "✅ 极速达标"]
        return valid_targets

    def _import_to_pool(self, target: str):
        """导入至指定目标池"""
        if self.worker and self.worker.isRunning():
            self._stop_mining()
            time.sleep(0.2)

        rows_to_import = self._get_target_rows()
        if not rows_to_import:
            InfoBar.warning(
                title="提示",
                content="当前无挖掘结果可导入！请先点击开始挖掘。",
                duration=3000,
                parent=self,
            )
            return

        if not self.controller:
            return

        now_ts = time.time()
        cnt = 0
        pool_names = {
            "fav": "【⭐ 优质精选池】",
            "verified": "【⏳ 沉淀孵化池】",
            "stars": "【🏆 典藏管理池】",
            "pending": "【⚪ 活跃待测池】",
        }
        target_name = pool_names.get(target, "目标池")

        pending_items_to_send = []
        if target == "pending":
            with self.controller.state.lock:
                for r in rows_to_import:
                    ip = r.get("ip", "")
                    port = r.get("port", 443)
                    ep = f"{ip}:{port}"
                    colo = r.get("colo", "亚洲")
                    rem = f"{colo} [C段挖掘待测]"
                    pending_items_to_send.append((ep, rem))
                    self.controller.state.local_blacklist.discard(ep)
                    self.controller.state.speed_blacklist.discard(ep)
                    cnt += 1
        else:
            with self.controller.state.lock:
                for r in rows_to_import:
                    ip = r.get("ip", "")
                    port = r.get("port", 443)
                    ep = f"{ip}:{port}"
                    colo = r.get("colo", "-")
                    delay = r.get("delay", 0)
                    rem = f"{colo} [C段挖掘]"

                    if target == "fav":
                        self.controller.state.favorites.add(ep)
                        self.controller.state.fav_reasons[ep] = "C段深度挖掘"
                        if delay > 0:
                            self.controller.state.node_delays[ep] = delay
                            hist = self.controller.state.node_history.setdefault(ep, [])
                            hist.append(delay)
                            self.controller.state.node_history[ep] = hist[-6:]
                        if colo and colo != "-":
                            self.controller.state.node_colo[ep] = colo
                        self.controller.state.local_blacklist.discard(ep)
                        self.controller.state.speed_blacklist.discard(ep)
                        self.controller.state.cloud_endpoints[ep] = rem
                        if ":" in ep:
                            self.controller.state.cloud_endpoints[ep.split(":")[0]] = rem
                        self.controller.state.auto_endpoints.add(ep)
                        cnt += 1

                    elif target == "verified":
                        if ep not in self.controller.state.verified_nodes:
                            self.controller.state.verified_nodes[ep] = {
                                "endpoint": ep,
                                "colo": colo,
                                "remark": rem,
                                "first_seen": now_ts,
                                "passes": 1,
                                "fails": 0,
                                "delay": delay,
                                "speed": 0.0,
                                "reason": "C段深度挖掘入孵",
                            }
                            cnt += 1

                    elif target == "stars":
                        existing_eps = {s.get("endpoint", "") for s in self.controller.state.stars_nodes}
                        if ep not in existing_eps:
                            self.controller.state.stars_nodes.append({
                                "endpoint": ep,
                                "colo": colo,
                                "remark": rem,
                                "delay": delay,
                                "speed": 0.0,
                                "matched_name": "",
                                "reason": "C段深度挖掘加冕",
                            })
                            cnt += 1

        # 保存快照并记录日志
        self.controller.save_config(self.controller.get_state_snapshot())
        self.controller.log(f"📥 C 段挖掘: 已收录 {cnt} 个达标 IP 到 {target_name}")

        # 启动 PostImportWorker 统一执行 4 步全链路热更闭环
        self._post_worker = PostImportWorker(self.controller, target, cnt, parent=self)
        if target == "pending":
            self._post_worker.pending_items = pending_items_to_send

        progress_dialog = QProgressDialog("正在执行热更闭环处理...", "取消", 0, 0, self)
        progress_dialog.setWindowTitle("同步推进中")
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dialog.setCancelButton(None)
        progress_dialog.setStyleSheet("""
            QProgressDialog {
                background-color: #1a1d29;
                color: #e2e8f0;
            }
            QLabel {
                color: #38bdf8;
                font-size: 13px;
            }
        """)

        def _on_step(msg):
            progress_dialog.setLabelText(msg)

        def _on_post_finished(success, message, steps):
            progress_dialog.close()
            dlg_detail = "\n".join(steps)
            if success:
                MessageBox("收编与热更完成", f"{message}\n\n执行明细:\n{dlg_detail}", self).exec()
            else:
                MessageBox("热更过程提示", f"{message}\n\n执行明细:\n{dlg_detail}", self).exec()
            # 若导入的是精选、孵化或典藏，顺手触发一次云端待测池大扫除，清除已收编的端点
            if target != "pending":
                import threading
                threading.Thread(target=self.controller.purge_pending_endpoints_from_cloud, daemon=True).start()

        self._post_worker.step_signal.connect(_on_step)
        self._post_worker.finished_signal.connect(_on_post_finished)
        self._post_worker.start()
        progress_dialog.exec()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(500)
        if hasattr(self, "_post_worker") and self._post_worker and self._post_worker.isRunning():
            self._post_worker.wait(2000)
        super().closeEvent(event)
```

## File: `gui_fluent/widgets/node_table.py`

```python
"""
通用节点表格组件 (NodeTableView)
支持 11 列完整信息展示、状态高亮着色、智能列排序与鼠标拖选多行
"""
import re
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, QItemSelection, QItemSelectionModel
    from PyQt5.QtGui import QColor, QBrush, QFont
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
    )
else:
    from PyQt6.QtCore import Qt, QItemSelection, QItemSelectionModel
    from PyQt6.QtGui import QColor, QBrush, QFont
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
    )

from qfluentwidgets import RoundMenu, Action, FluentIcon, InfoBar


class DragSelectTableWidget(QTableWidget):
    """
    增强型 QTableWidget：支持鼠标按住左键直接上下拖拽滑动多选行
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_start_row = -1

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_row = self.rowAt(event.pos().y())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if (event.buttons() & Qt.MouseButton.LeftButton) and self._drag_start_row >= 0:
            curr_row = self.rowAt(event.pos().y())
            if curr_row >= 0:
                start = min(self._drag_start_row, curr_row)
                end = max(self._drag_start_row, curr_row)
                selection = QItemSelection(
                    self.model().index(start, 0),
                    self.model().index(end, self.columnCount() - 1),
                )
                self.selectionModel().select(
                    selection,
                    QItemSelectionModel.SelectionFlag.ClearAndSelect
                    | QItemSelectionModel.SelectionFlag.Rows,
                )
                return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_start_row = -1
        super().mouseReleaseEvent(event)


class NodeTableView(QWidget):
    """
    通用节点表格视图：适用于 活跃待测 / 优质精选 / 延迟黑名单 / 低速黑名单
    """

    COLUMN_KEYS = [
        "status",
        "colo",
        "colo_hist",
        "reason",
        "delay",
        "avg_delay",
        "delay_hist",
        "hist_avg",
        "speed",
        "speed_hist",
        "endpoint",
        "name",
    ]

    COLUMN_HEADERS = [
        "状态",
        "最新Colo",
        "Colo稳定性(7天)",
        "入选/拉黑原因",
        "最新延迟",
        "本轮均值",
        "延迟轨迹(轮数)",
        "历史均值/稳定度",
        "最新下行",
        "下行轨迹(近4次)",
        "IP:端口",
        "节点名称",
    ]

    COLUMN_WIDTHS = [90, 80, 150, 160, 75, 85, 120, 140, 75, 120, 140, 260]

    def __init__(self, parent=None, controller=None, page_type: str = "active"):
        super().__init__(parent)
        self.controller = controller
        self.page_type = page_type
        self._sort_col = -1
        self._sort_asc = True
        self._raw_rows = []
        self.init_ui()

    def set_controller(self, controller, page_type: str = "active"):
        """绑定控制器与当前页面类型"""
        self.controller = controller
        self.page_type = page_type

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = DragSelectTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        # 样式设定：深色风格
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #181b26;
                color: #e2e8f0;
                gridline-color: rgba(255, 255, 255, 0.06);
                border: none;
                selection-background-color: #28334a;
                selection-color: #ffffff;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1e2230;
                color: #8d98af;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QTableCornerButton::section {
                background-color: #1e2230;
                border: none;
            }
            QScrollBar:vertical {
                background: #181b26;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)

        # 预设初始列宽
        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        # 开启右键上下文菜单策略
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

    def populate(self, rows: list[dict]):
        """
        填充表格数据
        rows 为字典列表，每个字典包含 COLUMN_KEYS 中的字段
        """
        self._raw_rows = list(rows)
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            status_text = str(row_data.get("status", ""))
            delay_text = str(row_data.get("delay", ""))

            # 颜色规则
            if "优质精选" in status_text or "云端已保活" in status_text:
                row_color = QColor("#38bdf8")
            elif "活跃待测" in status_text:
                row_color = QColor("#e2e8f0")
            elif ("黑名单" in status_text) or ("拉黑" in status_text) or ("超时" in status_text) or ("超时" in delay_text) or ("淘汰" in status_text):
                row_color = QColor("#f87171")
            elif "缺失" in status_text:
                row_color = QColor("#fbbf24")
            else:
                row_color = QColor("#94a3b8")

            node_name = str(row_data.get("raw_name", row_data.get("name", "")))
            ep_val = str(row_data.get("endpoint", row_data.get("IP:端口", "")))
            if not ep_val or ep_val == "-":
                m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", node_name)
                if m:
                    ep_val = m.group(1)

            for col_idx, key in enumerate(self.COLUMN_KEYS):
                val_str = str(row_data.get(key, "-"))
                item = QTableWidgetItem(val_str)
                item.setForeground(QBrush(row_color))

                # 对齐方式：除最后一列“节点名称”靠左居中外，其余全部水平居中
                if key == "name":
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # 将原始节点名称与端点绑定到每一行首列的 UserRole
                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, node_name)
                    item.setData(Qt.ItemDataRole.UserRole + 1, ep_val)

                self.table.setItem(row_idx, col_idx, item)

    def get_selected_node_names(self) -> list[str]:
        """
        获取当前选中行的节点名称列表
        """
        selected_names = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                name = item.data(Qt.ItemDataRole.UserRole)
                if name and name not in ["", "无", "-"]:
                    selected_names.append(name)
                else:
                    ep = item.data(Qt.ItemDataRole.UserRole + 1)
                    if ep and ep not in ["", "-"]:
                        selected_names.append(ep)
                    else:
                        name_item = self.table.item(r, len(self.COLUMN_KEYS) - 1)
                        if name_item and name_item.text().strip() not in ["", "无", "-"]:
                            selected_names.append(name_item.text().strip())
        return selected_names

    def get_selected_endpoints(self) -> list[str]:
        """
        获取当前选中行的物理端点 (IP:Port) 列表
        """
        selected_eps = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                ep = item.data(Qt.ItemDataRole.UserRole + 1)
                if ep and ep not in ["", "-"]:
                    selected_eps.append(ep)
                else:
                    col_ep = self.COLUMN_KEYS.index("endpoint") if "endpoint" in self.COLUMN_KEYS else -1
                    if col_ep >= 0:
                        ep_item = self.table.item(r, col_ep)
                        if ep_item and ep_item.text().strip() not in ["", "-"]:
                            selected_eps.append(ep_item.text().strip())
                            continue
                    name = item.data(Qt.ItemDataRole.UserRole)
                    if hasattr(self, "controller") and self.controller:
                        ep_res = self.controller.get_node_endpoint(name)
                        if ep_res:
                            selected_eps.append(ep_res)
                    else:
                        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", str(name))
                        if m:
                            selected_eps.append(m.group(1))
        return selected_eps

    def _copy_to_clipboard(self, items: list[str], label: str = "内容"):
        """复制内容至系统剪贴板"""
        if not items:
            return
        text = "\n".join(str(x) for x in items if str(x).strip())
        QApplication.clipboard().setText(text)
        InfoBar.success(
            title="已复制到剪贴板",
            content=f"已成功复制 {len(items)} 条{label}",
            duration=2000,
            parent=self.window(),
        )

    def _show_context_menu(self, pos):
        """弹出 Fluent 风格圆角右键悬浮菜单"""
        item_at = self.table.itemAt(pos)
        if not item_at:
            return
        clicked_row = item_at.row()
        selected_rows = {idx.row() for idx in self.table.selectedIndexes()}
        if clicked_row not in selected_rows:
            self.table.clearSelection()
            self.table.selectRow(clicked_row)

        selected_nodes = self.get_selected_node_names()
        if not selected_nodes:
            return

        selected_endpoints = self.get_selected_endpoints()
        cnt = len(selected_nodes)

        menu = RoundMenu(parent=self)

        # 1. 基础剪贴板复制
        copy_name_action = Action(FluentIcon.COPY, f"复制节点名称 ({cnt}项)", self)
        copy_name_action.triggered.connect(lambda: self._copy_to_clipboard(selected_nodes, "节点名称"))
        menu.addAction(copy_name_action)

        if selected_endpoints:
            copy_ep_action = Action(FluentIcon.SHARE, f"复制物理端点 ({len(selected_endpoints)}项)", self)
            copy_ep_action.triggered.connect(lambda: self._copy_to_clipboard(selected_endpoints, "物理端点"))
            menu.addAction(copy_ep_action)

        menu.addSeparator()

        # 2. 业务操作
        if self.controller:
            test_delay_action = Action(FluentIcon.WIFI, f"⚡ 立即测延迟 ({cnt}项)", self)
            test_delay_action.triggered.connect(lambda: self.controller.test_nodes_delay(selected_nodes))
            menu.addAction(test_delay_action)

            colo_action = Action(getattr(FluentIcon, "EARTH", FluentIcon.GLOBE), "🌍 测当前 Colo", self)
            colo_action.triggered.connect(lambda: self.controller.test_nodes_colo(selected_nodes))
            menu.addAction(colo_action)

            # 补充 C 段挖掘功能
            mine_action = Action(FluentIcon.SEARCH, "🔍 C段挖掘", self)
            mine_action.triggered.connect(lambda: self.controller.mine_c_subnet(selected_nodes))
            menu.addAction(mine_action)

            p_type = getattr(self, "page_type", "active")
            if p_type == "active":
                fav_action = Action(FluentIcon.HEART, "⭐ 设为优质精选", self)
                fav_action.triggered.connect(lambda: self.controller.move_nodes_to_favorites(selected_nodes))
                menu.addAction(fav_action)

                star_action = Action(FluentIcon.ACCEPT, "🏆 晋升至典藏常青", self)
                star_action.triggered.connect(lambda: self.controller.promote_nodes_to_stars(selected_nodes))
                menu.addAction(star_action)

                menu.addSeparator()

                delay_bl_action = Action(FluentIcon.CANCEL, "🚫 延迟拉黑", self)
                delay_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "右键手动拉黑", "delay"))
                menu.addAction(delay_bl_action)

                speed_bl_action = Action(FluentIcon.REMOVE, "🐢 低速拉黑", self)
                speed_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "右键手动拉黑", "speed"))
                menu.addAction(speed_bl_action)

            elif p_type == "favorites":
                star_action = Action(FluentIcon.ACCEPT, "🏆 晋升至典藏常青", self)
                star_action.triggered.connect(lambda: self.controller.promote_nodes_to_stars(selected_nodes))
                menu.addAction(star_action)

                ver_action = Action(FluentIcon.SYNC, "⏳ 纳入沉淀孵化池", self)
                ver_action.triggered.connect(lambda: self.controller.sync_favorites_to_verified())
                menu.addAction(ver_action)

                menu.addSeparator()

                remove_fav_action = Action(FluentIcon.DELETE, "🗑️ 移出精选池", self)
                remove_fav_action.triggered.connect(lambda: self.controller.remove_nodes_from_favorites(selected_nodes))
                menu.addAction(remove_fav_action)

                delay_bl_action = Action(FluentIcon.CANCEL, "🚫 延迟拉黑", self)
                delay_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "从精选池手动拉黑", "delay"))
                menu.addAction(delay_bl_action)

                speed_bl_action = Action(FluentIcon.REMOVE, "🐢 低速拉黑", self)
                speed_bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "从精选池手动拉黑", "speed"))
                menu.addAction(speed_bl_action)

            elif p_type in ["delay_black", "speed_black"]:
                unbl_action = Action(FluentIcon.SYNC, "♻️ 移出黑名单 (恢复待测)", self)
                unbl_action.triggered.connect(lambda: self.controller.remove_nodes_from_blacklist(selected_nodes))
                menu.addAction(unbl_action)

                fav_action = Action(FluentIcon.HEART, "⭐ 破格设为优质", self)
                fav_action.triggered.connect(lambda: self.controller.move_nodes_to_favorites(selected_nodes))
                menu.addAction(fav_action)

                menu.addSeparator()

                if p_type == "delay_black":
                    to_speed_action = Action(FluentIcon.REMOVE, "🐢 转为低速拉黑", self)
                    to_speed_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "转为低速黑名单", "speed"))
                    menu.addAction(to_speed_action)
                else:
                    to_delay_action = Action(FluentIcon.CANCEL, "🚫 转为延迟拉黑", self)
                    to_delay_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_nodes, "转为延迟黑名单", "delay"))
                    menu.addAction(to_delay_action)

        menu.exec(self.table.mapToGlobal(pos))

    def _on_header_clicked(self, col: int):
        """
        点击列标题执行智能排序（区分数值与字符串）
        """
        if not self._raw_rows:
            return

        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        key = self.COLUMN_KEYS[col]
        is_numeric = key in ["delay", "avg_delay", "hist_avg", "speed"]

        def _sort_key(row_dict):
            val = str(row_dict.get(key, ""))
            if is_numeric:
                if not val or val == "-" or "超时" in val or "失败" in val:
                    return float("inf") if self._sort_asc else float("-inf")
                m = re.search(r"[-+]?\d*\.?\d+", val)
                return float(m.group()) if m else (float("inf") if self._sort_asc else float("-inf"))
            return val.lower()

        sorted_rows = sorted(self._raw_rows, key=_sort_key, reverse=not self._sort_asc)
        self.populate(sorted_rows)
```

## File: `gui_fluent/widgets/stars_table.py`

```python
"""
典藏管理池表格组件 (StarsTableView)
展示 8 列核心长青节点数据，支持双击编辑信号触发与智能排序
"""
import re
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, pyqtSignal, QItemSelection, QItemSelectionModel
    from PyQt5.QtGui import QColor, QBrush
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QInputDialog,
    )
else:
    from PyQt6.QtCore import Qt, pyqtSignal, QItemSelection, QItemSelectionModel
    from PyQt6.QtGui import QColor, QBrush
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
        QInputDialog,
    )

from qfluentwidgets import RoundMenu, Action, FluentIcon, InfoBar, MessageBox
from gui_fluent.widgets.node_table import DragSelectTableWidget


class StarsTableView(QWidget):
    """
    典藏管理池表格组件
    """

    double_clicked = pyqtSignal(str)

    COLUMN_KEYS = [
        "endpoint",
        "colo",
        "colo_hist",
        "reason",
        "remark",
        "delay",
        "speed",
        "match",
    ]

    COLUMN_HEADERS = [
        "IP:端口",
        "最新Colo",
        "Colo稳定性(7天)",
        "典藏入选原因",
        "备注信息 (可双击修改)",
        "最新延迟",
        "最新下行",
        "本地订阅关联状态",
    ]

    COLUMN_WIDTHS = [130, 85, 150, 190, 200, 75, 85, 250]

    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self._sort_col = -1
        self._sort_asc = True
        self._raw_rows = []
        self.init_ui()

    def set_controller(self, controller):
        """绑定控制器"""
        self.controller = controller

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = DragSelectTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #181b26;
                color: #e2e8f0;
                gridline-color: rgba(255, 255, 255, 0.06);
                border: none;
                selection-background-color: #28334a;
                selection-color: #ffffff;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1e2230;
                color: #8d98af;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QTableCornerButton::section {
                background-color: #1e2230;
                border: none;
            }
            QScrollBar:vertical {
                background: #181b26;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)

        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)

        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        # 开启右键上下文菜单策略
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

    def _copy_to_clipboard(self, items: list[str], label: str = "内容"):
        """复制内容至系统剪贴板"""
        if not items:
            return
        text = "\n".join(str(x) for x in items if str(x).strip())
        QApplication.clipboard().setText(text)
        InfoBar.success(
            title="已复制到剪贴板",
            content=f"已成功复制 {len(items)} 条{label}",
            duration=2000,
            parent=self.window(),
        )

    def _edit_remark(self, ep: str):
        """弹出修改备注输入框"""
        if not ep or not self.controller:
            return
        text, ok = QInputDialog.getText(self, "修改备注", f"修改典藏节点 [{ep}] 的备注信息:")
        if ok and text is not None:
            self.controller.update_star_remark(ep, text.strip())

    def _confirm_delete(self, eps: list[str]):
        """删除选中典藏节点确认"""
        if not eps or not self.controller:
            return
        w = MessageBox("删除确认", f"确定从本地典藏池移除选中的 {len(eps)} 个节点吗？\n（注：点击保存推送前云端数据不会变动）", self.window())
        if w.exec():
            self.controller.delete_selected_stars(eps)

    def _show_context_menu(self, pos):
        """弹出 Fluent 风格圆角右键悬浮菜单"""
        item_at = self.table.itemAt(pos)
        if not item_at:
            return
        clicked_row = item_at.row()
        selected_rows = {idx.row() for idx in self.table.selectedIndexes()}
        if clicked_row not in selected_rows:
            self.table.clearSelection()
            self.table.selectRow(clicked_row)

        selected_eps = self.get_selected_endpoints()
        if not selected_eps:
            return

        cnt = len(selected_eps)
        menu = RoundMenu(parent=self)

        # 1. 剪贴板复制
        copy_ep_action = Action(FluentIcon.COPY, f"复制物理端点 ({cnt}项)", self)
        copy_ep_action.triggered.connect(lambda: self._copy_to_clipboard(selected_eps, "物理端点"))
        menu.addAction(copy_ep_action)

        if cnt == 1:
            edit_action = Action(FluentIcon.EDIT, "✏️ 修改备注信息", self)
            edit_action.triggered.connect(lambda: self._edit_remark(selected_eps[0]))
            menu.addAction(edit_action)

        menu.addSeparator()

        # 2. 业务操作
        if self.controller:
            test_delay_action = Action(FluentIcon.WIFI, f"⚡ 测选中延迟 ({cnt}项)", self)
            test_delay_action.triggered.connect(lambda: self.controller.test_stars_pipeline(mode="delay", endpoints=selected_eps))
            menu.addAction(test_delay_action)

            test_speed_action = Action(FluentIcon.SYNC, f"🚀 测选中下行速度 ({cnt}项)", self)
            test_speed_action.triggered.connect(lambda: self.controller.test_stars_pipeline(mode="speed", endpoints=selected_eps))
            menu.addAction(test_speed_action)

            colo_action = Action(getattr(FluentIcon, "EARTH", FluentIcon.GLOBE), "🌍 测当前 Colo", self)
            colo_action.triggered.connect(lambda: self.controller.test_nodes_colo(selected_eps))
            menu.addAction(colo_action)

            # 补充 C 段挖掘功能
            mine_action = Action(FluentIcon.SEARCH, "🔍 C段挖掘", self)
            mine_action.triggered.connect(lambda: self.controller.mine_c_subnet(selected_eps))
            menu.addAction(mine_action)

            menu.addSeparator()

            del_action = Action(FluentIcon.DELETE, f"🗑️ 从典藏池移除 ({cnt}项)", self)
            del_action.triggered.connect(lambda: self._confirm_delete(selected_eps))
            menu.addAction(del_action)

        menu.exec(self.table.mapToGlobal(pos))

    def populate(self, rows: list[dict]):
        self._raw_rows = list(rows)
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            match_text = str(row_data.get("match", ""))
            delay_text = str(row_data.get("delay", ""))
            ep = str(row_data.get("endpoint", ""))

            # 颜色规则
            if ("未匹配" in match_text) or ("离线" in match_text) or ("已下线" in match_text):
                row_color = QColor("#94a3b8")
            elif "超时" in delay_text:
                row_color = QColor("#f87171")
            elif ep:
                row_color = QColor("#38bdf8")
            else:
                row_color = QColor("#94a3b8")

            for col_idx, key in enumerate(self.COLUMN_KEYS):
                val_str = str(row_data.get(key, "-"))
                item = QTableWidgetItem(val_str)
                item.setForeground(QBrush(row_color))

                if key in ["remark", "match"]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, ep)

                self.table.setItem(row_idx, col_idx, item)

    def get_selected_endpoints(self) -> list[str]:
        endpoints = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                ep = item.data(Qt.ItemDataRole.UserRole)
                endpoints.append(ep if ep else item.text().strip())
        return endpoints

    def _on_cell_double_clicked(self, row: int, col: int):
        item = self.table.item(row, 0)
        if item:
            ep = item.data(Qt.ItemDataRole.UserRole)
            self.double_clicked.emit(ep if ep else item.text().strip())

    def _on_header_clicked(self, col: int):
        if not self._raw_rows:
            return

        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        key = self.COLUMN_KEYS[col]
        is_numeric = key in ["delay", "speed"]

        def _sort_key(row_dict):
            val = str(row_dict.get(key, ""))
            if is_numeric:
                if not val or val == "-" or "超时" in val:
                    return float("inf") if self._sort_asc else float("-inf")
                m = re.search(r"[-+]?\d*\.?\d+", val)
                return float(m.group()) if m else (float("inf") if self._sort_asc else float("-inf"))
            return val.lower()

        sorted_rows = sorted(self._raw_rows, key=_sort_key, reverse=not self._sort_asc)
        self.populate(sorted_rows)
```

## File: `gui_fluent/widgets/verified_table.py`

```python
"""
沉淀孵化池表格组件 (VerifiedTableView)
展示 10 列信息：端点、机房、7天稳定性、考核状态、存活时长与订阅关联
"""
import re
import sys

if "PyQt5" in sys.modules:
    from PyQt5.QtCore import Qt, QItemSelection, QItemSelectionModel
    from PyQt5.QtGui import QColor, QBrush
    from PyQt5.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
    )
else:
    from PyQt6.QtCore import Qt, QItemSelection, QItemSelectionModel
    from PyQt6.QtGui import QColor, QBrush
    from PyQt6.QtWidgets import (
        QWidget,
        QVBoxLayout,
        QTableWidgetItem,
        QHeaderView,
        QAbstractItemView,
        QApplication,
    )

from qfluentwidgets import RoundMenu, Action, FluentIcon, InfoBar

from gui_fluent.widgets.node_table import DragSelectTableWidget


class VerifiedTableView(QWidget):
    """
    沉淀孵化池表格组件
    """

    COLUMN_KEYS = [
        "endpoint",
        "colo",
        "colo_hist",
        "reason",
        "remark",
        "delay",
        "speed",
        "time",
        "stats",
        "match",
    ]

    COLUMN_HEADERS = [
        "IP:端口",
        "最新Colo",
        "Colo稳定性(7天)",
        "入孵原因 / 考核状态",
        "备注信息",
        "最新延迟",
        "最新下行",
        "存活时长",
        "考核统计",
        "本地订阅关联",
    ]

    COLUMN_WIDTHS = [125, 85, 150, 170, 155, 75, 80, 90, 130, 220]

    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self.controller = controller
        self._sort_col = -1
        self._sort_asc = True
        self._raw_rows = []
        self.init_ui()

    def set_controller(self, controller):
        """绑定控制器"""
        self.controller = controller

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.table = DragSelectTableWidget(self)
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #181b26;
                color: #e2e8f0;
                gridline-color: rgba(255, 255, 255, 0.06);
                border: none;
                selection-background-color: #28334a;
                selection-color: #ffffff;
                outline: none;
            }
            QHeaderView::section {
                background-color: #1e2230;
                color: #8d98af;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
                padding: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QTableCornerButton::section {
                background-color: #1e2230;
                border: none;
            }
            QScrollBar:vertical {
                background: #181b26;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #334155;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #475569;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)

        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)

        for col_idx, width in enumerate(self.COLUMN_WIDTHS):
            self.table.setColumnWidth(col_idx, width)

        # 开启右键上下文菜单策略
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.table)

    def _copy_to_clipboard(self, items: list[str], label: str = "内容"):
        """复制内容至系统剪贴板"""
        if not items:
            return
        text = "\n".join(str(x) for x in items if str(x).strip())
        QApplication.clipboard().setText(text)
        InfoBar.success(
            title="已复制到剪贴板",
            content=f"已成功复制 {len(items)} 条{label}",
            duration=2000,
            parent=self.window(),
        )

    def _show_context_menu(self, pos):
        """弹出 Fluent 风格圆角右键悬浮菜单"""
        item_at = self.table.itemAt(pos)
        if not item_at:
            return
        clicked_row = item_at.row()
        selected_rows = {idx.row() for idx in self.table.selectedIndexes()}
        if clicked_row not in selected_rows:
            self.table.clearSelection()
            self.table.selectRow(clicked_row)

        selected_eps = self.get_selected_endpoints()
        if not selected_eps:
            return

        selected_names = self.get_selected_node_names()
        cnt = len(selected_eps)

        menu = RoundMenu(parent=self)

        # 1. 剪贴板复制
        copy_ep_action = Action(FluentIcon.COPY, f"复制物理端点 ({cnt}项)", self)
        copy_ep_action.triggered.connect(lambda: self._copy_to_clipboard(selected_eps, "物理端点"))
        menu.addAction(copy_ep_action)

        valid_names = [n for n in selected_names if n]
        if valid_names:
            copy_name_action = Action(FluentIcon.SHARE, f"复制关联节点名 ({len(valid_names)}项)", self)
            copy_name_action.triggered.connect(lambda: self._copy_to_clipboard(valid_names, "节点名称"))
            menu.addAction(copy_name_action)

        menu.addSeparator()

        # 2. 业务操作
        if self.controller:
            test_targets = valid_names if valid_names else selected_eps
            test_delay_action = Action(FluentIcon.WIFI, f"⚡ 立即测延迟 ({len(test_targets)}项)", self)
            test_delay_action.triggered.connect(lambda: self.controller.test_nodes_delay(test_targets))
            menu.addAction(test_delay_action)

            colo_action = Action(getattr(FluentIcon, "EARTH", FluentIcon.GLOBE), "🌍 测当前 Colo", self)
            colo_action.triggered.connect(lambda: self.controller.test_nodes_colo(test_targets))
            menu.addAction(colo_action)

            # 补充 C 段挖掘功能
            mine_action = Action(FluentIcon.SEARCH, "🔍 C段挖掘", self)
            mine_action.triggered.connect(lambda: self.controller.mine_c_subnet(selected_eps))
            menu.addAction(mine_action)

            promote_action = Action(FluentIcon.ACCEPT, f"🏆 提前加冕至典藏常青池 ({cnt}项)", self)
            promote_action.triggered.connect(lambda: self.controller.force_promote_verified_to_stars(selected_eps))
            menu.addAction(promote_action)

            menu.addSeparator()

            remove_action = Action(FluentIcon.DELETE, f"🗑️ 从沉淀池移出 ({cnt}项)", self)
            remove_action.triggered.connect(lambda: self.controller.delete_selected_verified(selected_eps))
            menu.addAction(remove_action)

            bl_action = Action(FluentIcon.CANCEL, f"🚫 延迟拉黑并移出 ({cnt}项)", self)
            bl_action.triggered.connect(lambda: self.controller.blacklist_nodes(selected_eps, "从孵化池手动拉黑", "delay"))
            menu.addAction(bl_action)

        menu.exec(self.table.mapToGlobal(pos))

    def populate(self, rows: list[dict]):
        self._raw_rows = list(rows)
        self.table.clearContents()
        self.table.setRowCount(len(rows))

        for row_idx, row_data in enumerate(rows):
            reason_text = str(row_data.get("reason", ""))
            delay_text = str(row_data.get("delay", ""))

            # 颜色规则
            if ("已验证" in reason_text) or ("达标" in reason_text) or ("留任" in reason_text):
                row_color = QColor("#34d399")
            elif ("黑名单" in reason_text) or ("拉黑" in reason_text) or ("超时" in delay_text):
                row_color = QColor("#f87171")
            else:
                row_color = QColor("#94a3b8")

            ep = str(row_data.get("endpoint", ""))
            matched_name = str(row_data.get("match", ""))

            for col_idx, key in enumerate(self.COLUMN_KEYS):
                val_str = str(row_data.get(key, "-"))
                item = QTableWidgetItem(val_str)
                item.setForeground(QBrush(row_color))

                if key in ["remark", "match"]:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if col_idx == 0:
                    item.setData(Qt.ItemDataRole.UserRole, ep)
                    item.setData(Qt.ItemDataRole.UserRole + 1, matched_name)

                self.table.setItem(row_idx, col_idx, item)

    def get_selected_endpoints(self) -> list[str]:
        endpoints = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                ep = item.data(Qt.ItemDataRole.UserRole)
                endpoints.append(ep if ep else item.text().strip())
        return endpoints

    def get_selected_node_names(self) -> list[str]:
        names = []
        selected_rows = sorted({idx.row() for idx in self.table.selectedIndexes()})
        for r in selected_rows:
            item = self.table.item(r, 0)
            if item:
                n = item.data(Qt.ItemDataRole.UserRole + 1)
                names.append(n if n else "")
        return names

    def _on_header_clicked(self, col: int):
        if not self._raw_rows:
            return

        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        key = self.COLUMN_KEYS[col]
        is_numeric = key in ["delay", "speed", "time"]

        def _sort_key(row_dict):
            val = str(row_dict.get(key, ""))
            if is_numeric:
                if not val or val == "-" or "超时" in val:
                    return float("inf") if self._sort_asc else float("-inf")
                m = re.search(r"[-+]?\d*\.?\d+", val)
                return float(m.group()) if m else (float("inf") if self._sort_asc else float("-inf"))
            return val.lower()

        sorted_rows = sorted(self._raw_rows, key=_sort_key, reverse=not self._sort_asc)
        self.populate(sorted_rows)
```

## File: `pipelines/__init__.py`

```python
"""
Clash Verge 节点管理助手 - 流水线与调度模块
"""
```

## File: `pipelines/base_pipeline.py`

```python
import threading

class BasePipeline:
    """
    流水线抽象基类：
    提供统一的生命周期管理、中断取消控制与事件通知接口。
    """

    def __init__(self, on_log=None, on_status=None, on_finished=None, on_error=None, on_aborted=None):
        self.on_log = on_log or (lambda msg: None)
        self.on_status = on_status or (lambda status: None)
        self.on_finished = on_finished or (lambda *args: None)
        self.on_error = on_error or (lambda err: None)
        self.on_aborted = on_aborted or (lambda: None)

        self._is_running = False
        self._cancel_requested = False
        self._thread = None

    @property
    def is_running(self):
        return self._is_running

    def request_stop(self):
        self._cancel_requested = True

    def should_abort(self):
        return self._cancel_requested or not self._is_running

    def start(self, *args, **kwargs):
        if self._is_running:
            return
        self._is_running = True
        self._cancel_requested = False
        self._thread = threading.Thread(
            target=self._run_wrapper,
            args=args,
            kwargs=kwargs,
            daemon=True,
            name=self.__class__.__name__
        )
        self._thread.start()

    def _run_wrapper(self, *args, **kwargs):
        try:
            self.execute(*args, **kwargs)
        except Exception as ex:
            import traceback
            err_trace = traceback.format_exc()
            self.on_log(f"流水线发生未捕获异常:\n{err_trace}")
            self.on_error(err_trace)
        finally:
            self._is_running = False

    def execute(self, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement execute()")
```

## File: `pipelines/scheduler.py`

```python
import re
import threading
import time

class SchedulerDaemon:
    """
    后台常驻定时调度守护服务：
    脱离 UI 线程，独立在守护线程中根据设定的时间点或定时间隔，自动触发大优选与优质池复检。
    """

    def __init__(self, get_config_fn, on_trigger_full, on_trigger_fav):
        self.get_config_fn = get_config_fn
        self.on_trigger_full = on_trigger_full
        self.on_trigger_fav = on_trigger_fav

        self._thread = None
        self._running = False
        self.last_full_run_timestamp = 0.0
        self.last_fav_run_timestamp = 0.0
        self.app_start_time = time.time()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="SchedulerDaemonThread")
        self._thread.start()

    def stop(self):
        self._running = False

    def update_last_run(self, full_ts=None, fav_ts=None):
        if full_ts is not None:
            self.last_full_run_timestamp = float(full_ts)
        if fav_ts is not None:
            self.last_fav_run_timestamp = float(fav_ts)

    def _loop(self):
        last_fixed_time_triggered = ""

        while self._running:
            time.sleep(3)
            try:
                now = time.time()
                if now - self.app_start_time < 10.0:
                    continue

                cfg = self.get_config_fn()
                if not cfg or cfg.get("is_pipeline_running", False):
                    continue

                now_dt = time.localtime(now)
                cur_hhmm = time.strftime("%H:%M", now_dt)
                cur_minute_key = time.strftime("%Y-%m-%d %H:%M", now_dt)

                # 1. 全自动大优选定时检测
                if cfg.get("schedule_enabled", False):
                    triggered_full = False
                    trigger_reason_full = ""

                    fixed_times_str = cfg.get("schedule_times", "").strip()
                    if fixed_times_str:
                        times_list = [t.strip() for t in re.split(r"[,，\s]+", fixed_times_str) if t.strip()]
                        if cur_hhmm in times_list and cur_minute_key != last_fixed_time_triggered:
                            last_fixed_time_triggered = cur_minute_key
                            triggered_full = True
                            trigger_reason_full = f"到达设定时间 {cur_hhmm}"

                    interval_str = str(cfg.get("schedule_interval", "")).strip()
                    if not triggered_full and interval_str.isdigit() and int(interval_str) > 0:
                        interval_sec = int(interval_str) * 60
                        elapsed_since_last = now - self.last_full_run_timestamp
                        if elapsed_since_last >= interval_sec:
                            triggered_full = True
                            elapsed_mins = int(elapsed_since_last // 60)
                            trigger_reason_full = f"距离上次测试已过 {elapsed_mins} 分钟"

                    if triggered_full:
                        self.on_trigger_full(trigger_reason_full)
                        continue

                # 2. 优质池复测定时检测
                if cfg.get("fav_schedule_enabled", False) and not cfg.get("is_pipeline_running", False):
                    fav_interval_str = str(cfg.get("fav_schedule_interval", "")).strip()
                    if fav_interval_str.isdigit() and int(fav_interval_str) > 0:
                        fav_interval_sec = int(fav_interval_str) * 60
                        elapsed_fav = now - self.last_fav_run_timestamp
                        if elapsed_fav >= fav_interval_sec:
                            elapsed_fav_mins = int(elapsed_fav // 60)
                            r_reason = f"距离上次优质复测已过 {elapsed_fav_mins} 分钟"
                            self.on_trigger_fav(r_reason)

            except Exception:
                pass
```

## File: `services/__init__.py`

```python
"""
Clash Verge 节点管理助手 - 业务服务层
"""
```

## File: `services/auto_heal_watcher.py`

```python
"""
services/auto_heal_watcher.py
Mihomo 实时链路感知与秒级无感自愈守护服务 (多策略组与非香港业务隔离增强版)
"""
import datetime
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional, Set, Tuple

from config.settings import EXCLUDE_HK_REGEX
from services.clash_client import ClashClient


class AutoHealWatcher:
    """
    后台常驻链路守护引擎：
    1. 并发监听多个核心策略组 (⚡ 自动选择 / ⚡ 自动选择 (非香港))
    2. 监听 Mihomo /connections API 抓取当前真实出口连接表 (CPU < 0.05%, 0额外外网流量)
    3. 检测单向发包黑洞 (Upload > 0, Download == 0 且持续多秒)
    4. 外科手术式斩断坏死连接 (DELETE /connections/{id}) 迫使客户端瞬间 TCP RST 重连
    5. 严格业务与区域隔离：
       - 【⚡ 自动选择 (非香港)】坏死时：严格在纯净非香港池（新加坡、日本、美国等）顺位补位，绝不切入香港！
       - 【⚡ 自动选择】坏死时：在全量精选池中挑选最优低延迟节点补位
    6. 熔断隔离坏死节点 15 分钟，防止反复横跳
    """

    def __init__(
        self,
        client: Optional[ClashClient] = None,
        get_candidates_fn: Optional[Callable[..., List[str]]] = None,
        on_heal_event: Optional[Callable[[str, str, dict], None]] = None,
        on_status_update: Optional[Callable[[dict], None]] = None,
        log_fn: Optional[Callable[[str], None]] = None,
        check_interval: float = 1.0,
        idle_timeout_seconds: float = 5.0,
        cooldown_duration: float = 900.0,
        min_switch_interval: float = 8.0,
        probe_timeout_ms: int = 1500,
        probe_url: str = "https://www.google.com/generate_204",
        min_blackhole_hosts: int = 2,
        is_pipeline_running_fn: Optional[Callable[[], bool]] = None,
        startup_grace_period: float = 15.0,
    ):
        self.client = client or ClashClient()
        self.get_candidates_fn = get_candidates_fn
        self.on_heal_event = on_heal_event
        self.on_status_update = on_status_update
        self.log_fn = log_fn
        self.is_pipeline_running_fn = is_pipeline_running_fn

        # 开机/启动冷启动静默保护期配置 (秒)
        self.startup_grace_period: float = max(0.0, float(startup_grace_period))
        self._start_time: float = time.time()

        # 核心探测参数
        self.enabled: bool = True
        self.check_interval: float = max(0.5, float(check_interval))
        self.idle_timeout_seconds: float = float(idle_timeout_seconds)
        self.min_blackhole_hosts: int = max(1, int(min_blackhole_hosts))
        self.probe_timeout_ms: int = max(500, int(probe_timeout_ms))
        self.cooldown_duration: float = 900.0      # 坏死节点临时熔断冷冻时长 (秒, 默认15分钟)
        self.min_switch_interval: float = 8.0      # 连续自愈最小时间间隔 (防雪崩/防抖动)
        self.conn_snapshots: Dict[str, dict] = {}  # {conn_id: {"up": int, "down": int, "ts": float, "stall_since": float}}
        self.probe_urls: List[str] = [
            "https://www.google.com/generate_204",
            "https://www.gstatic.com/generate_204",
        ]
        self.probe_url: str = probe_url

        # 【主循环彻底解耦与防抖核心】
        self._heal_lock = threading.Lock()
        self._healing_groups: Set[str] = set()     # 正在执行异步自愈流水线的策略组集合
        self._heal_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="AutoHealWorker")

        # 主动心跳巡检双保险配置 (Proactive Heartbeat)
        self.heartbeat_interval: float = 4.0       # 每 4 秒主动轮询一次当前在用节点
        self.last_heartbeat_time: float = 0.0
        self._heartbeat_lock = threading.Lock()
        self._heartbeat_running: bool = False
        
        # Cloudflare 专属平滑自愈与防抽风参数
        self.degrade_rtt_ms: int = 280            # 哨兵探针严重劣化判定门禁 (毫秒)
        self.strike_min_interval: float = 10.0    # 两次黄牌认定的最小观察间隔 (秒, 避免1秒内连出两牌)
        self.strike_window: float = 60.0          # 黄牌累积计分窗口 (秒)
        self.yellow_cards: Dict[str, float] = {}  # {node_name: last_strike_timestamp}
        self.soft_stall_bytes_limit: int = 3072   # 软失速下行速率下限 (字节/秒, 约3KB/s)

        # Google 送中感知冷冻黑名单与探针防御 (防香港 Anycast 导致 Gemini / IDE 报 403)
        self.google_hk_nodes: Dict[str, float] = {
            "东京 NRT 11.40 MB/s 3": time.time() + 86400,
            "东京 NRT 5.94 MB/s": time.time() + 86400,
            "东京 NRT 9.41 MB/s": time.time() + 86400,
        }
        self._last_google_check: Dict[str, float] = {}  # {node_name: last_check_ts}
        
        # 守护的核心策略组清单
        self.monitored_groups: List[str] = [
            "⚡ 自动选择",
            "⚡ 自动选择 (非香港)",
        ]

        # 内存热备候选队列缓存 (Pre-warmed Standby Cache, 0 延迟切换)
        self.standby_cache: Dict[str, List[str]] = {}

        # 运行时状态
        self._thread: Optional[threading.Thread] = None
        self._running: bool = False
        self._lock = threading.Lock()
        
        self.cooldown_nodes: Dict[str, float] = {}  # {node_name: expire_timestamp}
        self.healed_count: int = 0
        self.last_heal_timestamp: float = 0.0
        self.last_heal_info: Optional[dict] = None
        
        self.current_active_node: str = ""         # 全量出口当前在用
        self.current_active_nohk_node: str = ""    # 非港出口当前在用
        self.current_status_summary: str = "守护就绪"

    def log(self, message: str):
        if callable(self.log_fn):
            try:
                self.log_fn(message)
            except Exception:
                pass

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._running = True
            self._thread = threading.Thread(
                target=self._loop,
                daemon=True,
                name="AutoHealWatcherThread"
            )
            self._thread.start()
            self.log("🛡️ [自愈引擎] 后台秒级链路守卫服务已启动 (双通道智能感知中)")

    def stop(self):
        with self._lock:
            self._running = False
        try:
            self._heal_executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass

    def is_running(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    def update_config(self, **kwargs):
        with self._lock:
            if "enabled" in kwargs:
                self.enabled = bool(kwargs["enabled"])
            if "check_interval" in kwargs:
                try:
                    self.check_interval = max(1.0, float(kwargs["check_interval"]))
                except (ValueError, TypeError):
                    pass
            if "blackhole_timeout" in kwargs:
                try:
                    self.blackhole_timeout = max(1.5, float(kwargs["blackhole_timeout"]))
                except (ValueError, TypeError):
                    pass
            if "cooldown_duration" in kwargs:
                try:
                    self.cooldown_duration = max(60.0, float(kwargs["cooldown_duration"]))
                except (ValueError, TypeError):
                    pass
            if "degrade_rtt_ms" in kwargs:
                try:
                    self.degrade_rtt_ms = max(100, int(kwargs["degrade_rtt_ms"]))
                except (ValueError, TypeError):
                    pass
            if "strike_min_interval" in kwargs:
                try:
                    self.strike_min_interval = max(5.0, float(kwargs["strike_min_interval"]))
                except (ValueError, TypeError):
                    pass
            if "strike_window" in kwargs:
                try:
                    self.strike_window = max(10.0, float(kwargs["strike_window"]))
                except (ValueError, TypeError):
                    pass
            if "probe_timeout_ms" in kwargs:
                try:
                    self.probe_timeout_ms = max(500, int(kwargs["probe_timeout_ms"]))
                except (ValueError, TypeError):
                    pass
            if "probe_url" in kwargs and kwargs["probe_url"]:
                self.probe_url = str(kwargs["probe_url"]).strip()
            if "min_blackhole_hosts" in kwargs:
                try:
                    self.min_blackhole_hosts = max(1, int(kwargs["min_blackhole_hosts"]))
                except (ValueError, TypeError):
                    pass

    def get_status_dict(self) -> dict:
        now = time.time()
        active_cooldowns = {k: int(v - now) for k, v in self.cooldown_nodes.items() if v > now}
        active_yellow_cards = {k: int(v + self.strike_window - now) for k, v in self.yellow_cards.items() if (v + self.strike_window) > now}
        active_google_hk = {k: int(v - now) for k, v in self.google_hk_nodes.items() if v > now}
        status_summary = self.current_status_summary
        if callable(self.is_pipeline_running_fn) and self.is_pipeline_running_fn():
            status_summary = "⏸️ 优选测速中 (心跳探针自动避让)"
        return {
            "enabled": self.enabled,
            "running": self.is_running(),
            "active_node": self.current_active_node,
            "active_nohk_node": self.current_active_nohk_node,
            "status_summary": status_summary,
            "healed_count": self.healed_count,
            "last_heal_time": self.last_heal_timestamp,
            "last_heal_info": self.last_heal_info,
            "cooldown_nodes_count": len(active_cooldowns),
            "cooldown_nodes": active_cooldowns,
            "yellow_cards_count": len(active_yellow_cards),
            "yellow_cards": active_yellow_cards,
            "google_hk_nodes_count": len(active_google_hk),
            "google_hk_nodes": active_google_hk,
        }

    def _parse_start_time(self, start_str: str) -> float:
        if not start_str:
            return 0.0
        try:
            clean_str = start_str
            if "+" in clean_str:
                dt_part, tz_part = clean_str.split("+", 1)
                if "." in dt_part:
                    base, micro = dt_part.split(".", 1)
                    clean_str = f"{base}.{micro[:6]}+{tz_part}"
                dt = datetime.datetime.fromisoformat(clean_str)
                return dt.timestamp()
            elif "Z" in clean_str:
                clean_str = clean_str.replace("Z", "+00:00")
                dt = datetime.datetime.fromisoformat(clean_str)
                return dt.timestamp()
        except Exception:
            pass
        return time.time()

    def _is_ignorable_background_host(self, host: str) -> bool:
        """
        判断是否为系统后台静默长轮询、推送通道或遥测连接 (如 Google FCM / Meet Signaler / Apple APNs)。
        这些连接由客户端发起后长期挂起等待服务端下发事件，期间无下行数据属于完全正常的预期行为，
        必须从断流与软失速检测中白名单排除，避免误判为物理黑洞。
        """
        if not host:
            return True
        h = host.lower().strip()
        ignorable_keywords = (
            "mtalk.google.com",
            "signaler-pa.clients6.google.com",
            "chat-pa.clients6.google.com",
            "push.apple.com",
            "pipe.aria.microsoft.com",
            "gateway.facebook.com",
        )
        for kw in ignorable_keywords:
            if kw in h:
                return True
        return False

    def _is_external_host(self, host: str) -> bool:
        if not host:
            return False
        h = host.lower().strip()
        if h in ("localhost", "127.0.0.1", "::1"):
            return False
        if h.endswith(".local") or h.endswith(".internal"):
            return False
        if h.startswith("192.168.") or h.startswith("10.") or h.startswith("172."):
            return False
        if self._is_ignorable_background_host(h):
            return False
        return True

    def _get_root_domain(self, host: str) -> str:
        """
        提取根域名 (Apex Domain)，将同厂不同子域名 (如 www.bing.com 与 cn.bing.com，
        或 YouTube 的不同 googlevideo.com CDN 节点) 聚类为同一个根域名，
        防止因访问单个网站时多个子域名并发请求误触发多域名断流判定。
        """
        if not host:
            return ""
        h = host.strip().lower()
        if ":" in h and not h.startswith("["):
            h = h.split(":")[0]

        parts = h.split(".")
        if len(parts) == 4 and all(p.isdigit() for p in parts):
            return h

        if len(parts) <= 2:
            return h

        second_level_tlds = {
            "com.cn", "net.cn", "org.cn", "gov.cn", "edu.cn",
            "co.uk", "org.uk", "me.uk",
            "com.hk", "org.hk", "net.hk", "edu.hk",
            "com.tw", "org.tw", "net.tw",
            "com.jp", "co.jp", "ne.jp",
            "com.sg", "edu.sg",
        }
        two_tail = f"{parts[-2]}.{parts[-1]}"
        if two_tail in second_level_tlds and len(parts) >= 3:
            return f"{parts[-3]}.{two_tail}"
        return f"{parts[-2]}.{parts[-1]}"

    def _loop(self):
        prev_loop_ts = time.time()
        while self._running:
            try:
                time.sleep(self.check_interval)
                if not self.enabled:
                    self.current_status_summary = "已暂停守护"
                    prev_loop_ts = time.time()
                    continue

                now = time.time()
                # 检测系统休眠/挂起唤醒或时间大跳变 (实际间隔严重超出预期步长 8.0 秒以上)
                if (now - prev_loop_ts) > 8.0:
                    prev_loop_ts = now
                    self.conn_snapshots.clear()
                    self.last_heartbeat_time = now + 2.0  # 延后主动心跳，给予网卡 Wi-Fi 2~3 秒握手缓冲
                    self.log("💤 [休眠唤醒保护] 检测到系统唤醒或时间跳变，已重置监控快照并给予网卡 3 秒重连缓冲")
                    continue
                prev_loop_ts = now

                self._check_and_heal()
            except Exception:
                pass

    def _check_and_heal(self):
        if callable(self.is_pipeline_running_fn) and self.is_pipeline_running_fn():
            self.current_status_summary = "⏸️ 优选测速中 (心跳探针自动避让)"
            self._notify_status()
            return

        now = time.time()

        # 开机/启动冷启动静默保护期：前 15 秒仅监控更新，绝不下发任何物理切换与断流操作
        if (now - self._start_time) < self.startup_grace_period:
            remain = int(self.startup_grace_period - (now - self._start_time))
            self.current_status_summary = f"⏳ 开机网络热身静默保护中 ({remain}s)"
            self._notify_status()
            return

        # 1. 轻量拉取各组当前在用节点（调用 self.client.get_proxy(grp)）
        group_current_nodes: Dict[str, str] = {}
        for grp in self.monitored_groups:
            g_data = self.client.get_proxy(grp, timeout=0.8)
            c_node = g_data.get("now", "")
            if c_node:
                group_current_nodes[grp] = c_node

        self.current_active_node = group_current_nodes.get("⚡ 自动选择", "未知出口")
        self.current_active_nohk_node = group_current_nodes.get("⚡ 自动选择 (非香港)", "未知非港出口")

        # 2. 读取当前活跃连接快照
        conns_data = self.client.get_connections(timeout=1.5)
        if not conns_data or not isinstance(conns_data, dict):
            return

        connections = conns_data.get("connections", [])
        if not connections:
            self.conn_snapshots.clear()
            self.current_status_summary = f"空闲就绪 (全量: {self.current_active_node} | 非港: {self.current_active_nohk_node})"
            self._notify_status()
            return

        # 3. 严格协议过滤与 Delta Rate 增量计算
        blackhole_hosts: Dict[Tuple[str, str], Set[str]] = {}
        blackhole_conn_ids: Dict[Tuple[str, str], List[str]] = {}
        blackhole_stall_types: Dict[Tuple[str, str], Set[str]] = {}
        blackhole_max_durations: Dict[Tuple[str, str], float] = {}
        active_cids: Set[str] = set()

        for conn in connections:
            cid = conn.get("id")
            if not cid:
                continue
            active_cids.add(cid)

            # 严格协议过滤：仅分析 net_type == "tcp" 的外部连接，非 TCP 协议（UDP/ICMP）直接 continue 跳过
            metadata = conn.get("metadata", {})
            net_type = str(metadata.get("network", "") or conn.get("network", "")).lower()
            if net_type != "tcp":
                continue

            host = metadata.get("host") or metadata.get("destinationIP") or ""
            if not self._is_external_host(host):
                continue

            chains = conn.get("chains", [])
            node_name = chains[0] if chains else ""
            if not node_name:
                continue

            upload = conn.get("upload", 0)
            download = conn.get("download", 0)
            start_ts = self._parse_start_time(conn.get("start", ""))
            duration = now - start_ts

            is_stalled = False
            stall_type = ""
            stall_duration = 0.0

            # 4. Delta Rate 增量计算与严格四态状态机
            if cid not in self.conn_snapshots:
                # 若 conn_id 首次出现：初始化 snapshot
                if upload > 0 and download == 0:
                    stall_since = (now - duration) if duration > 0 else now
                    if duration >= self.blackhole_timeout:
                        is_stalled = True
                        stall_type = "硬断流"
                        stall_duration = duration
                elif upload > 0:
                    stall_since = now
                else:
                    stall_since = 0.0

                self.conn_snapshots[cid] = {
                    "up": upload,
                    "down": download,
                    "ts": now,
                    "stall_since": stall_since,
                }
            else:
                prev = self.conn_snapshots[cid]
                delta_up = upload - prev["up"]
                delta_down = download - prev["down"]
                prev["up"], prev["down"], prev["ts"] = upload, download, now

                # 严格四态状态转移：
                # (a) 若 delta_down > 0: 说明真正接收到了服务端回包，链路健康畅通，解除计时
                if delta_down > 0:
                    prev["stall_since"] = 0.0
                # (b) 若 delta_up > 0: 客户端产生新上传，若此前未处于挂起状态，则置 stall_since = now
                elif delta_up > 0:
                    if prev["stall_since"] == 0.0:
                        prev["stall_since"] = now
                # (c) 若 upload > 0 and download == 0: 纯物理发包黑洞，若未挂起则置 stall_since = now
                elif upload > 0 and download == 0:
                    if prev["stall_since"] == 0.0:
                        prev["stall_since"] = now
                # (d) 若 delta_up == 0 and delta_down == 0: 客户端处于等待服务端响应的挂起状态 (In-Flight)
                # 【关键红线】：若此时 prev["stall_since"] > 0.0，绝对禁止重置为 0.0！必须保持原有时间戳继续累加！
                else:
                    pass

                # 判定是否超时卡死
                if prev["stall_since"] > 0.0 and (now - prev["stall_since"]) >= self.blackhole_timeout:
                    is_stalled = True
                    stall_type = "在途软失速" if download > 0 else "硬断流"
                    stall_duration = now - prev["stall_since"]

            if is_stalled:
                matched_grp = None
                for grp in self.monitored_groups:
                    if grp in chains:
                        matched_grp = grp
                        break

                if not matched_grp:
                    for grp, curr_n in group_current_nodes.items():
                        if curr_n == node_name:
                            matched_grp = grp
                            break

                if not matched_grp:
                    matched_grp = "⚡ 自动选择"

                pair_key = (matched_grp, node_name)
                if pair_key not in blackhole_hosts:
                    blackhole_hosts[pair_key] = set()
                    blackhole_conn_ids[pair_key] = []
                    blackhole_stall_types[pair_key] = set()
                    blackhole_max_durations[pair_key] = 0.0

                root_domain = self._get_root_domain(host)
                blackhole_hosts[pair_key].add(root_domain or host)
                blackhole_conn_ids[pair_key].append(cid)
                blackhole_stall_types[pair_key].add(stall_type)
                if stall_duration > blackhole_max_durations[pair_key]:
                    blackhole_max_durations[pair_key] = stall_duration

        # 5. 清理已断开连接的 snapshot 字典，防止内存泄漏
        dead_keys = [k for k in self.conn_snapshots if k not in active_cids]
        for k in dead_keys:
            self.conn_snapshots.pop(k, None)

        # 6. 复合触发判定与异步分发（0ms 阻塞）
        self._refresh_standby_cache()

        for grp, curr_n in group_current_nodes.items():
            pair_key = (grp, curr_n)
            distinct_hosts = blackhole_hosts.get(pair_key, set())
            stalled_conns = blackhole_conn_ids.get(pair_key, [])
            max_stall_duration = blackhole_max_durations.get(pair_key, 0.0)

            # 多阶自愈触发门禁：适配单应用 IDE (如反重力) 与流式大模型长连接
            is_suspicious = (
                (len(distinct_hosts) >= self.min_blackhole_hosts) or
                (len(distinct_hosts) >= 1 and len(stalled_conns) >= 2) or
                (len(stalled_conns) >= 1 and max_stall_duration >= max(3.0, self.blackhole_timeout * 1.5))
            )

            if is_suspicious:
                # 【防抖防重入门禁检查】
                with self._heal_lock:
                    if grp in self._healing_groups:
                        continue  # 该策略组已有后台自愈任务在执行，跳过，绝不重复触发！
                    if (now - self.last_heal_timestamp) < self.min_switch_interval:
                        continue  # 处于避震窗口内，跳过
                    # 成功获取自愈任务令牌
                    self._healing_groups.add(grp)

                # 【Fire-and-Forget 瞬间分发到独立线程池，主循环 0 毫秒放行，绝不等待任何结果】
                stall_desc = "/".join(sorted(list(blackhole_stall_types.get(pair_key, set())))) or "断流"
                is_non_hk = ("非香港" in grp)
                self._heal_executor.submit(
                    self._async_heal_worker,
                    grp,
                    curr_n,
                    list(distinct_hosts),
                    list(stalled_conns),
                    is_non_hk,
                    stall_desc,
                )

        with self._heal_lock:
            currently_healing = list(self._healing_groups)

        if currently_healing:
            self.current_status_summary = (
                f"🔄 深度自愈探查中 (目标组: {', '.join(currently_healing)})"
            )
            self._notify_status()
        else:
            active_count = len(connections)
            yc_count = len([k for k, v in self.yellow_cards.items() if (now - v) <= self.strike_window])
            yc_str = f" | 🟨黄牌节点: {yc_count}" if yc_count > 0 else ""
            self.current_status_summary = (
                f"🟢 双通道畅通 (全量: {self.current_active_node} | 非港: {self.current_active_nohk_node} | 活跃: {active_count}{yc_str})"
            )
            self._notify_status()

        # 7. 主动心跳巡检双保险 (Proactive Heartbeat - 0ms 异步分发)
        if (now - self.last_heartbeat_time) >= self.heartbeat_interval:
            with self._heartbeat_lock:
                if not self._heartbeat_running:
                    self._heartbeat_running = True
                    self.last_heartbeat_time = now
                    self._heal_executor.submit(self._proactive_heartbeat_worker)

    def _async_heal_worker(
        self,
        grp: str,
        curr_n: str,
        distinct_hosts: list,
        dead_conn_ids: list,
        is_non_hk: bool,
        stall_desc: str,
    ):
        """
        独立线程池中执行的自愈工作流水线：
        双通道 HTTPS 竞速探针 -> 裁决判定 -> 顺位切换 -> 并发清理僵尸连接
        """
        try:
            # 1. 双通道 HTTPS 并发竞速探针（验证 443 端口与 TLS 握手）
            probe_delay = 99999
            for u in self.probe_urls:
                d = self.client.query_proxy_delay(curr_n, u, timeout_ms=self.probe_timeout_ms)
                if d < probe_delay:
                    probe_delay = d
                if probe_delay < self.degrade_rtt_ms:
                    break  # 极速响应直接短路返回，无需重复探测

            # 2. 探针裁决逻辑
            now = time.time()
            hosts_preview = ", ".join(sorted(distinct_hosts)[:3])
            if probe_delay >= 99999:
                # 二次复验防抖机制：首次超时后等待 500ms 重试确认，两次均超时方判定为暴毙
                time.sleep(0.5)
                for u in self.probe_urls:
                    rd = self.client.query_proxy_delay(curr_n, u, timeout_ms=self.probe_timeout_ms)
                    if rd < probe_delay:
                        probe_delay = rd
                    if probe_delay < self.degrade_rtt_ms:
                        break

            if probe_delay >= 99999:
                # 确认物理暴毙，立即下发自愈顺移
                dead_reason = (
                    f"【{grp}】并发 {len(distinct_hosts)} 个主域名{stall_desc}且 HTTPS 双探针超时暴毙 (二次复验确认，目标: {hosts_preview})"
                )
                self.yellow_cards.pop(curr_n, None)
                self._execute_auto_heal(
                    target_group=grp,
                    dead_node=curr_n,
                    reason=dead_reason,
                    dead_conn_ids=dead_conn_ids,
                    is_non_hk=is_non_hk,
                )
            elif probe_delay >= self.degrade_rtt_ms:
                # 黄牌观察与两黄变一红机制
                last_card_ts = self.yellow_cards.get(curr_n, 0.0)
                time_since_last_card = now - last_card_ts
                if self.strike_min_interval <= time_since_last_card <= self.strike_window:
                    dead_reason = (
                        f"【{grp}】二次抽风/延迟严重劣化 ({probe_delay}ms >= {self.degrade_rtt_ms}ms, {stall_desc}) (目标: {hosts_preview})"
                    )
                    self.yellow_cards.pop(curr_n, None)
                    self._execute_auto_heal(
                        target_group=grp,
                        dead_node=curr_n,
                        reason=dead_reason,
                        dead_conn_ids=dead_conn_ids,
                        is_non_hk=is_non_hk,
                    )
                elif time_since_last_card > self.strike_window or last_card_ts == 0.0:
                    self.yellow_cards[curr_n] = now
                    self.log(f"🟨 [自愈黄牌] 节点 【{curr_n}】 延迟飙升 ({probe_delay}ms)，出示黄牌进入观察期...")
                    self.current_status_summary = f"🟨 黄牌警告 ({curr_n} 延迟 {probe_delay}ms) | 观察中"
                    self._notify_status()
            else:
                # 探针极速通畅，一票否决证明健康
                if curr_n in self.yellow_cards and (now - self.yellow_cards[curr_n]) > self.strike_window:
                    self.yellow_cards.pop(curr_n, None)
        except Exception as e:
            self.log(f"⚠️ [自愈流水线异常] {grp} 自愈处理过程发生异常: {e}")
        finally:
            # 【防抖锁释放】：流水线结束（无论成功或异常），必须在锁内移出 grp
            with self._heal_lock:
                self._healing_groups.discard(grp)

    def _inspect_google_node_compliance(self, c_node: str) -> Tuple[bool, str, str]:
        """
        全面深度检测非香港出口节点的 Google 洁净度：
        1. 检测 Google Anycast 送中 (.hk 重定向)
        2. 检测 Google 官方风控拦截 (HTTP 429 Too Many Requests / 403 Forbidden / sorry/index 人机验证)
        返回: (is_bad: bool, bad_type: str, detail_msg: str)
        """
        now = time.time()
        # 1. 优先查长效冷冻记录
        if c_node in self.google_hk_nodes and self.google_hk_nodes[c_node] > now:
            remain = int(self.google_hk_nodes[c_node] - now)
            return True, "Google 拦截隔离", f"该节点处于长效熔断期 (剩余 {remain}s)"

        mix_port = self.client.get_mixed_port(default=7897)
        proxy_handler = urllib.request.ProxyHandler({
            "http": f"http://127.0.0.1:{mix_port}",
            "https": f"http://127.0.0.1:{mix_port}",
        })
        opener = urllib.request.build_opener(proxy_handler)
        g_req = urllib.request.Request(
            "https://www.google.com",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )

        try:
            with opener.open(g_req, timeout=3.0) as g_resp:
                final_u = g_resp.geturl()
                if "google.com.hk" in final_u:
                    return True, "Google Anycast 送中", f"重定向至 {final_u} (.hk 归属)"
                if "sorry" in final_u or "/sorry/" in final_u:
                    return True, "Google 官方风控拦截", f"导向人机验证页面: {final_u}"
                return False, "CLEAN", final_u
        except urllib.error.HTTPError as e:
            # 精准捕获 Google 官方风控 429 / 403 / 503 及 sorry 重定向
            loc = e.headers.get("Location", "") if hasattr(e, "headers") else ""
            if e.code == 429 or "sorry" in getattr(e, "url", "") or "sorry" in loc:
                return True, "Google 官方风控拦截", f"HTTP 429 Too Many Requests (人机验证拦截)"
            elif e.code == 403:
                return True, "Google 区域受限拦截", f"HTTP 403 Forbidden (非授权区域受限)"
            elif "google.com.hk" in getattr(e, "url", "") or "google.com.hk" in loc:
                return True, "Google Anycast 送中", f"重定向抛错且包含 .hk"
            return False, f"HTTP_{e.code}", str(e)
        except Exception as ex:
            return False, "EXCEPTION", str(ex)

    def _proactive_heartbeat_worker(self):
        """
        后台异步主动心跳巡检双保险流水线：
        周期性轻量化双探针竞速探测各受监控策略组当前在用节点的可用性，
        若检测到物理暴毙（超时 >= 99999ms）或非港出口触发 Google 送中/官方拦截，抓取坏死连接并立即触发自愈切换。
        """
        if callable(self.is_pipeline_running_fn) and self.is_pipeline_running_fn():
            self.current_status_summary = "⏸️ 优选测速中 (心跳探针自动避让)"
            self._notify_status()
            return

        now = time.time()
        if (now - self._start_time) < self.startup_grace_period:
            return

        try:
            for grp in self.monitored_groups:
                g_data = self.client.get_proxy(grp, timeout=0.8)
                c_node = g_data.get("now", "")
                if not c_node:
                    continue

                is_non_hk = ("非香港" in grp)

                # (0) 非香港策略组专属：Google 官方拦截与送中洁净度感知防御双保险
                if is_non_hk:
                    is_bad = False
                    bad_type = ""
                    detail_msg = ""

                    if c_node in self.google_hk_nodes and self.google_hk_nodes[c_node] > now:
                        is_bad = True
                        bad_type = "Google 拦截隔离"
                        detail_msg = f"该节点处于长效熔断期 (剩余 {int(self.google_hk_nodes[c_node] - now)}s)"
                    elif (now - self._last_google_check.get(c_node, 0.0)) >= 30.0:
                        self._last_google_check[c_node] = now
                        is_bad, bad_type, detail_msg = self._inspect_google_node_compliance(c_node)
                        if is_bad:
                            self.google_hk_nodes[c_node] = now + 43200
                            self.cooldown_nodes[c_node] = now + 43200
                            self.log(f"🚨 [{bad_type}] 节点 【{c_node}】 {detail_msg}，触发非港 12 小时自愈熔断！")

                    if is_bad:
                        with self._heal_lock:
                            if grp in self._healing_groups:
                                continue
                            if (now - self.last_heal_timestamp) < self.min_switch_interval:
                                continue
                            self._healing_groups.add(grp)

                        try:
                            dead_cids = []
                            try:
                                conns_data = self.client.get_connections(timeout=1.2)
                                if conns_data and isinstance(conns_data, dict):
                                    for conn in conns_data.get("connections", []):
                                        chains = conn.get("chains", [])
                                        if c_node in chains or (chains and chains[0] == c_node):
                                            cid = conn.get("id")
                                            if cid:
                                                dead_cids.append(cid)
                            except Exception:
                                dead_cids = []

                            self._execute_auto_heal(
                                target_group=grp,
                                dead_node=c_node,
                                reason=f"【{grp}】{bad_type} ({detail_msg})，触发 12 小时熔断隔离保护 Gemini/IDE",
                                dead_conn_ids=dead_cids,
                                is_non_hk=True,
                            )
                        finally:
                            with self._heal_lock:
                                self._healing_groups.discard(grp)
                        continue

                # (a) 双探针竞速探测
                d = 99999
                for u in self.probe_urls:
                    cur_d = self.client.query_proxy_delay(c_node, u, timeout_ms=self.probe_timeout_ms)
                    if cur_d < d:
                        d = cur_d
                    if d < self.degrade_rtt_ms:
                        break

                if d >= 99999:
                    # 二次复验防抖机制：首次超时后等待 500ms 重试确认，两次均超时方判定为暴毙
                    time.sleep(0.5)
                    d2 = 99999
                    for u in self.probe_urls:
                        cur_d2 = self.client.query_proxy_delay(c_node, u, timeout_ms=self.probe_timeout_ms)
                        if cur_d2 < d2:
                            d2 = cur_d2
                        if d2 < self.degrade_rtt_ms:
                            break
                    if d2 < 99999:
                        # 二次复验恢复健康，安全放行
                        continue

                    with self._heal_lock:
                        if grp in self._healing_groups:
                            continue  # 被动异步工作线程已在处理该组自愈，主动心跳主动让行，杜绝重复触发
                        if (now - self.last_heal_timestamp) < self.min_switch_interval:
                            continue  # 处于避震窗口期，跳过
                        self._healing_groups.add(grp)

                    try:
                        # (b) 确认物理暴毙，主动从内核抓取当前所有活跃连接，提取挂在该坏死节点上的连接 ID
                        dead_cids = []
                        try:
                            conns_data = self.client.get_connections(timeout=1.2)
                            if conns_data and isinstance(conns_data, dict):
                                for conn in conns_data.get("connections", []):
                                    chains = conn.get("chains", [])
                                    if c_node in chains or (chains and chains[0] == c_node):
                                        cid = conn.get("id")
                                        if cid:
                                            dead_cids.append(cid)
                        except Exception:
                            dead_cids = []

                        # (c) 传入 dead_conn_ids 立即并发清退，触发客户端瞬间重连
                        self._execute_auto_heal(
                            target_group=grp,
                            dead_node=c_node,
                            reason=f"【{grp}】主动心跳探针超时(>{self.probe_timeout_ms}ms物理断流，二次复验确认)",
                            dead_conn_ids=dead_cids,
                            is_non_hk=is_non_hk,
                        )
                    finally:
                        with self._heal_lock:
                            self._healing_groups.discard(grp)
        except Exception as e:
            self.log(f"⚠️ [主动心跳探针异常] 巡检过程发生错误: {e}")
        finally:
            with self._heartbeat_lock:
                self._heartbeat_running = False

    def _execute_auto_heal(
        self,
        target_group: str,
        dead_node: str,
        reason: str,
        dead_conn_ids: List[str],
        is_non_hk: bool = False,
    ):
        now = time.time()
        if now - self.last_heal_timestamp < self.min_switch_interval:
            self.log(f"⚠️ [自愈避震] 策略组 【{target_group}】 节点 {dead_node} 异常，但距离上次切换不足 {int(self.min_switch_interval)}s，暂缓动作")
            return

        tag_prefix = "🛡️ [非港AI自愈]" if is_non_hk else "🚨 [全量出口自愈]"
        self.log(f"{tag_prefix} 检测到策略组 【{target_group}】 当前在用节点 【{dead_node}】 触发自愈！原因: {reason}")

        # 步骤 1：挑选次优顺位备选节点 (若为非港组，绝对排除香港)
        backup_node = self._pick_backup_node(
            target_group=target_group,
            exclude_node=dead_node,
            is_non_hk=is_non_hk,
        )
        if not backup_node:
            self.log(f"❌ [自愈失败] 策略组 【{target_group}】 中未找到可用的健康备选节点！")
            return

        # 步骤 2：毫秒级优雅引流 —— 0ms 瞬间把出口切换至热备节点 (所有新请求/重发秒走新路)
        t0 = time.perf_counter()
        switched = self.client.switch_proxy(target_group, backup_node, timeout=1.5)
        switch_cost_ms = (time.perf_counter() - t0) * 1000

        if switched:
            # 步骤 3：坏死节点冷冻熔断 15 分钟 (若触发 Google 官方拦截/送中则冷冻 12 小时)
            self.cooldown_nodes[dead_node] = now + self.cooldown_duration
            if is_non_hk and ("Google" in reason or dead_node in self.google_hk_nodes):
                self.google_hk_nodes[dead_node] = max(self.google_hk_nodes.get(dead_node, 0.0), now + 43200)
                self.cooldown_nodes[dead_node] = max(self.cooldown_nodes.get(dead_node, 0.0), now + 43200)
            self.healed_count += 1
            self.last_heal_timestamp = now

            if is_non_hk:
                self.current_active_nohk_node = backup_node
            else:
                self.current_active_node = backup_node

            self.last_heal_info = {
                "group": target_group,
                "dead_node": dead_node,
                "backup_node": backup_node,
                "is_non_hk": is_non_hk,
                "cost_ms": round(switch_cost_ms, 1),
                "evicted": len(dead_conn_ids),
                "reason": reason,
                "time": time.strftime("%H:%M:%S", time.localtime(now))
            }

            non_hk_tip = " (已严格继承非港限制，Gemini/反重力保持畅通)" if is_non_hk else ""
            log_msg = f"✨ [优雅引流完成] 策略组 【{target_group}】 耗时 {switch_cost_ms:.1f}ms 顺移至备选节点 【{backup_node}】！原因: {reason}{non_hk_tip}"
            self.log(log_msg)

            # 步骤 4：异步平滑并发清退 —— 双保险真空吸尘器
            def _delayed_drain():
                evicted_count = 0
                # 1. 优先并发斩断预先抓取到的指定死连接 ID
                valid_cids = [cid for cid in dead_conn_ids if cid]
                if valid_cids:
                    try:
                        with ThreadPoolExecutor(max_workers=8) as pool:
                            results = list(pool.map(lambda cid: self.client.close_connection(cid, timeout=0.8), valid_cids))
                            evicted_count += sum(1 for r in results if r)
                    except Exception:
                        pass

                # 2. 毫秒级二次真空扫尾：调用底层 close_connections_by_proxy 切断任何残留或刚产生的孤儿连接
                try:
                    time.sleep(0.1)  # 给予 100ms 裕量让策略组路由完全生效
                    extra_closed = self.client.close_connections_by_proxy(dead_node, timeout=1.2)
                    evicted_count += extra_closed
                except Exception:
                    pass

                if evicted_count > 0:
                    self.log(f"🔪 [定点扫尾] 已双重并发精准清理旧节点 【{dead_node}】 遗留的 {evicted_count} 条死锁僵尸连接")

            threading.Thread(target=_delayed_drain, daemon=True, name="HealDrainThread").start()

            self.current_status_summary = f"⚡ 刚刚自愈: 【{target_group}】已顺移至 {backup_node}"

            if callable(self.on_heal_event):
                try:
                    self.on_heal_event(dead_node, backup_node, self.last_heal_info)
                except Exception:
                    pass
        else:
            self.log(f"❌ [自愈切换失败] 向策略组 【{target_group}】 推送目标节点失败！")

        self._notify_status()

    def _refresh_standby_cache(self, proxies_map: Optional[dict] = None):
        """
        在后台心跳中预先计算并缓存各策略组的顺位热备节点 (Pre-warmed Standby)，
        100% 以内核策略组真实 all 成员为唯一权威事实源，彻底消灭 HTTP 400 切换脱节。
        """
        now = time.time()
        for grp in self.monitored_groups:
            is_non_hk = ("非香港" in grp)

            # (a) 100% 以内核该策略组的真实成员为权威基准
            all_members: List[str] = []
            if proxies_map and grp in proxies_map:
                all_members = list(proxies_map.get(grp, {}).get("all", []))
            if not all_members:
                g_data = self.client.get_proxy(grp, timeout=0.8)
                all_members = list(g_data.get("all", []))

            if not all_members:
                continue

            # (b) 区域合规过滤 (非港组剔除香港节点及被 Google 送中冷冻的节点)
            if is_non_hk:
                valid_members = [
                    c for c in all_members
                    if c and not EXCLUDE_HK_REGEX.search(c)
                    and (c not in self.google_hk_nodes or self.google_hk_nodes[c] <= now)
                ]
            else:
                valid_members = [c for c in all_members if c]

            if not valid_members:
                continue

            # (d) 智能排序算法：从节点名正则提取速度，结合 get_candidates_fn 建立权重映射
            fav_cands: List[str] = []
            if callable(self.get_candidates_fn):
                try:
                    fav_cands = self.get_candidates_fn(is_non_hk=is_non_hk) or []
                except TypeError:
                    fav_cands = self.get_candidates_fn() or []
                except Exception:
                    fav_cands = []

            fav_rank = {name: idx for idx, name in enumerate(fav_cands)}

            def _sort_key(name: str):
                m = re.search(r"([\d.]+)\s*MB/s", name, re.IGNORECASE)
                sp = float(m.group(1)) if m else 0.0
                rank = fav_rank.get(name, 9999)
                return (-sp, rank, name)

            sorted_members = sorted(valid_members, key=_sort_key)

            # (e) 过滤掉当前处于 15 分钟熔断冷冻期的节点，若全在冷却期则保留有效成员兜底
            ready_cands = [c for c in sorted_members if (c not in self.cooldown_nodes or self.cooldown_nodes[c] <= now)]
            self.standby_cache[grp] = ready_cands or sorted_members

    def _pick_backup_node(
        self,
        target_group: str,
        exclude_node: str,
        is_non_hk: bool = False,
    ) -> Optional[str]:
        """
        以内核当前策略组的真实成员为唯一事实基准，挑选最佳顺位备选节点 (消灭 400 脱节)
        """
        now = time.time()

        # 1. 优先直接从内存热备队列中取出首个非死且真实存在的未冷冻节点 (0 毫秒开销)
        cached = self.standby_cache.get(target_group, [])
        for cand in cached:
            if is_non_hk and cand in self.google_hk_nodes and self.google_hk_nodes[cand] > now:
                continue
            if cand and cand != exclude_node and (cand not in self.cooldown_nodes or self.cooldown_nodes[cand] <= now):
                return cand

        # 2. 若热备缓存未命中，实时以内核该策略组真实成员为权威基准提取
        g_data = self.client.get_proxy(target_group, timeout=1.0)
        all_members = list(g_data.get("all", []))
        if not all_members:
            return None

        # (b) 区域合规过滤 (非港组剔除香港节点及被 Google 送中冷冻的节点)
        if is_non_hk:
            valid_members = [
                c for c in all_members
                if c and not EXCLUDE_HK_REGEX.search(c)
                and (c not in self.google_hk_nodes or self.google_hk_nodes[c] <= now)
            ]
        else:
            valid_members = [c for c in all_members if c]

        # (c) 排除当前坏死节点
        candidates = [c for c in valid_members if c != exclude_node]
        if not candidates:
            return None

        # (d) 智能排序算法：正则提取下行速度并结合 get_candidates_fn 排序
        fav_cands: List[str] = []
        if callable(self.get_candidates_fn):
            try:
                fav_cands = self.get_candidates_fn(is_non_hk=is_non_hk) or []
            except TypeError:
                fav_cands = self.get_candidates_fn() or []
            except Exception:
                fav_cands = []

        fav_rank = {name: idx for idx, name in enumerate(fav_cands)}

        def _sort_key(name: str):
            m = re.search(r"([\d.]+)\s*MB/s", name, re.IGNORECASE)
            sp = float(m.group(1)) if m else 0.0
            rank = fav_rank.get(name, 9999)
            return (-sp, rank, name)

        candidates.sort(key=_sort_key)

        # (e) 优先返回未在 15 分钟熔断冷冻期的顶级节点
        for cand in candidates:
            if cand not in self.cooldown_nodes or self.cooldown_nodes[cand] <= now:
                return cand

        # (e 兜底) 若全部处于冷却期，返回除 exclude_node 之外评分最高的有效成员兜底
        for cand in candidates:
            return cand

        return None

    def _notify_status(self):
        if callable(self.on_status_update):
            try:
                self.on_status_update(self.get_status_dict())
            except Exception:
                pass

    def diagnose_current_link(self) -> dict:
        """
        一键手动双通道链路深度诊断
        """
        g_auto = self.client.get_proxy("⚡ 自动选择", timeout=1.2)
        g_nohk = self.client.get_proxy("⚡ 自动选择 (非香港)", timeout=1.2)
        auto_now = g_auto.get("now", "")
        nohk_now = g_nohk.get("now", "")

        delay_auto = self.client.query_proxy_delay(auto_now, self.probe_url, timeout_ms=1500) if auto_now else 99999
        delay_nohk = self.client.query_proxy_delay(nohk_now, self.probe_url, timeout_ms=1500) if nohk_now else 99999

        conns_data = self.client.get_connections(timeout=2.0)
        total_conns = len(conns_data.get("connections", []))

        is_healthy = (delay_auto < 99999 and delay_nohk < 99999)
        return {
            "active_node": auto_now or "未获取到",
            "active_nohk_node": nohk_now or "未获取到",
            "delay_ms": delay_auto if delay_auto < 99999 else "超时(断流)",
            "delay_nohk_ms": delay_nohk if delay_nohk < 99999 else "超时(断流)",
            "is_healthy": is_healthy,
            "total_connections": total_conns,
            "healed_count": self.healed_count,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
```

## File: `services/c_segment_miner.py`

```python
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
```

## File: `services/clash_client.py`

```python
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

from config.settings import BASE_DIR, PARENT_DIR, THEME
from utils.win32_utils import trigger_verge_reactivate_hotkey, is_run_as_admin


class ClashClient:
    """
    Clash / Clash Verge REST API 客户端：
    封装与内核 external-controller 的 HTTP 通信、延迟检测、模式切换与装载探测。
    """

    def __init__(self, host="127.0.0.1", port=9097, secret="", base_url=None):
        if base_url:
            parsed = urllib.parse.urlparse(base_url)
            self.host = parsed.hostname or host
            self.port = parsed.port or port
        else:
            self.host = host
            self.port = int(port)
        self.secret = str(secret).strip()
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    @property
    def base_url(self):
        return f"http://{self.host}:{self.port}"

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

    def get_proxy(self, proxy_name: str, timeout: float = 1.5) -> dict:
        enc_name = urllib.parse.quote(proxy_name, safe="")
        data = self.call_api(f"/proxies/{enc_name}", timeout=timeout)
        return data if (data and isinstance(data, dict)) else {}

    def query_proxy_delay(self, proxy_name, test_url, timeout_ms=1500):
        enc_name = urllib.parse.quote(proxy_name, safe="")
        enc_url = urllib.parse.quote(test_url, safe="")
        endpoint = f"/proxies/{enc_name}/delay?timeout={timeout_ms}&url={enc_url}"
        res = self.call_api(endpoint, timeout=(timeout_ms / 1000.0) + 0.6)
        if res and isinstance(res, dict) and "delay" in res:
            return res["delay"]
        return 99999

    def get_connections(self, timeout=2.0) -> dict:
        """
        获取当前内核所有活跃 TCP / UDP 连接快照
        """
        data = self.call_api("/connections", timeout=timeout)
        return data if (data and isinstance(data, dict)) else {}

    def close_connection(self, conn_id: str, timeout=1.0) -> bool:
        """
        关闭指定连接，内核将向客户端发送 TCP RST 以迫使其瞬时重连
        """
        if not conn_id:
            return False
        res = self.call_api(f"/connections/{conn_id}", method="DELETE", timeout=timeout)
        return res is not None

    def close_connections_by_proxy(self, proxy_name: str, timeout=2.0) -> int:
        """
        外科手术式批量切断途径指定物理代理节点的所有僵尸连接
        """
        if not proxy_name:
            return 0
        conns_data = self.get_connections(timeout=timeout)
        conns = conns_data.get("connections", [])
        closed_count = 0
        for conn in conns:
            chains = conn.get("chains", [])
            # chains 格式如: ["香港 HKG 24.62 MB/s", "⚡ 自动选择", "🚀 节点选择"]
            if proxy_name in chains or (chains and chains[0] == proxy_name):
                cid = conn.get("id")
                if cid and self.close_connection(cid, timeout=0.8):
                    closed_count += 1
        return closed_count

    def switch_proxy(self, group_name: str, target_proxy_name: str, timeout=2.0) -> bool:
        """
        向策略组（Selector 或 URLTest）发送 PUT 请求，毫秒级内存热切换出口节点
        """
        if not group_name or not target_proxy_name:
            return False
        enc_group = urllib.parse.quote(group_name, safe="")
        res = self.call_api(f"/proxies/{enc_group}", method="PUT", data={"name": target_proxy_name}, timeout=timeout)
        return res is not None

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
```

## File: `services/colo_service.py`

```python
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
```

## File: `services/filter_service.py`

```python
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
```

## File: `services/pool_service.py`

```python
import copy
import re
import threading
import time


def get_pool_endpoint_sets(favorites, local_blacklist, speed_blacklist, auto_endpoints, verified_nodes, stars_nodes, get_node_endpoint_fn):
    """
    全系统统一的物理端点集合生成器：
    返回: (fav_eps, bl_eps, sbl_eps, star_eps)
    """
    fav_eps = set()
    for f in favorites:
        if f:
            ep = get_node_endpoint_fn(f)
            if ep and ep != "127.0.0.1:443":
                fav_eps.add(ep)
    for a in auto_endpoints:
        if a:
            ep = get_node_endpoint_fn(a)
            if ep and ep != "127.0.0.1:443":
                fav_eps.add(ep)
    for v in verified_nodes.values():
        ep_v = v.get("endpoint", "")
        if ep_v and ep_v != "127.0.0.1:443":
            fav_eps.add(ep_v)

    bl_eps = set()
    for b in local_blacklist:
        if not b or b.startswith("http"):
            continue
        ep = get_node_endpoint_fn(b)
        if ep and ep != "127.0.0.1:443":
            bl_eps.add(ep)

    sbl_eps = set()
    for s in speed_blacklist:
        if not s or s.startswith("http"):
            continue
        ep = get_node_endpoint_fn(s)
        if ep and ep != "127.0.0.1:443":
            sbl_eps.add(ep)

    star_eps = {
        st.get("endpoint", "") for st in stars_nodes
        if isinstance(st, dict) and st.get("endpoint")
    }

    return fav_eps, bl_eps, sbl_eps, star_eps


def deduplicate_favorites_by_endpoint(favorites, all_nodes, node_details, get_node_endpoint_fn, choose_canonical_node_name_fn):
    """
    物理端点 1:1 严格唯一归一化合并：
    对 favorites 中共享相同 IP:Port 的冗余马甲节点进行智能聚合，只保留最高权重代表。
    返回: (deduped_favorites: set, merged_count: int)
    """
    ep_map = {}
    non_ep_nodes = []

    for n in list(favorites):
        ep = get_node_endpoint_fn(n)
        if ep:
            ep_map.setdefault(ep, []).append(n)
        else:
            non_ep_nodes.append(n)

    new_favs = set(non_ep_nodes)
    merged_count = 0

    for ep, name_list in ep_map.items():
        if len(name_list) > 1:
            merged_count += len(name_list) - 1
            canonical = choose_canonical_node_name_fn(name_list)
            new_favs.add(canonical)
        elif name_list:
            new_favs.add(name_list[0])

    favorites.clear()
    favorites.update(new_favs)
    return favorites, merged_count


def align_favorites_with_current_subscription(favorites, all_nodes, resolve_node_to_current_fn):
    """
    智能将历史精选池中因订阅更名（如测速后缀变化）的节点映射迁移到当前订阅中真实存在的节点名称。
    返回: (migrated_count: int)
    """
    if not all_nodes or not favorites:
        return 0

    migrated_count = 0
    updated_favs = set()

    for fav in list(favorites):
        if fav in all_nodes:
            updated_favs.add(fav)
        else:
            resolved = resolve_node_to_current_fn(fav)
            if resolved and resolved in all_nodes:
                updated_favs.add(resolved)
                migrated_count += 1
            else:
                updated_favs.add(fav)

    favorites.clear()
    favorites.update(updated_favs)
    return migrated_count


def clean_offline_favorites(favorites, all_nodes, local_blacklist, speed_blacklist, get_node_endpoint_fn):
    """
    精选池健康度审计：
    清除已被拉黑的节点。
    返回: (purged_count: int)
    """
    purged_count = 0
    for n in list(favorites):
        ep = get_node_endpoint_fn(n)
        if n in local_blacklist or n in speed_blacklist or (ep and (ep in local_blacklist or ep in speed_blacklist)):
            favorites.discard(n)
            purged_count += 1
    return purged_count


def process_verified_lifecycle(verified_nodes, current_favs, stars_nodes, incubate_hours=24, incubate_passes=5):
    """
    处理 7 天沉淀池的生命周期状态流转。
    确保写入 verified_nodes[ep] 时，键与 item["endpoint"] 必须为规范的纯 IP:Port 字符串，
    严禁将原机场主的长字符串直接作为键，彻底杜绝表格第一列错位显示原名的问题。
    """
    now = time.time()

    # 1. 深度清洗历史遗留的不规范脏键，杜绝机场名作为 Key
    for k in list(verified_nodes.keys()):
        clean_k = str(k).strip()
        if "#" in clean_k:
            clean_k = clean_k.split("#")[0].strip()
        pure_ep = None
        if re.match(r"^[\w\.\-]+\:\d+$", clean_k):
            pure_ep = clean_k
        else:
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", clean_k)
            if m:
                pure_ep = m.group(1)

        if pure_ep:
            if pure_ep != k:
                val = verified_nodes.pop(k)
                val["endpoint"] = pure_ep
                if pure_ep not in verified_nodes:
                    verified_nodes[pure_ep] = val
            else:
                verified_nodes[k]["endpoint"] = pure_ep
        else:
            verified_nodes.pop(k, None)

    # 2. 规范化登记与考核达标存活端点
    for fav in current_favs:
        if not fav:
            continue
        clean_str = str(fav).strip()
        if "#" in clean_str:
            clean_str = clean_str.split("#")[0].strip()

        ep = None
        if re.match(r"^[\w\.\-]+\:\d+$", clean_str):
            ep = clean_str
        else:
            m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3}:\d{1,5})", clean_str)
            if m:
                ep = m.group(1)

        if not ep or ep == "127.0.0.1:443":
            continue

        if ep not in verified_nodes:
            verified_nodes[ep] = {
                "endpoint": ep,
                "first_seen": now,
                "last_seen": now,
                "pass_count": 1,
                "passes": 1,
                "fails": 0,
                "status": "incubating",
            }
        else:
            v = verified_nodes[ep]
            v["endpoint"] = ep
            v["last_seen"] = now
            cur_passes = v.get("passes", v.get("pass_count", 0)) + 1
            v["passes"] = cur_passes
            v["pass_count"] = cur_passes
            hours_alive = (now - v.get("first_seen", now)) / 3600.0
            if hours_alive >= incubate_hours and cur_passes >= incubate_passes:
                v["status"] = "verified"


def purge_invalid_and_blacklisted_from_all_pools(favorites, verified_nodes, stars_nodes, local_blacklist, speed_blacklist, get_node_endpoint_fn):
    """
    全域清洗过滤：从优质精选池、沉淀孵化池、典藏常青池中彻底清除落入延迟/低速黑名单的节点。
    返回: (purged_favs: int, purged_verified: int, purged_stars: int)
    """
    p_favs = 0
    p_ver = 0
    p_star = 0

    all_bl = local_blacklist | speed_blacklist

    for f in list(favorites):
        ep = get_node_endpoint_fn(f)
        if f in all_bl or (ep and ep in all_bl):
            favorites.discard(f)
            p_favs += 1

    for k in list(verified_nodes.keys()):
        ep = verified_nodes[k].get("endpoint", "")
        if k in all_bl or (ep and ep in all_bl):
            del verified_nodes[k]
            p_ver += 1

    initial_stars_len = len(stars_nodes)
    stars_nodes[:] = [
        item for item in stars_nodes
        if not (
            item.get("matched_name", "") in all_bl
            or item.get("endpoint", "") in all_bl
        )
    ]
    p_star = initial_stars_len - len(stars_nodes)

    return p_favs, p_ver, p_star


class PoolService:
    """
    多池节点流转服务 (单例模式)
    负责管理 活跃、精选、黑名单、典藏 等多个节点池的原子性流转
    """
    _instance = None
    _init_lock = threading.Lock()

    def __new__(cls):
        with cls._init_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._init_service()
            return cls._instance

    def _init_service(self):
        self._pool_lock = threading.RLock()
        self._pools = {
            "active": [],
            "favorites": [],
            "delay_black": [],
            "speed_black": [],
            "stars": []
        }

    def get_pool_data(self, pool_name: str) -> list:
        with self._pool_lock:
            if pool_name not in self._pools:
                return []
            return copy.deepcopy(self._pools[pool_name])

    def set_pool_data(self, pool_name: str, nodes: list):
        with self._pool_lock:
            if pool_name in self._pools:
                self._pools[pool_name] = copy.deepcopy(nodes)

    def add_to_pool(self, pool_name: str, node: dict):
        with self._pool_lock:
            if pool_name in self._pools:
                for existing_node in self._pools[pool_name]:
                    if existing_node.get("name") == node.get("name"):
                        return
                self._pools[pool_name].append(copy.deepcopy(node))

    def atomic_transfer(self, node: dict, from_pool_name: str, to_pool_name: str) -> bool:
        with self._pool_lock:
            if from_pool_name not in self._pools or to_pool_name not in self._pools:
                return False

            snapshot_from = copy.deepcopy(self._pools[from_pool_name])
            snapshot_to = copy.deepcopy(self._pools[to_pool_name])

            try:
                node_name = node.get("name")
                if not node_name:
                    raise ValueError("节点缺少 name 唯一标识")

                found_index = -1
                for idx, n in enumerate(self._pools[from_pool_name]):
                    if n.get("name") == node_name:
                        found_index = idx
                        break

                if found_index == -1:
                    return False

                popped_node = self._pools[from_pool_name].pop(found_index)
                existing_names = {n.get("name") for n in self._pools[to_pool_name]}
                if popped_node.get("name") not in existing_names:
                    self._pools[to_pool_name].append(popped_node)

                return True

            except Exception:
                self._pools[from_pool_name] = snapshot_from
                self._pools[to_pool_name] = snapshot_to
                return False

    def atomic_batch_transfer(self, nodes: list, from_pool_name: str, to_pool_name: str) -> bool:
        if not nodes:
            return True

        with self._pool_lock:
            if from_pool_name not in self._pools or to_pool_name not in self._pools:
                return False

            snapshot_from = copy.deepcopy(self._pools[from_pool_name])
            snapshot_to = copy.deepcopy(self._pools[to_pool_name])

            try:
                node_names_to_transfer = {n.get("name") for n in nodes if n.get("name")}
                remaining_nodes = [
                    n for n in self._pools[from_pool_name]
                    if n.get("name") not in node_names_to_transfer
                ]
                self._pools[from_pool_name] = remaining_nodes

                existing_to_names = {n.get("name") for n in self._pools[to_pool_name]}
                for n in nodes:
                    if n.get("name") and n.get("name") not in existing_to_names:
                        self._pools[to_pool_name].append(copy.deepcopy(n))
                        existing_to_names.add(n.get("name"))

                return True

            except Exception:
                self._pools[from_pool_name] = snapshot_from
                self._pools[to_pool_name] = snapshot_to
                return False
```

## File: `services/probe_service.py`

```python
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
```

## File: `services/script_generator.py`

```python
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


```

## File: `services/subscription_service.py`

```python
import gzip
import hashlib
import os
import re
import ssl
import threading
import time
import urllib.parse
import urllib.request

from config.settings import PARENT_DIR


def extract_nodes_and_details_from_file(filepath):
    nodes = []
    details = {}
    if not os.path.exists(filepath):
        return nodes, details
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        inline_matches = re.findall(r"-\s*\{([^}]+)\}", content)
        for item in inline_matches:
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
    if not node_list:
        return ""
    if len(node_list) == 1:
        return node_list[0]

    def _canonical_score(name):
        score = 0
        if re.search(r"\d+(?:\.\d+)?\s*(?:ms|mb/s|kb/s)", str(name), re.IGNORECASE):
            score += 60
        if any(k in str(name) for k in ["优选", "高速", "精品", "专线", "PRO", "VIP"]):
            score += 30
        if any(k in str(name) for k in ["香港", "HK", "台湾", "TW", "日本", "JP", "韩国", "KR", "新加坡", "SG"]):
            score += 20
        clean_n = str(name).strip()
        if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}(?::\d+)?$", clean_n):
            score -= 30
        if "auto" in str(name).lower() or "保活" in str(name):
            score -= 10
        return score

    return max(node_list, key=_canonical_score)


def get_node_endpoint(node_name, node_details=None, all_nodes=None, verified_nodes=None, clash_client=None):
    if not node_name:
        return ""

    node_name_clean = str(node_name).strip()
    if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}$", node_name_clean):
        return node_name_clean

    if "#" in node_name_clean:
        prefix = node_name_clean.split("#", 1)[0].strip()
        m_pre = re.match(r"^(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})$", prefix)
        if m_pre:
            return f"{m_pre.group(1)}:{m_pre.group(2)}"

    if node_details and isinstance(node_details, dict):
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

    if verified_nodes and isinstance(verified_nodes, dict) and node_name in verified_nodes:
        v_ep = verified_nodes[node_name].get("endpoint", "")
        if v_ep:
            return v_ep

    if all_nodes and node_name in all_nodes and clash_client is not None:
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


def resolve_node_to_current(target_key, all_nodes=None, node_details=None):
    if not target_key:
        return None
    if all_nodes and target_key in all_nodes:
        return target_key

    target_ep = ""
    if node_details:
        info = node_details.get(target_key, {})
        s = info.get("server", "").strip()
        p = str(info.get("port", "443")).strip()
        if s:
            target_ep = f"{s}:{p}"

    if not target_ep:
        if ":" in str(target_key) and re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}$", str(target_key).strip()):
            target_ep = str(target_key).strip()
        elif "#" in str(target_key):
            prefix = str(target_key).split("#", 1)[0].strip()
            if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:(?:\d{1,5})$", prefix):
                target_ep = prefix

    if target_ep and ":" in target_ep and all_nodes and node_details:
        target_ip, target_port = target_ep.split(":", 1)
        for n in all_nodes:
            n_info = node_details.get(n, {})
            if n_info.get("server", "").strip() == target_ip and str(n_info.get("port", "443")).strip() == target_port:
                return n
        for n in all_nodes:
            n_info = node_details.get(n, {})
            if n_info.get("server", "").strip() == target_ip:
                return n

    m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})(?::(\d{2,5}))?", str(target_key))
    if m and all_nodes and node_details:
        raw_ip = m.group(1)
        raw_port = m.group(2) if m.group(2) else "443"
        for n in all_nodes:
            n_info = node_details.get(n, {})
            if n_info.get("server", "").strip() == raw_ip and str(n_info.get("port", "443")).strip() == raw_port:
                return n
        for n in all_nodes:
            n_info = node_details.get(n, {})
            if n_info.get("server", "").strip() == raw_ip:
                return n

    return None


def update_remote_subscription(target_yaml_path, mixed_port=7897, on_step_callback=None):
    fname = os.path.basename(target_yaml_path)
    file_stem = os.path.splitext(fname)[0]

    profiles_yaml = os.path.join(PARENT_DIR, "profiles.yaml")
    if not os.path.exists(profiles_yaml):
        return False, "未找到 profiles.yaml 配置文件", False

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
        return False, f"读取 profiles.yaml 出错: {ex}", False

    if not sub_url or not sub_url.startswith("http"):
        return False, f"在 profiles.yaml 中未定位到【{fname}】的有效远程 URL", False

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
            channel_name = f"代理端口:{mixed_port}" if use_proxy else "本地直连"
            try:
                if on_step_callback:
                    on_step_callback(f"同步最新订阅 (第 {attempt}/3 次尝试 - {channel_name})...")

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
                        content_changed = (new_md5 != old_md5)

                        if content_changed:
                            with open(target_yaml_path, "wb") as f:
                                f.write(data)
                            return True, f"成功同步订阅【{sub_name or fname}】(内容已变动)", True
                        else:
                            return True, f"成功拉取订阅【{sub_name or fname}】(内容与本地一致，MD5未变)", False
                    else:
                        last_error = "拉取到的内容非合法 Clash YAML"
            except Exception as ex:
                last_error = f"{type(ex).__name__}: {str(ex)}"
                continue

    return False, last_error, False


class SubscriptionService:
    def __init__(self):
        self.timeout = 10.0

    def fetch_subscription(self, url, retries=3):
        import requests
        from requests.exceptions import RequestException
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
            except RequestException as e:
                time.sleep(2.0 * (attempt + 1))
        return ""

    def update_all_subscriptions(self, urls):
        results = {}
        for url in urls:
            results[url] = self.fetch_subscription(url)
        return results


```

## File: `utils/__init__.py`

```python
"""
Clash Verge 节点管理助手 - 工具包
"""
```

## File: `utils/win32_utils.py`

```python
import ctypes
import os
import subprocess
import sys
import time
import tkinter as tk
import winreg
import winsound

try:
    from PIL import Image, ImageDraw
    TRAY_IMAGE_SUPPORTED = True
except ImportError:
    TRAY_IMAGE_SUPPORTED = False

from config.settings import RUN_REG_KEY, REG_APP_NAME, THEME


def send_system_notification(title, message):
    """
    发送 Windows 系统级 Toast 通知并附带系统提示音
    """
    try:
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        pass

    t_clean = title.replace("'", "''").replace('"', "")
    m_clean = message.replace("'", "''").replace('"', "")
    ps_script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
        "$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
        "$toastXml = [xml]$template.GetXml(); "
        f"$toastXml.GetElementsByTagName('text')[0].AppendChild($toastXml.CreateTextNode('{t_clean}')) > $null; "
        f"$toastXml.GetElementsByTagName('text')[1].AppendChild($toastXml.CreateTextNode('{m_clean}')) > $null; "
        "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument; "
        "$xml.LoadXml($toastXml.OuterXml); "
        "$toast = [Windows.UI.Notifications.ToastNotification]::new($xml); "
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Clash Verge 节点助手').Show($toast);"
    )
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            creationflags=0x08000000,
        )
    except Exception:
        pass


def is_run_as_admin():
    """
    检测当前进程是否具备 Windows 管理员提权权限
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def trigger_verge_reactivate_hotkey():
    """
    模拟系统级全局组合热键 (Ctrl + Shift + F12) 通知 Clash Verge 重新激活装载规则
    """
    user32 = ctypes.windll.user32
    VK_CONTROL = 0x11
    VK_SHIFT = 0x10
    VK_F12 = 0x7B
    KEYEVENTF_KEYUP = 0x0002

    try:
        # 释放潜在的物理按键粘滞状态
        for vk in [VK_CONTROL, VK_SHIFT, VK_F12]:
            user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)

        # 模拟按下组合键
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(VK_SHIFT, 0, 0, 0)
        user32.keybd_event(VK_F12, 0, 0, 0)
        time.sleep(0.15)  # 保持 150ms 确保被系统级热键总线捕获

        # 模拟释放组合键
        user32.keybd_event(VK_F12, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        return True, ""
    except Exception as e:
        return False, str(e)


def create_tray_icon_image():
    """
    动态生成 64x64 现代蓝色渐变系统托盘矢量图标
    """
    if not TRAY_IMAGE_SUPPORTED:
        return None
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, 60, 60), fill="#2563eb", outline="#38bdf8", width=3)
    draw.polygon([(34, 12), (22, 34), (32, 34), (30, 52), (42, 30), (32, 30)], fill="#ffffff")
    return img


def check_boot_startup_registry():
    """
    检查注册表自启项
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_KEY, 0, winreg.KEY_READ)
        _, _ = winreg.QueryValueEx(key, REG_APP_NAME)
        winreg.CloseKey(key)
        return True
    except WindowsError:
        return False


def set_boot_startup_registry(enable=True):
    """
    开启或关闭 Windows 开机自启（写入当前用户注册表）
    """
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_KEY, 0, winreg.KEY_SET_VALUE)
        if enable:
            python_exe = sys.executable
            pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw_exe):
                pythonw_exe = python_exe
            script_path = os.path.abspath(sys.argv[0])
            cmd_val = f'"{pythonw_exe}" "{script_path}" --tray'
            winreg.SetValueEx(key, REG_APP_NAME, 0, winreg.REG_SZ, cmd_val)
        else:
            try:
                winreg.DeleteValue(key, REG_APP_NAME)
            except WindowsError:
                pass
        winreg.CloseKey(key)
        return True, ""
    except Exception as e:
        return False, str(e)


def create_modern_btn(parent, text, command, bg, fg="#ffffff", hover_bg=None, font_size=9, **kwargs):
    """
    创建现代化扁平样式按钮，内置鼠标滑过悬停变色动效
    """
    if hover_bg is None:
        hover_bg = THEME["bg_hover"]

    padx = kwargs.pop("padx", 12)
    pady = kwargs.pop("pady", 6)

    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        activebackground=hover_bg,
        activeforeground=fg,
        relief="flat",
        bd=0,
        padx=padx,
        pady=pady,
        cursor="hand2",
        font=("Microsoft YaHei UI", font_size, "bold"),
        **kwargs,
    )

    def on_enter(e):
        if btn["state"] != "disabled":
            btn.config(bg=hover_bg)

    def on_leave(e):
        if btn["state"] != "disabled":
            btn.config(bg=bg)

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    return btn
```

