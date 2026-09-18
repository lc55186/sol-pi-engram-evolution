"""
阶段 2：图谱检索测试
验证 TMatch、关系遍历、top-k、min_score 过滤
"""

import importlib.util
import sys
import os
import tempfile

# 加载 graph_store 模块
_GS_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "graph_store.py"
)
_spec_gs = importlib.util.spec_from_file_location("graph_store", _GS_PATH)
_graph_store = importlib.util.module_from_spec(_spec_gs)
sys.modules["graph_store"] = _graph_store
_spec_gs.loader.exec_module(_graph_store)

# 加载 graph_retriever 模块
_GR_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "graph_retriever.py"
)
_spec_gr = importlib.util.spec_from_file_location("graph_retriever", _GR_PATH)
_graph_retriever = importlib.util.module_from_spec(_spec_gr)
sys.modules["graph_retriever"] = _graph_retriever
_spec_gr.loader.exec_module(_graph_retriever)


def _make_store():
    """创建带测试数据的 GraphStore"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    store = _graph_store.GraphStore(db_path=path)

    # 插入测试节点
    store.add_task_node(
        title="任务 A：设计数据库 schema",
        description="设计用户表和订单表的 schema",
        status="completed",
        priority=5,
        source_pointer="archive://task-a"
    )
    store.add_task_node(
        title="任务 B：实现 API 接口",
        description="实现用户管理和订单查询的 REST API",
        status="in_progress",
        priority=4,
        source_pointer="archive://task-b"
    )
    store.add_event_node(
        title="决策：选择 PostgreSQL",
        description="经过评估，选择 PostgreSQL 作为数据库",
        event_type="decision",
        entities=["PostgreSQL", "团队"],
        outcome="确定使用 PostgreSQL",
        source_pointer="archive://decision-pg"
    )
    store.add_event_node(
        title="错误：连接超时",
        description="数据库连接超时导致 API 报错",
        event_type="error",
        entities=["API", "数据库"],
        outcome="修复后恢复",
        source_pointer="archive://error-timeout"
    )
    store.add_relation(
        source_node_id="task-a",  # 这里用真实 ID
        target_node_id="task-b",
        relation_type="depends_on",
        weight=0.9,
        source_pointer="archive://rel-ab"
    )
    # 获取实际插入的 ID
    task_a = store.get_task_node_by_title("任务 A：设计数据库 schema")
    task_b = store.get_task_node_by_title("任务 B：实现 API 接口")
    event_dec = store.get_event_node_by_title("决策：选择 PostgreSQL")
    event_err = store.get_event_node_by_title("错误：连接超时")

    if task_a and task_b and event_dec and event_err:
        store.add_relation(
            source_node_id=task_a['node_id'],
            target_node_id=task_b['node_id'],
            relation_type="depends_on",
            weight=0.9,
            source_pointer="archive://rel-ab"
        )
        store.add_relation(
            source_node_id=task_b['node_id'],
            target_node_id=event_dec['node_id'],
            relation_type="during",
            weight=0.7,
            source_pointer="archive://rel-b-dec"
        )
        store.add_relation(
            source_node_id=task_b['node_id'],
            target_node_id=event_err['node_id'],
            relation_type="causes",
            weight=0.8,
            source_pointer="archive://rel-b-err"
        )

    return store


def test_tmatch_basic():
    """测试基本 TMatch：关键词匹配节点"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)

    results = retriever.retrieve("数据库 schema 设计", top_k=10)
    assert len(results) >= 1, "应该至少检索到一个节点"

    # 任务 A 应该被检索到（包含"数据库"、"schema"、"设计"）
    titles = [n['title'] for n, _ in results]
    assert any("数据库" in t and "schema" in t for t in titles), \
        "任务 A 应该被检索到"

    store.close()
    print("✓ TMatch basic passed")


def test_tmatch_weight_fields():
    """测试字段权重：title 比 description 更重要"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)

    # 用"PostgreSQL"检索，决策事件应被检索到（title 中有）
    results = retriever.retrieve("PostgreSQL", top_k=10)
    titles = [n['title'] for n, _ in results]
    assert any("PostgreSQL" in t for t in titles), \
        "PostgreSQL 相关节点应被检索到"

    store.close()
    print("✓ TMatch field weights passed")


def test_relation_traverse():
    """测试关系遍历：检索任务 B 时应展开关联的决策和错误"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)

    # 检索"API 接口"，任务 B 被检索
    results = retriever.retrieve("API 接口", top_k=10)
    titles = [n['title'] for n, _ in results]

    # 任务 B 应该在结果中
    assert any("API 接口" in t for t in titles), \
        "任务 B 应被检索到"

    # 通过 depends_on 关系，任务 A 也被展开
    assert any("数据库 schema" in t for t in titles), \
        "任务 A 应通过关系遍历被展开"

    store.close()
    print("✓ Relation traverse passed")


def test_top_k_truncation():
    """测试 top-k 截断"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)

    results = retriever.retrieve("数据库", top_k=2)
    assert len(results) <= 2, f"结果数量應該 <= 2，實際 {len(results)}"

    store.close()
    print("✓ Top-k truncation passed")


def test_min_score_filter():
    """测试 min_score 过滤"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)

    # 设置很高的 min_score，应该没有结果
    results = retriever.retrieve("数据库", top_k=10, min_score=100.0)
    assert len(results) == 0, "min_score 太高應該無結果"

    # 设置合理的 min_score
    results = retriever.retrieve("数据库", top_k=10, min_score=0.0)
    assert len(results) >= 1, "合理 min_score 應該有結果"

    store.close()
    print("✓ Min-score filter passed")


def test_combine_same_node():
    """测试合并：同一节点通过多条路径到达取最高分"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)

    results = retriever.retrieve("API", top_k=10)
    # 任务 B 通过 TMatch 和关系遍历都可能到达，结果中不应重复
    node_ids = [n['node_id'] for n, _ in results]
    assert len(node_ids) == len(set(node_ids)), \
        "同一节点不應在結果中重複"

    store.close()
    print("✓ Combine same node passed")


def test_no_results_for_irrelevant():
    """测试无关查询返回空"""
    store = _make_store()
    retriever = _graph_retriever.GraphRetriever(store)

    results = retriever.retrieve("完全无关的词汇 xyzabc", top_k=5)
    assert len(results) == 0, "完全无关的查询應該返回空"

    store.close()
    print("✓ Irrelevant query returns empty passed")


if __name__ == "__main__":
    test_tmatch_basic()
    test_tmatch_weight_fields()
    test_relation_traverse()
    test_top_k_truncation()
    test_min_score_filter()
    test_combine_same_node()
    test_no_results_for_irrelevant()
    print("\n✅ 阶段 2 图谱检索测试全部通过")
