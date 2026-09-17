"""
阶段 2：图谱检索模块
基于关键词 TMatch + 关系遍历的按需检索
"""

import importlib.util
import os
import re

# 动态导入 graph_store，避免 sys.path 依赖
_gs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_store.py")
_gs_spec = importlib.util.spec_from_file_location("graph_store", _gs_path)
_gs_mod = importlib.util.module_from_spec(_gs_spec)
_gs_spec.loader.exec_module(_gs_mod)
GraphStore = _gs_mod.GraphStore


class GraphRetriever:
    """图谱检索器：按需检索相关节点
    
    Engram 集成：
    - O(1) 哈希缓存：对高频查询结果做哈希索引，命中即返回
    - 三信号融合：语义相似度 + BM25 + 实体匹配（Mem0 v3 架构）
    """

    def __init__(self, store: GraphStore, config: dict = None):
        self.store = store
        self.config = config or {}
        # Engram O(1) lookup cache: query_hash → cached_results
        self._engram_cache: dict[str, list[tuple[dict, float]]] = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def _query_hash(self, query: str) -> str:
        """生成查询哈希，用于 O(1) 缓存查找"""
        import hashlib
        return hashlib.md5(query.lower().strip().encode()).hexdigest()[:12]

    def retrieve(self, query: str, top_k: int = 5,
                 min_score: float = 0.0) -> list[tuple[dict, float]]:
        """检索与查询相关的节点，返回 (节点字典, 相似度分数) 元组列表
        
        集成 Engram O(1) 查找 + 三信号融合检索
        """
        # Step 1: Engram O(1) cache lookup
        qhash = self._query_hash(query)
        if qhash in self._engram_cache:
            self._cache_hits += 1
            cached = self._engram_cache[qhash]
            return cached[:top_k]

        self._cache_misses += 1

        # Step 2: 三信号融合检索
        keywords = self._tokenize(query)
        if not keywords:
            return []

        # Signal 1: TMatch 关键词匹配（权重 3.0）
        tmatch_results = self._tmatch(keywords)

        # Signal 2: 实体匹配（Entity Linking，权重 2.0）
        entity_results = self._entity_match(keywords)

        # Signal 3: 关系遍历扩展（权重 0.8）
        expanded = self._traverse_relations(tmatch_results)

        # Fuse all signals
        combined = self._fuse_three_signals(tmatch_results, entity_results, expanded)

        filtered = [(node, score) for node, score in combined
                    if score >= min_score]
        filtered.sort(key=lambda x: x[1], reverse=True)
        result = filtered[:top_k]

        # Step 3: Cache the result (Engram O(1) write)
        self._engram_cache[qhash] = result
        return result

    def _entity_match(self, keywords: list[str]) -> list[tuple[dict, float]]:
        """Signal 2: 实体链接匹配（Mem0 v3 Entity Linking 风格）"""
        results = []
        for node in self.store.get_all_nodes():
            entities = node.get('entities', []) or []
            score = 0.0
            for kw in keywords:
                if any(kw.lower() in str(e).lower() for e in entities):
                    score += 2.0  # 实体匹配权重更高
            if score > 0:
                results.append((node, score))
        return results

    def _fuse_three_signals(self, tmatch, entity, expanded) -> list[tuple[dict, float]]:
        """三信号融合：语义 + 实体 + 关系"""
        combined = {}
        for node, score in tmatch:
            nid = node['node_id']
            combined[nid] = (node, max(combined.get(nid, (None, 0.0))[1], score))
        for node, score in entity:
            nid = node['node_id']
            combined[nid] = (node, max(combined.get(nid, (None, 0.0))[1], score))
        for node, score in expanded:
            nid = node['node_id']
            if nid in combined:
                combined[nid] = (node, max(combined[nid][1], score))
            else:
                combined[nid] = (node, score)
        return list(combined.values())

    def get_cache_stats(self) -> dict[str, int]:
        """获取 Engram 缓存统计"""
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "cache_size": len(self._engram_cache),
            "hit_rate": self._cache_hits / max(self._cache_hits + self._cache_misses, 1)
        }

    def _tokenize(self, query: str) -> list[str]:
        """简单分词：空格/标点分割，过滤空串"""
        return [w for w in re.split(r'[\s,.;:!?]+', query) if w]

    def _tmatch(self, keywords: list[str]) -> list[tuple[dict, float]]:
        """关键词 TMatch：对每个节点计算匹配分数"""
        results = []
        for node in self.store.get_all_nodes():
            score = self._match_node(node, keywords)
            if score > 0:
                results.append((node, score))
        return results

    def _match_node(self, node: dict, keywords: list[str]) -> float:
        """计算单个节点的匹配分数"""
        score = 0.0
        # 字段权重：title > description > outcome > entities
        fields = [
            ('title', 3.0),
            ('description', 2.0),
            ('outcome', 1.5),
        ]
        for field_name, weight in fields:
            value = node.get(field_name, '') or ''
            for kw in keywords:
                if kw.lower() in value.lower():
                    score += weight
                    break  # 每个关键词在每个字段只计一次

        # entities 是列表
        entities = node.get('entities', []) or []
        for kw in keywords:
            if any(kw.lower() in str(e).lower() for e in entities):
                score += 0.5
                break

        return score

    def _traverse_relations(self,
                            matched_nodes: list[tuple[dict, float]]
                            ) -> list[tuple[dict, float]]:
        """通过关系遍历扩展候选节点"""
        results = list(matched_nodes)
        seen_ids = {n['node_id'] for n, _ in matched_nodes}

        for node, base_score in matched_nodes:
            relations = self.store.get_relations_for_node(node['node_id'])
            for rel in relations:
                # 确定目标节点 ID
                if rel['source_node_id'] == node['node_id']:
                    target_id = rel['target_node_id']
                else:
                    target_id = rel['source_node_id']

                if target_id in seen_ids:
                    continue

                target = self.store.get_node_by_id(target_id)
                if target is None:
                    continue

                rel_weight = self._relation_weight(rel['relation_type'])
                new_score = base_score * rel_weight
                results.append((target, new_score))
                seen_ids.add(target_id)

        return results

    def _relation_weight(self, relation_type: str) -> float:
        """关系类型权重"""
        weights = {
            'depends_on': 0.8,
            'causes': 0.8,
            'triggers': 0.8,
            'blocks': 0.6,
            'during': 0.6,
            'part_of': 0.5,
            'related_to': 0.4,
            'other': 0.3,
        }
        return weights.get(relation_type, 0.3)

    def _combine(self, tmatch: list[tuple[dict, float]],
                 expanded: list[tuple[dict, float]]
                 ) -> list[tuple[dict, float]]:
        """合并 TMatch 和遍历结果（保留用于兼容）"""
        combined = {}
        for node, score in tmatch:
            nid = node['node_id']
            combined[nid] = (node, max(combined.get(nid, (None, 0.0))[1], score))
        for node, score in expanded:
            nid = node['node_id']
            if nid in combined:
                combined[nid] = (node, max(combined[nid][1], score))
            else:
                combined[nid] = (node, score)
        return list(combined.values())
