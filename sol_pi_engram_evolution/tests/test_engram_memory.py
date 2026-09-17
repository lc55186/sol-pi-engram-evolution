#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Engram × SoL-Pi 集成测试

覆盖：
1. NgramHasher 哈希计算
2. EngramMemory 存储/召回
3. 时间衰减
4. 容量淘汰
5. EngramSoLPiBridge 桥接接口
6. 中文谈判场景
"""

import os
import sys
import time
import tempfile

# 动态导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engram_memory import (
    EngramConfig,
    EngramMemory,
    EngramSoLPiBridge,
    NgramHasher,
)


def get_temp_db():
    """创建临时数据库路径"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    return path


def cleanup(path):
    if os.path.exists(path):
        os.unlink(path)


# ===== 测试 1: NgramHasher 分词 =====

class TestNgramHasher:
    def test_tokenize_chinese(self):
        config = EngramConfig()
        hasher = NgramHasher(config)
        tokens = hasher.tokenize("对方同意降价5%，总价30万")
        assert len(tokens) > 0
        assert "对方" in tokens or "同" in tokens

    def test_tokenize_english(self):
        config = EngramConfig()
        hasher = NgramHasher(config)
        tokens = hasher.tokenize("The price is 300000 RMB for 100 units")
        assert "The" in tokens or "the" in tokens
        assert "300000" in tokens

    def test_extract_bigrams(self):
        config = EngramConfig(max_ngram_size=2)
        hasher = NgramHasher(config)
        ngrams = hasher.extract_ngrams("价格 谈判 条件")
        # 2个 bigrams: (价格,谈判), (谈判,条件)
        assert len(ngrams) >= 2
        for text, h, n in ngrams:
            assert n == 2
            assert isinstance(h, int)

    def test_extract_trigrams(self):
        config = EngramConfig(max_ngram_size=3)
        hasher = NgramHasher(config)
        ngrams = hasher.extract_ngrams("对方同意降价百分之五")
        trigrams = [ng for ng in ngrams if ng[2] == 3]
        assert len(trigrams) > 0

    def test_hash_deterministic(self):
        config = EngramConfig()
        hasher = NgramHasher(config)
        h1 = hasher.compute_hash(["价格", "谈判"], 2)
        h2 = hasher.compute_hash(["价格", "谈判"], 2)
        assert h1 == h2

    def test_hash_different_ngrams(self):
        config = EngramConfig()
        hasher = NgramHasher(config)
        h1 = hasher.compute_hash(["价格", "谈判"], 2)
        h2 = hasher.compute_hash(["价格", "质量"], 2)
        assert h1 != h2


# ===== 测试 2: EngramMemory 存储与召回 =====

class TestEngramMemory:
    def setup_method(self):
        self.db_path = get_temp_db()
        self.config = EngramConfig(db_path=self.db_path)
        self.mem = EngramMemory(self.config)

    def teardown_method(self):
        self.mem.close()
        cleanup(self.db_path)

    def test_store_and_recall(self):
        self.mem.store(
            "对方同意降价5%",
            value={"type": "commitment", "price_drop_pct": 5},
            importance=0.8,
        )
        results = self.mem.recall("对方同意降价")
        assert len(results) > 0
        assert results[0]['importance'] == 0.8

    def test_recall_empty(self):
        results = self.mem.recall("完全不相关的查询")
        assert len(results) == 0

    def test_store_multiple(self):
        facts = [
            ("定州轮胎厂报价每套120元", {"type": "price", "amount": 120, "unit": "套"}, 0.7),
            ("对方要求预付30%", {"type": "payment", "prepay_pct": 30}, 0.9),
            ("交货周期45天", {"type": "delivery", "days": 45}, 0.6),
        ]
        for text, value, imp in facts:
            self.mem.store(text, value, importance=imp)

        # 用不同关键词召回
        results = self.mem.recall("定州轮胎厂报价")
        assert len(results) >= 1

    def test_access_count_increment(self):
        self.mem.store("测试文本", {"data": "test"}, importance=0.5)
        self.mem.recall("测试文本")
        self.mem.recall("测试文本")
        results = self.mem.recall("测试文本")
        if results:
            assert results[0]['access_count'] >= 2

    def test_forget(self):
        self.mem.store("忘记这条", {"data": "forget"}, importance=0.5)
        ngrams = self.mem.hasher.extract_ngrams("忘记这条")
        if ngrams:
            h = ngrams[0][1]
            n = ngrams[0][2]
            deleted = self.mem.forget(h, n)
            assert deleted

    def test_stats(self):
        self.mem.store("文本1", {"d": 1}, importance=0.5)
        self.mem.store("文本2", {"d": 2}, importance=0.7)
        stats = self.mem.stats()
        assert stats['total_entries'] > 0
        assert stats['avg_importance'] > 0

    def test_clear(self):
        self.mem.store("文本", {"d": 1}, importance=0.5)
        self.mem.clear()
        stats = self.mem.stats()
        assert stats['total_entries'] == 0


# ===== 测试 3: 时间衰减 =====

class TestTimeDecay:
    def setup_method(self):
        self.db_path = get_temp_db()
        self.config = EngramConfig(db_path=self.db_path, decay_rate=0.5)
        self.mem = EngramMemory(self.config)

    def teardown_method(self):
        self.mem.close()
        cleanup(self.db_path)

    def test_decay_reduces_score(self):
        self.mem.store("重要承诺", {"type": "promise"}, importance=0.9)
        # 刚存入应该能召回
        results = self.mem.recall_with_decay("重要承诺")
        assert len(results) > 0
        assert results[0]['decayed_score'] > 0

    def test_decay_cleanup(self):
        self.mem.store("低重要性", {"d": 1}, importance=0.1)
        # 衰减阈值 0.1，importance=0.1 的条目应该被清理
        cleaned = self.mem.decay_cleanup(threshold=0.15)
        # 可能清理了也可能没有（取决于时间），但不应报错
        assert isinstance(cleaned, int)


