#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
阶段 2：上下文压缩模块（V2 TokenJuice 增强版）

复用 OpenHuman 的 TokenJuice 压缩思路：
- 时序树状索引：按时间分层组织记忆节点
- 智能分层压缩：不同层级的压缩策略不同
- 实体一致性保留：确保压缩后实体关系不丢失
- 渐进式压缩：基于访问频率的淘汰策略

V2 新增：
- TokenJuice 三层压缩架构（瞬/短/长期分层）
- 实体关系一致性保留（Coreference-Aware Compression）
- 时序感知的时间衰减压缩比
- 跨节点引用完整性维护
"""

from __future__ import annotations

import importlib.util
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any

# 动态导入避免 sys.path 依赖
_gs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_store.py")
_gs_spec = importlib.util.spec_from_file_location("graph_store", _gs_path)
_gs_mod = importlib.util.module_from_spec(_gs_spec)
_gs_spec.loader.exec_module(_gs_mod)


@dataclass
class CompressionTier:
    """压缩层级配置（TokenJuice 三层模型）"""
    name: str
    max_age_hours: float        # 该层级的最大保留时间
    base_ratio: float           # 基础压缩比
    preserve_fields: list[str]  # 必须保留的字段
    optional_fields: list[str]  # 可压缩的字段
    min_token_floor: int = 50   # 最低保留 token 数


# TokenJuice 三层压缩策略
TIER_EPHEMERAL = CompressionTier(
    name="ephemeral",
    max_age_hours=1.0,
    base_ratio=0.3,
    preserve_fields=["node_id", "node_type"],
    optional_fields=["title", "description"],
    min_token_floor=30,
)

TIER_SHORTTERM = CompressionTier(
    name="shortterm",
    max_age_hours=24.0,
    base_ratio=0.5,
    preserve_fields=["node_id", "node_type", "title", "entities"],
    optional_fields=["description", "outcome"],
    min_token_floor=80,
)

TIER_LONGTERM = CompressionTier(
    name="longterm",
    max_age_hours=720.0,  # 30天
    base_ratio=0.7,
    preserve_fields=["node_id", "node_type", "title", "entities", "description"],
    optional_fields=["outcome"],
    min_token_floor=100,
)


# ========== TokenJuice 压缩引擎 ==========

class TokenJuiceCompressor:
    """TokenJuice 压缩引擎 — OpenHuman 记忆压缩思路实现

    核心思路：
    1. 按时间分三层（瞬/短/长期），不同层不同压缩比
    2. 实体一致性保留：压缩时维护实体引用完整性
    3. 渐进式压缩：高频访问节点低压缩，低频高压缩
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.tiers = {
            "ephemeral": TIER_EPHEMERAL,
            "shortterm": TIER_SHORTTERM,
            "longterm": TIER_LONGTERM,
        }
        self._compression_stats = {
            "total_compressed": 0,
            "total_tokens_saved": 0,
            "tier_counts": {"ephemeral": 0, "shortterm": 0, "longterm": 0},
        }

    def compress_node(self, node: dict, tier: CompressionTier,
                      access_frequency: float = 1.0) -> dict:
        """对单个节点执行 TokenJuice 分层压缩"""
        compressed = {
            "node_id": node.get("node_id"),
            "node_type": node.get("node_type"),
            "_tokenjuice_compressed": True,
            "_tier": tier.name,
            "_compressed_at": time.time(),
        }

        # 访问频率越高，压缩比越低（渐进式压缩）
        freq_factor = max(0.3, min(1.0, 1.0 / max(access_frequency, 0.1)))
        effective_ratio = tier.base_ratio * freq_factor

        # 保留字段
        for field in tier.preserve_fields:
            if field in ("node_id", "node_type"):
                continue  # 已处理
            val = node.get(field)
            if val:
                if isinstance(val, str):
                    compressed[field] = val  # 保留字段不压缩
                else:
                    compressed[field] = val

        # 可压缩字段
        for field in tier.optional_fields:
            val = node.get(field)
            if not val or not isinstance(val, str):
                continue
            compressed[field] = self._compress_text(val, effective_ratio)

        # 实体一致性：确保 entities 引用完整
        entities = node.get("entities")
        if entities and "entities" in tier.preserve_fields:
            compressed["entities"] = entities

        # 引用完整性：保留 relation 指向的 node_id
        for key in ("related_event_ids", "related_task_ids"):
            val = node.get(key)
            if val and isinstance(val, list):
                compressed[key] = val

        self._compression_stats["total_compressed"] += 1
        self._compression_stats["tier_counts"][tier.name] += 1
        original_tokens = self._estimate_tokens(node)
        compressed_tokens = self._estimate_tokens(compressed)
        self._compression_stats["total_tokens_saved"] += (original_tokens - compressed_tokens)

        return compressed

    def _compress_text(self, text: str, ratio: float) -> str:
        """压缩文本到目标比率（TokenJuice 风格）"""
        target_len = max(20, int(len(text) * (1 - ratio)))
        if len(text) <= target_len:
            return text

        # 优先保留句首（通常含关键信息）
        sentences = re.split(r'[。！？.!?]', text)
        if len(sentences) > 1:
            kept = []
            current_len = 0
            for sent in sentences:
                if current_len + len(sent) <= target_len:
                    kept.append(sent)
                    current_len += len(sent)
                else:
                    break
            result = "。".join(kept)
            if not result:
                result = text[:target_len]
            return result + ("..." if len(text) > len(result) else "")

        # 单句直接截断
        return text[:target_len] + "..."

    def _estimate_tokens(self, node: dict) -> int:
        """估算节点 token 数"""
        total = 0
        for v in node.values():
            if isinstance(v, str):
                total += len(v) // 4  # 粗略估算：1 token ≈ 4 chars
            elif isinstance(v, (list, dict)):
                total += len(str(v)) // 4
        return total

    def determine_tier(self, node: dict) -> CompressionTier:
        """根据节点创建时间确定压缩层级"""
        created = node.get("created_at", "")
        now = time.time()

        # 解析 ISO 时间戳
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            age_hours = (now - dt.timestamp()) / 3600.0
        except Exception:
            age_hours = 0  # 解析失败视为即时

        if age_hours < 1:
            return self.tiers["ephemeral"]
        elif age_hours < 24:
            return self.tiers["shortterm"]
        else:
            return self.tiers["longterm"]

    def get_stats(self) -> dict:
        return dict(self._compression_stats)


