#!/usr/bin/env python3
"""
RSI 自主演进引擎 — 具体行动落地
① 模块热替换框架
② Prompt 自动 A/B 测试
③ 话术库自动扩展（模板库进化）
"""
import hashlib
import json
import os
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).parent


# ========== ① 模块热替换框架 ==========

class HotSwapRegistry:
    """模块热替换注册表 — 运行时加载/卸载/替换模块"""

    def __init__(self):
        self._modules: dict[str, Any] = {}
        self._metadata: dict[str, dict] = {}
        self._listeners: list[Callable] = []

    def register(self, name: str, module: Any, version: str = "1.0.0"):
        """注册模块"""
        self._modules[name] = module
        self._metadata[name] = {
            "version": version,
            "registered_at": datetime.now().isoformat(),
            "status": "active"
        }
        self._notify(f"registered:{name}")

    def replace(self, name: str, new_module: Any, new_version: str = None) -> bool:
        """热替换模块"""
        if name not in self._modules:
            return False

        old_meta = self._metadata[name]
        old_version = old_meta["version"]

        if new_version is None:
            # 自动递增版本号
            parts = old_version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            new_version = ".".join(parts)

        # 执行替换
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
        """获取模块"""
        return self._modules.get(name)

    def list_modules(self) -> list[dict]:
        """列出所有模块"""
        result = []
        for name, meta in self._metadata.items():
            result.append({
                "name": name,
                **meta
            })
        return result

    def on_change(self, callback: Callable):
        """注册变更监听"""
        self._listeners.append(callback)

    def _notify(self, event: str):
        """通知所有监听者"""
        for cb in self._listeners:
            try:
                cb(event, self._metadata)
            except Exception:
                pass


# ========== ② Prompt 自动 A/B 测试 ==========

@dataclass
class PromptVariant:
    """Prompt 变体"""
    id: str
    template: str
    description: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # 评估指标
    total_uses: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0

    @property
    def score(self) -> float:
        """Elo-style score with Bayesian smoothing"""
        if self.total_uses == 0:
            return 0.5
        # Wilson score lower bound (95% confidence)
        n = self.total_uses
        if n == 0:
            return 0.0
        z = 1.96  # 95% confidence
        phat = self.positive_feedback / n
        denominator = 1 + z * z / n
        centre = phat + z * z / (2 * n)
        spread = z * ((phat * (1 - phat) + z * z / (4 * n)) / n) ** 0.5
        return (centre - spread) / denominator


class ABTestManager:
    """Prompt A/B 测试管理器 — 自动选择最优 Prompt"""

    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or str(BASE_DIR / "ab_test_variants.json")
        self.variants: dict[str, list[PromptVariant]] = {}  # task -> variants
        self.active: dict[str, str] = {}  # task -> active variant id
        self._load()

    def _load(self):
        """加载已有变体"""
        if os.path.exists(self.storage_path):
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
                for task_id, variants in data.get("variants", {}).items():
                    self.variants[task_id] = [
                        PromptVariant(**v) for v in variants
                    ]
                self.active = data.get("active", {})

    def _save(self):
        """持久化"""
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
        """注册新的 Prompt 变体"""
        if task_id not in self.variants:
            self.variants[task_id] = []

        variant_id = hashlib.md5(template.encode()).hexdigest()[:8]
        variant = PromptVariant(
            id=variant_id,
            template=template,
            description=description
        )
        self.variants[task_id].append(variant)
        self._save()
        return variant

    def get_prompt(self, task_id: str) -> str | None:
        """获取当前活跃的 Prompt（UCB1 探索-利用平衡）"""
        if task_id not in self.variants:
            return None

        variants = self.variants[task_id]
        if not variants:
            return None

        total_uses = sum(v.total_uses for v in variants)

        # UCB1 选择
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
        """记录用户反馈（隐式/显式）"""
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
        """如果某变体明显优于其他，自动提升为默认"""
        variants = self.variants.get(task_id, [])
        if len(variants) < 2:
            return

        # 找到最佳变体
        best = max(variants, key=lambda v: v.score)
        second = sorted(variants, key=lambda v: v.score, reverse=True)[1]

        # 如果最佳变体显著优于次优（>10%），且使用次数>50，提升为默认
        if (best.score > second.score + 0.1 and
            best.total_uses > 50 and
            best.total_uses > second.total_uses * 2):
            self.active[task_id] = best.id
            print(f"[A/B] Promoted variant {best.id} for task '{task_id}' (score={best.score:.3f})")

    def get_leaderboard(self, task_id: str) -> list[dict]:
        """获取排行榜"""
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
        """获取当前活跃 Prompt"""
        return self.get_prompt(task_id)


# ========== ③ 话术库自动扩展（模板库进化） ==========

