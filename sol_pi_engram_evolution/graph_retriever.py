#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
阶段 2：图谱检索模块（V2 混合检索版）
复用 WeKnora 的混合检索策略：BM25 + Dense + GraphRAG + Parent-Child

V2 新增：
- BM25 检索（IDF 加权的关键词匹配）
- Dense 向量检索（基于 Jaccard 相似度的语义匹配）
- Parent-Child 层级检索（子节点匹配 → 返回父上下文）
- Reciprocal Rank Fusion (RRF) 四路信号融合
"""

import hashlib
import importlib.util
import math
import os
import re
from collections import Counter

# 动态导入 graph_store，避免 sys.path 依赖
_gs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_store.py")
_gs_spec = importlib.util.spec_from_file_location("graph_store", _gs_path)
_gs_mod = importlib.util.module_from_spec(_gs_spec)
_gs_spec.loader.exec_module(_gs_mod)
GraphStore = _gs_mod.GraphStore


class BM25Retriever:
    """BM25 检索器：基于 IDF 加权的关键词检索"""

    def __init__(self, store: GraphStore):
        self.store = store
        self.k1 = 1.5  # BM25 参数
        self.b = 0.75  # BM25 参数
        self._idf_cache: dict[str, float] = {}
        self._avg_dl = 0.0
        self._doc_count = 0
        # 预初始化所有索引属性（确保 store 为空时属性也存在）
        self._doc_freqs: dict[str, int] = Counter()
        self._doc_lengths: dict[str, int] = {}
        self._doc_tokens: dict[str, list[str]] = {}
        self._build_index()

    def _build_index(self):
        """构建 BM25 索引（文档长度、词频统计）"""
        nodes = self.store.get_all_nodes()
        self._doc_count = len(nodes)
        if self._doc_count == 0:
            return

        total_len = 0
        # 重新初始化（避免重复调用时数据残留）
        self._doc_freqs = Counter()
        self._doc_lengths = {}
        self._doc_tokens = {}

        for node in nodes:
            tokens = self._tokenize_node(node)
            nid = node['node_id']
            self._doc_tokens[nid] = tokens
            self._doc_lengths[nid] = len(tokens)
            total_len += len(tokens)

            # 文档频率（每个词在多少个文档中出现）
            unique_tokens = set(tokens)
            for t in unique_tokens:
                self._doc_freqs[t] += 1

        self._avg_dl = total_len / max(self._doc_count, 1)

    def _tokenize_node(self, node: dict) -> list[str]:
        """将节点文本分词"""
        text = " ".join([
            node.get('title', '') or '',
            node.get('description', '') or '',
            node.get('outcome', '') or '',
            ' '.join(node.get('entities', []) or []),
        ])
        return [w for w in re.split(r'[\s,.;:!?]+', text.lower()) if w]

    def _idf(self, term: str) -> float:
        """计算 IDF 值"""
        if term in self._idf_cache:
            return self._idf_cache[term]
        df = self._doc_freqs.get(term, 0)
        idf = math.log((self._doc_count - df + 0.5) / (df + 0.5) + 1.0)
        self._idf_cache[term] = idf
        return idf

    def search(self, query: str, top_k: int = 10) -> list[tuple[dict, float]]:
        """BM25 检索"""
        query_tokens = [w for w in re.split(r'[\s,.;:!?]+', query.lower()) if w]
        if not query_tokens:
            return []

        scores: dict[str, float] = {}
        for nid, doc_tokens in self._doc_tokens.items():
            dl = self._doc_lengths[nid]
            if dl == 0:
                continue

            score = 0.0
            doc_freq = Counter(doc_tokens)
            for qt in query_tokens:
                tf = doc_freq.get(qt, 0)
                if tf == 0:
                    continue
                idf = self._idf(qt)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / max(self._avg_dl, 1))
                score += idf * numerator / denominator

            if score > 0:
                scores[nid] = score

        # 排序并返回 top_k
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        result = []
        for nid, score in ranked:
            node = self.store.get_node_by_id(nid)
            if node:
                result.append((node, score))
        return result


class DenseRetriever:
    """Dense 向量检索器（轻量级，无外部依赖）

    使用 n-gram token 集合的加权 Jaccard 相似度模拟语义检索。
    可替换为真正的 embedding 模型以获得更好效果。
    """

    def __init__(self, store: GraphStore):
        self.store = store
        self._vectors: dict[str, Counter] = {}
        self._build_index()

    def _build_index(self):
        """构建向量索引"""
        nodes = self.store.get_all_nodes()
        for node in nodes:
            nid = node['node_id']
            text = " ".join([
                (node.get('title', '') or '') * 3,  # title 权重 x3
                (node.get('description', '') or '') * 2,  # description 权重 x2
                node.get('outcome', '') or '',
                ' '.join(node.get('entities', []) or []) * 2,  # entities 权重 x2
            ])
            tokens = [w for w in re.split(r'[\s,.;:!?]+', text.lower()) if w]
            # 使用 unigram + bigram 特征
            bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens)-1)]
            self._vectors[nid] = Counter(tokens + bigrams)

    def search(self, query: str, top_k: int = 10) -> list[tuple[dict, float]]:
        """Dense 检索（加权 Jaccard 相似度）"""
        tokens = [w for w in re.split(r'[\s,.;:!?]+', query.lower()) if w]
        if not tokens:
            return []

        bigrams = [f"{tokens[i]}_{tokens[i+1]}" for i in range(len(tokens)-1)]
        query_vec = Counter(tokens + bigrams)

        scores: dict[str, float] = {}
        for nid, doc_vec in self._vectors.items():
            # 加权 Jaccard
            intersection = sum((query_vec & doc_vec).values())
            union = sum((query_vec | doc_vec).values())
            if union == 0:
                continue
            scores[nid] = intersection / union

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        result = []
        for nid, score in ranked:
            if score > 0:
                node = self.store.get_node_by_id(nid)
                if node:
                    result.append((node, score))
        return result


class ParentChildRetriever:
    """Parent-Child 层级检索器

    当子节点匹配时，同时返回其父节点（上下文），
    确保 LLM 获得完整的上下文段落而非碎片。
    """

    def __init__(self, store: GraphStore):
        self.store = store

    def expand_to_parents(self, child_results: list[tuple[dict, float]]) -> list[tuple[dict, float]]:
        """将子节点结果扩展为包含父节点的结果"""
        expanded = list(child_results)
        seen_ids = {n['node_id'] for n, _ in child_results}

        for child_node, child_score in child_results:
            # 查找与该子节点有关系的所有节点作为"父"
            relations = self.store.get_relations_for_node(child_node['node_id'])
            for rel in relations:
                parent_id = (rel['target_node_id']
                             if rel['source_node_id'] == child_node['node_id']
                             else rel['source_node_id'])
                if parent_id in seen_ids:
                    continue

                parent_node = self.store.get_node_by_id(parent_id)
                if parent_node is None:
                    continue

                # 父节点得分 = 子节点得分 × 关系权重 × 衰减
                rel_weight = self._relation_weight(rel['relation_type'])
                parent_score = child_score * rel_weight * 0.8  # 层级衰减
                expanded.append((parent_node, parent_score))
                seen_ids.add(parent_id)

        return expanded

    def _relation_weight(self, relation_type: str) -> float:
        weights = {
            'depends_on': 0.8, 'causes': 0.8, 'triggers': 0.8,
            'blocks': 0.6, 'during': 0.6, 'part_of': 0.9,
            'related_to': 0.4, 'other': 0.3,
        }
        return weights.get(relation_type, 0.3)


class HybridGraphRetriever:
    """混合图谱检索器：BM25 + Dense + GraphRAG + Parent-Child

    使用 Reciprocal Rank Fusion (RRF) 融合四路信号。
    """

    def __init__(self, store: GraphStore, config: dict = None):
        self.store = store
        self.config = config or {}

        # 四个检索通道
        self.bm25 = BM25Retriever(store)
        self.dense = DenseRetriever(store)
        self.parent_child = ParentChildRetriever(store)

        # RRF 参数
        self.rrf_k = self.config.get('rrf_k', 60)
        # 各通道权重
        self.weights = self.config.get('channel_weights', {
            'bm25': 1.0, 'dense': 1.0, 'graph': 1.0, 'parent_child': 0.8
        })

        # Engram O(1) lookup cache
        self._engram_cache: dict[str, list[tuple[dict, float]]] = {}
        self._cache_hits = 0
        self._cache_misses = 0

    def retrieve(self, query: str, top_k: int = 5,
                 min_score: float = 0.0) -> list[tuple[dict, float]]:
        """混合检索主入口：BM25 + Dense + GraphRAG + Parent-Child + RRF 融合"""

        # Step 1: Engram O(1) cache
        qhash = self._query_hash(query, min_score)
        if qhash in self._engram_cache:
            self._cache_hits += 1
            return self._engram_cache[qhash][:top_k]
        self._cache_misses += 1

        # Step 2: 四路并行检索
        bm25_results = self.bm25.search(query, top_k=top_k * 3)
        dense_results = self.dense.search(query, top_k=top_k * 3)
        graph_results = self._graph_search(query, top_k=top_k * 2)

        # Parent-Child 扩展：对 BM25 和 Dense 的 top 结果做扩展
        pc_results = self.parent_child.expand_to_parents(
            bm25_results[:top_k] + dense_results[:top_k]
        )

        # Step 3: RRF 融合
        fused = self._reciprocal_rank_fusion({
            'bm25': bm25_results,
            'dense': dense_results,
            'graph': graph_results,
            'parent_child': pc_results,
        })

        filtered = [(n, s) for n, s in fused if s >= min_score]
        filtered.sort(key=lambda x: x[1], reverse=True)
        result = filtered[:top_k]

        # Step 4: Cache
        self._engram_cache[qhash] = result
        return result

    def _reciprocal_rank_fusion(self, channel_results: dict[str, list[tuple[dict, float]]]
                                ) -> list[tuple[dict, float]]:
        """Reciprocal Rank Fusion：融合多路检索结果"""
        fused_scores: dict[str, float] = {}
        node_map: dict[str, dict] = {}

        for channel_name, results in channel_results.items():
            weight = self.weights.get(channel_name, 1.0)
            for rank, (node, _orig_score) in enumerate(results):
                nid = node['node_id']
                if nid not in fused_scores:
                    fused_scores[nid] = 0.0
                    node_map[nid] = node
                # RRF 公式: 1 / (k + rank)
                fused_scores[nid] += weight * (1.0 / (self.rrf_k + rank + 1))

        ranked = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)
        return [(node_map[nid], score) for nid, score in ranked]

    def _graph_search(self, query: str, top_k: int = 10) -> list[tuple[dict, float]]:
        """GraphRAG 检索：关键词匹配 + 关系遍历"""
        keywords = [w for w in re.split(r'[\s,.;:!?]+', query) if w]
        if not keywords:
            return []

        # TMatch
        tmatch = []
        for node in self.store.get_all_nodes():
            score = self._match_score(node, keywords)
            if score > 0:
                tmatch.append((node, score))

        # 关系遍历扩展
        expanded = list(tmatch)
        seen = {n['node_id'] for n, _ in tmatch}
        for node, base_score in tmatch:
            for rel in self.store.get_relations_for_node(node['node_id']):
                target_id = (rel['target_node_id']
                             if rel['source_node_id'] == node['node_id']
                             else rel['source_node_id'])
                if target_id in seen:
                    continue
                target = self.store.get_node_by_id(target_id)
                if target:
                    w = self._relation_weight(rel['relation_type'])
                    expanded.append((target, base_score * w))
                    seen.add(target_id)

        expanded.sort(key=lambda x: x[1], reverse=True)
        return expanded[:top_k]

    def _match_score(self, node: dict, keywords: list[str]) -> float:
        """节点匹配分数"""
        score = 0.0
        for field, weight in [('title', 3.0), ('description', 2.0), ('outcome', 1.5)]:
            value = (node.get(field, '') or '').lower()
            for kw in keywords:
                if kw.lower() in value:
                    score += weight
                    break
        entities = node.get('entities', []) or []
        for kw in keywords:
            if any(kw.lower() in str(e).lower() for e in entities):
                score += 0.5
                break
        return score

    def _relation_weight(self, relation_type: str) -> float:
        weights = {
            'depends_on': 0.8, 'causes': 0.8, 'triggers': 0.8,
            'blocks': 0.6, 'during': 0.6, 'part_of': 0.5,
            'related_to': 0.4, 'other': 0.3,
        }
        return weights.get(relation_type, 0.3)

    def _query_hash(self, query: str, min_score: float = 0.0) -> str:
        key = f"{query.lower().strip()}|ms={min_score}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def get_cache_stats(self) -> dict[str, int]:
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "cache_size": len(self._engram_cache),
            "hit_rate": self._cache_hits / max(self._cache_hits + self._cache_misses, 1)
        }


# 保留向后兼容的别名
GraphRetriever = HybridGraphRetriever
