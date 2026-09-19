#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Search Engine Manager Tests"""
import os
import sys
import time
import json
import random
import tempfile
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from search_manager import (
    SearchEngineManager, SearchEngine, EngineStatus, SearchResult,
    get_search_manager, nous_meituan_backend
)


def test_engine_status():
    """测试引擎状态"""
    status = EngineStatus(name="test_engine")
    assert status.is_healthy is True
    assert status.is_available is True
    assert status.success_rate == 1.0
    assert status.total_requests == 0
    
    # 模拟失败
    status.consecutive_failures = 3
    status.total_requests = 5
    status.successful_requests = 2
    assert status.success_rate == 0.4
    
    print("  ✓ EngineStatus works correctly")


def test_search_engine():
    """测试搜索引擎定义"""
    engine = SearchEngine(
        name="test_engine",
        priority=1,
        weight=5,
        max_failures=3,
        cooldown_seconds=60
    )
    
    assert engine.name == "test_engine"
    assert engine.status.name == "test_engine"
    assert engine.enabled is True
    
    print("  ✓ SearchEngine definition works correctly")


def test_engine_priority_sort():
    """测试引擎优先级排序"""
    manager = SearchEngineManager()
    
    # 清空默认引擎，只注册测试引擎
    manager.engines = {}
    
    # 注册多个引擎
    engines = [
        SearchEngine(name="engine_a", priority=3),
        SearchEngine(name="engine_b", priority=1),
        SearchEngine(name="engine_c", priority=2),
    ]
    
    for e in engines:
        manager.engines[e.name] = e
    
    available = manager.get_available_engines()
    assert len(available) == 3
    assert available[0].name == "engine_b"  # priority=1
    assert available[1].name == "engine_c"  # priority=2
    assert available[2].name == "engine_a"  # priority=3
    
    print("  ✓ Engine priority sorting works correctly")


def test_weighted_selection():
    """测试加权随机选择"""
    manager = SearchEngineManager()
    
    # 清空默认引擎
    manager.engines = {
        "engine_a": SearchEngine(name="engine_a", priority=1, weight=1),
        "engine_b": SearchEngine(name="engine_b", priority=2, weight=3),
    }
    
    # 统计100次选择结果
    counts = {"engine_a": 0, "engine_b": 0}
    for _ in range(100):
        engine = manager.select_engine(strategy="weighted")
        counts[engine.name] += 1
    
    # engine_b 权重更高，应该被选中更多次
    assert counts["engine_b"] > counts["engine_a"]
    
    print("  ✓ Weighted selection works correctly")


def test_cooldown_and_recovery():
    """测试冷却和恢复"""
    engine = SearchEngine(
        name="test_engine",
        priority=1,
        max_failures=2,
        cooldown_seconds=1
    )
    
    # 模拟失败
    engine.status.consecutive_failures = 2
    engine.status.is_healthy = False
    from datetime import datetime, timedelta
    engine.status.cooldown_until = datetime.now() + timedelta(seconds=1)
    
    assert engine.status.is_available is False
    
    # 等待冷却
    time.sleep(1.1)
    assert engine.status.is_available is True
    
    print("  ✓ Cooldown and recovery works correctly")


def test_cache_mechanism():
    """测试缓存机制"""
    manager = SearchEngineManager()
    
    # 手动缓存一个结果
    cache_key = manager._get_cache_key("test query", 5)
    result = SearchResult(
        engine="test",
        query="test query",
        results=[{"title": "test"}],
        latency_ms=100.0
    )
    manager._save_to_cache(cache_key, result)
    
    # 从缓存获取
    cached = manager._get_from_cache(cache_key)
    assert cached is not None
    assert cached.is_cached is True
    assert cached.results[0]["title"] == "test"
    
    # 测试不同 key 不命中
    assert manager._get_from_cache("nonexistent_key") is None
    
    print("  ✓ Cache mechanism works correctly")


def test_cache_ttl():
    """测试缓存过期"""
    manager = SearchEngineManager()
    manager.cache_ttl_seconds = 1  # 1秒过期
    
    cache_key = manager._get_cache_key("test", 5)
    result = SearchResult(engine="test", query="test", results=[], latency_ms=0)
    manager._save_to_cache(cache_key, result)
    
    # 未过期
    assert manager._get_from_cache(cache_key) is not None
    
    # 等待过期
    time.sleep(1.5)
    assert manager._get_from_cache(cache_key) is None
    
    print("  ✓ Cache TTL works correctly")


def test_status_report():
    """测试状态报告"""
    manager = SearchEngineManager()
    
    report = manager.get_status_report()
    
    assert "timestamp" in report
    assert "total_engines" in report
    assert "healthy_engines" in report
    assert "cache_size" in report
    assert "engines" in report
    
    assert report["total_engines"] > 0
    
    print("  ✓ Status report works correctly")


