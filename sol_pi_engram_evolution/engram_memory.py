#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Engram × SoL-Pi 集成模块 — 条件记忆层

基于 DeepSeek Engram 论文核心思想（arXiv:2601.07372）：
- N-gram hash → O(1) lookup
- 静态模式存储与动态推理分离
- 作为 SoL-Pi 图谱记忆的持久化缓存层

适配 SoL-Pi 场景：
- 谈判对话中的关键事实/承诺/数字 → engram 存储
- 后续对话中相同/相似 n-gram 出现时 O(1) 召回
- 与 GraphStore 配合：engram 是热缓存，GraphStore 是持久存储
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class EngramEntry:
    """单条 engram 记忆条目"""
    key: str              # 原始 n-gram 文本
    hash_val: int         # n-gram hash 值
    value: dict           # 关联数据（事实/承诺/数字/上下文）
    created_at: float     # 创建时间戳
    access_count: int = 0
    last_accessed: float = 0.0
    importance: float = 0.5   # 0-1 重要性评分
    ngram_size: int = 2       # n-gram 大小（2 或 3）
    source: str = ""          # 来源标识


@dataclass
class EngramConfig:
    """Engram 模块配置"""
    db_path: str = "engram_memory.db"
    max_ngram_size: int = 3        # 最大 n-gram 大小
    hash_prime: int = 10007        # 哈希质数基数
    capacity: int = 100000         # 最大条目数
    importance_threshold: float = 0.3  # 低于此值可被淘汰
    decay_rate: float = 0.95       # 时间衰减率
    auto_evict: bool = True        # 超容时自动淘汰


class NgramHasher:
    """
    N-gram 哈希映射器（Engram 核心算法）

    原理：对 token 序列中的每个 n-gram 计算多项式哈希，
    实现 O(1) 的常量时间查找。
    """

    def __init__(self, config: EngramConfig):
        self.config = config
        # 预计算不同 n-gram 大小的乘数
        self.multipliers = self._init_multipliers()

    def _init_multipliers(self) -> dict[int, list[int]]:
        """为每种 n-gram 大小初始化乘数组"""
        multipliers = {}
        for n in range(2, self.config.max_ngram_size + 1):
            mults = []
            for k in range(n):
                # 使用质数乘数确保哈希分布均匀
                m = self.config.hash_prime * (k + 1) + (k * 31)
                mults.append(m)
            multipliers[n] = mults
        return multipliers

    def tokenize(self, text: str) -> list[str]:
        """
        轻量级分词：中英文混合处理

        - 英文/数字：按空格切分
        - 中文：逐字切分（字级别 n-gram 在中文场景效果最好）
        - 保留百分号、货币符号等关键标记

        谈判场景优化：保留数字、百分比、金额等关键 token
        """
        tokens = []
        current_alnum = []  # 连续 alphanumeric（英文/数字）

        for ch in text:
            if '\u4e00' <= ch <= '\u9fff':
                # 中文字符：先 flush 之前的 alnum，再单独成 token
                if current_alnum:
                    tokens.append(''.join(current_alnum))
                    current_alnum = []
                tokens.append(ch)
            elif ch.isalnum() or ch in '%.￥$':
                current_alnum.append(ch)
            else:
                # 标点/空格：flush alnum
                if current_alnum:
                    tokens.append(''.join(current_alnum))
                    current_alnum = []
                # 跳过空白，但保留有意义的标点
                if ch.strip() and ch not in '，。！？、；：""''（）【】《》':
                    tokens.append(ch)

        if current_alnum:
            tokens.append(''.join(current_alnum))

        return tokens

    def compute_hash(self, ngram_tokens: list[str], ngram_size: int) -> int:
        """计算 n-gram 哈希值"""
        mults = self.multipliers[ngram_size]
        hash_val = 0
        for i, token in enumerate(ngram_tokens):
            # 对每个 token 用内置 hash 转整数
            token_hash = int(hashlib.md5(token.encode()).hexdigest()[:8], 16)
            hash_val ^= (token_hash * mults[i])
        return abs(hash_val)

    def extract_ngrams(self, text: str) -> list[tuple[str, int, int]]:
        """
        从文本中提取所有 n-gram 及其哈希

        Returns:
            [(ngram_text, hash_val, ngram_size), ...]
        """
        tokens = self.tokenize(text)
        results = []
        for n in range(2, self.config.max_ngram_size + 1):
            for i in range(len(tokens) - n + 1):
                gram = tokens[i:i + n]
                gram_text = ' '.join(gram)
                h = self.compute_hash(gram, n)
                results.append((gram_text, h, n))
        return results


