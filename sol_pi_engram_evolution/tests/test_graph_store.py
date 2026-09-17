"""
阶段 1：图谱存储测试
验证 SQLite 存储、CRUD、统计
"""

import importlib.util
import os
import os.path as osp
import tempfile


def _load_module(name, rel_path):
    path = osp.join(
        osp.dirname(osp.abspath(__file__)), "..", rel_path
    )
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_graph_store = _load_module("graph_store", "graph_store.py")


def _make_store():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    return _graph_store.GraphStore(db_path=path), path


def test_add_task_node():
    """测试添加任务节点"""
    store, _ = _make_store()
    node = store.add_task_node(
        title="测试任务",
        description="测试描述",
        status="completed",
        priority=5,
        source_pointer="archive://test.db",
        confidence=0.9,
    )
    assert node is not None
    assert node['node_id'].startswith('task-')
    assert node['node_type'] == 'task'
    assert node['title'] == '测试任务'
    assert node['status'] == 'completed'
    assert node['priority'] == 5
    assert node['confidence'] == 0.9
    store.close()
    print("✓ Add task node passed")


def test_add_event_node():
    """测试添加事件节点"""
    store, _ = _make_store()
    node = store.add_event_node(
        title="测试事件",
        description="测试事件描述",
        event_type="decision",
        entities=["实体 A", "实体 B"],
        outcome="结果：成功",
        source_pointer="archive://test.db",
        confidence=0.85,
    )
    assert node is not None
    assert node['node_id'].startswith('event-')
    assert node['node_type'] == 'event'
    assert node['title'] == '测试事件'
    assert node['event_type'] == 'decision'
    assert node['entities'] == ["实体 A", "实体 B"]
    assert node['outcome'] == '结果：成功'
    store.close()
    print("✓ Add event node passed")


def test_add_relation():
    """测试添加关系"""
    store, _ = _make_store()

    # 先添加两个节点
    task = store.add_task_node(title="任务 A", description="测试任务 A")
    event = store.add_event_node(title="事件 B", description="测试事件 B",
                                  event_type="decision", outcome="成功")

    rel = store.add_relation(
        source_node_id=task['node_id'],
        target_node_id=event['node_id'],
        relation_type="depends_on",
        weight=0.8,
        description="任务 A 依赖事件 B",
        confidence=0.9,
    )
    assert rel is not None
    assert rel['relation_id'].startswith('rel-')
    assert rel['source_node_id'] == task['node_id']
    assert rel['target_node_id'] == event['node_id']
    assert rel['relation_type'] == 'depends_on'
    assert rel['weight'] == 0.8
    store.close()
    print("✓ Add relation passed")


def test_get_node_by_id_task():
    """测试根据 ID 获取任务节点"""
    store, _ = _make_store()
    node = store.add_task_node(title="查找任务", description="用于查找测试")
    retrieved = store.get_node_by_id(node['node_id'])
    assert retrieved is not None
    assert retrieved['node_id'] == node['node_id']
    assert retrieved['title'] == "查找任务"
    assert retrieved['node_type'] == 'task'
    store.close()
    print("✓ Get node by ID (task) passed")


def test_get_node_by_id_event():
    """测试根据 ID 获取事件节点"""
    store, _ = _make_store()
    node = store.add_event_node(title="查找事件", event_type="outcome", outcome="完成")
    retrieved = store.get_node_by_id(node['node_id'])
    assert retrieved is not None
    assert retrieved['node_type'] == 'event'
    assert retrieved['title'] == "查找事件"
    store.close()
    print("✓ Get node by ID (event) passed")


def test_get_task_node_by_title():
    """测试根据标题查找任务节点"""
    store, _ = _make_store()
    store.add_task_node(title="唯一标题", description="测试")
    found = store.get_task_node_by_title("唯一标题")
    assert found is not None
    assert found['title'] == "唯一标题"
    not_found = store.get_task_node_by_title("不存在标题")
    assert not_found is None
    store.close()
    print("✓ Get task node by title passed")


