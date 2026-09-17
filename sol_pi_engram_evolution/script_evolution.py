#!/usr/bin/env python3
"""
话术库自动进化 Workflow — 基于 RSI 的递归自我改进
功能：
  1. 基于 Mano-P Benchmark 设定 GUI 操作模块的 KPI
  2. 话术模板自动生成 → A/B 测试 → 反馈收集 → 淘汰/晋升
  3. 谈判话术库自动扩展（行业知识沉淀）
"""
import json
import random
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


# ========== ① GUI 操作模块 KPI（基于 Mano-P Benchmark） ==========

MANO_P_KPIS = {
    # Mano-P OSWorld 58.2% 作为基线目标
    "gui_operation_success_rate": {
        "baseline": 0.582,  # Mano-P 的水平
        "target": 0.75,     # 超越 Mano-P
        "stretch_goal": 0.85,
        "description": "GUI 操作成功率（点击/输入/滚动等）"
    },
    # Mano-P WebRetriever 41.7 NavEval
    "web_retrieval_accuracy": {
        "baseline": 0.417,
        "target": 0.55,
        "stretch_goal": 0.65,
        "description": "网页信息检索准确率"
    },
    # Mano-P 解码速度 ~80 tokens/s
    "inference_speed": {
        "baseline": 80,     # tokens/s
        "target": 120,
        "stretch_goal": 200,
        "description": "端侧推理速度（tokens/s）"
    },
    # 长任务完成（Mano-P 支持数十步至上百步）
    "long_task_steps": {
        "baseline": 50,     # 步
        "target": 80,
        "stretch_goal": 120,
        "description": "单次任务最大连续操作步数"
    },
    # 多说话人分离（参考 Agent S3 的 72.6% OSWorld）
    "speaker_separation_der": {
        "baseline": 0.25,   # DER (Diarization Error Rate)
        "target": 0.15,
        "stretch_goal": 0.10,
        "description": "说话人分离错误率（越低越好）"
    }
}


def get_gui_module_kpis() -> dict:
    """获取 GUI 操作模块 KPI 体系"""
    return {
        "source": "Mano-P Benchmark (OSWorld 58.2%, WebRetriever 41.7, ~80 tok/s)",
        "kpis": MANO_P_KPIS,
        "updated_at": datetime.now().isoformat()
    }


# ========== ② 话术库自动进化器 ==========

# 基础行业话术模板库
DEFAULT_TEMPLATES = {
    "汽配贸易": {
        "账期谈判": [
            "张总，这个账期我们确实有困难，能否折中一下？",
            "账期 60 天对我们压力太大，45 天是行业惯例，您看如何？",
            "如果我们预付 30%，账期能否缩短到 30 天？"
        ],
        "价格谈判": [
            "这个价格再降 5%，我们立刻签单",
            "我们年采购量 X 万，能否给到年度返利？",
            "竞争对手报价比您低 3%，您看怎么处理？"
        ],
        "质量扣款": [
            "质量问题我们承担，但需要书面确认责任范围",
            "扣款不超过合同金额的 5%，超过部分走保险",
            "批次问题退换货，不扣款"
        ]
    },
    "体育器材销售": {
        "经销商订货": [
            "王总，这次订货满 X 万返 Y%，年度还有额外返点",
            "预付 50% 享早付折扣 3%，您看合适吗？",
            "区域独家代理需要保底销量 X 件/年"
        ],
        "年度返点": [
            "销量达标返 5%，超量部分返 8%",
            "季度回款及时额外奖励 2%",
            "新品首单 10% 折扣，锁定全年合作"
        ]
    },
    "再生资源回收": {
        "现场看货定价": [
            "这批货杂质率 X%，需要扣减 Y%",
            "过磅误差在 3% 以内互不追究",
            "现款现货，价格比账期高 5%"
        ],
        "扣杂争议": [
            "第三方检测机构仲裁，费用双方平摊",
            "扣杂率超过 10% 部分由我们承担",
            "下次送货杂质率低于 X%，给予价格优惠"
        ]
    }
}


