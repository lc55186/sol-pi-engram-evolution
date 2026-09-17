#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
BOSS-AI-R 多角色顾问系统 — 角色定义、切换逻辑、知识隔离

基于 PRD: docs/deployer-report-2026-09-17.md 第二节
5 个角色: 谈判专家/心理分析师/财务顾问/法务顾问/行业顾问
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RoleType(Enum):
    """角色类型枚举"""
    NEGOTIATOR = "negotiator"       # 谈判专家（主角色）
    PSYCHOLOGIST = "psychologist"   # 心理分析师
    CFO = "cfo"                     # 财务顾问
    LEGAL = "legal"                 # 法务顾问
    INDUSTRY = "industry"           # 行业顾问


@dataclass
class RoleConfig:
    """单个角色配置"""
    role_type: RoleType
    name: str
    name_cn: str
    core_capability: str
    knowledge_base: str
    trigger_keywords: list[str]
    system_prompt: str
    is_active: bool = True
    priority: int = 0  # 0=主角色, 1-4=辅助角色


# ── 角色 Prompt 模板 ──────────────────────────────────────

NEGOTIATOR_PROMPT = """你是「谈判专家」，BOSS-AI-R 系统的主顾问角色。
核心能力：谈判策略制定、让步分析、BATNA 计算、时机判断。
风格：简洁、直接、不废话。用一句话给出建议，必要时附数据支撑。
谈判原则：永远保护用户底线，识别对方施压信号，把握让步节奏。"""

PSYCHOLOGIST_PROMPT = """你是「心理分析师」，负责实时分析谈判对手的心理状态。
核心能力：情绪识别（语调/用词/停顿）、意图推断、压力点判断、欺骗检测。
风格：客观分析，给出置信度。示例："对方语速加快(72%置信度) → 可能在施压"。
关注：微表情描述、语气变化、用词情绪倾向。"""

CFO_PROMPT = """你是「财务顾问」，负责谈判中的财务维度分析。
核心能力：成本核算、利润分析、付款条件评估、税务优化建议。
风格：数据驱动，给出具体数字和百分比。
原则：每笔交易都要算清楚账，识别对方的财务施压手段。"""

LEGAL_PROMPT = """你是「法务顾问」，负责谈判中的法律风险防控。
核心能力：合同风险识别、条款审查、合规检查、承诺法律效力评估。
风格：谨慎、引用具体法规条文。示例："根据合同法第52条，此条款存在…"。
原则：任何口头承诺都需要书面确认，识别不平等条款。"""

INDUSTRY_PROMPT = """你是「行业顾问」，聚焦定州三大产业行情。
核心能力：汽车零部件/体育器材/再生资源 产业供需、价格趋势、竞争格局。
风格：本地化、接地气。引用定州本地市场数据。
数据来源：定州产业数据库、1688 行情、本地商会信息。"""


# ── 角色注册表 ────────────────────────────────────────────

ROLE_REGISTRY: dict[RoleType, RoleConfig] = {
    RoleType.NEGOTIATOR: RoleConfig(
        role_type=RoleType.NEGOTIATOR,
        name="Negotiator",
        name_cn="谈判专家",
        core_capability="谈判策略、让步分析、BATNA计算",
        knowledge_base="谈判心理学/定州产业行情",
        trigger_keywords=["谈判", "条件", "合作", "交易", "价格讨论"],
        system_prompt=NEGOTIATOR_PROMPT,
        priority=0,
    ),
    RoleType.PSYCHOLOGIST: RoleConfig(
        role_type=RoleType.PSYCHOLOGIST,
        name="Psychologist",
        name_cn="心理分析师",
        core_capability="对方情绪识别、意图推断、压力点判断",
        knowledge_base="微表情/语调/用词模式",
        trigger_keywords=["对方说", "情绪", "态度", "感觉", "语气"],
        system_prompt=PSYCHOLOGIST_PROMPT,
        priority=1,
    ),
    RoleType.CFO: RoleConfig(
        role_type=RoleType.CFO,
        name="CFO",
        name_cn="财务顾问",
        core_capability="成本核算、利润分析、付款条件评估",
        knowledge_base="企业财务/税务规则",
        trigger_keywords=["价格", "成本", "利润", "付款", "账期", "发票", "税"],
        system_prompt=CFO_PROMPT,
        priority=2,
    ),
    RoleType.LEGAL: RoleConfig(
        role_type=RoleType.LEGAL,
        name="Legal",
        name_cn="法务顾问",
        core_capability="合同风险、条款审查、合规检查",
        knowledge_base="合同法/行业法规",
        trigger_keywords=["合同", "条款", "违约", "法律", "风险", "承诺", "协议"],
        system_prompt=LEGAL_PROMPT,
        priority=3,
    ),
    RoleType.INDUSTRY: RoleConfig(
        role_type=RoleType.INDUSTRY,
        name="Industry",
        name_cn="行业顾问",
        core_capability="定州三大产业行情分析",
        knowledge_base="产业数据库/供需信息",
        trigger_keywords=["零部件", "体育器材", "再生资源", "行情", "市场", "供应商"],
        system_prompt=INDUSTRY_PROMPT,
        priority=4,
    ),
}


