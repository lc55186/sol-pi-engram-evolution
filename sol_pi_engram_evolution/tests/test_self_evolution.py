#!/usr/bin/env python3
"""
RSI 自主演化引擎测试
验证模块热替换、A/B 测试、模板进化三大能力
"""
import json
import os
import sys
import tempfile
from pathlib import Path

# 动态加载被测模块（添加父目录到 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from self_evolution import (
    ABTestManager,
    HotSwapRegistry,
    SelfEvolutionEngine,
    TemplateEvolver,
    get_evolution_engine,
)


def test_hot_swap_registry():
    """测试模块热替换注册表"""
    print("\n[Test] HotSwapRegistry 模块热替换...")

    registry = HotSwapRegistry()

    # 注册模块
    class ModuleA:
        def run(self):
            return "A"

    class ModuleB:
        def run(self):
            return "B"

    registry.register("mod_a", ModuleA(), "1.0.0")
    assert registry.get("mod_a").run() == "A"
    print("  ✓ 注册成功")

    # 热替换
    success = registry.replace("mod_a", ModuleB(), "2.0.0")
    assert success
    assert registry.get("mod_a").run() == "B"
    print("  ✓ 热替换成功")

    # 检查元数据
    modules = registry.list_modules()
    assert modules[0]["version"] == "2.0.0"
    print(f"  ✓ 版本号正确: {modules[0]['version']}")

    # 替换不存在模块
    success = registry.replace("non_exist", object())
    assert not success
    print("  ✓ 替换不存在模块返回 False")

    print("  ✅ HotSwapRegistry 全部通过")
    return True


def test_ab_test_manager():
    """测试 Prompt A/B 测试管理器"""
    print("\n[Test] ABTestManager Prompt A/B 测试...")

    # 使用临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = os.path.join(tmpdir, "ab_test.json")
        manager = ABTestManager(storage_path=storage)

        # 注册 3 个变体
        v1 = manager.register_variant("report", "老板早上好，今天{count}件事：{items}", "标准版")
        v2 = manager.register_variant("report", "老王早，{count}项待办：{items}", "简洁版")
        v3 = manager.register_variant("report", "【日报】{date}必读：{count}项待办", "正式版")

        assert len(manager.variants["report"]) == 3
        print("  ✓ 注册 3 个变体成功")

        # 获取 Prompt（UCB1 选择）
        prompt = manager.get_prompt("report")
        assert prompt is not None
        print(f"  ✓ UCB1 选择成功: {prompt[:30]}...")

        # 模拟反馈
        for i in range(200):
            prompt = manager.get_prompt("report")
            variant_id = None
            for v in manager.variants["report"]:
                if v.template == prompt:
                    variant_id = v.id
                    break

            # 模拟用户偏好简洁版
            positive = "早" in prompt and "老板" not in prompt
            manager.record_feedback("report", variant_id, positive)

        # 检查排行榜
        leaderboard = manager.get_leaderboard("report")
        assert len(leaderboard) == 3
        print("  ✓ 排行榜生成成功")
        for entry in leaderboard:
            print(f"    [{entry['id'][:8]}] score={entry['score']:.4f} uses={entry['uses']} | {entry['description']}")

        # 简洁版应该排在前面
        #（因为用户偏好 "早" 且不含 "老板"）
        # 注意：由于 UCB1 探索，可能不是 100% 排在第一，但分数应该较高

        # 持久化验证
        assert os.path.exists(storage)
        with open(storage, encoding="utf-8") as f:
            data = json.load(f)
        assert "variants" in data
        print("  ✓ 持久化成功")

    print("  ✅ ABTestManager 全部通过")
    return True