# ========== 经济学触发判断（保留 LoPace 兼容） ==========

LOPACE_COMPRESSION_RATE = 0.722
CONTEXT_BUDGET_WEIGHT = 0.85

# 全局 TokenJuice 压缩器
_tokenjuice_compressor = None


def _get_compressor(config: dict = None) -> TokenJuiceCompressor:
    global _tokenjuice_compressor
    if _tokenjuice_compressor is None:
        _tokenjuice_compressor = TokenJuiceCompressor(config)
    return _tokenjuice_compressor


def should_compact(context: dict[str, Any],
                   config: dict = None) -> bool:
    """判断是否应执行上下文压缩（经济学触发）"""
    config = config or {}
    future_savings = _estimate_future_savings(context, config)
    rewrite_cost = _estimate_rewrite_cost(context, config)
    cache_miss_cost = _estimate_cache_miss_cost(context, config)
    return future_savings >= rewrite_cost + cache_miss_cost


def compact_context(context: dict[str, Any],
                    config: dict = None) -> dict[str, Any]:
    """执行压缩：TokenJuice 三层分层压缩

    策略：
    1. 按价值评估排序节点
    2. 按创建时间确定压缩层级（瞬/短/长期）
    3. 高价值节点应用轻压缩，低价值节点应用重压缩
    4. 保留实体关系完整性
    """
    config = config or {}
    compressor = _get_compressor(config)
    result = dict(context)

    nodes = context.get('relevant_nodes', [])
    if not nodes:
        result['compressed'] = True
        result['compression_timestamp'] = time.time()
        return result

    # 加载 ValueEvaluator
    try:
        ve_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "value_evaluator.py")
        ve_spec = importlib.util.spec_from_file_location("value_evaluator", ve_path)
        ve_mod = importlib.util.module_from_spec(ve_spec)
        ve_spec.loader.exec_module(ve_mod)
        evaluator = ve_mod.ValueEvaluator()
    except Exception:
        evaluator = None

    # Step 1: 评估节点价值并排序
    scored_nodes = []
    for node in nodes:
        node_dict = node[0] if isinstance(node, tuple) else node
        score = evaluator.evaluate(node_dict) if evaluator else 0.5
        scored_nodes.append((node_dict, score))
    scored_nodes.sort(key=lambda x: x[1], reverse=True)

    # Step 2: ContextBudget 动态预算
    budget_ratio = config.get('context_budget_ratio', CONTEXT_BUDGET_WEIGHT)
    keep_count = max(1, int(len(scored_nodes) * (1 - budget_ratio)))

    # 高价值节点保留，低价值节点压缩
    preserved_nodes = [n for n, _ in scored_nodes[:keep_count]]
    compressed_nodes = []
    for node, score in scored_nodes[keep_count:]:
        tier = compressor.determine_tier(node)
        access_freq = max(1, node.get('access_count', 1))
        compressed = compressor.compress_node(node, tier, access_freq)
        compressed_nodes.append(compressed)

    result['relevant_nodes'] = preserved_nodes + compressed_nodes
    result['compressed'] = True
    result['compression_timestamp'] = time.time()
    result['compression_method'] = 'tokenjuice_3tier_hybrid'
    result['nodes_preserved'] = len(preserved_nodes)
    result['nodes_compressed'] = len(compressed_nodes)
    result['tier_stats'] = compressor.get_stats()

    # 估算节省 token
    original_total = sum(_estimate_node_tokens(n) for n in nodes if isinstance(n, dict))
    compressed_total = sum(_estimate_node_tokens(n) for n in compressed_nodes)
    preserved_total = sum(_estimate_node_tokens(n) for n in preserved_nodes)
    result['estimated_token_savings'] = max(0, original_total - (compressed_total + preserved_total))

    return result


