#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSI 自主演化引擎 — V2 记忆管理增强版

新增：基于 WeKnora 长短期记忆分类的记忆管理系统
- 短期记忆：高频访问、实时更新、自动淘汰
- 长期记忆：跨会话持久化、知识图谱化、可追溯
- 记忆分类器：基于时间衰减和访问模式的自动分类
- 记忆压缩：使用 TokenJuice 风格的分层压缩
"""

import hashlib
import json
import os
import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent


# ========== ① WeKnora 长短期记忆分类器 ==========

@dataclass
class MemoryEntry:
    """单条记忆条目"""
    content: str
    category: str          # short_term / long_term
    created_at: float
    access_count: int = 0
    last_accessed: float = 0.0
    importance: float = 0.5
    source: str = ""
    metadata: dict = field(default_factory=dict)

    def decay_score(self, now: float = None) -> float:
        """计算时间衰减后的重要性分数"""
        now = now or time.time()
        age_hours = (now - self.created_at) / 3600.0
        recency = 1.0 / (1.0 + age_hours / 24.0)  # 24小时半衰期
        frequency = min(self.access_count / 10.0, 1.0)  # 10次访问封顶
        return self.importance * recency * (0.5 + 0.5 * frequency)


class WeKnoraMemoryClassifier:
    """WeKnora 长短期记忆分类器

    基于时间衰减和访问模式自动将记忆分为：
    - Short-Term Memory (STM)：高频访问、实时上下文、临时缓存
    - Long-Term Memory (LTM)：跨会话持久化、知识图谱化、可追溯

    分类规则：
    1. 短期记忆：最近24小时内创建 或 访问频率 > 0.7
    2. 长期记忆：创建时间 > 72小时 且 被确认过（显式反馈或持久化）
    3. 过渡记忆：介于两者之间，根据后续行为升级或降级
    """

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.stm_max_hours = self.config.get('stm_max_hours', 24.0)
        self.ltm_min_hours = self.config.get('ltm_min_hours', 72.0)
        self.high_access_threshold = self.config.get('high_access_threshold', 5)

        # 记忆存储
        self._memories: dict[str, MemoryEntry] = {}
        self._stm_keys: set[str] = set()   # 短期记忆 key 集合
        self._ltm_keys: set[str] = set()   # 长期记忆 key 集合

        # 存储路径
        self.storage_path = Path(self.config.get(
            'memory_storage', str(BASE_DIR / 'weknora_memories.json')
        ))
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def classify(self, key: str, entry: MemoryEntry) -> str:
        """对记忆进行分类"""
        now = time.time()
        age_hours = (now - entry.created_at) / 3600.0
        is_high_access = entry.access_count >= self.high_access_threshold

        if age_hours <= self.stm_max_hours or is_high_access:
            category = "short_term"
            self._stm_keys.add(key)
            self._ltm_keys.discard(key)
        elif age_hours >= self.ltm_min_hours and entry.access_count > 0:
            category = "long_term"
            self._ltm_keys.add(key)
            self._stm_keys.discard(key)
        else:
            category = "transition"
            self._stm_keys.add(key)
            self._ltm_keys.discard(key)

        entry.category = category
        return category

    def add_memory(self, content: str, importance: float = 0.5,
                   source: str = "", metadata: dict = None) -> MemoryEntry:
        """添加记忆"""
        key = hashlib.md5(content.encode()).hexdigest()[:16]
        now = time.time()

        entry = MemoryEntry(
            content=content,
            category="short_term",
            created_at=now,
            last_accessed=now,
            importance=importance,
            source=source,
            metadata=metadata or {},
        )

        self._memories[key] = entry
        self.classify(key, entry)
        return entry

    def access_memory(self, key: str) -> MemoryEntry | None:
        """访问记忆（更新访问计数和时间）"""
        if key not in self._memories:
            return None

        entry = self._memories[key]
        entry.access_count += 1
        entry.last_accessed = time.time()

        # 重新分类（高频访问可能升级为长期记忆）
        self.classify(key, entry)
        return entry

    def get_stm_memories(self, limit: int = 20) -> list[dict]:
        """获取短期记忆（按衰减分数排序）"""
        now = time.time()
        stm_entries = [
            (k, v) for k, v in self._memories.items() if k in self._stm_keys
        ]
        stm_entries.sort(key=lambda x: x[1].decay_score(now), reverse=True)
        return [
            {"key": k, "content": v.content, "category": v.category,
             "importance": v.importance, "access_count": v.access_count,
             "score": v.decay_score(now)}
            for k, v in stm_entries[:limit]
        ]

    def get_ltm_memories(self, limit: int = 20) -> list[dict]:
        """获取长期记忆（按重要性排序）"""
        ltm_entries = [
            (k, v) for k, v in self._memories.items() if k in self._ltm_keys
        ]
        ltm_entries.sort(key=lambda x: x[1].importance, reverse=True)
        return [
            {"key": k, "content": v.content, "category": v.category,
             "importance": v.importance, "access_count": v.access_count}
            for k, v in ltm_entries[:limit]
        ]

    def promote_to_ltm(self, key: str):
        """将记忆显式升级为长期记忆"""
        if key in self._memories:
            self._memories[key].importance = min(1.0, self._memories[key].importance + 0.3)
            self._ltm_keys.add(key)
            self._stm_keys.discard(key)
            self._memories[key].category = "long_term"

    def get_relevant_memories(self, query: str, limit: int = 10) -> list[dict]:
        """获取与查询相关的记忆（简单关键词匹配）"""
        keywords = query.lower().split()
        scored = []
        for key, entry in self._memories.items():
            score = 0.0
            content_lower = entry.content.lower()
            for kw in keywords:
                if kw in content_lower:
                    score += 1.0
            if score > 0:
                score *= entry.importance * (1.0 + entry.access_count / 10.0)
                scored.append((key, entry, score))

        scored.sort(key=lambda x: x[2], reverse=True)
        return [
            {"key": k, "content": e.content, "category": e.category,
             "relevance": s, "importance": e.importance}
            for k, e, s in scored[:limit]
        ]

    def evict_stm(self, max_age_hours: float = 48.0, min_score: float = 0.1):
        """淘汰低价值短期记忆"""
        now = time.time()
        to_remove = []
        for key in self._stm_keys:
            entry = self._memories.get(key)
            if entry is None:
                to_remove.append(key)
                continue
            age = (now - entry.created_at) / 3600.0
            if age > max_age_hours and entry.decay_score(now) < min_score:
                to_remove.append(key)

        for key in to_remove:
            del self._memories[key]
            self._stm_keys.discard(key)

        return len(to_remove)

    def stats(self) -> dict:
        return {
            "total_memories": len(self._memories),
            "short_term_count": len(self._stm_keys),
            "long_term_count": len(self._ltm_keys),
            "storage_path": str(self.storage_path),
        }

    def _save(self):
        """持久化记忆"""
        data = {
            "memories": {
                k: {
                    "content": v.content,
                    "category": v.category,
                    "created_at": v.created_at,
                    "access_count": v.access_count,
                    "last_accessed": v.last_accessed,
                    "importance": v.importance,
                    "source": v.source,
                    "metadata": v.metadata,
                }
                for k, v in self._memories.items()
            },
            "stm_keys": list(self._stm_keys),
            "ltm_keys": list(self._ltm_keys),
            "saved_at": datetime.now().isoformat(),
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load(self):
        """加载记忆"""
        if not self.storage_path.exists():
            return
        try:
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.get("memories", {}).items():
                entry = MemoryEntry(
                    content=v["content"],
                    category=v["category"],
                    created_at=v["created_at"],
                    access_count=v["access_count"],
                    last_accessed=v.get("last_accessed", v["created_at"]),
                    importance=v["importance"],
                    source=v.get("source", ""),
                    metadata=v.get("metadata", {}),
                )
                self._memories[k] = entry
            self._stm_keys = set(data.get("stm_keys", []))
            self._ltm_keys = set(data.get("ltm_keys", []))
        except Exception:
            pass


# ========== ① 模块热替换框架 ==========

class HotSwapRegistry:
    """模块热替换注册表"""

    def __init__(self):
        self._modules: dict[str, Any] = {}
        self._metadata: dict[str, dict] = {}
        self._listeners: list[Callable] = []

    def register(self, name: str, module: Any, version: str = "1.0.0"):
        self._modules[name] = module
        self._metadata[name] = {
            "version": version,
            "registered_at": datetime.now().isoformat(),
            "status": "active"
        }
        self._notify(f"registered:{name}")

    def replace(self, name: str, new_module: Any, new_version: str = None) -> bool:
        if name not in self._modules:
            return False
        old_meta = self._metadata[name]
        old_version = old_meta["version"]
        if new_version is None:
            parts = old_version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            new_version = ".".join(parts)
        self._modules[name] = new_module
        self._metadata[name] = {
            "version": new_version,
            "replaced_at": datetime.now().isoformat(),
            "previous_version": old_version,
            "status": "active"
        }
        self._notify(f"replaced:{name}")
        return True

    def get(self, name: str) -> Any:
        return self._modules.get(name)

    def list_modules(self) -> list[dict]:
        return [{"name": name, **meta} for name, meta in self._metadata.items()]

    def on_change(self, callback: Callable):
        self._listeners.append(callback)

    def _notify(self, event: str):
        for cb in self._listeners:
            try:
                cb(event, self._metadata)
            except Exception:
                pass


# ========== ② Prompt 自动 A/B 测试 ==========

@dataclass
class PromptVariant:
    id: str
    template: str
    description: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    total_uses: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0

    @property
    def score(self) -> float:
        if self.total_uses == 0:
            return 0.5
        n = self.total_uses
        if n == 0:
            return 0.0
        z = 1.96
        phat = self.positive_feedback / n
        denominator = 1 + z * z / n
        centre = phat + z * z / (2 * n)
        spread = z * ((phat * (1 - phat) + z * z / (4 * n)) / n) ** 0.5
        return (centre - spread) / denominator


class ABTestManager:
    """Prompt A/B 测试管理器"""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or str(BASE_DIR / "ab_test_variants.json")
        self.variants: dict[str, list[PromptVariant]] = {}
        self.active: dict[str, str] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
                for task_id, variants in data.get("variants", {}).items():
                    self.variants[task_id] = [PromptVariant(**v) for v in variants]
                self.active = data.get("active", {})

    def _save(self):
        data = {
            "variants": {
                task: [vars(v) for v in vs]
                for task, vs in self.variants.items()
            },
            "active": self.active
        }
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def register_variant(self, task_id: str, template: str, description: str = ""):
        if task_id not in self.variants:
            self.variants[task_id] = []
        variant_id = hashlib.md5(template.encode()).hexdigest()[:8]
        variant = PromptVariant(id=variant_id, template=template, description=description)
        self.variants[task_id].append(variant)
        self._save()
        return variant

    def get_prompt(self, task_id: str) -> str | None:
        if task_id not in self.variants:
            return None
        variants = self.variants[task_id]
        if not variants:
            return None
        total_uses = sum(v.total_uses for v in variants)
        best_variant = None
        best_score = -1
        for v in variants:
            exploitation = v.score
            exploration = (2 * (total_uses ** 0.5) / max(v.total_uses, 1)) ** 0.5
            ucb_score = exploitation + exploration
            if ucb_score > best_score:
                best_score = ucb_score
                best_variant = v
        if best_variant:
            self.active[task_id] = best_variant.id
            return best_variant.template
        return None

    def record_feedback(self, task_id: str, variant_id: str, positive: bool):
        if task_id not in self.variants:
            return
        for v in self.variants[task_id]:
            if v.id == variant_id:
                v.total_uses += 1
                if positive:
                    v.positive_feedback += 1
                else:
                    v.negative_feedback += 1
                break
        self._save()
        self._maybe_promote(task_id)

    def _maybe_promote(self, task_id: str):
        variants = self.variants.get(task_id, [])
        if len(variants) < 2:
            return
        best = max(variants, key=lambda v: v.score)
        second = sorted(variants, key=lambda v: v.score, reverse=True)[1]
        if (best.score > second.score + 0.1 and
            best.total_uses > 50 and
            best.total_uses > second.total_uses * 2):
            self.active[task_id] = best.id
            print(f"[A/B] Promoted variant {best.id} for '{task_id}' (score={best.score:.3f})")

    def get_leaderboard(self, task_id: str) -> list[dict]:
        variants = self.variants.get(task_id, [])
        return sorted([
            {
                "id": v.id,
                "template": v.template[:80] + "...",
                "description": v.description,
                "uses": v.total_uses,
                "positive": v.positive_feedback,
                "score": round(v.score, 4),
                "active": self.get(task_id) == v.id
            }
            for v in variants
        ], key=lambda x: x["score"], reverse=True)

    def get(self, task_id: str) -> str | None:
        return self.get_prompt(task_id)


# ========== ③ 话术库自动扩展（模板库进化） ==========

class TemplateEvolver:
    """话术模板进化器"""

    def __init__(self, template_dir: str = None):
        self.template_dir = Path(template_dir or BASE_DIR / "evolution_templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.templates: dict[str, list[str]] = {}
        self._load_templates()

    def _load_templates(self):
        for f in self.template_dir.glob("*.json"):
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
                self.templates[f.stem] = data.get("templates", [])

    def _save_templates(self, category: str):
        path = self.template_dir / f"{category}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "category": category,
                "templates": self.templates.get(category, []),
                "updated_at": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)

    def add_template(self, category: str, template: str, source: str = "manual"):
        if category not in self.templates:
            self.templates[category] = []
        if template in self.templates[category]:
            return
        self.templates[category].append(template)
        self._save_templates(category)

    def evolve_template(self, category: str, base_template: str, feedback: str = "") -> str:
        variants = [
            base_template,
            base_template.replace("建议", "推荐"),
            base_template.replace("需要", "应该"),
            base_template + "（AI 分析，仅供参考）",
            "【重要】" + base_template,
        ]
        feedback_lower = feedback.lower()
        if "太长" in feedback_lower or "啰嗦" in feedback_lower:
            short = base_template[:30] + "..."
            variants.append(short)
        if "不够详细" in feedback_lower or "太简单" in feedback_lower:
            detailed = base_template + "\n\n详细说明：本建议基于您的历史数据和行业基准综合评估。"
            variants.append(detailed)
        chosen = random.choice(variants)
        if chosen == base_template and len(variants) > 1:
            other = [v for v in variants if v != base_template]
            chosen = random.choice(other)
        self.add_template(category, chosen, source="evolved")
        return chosen

    def get_templates(self, category: str) -> list[str]:
        return self.templates.get(category, [])

    def get_random_template(self, category: str) -> str | None:
        templates = self.templates.get(category, [])
        if not templates:
            return None
        return random.choice(templates)


# ========== 自主演化引擎（整合以上所有 + WeKnora 记忆管理） ==========

class SelfEvolutionEngine:
    """RSI 自主演化引擎 — V2 WeKnora 记忆增强版"""

    def __init__(self):
        self.registry = HotSwapRegistry()
        self.ab_manager = ABTestManager()
        self.template_evolver = TemplateEvolver()
        self.evolution_log: list[dict] = []
        self._running = False
        self._thread = None

        # V2: WeKnora 长短期记忆管理
        self.memory = WeKnoraMemoryClassifier()

    def register_module(self, name: str, module: Any, version: str = "1.0.0"):
        self.registry.register(name, module, version)
        self._log_event("module_registered", {"name": name, "version": version})

    def replace_module(self, name: str, new_module: Any, new_version: str = None):
        success = self.registry.replace(name, new_module, new_version)
        if success:
            self._log_event("module_replaced", {"name": name, "new_version": new_version})
        return success

    def ab_test_prompt(self, task_id: str, template: str, description: str = ""):
        return self.ab_manager.register_variant(task_id, template, description)

    def get_best_prompt(self, task_id: str) -> str | None:
        return self.ab_manager.get(task_id)

    def record_prompt_feedback(self, task_id: str, variant_id: str, positive: bool):
        self.ab_manager.record_feedback(task_id, variant_id, positive)

    def evolve_templates(self, category: str, base: str, feedback: str = "") -> str:
        evolved = self.template_evolver.evolve_template(category, base, feedback)
        self._log_event("template_evolved", {
            "category": category, "base": base[:50], "evolved": evolved[:50]
        })
        return evolved

    # ========== V2: WeKnora 记忆管理接口 ==========

    def add_memory(self, content: str, importance: float = 0.5,
                   source: str = "", metadata: dict = None) -> MemoryEntry:
        """添加记忆到系统"""
        entry = self.memory.add_memory(content, importance, source, metadata)
        self._log_event("memory_added", {
            "category": entry.category,
            "importance": importance,
            "source": source,
        })
        return entry

    def access_memory(self, key: str) -> MemoryEntry | None:
        """访问记忆"""
        entry = self.memory.access_memory(key)
        if entry:
            self._log_event("memory_accessed", {
                "key": key, "category": entry.category,
                "access_count": entry.access_count,
            })
        return entry

    def get_short_term_memories(self, limit: int = 20) -> list[dict]:
        """获取短期记忆"""
        return self.memory.get_stm_memories(limit)

    def get_long_term_memories(self, limit: int = 20) -> list[dict]:
        """获取长期记忆"""
        return self.memory.get_ltm_memories(limit)

    def get_relevant_memories(self, query: str, limit: int = 10) -> list[dict]:
        """获取与查询相关的记忆"""
        return self.memory.get_relevant_memories(query, limit)

    def promote_memory(self, key: str):
        """将记忆升级为长期记忆"""
        self.memory.promote_to_ltm(key)
        self._log_event("memory_promoted", {"key": key})

    def evict_memories(self, max_age_hours: float = 48.0, min_score: float = 0.1) -> int:
        """淘汰低价值短期记忆"""
        count = self.memory.evict_stm(max_age_hours, min_score)
        self._log_event("memory_eviction", {"evicted_count": count})
        return count

    def get_memory_stats(self) -> dict:
        """获取记忆系统统计"""
        return self.memory.stats()

    def _log_event(self, event_type: str, details: dict):
        self.evolution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "details": details,
        })

    def get_status(self) -> dict:
        return {
            "modules": self.registry.list_modules(),
            "ab_tests": {
                task_id: self.ab_manager.get_leaderboard(task_id)
                for task_id in self.ab_manager.variants.keys()
            },
            "template_categories": {
                cat: len(tpl)
                for cat, tpl in self.template_evolver.templates.items()
            },
            "evolution_log_count": len(self.evolution_log),
            "recent_events": self.evolution_log[-5:],
            "memory": self.get_memory_stats(),
        }


# ========== 工厂函数 ==========

_engine: SelfEvolutionEngine | None = None


def get_evolution_engine() -> SelfEvolutionEngine:
    """获取全局唯一的进化引擎"""
    global _engine
    if _engine is None:
        _engine = SelfEvolutionEngine()
    return _engine


# ========== 测试 / Demo ==========

if __name__ == "__main__":
    engine = get_evolution_engine()

    print("=" * 60)
    print("RSI 自主演化引擎 V2 — WeKnora 记忆管理演示")
    print("=" * 60)

    # 1. 注册模块热替换
    print("\n[1] 模块热替换注册...")

    class MockAnalyzer:
        def analyze(self, data):
            return {"result": "analyzed", "version": "1.0.0"}

    class MockAnalyzerV2:
        def analyze(self, data):
            return {"result": "analyzed_improved", "version": "2.0.0"}

    engine.register_module("analyzer", MockAnalyzer(), "1.0.0")
    engine.register_module("reporter", object(), "1.0.0")
    modules = engine.registry.list_modules()
    print(f"  注册了 {len(modules)} 个模块")
    for m in modules:
        print(f"    - {m['name']} v{m['version']} ({m['status']})")

    engine.replace_module("analyzer", MockAnalyzerV2())
    modules = engine.registry.list_modules()
    print(f"  热替换后：analyzer v{modules[0]['version']}")

    # 2. Prompt A/B 测试
    print("\n[2] Prompt A/B 测试...")
    engine.ab_test_prompt("daily_report", "老板早上好，今天有 {count} 件事需要关注：{items}", "标准问候版")
    engine.ab_test_prompt("daily_report", "老王早，今日{count}项待办：{items}", "简洁直接版")
    engine.ab_test_prompt("daily_report", "【经营日报】{date}必读：您有{count}项关键事项待处理。详情：{items}", "正式版")
    for i in range(100):
        prompt = engine.get_best_prompt("daily_report")
        variant_id = hashlib.md5(prompt.encode()).hexdigest()[:8]
        positive = "简洁" in prompt or "早" in prompt
        engine.record_prompt_feedback("daily_report", variant_id, positive)
    leaderboard = engine.ab_manager.get_leaderboard("daily_report")
    print("  Prompt 排行榜（Top 3）：")
    for entry in leaderboard[:3]:
        print(f"    [{entry['id']}] score={entry['score']:.4f} uses={entry['uses']} | {entry['description']}")

    # 3. 模板进化
    print("\n[3] 模板进化...")
    base = "建议关注{topic}，因为{reason}"
    engine.template_evolver.add_template("risk_alert", base)
    evolved = engine.evolve_templates("risk_alert", base, feedback="不够详细")
    print(f"  基础模板：{base}")
    print(f"  进化结果：{evolved}")

    # 4. WeKnora 记忆管理演示
    print("\n[4] WeKnora 长短期记忆分类...")
    m1 = engine.add_memory("今天是启动谈判的第一天，对方报价偏高", importance=0.9, source="session")
    m2 = engine.add_memory("对方核心诉求是交付周期而非价格", importance=0.8, source="session")
    m3 = engine.add_memory("我方底线是利润不低于15%", importance=0.95, source="session")
    print(f"  添加记忆 m1: category={m1.category}, importance={m1.importance}")
    print(f"  添加记忆 m2: category={m2.category}, importance={m2.importance}")
    print(f"  添加记忆 m3: category={m3.category}, importance={m3.importance}")

    # 模拟高频访问
    for _ in range(10):
        engine.access_memory(m2.content)
    print(f"  访问 m2 10次后: category={engine.memory._memories[hashlib.md5(m2.content.encode()).hexdigest()[:16]].category}")

    # 升级记忆
    key_to_promote = hashlib.md5(m3.content.encode()).hexdigest()[:16]
    engine.promote_memory(key_to_promote)
    print(f"  升级 m3 为长期记忆: success")

    # 获取记忆
    stm = engine.get_short_term_memories()
    ltm = engine.get_long_term_memories()
    print(f"  短期记忆数量: {len(stm)}")
    print(f"  长期记忆数量: {len(ltm)}")

    # 查询相关记忆
    relevant = engine.get_relevant_memories("谈判 报价 交付")
    print(f"  相关记忆数量: {len(relevant)}")
    for r in relevant[:3]:
        print(f"    - [{r['category']}] {r['content'][:30]}... (rel={r['relevance']:.2f})")

    # 5. 状态总览
    print("\n[5] 引擎状态：")
    status = engine.get_status()
    print(f"  注册模块数：{len(status['modules'])}")
    print(f"  A/B 测试任务数：{len(status['ab_tests'])}")
    print(f"  模板类别数：{len(status['template_categories'])}")
    print(f"  进化事件数：{status['evolution_log_count']}")
    print(f"  记忆系统：{status['memory']}")

    # 保存记忆
    engine.memory._save()
    print(f"\n  记忆已持久化到: {engine.memory.storage_path}")

    print("\n" + "=" * 60)
    print("✅ RSI V2 自主演化引擎演示完成")
    print("模块热替换 + Prompt A/B 测试 + 模板进化 + WeKnora 记忆管理 全部就绪")
    print("=" * 60)
