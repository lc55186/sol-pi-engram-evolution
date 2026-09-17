"""
Context Tracker 测试
验证记录、相关性检测、展开、会话历史
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import shutil
import tempfile

from context_tracker import ContextTracker


def _make_tracker():
    tmpdir = tempfile.mkdtemp()
    db = os.path.join(tmpdir, "tracker.db")
    return ContextTracker(tracker_db=db), tmpdir


def test_record_and_retrieve():
    """测试记录一轮对话并获取历史"""
    tracker, tmpdir = _make_tracker()

    session_id = "session-1"
    query = "数据库设计 PostgreSQL"
    fingerprint = hashlib_fingerprint(query)

    round_id = tracker.record_round(session_id, query, fingerprint)
    assert round_id and len(round_id) == 16

    history = tracker.get_session_history(session_id, limit=10)
    assert len(history) == 1
    assert history[0]['query'] == query
    assert history[0]['round_id'] == round_id

    tracker.close()
    shutil.rmtree(tmpdir)
    print("✓ Record and retrieve passed")


def test_relevance_detection():
    """测试相关性检测"""
    tracker, tmpdir = _make_tracker()

    session_id = "session-relevance"
    tracker.record_round(session_id, "数据库设计 PostgreSQL", "fp1")
    tracker.record_round(session_id, "API 接口开发", "fp2")
    tracker.record_round(session_id, "测试数据库连接", "fp3")

    relevant = tracker.track_relevance(session_id, "PostgreSQL 数据库 设计")
    assert len(relevant) >= 1
    # 第一个记录应该最相关
    assert relevant[0]['query'] == "数据库设计 PostgreSQL"
    assert relevant[0]['relevance_score'] >= 0.3

    tracker.close()
    shutil.rmtree(tmpdir)
    print("✓ Relevance detection passed")


def test_expand_context():
    """测试展开相关上下文"""
    tracker, tmpdir = _make_tracker()

    session_id = "session-expand"
    tracker.record_round(
        session_id, "数据库设计 PostgreSQL",
        hashlib_fingerprint("数据库设计 PostgreSQL"),
        expanded_content="设计用户表和订单表，使用 PostgreSQL"
    )
    tracker.record_round(
        session_id, "API 接口开发",
        hashlib_fingerprint("API 接口开发"),
        expanded_content="实现用户管理 REST API"
    )

    result = tracker.expand_context(session_id, "数据库设计")

    assert result['expanded'] is True
    assert len(result['expanded_items']) >= 1
    assert '设计用户表和订单表，使用 PostgreSQL' in result['combined_content']

    tracker.close()
    shutil.rmtree(tmpdir)
    print("✓ Expand context passed")


def test_expand_no_relevance():
    """测试无相关上下文展开"""
    tracker, tmpdir = _make_tracker()

    session_id = "session-no-relevance"
    tracker.record_round(session_id, "完全无关的话题", "fp1")

    result = tracker.expand_context(session_id, "佛祖保佑 代码无 bug")

    assert result['expanded'] is False
    assert result['reason'] == '无相关历史上下文'
    assert len(result['expanded_items']) == 0

    tracker.close()
    shutil.rmtree(tmpdir)
    print("✓ Expand no relevance passed")


def test_clear_session():
    """测试清除会话"""
    tracker, tmpdir = _make_tracker()

    session_id = "session-clear"
    tracker.record_round(session_id, "测试", "fp1")
    tracker.record_round(session_id, "测试2", "fp2")

    assert len(tracker.get_session_history(session_id)) == 2

    tracker.clear_session(session_id)

    history = tracker.get_session_history(session_id)
    assert len(history) == 0

    tracker.close()
    shutil.rmtree(tmpdir)
    print("✓ Clear session passed")


def test_stats():
    """测试统计"""
    tracker, tmpdir = _make_tracker()

    for i in range(3):
        tracker.record_round(f"session-{i}", f"查询 {i}", f"fp{i}")

    stats = tracker.get_stats()
    assert stats['total_rounds'] == 3
    assert stats['total_sessions'] == 3

    tracker.close()
    shutil.rmtree(tmpdir)
    print("✓ Stats passed")


def hashlib_fingerprint(text: str) -> str:
    """生成简单指纹"""
    import hashlib
    return hashlib.md5(text.encode()).hexdigest()[:16]


if __name__ == "__main__":
    test_record_and_retrieve()
    test_relevance_detection()
    test_expand_context()
    test_expand_no_relevance()
    test_clear_session()
    test_stats()
    print("\n✅ Context Tracker 测试全部通过")
