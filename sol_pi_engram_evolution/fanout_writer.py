#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
阶段 2.5：扇出落图模块（Fanout Graph Writer）

借鉴 Flowsint（reconurge/flowsint）的核心设计——"图当底座，结果落回同图"：
- 图谱是持久事实层，enricher（数据源工具）是可插拔扩展层
- 每一轮扇出的新实体/新关系全部写回同一张图（GraphStore），下一轮就有更多节点可查
- 每次写入保留证据链（哪个 enricher、哪一轮、从哪个种子节点扇出），报告可审计

与 Flowsint 的差异：这里不依赖 Neo4j/Postgres，复用项目既有的 SQLite GraphStore，
保持"零外部依赖 + 端侧可运行"约束。
"""

import json
import time
from dataclasses import dataclass, field
from typing import Callable, Protocol
from datetime import datetime


class Enricher(Protocol):
    """可插拔数据源（enricher）。

    实现类只需提供：
    - name: str —— enricher 标识（进证据链）
    - applicable(node) -> bool —— 判断节点是否可被本 enricher 处理
    - apply(node) -> list[EntityHit] —— 对该节点扇出，返回新实体假设
    """

    name: str

    def applicable(self, node: dict) -> bool:
        ...

    def apply(self, node: dict) -> list:
        ...


@dataclass
class EntityHit:
    """一次扇出产生的新实体假设（尚未落图）。"""
    title: str
    description: str = ""
    node_type: str = "task"          # 与 GraphStore 的 node_type 对齐：task/event
    relation_type: str = "related_to"
    weight: float = 0.5
    confidence: float = 1.0

    def __post_init__(self):
        if not self.title:
            raise ValueError("EntityHit.title 不能为空")


@dataclass
class FanoutRound:
    """一轮扇出的完整记录（可审计）。"""
    round_no: int
    seed_node_ids: list = field(default_factory=list)
    enriched_node_ids: list = field(default_factory=list)
    new_node_ids: list = field(default_factory=list)
    new_relation_ids: list = field(default_factory=list)
    enricher_hits: dict = field(default_factory=dict)   # enricher 名 -> 命中数
    enricher_errors: dict = field(default_factory=dict)  # enricher 名 -> 错误信息
    started_at: float = 0.0
    finished_at: float = 0.0
    converged: bool = False

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["new_relation_ids"] = self.new_relation_ids
        d["duration_s"] = round(self.finished_at - self.started_at, 4)
        return d


class FanoutGraphWriter:
    """扇出落图器：多轮扇出 + 新实体/关系写回 GraphStore + 证据链。

    用法::

        writer = FanoutGraphWriter(store, enrichers=[WikiEnricher(), ...])
        report = writer.fanout_from(["task-xxx", "event-yyy"], max_rounds=3)
        # report["rounds"][i]["new_node_ids"] / ["enricher_hits"] / ["converged"]
    """

    MAX_NEW_PER_ROUND_DEFAULT = 200
    SOURCE_POINTER_TAG = "[fanout]"

    def __init__(self, graph_store, enrichers: list,
                 max_new_per_round: int = MAX_NEW_PER_ROUND_DEFAULT,
                 now_fn: Callable[[], str] | None = None):
        """
        Args:
            graph_store: 已打开的 GraphStore 实例（db_path 注入，见其 __init__）
            enrichers: Enricher 协议实现列表（空列表也可用，退化为纯记录器）
            max_new_per_round: 单轮新节点上限（超过截断，防无限扇出）
            now_fn: 时间注入（测试用），返回 ISO 字符串；默认 datetime.now().isoformat()
        """
        self.store = graph_store
        self.enrichers = list(enrichers or [])
        self.max_new_per_round = max_new_per_round
        self._now_fn = now_fn or (lambda: datetime.now().isoformat())
        self._title_index: dict | None = None

    # ---------------------------------------------------------------- 内部

    def _ensure_title_index(self) -> None:
        """缓存 title -> node_id 的全局索引（任务+事件）。"""
        idx: dict[str, dict] = {}
        for node in self.store.get_all_nodes():
            title = node.get("title") or ""
            if title:
                idx.setdefault(title, node)
        self._title_index = idx

    def _upsert_node(self, hit: EntityHit, provenance: str) -> tuple[dict, bool]:
        """新实体落图；同名节点已存在则复用（只加关系，不建新节点）。

        Returns:
            (node, created) —— node 为图谱中该实体节点，created 标记是否新建。
        """
        if self._title_index is None:
            self._ensure_title_index()

        existing = self._title_index.get(hit.title)
        if existing is not None:
            return existing, False

        adder = self.store.add_task_node if hit.node_type == "task" else self.store.add_event_node
        desc = hit.description or ""
        if provenance:
            desc = f"{desc}\n{provenance}".strip()
        node = adder(
            title=hit.title,
            description=desc,
            confidence=hit.confidence,
            source_pointer=provenance,
        )
        # 更新索引 + 标记证据来源
        if self._title_index is not None:
            self._title_index[hit.title] = node
        return node, True

    @staticmethod
    def _relation_desc(seed_title: str, hit: EntityHit, enricher_name: str, round_no: int) -> str:
        """关系描述同时充当证据链：从哪扇出、哪个 enricher、第几轮。"""
        return f"fanout r{round_no} via {enricher_name} from '{seed_title}'"

    # ---------------------------------------------------------------- 对外

    def fanout_from(self, seed_node_ids: list, max_rounds: int = 3) -> dict:
        """从种子节点出发做多轮扇出，每轮结果写回同一张图。

        收敛规则：某轮没有新节点（enricher 全空或全命中已存在节点）即提前停止。
        enricher 失败隔离：单个 enricher 抛错记录到 enricher_errors，不中断其它 enricher。

        Args:
            seed_node_ids: 起点节点 ID 列表（第 0 轮种子；后续轮以新节点为种子）
            max_rounds: 最大轮数（不含种子解析轮）

        Returns:
            完整扇出报告 dict：
            {
                "seed_node_ids": [...],
                "rounds": [FanoutRound.to_dict(), ...],
                "total_new_nodes": N,
                "total_new_relations": M,
                "converged": bool,        # 是否因无新节点而收敛（非跑满轮数）
                "graph_stats": store.get_node_stats(),
            }
        """
        seeds = []
        missing = []
        for sid in seed_node_ids:
            node = self.store.get_node_by_id(sid)
            if node is None:
                missing.append(sid)
            else:
                seeds.append(node)
        if not seeds:
            return {"seed_node_ids": list(seed_node_ids), "rounds": [],
                    "total_new_nodes": 0, "total_new_relations": 0,
                    "converged": False, "missing_seeds": missing,
                    "graph_stats": self.store.get_node_stats()}

        self._ensure_title_index()
        rounds: list[FanoutRound] = []
        frontier = seeds
        converged = False

        for r in range(1, max_rounds + 1):
            round_no = r
            rd = FanoutRound(round_no=round_no, seed_node_ids=[n["node_id"] for n in frontier])
            rd.started_at = time.time()

            # ---- 本轮扇出：对前沿节点逐个跑全部 enricher ----
            frontier_titles = {n.get("title") for n in frontier}
            new_nodes_this_round: list[dict] = []
            new_relations_this_round: list[dict] = []
            for node in frontier:
                rd.enriched_node_ids.append(node["node_id"])
                for enr in self.enrichers:
                    try:
                        if not enr.applicable(node):
                            continue
                        hits = enr.apply(node) or []
                    except Exception as exc:  # 失败隔离（self-heal 铁律：记录不中断）
                        rd.enricher_errors[enr.name] = f"{type(exc).__name__}: {exc}"
                        continue
                    rd.enricher_hits[enr.name] = rd.enricher_hits.get(enr.name, 0) + len(hits)
                    for hit in hits[: self.max_new_per_round]:
                        provenance = (f"{self.SOURCE_POINTER_TAG} round={round_no} "
                                      f"enricher={enr.name} seed={node['node_id']}")
                        entity, created = self._upsert_node(hit, provenance)
                        if created:
                            new_nodes_this_round.append(entity)
                        # 新实体/已存在实体都要挂关系（图越叠越多）
                        rel = self.store.add_relation(
                            source_node_id=node["node_id"],
                            target_node_id=entity["node_id"],
                            relation_type=hit.relation_type,
                            weight=hit.weight,
                            description=self._relation_desc(
                                node.get("title", ""), hit, enr.name, round_no),
                            confidence=hit.confidence,
                            source_pointer=provenance,
                        )
                        new_relations_this_round.append(rel)

            # ---- 收口 ----
            rd.new_node_ids = [n["node_id"] for n in new_nodes_this_round]
            rd.new_relation_ids = [x["relation_id"] for x in new_relations_this_round]
            rd.finished_at = time.time()

            if not new_nodes_this_round:
                rd.converged = True
                converged = True
                rounds.append(rd)
                break

            frontier = new_nodes_this_round
            rounds.append(rd)

        return {
            "seed_node_ids": list(seed_node_ids),
            "missing_seeds": missing,
            "rounds": [rd.to_dict() for rd in rounds],
            "total_new_nodes": sum(len(rd.new_node_ids) for rd in rounds),
            "total_new_relations": sum(len(rd.new_relation_ids) for rd in rounds),
            "converged": converged,
            "graph_stats": self.store.get_node_stats(),
        }

    def audit_fanout_nodes(self) -> list:
        """列出所有带扇出证据链的节点（证据链审计）。"""
        out = []
        for node in self.store.get_all_nodes():
            sp = node.get("source_pointer") or ""
            if self.SOURCE_POINTER_TAG in sp:
                out.append({
                    "node_id": node["node_id"],
                    "title": node.get("title"),
                    "node_type": node.get("node_type"),
                    "provenance": sp,
                })
        return out
