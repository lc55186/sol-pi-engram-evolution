"""
阶段 0：图谱 Schema 测试
验证节点类型定义、字段校验、工厂函数
"""

import importlib.util
import os

# 直接从文件路径加载 graph_schema 模块，避免 sys.path 问题
_GRAPH_SCHEMA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "graph_schema.py"
)
if not os.path.exists(_GRAPH_SCHEMA_PATH):
    raise FileNotFoundError(f"graph_schema.py not found at {_GRAPH_SCHEMA_PATH}")

_spec = importlib.util.spec_from_file_location("graph_schema", _GRAPH_SCHEMA_PATH)
_graph_schema = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_graph_schema)

TaskNode = _graph_schema.TaskNode
EventNode = _graph_schema.EventNode
RelationNode = _graph_schema.RelationNode
create_task_node = _graph_schema.create_task_node
create_event_node = _graph_schema.create_event_node
create_relation_node = _graph_schema.create_relation_node


def test_task_node_defaults():
    """测试任务节点默认值"""
    node = TaskNode()
    assert node.task_id != ""
    assert node.status == "not_started"
    assert node.priority == 3
    assert node.confidence == 1.0
    assert node.importance_score == 0.5
    assert node.decay_rate == 0.95
    assert node.related_event_ids == []
    assert node.related_task_ids == []
    print("✓ TaskNode defaults passed")


def test_task_node_validation():
    """测试任务节点字段校验"""
    # 有效节点
    node = create_task_node("test task", status="in_progress", priority=5, confidence=0.9)
    assert node.status == "in_progress"
    assert node.priority == 5
    assert node.confidence == 0.9

    # 非法 status
    try:
        TaskNode(status="invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # 非法 priority
    try:
        TaskNode(priority=10)
        assert False
    except ValueError:
        pass

    # 非法 confidence
    try:
        TaskNode(confidence=1.5)
        assert False
    except ValueError:
        pass

    print("✓ TaskNode validation passed")


def test_event_node_defaults():
    """测试事件节点默认值"""
    node = EventNode()
    assert node.event_id != ""
    assert node.event_type == "other"
    assert node.confidence == 1.0
    assert node.importance_score == 0.5
    assert node.entities == []
    print("✓ EventNode defaults passed")


def test_event_node_validation():
    """测试事件节点字段校验"""
    node = create_event_node("test event", event_type="decision", entities=["A", "B"], outcome="yes")
    assert node.event_type == "decision"
    assert node.entities == ["A", "B"]
    assert node.outcome == "yes"

    try:
        EventNode(event_type="invalid")
        assert False
    except ValueError:
        pass

    print("✓ EventNode validation passed")


def test_relation_node_defaults():
    """测试关系节点默认值"""
    node = RelationNode()
    assert node.relation_id != ""
    assert node.relation_type == "related_to"
    assert node.weight == 0.5
    assert node.confidence == 1.0
    print("✓ RelationNode defaults passed")


def test_relation_node_validation():
    """测试关系节点字段校验"""
    node = create_relation_node("src-1", "tgt-2", "depends_on", weight=0.8, confidence=0.9)
    assert node.source_node_id == "src-1"
    assert node.target_node_id == "tgt-2"
    assert node.relation_type == "depends_on"
    assert node.weight == 0.8
    assert node.confidence == 0.9

    try:
        RelationNode(relation_type="invalid")
        assert False
    except ValueError:
        pass

    try:
        RelationNode(weight=1.5)
        assert False
    except ValueError:
        pass

    print("✓ RelationNode validation passed")


def test_factory_functions():
    """测试工厂函数"""
    task = create_task_node("task1", "desc", "completed", 4, 0.8, "pointer://1")
    assert task.title == "task1"
    assert task.description == "desc"
    assert task.status == "completed"
    assert task.priority == 4
    assert task.confidence == 0.8
    assert task.source_pointer == "pointer://1"

    event = create_event_node("event1", "desc", "outcome", ["E1"], "done", 0.9, "ptr://2")
    assert event.title == "event1"
    assert event.event_type == "outcome"
    assert event.confidence == 0.9
    assert event.source_pointer == "ptr://2"

    rel = create_relation_node("a", "b", "causes", 0.7, "desc", 0.85, "ptr://3")
    assert rel.source_node_id == "a"
    assert rel.target_node_id == "b"
    assert rel.relation_type == "causes"
    assert rel.weight == 0.7
    assert rel.confidence == 0.85

    print("✓ Factory functions passed")


if __name__ == "__main__":
    test_task_node_defaults()
    test_task_node_validation()
    test_event_node_defaults()
    test_event_node_validation()
    test_relation_node_defaults()
    test_relation_node_validation()
    test_factory_functions()
    print("\n✅ 阶段 0 测试全部通过：图谱 Schema 定义完成")
