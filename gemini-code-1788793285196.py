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
