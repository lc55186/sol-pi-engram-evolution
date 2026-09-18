"""
阶段 5：自主演进接口测试
验证经验记录、历史检索、决策指导、渐进更新
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
_evolution = _load_module("evolution_interface", "evolution_interface.py")


def _make_store():
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    return _graph_store.GraphStore(db_path=path), path


def test_record_optimization():
    """测试记录优化决策"""
    store, db_path = _make_store()
    interface = _evolution.EvolutionInterface(store)

    step = _evolution.EvolutionStep(
        step_type="action_fusion",
        action="合并 edit+run 操作",
        result="成功减少 1 次模型往返",
        confidence=0.85,
        metadata={"tokens_saved": 200},
    )

    result = interface.record_optimization(step)
    assert result is True, "记录应成功"

    # 验证写入
    history = interface.get_optimization_history()
    assert len(history) >= 1, "历史记录应至少 1 条"

    store.close()
    os.unlink(db_path)
    print("✓ Record optimization passed")


def test_record_low_confidence():
    """测试低置信度不记录"""
    store, db_path = _make_store()
    interface = _evolution.EvolutionInterface(store)

    step = _evolution.EvolutionStep(
        step_type="action_fusion",
        action="不可靠操作",
        result="测试",
        confidence=0.3,  # 低于默认阈值 0.5
    )

    result = interface.record_optimization(step)
    assert result is False, "低置信度不应记录"

    store.close()
    os.unlink(db_path)
    print("✓ Record low confidence passed")


def test_get_optimization_history():
    """测试获取优化历史"""
    store, db_path = _make_store()
    interface = _evolution.EvolutionInterface(store)

    # 写入多条记录
    for i in range(5):
        step = _evolution.EvolutionStep(
            step_type="action_fusion",
            action=f"操作 {i}",
            result=f"结果 {i}",
            confidence=0.8,
        )
        interface.record_optimization(step)

    history = interface.get_optimization_history(limit=3)
    assert len(history) == 3, f"应返回 3 条，实际 {len(history)}"

    # 按时间倒序
    for i in range(len(history) - 1):
        assert history[i]['created_at'] >= history[i + 1]['created_at'], "应按时间倒序"

    store.close()
    os.unlink(db_path)
    print("✓ Get optimization history passed")


def test_get_decision_guidance():
    """测试获取决策指导"""
    store, db_path = _make_store()
    interface = _evolution.EvolutionInterface(store)

    # 写入一些历史
    for i in range(5):
        step = _evolution.EvolutionStep(
            step_type="compaction",
            action="上下文压缩",
            result=f"token 减少 {i * 100}",
            confidence=0.9,
        )
        interface.record_optimization(step)

    guidance = interface.get_decision_guidance("上下文压缩")

    assert 'relevant_history' in guidance
    assert 'suggestions' in guidance
    assert 'confidence' in guidance

    store.close()
    os.unlink(db_path)
    print("✓ Get decision guidance passed")


def test_search_relevant_history():
    """测试搜索相关历史"""
    store, db_path = _make_store()
    interface = _evolution.EvolutionInterface(store)

    # 写入两条不同类型的记录
    interface.record_optimization(_evolution.EvolutionStep(
        step_type="action_fusion", action="编辑加测试合并", result="成功减少往返", confidence=0.9
    ))
    interface.record_optimization(_evolution.EvolutionStep(
        step_type="compaction", action="上下文压缩", result="节省 token", confidence=0.9
    ))

    # 搜索与"编辑"相关的（使用 action 中的关键词）
    relevant = interface._search_relevant_history("编辑")
    assert len(relevant) >= 1, f"应至少找到 1 条相关记录，实际 {len(relevant)}"

    store.close()
    os.unlink(db_path)
    print("✓ Search relevant history passed")


def test_evaluate_evolution_progress():
    """测试评估进化进度"""
    store, db_path = _make_store()
    interface = _evolution.EvolutionInterface(store)

    # 空状态
    progress = interface.evaluate_evolution_progress()
    assert progress['status'] == 'no_history'

    # 写入记录
    for i in range(15):
        step = _evolution.EvolutionStep(
            step_type="action_fusion",
            action=f"操作 {i}",
            result="成功",
            confidence=0.8,
        )
        interface.record_optimization(step)

    progress = interface.evaluate_evolution_progress()
    assert progress['status'] in ('active', 'warming_up')
    assert progress['total_records'] == 15

    store.close()
    os.unlink(db_path)
    print("✓ Evaluate evolution progress passed")


def test_incremental_update():
    """测试渐进更新"""
    store, db_path = _make_store()
    interface = _evolution.EvolutionInterface(store)

    # 插入一些节点
    store.add_task_node(title="测试任务", description="测试", priority=3)
    store.add_event_node(title="测试事件", event_type="decision", outcome="测试")

    updated = interface.incremental_update(batch_size=10)
    assert updated >= 0

    store.close()
    os.unlink(db_path)
    print("✓ Incremental update passed")


def test_record_step_function():
    """测试便捷函数"""
    store, db_path = _make_store()
    result = _evolution.record_step(
        step_type="action_fusion",
        action="测试操作",
        result="测试结果",
        confidence=0.8,
        store=store
    )
    assert result is True
    store.close()
    os.unlink(db_path)
    print("✓ Record step function passed")


def test_get_guidance_function():
    """测试便捷函数"""
    store, db_path = _make_store()
    guidance = _evolution.get_guidance("测试查询", store=store)
    assert 'relevant_history' in guidance
    assert 'suggestions' in guidance
    store.close()
    os.unlink(db_path)
    print("✓ Get guidance function passed")


if __name__ == "__main__":
    test_record_optimization()
    test_record_low_confidence()
    test_get_optimization_history()
    test_get_decision_guidance()
    test_search_relevant_history()
    test_evaluate_evolution_progress()
    test_incremental_update()
    test_record_step_function()
    test_get_guidance_function()
    print("\n✅ 阶段 5 自主演进接口测试全部通过")