def test_get_event_node_by_title():
    """测试根据标题查找事件节点"""
    store, _ = _make_store()
    store.add_event_node(title="唯一事件", event_type="decision", outcome="yes")
    found = store.get_event_node_by_title("唯一事件")
    assert found is not None
    assert found['title'] == "唯一事件"
    not_found = store.get_event_node_by_title("不存在事件")
    assert not_found is None
    store.close()
    print("✓ Get event node by title passed")


def test_get_relations_for_node():
    """测试获取节点相关关系"""
    store, _ = _make_store()
    task = store.add_task_node(title="任务 X")
    event = store.add_event_node(title="事件 Y", event_type="decision")
    rel1 = store.add_relation(task['node_id'], event['node_id'],
                              relation_type="depends_on")
    rel2 = store.add_relation(event['node_id'], task['node_id'],
                              relation_type="causes")

    rels = store.get_relations_for_node(task['node_id'])
    rel_ids = [r['relation_id'] for r in rels]
    assert rel1['relation_id'] in rel_ids
    assert rel2['relation_id'] in rel_ids

    store.close()
    print("✓ Get relations for node passed")


def test_get_all_nodes():
    """测试获取所有节点"""
    store, _ = _make_store()
    store.add_task_node(title="任务 1")
    store.add_event_node(title="事件 1", event_type="decision")
    store.add_task_node(title="任务 2")
    nodes = store.get_all_nodes()
    assert len(nodes) == 3
    types = [n['node_type'] for n in nodes]
    assert types.count('task') == 2
    assert types.count('event') == 1
    store.close()
    print("✓ Get all nodes passed")


def test_get_node_stats():
    """测试图谱统计"""
    store, _ = _make_store()
    store.add_task_node(title="任务 1")
    store.add_task_node(title="任务 2")
    store.add_event_node(title="事件 1", event_type="decision")
    store.add_relation("task-0", "event-0", relation_type="depends_on")

    stats = store.get_node_stats()
    assert stats['task_count'] == 2
    assert stats['event_count'] == 1
    assert stats['relation_count'] == 1
    assert stats['total_node_count'] == 3

    store.close()
    print("✓ Get node stats passed")


def test_delete_node():
    """测试删除节点"""
    store, _ = _make_store()
    task = store.add_task_node(title="删除任务")
    event = store.add_event_node(title="关联事件", event_type="decision")
    store.add_relation(task['node_id'], event['node_id'],
                       relation_type="depends_on")

    deleted = store.delete_node(task['node_id'])
    assert deleted is True

    # 节点应已删除
    assert store.get_node_by_id(task['node_id']) is None
    # 关联关系也应删除
    rels = store.get_relations_for_node(event['node_id'])
    assert len(rels) == 0

    store.close()
    print("✓ Delete node passed")


def test_delete_relation():
    """测试删除关系"""
    store, _ = _make_store()
    task = store.add_task_node(title="任务")
    event = store.add_event_node(title="事件", event_type="decision")
    rel = store.add_relation(task['node_id'], event['node_id'],
                             relation_type="depends_on")

    deleted = store.delete_relation(rel['relation_id'])
    assert deleted is True
    assert store.get_relation_by_id(rel['relation_id']) is None

    store.close()
    print("✓ Delete relation passed")


def test_close():
    """测试关闭连接"""
    store, db_path = _make_store()
    store.add_task_node(title="测试")
    store.close()
    # 重新打开应可正常工作
    store2 = _graph_store.GraphStore(db_path=db_path)
    nodes = store2.get_all_nodes()
    assert len(nodes) == 1
    store2.close()
    os.unlink(db_path)

    print("✓ Close passed")


if __name__ == "__main__":
    test_add_task_node()
    test_add_event_node()
    test_add_relation()
    test_get_node_by_id_task()
    test_get_node_by_id_event()
    test_get_task_node_by_title()
    test_get_event_node_by_title()
    test_get_relations_for_node()
    test_get_all_nodes()
    test_get_node_stats()
    test_delete_node()
    test_delete_relation()
    test_close()
    print("\n✅ 阶段 1 图谱存储测试全部通过")
