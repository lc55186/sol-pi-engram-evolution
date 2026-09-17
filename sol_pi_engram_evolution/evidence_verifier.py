"""
阶段 1：证据核验模块
核验提取节点是否有原始归档支撑
"""

import os
import re
from typing import Any


class EvidenceVerifier:
    """证据核验器：回查原始归档验证节点"""

    def __init__(self, archive_dir: str = "./archives",
                 min_match_ratio: float = 0.3,
                 min_keywords_matched: int = 1):
        self.archive_dir = archive_dir
        self.min_match_ratio = min_match_ratio
        self.min_keywords_matched = min_keywords_matched

    def verify_node(self, node: dict[str, Any],
                    source_pointer: str = None) -> dict[str, Any]:
        """核验单个节点的证据"""
        pointer = source_pointer or node.get('source_pointer', '')
        result = {
            'valid': False,
            'confidence': node.get('confidence', 1.0),
            'reason': '',
            'matched_keywords': [],
            'archive_content_snippet': '',
        }

        if not pointer:
            result['reason'] = '缺少 source_pointer，无法核验'
            return result

        pointer_info = self._parse_pointer(pointer)
        if not pointer_info:
            result['reason'] = f'无法解析 source_pointer: {pointer}'
            return result

        archive_content = self._read_archive(pointer_info)
        if archive_content is None:
            result['reason'] = f'归档文件未找到: {pointer_info["file_path"]}'
            return result

        result['archive_content_snippet'] = self._get_snippet(archive_content, 200)

        keywords = self._extract_keywords(node)
        if not keywords:
            result['reason'] = '节点无有效关键词用于匹配'
            return result

        matched = self._match_keywords(keywords, archive_content)
        match_ratio = len(matched) / len(keywords) if keywords else 0
        result['matched_keywords'] = matched

        if match_ratio >= self.min_match_ratio and len(matched) >= self.min_keywords_matched:
            result['valid'] = True
            result['reason'] = f'证据充足，匹配关键词 {len(matched)}/{len(keywords)}'
            result['confidence'] = min(1.0, node.get('confidence', 1.0) * (0.8 + 0.2 * match_ratio))
        else:
            result['reason'] = f'证据不足，仅匹配 {len(matched)}/{len(keywords)} 关键词，比例 {match_ratio:.2f}'
            result['confidence'] = node.get('confidence', 1.0) * 0.3

        return result

    def _parse_pointer(self, pointer: str) -> dict | None:
        """解析 source_pointer 格式"""
        if pointer.startswith('archive://'):
            path_part = pointer[10:]
            parts = path_part.split('#', 1)
            return {
                'file_id': parts[0],
                'fragment': parts[1] if len(parts) > 1 else None,
                'file_path': os.path.join(self.archive_dir, parts[0]),
            }
        return None

    def _read_archive(self, pointer_info: dict) -> str | None:
        """读取归档文件内容"""
        file_path = pointer_info.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return None
        try:
            with open(file_path, encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    def _extract_keywords(self, node: dict) -> list:
        """从节点提取用于匹配的关键词"""
        keywords = []
        for field in ['title', 'description', 'outcome']:
            value = node.get(field, '') or ''
            if isinstance(value, str):
                words = re.split(r'[\s,.;:!?，。；：！？]+', value)
                keywords.extend([w for w in words if len(w) >= 2])

        entities = node.get('entities') or []
        if isinstance(entities, list):
            keywords.extend([str(e) for e in entities if len(str(e)) >= 2])

        return list(dict.fromkeys(keywords))

    def _match_keywords(self, keywords: list, content: str) -> list:
        """匹配关键词，返回命中的关键词列表"""
        content_lower = content.lower()
        matched = []
        for kw in keywords:
            if kw.lower() in content_lower:
                matched.append(kw)
        return matched

    def _get_snippet(self, content: str, max_len: int = 200) -> str:
        """截取归档内容片段"""
        if len(content) <= max_len:
            return content
        return content[:max_len] + '...[truncated]'


def verify_node_against_source(node: dict[str, Any],
                               source_pointer: str = None,
                               archive_dir: str = "./archives",
                               min_match_ratio: float = 0.3) -> dict[str, Any]:
    """独立函数接口：核验节点"""
    verifier = EvidenceVerifier(archive_dir=archive_dir,
                                min_match_ratio=min_match_ratio)
    return verifier.verify_node(node, source_pointer)
