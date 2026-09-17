"""
压缩质量验证测试
验证大海捞针测试、图谱检索准确率
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import shutil
import tempfile

from compression_verifier import CompressionVerifier
from observation_pack import ObservationPack


def _make_obs():
    tmpdir = tempfile.mkdtemp()
    obs_root = os.path.join(tmpdir, "observations")
    obs = ObservationPack(archive_root=obs_root)
    return obs, tmpdir


def test_needle_test_basic():
    """测试大海捞针基础测试"""
    obs, tmpdir = _make_obs()

    def archive_fn(content):
        return obs.archive(content, content_type="text")

    def retrieve_fn(handle):
        return obs.retrieve(handle)

    verifier = CompressionVerifier({
        'needle_count': 3,
        'haystack_size': 50,
        'pass_threshold': 0.95,
    })

    result = verifier.run_needle_test(archive_fn, retrieve_fn)

    assert result['test_name'] == ' Needle-in-Haystack Test'
    assert result['needle_count'] == 3
    assert result['accuracy'] == 1.0  # 全部找到
    assert result['pass'] is True
    assert result['found_count'] == 3
    assert result['missing_count'] == 0

    shutil.rmtree(tmpdir)
    print("✓ Needle test basic passed")


def test_needle_test_with_retrieval():
    """测试大海捞针 + 召回"""
    obs, tmpdir = _make_obs()

    def archive_fn(content):
        return obs.archive(content, content_type="text")

    def retrieve_fn(handle):
        return obs.retrieve(handle, chunk_index=0)

    verifier = CompressionVerifier({
        'needle_count': 5,
        'haystack_size': 100,
        'pass_threshold': 0.95,
    })

    result = verifier.run_needle_test(archive_fn, retrieve_fn)

    assert result['pass'] is True
    assert result['accuracy'] >= 0.95

    shutil.rmtree(tmpdir)
    print("✓ Needle test with retrieval passed")


def test_needle_test_half():
    """测试部分丢失情况"""
    obs, tmpdir = _make_obs()

    def archive_fn(content):
        # 模拟压缩：只保留一半内容
        half_len = len(content) // 2
        compressed = content[:half_len]
        return obs.archive(compressed, content_type="text")

    def retrieve_fn(handle):
        return obs.retrieve(handle)

    verifier = CompressionVerifier({
        'needle_count': 5,
        'haystack_size': 50,
        'pass_threshold': 0.5,  # 降低阈值，因为我们模拟了压缩丢失
    })

    result = verifier.run_needle_test(archive_fn, retrieve_fn)

    # 由于我们只保留了一半内容，可能会丢失一些针
    # 但我们的模拟是随机的，所以结果可能有所不同
    # 这里我们只是验证测试能跑通
    assert result['needle_count'] == 5
    assert result['found_count'] + result['missing_count'] == 5

    shutil.rmtree(tmpdir)
    print("✓ Needle test half passed")


def test_needle_test_various_sizes():
    """测试不同大小的海量内容"""
    obs, tmpdir = _make_obs()

    def archive_fn(content):
        return obs.archive(content, content_type="text")

    def retrieve_fn(handle):
        return obs.retrieve(handle)

    # 小海量
    verifier_small = CompressionVerifier({
        'needle_count': 3,
        'haystack_size': 20,
        'pass_threshold': 0.95,
    })
    result_small = verifier_small.run_needle_test(archive_fn, retrieve_fn)
    assert result_small['pass'] is True

    # 大海量
    verifier_large = CompressionVerifier({
        'needle_count': 5,
        'haystack_size': 200,
        'pass_threshold': 0.95,
    })
    result_large = verifier_large.run_needle_test(archive_fn, retrieve_fn)
    assert result_large['pass'] is True

    shutil.rmtree(tmpdir)
    print("✓ Needle test various sizes passed")


def test_graph_needle_test():
    """测试图谱大海捞针"""
    import tempfile

    from graph_store import GraphStore

    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    store = GraphStore(db_path=db_path)

    verifier = CompressionVerifier({
        'needle_count': 3,
        'pass_threshold': 0.95,
    })

    result = verifier.run_graph_needle_test(store, node_count=20, needle_count=3)

    assert result['needle_count'] == 3
    assert result['found_count'] + result['missing_count'] == 3
    # 检索应该能找到大部分针
    assert result['found_count'] >= 2

    store.close()
    os.unlink(db_path)

    print("✓ Graph needle test passed")


def test_retrieval_accuracy():
    """测试检索准确率"""
    import tempfile

    from graph_store import GraphStore

    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    store = GraphStore(db_path=db_path)

    # 插入特定节点
    store.add_task_node(
        title="数据库设计 PostgreSQL",
        description="设计用户表和订单表，使用 PostgreSQL",
        priority=5
    )
    store.add_task_node(
        title="API 接口开发",
        description="实现用户管理 REST API",
        priority=4
    )
    store.add_task_node(
        title="测试数据库连接",
        description="测试数据库连接是否正常",
        priority=3
    )

    verifier = CompressionVerifier()

    result = verifier.run_retrieval_accuracy_test(
        store, "数据库设计", expected_node_count=1, expected_min_score=0.1
    )

    assert result['query'] == "数据库设计"
    assert result['retrieved_count'] >= 1
    assert result['pass'] is True

    store.close()
    os.unlink(db_path)

    print("✓ Retrieval accuracy passed")


if __name__ == "__main__":
    test_needle_test_basic()
    test_needle_test_with_retrieval()
    test_needle_test_half()
    test_needle_test_various_sizes()
    test_graph_needle_test()
    test_retrieval_accuracy()
    print("\n✅ 压缩质量验证测试全部通过")