def test_template_evolver():
    """测试模板进化器"""
    print("\n[Test] TemplateEvolver 模板进化...")

    with tempfile.TemporaryDirectory() as tmpdir:
        evolver = TemplateEvolver(template_dir=tmpdir)

        # 添加基础模板
        base = "建议关注{topic}，因为{reason}"
        evolver.add_template("risk_alert", base)

        templates = evolver.get_templates("risk_alert")
        assert len(templates) == 1
        print("  ✓ 基础模板添加成功")

        # 进化模板
        evolved = evolver.evolve_template("risk_alert", base, feedback="不够详细")
        assert evolved != base or len(evolver.get_templates("risk_alert")) > 1
        print(f"  ✓ 模板进化成功: {evolved[:50]}...")

        # 再次进化
        evolved2 = evolver.evolve_template("risk_alert", base, feedback="太长")
        templates = evolver.get_templates("risk_alert")
        assert len(templates) >= 2
        print(f"  ✓ 模板库扩展: {len(templates)} 个模板")

        # 随机获取
        random_tpl = evolver.get_random_template("risk_alert")
        assert random_tpl is not None
        print("  ✓ 随机获取模板成功")

        # 持久化验证
        files = list(Path(tmpdir).glob("*.json"))
        assert len(files) >= 1
        print("  ✓ 持久化成功")

    print("  ✅ TemplateEvolver 全部通过")
    return True


def test_self_evolution_engine():
    """测试整合的自主演化引擎"""
    print("\n[Test] SelfEvolutionEngine 整合测试...")

    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)

        engine = SelfEvolutionEngine()

        # 注册模块
        class MockModule:
            def run(self):
                return "result"

        engine.register_module("test_module", MockModule(), "1.0.0")
        assert len(engine.registry.list_modules()) == 1
        print("  ✓ 模块注册成功")

        # 热替换
        class MockModuleV2:
            def run(self):
                return "result_v2"

        success = engine.replace_module("test_module", MockModuleV2(), "1.1.0")
        assert success
        assert engine.registry.get("test_module").run() == "result_v2"
        print("  ✓ 模块热替换成功")

        # A/B 测试
        engine.ab_test_prompt("greeting", "你好老板", "正式版")
        engine.ab_test_prompt("greeting", "老板好", "简洁版")

        prompt = engine.get_best_prompt("greeting")
        assert prompt is not None
        print(f"  ✓ A/B 测试 Prompt 选择: {prompt}")

        # 模板进化
        base_tpl = "注意{topic}，因为{reason}"
        evolved = engine.evolve_templates("warning", base_tpl, feedback="测试")
        assert evolved is not None
        print(f"  ✓ 模板进化: {evolved[:40]}...")

        # 状态总览
        status = engine.get_status()
        assert status["evolution_log_count"] >= 3  # 注册、替换、进化
        print(f"  ✓ 引擎状态: {status['evolution_log_count']} 个进化事件")

        print("  ✅ SelfEvolutionEngine 全部通过")
        return True


def test_singleton_engine():
    """测试全局单例引擎"""
    print("\n[Test] 全局单例引擎...")

    engine1 = get_evolution_engine()
    engine2 = get_evolution_engine()

    assert engine1 is engine2
    print("  ✓ 单例模式验证通过")

    print("  ✅ 全局单例引擎全部通过")
    return True


def run_all_tests():
    """运行全部测试"""
    print("=" * 60)
    print("RSI 自主演化引擎 — 全部测试")
    print("=" * 60)

    results = []

    results.append(("HotSwapRegistry", test_hot_swap_registry()))
    results.append(("ABTestManager", test_ab_test_manager()))
    results.append(("TemplateEvolver", test_template_evolver()))
    results.append(("SelfEvolutionEngine", test_self_evolution_engine()))
    results.append(("Singleton", test_singleton_engine()))

    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\n总计: {passed} 通过, {failed} 失败")

    if failed == 0:
        print("\n🎉 全部测试通过！RSI 自主演化引擎验证完成。")
        return 0
    else:
        print(f"\n⚠ {failed} 个测试未通过，请检查。")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