def test_register_backend():
    """测试后端注册"""
    manager = SearchEngineManager()
    
    def mock_backend(query, limit, config):
        return [{"title": "mock result"}]
    
    manager.register_backend("mock_engine", mock_backend)
    
    assert "mock_engine" in manager._backends
    
    # 调用后端
    result = manager._backends["mock_engine"]("test", 5, {})
    assert result[0]["title"] == "mock result"
    
    print("  ✓ Backend registration works correctly")


def test_search_with_fallback():
    """测试搜索故障转移"""
    manager = SearchEngineManager()
    manager.engines = {}
    
    call_order = []
    
    def failing_backend(query, limit, config):
        call_order.append("failing")
        raise Exception("Search failed")
    
    def success_backend(query, limit, config):
        call_order.append("success")
        return [{"title": "fallback result"}]
    
    # 注册两个引擎
    manager.engines["primary"] = SearchEngine(name="primary", priority=1)
    manager.engines["fallback"] = SearchEngine(name="fallback", priority=2)
    
    manager._backends["primary"] = failing_backend
    manager._backends["fallback"] = success_backend
    
    result = manager.search("test query", limit=5)
    
    assert result is not None
    assert result.engine == "fallback"
    assert result.results[0]["title"] == "fallback result"
    assert "failing" in call_order
    assert "success" in call_order
    
    print("  ✓ Search with fallback works correctly")


def test_parallel_search():
    """测试并行搜索"""
    manager = SearchEngineManager()
    manager.engines = {}
    
    results_collector = []
    
    def backend_a(query, limit, config):
        time.sleep(0.1)
        return [{"title": "result A", "source": "a"}]
    
    def backend_b(query, limit, config):
        time.sleep(0.05)
        return [{"title": "result B", "source": "b"}]
    
    manager.engines["a"] = SearchEngine(name="a", priority=1)
    manager.engines["b"] = SearchEngine(name="b", priority=2)
    manager._backends["a"] = backend_a
    manager._backends["b"] = backend_b
    
    results = manager.parallel_search("test", limit=5, engines=["a", "b"])
    
    assert len(results) == 2
    engines_used = {r.engine for r in results}
    assert engines_used == {"a", "b"}
    
    print("  ✓ Parallel search works correctly")


def test_singleton_manager():
    """测试单例模式"""
    manager1 = get_search_manager()
    manager2 = get_search_manager()
    
    assert manager1 is manager2
    
    print("  ✓ Singleton pattern works correctly")


def test_config_persistence():
    """测试配置持久化"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "cache_ttl_seconds": 600,
            "engines": [
                {
                    "name": "custom_engine",
                    "priority": 1,
                    "enabled": True,
                    "weight": 10,
                    "max_failures": 5,
                    "cooldown_seconds": 120,
                    "config": {"api_key": "test_key"}
                }
            ]
        }
        json.dump(config, f)
        config_path = f.name
    
    try:
        manager = SearchEngineManager(config_path)
        
        assert "custom_engine" in manager.engines
        assert manager.engines["custom_engine"].priority == 1
        assert manager.engines["custom_engine"].weight == 10
        assert manager.cache_ttl_seconds == 600
        
        print("  ✓ Config persistence works correctly")
    finally:
        os.unlink(config_path)


def test_thread_safety():
    """测试线程安全"""
    manager = SearchEngineManager()
    
    def mock_backend(query, limit, config):
        time.sleep(random.random() * 0.01)
        return [{"title": f"result for {query}"}]
    
    for i in range(5):
        manager.engines[f"engine_{i}"] = SearchEngine(name=f"engine_{i}", priority=i)
        manager._backends[f"engine_{i}"] = mock_backend
    
    results = []
    errors = []
    
    def worker(query):
        try:
            result = manager.search(query, limit=5, use_cache=False)
            if result:
                results.append(result)
        except Exception as e:
            errors.append(str(e))
    
    threads = []
    for i in range(20):
        thread = threading.Thread(target=worker, args=(f"query_{i}",))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join(timeout=10)
    
    assert len(results) == 20
    assert len(errors) == 0
    
    print("  ✓ Thread safety works correctly")


import random


if __name__ == "__main__":
    print("=" * 60)
    print("Search Engine Manager Tests")
    print("=" * 60)
    
    test_engine_status()
    test_search_engine()
    test_engine_priority_sort()
    test_weighted_selection()
    test_cooldown_and_recovery()
    test_cache_mechanism()
    test_cache_ttl()
    test_status_report()
    test_register_backend()
    test_search_with_fallback()
    test_parallel_search()
    test_singleton_manager()
    test_config_persistence()
    test_thread_safety()
    
    print("\n✅ All search engine manager tests passed")
