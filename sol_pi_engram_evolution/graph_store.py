"""
阶段 1：图谱存储模块
SQLite-based 本地图谱存储
"""

import json
import sqlite3
from datetime import datetime


class GraphStore:
    """本地图谱存储，基于 SQLite"""

    def __init__(self, db_path: str = "graph.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """初始化数据库架构"""
        cursor = self.conn.cursor()

        # 统一节点元数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                node_id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                importance_score REAL DEFAULT 0.5,
                decay_rate REAL DEFAULT 0.95,
                confidence REAL DEFAULT 1.0,
                source_pointer TEXT,
                title TEXT,
                description TEXT
            )
        """)

        # 任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                node_id TEXT PRIMARY KEY,
                status TEXT DEFAULT 'not_started',
                priority INTEGER DEFAULT 3,
                related_event_ids TEXT DEFAULT '[]',
                related_task_ids TEXT DEFAULT '[]',
                FOREIGN KEY (node_id) REFERENCES nodes(node_id)
            )
        """)

        # 事件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                node_id TEXT PRIMARY KEY,
                event_type TEXT DEFAULT 'other',
                timestamp TEXT,
                entities TEXT DEFAULT '[]',
                outcome TEXT DEFAULT '',
                FOREIGN KEY (node_id) REFERENCES nodes(node_id)
            )
        """)

        # 关系表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS relations (
                relation_id TEXT PRIMARY KEY,
                source_node_id TEXT NOT NULL,
                target_node_id TEXT NOT NULL,
                relation_type TEXT DEFAULT 'related_to',
                weight REAL DEFAULT 0.5,
                description TEXT DEFAULT '',
                confidence REAL DEFAULT 1.0,
                source_pointer TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed TEXT,
                importance_score REAL DEFAULT 0.5,
                decay_rate REAL DEFAULT 0.95
            )
        """)

        # 关系索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relations_source
            ON relations(source_node_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_relations_target
            ON relations(target_node_id)
        """)

        self.conn.commit()

    _counter = 0

    def add_task_node(self, title: str = "", description: str = "",
                      status: str = "not_started", priority: int = 3,
                      source_pointer: str = "", confidence: float = 1.0,
                      importance_score: float = 0.5,
                      decay_rate: float = 0.95) -> dict:
        """添加任务节点"""
        GraphStore._counter += 1
        node_id = f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}-{GraphStore._counter}"
        now = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO nodes
               (node_id, node_type, created_at, updated_at,
                title, description, confidence, source_pointer,
                importance_score, decay_rate, access_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (node_id, "task", now, now, title, description,
             confidence, source_pointer, importance_score,
             decay_rate, 0)
        )
        cursor.execute(
            """INSERT INTO tasks
               (node_id, status, priority, related_event_ids, related_task_ids)
               VALUES (?, ?, ?, ?, ?)""",
            (node_id, status, priority, "[]", "[]")
        )
        self.conn.commit()

        return self.get_node_by_id(node_id)

    def add_event_node(self, title: str = "", description: str = "",
                       event_type: str = "other",
                       entities: list[str] = None, outcome: str = "",
                       source_pointer: str = "", confidence: float = 1.0,
                       importance_score: float = 0.5,
                       decay_rate: float = 0.95) -> dict:
        """添加事件节点"""
        GraphStore._counter += 1
        node_id = f"event-{datetime.now().strftime('%Y%m%d%H%M%S')}-{GraphStore._counter}"
        now = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO nodes
               (node_id, node_type, created_at, updated_at,
                title, description, confidence, source_pointer,
                importance_score, decay_rate, access_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (node_id, "event", now, now, title, description,
             confidence, source_pointer, importance_score,
             decay_rate, 0)
        )
        cursor.execute(
            """INSERT INTO events
               (node_id, event_type, timestamp, entities, outcome)
               VALUES (?, ?, ?, ?, ?)""",
            (node_id, event_type, now,
             json.dumps(entities or []), outcome)
        )
        self.conn.commit()

        return self.get_node_by_id(node_id)

    def add_relation(self, source_node_id: str, target_node_id: str,
                     relation_type: str = "related_to",
                     weight: float = 0.5, description: str = "",
                     confidence: float = 1.0,
                     source_pointer: str = "",
                     importance_score: float = 0.5,
                     decay_rate: float = 0.95) -> dict:
        """添加关系"""
        GraphStore._counter += 1
        relation_id = f"rel-{source_node_id}-{target_node_id}-{GraphStore._counter}"
        now = datetime.now().isoformat()

        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT INTO relations
               (relation_id, source_node_id, target_node_id,
                relation_type, weight, description, confidence,
                source_pointer, access_count, last_accessed,
                importance_score, decay_rate)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (relation_id, source_node_id, target_node_id,
             relation_type, weight, description, confidence,
             source_pointer, 0, None, importance_score, decay_rate)
        )
        self.conn.commit()

        return self.get_relation_by_id(relation_id)

    def get_node_by_id(self, node_id: str) -> dict | None:
        """根据节点 ID 获取完整节点"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
        node_row = cursor.fetchone()
        if node_row is None:
            return None

        node = dict(node_row)
        node_type = node['node_type']

        if node_type == 'task':
            cursor.execute("SELECT * FROM tasks WHERE node_id = ?", (node_id,))
            task_row = cursor.fetchone()
            if task_row:
                task_data = dict(task_row)
                node['status'] = task_data['status']
                node['priority'] = task_data['priority']
                node['related_event_ids'] = json.loads(task_data['related_event_ids'])
                node['related_task_ids'] = json.loads(task_data['related_task_ids'])
        elif node_type == 'event':
            cursor.execute("SELECT * FROM events WHERE node_id = ?", (node_id,))
            event_row = cursor.fetchone()
            if event_row:
                event_data = dict(event_row)
                node['event_type'] = event_data['event_type']
                node['timestamp'] = event_data['timestamp']
                node['entities'] = json.loads(event_data['entities'])
                node['outcome'] = event_data['outcome']

        node['access_count'] = node.get('access_count', 0)
        node['last_accessed'] = node.get('last_accessed')
        return node

    def get_task_node_by_title(self, title: str) -> dict | None:
        """根据标题获取任务节点"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT node_id FROM nodes WHERE node_type = 'task' AND title = ?",
            (title,)
        )
        row = cursor.fetchone()
        if row:
            return self.get_node_by_id(row['node_id'])
        return None

    def get_event_node_by_title(self, title: str) -> dict | None:
        """根据标题获取事件节点"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT node_id FROM nodes WHERE node_type = 'event' AND title = ?",
            (title,)
        )
        row = cursor.fetchone()
        if row:
            return self.get_node_by_id(row['node_id'])
        return None

    def get_relations_for_node(self, node_id: str) -> list[dict]:
        """获取与指定节点相关的所有关系"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM relations WHERE source_node_id = ? OR target_node_id = ?",
            (node_id, node_id)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_relation_by_id(self, relation_id: str) -> dict | None:
        """根据关系 ID 获取关系"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM relations WHERE relation_id = ?", (relation_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_nodes(self) -> list[dict]:
        """获取所有节点"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM nodes")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_node_stats(self) -> dict[str, int]:
        """获取图谱统计"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM nodes WHERE node_type = 'task'")
        task_count = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) as cnt FROM nodes WHERE node_type = 'event'")
        event_count = cursor.fetchone()['cnt']
        cursor.execute("SELECT COUNT(*) as cnt FROM relations")
        relation_count = cursor.fetchone()['cnt']
        return {
            'task_count': task_count,
            'event_count': event_count,
            'relation_count': relation_count,
            'total_node_count': task_count + event_count,
        }

    def delete_node(self, node_id: str) -> bool:
        """删除节点及其关联关系"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM relations WHERE source_node_id = ? OR target_node_id = ?",
                       (node_id, node_id))
        cursor.execute("DELETE FROM tasks WHERE node_id = ?", (node_id,))
        cursor.execute("DELETE FROM events WHERE node_id = ?", (node_id,))
        cursor.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def delete_relation(self, relation_id: str) -> bool:
        """删除关系"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM relations WHERE relation_id = ?", (relation_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
