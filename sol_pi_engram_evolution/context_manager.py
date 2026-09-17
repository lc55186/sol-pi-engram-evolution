"""
阶段 2：上下文管理器
新提问 → 图谱检索 → 上下文装配 → SoL-Pi 效率优化接口
"""

import importlib.util
import os
from typing import Any

# 动态导入 graph_retriever，避免 sys.path 依赖
_gr_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_retriever.py")
_gr_spec = importlib.util.spec_from_file_location("graph_retriever", _gr_path)
_gr_mod = importlib.util.module_from_spec(_gr_spec)
_gr_spec.loader.exec_module(_gr_mod)
GraphRetriever = _gr_mod.GraphRetriever


class ContextManager:
    """上下文管理器：图谱检索 + SoL-Pi 上下文优化入口"""

    def __init__(self, retriever: GraphRetriever, config: dict = None):
        self.retriever = retriever
        self.config = config or {}

    def build_context(self, query: str) -> dict[str, Any]:
        """构建上下文：检索相关节点 + 摘要 + 优化触发标志"""
        nodes = self.retriever.retrieve(
            query,
            top_k=self.config.get('context_limit', 5)
        )

        context = {
            'query': query,
            'relevant_nodes': nodes,
            'nodes_summary': self._summarize_nodes(nodes),
            'node_count': len(nodes),
            'action_fusion_ready': len(nodes) > 0,
            'compact_trigger': self._should_compact(query, nodes),
            'total_tokens_estimate': self._estimate_tokens(nodes),
        }
        return context

    def _summarize_nodes(self, nodes: list[tuple]) -> list[str]:
        """每个节点一行摘要"""
        summaries = []
        for node, score in nodes:
            node_type = node.get('node_type', 'unknown')
            title = node.get('title', '') or 'Untitled'
            summaries.append(f"[{node_type}] {title} (score={score:.2f})")
        return summaries

    def _should_compact(self, query: str,
                        nodes: list[tuple]) -> bool:
        """判断是否触发上下文压缩（简单启发式）"""
        node_count = len(nodes)
        query_len = len(query)
        threshold_nodes = self.config.get('compact_node_threshold', 10)
        threshold_query_len = self.config.get('compact_query_length', 500)
        return node_count > threshold_nodes or query_len > threshold_query_len

    def _estimate_tokens(self, nodes: list[tuple]) -> int:
        """估计上下文总 token（粗略）"""
        tokens_per_node = self.config.get('tokens_per_node', 200)
        return len(nodes) * tokens_per_node

    def apply_action_fusion(self, operations: list) -> list:
        """委托给 action_fusion 模块"""
        # 动态导入，避免 sys.path 依赖
        af_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "action_fusion.py")
        af_spec = importlib.util.spec_from_file_location("action_fusion", af_path)
        af_mod = importlib.util.module_from_spec(af_spec)
        af_spec.loader.exec_module(af_mod)
        return af_mod.fuse_operations(operations, self.config)

    def apply_compaction(self, context: dict) -> dict:
        """委托给 context_compactor 模块"""
        cc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "context_compactor.py")
        cc_spec = importlib.util.spec_from_file_location("context_compactor", cc_path)
        cc_mod = importlib.util.module_from_spec(cc_spec)
        cc_spec.loader.exec_module(cc_mod)
        if cc_mod.should_compact(context, self.config):
            return cc_mod.compact_context(context, self.config)
        return context
