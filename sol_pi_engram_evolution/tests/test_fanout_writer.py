#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""阶段 2.5 模块 fanout_writer 的测试。

运行：cd tests && python -m pytest test_fanout_writer.py -v
"""

import tempfile
import sys
import os

# 动态加载兄弟模块（项目规范：不用 sys.path 直接 import）
import importlib.util

_HERE = os.path.dirname(os.path.abspath(__file__))
_MOD_DIR = os.path.dirname(_HERE)


def _load(mod_name):
    spec = importlib.util.spec_from_file_location(
        mod_name, os.path.join(_MOD_DIR, mod_name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GraphStore = _load("graph_store").GraphStore
fanout_mod = _load("fanout_writer")
EntityHit = fanout_mod.EntityHit
FanoutGraphWriter = fanout_mod.FanoutGraphWriter


class _DictEnricher:
    """确定性 enricher：从预设映射表扇出（可预测、无网络）。"""

    def __init__(self, name, mapping, fail_on=None):
        self.name = name
        self._mapping = mapping
        self._fail_on = fail_on

    def applicable(self, node):
        return (node.get("title") or "") in self._mapping

    def apply(self, node):
        if self._fail_on and node.get("title") == self._fail_on:
            raise RuntimeError("enricher 故意失败（测试隔离）")
        out = []
        for t, d in self._mapping[node["title"]].items():
            out.append(EntityHit(title=t, description=d,
                                 relation_type="fanout_via_" + self.name,
                                 confidence=0.9))
        return out


def _make_store():
    tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tf.close()
    return GraphStore(tf.name), tf.name


def test_two_round_fanout_grows_graph():
    """两轮扇出：种子 → 第1轮新节点 → 第2轮新节点，图逐轮增长。"""
    store, path = _make_store()
    seed = store.add_task_node(title="A", description="种子")
    enricher = _DictEnricher("dict", {
        "A": {"B": "B from A"},
        "B": {"C": "C from B"},
    })
    w = FanoutGraphWriter(store, [enricher])
    rep = w.fanout_from([seed["node_id"]], max_rounds=3)

    assert rep["total_new_nodes"] == 2            # B、C
    assert rep["total_new_relations"] == 2
    assert rep["rounds"][0]["new_node_ids"] and len(rep["rounds"][0]["new_node_ids"]) == 1
    assert len(rep["rounds"][1]["new_node_ids"]) == 1
    assert rep["rounds"][0]["converged"] is False
    assert rep["rounds"][1]["converged"] is False   # 第2轮产 C，未收敛
    assert len(rep["rounds"]) == 3
    assert rep["rounds"][2]["converged"] is True     # 第3轮 C 无后继 → 收敛
    assert rep["converged"] is True
    stats = store.get_node_stats()
    assert stats["task_count"] == 3                # A+B+C
    store.close()
    os.unlink(path)


def test_dedup_by_title_no_new_node_but_relation_added():
    """同名实体已存在 → 不建新节点（created=False），但仍加关系（图越叠越多）。"""
    store, path = _make_store()
    seed = store.add_task_node(title="A")
    store.add_task_node(title="B")                # B 已存在
    enricher = _DictEnricher("dict", {"A": {"B": "已存在"}})
    w = FanoutGraphWriter(store, [enricher])
    rep = w.fanout_from([seed["node_id"]], max_rounds=2)

    assert rep["total_new_nodes"] == 0            # B 复用
    assert rep["total_new_relations"] == 1        # 关系照挂
    assert rep["converged"] is True               # 无新节点即收敛
    assert store.get_node_stats()["task_count"] == 2
    store.close()
    os.unlink(path)


def test_enricher_failure_isolated_not_fatal():
    """单个 enricher 抛错 → 记录到 enricher_errors，其它 enricher 照常跑（self-heal 铁律）。"""
    store, path = _make_store()
    seed = store.add_task_node(title="A")
    bad = _DictEnricher("bad", {"A": {}}, fail_on="A")   # 对 A 适用，apply 内故意抛错
    good = _DictEnricher("good", {"A": {"B": "good 扇出"}})
    w = FanoutGraphWriter(store, [bad, good])
    rep = w.fanout_from([seed["node_id"]], max_rounds=1)

    assert "bad" in rep["rounds"][0]["enricher_errors"]
    assert "good" in rep["rounds"][0]["enricher_hits"]
    assert rep["total_new_nodes"] == 1
    store.close()
    os.unlink(path)


def test_missing_seed_reported_and_empty_fanout():
    """种子 ID 不存在 → missing_seeds 记录，且不建任何新节点。"""
    store, path = _make_store()
    enricher = _DictEnricher("dict", {"X": {"Y": "y"}})
    w = FanoutGraphWriter(store, [enricher])
    rep = w.fanout_from(["nonexistent-123"], max_rounds=2)

    assert rep["missing_seeds"] == ["nonexistent-123"]
    assert rep["total_new_nodes"] == 0
    assert rep["rounds"] == []
    store.close()
    os.unlink(path)


def test_provenance_evidence_chain_written():
    """每个新节点/关系都带 [fanout] 证据链（轮次+enricher+种子），可审计。"""
    store, path = _make_store()
    seed = store.add_task_node(title="A")
    enricher = _DictEnricher("dict", {"A": {"B": "b"}})
    w = FanoutGraphWriter(store, [enricher])
    w.fanout_from([seed["node_id"]], max_rounds=1)

    audited = w.audit_fanout_nodes()
    assert len(audited) == 1
    assert audited[0]["title"] == "B"
    assert "round=1" in audited[0]["provenance"]
    assert "enricher=dict" in audited[0]["provenance"]
    assert "seed=" in audited[0]["provenance"]

    # 关系描述也带证据链
    rels = store.get_relations_for_node(seed["node_id"])
    assert any("fanout r1 via dict" in (r.get("description") or "") for r in rels)
    store.close()
    os.unlink(path)


def test_max_new_per_round_cap():
    """单轮新节点超过上限时截断（防无限扇出）。"""
    store, path = _make_store()
    seed = store.add_task_node(title="A")
    many = {f"N{i}": f"N{i} d" for i in range(10)}
    enricher = _DictEnricher("dict", {"A": many})
    w = FanoutGraphWriter(store, [enricher], max_new_per_round=3)
    rep = w.fanout_from([seed["node_id"]], max_rounds=1)

    assert rep["total_new_nodes"] == 3            # 10 个只落 3 个
    store.close()
    os.unlink(path)


def test_event_node_fanout():
    """扇出目标为 event 型节点时走 add_event_node 分支。"""
    store, path = _make_store()
    seed = store.add_event_node(title="E", event_type="deploy")
    hit = EntityHit(title="E1", node_type="event")
    enricher = _DictEnricher.__new__(_DictEnricher)
    enricher.name = "dict"
    enricher._mapping = {"E": {"E1": "event"}}
    enricher._fail_on = None

    def _app(node):
        return node.get("title") in enricher._mapping
    def _apply(node):
        return [hit]
    enricher.applicable, enricher.apply = _app, _apply

    w = FanoutGraphWriter(store, [enricher])
    rep = w.fanout_from([seed["node_id"]], max_rounds=1)
    assert rep["total_new_nodes"] == 1
    assert store.get_node_stats()["event_count"] == 2
    store.close()
    os.unlink(path)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
