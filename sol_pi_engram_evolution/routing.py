"""
阶段 4：短对话轻量路由
对话长度／任务复杂度／图谱节点存在性 → 路由决策 lightweight / standard / full_graph
"""

import importlib.util
import os
from typing import Any

# 动态导入
_gs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_store.py")
_gs_spec = importlib.util.spec_from_file_location("graph_store", _gs_path)
_gs_mod = importlib.util.module_from_spec(_gs_spec)
_gs_spec.loader.exec_module(_gs_mod)
GraphStore = _gs_mod.GraphStore


class RoutingStrategy:
    """路由策略枚举"""
    LIGHTWEIGHT = "lightweight"
    STANDARD = "standard"
    FULL_GRAPH = "full_graph"


class Router:
    """短对话轻量路由器"""

    def __init__(self, store: GraphStore, config: dict = None):
        self.store = store
        self.config = config or {}
        # 阈值配置
        self.short_message_threshold = self.config.get('short_message_threshold', 3)
        self.long_message_threshold = self.config.get('long_message_threshold', 15)
        self.complexity_keywords = self.config.get('complexity_keywords', [
            '复杂', '系统', '架构', '优化', '设计', '实现', '集成',
            '开发', '项目', '部署', '配置', '调试', '分析', '重构'
        ])
        self.min_graph_nodes_for_full = self.config.get('min_graph_nodes_for_full', 5)

    def route(self, messages: list[dict[str, Any]],
              query: str = None) -> str:
        """
        路由决策
        
        Args:
            messages: 对话消息列表
            query: 最新查询（可选）
            
        Returns:
            路由决策 ∈ {lightweight, standard, full_graph}
        """
        msg_count = len(messages)

        # 极短对话 → lightweight
        if msg_count <= self.short_message_threshold:
            return RoutingStrategy.LIGHTWEIGHT

        # 对话长度在中间范围，判断复杂度
        query = query or (messages[-1].get('content', '') if messages else '')

        # 检查复杂度信号
        complexity_score = self._complexity_score(query)

        # 检查是否涉及已有图谱节点
        graph_relevance = self._check_graph_relevance(query)

        # 决策
        if complexity_score >= 0.5 and graph_relevance >= 0.3:
            return RoutingStrategy.FULL_GRAPH
        elif complexity_score >= 0.3 or msg_count >= self.long_message_threshold:
            return RoutingStrategy.STANDARD
        else:
            return RoutingStrategy.LIGHTWEIGHT

    def _complexity_score(self, query: str) -> float:
        """计算查询复杂度分数"""
        if not query:
            return 0.0

        score = 0.0
        query_lower = query.lower()

        # 关键词匹配
        for kw in self.complexity_keywords:
            if kw in query_lower:
                score += 0.15

        # 长度因子
        score += min(0.3, len(query) / 500.0)

        # 多问题检测（问号数量）
        question_count = query.count('?') + query.count('？')
        score += min(0.2, question_count * 0.05)

        return min(1.0, score)

    def _check_graph_relevance(self, query: str) -> float:
        """检查查询与图谱的相关性"""
        if not query:
            return 0.0

        nodes = self.store.get_all_nodes()
        if not nodes:
            return 0.0

        # 简单关键词匹配
        query_lower = query.lower()
        relevant_count = 0

        for node in nodes:
            title = (node.get('title', '') or '').lower()
            description = (node.get('description', '') or '').lower()

            if title and title in query_lower:
                relevant_count += 1
            elif description:
                # 取前100字符作为关键词源
                words = description[:100].split()
                for word in words:
                    if len(word) > 2 and word in query_lower:
                        relevant_count += 1
                        break

        return min(1.0, relevant_count / max(1, len(nodes)))

    def get_routing_info(self, messages: list[dict[str, Any]],
                         query: str = None) -> dict[str, Any]:
        """获取详细路由信息（用于调试和日志）"""
        msg_count = len(messages)
        query = query or (messages[-1].get('content', '') if messages else '')

        return {
            'strategy': self.route(messages, query),
            'message_count': msg_count,
            'query_length': len(query) if query else 0,
            'complexity_score': self._complexity_score(query),
            'graph_relevance': self._check_graph_relevance(query),
            'short_threshold': self.short_message_threshold,
            'long_threshold': self.long_message_threshold,
        }


def route_conversation(messages: list[dict[str, Any]],
                       query: str = None,
                       store: GraphStore = None,
                       config: dict = None) -> str:
    """路由决策便捷函数"""
    router = Router(store, config)
    return router.route(messages, query)
