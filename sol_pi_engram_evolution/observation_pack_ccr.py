"""
CCR 风格自动取回层（ObservationPack 之上的拦截缓存）
参考 Headroom CCR 协议：压缩不是删除，是暂存；
模型请求时通过本地拦截返回归档内容，延迟极低。
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Any


class CCRCache:
    """
    CCR 缓存层：
    - 归档内容存到 SQLite，本地拦截模型请求
    - 每个归档条目有唯一 hash 标记
    - 模型请求匹配 hash 时，本地直接返回，不走网络
    """

    def __init__(self, cache_db: str = "./ccr_cache.db",
                 observation_pack=None):
        self.cache_db = cache_db
        self.observation_pack = observation_pack
        self._init_db()

    def _init_db(self):
        import sqlite3
        self.conn = sqlite3.connect(self.cache_db)
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ccr_entries (
                hash TEXT PRIMARY KEY,
                content_id TEXT NOT NULL,
                content_type TEXT,
                archived_at TEXT,
                original_size INTEGER,
                content_hash TEXT,
                status TEXT DEFAULT 'cached',
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_ccr_hash ON ccr_entries(hash)
        """)
        self.conn.commit()

    def register(self, handle: dict[str, Any]) -> str:
        """
        注册一个归档条目到 CCR 缓存
        返回该条目的唯一 hash 标记
        """
        content_id = handle['content_id']
        content_hash = handle.get('content_hash')
        if not content_hash:
            # 如果没有 content_hash，基于内容生成
            content = handle.get('content', '')
            content_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
        content_type = handle.get('content_type', 'text')
        archived_at = handle.get('archived_at', datetime.now().isoformat())
        original_size = handle.get('original_size', 0)

        # 生成唯一 hash 标记（基于 content_id + content_hash）
        marker = hashlib.sha256(
            f"{content_id}:{content_hash}".encode()
        ).hexdigest()[:32]

        cur = self.conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO ccr_entries
            (hash, content_id, content_type, archived_at,
             original_size, content_hash, last_accessed, access_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
        """, (marker, content_id, content_type, archived_at,
              original_size, content_hash, archived_at))
        self.conn.commit()

        return marker

    def intercept(self, request_content: str,
                  request_type: str = "query") -> dict[str, Any] | None:
        """
        拦截模型请求，检查是否匹配已缓存的归档条目
        如果匹配，返回缓存内容；否则返回 None
        """
        # 提取请求中的 hash 标记（如果有）
        marker = self._extract_marker(request_content)
        if marker:
            entry = self._get_entry_by_hash(marker)
            if entry:
                # 找到归档，取回内容
                handle = self.retrieve_by_content_id(
                    entry['content_id']
                )
                if handle:
                    self._record_access(marker)
                    return {
                        'hit': True,
                        'marker': marker,
                        'content': handle['content'],
                        'content_id': entry['content_id'],
                        'content_type': entry['content_type'],
                        'source': 'ccr_cache',
                        'latency_ms': 1,  # 本地拦截，极低延迟
                    }

        # 尝试内容匹配（基于关键词/语义的启发式）
        handle = self._content_match(request_content, request_type)
        if handle:
            marker = self.register(handle)
            self._record_access(marker)
            return {
                'hit': True,
                'marker': marker,
                'content': handle['content'],
                'content_id': handle['content_id'],
                'content_type': handle['content_type'],
                'source': 'ccr_cache_auto',
                'latency_ms': 1,
            }

        return None

    def _extract_marker(self, request_content: str) -> str | None:
        """从请求中提取 hash 标记"""
        # 标记可能以 [CCR:hash] 或 {ccr: hash} 形式出现
        import re
        patterns = [
            r'\[CCR:([a-f0-9]{32})\]',
            r'\{ccr:\s*([a-f0-9]{32})\}',
            r'ccr_marker=["\']([a-f0-9]{32})["\']',
        ]
        for pattern in patterns:
            match = re.search(pattern, request_content)
            if match:
                return match.group(1)
        return None

    def _get_entry_by_hash(self, marker: str) -> dict | None:
        """根据 hash 标记获取缓存条目"""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM ccr_entries WHERE hash = ?", (marker,))
        row = cur.fetchone()
        return dict(row) if row else None

    def _record_access(self, marker: str):
        """记录访问"""
        cur = self.conn.cursor()
        cur.execute("""
            UPDATE ccr_entries
            SET last_accessed = ?, access_count = access_count + 1
            WHERE hash = ?
        """, (datetime.now().isoformat(), marker))
        self.conn.commit()

    def _content_match(self, request_content: str,
                       request_type: str) -> dict | None:
        """
        基于内容匹配的启发式检索
        如果请求与某个归档条目语义相关，返回该条目
        """
        # 简单启发式：检查请求中是否包含归档的关键词
        # 实际实现中应使用更 sophisticated 的匹配
        # 这里我们遍历所有已缓存条目，检查是否与请求相关
        # 由于 ObservationPack 没有直接的搜索接口，
        # 我们可以检查最近归档的条目
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM ccr_entries
            ORDER BY last_accessed DESC
            LIMIT 100
        """)
        entries = cur.fetchall()

        for entry in entries:
            # 尝试从 ObservationPack 取回内容，检查是否相关
            try:
                handle = self.retrieve_by_content_id(
                    entry['content_id']
                )
                if handle and self._is_relevant(handle['content'],
                                                request_content):
                    return handle
            except Exception:
                continue

        return None

    def _is_relevant(self, archived_content: str,
                     request_content: str) -> bool:
        """检查归档内容是否与请求相关"""
        # 简单启发式：检查请求中的关键词是否在归档中出现
        # 对于中文（无空格分隔），使用子串匹配
        if any('\u4e00' <= c <= '\u9fff' for c in request_content):
            # 中文场景：请求是归档的子串即认为相关
            return request_content.lower() in archived_content.lower()
        # 英文/混合场景：词重叠
        request_words = set(request_content.lower().split())
        archived_words = set(archived_content.lower().split())
        overlap = request_words & archived_words
        # 如果有至少 2 个词重叠，认为相关
        return len(overlap) >= 2

    def retrieve_by_content_id(self, content_id: str) -> dict | None:
        """根据 content_id 从 ObservationPack 取回"""
        # 列出所有归档，找到匹配的
        archives = self.observation_pack.list_archives()
        for archive in archives:
            if archive.get('content_id') == content_id:
                filepath = archive['filepath']
                if os.path.exists(filepath):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    meta_path = f"{filepath}.meta.json"
                    meta = {}
                    if os.path.exists(meta_path):
                        with open(meta_path, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                    return {
                        'content': content,
                        'content_id': content_id,
                        'content_type': archive.get('content_type', 'text'),
                        'metadata': meta,
                        'filepath': filepath,
                    }
        return None

    def get_stats(self) -> dict[str, Any]:
        """获取 CCR 缓存统计"""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM ccr_entries")
        total = cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(*) as cnt FROM ccr_entries WHERE access_count > 0")
        accessed = cur.fetchone()['cnt']
        cur.execute("SELECT SUM(original_size) as total FROM ccr_entries")
        total_size = cur.fetchone()['total'] or 0
        return {
            'total_entries': total,
            'accessed_entries': accessed,
            'total_size_bytes': total_size,
            'cache_db': self.cache_db,
        }

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


# 便捷函数
def ccr_register(handle: dict[str, Any],
                  cache: CCRCache = None) -> str:
    """注册到 CCR 缓存"""
    if cache is None:
        cache = CCRCache()
    return cache.register(handle)


def ccr_intercept(request_content: str,
                  request_type: str = "query",
                  cache: CCRCache = None) -> dict[str, Any] | None:
    """拦截请求，检查 CCR 缓存"""
    if cache is None:
        cache = CCRCache()
    return cache.intercept(request_content, request_type)
