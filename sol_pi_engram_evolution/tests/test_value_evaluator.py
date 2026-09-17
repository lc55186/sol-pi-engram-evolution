"""
阶段 3：价值评估测试
验证节点价值评估、排序、分层、淘汰
"""

import importlib.util
import os
import os.path as osp
import tempfile
from datetime import datetime

# 固定测试时间：2024年2月1日，避免时间衰减导致分数接近0
TEST_NOW = datetime(2024, 2, 1)


def _load_module(name, rel_path):
    path = osp.join(
        osp.dirname(osp.abspath(__file__)), "..", rel_path
    )
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_graph_store = _load_module("graph_store", "graph_store.py")
_value_evaluator = _load_module("value_evaluator", "value_evaluator.py")


def _make_store():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    return _graph_store.GraphStore(db_path=path), path


def test_evaluate_basic():
    """测试基本价值评估"""
    store, _ = _make_store()
    evaluator = _value_evaluator.ValueEvaluator(store, config={'now': TEST_NOW})

    node = {
        'node_id': 'task-1',
        'node_type': 'task',
        'title': '重要任务',
        'description': '这是一个重要任务',
        'status': 'in_progress',
        'priority': 5,
        'access_count': 10,
        'created_at': '2024-01-01T00:00:00',
        'last_accessed': '2024-01-15T00:00:00',
        'importance_score': 0.8,
        'decay_rate': 0.95,
    }

    score = evaluator.evaluate(node)
    assert 0.0 <= score <= 1.0, f"分数应在 0-1 之间，实际 {score}"
    print(f"  评估分数: {score}")
    print("✓ Evaluate basic passed")


def test_rank_nodes():
    """测试节点排序"""
    store, _ = _make_store()
    evaluator = _value_evaluator.ValueEvaluator(store, config={'now': TEST_NOW})

    nodes = [
        {'node_id': '1', 'node_type': 'task', 'title': '低优先级', 'priority': 1,
         'access_count': 0, 'importance_score': 0.2, 'created_at': '2024-01-01T00:00:00'},
        {'node_id': '2', 'node_type': 'task', 'title': '高优先级', 'priority': 5,
         'access_count': 50, 'importance_score': 0.9, 'created_at': '2024-01-01T00:00:00',
         'last_accessed': '2024-01-20T00:00:00'},
        {'node_id': '3', 'node_type': 'event', 'title': '普通事件',
         'event_type': 'decision', 'access_count': 5, 'importance_score': 0.5,
         'created_at': '2024-01-01T00:00:00'},
    ]

    ranked = evaluator.rank_nodes(nodes)
    assert len(ranked) == 3
    # 高优先级节点应该排在前面
    assert ranked[0][0]['node_id'] == '2', "高优先级节点应排在最前"
    print(f"  排序结果: {[n['title'] for n, _ in ranked]}")
    print("✓ Rank nodes passed")


def test_select_for_compression():
    """测试压缩选择"""
    store, _ = _make_store()
    evaluator = _value_evaluator.ValueEvaluator(store, config={'now': TEST_NOW})

    nodes = [
        {'node_id': '1', 'node_type': 'task', 'title': '高价值', 'priority': 5,
         'access_count': 100, 'importance_score': 0.9, 'created_at': '2024-01-01T00:00:00'},
        {'node_id': '2', 'node_type': 'task', 'title': '中价值', 'priority': 3,
         'access_count': 10, 'importance_score': 0.5, 'created_at': '2024-01-01T00:00:00'},
        {'node_id': '3', 'node_type': 'task', 'title': '低价值', 'priority': 1,
         'access_count': 0, 'importance_score': 0.1, 'created_at': '2024-01-01T00:00:00'},
        {'node_id': '4', 'node_type': 'task', 'title': '极低价值', 'priority': 1,
         'access_count': 0, 'importance_score': 0.05, 'created_at': '2024-01-01T00:00:00'},
    ]

    keep, compress = evaluator.select_for_compression(nodes, compression_ratio=0.5)
    assert len(keep) == 2
    assert len(compress) == 2
    keep_ids = [n['node_id'] for n in keep]
    assert '1' in keep_ids, "高价值节点应保留"
    print(f"  保留: {[n['title'] for n in keep]}")
    print(f"  压缩: {[n['title'] for n in compress]}")
    print("✓ Select for compression passed")


def test_select_for_eviction():
    """测试淘汰选择"""
    store, _ = _make_store()
    evaluator = _value_evaluator.ValueEvaluator(store, config={'now': TEST_NOW})

    nodes = [
        {'node_id': '1', 'node_type': 'task', 'title': '高价值', 'priority': 5,
         'access_count': 100, 'importance_score': 0.9, 'created_at': '2024-01-01T00:00:00'},
        {'node_id': '2', 'node_type': 'task', 'title': '低价值', 'priority': 1,
         'access_count': 0, 'importance_score': 0.05, 'created_at': '2024-01-01T00:00:00'},
    ]

    keep, evict = evaluator.select_for_eviction(nodes, threshold=0.1)
    assert len(evict) >= 1
    evict_ids = [n['node_id'] for n in evict]
    assert '2' in evict_ids, "低价值节点应被淘汰"
    print(f"  保留: {[n['title'] for n in keep]}")
    print(f"  淘汰: {[n['title'] for n in evict]}")
    print("✓ Select for eviction passed")


