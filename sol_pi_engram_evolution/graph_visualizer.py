#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Visualization Engine - 图谱可视化引擎
生成 Mermaid 图、交互式 HTML、统计分析
"""

import sqlite3
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class GraphVisualizer:
    """图谱可视化引擎"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _query(self, sql: str, params: tuple = ()) -> List[dict]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    def generate_mermaid(self, limit: int = 50) -> str:
        """生成 Mermaid 关系图"""
        nodes = self._query("SELECT * FROM nodes LIMIT ?", (limit,))
        relations = self._query("SELECT * FROM relations LIMIT ?", (limit,))

        lines = ["graph TD"]

        # 节点定义
        node_defs = {}
        for node in nodes:
            nid = node['node_id']
            title = node.get('title', 'Unknown')[:30]
            ntype = node.get('node_type', 'unknown')

            # 根据类型选择样式
            if ntype == 'task':
                shape = f"[{title}]"
                style = "classDef task fill:#4CAF50,stroke:#388E3C,color:#fff"
            elif ntype == 'event':
                shape = f"({title})"
                style = "classDef event fill:#2196F3,stroke:#1976D2,color:#fff"
            else:
                shape = f"[{title}]"
                style = ""

            node_defs[nid] = f"{nid}{shape}"
            lines.append(f"    {nid}{shape}")

        # 关系定义
        for rel in relations:
            src = rel['source_node_id']
            tgt = rel['target_node_id']
            rtype = rel.get('relation_type', 'related_to')
            weight = rel.get('weight', 0.5)

            if src in node_defs and tgt in node_defs:
                # 根据权重选择线型
                if weight > 0.8:
                    line = "==>"
                elif weight > 0.5:
                    line = "-->"
                else:
                    line = "-.->"

                label = rtype[:10]
                lines.append(f"    {src} {line}|{label}| {tgt}")

        # 添加样式
        lines.append("    classDef task fill:#4CAF50,stroke:#388E3C,color:#fff")
        lines.append("    classDef event fill:#2196F3,stroke:#1976D2,color:#fff")
        lines.append("    classDef customer fill:#FF9800,stroke:#F57C00,color:#fff")
        lines.append("    classDef risk fill:#F44336,stroke:#D32F2F,color:#fff")
        lines.append("    classDef opportunity fill:#8BC34A,stroke:#689F38,color:#fff")
        lines.append("    classDef decision fill:#9C27B0,stroke:#7B1FA2,color:#fff")

        # 应用样式
        for node in nodes:
            ntype = node.get('node_type', '')
            nid = node['node_id']
            if ntype == 'task':
                lines.append(f"    class {nid} task")
            elif ntype == 'event':
                lines.append(f"    class {nid} event")

        return "\n".join(lines)

    def generate_html(self, output_path: str):
        """生成交互式 HTML 可视化"""
        nodes = self._query("SELECT * FROM nodes")
        relations = self._query("SELECT * FROM relations")

        # 转换为 JSON 供前端使用
        graph_data = {
            "nodes": nodes,
            "relations": relations,
            "generated_at": datetime.now().isoformat()
        }

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BOSS-AI-R 知识图谱</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 0; background: #1a1a2e; color: #eee; }}
        #graph {{ width: 100vw; height: 100vh; }}
        .node {{ cursor: pointer; }}
        .node circle {{ stroke: #fff; stroke-width: 2px; }}
        .node text {{ font-size: 12px; fill: #fff; pointer-events: none; }}
        .link {{ stroke-opacity: 0.6; }}
        .link-label {{ font-size: 10px; fill: #aaa; }}
        #info-panel {{
            position: fixed; top: 20px; right: 20px; width: 300px;
            background: rgba(0,0,0,0.8); padding: 20px; border-radius: 10px;
            border: 1px solid #444; display: none;
        }}
        #info-panel h3 {{ margin-top: 0; color: #4CAF50; }}
        #info-panel .label {{ color: #888; font-size: 12px; }}
        #info-panel .value {{ color: #fff; margin-bottom: 10px; }}
        #stats {{
            position: fixed; bottom: 20px; left: 20px;
            background: rgba(0,0,0,0.8); padding: 15px; border-radius: 10px;
            border: 1px solid #444;
        }}
        #stats h4 {{ margin: 0 0 10px 0; color: #2196F3; }}
        #stats .stat {{ display: flex; justify-content: space-between; margin-bottom: 5px; }}
        #stats .stat-label {{ color: #888; }}
        #stats .stat-value {{ color: #4CAF50; font-weight: bold; }}
    </style>
</head>
<body>
    <div id="graph"></div>
    <div id="info-panel">
        <h3 id="node-title">节点详情</h3>
        <div class="label">类型</div>
        <div class="value" id="node-type">-</div>
        <div class="label">描述</div>
        <div class="value" id="node-desc">-</div>
        <div class="label">置信度</div>
        <div class="value" id="node-confidence">-</div>
        <div class="label">来源</div>
        <div class="value" id="node-source">-</div>
    </div>
    <div id="stats">
        <h4>📊 图谱统计</h4>
        <div class="stat"><span class="stat-label">节点总数</span><span class="stat-value" id="total-nodes">0</span></div>
        <div class="stat"><span class="stat-label">关系总数</span><span class="stat-value" id="total-relations">0</span></div>
        <div class="stat"><span class="stat-label">任务节点</span><span class="stat-value" id="task-nodes">0</span></div>
        <div class="stat"><span class="stat-label">事件节点</span><span class="stat-value" id="event-nodes">0</span></div>
    </div>
    <script>
        const graphData = {json.dumps(graph_data, ensure_ascii=False)};

        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#graph").append("svg")
            .attr("width", width)
            .attr("height", height);

        const g = svg.append("g");

        // 缩放
        svg.call(d3.zoom().on("zoom", (event) => {{
            g.attr("transform", event.transform);
        }}));

        // 力导向图
        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.relations).id(d => d.node_id).distance(150))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(50));

        // 连线
        const link = g.append("g")
            .selectAll("line")
            .data(graphData.relations)
            .enter().append("line")
            .attr("class", "link")
            .attr("stroke", d => d.weight > 0.8 ? "#F44336" : d.weight > 0.5 ? "#FF9800" : "#4CAF50")
            .attr("stroke-width", d => d.weight * 3);

        // 连线标签
        const linkLabel = g.append("g")
            .selectAll("text")
            .data(graphData.relations)
            .enter().append("text")
            .attr("class", "link-label")
            .attr("text-anchor", "middle")
            .text(d => d.relation_type);

        // 节点
        const node = g.append("g")
            .selectAll("g")
            .data(graphData.nodes)
            .enter().append("g")
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        // 节点圆圈
        node.append("circle")
            .attr("r", d => d.node_type === 'task' ? 25 : 20)
            .attr("fill", d => {{
                if (d.node_type === 'task') return '#4CAF50';
                if (d.title.includes('风险')) return '#F44336';
                if (d.title.includes('商机')) return '#8BC34A';
                if (d.title.includes('决策')) return '#9C27B0';
                return '#2196F3';
            }});

        // 节点标签
        node.append("text")
            .attr("dy", 35)
            .attr("text-anchor", "middle")
            .text(d => d.title.length > 10 ? d.title.substring(0, 10) + '...' : d.title);

        // 点击事件
        node.on("click", (event, d) => {{
            const panel = document.getElementById('info-panel');
            panel.style.display = 'block';
            document.getElementById('node-title').textContent = d.title;
            document.getElementById('node-type').textContent = d.node_type;
            document.getElementById('node-desc').textContent = d.description || '无描述';
            document.getElementById('node-confidence').textContent = (d.confidence * 100).toFixed(0) + '%';
            document.getElementById('node-source').textContent = d.source_pointer || '未知';
        }});

        // 更新统计
        document.getElementById('total-nodes').textContent = graphData.nodes.length;
        document.getElementById('total-relations').textContent = graphData.relations.length;
        document.getElementById('task-nodes').textContent = graphData.nodes.filter(n => n.node_type === 'task').length;
        document.getElementById('event-nodes').textContent = graphData.nodes.filter(n => n.node_type === 'event').length;

        // 仿真
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            linkLabel
                .attr("x", d => (d.source.x + d.target.x) / 2)
                .attr("y", d => (d.source.y + d.target.y) / 2);

            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});

        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path

    def get_analytics(self) -> Dict[str, Any]:
        """图谱分析统计"""
        nodes = self._query("SELECT * FROM nodes")
        relations = self._query("SELECT * FROM relations")

        # 节点类型分布
        type_dist = {}
        for n in nodes:
            t = n.get('node_type', 'unknown')
            type_dist[t] = type_dist.get(t, 0) + 1

        # 关系类型分布
        rel_dist = {}
        for r in relations:
            t = r.get('relation_type', 'unknown')
            rel_dist[t] = rel_dist.get(t, 0) + 1

        # 高置信度节点
        high_conf = [n for n in nodes if n.get('confidence', 0) > 0.9]

        # 关键节点（连接数最多）
        conn_count = {}
        for r in relations:
            src = r['source_node_id']
            tgt = r['target_node_id']
            conn_count[src] = conn_count.get(src, 0) + 1
            conn_count[tgt] = conn_count.get(tgt, 0) + 1

        top_connected = sorted(conn_count.items(), key=lambda x: -x[1])[:5]

        return {
            "total_nodes": len(nodes),
            "total_relations": len(relations),
            "type_distribution": type_dist,
            "relation_distribution": rel_dist,
            "high_confidence_nodes": len(high_conf),
            "top_connected": top_connected,
            "avg_confidence": sum(n.get('confidence', 0) for n in nodes) / max(len(nodes), 1)
        }


if __name__ == "__main__":
    db_path = r"C:\Users\liuchao\Desktop\sol-pi-engram-evolution\sol_pi_engram_evolution\graph.db"
    viz = GraphVisualizer(db_path)

    # 生成 Mermaid
    mermaid = viz.generate_mermaid()
    print("=== Mermaid 图 ===")
    print(mermaid[:500])

    # 生成 HTML
    html_path = r"C:\Users\liuchao\Desktop\sol-pi-engram-evolution\sol_pi_engram_evolution\ui\templates\graph.html"
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    viz.generate_html(html_path)
    print(f"\n✅ HTML 可视化: {html_path}")

    # 分析
    analytics = viz.get_analytics()
    print(f"\n=== 图谱分析 ===")
    print(json.dumps(analytics, indent=2, ensure_ascii=False))
