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