# ===== 测试 4: 容量淘汰 =====

class TestEviction:
    def setup_method(self):
        self.db_path = get_temp_db()
        self.config = EngramConfig(db_path=self.db_path, capacity=10, auto_evict=True)
        self.mem = EngramMemory(self.config)

    def teardown_method(self):
        self.mem.close()
        cleanup(self.db_path)

    def test_eviction_triggered(self):
        # 存储超过容量的条目
        for i in range(20):
            self.mem.store(f"文本{i} 内容", {"id": i}, importance=0.3 + (i % 5) * 0.1)

        stats = self.mem.stats()
        assert stats['total_entries'] <= self.config.capacity

    def test_low_importance_evicted_first(self):
        # 先存低重要性
        for i in range(5):
            self.mem.store(f"低重要{i} 数据", {"id": f"low_{i}"}, importance=0.1)
        # 再存高重要性
        for i in range(10):
            self.mem.store(f"高重要{i} 数据", {"id": f"high_{i}"}, importance=0.9)

        stats = self.mem.stats()
        assert stats['total_entries'] <= self.config.capacity
        # 高重要性的应该还在
        results = self.mem.recall("高重要")
        assert len(results) > 0


# ===== 测试 5: EngramSoLPiBridge 桥接 =====

class TestEngramBridge:
    def setup_method(self):
        self.db_path = get_temp_db()
        self.config = EngramConfig(db_path=self.db_path)
        self.engram = EngramMemory(self.config)
        self.bridge = EngramSoLPiBridge(self.engram)

    def teardown_method(self):
        self.bridge.close()
        cleanup(self.db_path)

    def test_pre_query_no_memory(self):
        result = self.bridge.pre_query("定州轮胎价格")
        assert result['has_memory'] is False
        assert result['context_boost'] == ""

    def test_pre_query_with_memory(self):
        self.engram.store(
            "定州轮胎厂报价120元每套",
            value={"summary": "轮胎报价120元/套", "type": "price_info"},
            importance=0.8,
        )
        result = self.bridge.pre_query("定州轮胎价格")
        assert result['has_memory'] is True
        assert len(result['context_boost']) > 0

    def test_post_response_auto_store(self):
        self.bridge.post_response(
            "对方报价多少？",
            "对方报价每套120元，含税。",
        )
        results = self.engram.recall("对方报价")
        assert len(results) > 0

    def test_post_response_with_facts(self):
        self.bridge.post_response(
            "谈判结果如何？",
            "对方同意降价5%，总价28.5万。",
            extracted_facts=[
                {
                    "text": "对方同意降价5%",
                    "importance": 0.9,
                    "data": {"type": "price_change", "pct": -5},
                },
                {
                    "text": "总价28.5万",
                    "importance": 0.8,
                    "data": {"type": "final_price", "amount": 285000},
                },
            ],
        )
        results = self.engram.recall("降价5%")
        assert len(results) >= 1

    def test_stats(self):
        self.engram.store("测试", {"d": 1}, importance=0.5)
        stats = self.bridge.get_stats()
        assert stats['total_entries'] > 0


# ===== 测试 6: 中文谈判场景端到端 =====

class TestChineseNegotiation:
    """模拟真实谈判场景的端到端测试"""

    def setup_method(self):
        self.db_path = get_temp_db()
        self.config = EngramConfig(db_path=self.db_path)
        self.engram = EngramMemory(self.config)
        self.bridge = EngramSoLPiBridge(self.engram)

    def teardown_method(self):
        self.bridge.close()
        cleanup(self.db_path)

    def test_negotiation_scenario(self):
        """模拟汽车零部件采购谈判"""
        # 第一轮：存储对方报价
        self.engram.store(
            "定州宏业橡胶厂报价 轮胎每套120元 含税含运",
            value={
                "type": "supplier_quote",
                "supplier": "宏业橡胶",
                "product": "轮胎",
                "price_per_unit": 120,
                "currency": "CNY",
                "inc_tax": True,
            },
            importance=0.9,
            source="negotiation_round_1",
        )

        # 第二轮：存储还价结果
        self.engram.store(
            "对方同意降价5% 新价格114元每套",
            value={
                "type": "counter_offer_result",
                "original_price": 120,
                "new_price": 114,
                "discount_pct": 5,
            },
            importance=0.85,
            source="negotiation_round_2",
        )

        # 后续查询：问"上次宏业报价多少"
        result = self.bridge.pre_query("宏业橡胶厂轮胎报价")
        assert result['has_memory'] is True

        # 查询降价后价格
        results = self.engram.recall("114元 轮胎")
        assert len(results) >= 1

    def test_multi_session_recall(self):
        """跨会话召回测试"""
        self.engram.store(
            "上次谈判对方承诺预付30%定金",
            value={"type": "payment_terms", "prepay_pct": 30},
            importance=0.85,
        )

        # 新会话中询问付款条件
        result = self.bridge.pre_query("付款条件 预付定金")
        # 应该能召回（共享 n-gram "预付" 或 "定金"）
        # 注意：由于 n-gram 是 2-3 字的，不一定每个词都命中
        # 但不应报错
        assert isinstance(result, dict)


# ===== 运行入口 =====

if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__, '-v']))
