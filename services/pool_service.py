import threading
import copy

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
        # 全局池操作互斥锁，允许重入
        self._pool_lock = threading.RLock()
        
        # 初始化多池存储
        self._pools = {
            "active": [],
            "favorites": [],
            "delay_black": [],
            "speed_black": [],
            "stars": []
        }

    def get_pool_data(self, pool_name: str) -> list:
        """安全获取池内数据副本，防止外部直接引用修改污染内存"""
        with self._pool_lock:
            if pool_name not in self._pools:
                return []
            return copy.deepcopy(self._pools[pool_name])

    def set_pool_data(self, pool_name: str, nodes: list):
        """安全覆盖池数据"""
        with self._pool_lock:
            if pool_name in self._pools:
                self._pools[pool_name] = copy.deepcopy(nodes)

    def add_to_pool(self, pool_name: str, node: dict):
        with self._pool_lock:
            if pool_name in self._pools:
                # 防止重复添加
                for existing_node in self._pools[pool_name]:
                    if existing_node.get("name") == node.get("name"):
                        return
                self._pools[pool_name].append(copy.deepcopy(node))

    def atomic_transfer(self, node: dict, from_pool_name: str, to_pool_name: str) -> bool:
        """
        核心逻辑：原子化单节点流转
        利用深拷贝备份状态，发生任何异常直接整体回滚，杜绝“数据彻底蒸发”或“重复残留”
        """
        with self._pool_lock:
            if from_pool_name not in self._pools or to_pool_name not in self._pools:
                print("流转失败：目标或源数据池不存在")
                return False

            # 记录操作前状态（事务快照）
            snapshot_from = copy.deepcopy(self._pools[from_pool_name])
            snapshot_to = copy.deepcopy(self._pools[to_pool_name])

            try:
                node_name = node.get("name")
                if not node_name:
                    raise ValueError("节点缺少 name 唯一标识")

                # 定位并在源池中剔除
                found_index = -1
                for idx, n in enumerate(self._pools[from_pool_name]):
                    if n.get("name") == node_name:
                        found_index = idx
                        break
                
                if found_index == -1:
                    print(f"流转警告：节点 {node_name} 不在 {from_pool_name} 池中")
                    return False

                # 弹出节点
                popped_node = self._pools[from_pool_name].pop(found_index)
                
                # 压入目标池 (去重保护)
                existing_names = {n.get("name") for n in self._pools[to_pool_name]}
                if popped_node.get("name") not in existing_names:
                    self._pools[to_pool_name].append(popped_node)
                
                return True

            except Exception as e:
                # 异常拦截与事务回滚
                print(f"原子流转遭遇异常，触发数据回滚，保护内存一致性: {e}")
                self._pools[from_pool_name] = snapshot_from
                self._pools[to_pool_name] = snapshot_to
                return False

    def atomic_batch_transfer(self, nodes: list, from_pool_name: str, to_pool_name: str) -> bool:
        """
        核心逻辑：原子化批量节点流转
        确保集合操作的完整事务性
        """
        if not nodes:
            return True

        with self._pool_lock:
            if from_pool_name not in self._pools or to_pool_name not in self._pools:
                return False

            # 记录操作前状态（事务快照）
            snapshot_from = copy.deepcopy(self._pools[from_pool_name])
            snapshot_to = copy.deepcopy(self._pools[to_pool_name])

            try:
                node_names_to_transfer = {n.get("name") for n in nodes if n.get("name")}
                
                # 在源池中剔除待转移节点
                remaining_nodes = [
                    n for n in self._pools[from_pool_name] 
                    if n.get("name") not in node_names_to_transfer
                ]
                self._pools[from_pool_name] = remaining_nodes

                # 过滤重名节点并加入目标池
                existing_to_names = {n.get("name") for n in self._pools[to_pool_name]}
                for n in nodes:
                    if n.get("name") and n.get("name") not in existing_to_names:
                        self._pools[to_pool_name].append(copy.deepcopy(n))
                        existing_to_names.add(n.get("name"))

                return True

            except Exception as e:
                # 异常拦截与事务回滚
                print(f"批量原子流转遭遇异常，触发数据回滚，保护内存一致性: {e}")
                self._pools[from_pool_name] = snapshot_from
                self._pools[to_pool_name] = snapshot_to
                return False
