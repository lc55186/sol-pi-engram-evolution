"""
Context Tracker：跨轮追踪模块
参考 Headroom Context Tracker：下一轮问题如果与之前压缩/归档的内容相关，
自动把原文展开，模型不用额外发请求就能拿到全量信息。
"""

import hashlib
import sqlite3
from datetime import datetime
from typing import Any

from graph_store import GraphStore


class ContextTracker:
    """
    跨轮追踪器：
    - 记录每轮对话/请求的上下文指纹
    - 检测新请求与历史上下文的语义相关性
    - 如果相关，自动将历史上下文展开到当前上下文
    """

    def __init__(self, tracker_db: str = "./context_tracker.db",
                 graph_store: GraphStore = None):
        self.tracker_db = tracker_db
        self.graph_store = graph_store or GraphStore()
        self._init_db()

    def _init_db(self):
        """初始化追踪数据库"""
        self.conn = sqlite3.connect(self.tracker_db)
        self.conn.row_factory = sqlite3.Row
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS context_rounds (
                round_id TEXT PRIMARY KEY,
                session_id TEXT,
                query TEXT,
                context_fingerprint TEXT,
                created_at TEXT,
                expanded_content TEXT,
                source_type TEXT DEFAULT 'graph',
                relevance_score REAL DEFAULT 1.0
            )
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_session
            ON context_rounds(session_id)
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_context_fingerprint
            ON context_rounds(context_fingerprint)
        """)
        self.conn.commit()

    def record_round(self, session_id: str, query: str,
                     context_fingerprint: str,
                     source_type: str = 'graph',
                     expanded_content: str = "") -> str:
        """
        记录一轮对话
        返回 round_id
        """
        round_id = hashlib.sha256(
            f"{session_id}:{query}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO context_rounds
            (round_id, session_id, query, context_fingerprint,
             created_at, expanded_content, source_type, relevance_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (round_id, session_id, query, context_fingerprint,
              datetime.now().isoformat(), expanded_content,
              source_type, 1.0))
        self.conn.commit()

        return round_id

    def track_relevance(self, session_id: str, new_query: str,
                        threshold: float = 0.3) -> list[dict[str, Any]]:
        """
        检测新请求与历史上下文的相关性
        返回相关的历史上下文列表
        """
        # 获取该会话的历史上下文
        cur = self.conn.cursor()
        cur.execute("""
            SELECT * FROM context_rounds
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (session_id,))
        history = cur.fetchall()

        relevant = []
        for row in history:
            # 计算相关性分数
            score = self._compute_relevance(new_query, row['query'])
            if score >= threshold:
                relevant.append({
                    'round_id': row['round_id'],
                    'query': row['query'],
                    'context_fingerprint': row['context_fingerprint'],
                    'expanded_content': row['expanded_content'] or "",
                    'source_type': row['source_type'],
                    'relevance_score': score,
                    'created_at': row['created_at'],
                })

        # 按相关性排序
        relevant.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant

    def _compute_relevance(self, query1: str, query2: str) -> float:
        """
        计算两个查询之间的相关性
        返回 0.0 - 1.0 之间的分数
        """
        # 简单启发式：关键词重叠
        words1 = set(query1.lower().split())
        words2 = set(query2.lower().split())
        if not words1 or not words2:
            return 0.0

        overlap = words1 & words2
        score = len(overlap) / min(len(words1), len(words2))
        return min(1.0, score)

    def expand_context(self, session_id: str, new_query: str,
                       max_expand: int = 3) -> dict[str, Any]:
        """
        展开相关的历史上下文到当前上下文
        返回展开结果
        """
        relevant = self.track_relevance(session_id, new_query)

        if not relevant:
            return {
                'expanded': False,
                'reason': '无相关历史上下文',
                'expanded_items': [],
            }

        # 取 top-k
        expanded_items = relevant[:max_expand]
        total_relevance = sum(item['relevance_score'] for item in expanded_items)
        avg_relevance = total_relevance / len(expanded_items) if expanded_items else 0

        # 合并展开内容
        combined_content = []
        for item in expanded_items:
            if item['expanded_content']:
                combined_content.append(item['expanded_content'])

        return {
            'expanded': True,
            'reason': f"找到 {len(expanded_items)} 个相关历史上下文",
            'expanded_items': expanded_items,
            'combined_content': "\n\n".join(combined_content),
            'avg_relevance': avg_relevance,
            'total_relevance': total_relevance,
        }

    def get_session_history(self, session_id: str,
                            limit: int = 20) -> list[dict[str, Any]]:
        """获取会话历史"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT round_id, query, context_fingerprint, created_at,
                   source_type, relevance_score
            FROM context_rounds
            WHERE session_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (session_id, limit))
        rows = cur.fetchall()
        return [dict(row) for row in rows]

    def clear_session(self, session_id: str):
        """清除会话历史"""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM context_rounds WHERE session_id = ?",
                    (session_id,))
        self.conn.commit()

    def get_stats(self) -> dict[str, Any]:
        """获取追踪统计"""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as cnt FROM context_rounds")
        total_rounds = cur.fetchone()['cnt']
        cur.execute("SELECT COUNT(DISTINCT session_id) as cnt FROM context_rounds")
        total_sessions = cur.fetchone()['cnt']
        return {
            'total_rounds': total_rounds,
            'total_sessions': total_sessions,
            'tracker_db': self.tracker_db,
        }

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None


# 便捷函数
def track_query(session_id: str, query: str,
                context_fingerprint: str,
                tracker: ContextTracker = None) -> str:
    """记录一轮查询"""
    if tracker is None:
        tracker = ContextTracker()
    return tracker.record_round(
        session_id, query, context_fingerprint
    )


def expand_for_session(session_id: str, new_query: str,
                       tracker: ContextTracker = None) -> dict[str, Any]:
    """为会话展开相关上下文"""
    if tracker is None:
        tracker = ContextTracker()
    return tracker.expand_context(session_id, new_query)
