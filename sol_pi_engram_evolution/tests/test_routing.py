"""
阶段 4：短对话轻量路由测试
验证路由决策 lightweight / standard / full_graph
"""

import importlib.util
import sys
import os
import os.path as osp
import tempfile


def _load_module(name, rel_path):
    path = osp.join(
        osp.dirname(osp.abspath(__file__)), "..", rel_path
    )
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_graph_store = _load_module("graph_store", "graph_store.py")
_routing = _load_module("routing", "routing.py")


def _make_store():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    return _graph_store.GraphStore(db_path=path), path


def test_lightweight_short_conversation():
    """测试 lightweight 路由：极短对话"""
    store, _ = _make_store()
    router = _routing.Router(store)

    messages = [
        {'role': 'user', 'content': '你好'},
        {'role': 'assistant', 'content': '你好！有什么可以帮你的吗？'},
    ]

    result = router.route(messages, "你好")
    assert result == "lightweight", f"预期 lightweight，实际 {result}"

    store.close()
    print("✓ Lightweight short conversation passed")


def test_standard_medium_conversation():
    """测试 standard 路由：中等长度对话 + 复杂度信号"""
    store, _ = _make_store()
    router = _routing.Router(store)

    messages = [
        {'role': 'user', 'content': '你好'},
        {'role': 'assistant', 'content': '你好！有什么可以帮你的吗？'},
        {'role': 'user', 'content': '我想了解一下数据库'},
        {'role': 'assistant', 'content': '数据库是用于存储和管理数据的系统...'},
        {'role': 'user', 'content': '有哪些类型？'},
        {'role': 'assistant', 'content': '主要有关系型数据库和非关系型数据库...'},
        {'role': 'user', 'content': '我想设计一个数据库系统架构，需要包含索引优化、查询优化、缓存策略'},
        {'role': 'assistant', 'content': '好的，让我帮你设计一个完整的数据库架构...'},
        {'role': 'user', 'content': '还需要考虑高可用和高并发场景，请给出详细的实现方案和部署步骤'},
    ]

    result = router.route(messages, "还需要考虑高可用和高并发场景，请给出详细的实现方案和部署步骤")
    assert result == "standard", f"预期 standard，实际 {result}"

    store.close()
    print("✓ Standard medium conversation passed")


def test_full_graph_complex_query():
    """测试 full_graph 路由：复杂查询 + 图谱相关性高"""
    store, db_path = _make_store()

    # 插入图谱节点，使查询与图谱高度相关
    for i in range(10):
        store.add_task_node(
            title="数据库性能优化任务",
            description="数据库性能优化",
            priority=3,
        )

    router = _routing.Router(store)

    messages = [
        {'role': 'user', 'content': '你好'},
        {'role': 'assistant', 'content': '你好！有什么可以帮你的吗？'},
        {'role': 'user', 'content': '数据库性能优化方案'},
        {'role': 'assistant', 'content': '我来帮你分析数据库性能优化的方案...'},
        {'role': 'user', 'content': '索引优化、查询优化、缓存策略等方面'},
        {'role': 'assistant', 'content': '好的，让我详细分析这几个方面...'},
        {'role': 'user', 'content': '我需要设计一个完整的数据库架构优化系统'},
    ]

    result = router.route(messages, "数据库性能优化：我需要设计一个完整的数据库架构优化系统，包含索引优化、查询优化、缓存策略")
    assert result == "full_graph", f"预期 full_graph，实际 {result}"

    store.close()
    os.unlink(db_path)
    print("✓ Full graph complex query passed")


def test_lightweight_no_graph():
    """测试 lightweight 路由：无图谱节点时"""
    store, _ = _make_store()
    router = _routing.Router(store)

    # 空图谱
    messages = [
        {'role': 'user', 'content': '今天天气怎么样？'},
        {'role': 'assistant', 'content': '我不提供天气查询服务...'},
    ]

    result = router.route(messages, "今天天气怎么样？")
    assert result == "lightweight", f"预期 lightweight，实际 {result}"

    store.close()
    print("✓ Lightweight no graph passed")


def test_routing_info():
    """测试详细路由信息"""
    store, _ = _make_store()
    router = _routing.Router(store)

    messages = [
        {'role': 'user', 'content': '你好'},
        {'role': 'assistant', 'content': '你好！'},
    ]

    info = router.get_routing_info(messages, "你好")
    assert 'strategy' in info
    assert 'message_count' in info
    assert 'complexity_score' in info
    assert 'graph_relevance' in info

    store.close()
    print("✓ Routing info passed")


def test_custom_thresholds():
    """测试自定义阈值"""
    store, _ = _make_store()
    router = _routing.Router(store, config={
        'short_message_threshold': 5,
        'long_message_threshold': 20,
    })

    messages = [
        {'role': 'user', 'content': 'msg1'},
        {'role': 'assistant', 'content': 'resp1'},
        {'role': 'user', 'content': 'msg2'},
        {'role': 'assistant', 'content': 'resp2'},
        {'role': 'user', 'content': 'msg3'},
    ]

    result = router.route(messages, "msg3")
    # 5条消息，短阈值为5，应走 lightweight
    assert result == "lightweight", f"预期 lightweight（短阈值=5），实际 {result}"

    store.close()
    print("✓ Custom thresholds passed")


def test_complexity_score():
    """测试复杂度评分"""
    store, _ = _make_store()
    router = _routing.Router(store)

    # 简单查询
    simple_score = router._complexity_score("你好")
    # 复杂查询
    complex_score = router._complexity_score(
        "帮我设计一个完整的数据库系统架构，"
        "包含索引优化、查询优化、缓存策略、读写分离等方面，"
        "需要考虑高可用和高并发场景？请给出详细的实现方案和配置部署步骤。"
    )

    assert complex_score > simple_score, "复杂查询分数应高于简单查询"

    store.close()
    print("✓ Complexity score passed")


def test_graph_relevance():
    """测试图谱相关性检查"""
    store, db_path = _make_store()
    router = _routing.Router(store)

    # 空图谱
    relevance_empty = router._check_graph_relevance("数据库优化")

    # 插入相关节点
    store.add_task_node(title="数据库性能优化", description="关于索引优化的任务")
    store.add_event_node(title="决策：选择 PostgreSQL", event_type="decision", outcome="已决策")

    relevance_with_graph = router._check_graph_relevance("数据库性能优化")

    assert relevance_with_graph >= relevance_empty

    store.close()
    os.unlink(db_path)
    print("✓ Graph relevance passed")


def test_route_conversation_function():
    """测试便捷函数"""
    store, _ = _make_store()
    result = _routing.route_conversation(
        [{'role': 'user', 'content': '你好'}],
        "你好",
        store=store
    )
    assert result in ("lightweight", "standard", "full_graph")
    store.close()
    print("✓ Route conversation function passed")


if __name__ == "__main__":
    test_lightweight_short_conversation()
    test_standard_medium_conversation()
    test_full_graph_complex_query()
    test_lightweight_no_graph()
    test_routing_info()
    test_custom_thresholds()
    test_complexity_score()
    test_graph_relevance()
    test_route_conversation_function()
    print("\n✅ 阶段 4 短对话轻量路由测试全部通过")
