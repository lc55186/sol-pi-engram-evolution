"""
内容类型检测模块
参考 Headroom 的 Magika 模型：先识别内容类型，再分发给专属处理器
支持：文本、代码、JSON、日志、Markdown、HTML、对话
"""

import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ContentType:
    """内容类型枚举"""
    TYPE_TEXT = "text"
    TYPE_CODE = "code"
    TYPE_JSON = "json"
    TYPE_LOG = "log"
    TYPE_MARKDOWN = "markdown"
    TYPE_HTML = "html"
    TYPE_CONVERSATION = "conversation"
    TYPE_UNKNOWN = "unknown"

    @classmethod
    def all_types(cls) -> list[str]:
        return [
            cls.TYPE_TEXT, cls.TYPE_CODE, cls.TYPE_JSON,
            cls.TYPE_LOG, cls.TYPE_MARKDOWN, cls.TYPE_HTML,
            cls.TYPE_CONVERSATION, cls.TYPE_UNKNOWN
        ]


@dataclass
class TypeDetectionResult:
    """类型检测结果"""
    content_type: str
    confidence: float  # 0.0 - 1.0
    reasons: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ContentTypeDetector:
    """
    内容类型检测器
    基于启发式规则检测内容类型
    参考 Magika 的思路：先识别类型，再分发给专属处理器
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.min_confidence = self.config.get('min_confidence', 0.5)

    def detect(self, content: str) -> TypeDetectionResult:
        """
        检测内容类型
        返回检测结果
        """
        if not content or not content.strip():
            return TypeDetectionResult(
                content_type=ContentType.TYPE_UNKNOWN,
                confidence=0.0,
                reasons=["空内容"]
            )

        # 并行检测各个类型
        results = []

        # JSON 检测（优先，因为 JSON 也可能是代码）
        json_result = self._detect_json(content)
        if json_result.confidence > 0.7:
            return json_result
        results.append(json_result)

        # HTML 检测
        html_result = self._detect_html(content)
        if html_result.confidence > 0.7:
            return html_result
        results.append(html_result)

        # Markdown 检测
        md_result = self._detect_markdown(content)
        if md_result.confidence > 0.7:
            return md_result
        results.append(md_result)

        # 代码检测
        code_result = self._detect_code(content)
        results.append(code_result)

        # 日志检测
        log_result = self._detect_log(content)
        results.append(log_result)

        # 对话检测
        conv_result = self._detect_conversation(content)
        results.append(conv_result)

        # 文本检测（默认）
        text_result = self._detect_text(content)
        results.append(text_result)

        # 选择置信度最高的
        best = max(results, key=lambda x: x.confidence)

        if best.confidence < self.min_confidence:
            # 置信度太低，返回 unknown
            return TypeDetectionResult(
                content_type=ContentType.TYPE_UNKNOWN,
                confidence=best.confidence,
                reasons=["置信度低于阈值"] + best.reasons
            )

        return best

    def _detect_json(self, content: str) -> TypeDetectionResult:
        """检测 JSON 类型"""
        reasons = []
        confidence = 0.0

        content_stripped = content.strip()

        # 首尾括号检查
        if (content_stripped.startswith('{') and
                content_stripped.endswith('}')):
            reasons.append("首尾花括号")
            confidence += 0.4
        elif (content_stripped.startswith('[') and
                content_stripped.endswith(']')):
            reasons.append("首尾方括号")
            confidence += 0.4

        # 尝试解析
        try:
            import json
            parsed = json.loads(content_stripped)
            reasons.append("JSON解析成功")
            confidence += 0.4
            return TypeDetectionResult(
                content_type=ContentType.TYPE_JSON,
                confidence=min(1.0, confidence),
                reasons=reasons,
                metadata={'parsed': parsed}
            )
        except (json.JSONDecodeError, ValueError):
            pass

        return TypeDetectionResult(
            content_type=ContentType.TYPE_JSON,
            confidence=confidence,
            reasons=reasons
        )

    def _detect_html(self, content: str) -> TypeDetectionResult:
        """检测 HTML 类型"""
        reasons = []
        confidence = 0.0

        # HTML 标签检查
        if re.search(r'<[a-zA-Z][^>]*>', content):
            reasons.append("包含HTML标签")
            confidence += 0.3
        if re.search(r'<\s*/\s*[a-zA-Z][^>]*\s*>', content):
            reasons.append("包含闭合标签")
            confidence += 0.2
        if re.search(r'<!DOCTYPE', content):
            reasons.append("DOCTYPE声明")
            confidence += 0.3
        if re.search(r'<html', content, re.IGNORECASE):
            reasons.append("html标签")
            confidence += 0.2

        # 常见HTML特征
        if re.search(r'<(div|p|span|table|tr|td|th|a|img|input|form)', content):
            reasons.append("常见HTML元素")
            confidence += 0.2

        return TypeDetectionResult(
            content_type=ContentType.TYPE_HTML,
            confidence=min(1.0, confidence),
            reasons=reasons
        )

    def _detect_markdown(self, content: str) -> TypeDetectionResult:
        """检测 Markdown 类型"""
        reasons = []
        confidence = 0.0

        # Markdown 标题
        if re.search(r'^#{1,6}\s+', content, re.MULTILINE):
            reasons.append("Markdown标题")
            confidence += 0.3
        # Markdown 链接
        if re.search(r'\[.*?\]\(.*?\)', content):
            reasons.append("Markdown链接")
            confidence += 0.2
        # Markdown 代码块
        if re.search(r'```', content):
            reasons.append("Markdown代码块")
            confidence += 0.2
        # Markdown 列表
        if re.search(r'^[\*\-\+] ', content, re.MULTILINE):
            reasons.append("Markdown列表")
            confidence += 0.1
        # 表格
        if re.search(r'\|.+\|', content) and re.search(r'[-]+', content):
            reasons.append("Markdown表格")
            confidence += 0.2

        return TypeDetectionResult(
            content_type=ContentType.TYPE_MARKDOWN,
            confidence=min(1.0, confidence),
            reasons=reasons
        )

    def _detect_code(self, content: str) -> TypeDetectionResult:
        """检测代码类型"""
        reasons = []
        confidence = 0.0

        # 代码关键字检测
        code_keywords = [
            'function', 'def ', 'class ', 'import ', 'from ',
            'return ', 'if ', 'else', 'for ', 'while ',
            'const ', 'let ', 'var ', '=>', 'async', 'await',
            'console.log', 'print(', 'System.out',
            'public ', 'private ', 'protected ', 'static ',
            'void ', 'int ', 'string ', 'bool ', 'float ',
            'echo ', '<?php', '?>', '<%', '%>',
        ]
        for keyword in code_keywords:
            if keyword in content:
                reasons.append(f"代码关键字: {keyword}")
                confidence += 0.05

        # 代码块标记
        if re.search(r'```\w*', content):
            reasons.append("代码块标记")
            confidence += 0.2

        # 缩进模式（Python 风格）
        if re.search(r'^    ', content, re.MULTILINE):
            reasons.append("Python风格缩进")
            confidence += 0.15

        # 大量符号（代码特征）
        symbol_ratio = len(re.findall(r'[{}()\[\];=<>+\-*/&|!~]', content)) / max(len(content), 1)
        if symbol_ratio > 0.1:
            reasons.append(f"高符号密度({symbol_ratio:.2f})")
            confidence += 0.15

        return TypeDetectionResult(
            content_type=ContentType.TYPE_CODE,
            confidence=min(1.0, confidence),
            reasons=reasons
        )

    def _detect_log(self, content: str) -> TypeDetectionResult:
        """检测日志类型"""
        reasons = []
        confidence = 0.0

        # 日志级别
        log_levels = ['ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'FATAL', 'CRITICAL',
                      'error', 'warn', 'warning', 'info', 'debug', 'fatal', 'critical']
        for level in log_levels:
            if re.search(rf'\b{level}\b', content):
                reasons.append(f"日志级别: {level}")
                confidence += 0.1

        # 时间戳模式
        timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}',
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            r'\w{3}\s+\d{2}\s+\d{2}:\d{2}:\d{2}',
            r'\[\d{2}:\d{2}:\d{2}\]',
        ]
        for pattern in timestamp_patterns:
            if re.search(pattern, content):
                reasons.append("时间戳模式")
                confidence += 0.15
                break

        # 日志常见格式
        if re.search(r'\[.*?\]', content):
            reasons.append("方括号包裹")
            confidence += 0.1
        if re.search(r'(?:ERROR|WARN|INFO|DEBUG).*?:', content):
            reasons.append("日志级别后跟冒号")
            confidence += 0.1

        # 多行日志
        lines = content.split('\n')
        if len(lines) > 5:
            # 检查是否每行都有类似结构
            structured_lines = 0
            for line in lines:
                if re.search(r'(ERROR|WARN|INFO|DEBUG|\d{4}-\d{2}-\d{2}|\[)', line):
                    structured_lines += 1
            if structured_lines > len(lines) * 0.5:
                reasons.append("结构化日志")
                confidence += 0.15

        return TypeDetectionResult(
            content_type=ContentType.TYPE_LOG,
            confidence=min(1.0, confidence),
            reasons=reasons
        )

    def _detect_conversation(self, content: str) -> TypeDetectionResult:
        """检测对话类型"""
        reasons = []
        confidence = 0.0

        # 对话标记
        conv_patterns = [
            (r'(用户|User|user|提问|question|Q[.:])\s*[:：]?\s*', '用户标记'),
            (r'(助手|Assistant|assistant|回答|answer|A[.:]|模型|model)\s*[:：]?\s*', '助手标记'),
            (r'(System|system|系统|prompt)\s*[:：]?\s*', '系统标记'),
            (r'<\|?\s*(user|assistant|system)\s*\|?>', '特殊标记'),
        ]
        for pattern, desc in conv_patterns:
            if re.search(pattern, content):
                reasons.append(desc)
                confidence += 0.15

        # 轮次标记
        turn_patterns = [
            r'第?\s*\d+\s*轮\s*对话',
            r'Round\s*\d+:',
            r'Turn\s*\d+:',
            r'\n\n\d+\s*[.:]\s*',
        ]
        for pattern in turn_patterns:
            if re.search(pattern, content):
                reasons.append("轮次标记")
                confidence += 0.15
                break

        # 多轮结构
        if content.count('\n\n') >= 2:
            reasons.append("多段落结构")
            confidence += 0.1

        return TypeDetectionResult(
            content_type=ContentType.TYPE_CONVERSATION,
            confidence=min(1.0, confidence),
            reasons=reasons
        )

    def _detect_text(self, content: str) -> TypeDetectionResult:
        """检测普通文本类型（默认）"""
        reasons = ["默认文本类型"]
        confidence = 0.3

        # 如果有中文字符，提升置信度
        if re.search(r'[\u4e00-\u9fff]+', content):
            reasons.append("包含中文")
            confidence += 0.2

        # 如果有自然语言句式
        if re.search(r'[.]{2,}|[！。？]+', content):
            reasons.append("自然语言标点")
            confidence += 0.1

        return TypeDetectionResult(
            content_type=ContentType.TYPE_TEXT,
            confidence=min(1.0, confidence),
            reasons=reasons
        )


# 便捷函数
def detect_content_type(content: str,
                       config: dict | None = None) -> TypeDetectionResult:
    """检测内容类型"""
    detector = ContentTypeDetector(config=config)
    return detector.detect(content)


def detect_and_route(content: str, handlers: dict[str, callable],
                    config: dict | None = None) -> Any:
    """
    检测类型并路由到专属处理器
    handlers: {类型: 函数}
    """
    result = detect_content_type(content, config)
    handler = handlers.get(result.content_type)
    if handler:
        return handler(content, result)
    # 默认处理器
    default_handler = handlers.get('default')
    if default_handler:
        return default_handler(content, result)
    return result