def _estimate_node_tokens(node: dict) -> int:
    """估算单个节点 token 数"""
    if not isinstance(node, dict):
        return 200
    total = 0
    for v in node.values():
        if isinstance(v, str):
            total += len(v) // 4
        elif isinstance(v, (list, dict)):
            total += len(str(v)) // 4
    return total


def _lopace_compress_node(node: dict, compression_rate: float) -> dict:
    """保留 LoPace 兼容（旧接口）"""
    tier = CompressionTier(
        name="legacy_lopace",
        max_age_hours=9999,
        base_ratio=1.0 - compression_rate,
        preserve_fields=["node_id", "node_type"],
        optional_fields=["title", "description", "entities"],
    )
    return _get_compressor().compress_node(node, tier)


def _estimate_future_savings(context: dict[str, Any],
                             config: dict) -> float:
    nodes = context.get('relevant_nodes', [])
    tokens_per_node = config.get('tokens_per_node', 200)
    future_queries = config.get('future_queries_estimate', 3)
    return len(nodes) * tokens_per_node * future_queries


def _estimate_rewrite_cost(context: dict[str, Any],
                           config: dict) -> float:
    total_tokens = context.get('total_tokens_estimate', 0)
    factor = config.get('rewrite_cost_factor', 0.5)
    return total_tokens * factor


def _estimate_cache_miss_cost(context: dict[str, Any],
                              config: dict) -> float:
    return config.get('cache_miss_penalty', 500)


def get_compression_stats() -> dict:
    """获取压缩统计"""
    return _get_compressor().get_stats()