def test_node_value_tiers():
    """测试节点分层"""
    store, _ = _make_store()
    evaluator = _value_evaluator.ValueEvaluator(store, config={'now': TEST_NOW})

    nodes = [
        {'node_id': '1', 'node_type': 'task', 'title': '高价值', 'priority': 5,
         'access_count': 100, 'importance_score': 0.9, 'created_at': '2024-01-01T00:00:00'},
        {'node_id': '2', 'node_type': 'task', 'title': '中价值', 'priority': 3,
         'access_count': 10, 'importance_score': 0.5, 'created_at': '2024-01-01T00:00:00'},
        {'node_id': '3', 'node_type': 'task', 'title': '低价值', 'priority': 1,
         'access_count': 0, 'importance_score': 0.1, 'created_at': '2024-01-01T00:00:00'},
    ]

    tiers = evaluator.get_node_value_tiers(nodes)
    assert len(tiers['high']) + len(tiers['medium']) + len(tiers['low']) == 3
    print(f"  高价值: {len(tiers['high'])} 个")
    print(f"  中价值: {len(tiers['medium'])} 个")
    print(f"  低价值: {len(tiers['low'])} 个")
    print("✓ Node value tiers passed")


def test_access_frequency_score():
    """测试访问频率得分"""
    store, _ = _make_store()
    evaluator = _value_evaluator.ValueEvaluator(store, config={'now': TEST_NOW})

    node_low = {'node_id': '1', 'node_type': 'task', 'title': '低', 'priority': 3,
                'access_count': 0, 'importance_score': 0.5, 'created_at': '2024-01-01T00:00:00'}
    node_high = {'node_id': '2', 'node_type': 'task', 'title': '高', 'priority': 3,
                 'access_count': 100, 'importance_score': 0.5, 'created_at': '2024-01-01T00:00:00'}

    score_low = evaluator.evaluate(node_low)
    score_high = evaluator.evaluate(node_high)

    assert score_high > score_low, "高访问频率应获得更高分"
    print(f"  低访问分数: {score_low:.3f}")
    print(f"  高访问分数: {score_high:.3f}")
    print("✓ Access frequency score passed")


def test_time_decay_factor():
    """测试时间衰减因子"""
    store, _ = _make_store()
    evaluator = _value_evaluator.ValueEvaluator(store, config={'now': TEST_NOW})

    # 刚刚访问的节点
    recent_node = {
        'node_id': '1', 'node_type': 'task', 'title': '最近', 'priority': 3,
        'access_count': 10, 'importance_score': 0.5,
        'last_accessed': '2024-01-20T00:00:00',
        'created_at': '2024-01-01T00:00:00',
        'decay_rate': 0.95,
    }

    # 长期未访问的节点
    old_node = {
        'node_id': '2', 'node_type': 'task', 'title': '陈旧', 'priority': 3,
        'access_count': 10, 'importance_score': 0.5,
        'last_accessed': '2023-01-01T00:00:00',
        'created_at': '2023-01-01T00:00:00',
        'decay_rate': 0.95,
    }

    score_recent = evaluator.evaluate(recent_node)
    score_old = evaluator.evaluate(old_node)

    assert score_recent > score_old, "最近访问的节点应获得更高分"
    print(f"  最近节点分数: {score_recent:.3f}")
    print(f"  陈旧节点分数: {score_old:.3f}")
    print("✓ Time decay factor passed")


def test_critical_type_weight():
    """测试关键类型加权"""
    store, _ = _make_store()
    evaluator = _value_evaluator.ValueEvaluator(store, config={'now': TEST_NOW})

    decision_node = {
        'node_id': '1', 'node_type': 'event', 'title': '决策',
        'event_type': 'decision', 'priority': 3,
        'access_count': 10, 'importance_score': 0.5,
        'created_at': '2024-01-01T00:00:00',
    }
    other_node = {
        'node_id': '2', 'node_type': 'event', 'title': '其他',
        'event_type': 'other', 'priority': 3,
        'access_count': 10, 'importance_score': 0.5,
        'created_at': '2024-01-01T00:00:00',
    }

    score_decision = evaluator.evaluate(decision_node)
    score_other = evaluator.evaluate(other_node)

    assert score_decision >= score_other, "决策类型不应低于其他类型"
    print(f"  决策类型分数: {score_decision:.3f}")
    print(f"  其他类型分数: {score_other:.3f}")
    print("✓ Critical type weight passed")


def test_relation_density_score():
    """测试关联密度得分"""
    store, db_path = _make_store()
    evaluator = _value_evaluator.ValueEvaluator(store, config={'now': TEST_NOW})

    # 创建带关系的节点
    task1 = store.add_task_node(title="中心任务")
    task2 = store.add_task_node(title="关联任务 1")
    task3 = store.add_task_node(title="关联任务 2")
    event1 = store.add_event_node(title="关联事件 1", event_type="decision", outcome="是")

    store.add_relation(task1['node_id'], task2['node_id'], relation_type="depends_on")
    store.add_relation(task1['node_id'], task3['node_id'], relation_type="depends_on")
    store.add_relation(task1['node_id'], event1['node_id'], relation_type="during")

    # 重新获取完整节点
    task1_full = store.get_node_by_id(task1['node_id'])
    task2_full = store.get_node_by_id(task2['node_id'])

    score_center = evaluator.evaluate(task1_full)
    score_peripheral = evaluator.evaluate(task2_full)

    assert score_center > score_peripheral, "中心节点应获得更高分"
    print(f"  中心节点分数: {score_center:.3f}")
    print(f"  边缘节点分数: {score_peripheral:.3f}")

    store.close()
    os.unlink(db_path)
    print("✓ Relation density score passed")


if __name__ == "__main__":
    test_evaluate_basic()
    test_rank_nodes()
    test_select_for_compression()
    test_select_for_eviction()
    test_node_value_tiers()
    test_access_frequency_score()
    test_time_decay_factor()
    test_critical_type_weight()
    test_relation_density_score()
    print("\n✅ 阶段 3 价值评估测试全部通过")