class EngramMemory:
    """
    Engram 条件记忆模块 — SoL-Pi 的持久热缓存

    核心能力：
    1. store(key, value) — 存储谈判关键信息
    2. recall(text) — 根据输入文本 O(1) 召回相关记忆
    3. forget(hash) — 显式遗忘
    4. decay() — 时间衰减清理

    与 GraphStore 的关系：
    - Engram = 热缓存（内存 + SQLite，O(1) 查找）
    - GraphStore = 持久存储（结构化图谱，语义检索）
    """

    def __init__(self, config: EngramConfig = None):
        self.config = config or EngramConfig()
        self.hasher = NgramHasher(config or EngramConfig())
        self._init_db()

    def _init_db(self):
        """初始化 SQLite 存储"""
        self.conn = sqlite3.connect(self.config.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engram_entries (
                hash_val INTEGER NOT NULL,
                ngram_size INTEGER NOT NULL,
                key_text TEXT NOT NULL,
                value_json TEXT NOT NULL,
                created_at REAL NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed REAL DEFAULT 0,
                importance REAL DEFAULT 0.5,
                source TEXT DEFAULT '',
                PRIMARY KEY (hash_val, ngram_size)
            )
        """)
        # 索引加速 recall 查询
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_engram_hash
            ON engram_entries(hash_val, ngram_size)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_engram_importance
            ON engram_entries(importance DESC)
        """)
        self.conn.commit()

    def store(self, text: str, value: dict, importance: float = 0.5,
              source: str = "") -> list[int]:
        """
        存储文本的 n-gram engram

        Args:
            text: 原始文本（如"对方同意降价5%"）
            value: 关联数据（如{"type": "commitment", "price_drop": 5}）
            importance: 重要性评分 0-1
            source: 来源标识

        Returns:
            存储的 hash 值列表
        """
        ngrams = self.hasher.extract_ngrams(text)
        stored_hashes = []
        cursor = self.conn.cursor()

        for gram_text, hash_val, ngram_size in ngrams:
            entry = EngramEntry(
                key=gram_text,
                hash_val=hash_val,
                value=value,
                created_at=time.time(),
                importance=importance,
                ngram_size=ngram_size,
                source=source,
            )
            cursor.execute("""
                INSERT OR REPLACE INTO engram_entries
                (hash_val, ngram_size, key_text, value_json,
                 created_at, access_count, last_accessed, importance, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.hash_val, entry.ngram_size, entry.key,
                json.dumps(entry.value, ensure_ascii=False),
                entry.created_at, entry.access_count,
                entry.last_accessed, entry.importance, entry.source,
            ))
            stored_hashes.append(hash_val)

        self.conn.commit()

        # 超容淘汰
        if self.config.auto_evict:
            self._maybe_evict()

        return stored_hashes

    def recall(self, text: str, top_k: int = 5,
               min_importance: float = 0.0) -> list[dict]:
        """
        O(n) 召回：对输入文本的每个 n-gram 做 O(1) hash 查找

        Args:
            text: 输入文本
            top_k: 最多返回条数
            min_importance: 最低重要性过滤

        Returns:
            匹配的记忆条目列表（按重要性降序）
        """
        ngrams = self.hasher.extract_ngrams(text)
        results = []
        seen_hashes = set()
        cursor = self.conn.cursor()

        for gram_text, hash_val, ngram_size in ngrams:
            if hash_val in seen_hashes:
                continue

            cursor.execute("""
                SELECT * FROM engram_entries
                WHERE hash_val = ? AND ngram_size = ?
                AND importance >= ?
            """, (hash_val, ngram_size, min_importance))

            row = cursor.fetchone()
            if row:
                seen_hashes.add(hash_val)
                entry = {
                    'key_text': row['key_text'],
                    'value': json.loads(row['value_json']),
                    'importance': row['importance'],
                    'access_count': row['access_count'],
                    'created_at': row['created_at'],
                    'source': row['source'],
                    'ngram_size': row['ngram_size'],
                }
                results.append(entry)

                # 更新访问计数
                cursor.execute("""
                    UPDATE engram_entries
                    SET access_count = access_count + 1,
                        last_accessed = ?
                    WHERE hash_val = ? AND ngram_size = ?
                """, (time.time(), hash_val, ngram_size))

        self.conn.commit()

        # 按重要性 + 访问频率排序
        results.sort(
            key=lambda x: x['importance'] * 0.7 + min(x['access_count'] / 10, 0.3),
            reverse=True
        )
        return results[:top_k]

    def recall_with_decay(self, text: str, top_k: int = 5) -> list[dict]:
        """带时间衰减的召回：越新的记忆权重越高"""
        raw = self.recall(text, top_k=top_k * 2)
        now = time.time()
        for entry in raw:
            age_hours = (now - entry['created_at']) / 3600
            decay = self.config.decay_rate ** age_hours
            entry['decayed_score'] = entry['importance'] * decay
        raw.sort(key=lambda x: x['decayed_score'], reverse=True)
        return raw[:top_k]

    def forget(self, hash_val: int, ngram_size: int) -> bool:
        """显式遗忘某条 engram"""
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM engram_entries
            WHERE hash_val = ? AND ngram_size = ?
        """, (hash_val, ngram_size))
        self.conn.commit()
        return cursor.rowcount > 0

    def decay_cleanup(self, threshold: float = 0.1) -> int:
        """
        清理时间衰减后低于阈值的条目

        Returns:
        清理的条目数
        """
        cursor = self.conn.cursor()
        now = time.time()

        # 获取所有条目，计算衰减后评分
        cursor.execute("SELECT hash_val, ngram_size, importance, created_at FROM engram_entries")
        to_delete = []
        for row in cursor.fetchall():
            age_hours = (now - row['created_at']) / 3600
            decayed = row['importance'] * (self.config.decay_rate ** age_hours)
            if decayed < threshold:
                to_delete.append((row['hash_val'], row['ngram_size']))

        for hash_val, ngram_size in to_delete:
            cursor.execute("""
                DELETE FROM engram_entries
                WHERE hash_val = ? AND ngram_size = ?
            """, (hash_val, ngram_size))

        self.conn.commit()
        return len(to_delete)

    def _maybe_evict(self):
        """超容量时淘汰最低重要性条目"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM engram_entries")
        count = cursor.fetchone()['cnt']

        if count > self.config.capacity:
            evict_count = count - self.config.capacity
            cursor.execute("""
                DELETE FROM engram_entries
                WHERE rowid IN (
                    SELECT rowid FROM engram_entries
                    ORDER BY importance ASC, access_count ASC
                    LIMIT ?
                )
            """, (evict_count,))
            self.conn.commit()

    def stats(self) -> dict:
        """返回 engram 记忆统计"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM engram_entries")
        total = cursor.fetchone()['total']

        cursor.execute("""
            SELECT AVG(importance) as avg_imp,
                   AVG(access_count) as avg_access,
                   MAX(access_count) as max_access
            FROM engram_entries
        """)
        row = cursor.fetchone()

        return {
            'total_entries': total,
            'capacity': self.config.capacity,
            'usage_ratio': total / self.config.capacity if self.config.capacity > 0 else 0,
            'avg_importance': row['avg_imp'] or 0,
            'avg_access_count': row['avg_access'] or 0,
            'max_access_count': row['max_access'] or 0,
        }

    def clear(self):
        """清空所有 engram"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM engram_entries")
        self.conn.commit()

    def close(self):
        """关闭数据库连接"""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ── SoL-Pi 集成接口 ──────────────────────────────────────

class EngramSoLPiBridge:
    """
    Engram × SoL-Pi 桥接器

    将 Engram 条件记忆模块桥接到 SoL-Pi Pipeline：
    - 在 Pipeline 处理查询前，用 Engram 快速召回相关记忆
    - 将召回结果注入上下文，减少 GraphRetriever 负担
    - 在 Pipeline 产生新信息后，自动存储关键 engram
    """

    def __init__(self, engram: EngramMemory = None, config: dict = None):
        self.engram = engram or EngramMemory()
        self.config = config or {}
        self.recall_top_k = self.config.get('recall_top_k', 5)
        self.min_importance = self.config.get('min_importance', 0.2)

    def pre_query(self, query: str) -> dict:
        """
        查询前处理：从 Engram 快速召回

        Returns:
            {
                'engram_hits': [...],     # 命中的记忆
                'has_memory': bool,        # 是否有相关记忆
                'context_boost': str,      # 可注入上下文的文本
            }
        """
        hits = self.engram.recall(
            query,
            top_k=self.recall_top_k,
            min_importance=self.min_importance,
        )

        context_boost = ""
        if hits:
            facts = []
            for h in hits:
                v = h['value']
                if 'summary' in v:
                    facts.append(v['summary'])
                elif 'fact' in v:
                    facts.append(v['fact'])
            context_boost = " | ".join(facts)

        return {
            'engram_hits': hits,
            'has_memory': len(hits) > 0,
            'context_boost': context_boost,
        }

    def post_response(self, query: str, response: str,
                      extracted_facts: list[dict] = None):
        """
        响应后处理：将关键信息存入 Engram

        Args:
            query: 原始查询
            response: 模型响应
            extracted_facts: 从事实提取器得到的 facts 列表
                [{"text": "...", "importance": 0.8, "data": {...}}, ...]
        """
        if extracted_facts:
            for fact in extracted_facts:
                self.engram.store(
                    text=fact['text'],
                    value=fact.get('data', {'fact': fact['text']}),
                    importance=fact.get('importance', 0.5),
                    source='post_response',
                )
        else:
            # 默认：存储整个 query-response 对
            combined = f"{query} {response}"
            self.engram.store(
                text=combined,
                value={
                    'query': query,
                    'response': response[:500],  # 截断
                    'type': 'qa_pair',
                },
                importance=0.5,
                source='auto',
            )

    def get_stats(self) -> dict:
        return self.engram.stats()

    def close(self):
        self.engram.close()