class TemplateEvolver:
    """话术模板进化器 — 自动生成和优化话术模板"""

    def __init__(self, template_dir: str = None):
        self.template_dir = Path(template_dir or BASE_DIR / "evolution_templates")
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.templates: dict[str, list[str]] = {}
        self._load_templates()

    def _load_templates(self):
        """加载已有模板"""
        for f in self.template_dir.glob("*.json"):
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)
                self.templates[f.stem] = data.get("templates", [])

    def _save_templates(self, category: str):
        """持久化模板"""
        path = self.template_dir / f"{category}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "category": category,
                "templates": self.templates.get(category, []),
                "updated_at": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)

    def add_template(self, category: str, template: str, source: str = "manual"):
        """添加模板"""
        if category not in self.templates:
            self.templates[category] = []

        # 检查重复
        if template in self.templates[category]:
            return

        self.templates[category].append(template)
        self._save_templates(category)

    def evolve_template(self, category: str, base_template: str, feedback: str = "") -> str:
        """基于反馈进化模板（简单变体生成）"""
        variants = [
            base_template,
            base_template.replace("建议", "推荐"),
            base_template.replace("需要", "应该"),
            base_template + "（AI 分析，仅供参考）",
            "【重要】" + base_template,
        ]

        # 如果有反馈，生成更有针对性的变体
        feedback_lower = feedback.lower()
        if "太长" in feedback_lower or "啰嗦" in feedback_lower:
            # 生成精简版
            short = base_template[:30] + "..."
            variants.append(short)

        if "不够详细" in feedback_lower or "太简单" in feedback_lower:
            # 生成详细版
            detailed = base_template + "\n\n详细说明：本建议基于您的历史数据和行业基准综合评估。"
            variants.append(detailed)

        # 随机选择一个变体，确保不与基础模板相同
        chosen = random.choice(variants)
        if chosen == base_template and len(variants) > 1:
            other_variants = [v for v in variants if v != base_template]
            chosen = random.choice(other_variants)

        self.add_template(category, chosen, source="evolved")
        return chosen

    def get_templates(self, category: str) -> list[str]:
        """获取某类别的所有模板"""
        return self.templates.get(category, [])

    def get_random_template(self, category: str) -> str | None:
        """随机获取模板（用于 A/B 测试）"""
        templates = self.templates.get(category, [])
        if not templates:
            return None
        return random.choice(templates)


# ========== 自主演化引擎（整合以上三个） ==========

class SelfEvolutionEngine:
    """RSI 自主演化引擎 — 整合热替换 + A/B 测试 + 模板进化"""

    def __init__(self):
        self.registry = HotSwapRegistry()
        self.ab_manager = ABTestManager()
        self.template_evolver = TemplateEvolver()
        self.evolution_log: list[dict] = []
        self._running = False
        self._thread = None

    def register_module(self, name: str, module: Any, version: str = "1.0.0"):
        """注册模块"""
        self.registry.register(name, module, version)
        self._log_event("module_registered", {"name": name, "version": version})

    def replace_module(self, name: str, new_module: Any, new_version: str = None):
        """热替换模块"""
        success = self.registry.replace(name, new_module, new_version)
        if success:
            self._log_event("module_replaced", {"name": name, "new_version": new_version})
        return success

    def ab_test_prompt(self, task_id: str, template: str, description: str = ""):
        """注册 Prompt 变体用于 A/B 测试"""
        return self.ab_manager.register_variant(task_id, template, description)

    def get_best_prompt(self, task_id: str) -> str | None:
        """获取当前最佳 Prompt"""
        return self.ab_manager.get(task_id)

    def record_prompt_feedback(self, task_id: str, variant_id: str, positive: bool):
        """记录 Prompt 反馈"""
        self.ab_manager.record_feedback(task_id, variant_id, positive)

    def evolve_templates(self, category: str, base: str, feedback: str = "") -> str:
        """进化模板"""
        evolved = self.template_evolver.evolve_template(category, base, feedback)
        self._log_event("template_evolved", {
            "category": category,
            "base": base[:50],
            "evolved": evolved[:50]
        })
        return evolved

    def _log_event(self, event_type: str, details: dict):
        """记录进化事件"""
        self.evolution_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "details": details
        })

    def get_status(self) -> dict:
        """获取引擎状态"""
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
            "recent_events": self.evolution_log[-5:]
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
    print("RSI 自主演化引擎演示")
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

    # 热替换
    engine.replace_module("analyzer", MockAnalyzerV2())
    modules = engine.registry.list_modules()
    print(f"  热替换后：analyzer v{modules[0]['version']}")

    # 2. Prompt A/B 测试
    print("\n[2] Prompt A/B 测试...")

    engine.ab_test_prompt(
        "daily_report",
        "老板早上好，今天有 {count} 件事需要关注：{items}",
        "标准问候版"
    )
    engine.ab_test_prompt(
        "daily_report",
        "老王早，今日{count}项待办：{items}",
        "简洁直接版"
    )
    engine.ab_test_prompt(
        "daily_report",
        "【经营日报】{date}必读：您有{count}项关键事项待处理。详情：{items}",
        "正式版"
    )

    # 模拟用户选择
    for i in range(100):
        prompt = engine.get_best_prompt("daily_report")
        # 模拟反馈（第一个 prompt 更好）
        variant_id = hashlib.md5(prompt.encode()).hexdigest()[:8]
        positive = "简洁" in prompt or "早" in prompt  # 假设用户偏好简洁
        engine.record_prompt_feedback("daily_report", variant_id, positive)

    leaderboard = engine.ab_manager.get_leaderboard("daily_report")
    print("  Prompt 排行榜（Top 3）：")
    for entry in leaderboard[:3]:
        print(f"    [{entry['id']}] score={entry['score']:.4f} uses={entry['uses']} | {entry['description']}")

    # 3. 模板进化
    print("\n[3] 模板进化...")

    base_template = "建议关注{topic}，因为{reason}"
    engine.template_evolver.add_template("risk_alert", base_template)

    evolved = engine.evolve_templates(
        "risk_alert",
        base_template,
        feedback="不够详细"
    )
    print(f"  基础模板：{base_template}")
    print(f"  进化结果：{evolved}")

    # 4. 状态总览
    print("\n[4] 引擎状态：")
    status = engine.get_status()
    print(f"  注册模块数：{len(status['modules'])}")
    print(f"  A/B 测试任务数：{len(status['ab_tests'])}")
    print(f"  模板类别数：{len(status['template_categories'])}")
    print(f"  进化事件数：{status['evolution_log_count']}")

    print("\n" + "=" * 60)
    print("✅ RSI 自主演化引擎演示完成")
    print("模块热替换 + Prompt A/B 测试 + 模板进化 全部就绪")