# ── 订阅套餐定义 ──────────────────────────────────────────

class SubscriptionTier(Enum):
    """订阅套餐等级"""
    FREE = "free"
    PROFESSIONAL = "professional"
    FLAGSHIP = "flagship"
    ENTERPRISE = "enterprise"


TIER_CONFIG: dict[SubscriptionTier, dict] = {
    SubscriptionTier.FREE: {
        "name": "免费版",
        "price": 0,
        "roles": [RoleType.NEGOTIATOR],
        "target": "体验用户",
    },
    SubscriptionTier.PROFESSIONAL: {
        "name": "专业版",
        "price": 980,
        "roles": [RoleType.NEGOTIATOR, RoleType.PSYCHOLOGIST],
        "target": "个体老板",
    },
    SubscriptionTier.FLAGSHIP: {
        "name": "旗舰版",
        "price": 6800,
        "roles": list(RoleType),  # 全部5个角色
        "target": "中小企业",
    },
    SubscriptionTier.ENTERPRISE: {
        "name": "企业版",
        "price": 29800,
        "roles": list(RoleType),  # 全部角色 + 定制行业顾问
        "target": "规模企业",
        "extras": ["定制行业顾问", "API访问", "私有化部署"],
    },
}


# ── 角色路由器 ────────────────────────────────────────────

class RoleRouter:
    """
    角色路由器 — 自动/手动切换逻辑
    
    触发方式:
    1. 自动切换: ASR 实时识别关键词 → 路由到对应角色
    2. 手动切换: 用户双击耳机/手表按钮 → 循环切换角色
    3. 混合模式: 主角色(谈判专家)常驻 + 辅助角色按需弹出
    """

    def __init__(self, tier: SubscriptionTier = SubscriptionTier.FREE):
        self.tier = tier
        self.current_role = RoleType.NEGOTIATOR  # 默认主角色
        self.previous_role = RoleType.NEGOTIATOR
        self.switch_count = 0
        self.last_switch_time = 0.0
        self._switch_latency_ms = 0.0

    @property
    def available_roles(self) -> list[RoleType]:
        """返回当前套餐可用的角色列表"""
        return TIER_CONFIG[self.tier]["roles"]

    def auto_route(self, text: str) -> RoleType:
        """
        自动路由: 根据文本内容匹配关键词 → 返回最匹配的角色
        
        优先级规则:
        1. 关键词匹配数最多的角色
        2. 如果多个角色匹配数相同，选择 priority 值更小的
        3. 如果没有匹配，保持当前角色（通常是主角色）
        """
        text_lower = text.lower()
        best_role = self.current_role
        best_score = 0

        for role_type in self.available_roles:
            config = ROLE_REGISTRY[role_type]
            score = sum(1 for kw in config.trigger_keywords if kw in text_lower)
            if score > best_score or (score == best_score and config.priority < ROLE_REGISTRY[best_role].priority):
                best_score = score
                best_role = role_type

        if best_role != self.current_role:
            self._switch_to(best_role)

        return self.current_role

    def manual_switch(self) -> RoleType:
        """
        手动切换: 循环切换到下一个可用角色
        
        切换延迟目标: < 200ms
        """
        roles = self.available_roles
        current_idx = roles.index(self.current_role) if self.current_role in roles else 0
        next_idx = (current_idx + 1) % len(roles)
        next_role = roles[next_idx]
        self._switch_to(next_role)
        return self.current_role

    def force_role(self, role_type: RoleType) -> bool:
        """强制切换到指定角色（需确认权限）"""
        if role_type not in self.available_roles:
            return False
        self._switch_to(role_type)
        return True

    def _switch_to(self, new_role: RoleType):
        """内部切换逻辑，记录延迟"""
        start = time.monotonic()
        self.previous_role = self.current_role
        self.current_role = new_role
        self.switch_count += 1
        self._switch_latency_ms = (time.monotonic() - start) * 1000
        self.last_switch_time = time.time()

    def get_current_prompt(self) -> str:
        """获取当前角色的系统 prompt"""
        return ROLE_REGISTRY[self.current_role].system_prompt

    def get_shared_context(self) -> dict:
        """获取共享上下文（所有角色共享）"""
        return {
            "user_profile": {},       # 用户画像
            "negotiation_history": [], # 历史谈判记录
            "company_info": {},        # 企业基本信息
        }

    def get_isolated_context(self) -> dict:
        """获取隔离上下文（仅当前角色）"""
        config = ROLE_REGISTRY[self.current_role]
        return {
            "role": config.role_type.value,
            "name_cn": config.name_cn,
            "system_prompt": config.system_prompt,
            "knowledge_base": config.knowledge_base,
        }

    def resolve_conflict(self, opinions: dict[RoleType, str]) -> str:
        """
        多角色意见冲突时，主角色(谈判专家)做最终裁决
        
        Args:
            opinions: {角色: 意见} 字典
        Returns:
            最终裁决意见
        """
        if RoleType.NEGOTIATOR in opinions:
            return opinions[RoleType.NEGOTIATOR]
        # 如果没有谈判专家意见，返回 priority 最小的角色意见
        sorted_roles = sorted(opinions.keys(), key=lambda r: ROLE_REGISTRY[r].priority)
        return opinions[sorted_roles[0]]

    @property
    def switch_latency_ms(self) -> float:
        """最近一次切换延迟（毫秒）"""
        return self._switch_latency_ms


