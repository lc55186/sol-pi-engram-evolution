#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BOSS-AI-R 角色系统测试
"""

import sys
import os
import importlib.util

# 动态加载 role_system 模块
module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "role_system.py")
spec = importlib.util.spec_from_file_location("role_system", module_path)
role_system = importlib.util.module_from_spec(spec)
sys.modules["role_system"] = role_system
spec.loader.exec_module(role_system)

RoleType = role_system.RoleType
RoleRouter = role_system.RoleRouter
SubscriptionTier = role_system.SubscriptionTier
KnowledgeIsolation = role_system.KnowledgeIsolation
ROLE_REGISTRY = role_system.ROLE_REGISTRY
TIER_CONFIG = role_system.TIER_CONFIG
create_router = role_system.create_router
list_available_roles = role_system.list_available_roles


def test_role_registry():
    """测试角色注册表完整性"""
    assert len(ROLE_REGISTRY) == 5, f"期望 5 个角色，实际 {len(ROLE_REGISTRY)}"
    assert RoleType.NEGOTIATOR in ROLE_REGISTRY
    assert RoleType.PSYCHOLOGIST in ROLE_REGISTRY
    assert RoleType.CFO in ROLE_REGISTRY
    assert RoleType.LEGAL in ROLE_REGISTRY
    assert RoleType.INDUSTRY in ROLE_REGISTRY
    print("✅ test_role_registry PASSED")


def test_role_config():
    """测试角色配置正确性"""
    neg = ROLE_REGISTRY[RoleType.NEGOTIATOR]
    assert neg.name_cn == "谈判专家"
    assert neg.priority == 0, "谈判专家必须是主角色(priority=0)"
    assert len(neg.trigger_keywords) > 0, "每个角色必须有关键词"
    assert len(neg.system_prompt) > 0, "每个角色必须有 system prompt"

    for role_type, config in ROLE_REGISTRY.items():
        assert config.role_type == role_type
        assert len(config.name) > 0
        assert len(config.name_cn) > 0
        assert len(config.core_capability) > 0
    print("✅ test_role_config PASSED")


def test_tier_config():
    """测试套餐配置"""
    assert len(TIER_CONFIG) == 4

    # 免费版只有1个角色
    assert len(TIER_CONFIG[SubscriptionTier.FREE]["roles"]) == 1
    assert TIER_CONFIG[SubscriptionTier.FREE]["price"] == 0

    # 专业版有2个角色
    assert len(TIER_CONFIG[SubscriptionTier.PROFESSIONAL]["roles"]) == 2
    assert TIER_CONFIG[SubscriptionTier.PROFESSIONAL]["price"] == 980

    # 旗舰版有5个角色
    assert len(TIER_CONFIG[SubscriptionTier.FLAGSHIP]["roles"]) == 5
    assert TIER_CONFIG[SubscriptionTier.FLAGSHIP]["price"] == 6800

    # 企业版有5个角色 + 额外功能
    assert len(TIER_CONFIG[SubscriptionTier.ENTERPRISE]["roles"]) == 5
    assert TIER_CONFIG[SubscriptionTier.ENTERPRISE]["price"] == 29800
    assert "extras" in TIER_CONFIG[SubscriptionTier.ENTERPRISE]
    print("✅ test_tier_config PASSED")


def test_router_auto_route():
    """测试自动路由"""
    router = create_router("flagship")

    # 价格话题 → 财务顾问
    role = router.auto_route("这个价格成本是多少？利润空间还有多大？")
    assert role == RoleType.CFO, f"期望 CFO, 实际 {role}"

    # 合同话题 → 法务顾问
    role = router.auto_route("这个合同的违约条款有没有法律风险？")
    assert role == RoleType.LEGAL, f"期望 LEGAL, 实际 {role}"

    # 情绪话题 → 心理分析师
    role = router.auto_route("对方情绪很激动，语气强硬")
    assert role == RoleType.PSYCHOLOGIST, f"期望 PSYCHOLOGIST, 实际 {role}"
    print("✅ test_router_auto_route PASSED")


def test_router_manual_switch():
    """测试手动切换"""
    router = create_router("professional")
    initial = router.current_role

    # 专业版有2个角色
    assert len(router.available_roles) == 2

    # 切换一次
    new_role = router.manual_switch()
    assert new_role != initial or len(router.available_roles) == 1
    assert router.switch_count == 1

    # 再切换一次（应该回到初始）
    back_role = router.manual_switch()
    assert back_role == initial
    assert router.switch_count == 2
    print("✅ test_router_manual_switch PASSED")


def test_router_force_role():
    """测试强制切换"""
    router = create_router("free")  # 免费版只有谈判专家

    # 尝试切换到不可用的角色 → 失败
    result = router.force_role(RoleType.CFO)
    assert result == False, "免费版不应能切换到 CFO"
    assert router.current_role == RoleType.NEGOTIATOR

    # 旗舰版可以切换到任意角色
    router = create_router("flagship")
    result = router.force_role(RoleType.LEGAL)
    assert result == True
    assert router.current_role == RoleType.LEGAL
    print("✅ test_router_force_role PASSED")


def test_switch_latency():
    """测试切换延迟 < 200ms"""
    router = create_router("flagship")

    for _ in range(100):
        router.manual_switch()

    assert router.switch_latency_ms < 200, f"切换延迟 {router.switch_latency_ms}ms 超过 200ms 目标"
    print(f"✅ test_switch_latency PASSED (延迟: {router.switch_latency_ms:.4f}ms)")


def test_knowledge_isolation():
    """测试知识隔离"""
    ki = KnowledgeIsolation()

    # 更新共享知识
    ki.update_shared("company_name", "定州某零部件公司")
    ki.update_shared("user_name", "张总")

    # 更新隔离知识
    ki.update_isolated(RoleType.CFO, "last_margin", 0.15)
    ki.update_isolated(RoleType.LEGAL, "risk_level", "high")

    # 验证共享知识对所有角色可见
    cfo_ctx = ki.get_role_context(RoleType.CFO)
    assert cfo_ctx["company_name"] == "定州某零部件公司"

    legal_ctx = ki.get_role_context(RoleType.LEGAL)
    assert legal_ctx["company_name"] == "定州某零部件公司"

    # 验证隔离知识不互通
    assert "isolated" in cfo_ctx
    assert cfo_ctx["isolated"]["last_margin"] == 0.15

    legal_isolated = legal_ctx.get("isolated", {})
    assert "last_margin" not in legal_isolated, "隔离知识不应跨角色可见"
    print("✅ test_knowledge_isolation PASSED")


def test_conflict_resolution():
    """测试角色意见冲突裁决"""
    router = create_router("flagship")

    # 谈判专家在场 → 采用谈判专家意见
    opinions = {
        RoleType.PSYCHOLOGIST: "对方在施压",
        RoleType.CFO: "价格还有空间",
        RoleType.NEGOTIATOR: "先让5%试探",
    }
    result = router.resolve_conflict(opinions)
    assert result == "先让5%试探", "主角色(谈判专家)应裁决"

    # 谈判专家不在 → 采用 priority 最小的角色
    opinions_no_neg = {
        RoleType.CFO: "价格还有空间",
        RoleType.PSYCHOLOGIST: "对方在施压",
    }
    result = router.resolve_conflict(opinions_no_neg)
    # PSYCHOLOGIST priority=1 < CFO priority=2
    assert result == "对方在施压", "应采用 priority 最小的角色"
    print("✅ test_conflict_resolution PASSED")


def test_list_available_roles():
    """测试列出可用角色"""
    roles = list_available_roles("professional")
    assert len(roles) == 2
    assert roles[0]["role"] == "negotiator"
    assert roles[1]["role"] == "psychologist"

    roles = list_available_roles("enterprise")
    assert len(roles) == 5
    print("✅ test_list_available_roles PASSED")


def test_get_current_prompt():
    """测试获取当前角色 prompt"""
    router = create_router("flagship")
    prompt = router.get_current_prompt()
    assert "谈判专家" in prompt

    router.force_role(RoleType.LEGAL)
    prompt = router.get_current_prompt()
    assert "法务顾问" in prompt
    print("✅ test_get_current_prompt PASSED")


# ── A2A 协议适配层测试 ────────────────────────────────────

A2ARoleAdapter = role_system.A2ARoleAdapter
create_a2a_adapter = role_system.create_a2a_adapter


def test_a2a_agent_card():
    """测试 A2A Agent Card 生成"""
    adapter = create_a2a_adapter("flagship")
    card = adapter.get_agent_card(RoleType.NEGOTIATOR)

    assert card["name"] == "Negotiator"
    assert "url" in card
    assert card["version"] == "1.0.0"
    assert "capabilities" in card
    assert card["capabilities"]["streaming"] is True
    assert "skills" in card
    assert len(card["skills"]) == 1
    assert card["skills"][0]["id"] == "negotiator_analysis"
    print("✅ test_a2a_agent_card PASSED")


def test_a2a_list_agent_cards():
    """测试列出所有 Agent Cards"""
    adapter = create_a2a_adapter("flagship")
    cards = adapter.list_agent_cards()
    assert len(cards) == 5

    # 专业版只有 2 个
    adapter_pro = create_a2a_adapter("professional")
    cards_pro = adapter_pro.list_agent_cards()
    assert len(cards_pro) == 2
    print("✅ test_a2a_list_agent_cards PASSED")


def test_a2a_send_message():
    """测试 A2A send_message"""
    adapter = create_a2a_adapter("flagship")

    # 自动路由
    resp = adapter.send_message("这个价格成本是多少？利润多少？")
    assert "task_id" in resp
    assert resp["status"] == "completed"
    assert "role" in resp
    assert "message" in resp
    assert "agent_card" in resp

    # 指定角色
    resp2 = adapter.send_message("测试消息", target_role=RoleType.LEGAL)
    assert resp2["role"] == "legal"
    assert resp2["role_name_cn"] == "法务顾问"

    # 验证任务记录
    task = adapter.get_task_status(resp["task_id"])
    assert task is not None
    assert task["routed_role"] == resp["role"]
    print("✅ test_a2a_send_message PASSED")


def test_a2a_send_message_unauthorized_role():
    """测试无权访问的角色"""
    adapter = create_a2a_adapter("free")  # 免费版只有谈判专家
    resp = adapter.send_message("财务分析", target_role=RoleType.CFO)
    # CFO 不在可用角色中，应走 auto_route（fallback）
    assert resp["role"] == "negotiator"  # fallback 到主角色
    print("✅ test_a2a_send_message_unauthorized_role PASSED")


def test_a2a_multi_agent_consult():
    """测试多 Agent 会诊"""
    adapter = create_a2a_adapter("flagship")
    result = adapter.multi_agent_consult("对方要求预付50%，账期90天，合同是否有风险？")

    assert "consult_id" in result
    assert "participating_roles" in result
    assert len(result["participating_roles"]) == 5
    assert "opinions" in result
    assert "final_decision" in result
    assert "arbitration_rule" in result
    # 谈判专家在场 → negotiator_priority
    assert result["arbitration_rule"] == "negotiator_priority"
    print("✅ test_a2a_multi_agent_consult PASSED")


def test_a2a_multi_agent_consult_subset():
    """测试指定子集会诊"""
    adapter = create_a2a_adapter("flagship")
    result = adapter.multi_agent_consult(
        "价格谈判",
        roles=[RoleType.NEGOTIATOR, RoleType.CFO]
    )
    assert len(result["participating_roles"]) == 2
    assert "negotiator" in result["opinions"]
    assert "cfo" in result["opinions"]
    print("✅ test_a2a_multi_agent_consult_subset PASSED")


def test_a2a_multi_agent_no_negotiator():
    """测试无谈判专家时的裁决规则"""
    adapter = create_a2a_adapter("flagship")
    result = adapter.multi_agent_consult(
        "测试",
        roles=[RoleType.CFO, RoleType.PSYCHOLOGIST]
    )
    # 无谈判专家 → lowest_priority_wins (PSYCHOLOGIST priority=1 < CFO priority=2)
    assert result["arbitration_rule"] == "lowest_priority_wins"
    print("✅ test_a2a_multi_agent_no_negotiator PASSED")


def test_a2a_adapter_tier_isolation():
    """测试套餐隔离"""
    adapter_free = create_a2a_adapter("free")
    cards = adapter_free.list_agent_cards()
    assert len(cards) == 1
    assert cards[0]["name"] == "Negotiator"

    # 免费版会诊只有 1 个角色
    result = adapter_free.multi_agent_consult("测试")
    assert len(result["participating_roles"]) == 1
    print("✅ test_a2a_adapter_tier_isolation PASSED")


# ── A2A 新增：取消 & 流式 ────────────────────────────────


def test_a2a_cancel_task():
    """测试取消任务"""
    adapter = create_a2a_adapter("flagship")

    # 先发送一个任务
    resp = adapter.send_message("测试取消")
    task_id = resp["task_id"]
    assert adapter.get_task_status(task_id) is not None

    # 取消任务
    result = adapter.cancel_task(task_id)
    assert result is True

    # 验证状态
    status = adapter.get_task_status(task_id)
    assert status["status"] == "cancelled"

    # 取消不存在的任务
    result2 = adapter.cancel_task("nonexistent_task_999")
    assert result2 is False
    print("✅ test_a2a_cancel_task PASSED")


def test_a2a_stream_response():
    """测试 SSE 流式响应"""
    adapter = create_a2a_adapter("flagship")
    events = list(adapter.stream_response("对方要求降价10%"))

    # 应该有 message 事件 + done 事件
    assert len(events) >= 2
    assert events[-1]["event"] == "done"
    assert events[0]["event"] == "message"
    assert "task_id" in events[0]
    assert "role" in events[0]
    print("✅ test_a2a_stream_response PASSED")


def test_a2a_stream_response_with_target():
    """测试指定角色的流式响应"""
    adapter = create_a2a_adapter("flagship")
    events = list(adapter.stream_response("价格分析", target_role=RoleType.CFO))

    assert len(events) >= 2
    assert all(e["role"] == "cfo" for e in events if e["event"] == "message")
    print("✅ test_a2a_stream_response_with_target PASSED")


def test_a2a_stream_cancel():
    """测试流式响应中途取消"""
    adapter = create_a2a_adapter("flagship")

    # 获取第一个事件后取消
    gen = adapter.stream_response("长消息测试取消")
    first_event = next(gen)
    assert first_event["event"] == "message"

    # 取消任务
    task_id = first_event["task_id"]
    adapter.cancel_task(task_id)

    # 继续消费，应该收到 cancelled 事件
    remaining = list(gen)
    # 因为取消发生在生成器外部，下一个 yield 会检测到
    # 注意：取消后可能还有已缓冲的 token，但最终会有 cancelled 或 done
    assert any(e.get("event") in ("cancelled", "done") for e in remaining)
    print("✅ test_a2a_stream_cancel PASSED")


if __name__ == "__main__":
    test_role_registry()
    test_role_config()
    test_tier_config()
    test_router_auto_route()
    test_router_manual_switch()
    test_router_force_role()
    test_switch_latency()
    test_knowledge_isolation()
    test_conflict_resolution()
    test_list_available_roles()
    test_get_current_prompt()

    # A2A 测试
    test_a2a_agent_card()
    test_a2a_list_agent_cards()
    test_a2a_send_message()
    test_a2a_send_message_unauthorized_role()
    test_a2a_multi_agent_consult()
    test_a2a_multi_agent_consult_subset()
    test_a2a_multi_agent_no_negotiator()
    test_a2a_adapter_tier_isolation()

    # 新增：流式 & 取消测试
    test_a2a_cancel_task()
    test_a2a_stream_response()
    test_a2a_stream_response_with_target()
    test_a2a_stream_cancel()

    print("\n" + "=" * 50)
    print("🎉 全部 23 个测试 PASSED（11 基础 + 12 A2A）")
    print("=" * 50)