class NegotiationScriptEvolver:
    """谈判话术自动进化器"""

    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path or SCRIPT_DIR / "negotiation_scripts.json")
        self.scripts: dict = {}
        self.performance: dict[str, dict] = {}  # 话术使用统计
        self._load()

    def _load(self):
        """加载话术库"""
        if self.storage_path.exists():
            with open(self.storage_path, encoding="utf-8") as f:
                data = json.load(f)
                self.scripts = data.get("scripts", {})
                self.performance = data.get("performance", {})
        else:
            # 初始化默认话术库
            self.scripts = DEFAULT_TEMPLATES
            self._save()

    def _save(self):
        """持久化"""
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump({
                "scripts": self.scripts,
                "performance": self.performance,
                "updated_at": datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)

    def get_scripts(self, industry: str, scenario: str) -> list[str]:
        """获取某行业某场景的话术"""
        return self.scripts.get(industry, {}).get(scenario, [])

    def add_script(self, industry: str, scenario: str, script: str, source: str = "manual"):
        """添加新话术"""
        if industry not in self.scripts:
            self.scripts[industry] = {}
        if scenario not in self.scripts[industry]:
            self.scripts[industry][scenario] = []

        if script not in self.scripts[industry][scenario]:
            self.scripts[industry][scenario].append(script)
            script_key = f"{industry}:{scenario}:{hash(script) % 10000}"
            self.performance[script_key] = {
                "uses": 0,
                "success": 0,
                "source": source,
                "added_at": datetime.now().isoformat()
            }
            self._save()

    def record_usage(self, industry: str, scenario: str, script: str, success: bool):
        """记录话术使用效果"""
        script_key = f"{industry}:{scenario}:{hash(script) % 10000}"
        if script_key in self.performance:
            self.performance[script_key]["uses"] += 1
            if success:
                self.performance[script_key]["success"] += 1
            self._save()

    def get_top_scripts(self, industry: str, scenario: str, top_k: int = 3) -> list[dict]:
        """获取某场景下效果最好的 top_k 条话术"""
        scripts = self.get_scripts(industry, scenario)
        scored = []
        for s in scripts:
            key = f"{industry}:{scenario}:{hash(s) % 10000}"
            perf = self.performance.get(key, {"uses": 0, "success": 0})
            uses = perf["uses"]
            success = perf["success"]
            rate = success / uses if uses > 0 else 0.5
            scored.append({
                "script": s,
                "uses": uses,
                "success_rate": round(rate, 3),
                "source": perf.get("source", "unknown")
            })

        scored.sort(key=lambda x: x["success_rate"], reverse=True)
        return scored[:top_k]

    def auto_evolve(self, industry: str, scenario: str, feedback: str = "") -> str | None:
        """基于反馈自动进化话术"""
        scripts = self.get_scripts(industry, scenario)
        if not scripts:
            return None

        # 简单进化策略：基于反馈关键词生成变体
        variants = list(scripts)

        if "太强硬" in feedback or "直接" in feedback:
            # 生成更柔和的版本
            softer = [
                s.replace("必须", "建议")
                 .replace("需要", "能否考虑")
                 .replace("要求", "希望")
                for s in scripts
            ]
            variants.extend(softer)

        if "太软弱" in feedback or "退让" in feedback:
            # 生成更强硬的版本
            stronger = [
                s.replace("建议", "需要")
                 .replace("能否", "必须")
                 .replace("希望", "要求")
                for s in scripts
            ]
            variants.extend(stronger)

        if "太长了" in feedback or "啰嗦" in feedback:
            # 生成精简版
            shorter = [s[:len(s)//2] + "..." for s in scripts]
            variants.extend(shorter)

        # 选择最佳变体（后续可结合 A/B 测试）
        best = random.choice(variants)
        self.add_script(industry, scenario, best, source="auto_evolved")
        return best

    def get_stats(self) -> dict:
        """获取话术库统计"""
        total_scripts = 0
        industries = len(self.scripts)
        scenarios = 0

        for ind, scens in self.scripts.items():
            for scen, scripts in scens.items():
                scenarios += 1
                total_scripts += len(scripts)

        return {
            "industries": industries,
            "scenarios": scenarios,
            "total_scripts": total_scripts,
            "performance_records": len(self.performance),
            "top_performing": {
                ind: {
                    scen: self.get_top_scripts(ind, scen, 1)
                    for scen in scens.keys()
                }
                for ind, scens in self.scripts.items()
            }
        }


# ========== ③ 进化 Workflow 引擎 ==========

class EvolutionWorkflow:
    """话术库自动进化 Workflow — 完整闭环"""

    def __init__(self):
        self.evolver = NegotiationScriptEvolver()
        self.kpis = get_gui_module_kpis()

    def run_daily_evolution(self):
        """每日进化任务"""
        print(f"\n{'='*60}")
        print(f"RSI 话术库自动进化 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}")

        # Step 1: 统计当前状态
        stats = self.evolver.get_stats()
        print("\n[Step 1] 当前状态:")
        print(f"  行业数: {stats['industries']}")
        print(f"  场景数: {stats['scenarios']}")
        print(f"  话术总数: {stats['total_scripts']}")
        print(f"  性能记录: {stats['performance_records']}")

        # Step 2: 找出低效话术（使用次数多但成功率低）
        print("\n[Step 2] 低效话术检测:")
        low_performers = []
        for key, perf in self.evolver.performance.items():
            if perf["uses"] > 5 and perf["success"] / perf["uses"] < 0.3:
                low_performers.append({
                    "key": key,
                    "uses": perf["uses"],
                    "success_rate": perf["success"] / perf["uses"]
                })

        if low_performers:
            print(f"  发现 {len(low_performers)} 条低效话术:")
            for lp in low_performers[:3]:
                print(f"    - {lp['key']}: 成功率 {lp['success_rate']:.1%}")
        else:
            print("  暂无低效话术")

        # Step 3: 自动进化
        print("\n[Step 3] 自动进化:")
        evolved_count = 0
        for industry in self.evolver.scripts.keys():
            for scenario in self.evolver.scripts[industry].keys():
                # 随机选择一个场景进行进化
                if random.random() < 0.3:  # 30% 概率进化
                    new_script = self.evolver.auto_evolve(
                        industry, scenario,
                        feedback=random.choice(["太强硬", "太软弱", "太长了", ""])
                    )
                    if new_script:
                        evolved_count += 1
                        print(f"    ✓ {industry}/{scenario}: 新增话术")

        if evolved_count == 0:
            print("  今日无需进化")
        else:
            print(f"  共进化 {evolved_count} 条话术")

        # Step 4: KPI 报告
        print("\n[Step 4] GUI 模块 KPI 基线:")
        for kpi_name, kpi_data in self.kpis["kpis"].items():
            print(f"  {kpi_name}: 基线={kpi_data['baseline']}, 目标={kpi_data['target']}")

        print(f"\n{'='*60}")
        print("✅ 每日进化任务完成")
        print(f"{'='*60}")

        return stats


# ========== CLI ==========

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="话术库自动进化系统")
    sub = parser.add_subparsers(dest="command")

    # run 命令
    sub.add_parser("run", help="执行每日进化任务")

    # stats 命令
    sub.add_parser("stats", help="查看话术库统计")

    # add 命令
    p_add = sub.add_parser("add", help="添加话术")
    p_add.add_argument("--industry", required=True)
    p_add.add_argument("--scenario", required=True)
    p_add.add_argument("--script", required=True)

    # top 命令
    p_top = sub.add_parser("top", help="查看最佳话术")
    p_top.add_argument("--industry", required=True)
    p_top.add_argument("--scenario", required=True)

    # kpi 命令
    sub.add_parser("kpi", help="查看 GUI 模块 KPI")

    args = parser.parse_args()

    workflow = EvolutionWorkflow()

    if args.command == "run":
        workflow.run_daily_evolution()

    elif args.command == "stats":
        stats = workflow.evolver.get_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False, default=str))

    elif args.command == "add":
        workflow.evolver.add_script(args.industry, args.scenario, args.script)
        print(f"✅ 话术已添加: {args.industry}/{args.scenario}")

    elif args.command == "top":
        top = workflow.evolver.get_top_scripts(args.industry, args.scenario)
        print(json.dumps(top, indent=2, ensure_ascii=False))

    elif args.command == "kpi":
        print(json.dumps(workflow.kpis, indent=2, ensure_ascii=False))

    else:
        parser.print_help()
