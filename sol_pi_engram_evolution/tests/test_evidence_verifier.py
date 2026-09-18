"""
阶段 1：证据核验测试
验证归档回查、关键词匹配、置信度调整
"""

import importlib.util
import sys
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


_evidence_verifier = _load_module("evidence_verifier",
                                   "evidence_verifier.py")


def test_verify_valid_source():
    """测试核验：source_pointer 有效，归档内容包含关键词"""
    archive_dir = tempfile.mkdtemp()
    archive_path = osp.join(archive_dir, "test-archive-1.txt")
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write("这是一个关于数据库 schema 设计的讨论。\n"
                "我们决定使用 PostgreSQL 作为数据库。\n"
                "最终结果是成功完成了设计任务。\n")

    verifier = _evidence_verifier.EvidenceVerifier(archive_dir=archive_dir)

    node = {
        'node_id': 'test-node-1',
        'title': '数据库 schema 设计',
        'description': '关于数据库设计的讨论',
        'outcome': '成功完成设计任务',
        'entities': ['PostgreSQL'],
    }

    result = verifier.verify_node(node, "archive://test-archive-1.txt")
    assert result['valid'] is True
    assert result['reason'].startswith('证据充足')
    assert len(result['matched_keywords']) >= 1
    assert '数据库' in result['matched_keywords'] or 'schema' in result['matched_keywords']

    import shutil
    shutil.rmtree(archive_dir)

    print("✓ Verify valid source passed")


def test_verify_missing_source():
    """测试核验：source_pointer 指向的归档文件不存在"""
    archive_dir = tempfile.mkdtemp()
    verifier = _evidence_verifier.EvidenceVerifier(archive_dir=archive_dir)

    node = {
        'node_id': 'test-node-missing',
        'title': '测试任务',
        'description': '测试描述',
    }

    result = verifier.verify_node(node, "archive://nonexistent-file.txt")
    assert result['valid'] is False
    assert '归档文件未找到' in result['reason']

    import shutil
    shutil.rmtree(archive_dir)

    print("✓ Verify missing source passed")


def test_verify_low_confidence():
    """测试核验：匹配关键词少，置信度降低"""
    archive_dir = tempfile.mkdtemp()
    archive_path = osp.join(archive_dir, "test-low-match.txt")
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write("这是一段完全不相关的文本。")

    verifier = _evidence_verifier.EvidenceVerifier(archive_dir=archive_dir,
                                                   min_match_ratio=0.1)

    node = {
        'node_id': 'test-node-low',
        'title': '数据库设计任务',
        'description': '使用 PostgreSQL',
    }

    result = verifier.verify_node(node, "archive://test-low-match.txt")
    assert result['valid'] is False  # 无匹配关键词
    assert '证据不足' in result['reason']
    assert result['confidence'] < 1.0

    import shutil
    shutil.rmtree(archive_dir)

    print("✓ Verify low confidence passed")


def test_verify_no_keywords():
    """测试核验：节点无有效关键词"""
    archive_dir = tempfile.mkdtemp()
    archive_path = osp.join(archive_dir, "test-file.txt")
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write("任意内容")

    verifier = _evidence_verifier.EvidenceVerifier(archive_dir=archive_dir)

    node = {
        'node_id': 'test-node-nokeys',
        'title': 'A',  # 太短，不算关键词
        'description': '',
    }

    result = verifier.verify_node(node, "archive://test-file.txt")
    assert result['valid'] is False
    assert '无有效关键词' in result['reason']

    import shutil
    shutil.rmtree(archive_dir)

    print("✓ Verify no keywords passed")


def test_verify_with_fragment():
    """测试核验：source_pointer 带 fragment"""
    archive_dir = tempfile.mkdtemp()
    archive_path = osp.join(archive_dir, "test-fragment.txt")
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write("第一部分：数据库设计。\n")
        f.write("第二部分：API 接口开发。\n")

    verifier = _evidence_verifier.EvidenceVerifier(archive_dir=archive_dir)

    node = {
        'node_id': 'test-node-fragment',
        'title': '数据库设计',
        'description': '关于数据库的任务',
    }

    # 虽然带 fragment，但当前实现不按 fragment 解析，只是整文件匹配
    result = verifier.verify_node(node, "archive://test-fragment.txt#section1")
    assert result['valid'] is True  # 文件存在且包含关键词

    import shutil
    shutil.rmtree(archive_dir)

    print("✓ Verify with fragment passed")


