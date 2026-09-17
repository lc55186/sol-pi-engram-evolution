"""
阶段 3：价值评估模块
评估节点价值，指导压缩、检索、淘汰策略
"""

import importlib.util
import os
from datetime import datetime

# 动态导入 graph_store
_gs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_store.py")
_gs_spec = importlib.util.spec_from_file_location("graph_store", _gs_path)
_gs_mod = importlib.util.module_from_spec(_gs_spec)
_gs_spec.loader.exec_module(_gs_mod)
GraphStore = _gs_mod.GraphStore


class ValueEvaluator:
    """价值评估器"""

    def __init__(self, store: GraphStore, config: dict = None):
        self.store = store
        self.config = config or {}
        # 时间衰减半衰期（天）
        self.decay_half_life_days = self.config.get('decay_half_life_days', 30)
        # 可注入当前时间用于测试（优先 config，其次环境变量 TEST_NOW）
        _now = self.config.get('now')
        if _now is None:
            _now_str = os.environ.get('TEST_NOW')
            if _now_str:
                try:
                    _now = datetime.fromisoformat(_now_str)
                except (ValueError, TypeError):
                    _now = None
        self._now = _now

    def evaluate(self, node: dict) -> float:
        """评估单个节点的价值，返回 importance_score ∈ [0, 1]"""
        if not node:
            return 0.0

        # 1. 访问频率得分 (0-0.3)
        access_score = self._access_frequency_score(node)

        # 2. 时间衰减因子 (0-1.0)
        time_decay = self._time_decay_factor(node)

        # 3. 关联密度得分 (0-0.3)
        density_score = self._relation_density_score(node)

        # 4. 关键类型加权 (0-0.1)
        type_weight = self._critical_type_weight(node)

        # 基础分数
        base_score = node.get('importance_score', 0.5)

        # 加权组合
        raw_score = (
            base_score * 0.3 +
            access_score * 0.3 +
            density_score * 0.2 +
            type_weight * 0.1 +
            0.1  # 保底
        )

        # 应用时间衰减
        final_score = raw_score * time_decay

        return max(0.0, min(1.0, final_score))

    def _access_frequency_score(self, node: dict) -> float:
        """访问频率得分"""
        count = node.get('access_count', 0)
        if count <= 0:
            return 0.0
        # 对数衰减：访问越多分越高但边际递减
        import math
        return min(0.3, 0.3 * math.log(1 + count) / math.log(1 + 100))

    def _time_decay_factor(self, node: dict) -> float:
        """时间衰减因子"""
        now = self._now if self._now else datetime.now()

        # 优先使用 last_accessed
        last_accessed_str = node.get('last_accessed')
        if last_accessed_str:
            try:
                last_accessed = datetime.fromisoformat(last_accessed_str)
            except (ValueError, TypeError):
                last_accessed = now
        else:
            # 回退到 created_at
            created_str = node.get('created_at')
            if created_str:
                try:
                    last_accessed = datetime.fromisoformat(created_str)
                except (ValueError, TypeError):
                    last_accessed = now
            else:
                last_accessed = now

        delta = now - last_accessed
        delta_days = delta.total_seconds() / 86400.0

        # 指数衰减
        decay_rate = node.get('decay_rate', 0.95)
        factor = decay_rate ** delta_days

        return max(0.0, min(1.0, factor))

    def _relation_density_score(self, node: dict) -> float:
        """关联密度得分"""
        node_id = node.get('node_id')
        if not node_id:
            return 0.0

        relations = self.store.get_relations_for_node(node_id)
        count = len(relations)
        if count == 0:
            return 0.0

        # 对数衰减
        import math
        return min(0.3, 0.3 * math.log(1 + count) / math.log(1 + 10))

    def _critical_type_weight(self, node: dict) -> float:
        """关键类型加权"""
        node_type = node.get('node_type', '')

        if node_type == 'event':
            event_type = node.get('event_type', 'other')
            weights = {
                'decision': 0.1,
                'outcome': 0.1,
                'milestone': 0.08,
                'error': 0.05,
                'discovery': 0.05,
                'change': 0.03,
                'other': 0.0,
            }
            return weights.get(event_type, 0.0)
        elif node_type == 'task':
            # 任务优先级加权
            priority = node.get('priority', 3)
            return (priority - 1) * 0.025  # 0.025 ~ 0.1

        return 0.0

    def rank_nodes(self, nodes: list[dict],
                   top_k: int = None) -> list[tuple[dict, float]]:
        """对节点列表按价值排序"""
        scored = [(node, self.evaluate(node)) for node in nodes]
        scored.sort(key=lambda x: x[1], reverse=True)

        if top_k is not None:
            return scored[:top_k]
        return scored

    def select_for_compression(self, nodes: list[dict],
                               compression_ratio: float = 0.5) -> tuple[list[dict], list[dict]]:
        """
        为压缩选择节点：保留高价值节点，低价值节点作为压缩候选
        
        Returns:
            (keep_list, compress_list)
        """
        scored = self.rank_nodes(nodes)
        threshold_idx = max(1, int(len(scored) * (1 - compression_ratio)))
        keep = [node for node, _ in scored[:threshold_idx]]
        compress = [node for node, _ in scored[threshold_idx:]]
        return keep, compress

    def select_for_eviction(self, nodes: list[dict],
                            threshold: float = 0.1) -> tuple[list[dict], list[dict]]:
        """
        淘汰低价值节点
        
        Returns:
            (keep_list, evict_list)
        """
        keep = []
        evict = []
        for node in nodes:
            score = self.evaluate(node)
            if score < threshold:
                evict.append(node)
            else:
                keep.append(node)
        return keep, evict

    def update_importance_scores(self):
        """批量更新数据库中所有节点的 importance_score"""
        nodes = self.store.get_all_nodes()
        for node in nodes:
            new_score = self.evaluate(node)
            node_id = node.get('node_id')
            if node_id:
                self._update_node_score(node_id, new_score)

    def _update_node_score(self, node_id: str, new_score: float):
        """更新单个节点的 importance_score"""
        try:
            cursor = self.store.conn.cursor()
            cursor.execute(
                "UPDATE nodes SET importance_score = ? WHERE node_id = ?",
                (new_score, node_id)
            )
            self.store.conn.commit()
        except Exception:
            pass

    def get_node_value_tiers(self, nodes: list[dict] = None) -> dict[str, list[dict]]:
        """
        将节点分层：高价值、中价值、低价值
        
        Returns:
            {'high': [...], 'medium': [...], 'low': [...]}
        """
        if nodes is None:
            nodes = self.store.get_all_nodes()

        high, medium, low = [], [], []
        for node in nodes:
            score = self.evaluate(node)
            if score >= 0.7:
                high.append(node)
            elif score >= 0.3:
                medium.append(node)
            else:
                low.append(node)

        return {'high': high, 'medium': medium, 'low': low}
