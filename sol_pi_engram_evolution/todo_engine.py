#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Autonomous TODO Engine — 自主待办引擎
自动检查、完成、新增、记录待办任务
"""

import sqlite3
import os
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "graph.db")
LOG_PATH = os.path.join(os.path.dirname(__file__), "todo_log.jsonl")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class TodoEngine:
    """自主待办引擎"""

    def __init__(self):
        self.conn = get_db()
        self.cursor = self.conn.cursor()
        self.log_entries = []

    def close(self):
        self.conn.close()

    def check_pending(self) -> List[Dict]:
        """检查待处理任务"""
        self.cursor.execute("""
            SELECT n.*, t.status, t.priority, t.related_event_ids
            FROM nodes n
            LEFT JOIN tasks t ON n.node_id = t.node_id
            WHERE n.node_type = 'task' AND t.status = 'not_started'
            ORDER BY t.priority DESC, n.created_at ASC
        """)
        return [dict(r) for r in self.cursor.fetchall()]

    def complete_task(self, node_id: str, resolution: str = ""):
        """完成一个任务"""
        # 更新任务状态
        self.cursor.execute(
            "UPDATE tasks SET status = 'completed' WHERE node_id = ?",
            (node_id,)
        )
        # 更新时间戳
        self.cursor.execute(
            "UPDATE nodes SET updated_at = datetime('now') WHERE node_id = ?",
            (node_id,)
        )
        # 创建完成事件节点
        event_id = f"complete-{node_id}"
        self.cursor.execute("""
            INSERT OR REPLACE INTO nodes 
            (node_id, node_type, created_at, updated_at, title, description, confidence, source_pointer)
            VALUES (?, 'event', datetime('now'), datetime('now'), ?, ?, 1.0, 'auto_complete')
        """, (event_id, f"完成: {node_id}", resolution))
        # 创建完成关系
        rel_id = f"rel-{event_id}"
        self.cursor.execute("""
            INSERT OR REPLACE INTO relations 
            (relation_id, source_node_id, target_node_id, relation_type, weight, description, confidence, source_pointer)
            VALUES (?, ?, ?, 'completed_as', 1.0, '任务完成', 1.0, 'auto_rel')
        """, (rel_id, node_id, event_id))

        self.log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "action": "complete",
            "node_id": node_id,
            "resolution": resolution
        })
        return True

    def add_task(self, title: str, description: str, priority: int = 3,
                 related_event: str = "", source: str = "auto_todo") -> str:
        """添加新任务"""
        # 生成唯一ID
        self.cursor.execute("SELECT COUNT(*) FROM nodes WHERE node_type = 'task'")
        count = self.cursor.fetchone()[0] + 1
        node_id = f"todo-new-{count:03d}"

        # 插入节点
        self.cursor.execute("""
            INSERT INTO nodes 
            (node_id, node_type, created_at, updated_at, title, description, confidence, source_pointer, importance_score, decay_rate)
            VALUES (?, 'task', datetime('now'), datetime('now'), ?, ?, 1.0, ?, 0.85, 0.95)
        """, (node_id, title, description, source))

        # 插入任务
        rel_ids = json.dumps([related_event]) if related_event else "[]"
        self.cursor.execute("""
            INSERT INTO tasks (node_id, status, priority, related_event_ids, related_task_ids)
            VALUES (?, 'not_started', ?, ?, '[]')
        """, (node_id, priority, rel_ids))

        self.log_entries.append({
            "timestamp": datetime.now().isoformat(),
            "action": "add",
            "node_id": node_id,
            "title": title,
            "priority": priority
        })
        return node_id

    def extract_todos_from_events(self) -> List[Dict]:
        """从事件节点中提取待办"""
        new_todos = []

        # 查找有"需求"、"待"、"需要"等关键词的事件
        self.cursor.execute("""
            SELECT * FROM nodes 
            WHERE node_type = 'event' 
            AND (title LIKE '%需求%' OR title LIKE '%待%' OR title LIKE '%需要%' OR title LIKE '%谈判%')
        """)
        events = [dict(r) for r in self.cursor.fetchall()]

        for event in events:
            title = event.get("title", "")
            desc = event.get("description", "")
            event_id = event["node_id"]

            # 检查是否已存在相关待办
            self.cursor.execute(
                "SELECT COUNT(*) FROM tasks WHERE related_event_ids LIKE ?",
                (f"%{event_id}%",)
            )
            existing = self.cursor.fetchone()[0]
            if existing > 0:
                continue

            # 根据事件内容生成待办
            if "需求" in title or "需求" in desc:
                new_todos.append({
                    "title": f"跟进: {title}",
                    "description": f"源自事件: {desc}",
                    "priority": 4,
                    "related_event": event_id
                })
            elif "谈判" in title or "谈判" in desc:
                new_todos.append({
                    "title": f"谈判准备: {title}",
                    "description": f"源自事件: {desc}",
                    "priority": 5,
                    "related_event": event_id
                })

        return new_todos

    def log_to_file(self):
        """记录到日志文件"""
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            for entry in self.log_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def generate_report(self) -> str:
        """生成待办报告"""
        pending = self.check_pending()
        completed = self.completed_tasks()

        report = f"""# 📋 待办报告 — {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 待处理任务 ({len(pending)})