# ── 知识隔离层 ────────────────────────────────────────────

class KnowledgeIsolation:
    """
    知识隔离设计
    
    - 每个角色独立知识库，互不污染
    - 共享层: 用户画像、历史谈判记录、企业基本信息
    - 隔离层: 角色专属 Prompt、行业数据、分析框架
    """

    def __init__(self):
        self.shared_knowledge: dict = {}         # 共享知识层
        self.isolated_knowledge: dict[RoleType, dict] = {}  # 隔离知识层

    def update_shared(self, key: str, value):
        """更新共享知识"""
        self.shared_knowledge[key] = value

    def update_isolated(self, role: RoleType, key: str, value):
        """更新角色专属知识"""
        if role not in self.isolated_knowledge:
            self.isolated_knowledge[role] = {}
        self.isolated_knowledge[role][key] = value

    def get_role_context(self, role: RoleType) -> dict:
        """获取角色的完整上下文（共享 + 隔离）"""
        context = dict(self.shared_knowledge)
        if role in self.isolated_knowledge:
            context["isolated"] = self.isolated_knowledge[role]
        return context


# ── 便捷函数 ──────────────────────────────────────────────

def create_router(tier_str: str = "free") -> RoleRouter:
    """工厂函数: 根据套餐字符串创建路由器"""
    tier_map = {
        "free": SubscriptionTier.FREE,
        "professional": SubscriptionTier.PROFESSIONAL,
        "flagship": SubscriptionTier.FLAGSHIP,
        "enterprise": SubscriptionTier.ENTERPRISE,
    }
    tier = tier_map.get(tier_str, SubscriptionTier.FREE)
    return RoleRouter(tier=tier)


def list_available_roles(tier_str: str = "free") -> list[dict]:
    """列出指定套餐可用的所有角色"""
    tier_map = {
        "free": SubscriptionTier.FREE,
        "professional": SubscriptionTier.PROFESSIONAL,
        "flagship": SubscriptionTier.FLAGSHIP,
        "enterprise": SubscriptionTier.ENTERPRISE,
    }
    tier = tier_map.get(tier_str, SubscriptionTier.FREE)
    roles = TIER_CONFIG[tier]["roles"]
    return [
        {
            "role": r.value,
            "name_cn": ROLE_REGISTRY[r].name_cn,
            "capability": ROLE_REGISTRY[r].core_capability,
        }
        for r in roles
    ]


# ── A2A 协议适配层 ────────────────────────────────────────
# Google A2A (Agent-to-Agent) Protocol 接口预留
# 参考: https://github.com/a2aproject/A2A
# 定位: MCP 管 Agent↔Tool，A2A 管 Agent↔Agent
# BOSS-AI-R 多角色架构可直接基于 A2A 标准互联


