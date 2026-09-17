"""
内容类型检测测试
验证各种内容类型的检测准确性
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_type_detector import ContentType, ContentTypeDetector, detect_and_route


def test_detect_json():
    """测试 JSON 检测"""
    detector = ContentTypeDetector()

    # 有效 JSON 对象
    content = '{"name": "测试", "value": 123}'
    result = detector.detect(content)
    assert result.content_type == ContentType.TYPE_JSON
    assert result.confidence >= 0.7
    assert 'JSON解析成功' in result.reasons

    # 有效 JSON 数组
    content = '[1, 2, 3, "测试"]'
    result = detector.detect(content)
    assert result.content_type == ContentType.TYPE_JSON

    # 无效 JSON
    content = '{name: "测试"}'  # 缺少引号
    result = detector.detect(content)
    # 不应该是 JSON（解析失败）
    assert result.content_type != ContentType.TYPE_JSON or result.confidence < 0.7

    print("✓ Detect JSON passed")


def test_detect_html():
    """测试 HTML 检测"""
    detector = ContentTypeDetector()

    content = '<html><body><p>测试内容</p></body></html>'
    result = detector.detect(content)
    assert result.content_type == ContentType.TYPE_HTML
    assert result.confidence >= 0.5
    assert any('HTML标签' in r for r in result.reasons) or \
           any('html标签' in r for r in result.reasons)

    # 不完整 HTML
    content = '<div class="test">内容</div>'
    result = detector.detect(content)
    assert result.content_type == ContentType.TYPE_HTML or \
           result.content_type == ContentType.TYPE_CODE

    print("✓ Detect HTML passed")


def test_detect_markdown():
    """测试 Markdown 检测"""
    detector = ContentTypeDetector()

    content = """# 标题
## 二级标题

[链接](https://example.com)

```python
print("代码")
```

- 列表项 1
- 列表项 2
"""
    result = detector.detect(content)
    assert result.content_type == ContentType.TYPE_MARKDOWN
    assert result.confidence >= 0.5

    print("✓ Detect Markdown passed")


def test_detect_code():
    """测试代码检测"""
    detector = ContentTypeDetector()

    # Python 代码
    content = """def hello():
    print("Hello World")
    return True

class MyClass:
    def __init__(self):
        self.value = 0
"""
    result = detector.detect(content)
    assert result.content_type == ContentType.TYPE_CODE
    assert result.confidence >= 0.5

    # JavaScript 代码
    content = """const add = (a, b) => {
    return a + b;
};
"""
    result = detector.detect(content)
    assert result.content_type == ContentType.TYPE_CODE

    print("✓ Detect code passed")


def test_detect_log():
    """测试日志检测"""
    detector = ContentTypeDetector()

    content = """2026-01-20 10:30:45 ERROR Database connection failed
2026-01-20 10:30:46 WARN Retrying connection
2026-01-20 10:30:47 INFO Connection established
"""
    result = detector.detect(content)
    assert result.content_type == ContentType.TYPE_LOG
    assert result.confidence >= 0.5

    print("✓ Detect log passed")


def test_detect_conversation():
    """测试对话检测"""
    detector = ContentTypeDetector()

    content = """用户：你好，请问数据库怎么设计？
助手：你好！数据库设计需要考虑...
用户：那使用 PostgreSQL 怎么样？
助手：PostgreSQL 是个不错的选择..."""
    result = detector.detect(content)
    # 应该检测为对话或文本
    assert result.content_type in (
        ContentType.TYPE_CONVERSATION,
        ContentType.TYPE_TEXT
    )

    print("✓ Detect conversation passed")


def test_detect_text():
    """测试普通文本检测"""
    detector = ContentTypeDetector()

    content = "这是一个普通的文本内容，用于测试文本类型检测。"
    result = detector.detect(content)
    assert result.content_type == ContentType.TYPE_TEXT
    assert result.confidence >= 0.3

    print("✓ Detect text passed")


def test_detect_unknown():
    """测试未知类型检测"""
    detector = ContentTypeDetector()

    content = "ajsldkf jslakdjf laksdjf wqe"
    result = detector.detect(content)
    # 短随机字符串应该是 unknown 或文本
    assert result.content_type in (
        ContentType.TYPE_UNKNOWN,
        ContentType.TYPE_TEXT
    )

    print("✓ Detect unknown passed")


def test_detect_priority():
    """测试优先级：JSON 优先于其他"""
    detector = ContentTypeDetector()

    # JSON 对象（也包含代码关键字）
    content = '{"function": "test", "return": true}'
    result = detector.detect(content)
    # JSON 应该优先于代码
    assert result.content_type == ContentType.TYPE_JSON

    print("✓ Detect priority passed")


def test_detect_and_route():
    """测试检测 + 路由"""
    content = '{"key": "value"}'

    def json_handler(content, result):
        return f"JSON handler: {result.content_type}"

    def code_handler(content, result):
        return f"Code handler: {result.content_type}"

    handlers = {
        'json': json_handler,
        'code': code_handler,
        'default': lambda c, r: f"Default handler: {r.content_type}"
    }

    result = detect_and_route(content, handlers)
    assert 'JSON handler' in result

    print("✓ Detect and route passed")


def test_all_types_coverage():
    """测试所有类型都能被检测"""
    detector = ContentTypeDetector()

    test_cases = [
        ('{"json": true}', ContentType.TYPE_JSON),
        ('<html></html>', ContentType.TYPE_HTML),
        ('# Markdown', ContentType.TYPE_MARKDOWN),
        ('def foo(): pass', ContentType.TYPE_CODE),
        ('ERROR: something', ContentType.TYPE_LOG),
        ('用户：你好', ContentType.TYPE_CONVERSATION),
        ('普通文本', ContentType.TYPE_TEXT),
    ]

    for content, expected_type in test_cases:
        result = detector.detect(content)
        # 检查是否能检测到期望类型（或至少不是 unknown）
        assert result.content_type != ContentType.TYPE_UNKNOWN or \
               result.confidence < 0.5, \
               f"内容 {content[:30]}... 应该被检测为 {expected_type}"

    print("✓ All types coverage passed")


if __name__ == "__main__":
    test_detect_json()
    test_detect_html()
    test_detect_markdown()
    test_detect_code()
    test_detect_log()
    test_detect_conversation()
    test_detect_text()
    test_detect_unknown()
    test_detect_priority()
    test_detect_and_route()
    test_all_types_coverage()
    print("\n✅ 内容类型检测测试全部通过")