"""
        for t in pending:
            priority_icon = "🔴" if t.get("priority", 3) >= 4 else "🟡"
            report += f"- {priority_icon} **[P{t.get('priority', 3)}]** {t.get('title', '无标题')}\n"
            report += f"  - {t.get('description', '无描述')}\n"

        report += f"\n## 已完成任务 ({len(completed)})\n"
        for t in completed[:5]:  # 最近5个
            report += f"- ✅ {t.get('title', t.get('node_id', '未知'))}\n"

        report += f"\n## 日志\n"
        report += f"- 操作数: {len(self.log_entries)}\n"
        report += f"- 时间: {datetime.now().isoformat()}\n"

        return report

    def completed_tasks(self) -> List[Dict]:
        """获取已完成任务"""
        self.cursor.execute("""
            SELECT n.*, t.status
            FROM nodes n
            LEFT JOIN tasks t ON n.node_id = t.node_id
            WHERE t.status = 'completed'
            ORDER BY n.updated_at DESC
        """)
        return [dict(r) for r in self.cursor.fetchall()]

    def run_autonomous_cycle(self):
        """运行一个完整的自主循环"""
        print("=" * 60)
        print("🤖 自主待办循环启动")
        print("=" * 60)

        # 1. 检查现有待办
        pending = self.check_pending()
        print(f"\n[1/4] 检查待办: {len(pending)} 个待处理")

        # 2. 尝试完成可自动完成的任务
        completed_count = 0
        for task in pending:
            # P5 且有决策支持的任务可以自动完成
            if task.get("priority", 3) >= 5 and "negotiation" in task.get("related_event_ids", ""):
                # 检查是否有完成的决策
                event_id = json.loads(task.get("related_event_ids", "[]"))
                if event_id:
                    self.cursor.execute(
                        "SELECT COUNT(*) FROM nodes WHERE node_id LIKE 'decision%' AND updated_at > ?",
                        (task.get("created_at"),)
                    )
                    has_decision = self.cursor.fetchone()[0] > 0
                    if has_decision:
                        self.complete_task(task["node_id"], "决策已执行，自动完成")
                        completed_count += 1
                        print(f"  ✅ 自动完成: {task.get('title')}")

        # 3. 从事件提取新待办
        new_todos = self.extract_todos_from_events()
        added_count = 0
        for todo in new_todos:
            self.add_task(
                title=todo["title"],
                description=todo["description"],
                priority=todo.get("priority", 3),
                related_event=todo.get("related_event", ""),
                source="auto_extract"
            )
            added_count += 1
            print(f"  ➕ 新增待办: {todo['title']}")

        # 4. 记录并提交
        self.log_to_file()
        self.conn.commit()

        # 5. 生成报告
        report = self.generate_report()
        print(f"\n[2/4] 完成: {completed_count} 个")
        print(f"[3/4] 新增: {added_count} 个")
        print(f"[4/4] 记录已保存")

        return report


if __name__ == "__main__":
    engine = TodoEngine()
    try:
        report = engine.run_autonomous_cycle()
        print("\n" + report)
    finally:
        engine.close()