@dataclass
class AAACard:
    """A2A Agent Card — 角色能力声明（对外暴露的元数据）"""
    name: str
    description: str
    capabilities: list[str]
    input_modes: list[str] = field(default_factory=lambda: ["text"])
    output_modes: list[str] = field(default_factory=lambda: ["text"])
    version: str = "1.0.0"


class A2ARoleAdapter:
    """
    A2A 协议适配器 — 将 BOSS-AI-R 角色系统包装为 A2A 兼容接口
    
    每个角色对外暴露为独立 Agent，支持:
    - Agent Card 发现（能力声明）
    - 消息发送/接收（send_message / get_message）
    - 任务状态追踪（task_id → 角色 → 结果）
    - 流式响应（SSE 兼容）
    - 任务取消（cancel_task）
    """

    def __init__(self, router: RoleRouter):
        self.router = router
        self._task_log: dict[str, dict] = {}  # task_id → 执行记录
        self._cancelled_tasks: set[str] = set()  # 已取消的任务 ID

    def get_agent_card(self, role_type: RoleType) -> dict:
        """
        生成 A2A Agent Card（JSON 格式）
        
        A2A 协议要求每个 Agent 暴露 /.well-known/agent.json
        此方法生成对应角色的 Agent Card
        """
        config = ROLE_REGISTRY[role_type]
        return {
            "name": config.name,
            "description": config.core_capability,
            "url": f"/a2a/agents/{role_type.value}",
            "version": "1.0.0",
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
                "stateTransitionHistory": True,
            },
            "inputModes": ["text"],
            "outputModes": ["text"],
            "skills": [{
                "id": f"{role_type.value}_analysis",
                "name": config.name_cn,
                "description": config.core_capability,
                "tags": config.trigger_keywords[:5],
            }],
        }

    def list_agent_cards(self) -> list[dict]:
        """列出当前套餐所有可用角色的 Agent Card"""
        return [self.get_agent_card(r) for r in self.router.available_roles]

    def send_message(self, message: str, target_role: RoleType = None,
                     task_id: str = None) -> dict:
        """
        A2A send_message — 向指定角色发送消息（任务）
        
        Args:
            message: 消息内容（ASR 转写文本或用户输入）
            target_role: 目标角色（None 则自动路由）
            task_id: 任务 ID（可选，自动生成）
        
        Returns:
            A2A 标准响应格式
        """
        import uuid
        if task_id is None:
            task_id = str(uuid.uuid4())[:12]

        # 路由决策
        if target_role and target_role in self.router.available_roles:
            self.router.force_role(target_role)
            routed_role = target_role
        else:
            routed_role = self.router.auto_route(message)

        config = ROLE_REGISTRY[routed_role]

        # 构建 A2A 标准响应
        response = {
            "task_id": task_id,
            "status": "completed",
            "role": routed_role.value,
            "role_name_cn": config.name_cn,
            "agent_card": self.get_agent_card(routed_role),
            "message": {
                "role": "agent",
                "parts": [{
                    "type": "text",
                    "text": f"[{config.name_cn}] 已接收，系统 Prompt 已激活: {config.system_prompt[:100]}..."
                }],
            },
            "timestamp": time.time(),
            "metadata": {
                "system_prompt_full": config.system_prompt,
                "knowledge_base": config.knowledge_base,
                "shared_context": self.router.get_shared_context(),
                "isolated_context": self.router.get_isolated_context(),
            },
        }

        # 记录任务
        self._task_log[task_id] = {
            "message": message,
            "routed_role": routed_role.value,
            "timestamp": response["timestamp"],
        }

        return response

    def get_task_status(self, task_id: str) -> dict | None:
        """查询任务状态"""
        if task_id in self._cancelled_tasks:
            return {"task_id": task_id, "status": "cancelled"}
        return self._task_log.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务 — A2A 协议标准操作
        
        Returns:
            True 如果成功取消，False 如果任务不存在或已完成
        """
        if task_id in self._task_log or task_id in self._cancelled_tasks:
            self._cancelled_tasks.add(task_id)
            return True
        return False

    def stream_response(self, message: str, target_role: RoleType = None):
        """
        SSE 流式响应生成器 — 逐 token 产出响应
        
        A2A 协议 streaming=True 时的标准接口
        实际部署时对接 LLM streaming API，当前为模拟实现
        
        Yields:
            dict: SSE 事件 {"event": "message"|"error"|"done", "data": str}
        """
        import uuid
        task_id = str(uuid.uuid4())[:12]

        # 路由决策
        if target_role and target_role in self.router.available_roles:
            routed_role = target_role
        else:
            routed_role = self.router.auto_route(message)

        config = ROLE_REGISTRY[routed_role]

        # 模拟流式输出（实际部署替换为 LLM streaming）
        full_text = f"[{config.name_cn}] 分析: {message}"
        tokens = full_text.split()

        for i, token in enumerate(tokens):
            if task_id in self._cancelled_tasks:
                yield {"event": "cancelled", "data": "", "task_id": task_id}
                return
            yield {
                "event": "message",
                "data": token + " ",
                "task_id": task_id,
                "role": routed_role.value,
                "index": i,
            }

        # 记录任务
        self._task_log[task_id] = {
            "message": message,
            "routed_role": routed_role.value,
            "timestamp": time.time(),
            "status": "completed",
        }

        yield {"event": "done", "data": "", "task_id": task_id}

    def multi_agent_consult(self, message: str,
                            roles: list[RoleType] = None) -> dict:
        """
        多 Agent 会诊 — 同时向多个角色发送消息，汇总意见
        
        这是 BOSS-AI-R 的核心差异化能力：
        一个输入 → 多角色并行分析 → 冲突裁决 → 统一输出
        
        Args:
            message: 输入消息
            roles: 参与角色列表（None 则使用全部可用角色）
        
        Returns:
            多角色意见 + 最终裁决
        """
        if roles is None:
            roles = self.router.available_roles

        opinions: dict[RoleType, str] = {}
        agent_responses: list[dict] = []

        for role in roles:
            if role not in self.router.available_roles:
                continue
            resp = self.send_message(message, target_role=role)
            opinions[role] = resp["message"]["parts"][0]["text"]
            agent_responses.append(resp)

        # 冲突裁决
        final_decision = self.router.resolve_conflict(opinions)

        return {
            "consult_id": f"consult_{int(time.time() * 1000)}",
            "participating_roles": [r.value for r in roles],
            "opinions": {r.value: t for r, t in opinions.items()},
            "final_decision": final_decision,
            "arbitration_rule": "negotiator_priority" if RoleType.NEGOTIATOR in opinions else "lowest_priority_wins",
            "agent_responses": agent_responses,
        }


def create_a2a_adapter(tier_str: str = "free") -> A2ARoleAdapter:
    """工厂函数: 创建 A2A 适配器"""
    router = create_router(tier_str)
    return A2ARoleAdapter(router)


# ── 便捷导出 ──────────────────────────────────────────────

__all__ = [
    "RoleType",
    "RoleConfig",
    "RoleRouter",
    "KnowledgeIsolation",
    "SubscriptionTier",
    "ROLE_REGISTRY",
    "TIER_CONFIG",
    "create_router",
    "list_available_roles",
    "A2ARoleAdapter",
    "create_a2a_adapter",
    "AAACard",
]


if __name__ == "__main__":
    # 快速验证
    router = create_router("professional")
    print(f"当前角色: {router.current_role.value} ({ROLE_REGISTRY[router.current_role].name_cn})")
    print(f"可用角色: {[r.value for r in router.available_roles]}")

    # 测试自动路由
    test_texts = [
        "对方说价格太高了，情绪有点激动",
        "这个合同的违约条款是不是有问题？",
        "定州零部件供应商报价涨了10%",
    ]
    for text in test_texts:
        routed = router.auto_route(text)
        print(f"  '{text[:20]}...' → {routed.value} ({ROLE_REGISTRY[routed].name_cn})")

    # 测试手动切换
    router.manual_switch()
    print(f"手动切换后: {router.current_role.value}")

    # 验证延迟
    print(f"切换延迟: {router.switch_latency_ms:.2f}ms (目标 < 200ms)")

    # 测试 A2A 适配器
    print("\n--- A2A 协议适配层测试 ---")
    adapter = create_a2a_adapter("flagship")

    # Agent Card 发现
    cards = adapter.list_agent_cards()
    print(f"可用 Agent Cards: {len(cards)} 个")
    for card in cards:
        print(f"  - {card['name']}: {card['description'][:30]}...")

    # 单角色消息
    resp = adapter.send_message("对方报价比成本高30%，情绪很自信")
    print(f"\n单角色响应: task_id={resp['task_id']}, role={resp['role']}")

    # 多 Agent 会诊
    consult = adapter.multi_agent_consult("对方要求预付50%，账期90天")
    print(f"\n多 Agent 会诊: {len(consult['participating_roles'])} 个角色参与")
    print(f"最终裁决: {consult['final_decision'][:50]}...")
