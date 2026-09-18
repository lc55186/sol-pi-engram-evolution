"""
阶段 2：上下文管理器测试
验证检索 → 上下文装配 → 优化触发接口
"""

import importlib.util
import sys
import os
import tempfile


def _load_module(name, rel_path):
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", rel_path
    )
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_graph_store = _load_module("graph_store", "graph_store.py")
_graph_retriever = _load_module("graph_retriever", "graph_retriever.py")
_context_manager = _load_module("context_manager", "context_manager.py")


def _make_store():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    store = _graph_store.GraphStore(db_path=path)

    store.add_task_node(
        title="任务 A：设计数据库 schema",
        description="设计用户表和订单表",
        status="completed",
        priority=5,
    )
    store.add_task_node(
        title="任务 B：实现 API 接口",
        description="实现用户管理 REST API",
        status="in_progress",
        priority=4,
    )
    store.add_event_node(
        title="决策：选择 PostgreSQL",
        description="选择 PostgreSQL 作为数据库",
        event_type="decision",
        entities=["PostgreSQL"],
        outcome="确定使用 PostgreSQL",
    )
    store.add_relation(
        source_node_id="task-a",
        target_node_id="task-b",
        relation_type="depends_on",
        weight=0.9,
    )
    task_a = store.get_task_node_by_title("任务 A：设计数据库 schema")
    task_b = store.get_task_node_by_title("任务 B：实现 API 接口")
    event_dec = store.get_event_node_by_title("决策：选择 PostgreSQL")
    if task_a and task_b and event_dec:
        store.add_relation(
            source_node_id=task_a['node_id'],
            target_node_id=task_b['node_id'],
            relation_type="depends_on",
            weight=0.9,
        )
        store.add_relation(
            source_node_id=task_b['node_id'],
            target_node_id=event_dec['node_id'],
            relation_type="during",
            weight=0.7,
        )
    return store


def test_build_context():
    """测试构建上下文：检索 + 摘要 + 标志"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)
    cm = _context_manager.ContextManager(
        retriever,
        config={'context_limit': 5}
    )

    ctx = cm.build_context("数据库 schema 设计")

    assert ctx['query'] == "数据库 schema 设计"
    assert len(ctx['relevant_nodes']) >= 1
    assert len(ctx['nodes_summary']) >= 1
    assert ctx['node_count'] == len(ctx['relevant_nodes'])
    assert ctx['action_fusion_ready'] is True  # 有节点
    assert isinstance(ctx['total_tokens_estimate'], int)

    store.close()
    print("✓ Build context passed")


def test_nodes_summary_format():
    """测试节点摘要格式"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)
    cm = _context_manager.ContextManager(retriever)

    ctx = cm.build_context("PostgreSQL")

    summaries = ctx['nodes_summary']
    assert len(summaries) >= 1
    # 摘要应包含节点类型和分数
    for s in summaries:
        assert s.startswith('[')
        assert '(score=' in s

    store.close()
    print("✓ Nodes summary format passed")


def test_compact_trigger_node_count():
    """测试压缩触发：节点数超过阈值"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)
    cm = _context_manager.ContextManager(
        retriever,
        config={'context_limit': 10, 'compact_node_threshold': 3}
    )

    # 插入多个节点
    for i in range(5):
        store.add_task_node(
            title=f"任务 {i}：测试任务",
            description=f"描述 {i}",
            status="completed",
        )

    ctx = cm.build_context("测试")
    # 节点数 7 > 阈值 3，应触发压缩
    assert ctx['compact_trigger'] is True

    store.close()
    print("✓ Compact trigger node count passed")


def test_compact_trigger_query_length():
    """测试压缩触发：查询过长"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)
    cm = _context_manager.ContextManager(
        retriever,
        config={'compact_query_length': 100}
    )

    long_query = "A" * 200
    ctx = cm.build_context(long_query)
    assert ctx['compact_trigger'] is True

    store.close()
    print("✓ Compact trigger query length passed")


def test_apply_action_fusion_interface():
    """测试 action_fusion 接口委托"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)
    cm = _context_manager.ContextManager(retriever)

    ops = [
        {'type': 'edit', 'payload': '修改文件 A'},
        {'type': 'run', 'payload': '运行测试'},
        {'type': 'read', 'payload': '读取结果'},
    ]
    result = cm.apply_action_fusion(ops)
    assert isinstance(result, list)
    assert len(result) >= 0

    store.close()
    print("✓ Apply action fusion interface passed")


def test_apply_compaction_interface():
    """测试 compaction 接口委托"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)
    cm = _context_manager.ContextManager(
        retriever,
        config={'context_limit': 10, 'compact_node_threshold': 3}
    )

    # 插入多个节点触发压缩
    for i in range(5):
        store.add_task_node(
            title=f"任务 {i}：测试任务",
            description=f"描述 {i}",
            status="completed",
        )

    ctx = cm.build_context("测试")
    result = cm.apply_compaction(ctx)
    assert isinstance(result, dict)

    store.close()
    print("✓ Apply compaction interface passed")


if __name__ == "__main__":
    test_build_context()
    test_nodes_summary_format()
    test_compact_trigger_node_count()
    test_compact_trigger_query_length()
    test_apply_action_fusion_interface()
    test_apply_compaction_interface()
    print("\n✅ 阶段 2 上下文管理器测试全部通过")
