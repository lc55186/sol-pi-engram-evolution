#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Graph Extractor Tests"""
import os
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from graph_extractor import GraphExtractor


def test_extractor_initialization():
    """测试提取器初始化"""
    extractor = GraphExtractor()
    assert extractor.min_confidence == 0.5
    assert extractor.enable_heuristic is True
    assert extractor.enable_llm_assist is False
    assert extractor.chunk_size == 5000

    # 自定义配置
    extractor2 = GraphExtractor({
        'min_confidence': 0.3,
        'enable_llm_assist': True,
        'chunk_size': 1000
    })
    assert extractor2.min_confidence == 0.3
    assert extractor2.enable_llm_assist is True
    assert extractor2.chunk_size == 1000

    print("  ✓ Extractor initialization works correctly")


def test_empty_content():
    """测试空内容处理"""
    extractor = GraphExtractor()
    result = extractor.extract_from_content("", "test")
    assert result['tasks'] == []
    assert result['events'] == []
    assert result['relations'] == []
    assert result['extraction_meta']['reason'] == '空内容'

    print("  ✓ Empty content handling works correctly")


def test_task_extraction():
    """测试任务提取"""
    extractor = GraphExtractor({'min_confidence': 0.3})
    content = """
任务1：完成用户登录模块开发
TODO：修复注册页面的验证问题
待办：编写单元测试
目标：提升系统稳定性
    """
    result = extractor.extract_from_content(content, "test")

    assert len(result['tasks']) >= 3
    titles = [t.title for t in result['tasks']]
    assert any("登录模块" in t or "登录" in t for t in titles)

    print(f"  ✓ Task extraction: {len(result['tasks'])} tasks found")


def test_event_extraction():
    """测试事件提取"""
    extractor = GraphExtractor({'min_confidence': 0.3})
    content = """
决策：采用MySQL作为主数据库
结果：性能提升30%
发现：内存泄漏问题
错误：连接超时
完成：数据迁移
里程碑：V1.0版本发布
    """
    result = extractor.extract_from_content(content, "test")

    assert len(result['events']) >= 4
    types = [e.event_type for e in result['events']]
    assert 'decision' in types
    assert 'outcome' in types

    print(f"  ✓ Event extraction: {len(result['events'])} events found")


def test_confidence_threshold():
    """测试置信度阈值"""
    content = "任务X：测试任务"

    # 高阈值
    extractor_high = GraphExtractor({'min_confidence': 0.9})
    result_high = extractor_high.extract_from_content(content, "test")

    # 低阈值
    extractor_low = GraphExtractor({'min_confidence': 0.1})
    result_low = extractor_low.extract_from_content(content, "test")

    # 低阈值应该提取更多或相等的节点
    assert len(result_low['tasks']) >= len(result_high['tasks'])

    print(f"  ✓ Confidence threshold: high={len(result_high['tasks'])}, low={len(result_low['tasks'])}")


def test_deduplication():
    """测试去重"""
    extractor = GraphExtractor({'min_confidence': 0.3})
    content = """
任务1：同一个任务
任务1：同一个任务
任务2：不同任务
    """
    result = extractor.extract_from_content(content, "test")

    titles = [t.title for t in result['tasks']]
    # "同一个任务" 应该只出现一次
    assert titles.count("同一个任务") <= 1 or len(result['tasks']) <= 2

    print(f"  ✓ Deduplication: {len(result['tasks'])} unique tasks")


def test_source_pointer():
    """测试来源指针"""
    extractor = GraphExtractor()
    content = "任务：测试任务"
    result = extractor.extract_from_content(content, "archive-001")

    assert result['extraction_meta']['source_pointer'] == "archive-001"

    if result['tasks']:
        assert result['tasks'][0].source_pointer == "archive-001"

    print("  ✓ Source pointer preserved")


def test_clean_text():
    """测试文本清洗"""
    extractor = GraphExtractor()

    test_cases = [
        ("  Hello  World  ", "Hello World"),
        ("【任务】测试", "测试"),
        ("测试。。。", "测试"),
        ("测试！！！", "测试"),
    ]

    for input_text, expected in test_cases:
        result = extractor._clean_text(input_text)
        assert result == expected, f"Expected '{expected}', got '{result}'"

    print("  ✓ Text cleaning works correctly")


def test_entity_extraction():
    """测试实体提取"""
    extractor = GraphExtractor()
    content = """
张三工程师完成了开发工作
项目经理李四组织了会议
测试团队发现了bug
    """
    entities = extractor._extract_entities(content)

    assert len(entities) >= 2
    # 检查是否提取到了人名
    has_person = any("工程师" in e or "经理" in e or len(e) >= 2 for e in entities)
    assert has_person

    print(f"  ✓ Entity extraction: {len(entities)} entities found")


if __name__ == "__main__":
    print("=" * 60)
    print("Graph Extractor Tests")
    print("=" * 60)

    test_extractor_initialization()
    test_empty_content()
    test_task_extraction()
    test_event_extraction()
    test_confidence_threshold()
    test_deduplication()
    test_source_pointer()
    test_clean_text()
    test_entity_extraction()

    print("\n✅ All graph extractor tests passed")
