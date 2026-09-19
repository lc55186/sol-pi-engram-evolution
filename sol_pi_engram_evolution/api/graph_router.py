#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph API Router — 图谱 API 接口
提供 RESTful 接口操作图谱：查询/添加/更新/删除/搜索/分析
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sqlite3
import json
import os

router = APIRouter(prefix="/api/v1/graph", tags=["Graph"])


def get_db():
    db_path = os.path.join(os.path.dirname(__file__), "..", "graph.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


class NodeCreate(BaseModel):
    node_id: str
    node_type: str  # task, event, customer, negotiation, opportunity, risk, decision, todo
    title: str
    description: str = ""
    confidence: float = 1.0
    source_pointer: str = ""
    importance_score: float = 0.5
    decay_rate: float = 0.95
    status: Optional[str] = None  # for tasks
    priority: Optional[int] = None  # for tasks
    event_type: Optional[str] = None  # for events
    entities: Optional[List[str]] = None  # for events
    outcome: Optional[str] = None  # for events


class RelationCreate(BaseModel):
    relation_id: str
    source_node_id: str
    target_node_id: str
    relation_type: str = "related_to"
    weight: float = 0.5
    description: str = ""
    confidence: float = 1.0
    source_pointer: str = ""


@router.get("/nodes")
def get_nodes(node_type: Optional[str] = None, limit: int = 100):
    """获取节点列表"""
    conn = get_db()
    cursor = conn.cursor()
    if node_type:
        cursor.execute("SELECT * FROM nodes WHERE node_type = ? LIMIT ?", (node_type, limit))
    else:
        cursor.execute("SELECT * FROM nodes LIMIT ?", (limit,))
    nodes = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return nodes


@router.get("/nodes/{node_id}")
def get_node(node_id: str):
    """获取单个节点"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nodes WHERE node_id = ?", (node_id,))
    node = cursor.fetchone()
    conn.close()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return dict(node)


@router.post("/nodes")
def create_node(node: NodeCreate):
    """创建节点"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 插入 nodes 表
    cursor.execute("""
        INSERT INTO nodes (node_id, node_type, created_at, updated_at, title, description, 
                          confidence, source_pointer, importance_score, decay_rate)
        VALUES (?, ?, datetime('now'), datetime('now'), ?, ?, ?, ?, ?, ?)
    """, (node.node_id, node.node_type, node.title, node.description,
          node.confidence, node.source_pointer, node.importance_score, node.decay_rate))
    
    # 根据类型插入子表
    if node.node_type == "task" and node.status:
        cursor.execute("""
            INSERT INTO tasks (node_id, status, priority, related_event_ids, related_task_ids)
            VALUES (?, ?, ?, '[]', '[]')
        """, (node.node_id, node.status, node.priority or 3))
    elif node.node_type == "event" and node.event_type:
        cursor.execute("""
            INSERT INTO events (node_id, event_type, timestamp, entities, outcome)
            VALUES (?, ?, datetime('now'), ?, ?)
        """, (node.node_id, node.event_type, json.dumps(node.entities or []), node.outcome or ""))
    
    conn.commit()
    conn.close()
    return {"status": "created", "node_id": node.node_id}


@router.delete("/nodes/{node_id}")
def delete_node(node_id: str):
    """删除节点"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM relations WHERE source_node_id = ? OR target_node_id = ?", (node_id, node_id))
    cursor.execute("DELETE FROM tasks WHERE node_id = ?", (node_id,))
    cursor.execute("DELETE FROM events WHERE node_id = ?", (node_id,))
    cursor.execute("DELETE FROM nodes WHERE node_id = ?", (node_id,))
    conn.commit()
    conn.close()
    return {"status": "deleted"}


@router.get("/relations")
def get_relations(node_id: Optional[str] = None):
    """获取关系"""
    conn = get_db()
    cursor = conn.cursor()
    if node_id:
        cursor.execute("SELECT * FROM relations WHERE source_node_id = ? OR target_node_id = ?", (node_id, node_id))
    else:
        cursor.execute("SELECT * FROM relations")
    relations = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return relations


@router.post("/relations")
def create_relation(rel: RelationCreate):
    """创建关系"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO relations (relation_id, source_node_id, target_node_id, relation_type, 
                              weight, description, confidence, source_pointer, access_count, 
                              importance_score, decay_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0.5, 0.95)
    """, (rel.relation_id, rel.source_node_id, rel.target_node_id, rel.relation_type,
          rel.weight, rel.description, rel.confidence, rel.source_pointer))
    conn.commit()
    conn.close()
    return {"status": "created", "relation_id": rel.relation_id}


@router.get("/search")
def search_nodes(q: str = Query(..., description="Search query")):
    """搜索节点"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM nodes 
        WHERE title LIKE ? OR description LIKE ?
        ORDER BY importance_score DESC
        LIMIT 20
    """, (f"%{q}%", f"%{q}%"))
    results = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return results


@router.get("/stats")
def get_stats():
    """图谱统计"""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {}
    cursor.execute("SELECT COUNT(*) FROM nodes")
    stats["total_nodes"] = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM relations")
    stats["total_relations"] = cursor.fetchone()[0]
    cursor.execute("SELECT node_type, COUNT(*) FROM nodes GROUP BY node_type")
    stats["type_distribution"] = {r[0]: r[1] for r in cursor.fetchall()}
    cursor.execute("SELECT relation_type, COUNT(*) FROM relations GROUP BY relation_type")
    stats["relation_distribution"] = {r[0]: r[1] for r in cursor.fetchall()}
    
    conn.close()
    return stats


@router.get("/visualization")
def get_visualization():
    """获取可视化数据"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nodes")
    nodes = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM relations")
    relations = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {"nodes": nodes, "relations": relations}


@router.get("/mermaid")
def get_mermaid():
    """获取 Mermaid 图"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM nodes LIMIT 50")
    nodes = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM relations LIMIT 50")
    relations = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    lines = ["graph TD"]
    for node in nodes:
        nid = node['node_id']
        title = node.get('title', 'Unknown')[:30]
        lines.append(f"    {nid}[{title}]")
    
    for rel in relations:
        src = rel['source_node_id']
        tgt = rel['target_node_id']
        rtype = rel.get('relation_type', 'related_to')
        lines.append(f"    {src} -->|{rtype}| {tgt}")
    
    return {"mermaid": "\n".join(lines)}


@router.get("/html", response_class=HTMLResponse)
def get_html_visualization():
    """获取 HTML 可视化页面"""
    html_path = os.path.join(os.path.dirname(__file__), "..", "ui", "templates", "graph.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Graph visualization not found</h1>"


# HTML 页面路由
@router.get("/view", response_class=HTMLResponse)
def graph_view():
    """图谱可视化页面"""
    return get_html_visualization()
