"""
CCR 缓存测试
验证注册、拦截、取回、统计
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import importlib.util
import shutil
import tempfile


def _load_module(name, rel_path):
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", rel_path
    )
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_ccr = _load_module("observation_pack_ccr", "observation_pack_ccr.py")
_obs = _load_module("observation_pack", "observation_pack.py")

CCRCache = _ccr.CCRCache
ObservationPack = _obs.ObservationPack


def _make_ccr_cache():
    tmpdir = tempfile.mkdtemp()
    cache_db = os.path.join(tmpdir, "ccr_cache.db")
    obs_root = os.path.join(tmpdir, "observations")
    obs = ObservationPack(archive_root=obs_root)
    cache = CCRCache(cache_db=cache_db, observation_pack=obs)
    return cache, tmpdir


def test_register_and_intercept():
    """测试注册后拦截成功"""
    cache, tmpdir = _make_ccr_cache()

    # 创建归档
    obs = cache.observation_pack
    handle = obs.archive("测试内容：数据库设计任务", content_type="text")
    marker = cache.register(handle)

    assert marker and len(marker) == 32

    # 拦截请求（带标记）
    request = f"请查看 [CCR:{marker}] 的内容"
    result = cache.intercept(request)

    assert result is not None
    assert result['hit'] is True
    assert result['marker'] == marker
    assert '数据库设计任务' in result['content']
    assert result['source'] in ('ccr_cache', 'ccr_cache_auto')

    stats = cache.get_stats()
    assert stats['total_entries'] == 1

    shutil.rmtree(tmpdir)
    print("✓ Register and intercept passed")


def test_intercept_without_marker():
    """测试拦截不带标记的请求（内容匹配）"""
    cache, tmpdir = _make_ccr_cache()

    obs = cache.observation_pack
    handle = obs.archive("数据库设计 PostgreSQL", content_type="text")
    cache.register(handle)

    # 不带标记的请求，但包含匹配关键词
    request = "数据库设计"
    result = cache.intercept(request)

    # 应该通过内容匹配找到
    assert result is not None
    assert result['hit'] is True
    assert '数据库设计' in result['content']

    shutil.rmtree(tmpdir)
    print("✓ Intercept without marker passed")


def test_intercept_no_match():
    """测试无匹配请求"""
    cache, tmpdir = _make_ccr_cache()

    obs = cache.observation_pack
    obs.archive("完全无关的内容", content_type="text")

    request = "佛祖保佑 代码无 bug"
    result = cache.intercept(request)

    assert result is None

    shutil.rmtree(tmpdir)
    print("✓ Intercept no match passed")


def test_stats():
    """测试统计"""
    cache, tmpdir = _make_ccr_cache()

    obs = cache.observation_pack
    for i in range(5):
        handle = obs.archive(f"测试内容 {i}", content_type="text")
        cache.register(handle)

    stats = cache.get_stats()
    assert stats['total_entries'] == 5

    # 访问几个条目
    for i in range(2):
        handle = obs.archive(f"访问内容 {i}", content_type="text")
        marker = cache.register(handle)
        cache.intercept(f"测试 [CCR:{marker}]")

    stats = cache.get_stats()
    assert stats['accessed_entries'] >= 2

    shutil.rmtree(tmpdir)
    print("✓ Stats passed")


def test_retrieve_by_content_id():
    """测试根据 content_id 取回"""
    cache, tmpdir = _make_ccr_cache()

    obs = cache.observation_pack
    handle = obs.archive("可取回的内容", content_type="text")
    cache.register(handle)

    retrieved = cache.retrieve_by_content_id(handle['content_id'])
    assert retrieved is not None
    assert retrieved['content'] == "可取回的内容"

    shutil.rmtree(tmpdir)
    print("✓ Retrieve by content_id passed")


def test_register_duplicate():
    """测试重复注册（同一 content_id）"""
    cache, tmpdir = _make_ccr_cache()

    obs = cache.observation_pack
    handle = obs.archive("重复测试", content_type="text")
    marker1 = cache.register(handle)
    marker2 = cache.register(handle)

    # 应该成功，返回 marker
    assert marker1
    assert marker2

    stats = cache.get_stats()
    assert stats['total_entries'] == 1  # 重复注册不增加数量

    shutil.rmtree(tmpdir)
    print("✓ Register duplicate passed")


if __name__ == "__main__":
    test_register_and_intercept()
    test_intercept_without_marker()
    test_intercept_no_match()
    test_stats()
    test_retrieve_by_content_id()
    test_register_duplicate()
    print("\n✅ CCR 缓存测试全部通过")