def test_verify_invalid_pointer_format():
    """测试核验：无效的 source_pointer 格式"""
    archive_dir = tempfile.mkdtemp()
    verifier = _evidence_verifier.EvidenceVerifier(archive_dir=archive_dir)

    node = {
        'node_id': 'test-node-invalid',
        'title': '测试任务',
        'description': '测试描述',
    }

    result = verifier.verify_node(node, "invalid://format")
    assert result['valid'] is False
    assert '无法解析' in result['reason']

    import shutil
    shutil.rmtree(archive_dir)

    print("✓ Verify invalid pointer format passed")


def test_verify_with_custom_min_match():
    """测试核验：自定义最小匹配比例"""
    archive_dir = tempfile.mkdtemp()
    archive_path = osp.join(archive_dir, "test-custom.txt")
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write("PostgreSQL 数据库\n")

    # 最小匹配比例设为 0.8，需要更多关键词命中
    verifier = _evidence_verifier.EvidenceVerifier(archive_dir=archive_dir,
                                                   min_match_ratio=0.8)

    node = {
        'node_id': 'test-node-custom',
        'title': '数据库设计',
        'description': '使用 PostgreSQL',
        'outcome': '成功',
    }

    result = verifier.verify_node(node, "archive://test-custom.txt")
    # 关键词: '数据库设计', '使用', 'PostgreSQL', '成功' (4个)
    # 归档中匹配: 'PostgreSQL' (1/4 = 0.25 < 0.8) → 不通过
    assert result['valid'] is False

    # 调低最小匹配比例到 0.2
    verifier2 = _evidence_verifier.EvidenceVerifier(archive_dir=archive_dir,
                                                    min_match_ratio=0.2)
    result2 = verifier2.verify_node(node, "archive://test-custom.txt")
    # 1/4 = 0.25 >= 0.2 → 通过
    assert result2['valid'] is True

    import shutil
    shutil.rmtree(archive_dir)

    print("✓ Verify with custom min match passed")


def test_verify_snippet_generation():
    """测试核验：归档内容片段生成"""
    archive_dir = tempfile.mkdtemp()
    archive_path = osp.join(archive_dir, "test-snippet.txt")
    long_content = "x" * 500 + "数据库" + "y" * 500

    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write(long_content)

    verifier = _evidence_verifier.EvidenceVerifier(archive_dir=archive_dir)

    node = {
        'node_id': 'test-node-snippet',
        'title': '数据库',
    }

    result = verifier.verify_node(node, "archive://test-snippet.txt")
    assert 'archive_content_snippet' in result
    assert len(result['archive_content_snippet']) <= 200 + 14  # 截断 + 标记
    assert 'truncated' in result['archive_content_snippet']

    import shutil
    shutil.rmtree(archive_dir)

    print("✓ Verify snippet generation passed")


def test_verify_standalone_function():
    """测试独立函数接口"""
    archive_dir = tempfile.mkdtemp()
    archive_path = osp.join(archive_dir, "test-standalone.txt")
    with open(archive_path, 'w', encoding='utf-8') as f:
        f.write("数据库设计 PostgreSQL 成功")

    node = {
        'node_id': 'test-node-standalone',
        'title': '数据库设计',
        'description': 'PostgreSQL',
    }

    result = _evidence_verifier.verify_node_against_source(
        node, "archive://test-standalone.txt", archive_dir
    )
    assert result['valid'] is True

    import shutil
    shutil.rmtree(archive_dir)

    print("✓ Verify standalone function passed")


if __name__ == "__main__":
    test_verify_valid_source()
    test_verify_missing_source()
    test_verify_low_confidence()
    test_verify_no_keywords()
    test_verify_with_fragment()
    test_verify_invalid_pointer_format()
    test_verify_with_custom_min_match()
    test_verify_snippet_generation()
    test_verify_standalone_function()
    print("\n✅ 阶段 1 证据核验测试全部通过")
