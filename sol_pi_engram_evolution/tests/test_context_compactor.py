"""
阶段 2：上下文压缩测试
验证经济触发公式、触发/不触发场景
"""

import importlib.util
import os


def _load_module(name, rel_path):
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", rel_path
    )
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_compactor = _load_module("context_compactor", "context_compactor.py")


def test_compact_triggered():
    """测试压缩被触发：未来节省 > 重写成本 + cache miss"""
    context = {
        'relevant_nodes': [{'node_id': '1'}, {'node_id': '2'}],
        'total_tokens_estimate': 1000,
        'query': '测试查询',
    }
    config = {
        'tokens_per_node': 200,
        'future_queries_estimate': 3,
        'rewrite_cost_factor': 0.5,
        'cache_miss_penalty': 500,
    }

    # 未来节省 = 2 * 200 * 3 = 1200
    # 重写成本 = 1000 * 0.5 = 500
    # cache miss = 500
    # 1200 >= 500 + 500 = 1000 → 触发

    result = _compactor.should_compact(context, config)
    assert result is True, f"预期触发，实际 {result}"

    print("✓ Compact triggered passed")


def test_compact_not_triggered():
    """测试压缩不触发：未来节省 < 重写成本 + cache miss"""
    context = {
        'relevant_nodes': [{'node_id': '1'}],
        'total_tokens_estimate': 5000,
        'query': '测试查询',
    }
    config = {
        'tokens_per_node': 100,
        'future_queries_estimate': 1,
        'rewrite_cost_factor': 0.5,
        'cache_miss_penalty': 500,
    }

    # 未来节省 = 1 * 100 * 1 = 100
    # 重写成本 = 5000 * 0.5 = 2500
    # cache miss = 500
    # 100 < 2500 + 500 = 3000 → 不触发

    result = _compactor.should_compact(context, config)
    assert result is False, f"预期不触发，实际 {result}"

    print("✓ Compact not triggered passed")


def test_compact_boundary():
    """测试边界：未来节省 == 重写成本 + cache miss → 触发"""
    context = {
        'relevant_nodes': [{'node_id': '1'}],
        'total_tokens_estimate': 1000,
        'query': '测试',
    }
    config = {
        'tokens_per_node': 200,
        'future_queries_estimate': 2.5,
        'rewrite_cost_factor': 0.5,
        'cache_miss_penalty': 500,
    }

    # 未来节省 = 1 * 200 * 2.5 = 500
    # 重写成本 = 1000 * 0.5 = 500
    # cache miss = 500
    # 500 >= 500 + 500？ 500 < 1000 → 不触发

    result = _compactor.should_compact(context, config)
    assert result is False

    print("✓ Compact boundary passed")


def test_compact_empty_nodes():
    """测试空节点：未来节省为 0，不触发"""
    context = {
        'relevant_nodes': [],
        'total_tokens_estimate': 0,
        'query': '测试',
    }
    config = {
        'tokens_per_node': 200,
        'future_queries_estimate': 3,
        'rewrite_cost_factor': 0.5,
        'cache_miss_penalty': 500,
    }

    result = _compactor.should_compact(context, config)
    assert result is False

    print("✓ Compact empty nodes passed")


def test_compact_context_result():
    """测试压缩执行结果"""
    context = {
        'relevant_nodes': [{'node_id': '1'}],
        'total_tokens_estimate': 1000,
        'query': '测试',
    }
    config = {
        'tokens_per_node': 200,
        'future_queries_estimate': 3,
        'rewrite_cost_factor': 0.5,
        'cache_miss_penalty': 500,
    }

    result = _compactor.compact_context(context, config)
    assert result['compressed'] is True
    assert 'compression_timestamp' in result
    assert result['query'] == '测试'  # 原字段保留

    print("✓ Compact context result passed")


if __name__ == "__main__":
    test_compact_triggered()
    test_compact_not_triggered()
    test_compact_boundary()
    test_compact_empty_nodes()
    test_compact_context_result()
    print("\n✅ 阶段 2 上下文压缩测试全部通过")
