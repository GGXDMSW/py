import os

def is_ignored(path):
    ignored_dirs = {'.git', '__pycache__', '.idea', '.vscode', 'venv', 'env', 'node_modules', 'dist', 'build', 'gui', 'scratch'}
    ignored_exts = {'.pyc', '.pyd', '.exe', '.dll', '.so', '.dylib', '.png', '.jpg', '.jpeg', '.gif', '.zip', '.tar', '.gz', '.ico', '.pdf', '.bak', '.json', '.txt', '.log'}
    
    parts = path.split(os.sep)
    if any(part in ignored_dirs for part in parts):
        return True
        
    ext = os.path.splitext(path)[1].lower()
    if ext in ignored_exts:
        return True
        
    if os.path.basename(path) == 'repo_context.md':
        return True
        
    return False

GOD_VIEW_MAP = """# 🌌 反重力平台 py 项目「绝对上帝视角」架构总图 (God-View Architecture Map)

> **致下一任 AI 架构师**：
> 本文件是本项目的最高级别系统全景认知枢纽。请务必优先精读本章节，它将赋予你对整个代码库拓扑链路、并发锁分布、状态生命周期与不可违背的底层红线 **100% 的掌控权**。阅读完毕后即可达到零损耗接手、精准决策与系统级架构治理。

---

## 一、 全局拓扑链路与模块调用流向

本系统是一套专为 **Clash Verge Rev** 量身打造的高性能、自动化节点优选、全链路状态守护与秒级无感自愈中枢。整体遵循 **分层解耦、单向依赖、Controller中枢编排、双引擎热重载** 的企业级工程架构。

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

### 关键数据与指令流向：
1. **启动与状态恢复**：`main_fluent.py` 实例化 `AppController` -> `AppController` 从 `config_manager` 安全加载 `node_assistant_config.json` 注入 `StateManager` -> 初始化 UI 并启动后台守护线程。
2. **全量大优选流程**：`auto_pipeline.py` 从云端/本地拉取订阅 -> 并发调用 `subscription_service` 提取去重物理端点 -> 调用 `colo_service` 嗅探真实机房代码 (HKG, NRT 等) -> 过滤漂移节点 -> 调用 `probe_service` 进行真实文件下行带宽测速 -> 将达标节点冠名（如 `香港 HKG 22.56 MB/s`）入驻精选池与 `cloud_endpoints` 字典 -> 调用 `script_generator` 生成 `Script.js` 并执行双引擎内核热重载。
3. **秒级无感自愈流程**：`auto_heal_watcher.py` 后台 1.0s 旁路轮询 Mihomo `/connections` 连接表 -> 发现单向发包黑洞或软失速 -> 外科手术式 `DELETE /connections/{id}` 断开坏死连接 -> 在策略组内无感秒级顺位切换至健康低延迟节点（严格隔离非香港与香港池）-> 坏死节点临时熔断冷冻 15 分钟。

---

## 二、 状态与并发生命周期 (State & Concurrency Lifecycle)

### 1. StateManager 核心数据结构
`core/state_manager.py` 中的 `StateManager` 是整个应用的唯一事实源 (Single Source of Truth)：
- `favorites`: `set[str]` - 优质精选节点名称集合。
- `stars_nodes`: `list[dict]` - 典藏常青极品池清单。
- `all_nodes`: `list[str]` - 订阅中的物理端点去重全量节点名称列表。
- `node_details`: `dict[str, dict]` - 节点详情映射（包含 `server`, `port`, `type`, `uuid` 等原始物理参数）。
- `cloud_endpoints`: `dict[str, str]` - 物理端点 (`IP:Port`) -> 规范化名称（如 `"23.133.52.10:2053": "香港 HKG 22.56 MB/s"`），拥有最高霸占优先级。
- `node_colo`: `dict[str, str]` - 端点/节点 -> 物理机房代码（如 `"HKG"`, `"NRT"`）。
- `node_colo_history`: `dict[str, list]` - 7 天机房历史检测记录，用于长效防漂移。
- `local_blacklist` & `speed_blacklist`: `set[str]` - 延迟超标与下行低速黑名单集合。

### 2. 并发模型与锁 (Lock) 分布规则
系统涉及多个并发执行上下文：
- **GUI 主线程**：运行 PyQt6 响应式事件循环，负责所有界面交互与渲染。
- **Pipeline 工作线程**：`AutoPipeline` (QThread)、`FavPipeline` (QThread)，负责长时间测速与优选计算。
- **Sentinel 哨兵线程**：`AutoHealWatcher` (threading.Thread)，常驻后台进行毫秒级链路感知。
- **定时调度线程**：`Scheduler` (threading.Thread)，处理定时自动优选。

#### ⚠️ 死锁防范与锁粒度黄金军规：
1. **统一锁接口**：`StateManager` 内置私有递归互斥锁 `_global_lock`，对外通过 `@property def lock(self): return self._global_lock` 暴露。所有线程必须统一通过 `with self.state.lock:` 或 `with self.controller.state.lock:` 获取锁。
2. **锁内严禁同步阻塞 I/O**：绝对禁止在持有 `state.lock` 时调用网络请求（如 `requests.get`、下行测速、`time.sleep`）或弹出 GUI 阻塞对话框（如 `QMessageBox.exec()`）。
3. **快照分离模式 (Snapshot Pattern)**：
   ```python
   # 正确范式：锁内快照，锁外耗时操作
   with self.state.lock:
       fav_snapshot = set(self.state.favorites)
       details_snapshot = dict(self.state.node_details)
   
   # 锁外执行耗时网络测速
   results = perform_speed_tests(fav_snapshot, details_snapshot)
   
   # 结果回写再短暂入锁
   with self.state.lock:
       self.state.favorites.update(results.qualified)
   ```
4. **协作式优雅终止 (Stop Event)**：严禁使用 `terminate()` 或系统级暴力杀线程。统一调用 `self.state.get_stop_event(name)` 获取 `threading.Event`，流水线循环内检测 `if stop_event.is_set(): break` 实现安全收尾与状态自愈。

---

## 三、 模块边界与底层契约 (Architecture Red Lines & Contracts)

### 1. 目录依赖架构红线（绝对不可逾越）
- **红线 1（严格单向分层，严禁反向污染）**：
  `services` 和 `config` 属于纯粹的基础设施与算法层，**绝对严禁导入任何 GUI 模块**（无论是 `gui` 还是 `gui_fluent`）。基础模块必须能够在无任何 UI 的 Headless 环境下独立进行单元测试。
- **红线 2（View-Controller 严格隔离）**：
  所有界面层组件（`pages/`、`widgets/`、`components/`）只负责数据渲染与事件触发，**绝对严禁直接调用底层 `services` 或直接执行文件写盘**。所有业务操作必须通过委托 `self.controller.<method>()` 执行。
- **红线 3（物理机房级绝对防御契约）**：
  对非香港策略组（`⚡ 自动选择 (非香港)`）的过滤，**绝不允许仅依赖节点名称字符串正则**！必须将由 Python 端嗅探到的物理香港机房端点黑名单（`hkEndpoints`）注入脚本，在物理端点层实施一票否决。
- **红线 4（规范命名唯一霸占契约）**：
  由系统冠名并收录于 `cloud_endpoints` 的规范名称（如 `香港 HKG 22.56 MB/s`），在全局任何订阅解析（`load_nodes_from_profile`）与状态对齐（`reconcile_endpoints`）中**具备最高霸占优先级**，严禁逆向降级还原回机场原始未清洗的广告名称。

### 2. 系统核心设计模式
- **Controller 协调器模式**：`gui_fluent/app_controller.py` 作为全系统总调度中枢，统一协调状态持久化、UI 信号转发、流水线启停与内核重载。
- **Pipeline 管道模式**：`auto_pipeline.py` 与 `fav_pipeline.py` 将复杂的测活、测速、校准、入池与热载步骤分解为标准管道阶段。
- **Observer 观察者模式**：通过 `SignalBus` 与 PyQt6 Signals 实现后台任务进度、日志、状态向界面的解耦通知。
- **Sentinel 哨兵自愈模式**：`auto_heal_watcher.py` 以后台旁路方式进行零流量损耗的真实连接感知与断流自愈。
- **Dual-Engine 双引擎热更模式**：`Script.js`（动态规则注入） + `clash-verge.yaml`（原子覆盖并通知 API 热重载），彻底攻克快捷键穿透失败的边界场景。

---

## 四、 近期关键排雷与核心修复纪要 (Critical Bug Post-Mortems)

### 1. StateManager 缺少 lock 属性导致多线程崩溃闪退
- **事故现象**：在 Fluent 界面下启动大优选或复测时，程序瞬间崩溃闪退。
- **底层根因**：`StateManager` 原本私有锁命名为 `_global_lock`，但在模块化重构时，Controller 和各 Pipeline 广泛采用了 `with self.state.lock:`。当多线程并发执行时，直接抛出 `AttributeError: 'StateManager' object has no attribute 'lock'`，未捕获异常导致 Python 进程直接退出。
- **解决方案**：在 `core/state_manager.py` 中为 `StateManager` 添加 `@property def lock(self): return self._global_lock`，确保所有多线程上下文安全、平滑地获得线程锁保护。

### 2. 香港节点因机场广告名伪装穿透「⚡ 自动选择 (非香港)」策略组
- **事故现象**：全量大优选后，用户发现非香港组首位赫然排着 `Mia优选 | 09-12 19:32 | BestCF.pages.dev`，不仅没改名，而且物理机房实际为香港 HKG。
- **底层根因**：
  1. `Script.js` 中的 `isNonHongKongProxy` 纯粹依赖名称正则 `/(香港|HK|Hong\\s*Kong)/i`，而机场原始名字脱敏不带任何地区词，导致正则一票否决失效；
  2. 生成 `Script.js` 时未在 `config.proxies` 内存中覆盖 `p.name`；
  3. `reconcile_endpoints` 在对齐时把已命名的 `香港 HKG 22.56 MB/s` 反向还原为了原始订阅中的怪名字。
- **解决方案**：
  1. **物理端点黑名单硬核拦截**：在 `services/script_generator.py` 中聚合已知香港端点注入 `hkEndpoints`（收录 808 个端点），在 `isNonHongKongProxy` 中实施物理端点 `hkEndpoints.includes(ep)` 一票否决；
  2. **内存规范更名注入**：在 `Script.js` 步骤 0 中引入 `canonicalNameMap`，遍历 `config.proxies` 时自动将其覆盖更名为规范名称（如 `香港 HKG 22.56 MB/s`）；
  3. **消除反向降级**：修复 `reconcile_endpoints`，锁定 `cloud_endpoints` 规范命名优先权。

### 3. YouTube Shorts 播放中途短暂断流转圈（DNS Fake-IP 与流媒体加固）
- **事故现象**：播放 YouTube 视频时前几秒秒开，随后第 10 秒发生几秒卡顿转圈才继续复播。
- **底层根因**：Clash Verge 的 DNS 缺少 `enhanced-mode: fake-ip`，且 `fallback-filter` 缺少 `googlevideo.com` 等流媒体 CDN 域名，导致国内公共 DNS 解析分片域名时遭受 GFW 投毒返回 Facebook 虚假 IP（HTTP 404），引发播放器卡顿重试。
- **解决方案**：在 `services/script_generator.py` 的脚本模板与 `sync_runtime_clash_yaml_and_reload` 中固化 `enhanced-mode: fake-ip` 与完整流媒体白名单，实现 0 毫秒虚拟 IP 极速下发，彻底免疫 DNS 污染。

---

## 五、 全局源码全量打包索引 (Source Manifest)
以下为当前代码库中所有非忽略源码文件的完整内容（未做任何截断），供全局审阅与深度代码级追踪：

"""

def pack_repo():
    output_file = 'repo_context.md'
    
    with open(output_file, 'w', encoding='utf-8') as out_f:
        # 写入上帝视角大地图
        out_f.write(GOD_VIEW_MAP)
        out_f.write("\n\n")
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d))]
            
            for file in sorted(files):
                file_path = os.path.join(root, file)
                if is_ignored(file_path):
                    continue
                    
                display_path = os.path.normpath(file_path).replace('\\', '/')
                if display_path.startswith('./'):
                    display_path = display_path[2:]
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as in_f:
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
                except Exception as e:
                    out_f.write(f"## File: `{display_path}`\n\n")
                    out_f.write(f"> Error reading file: {str(e)}\n\n")

if __name__ == '__main__':
    print("Packing repository with God-View Architecture Map into repo_context.md...")
    pack_repo()
    print("Done! repo_context.md is now fully updated with God-View Architecture Map.")


