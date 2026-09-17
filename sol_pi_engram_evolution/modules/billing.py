"""
BOSS-AI-R 订阅与计费模块（P1 优先）

核心职责：
1. 四级订阅管理：L0 免费 / L1 基础 / L2 专业 / L3 陪跑
2. 配额管理：时长、次数、功能权限控制
3. 成本监控：单用户月成本追踪、自建切换触发
4. 渠道分润：30-40% 阶梯分润
5. 数智券：保定数智券申报辅助

V0.1 实现：基于内存的订阅状态管理。
V0.2 扩展：持久化 + 微信支付/支付宝集成。
"""

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class SubscriptionTier(Enum):
    """订阅层级"""
    L0_FREE = "L0"
    L1_BASIC = "L1"
    L2_PROFESSIONAL = "L2"
    L3_ENTERPRISE = "L3"


class SubscriptionStatus(Enum):
    """订阅状态"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    TRIAL = "trial"
    GRACE_PERIOD = "grace_period"  # 宽限期


@dataclass
class QuotaUsage:
    """配额使用量"""
    session_id: str = ""
    tenant_id: str = ""
    user_id: str = ""

    # 时长配额（分钟）
    total_minutes_limit: int = 0
    used_minutes: int = 0
    remaining_minutes: int = 0

    # 次数配额
    total_sessions_limit: int = 0
    used_sessions: int = 0
    remaining_sessions: int = 0

    # 功能权限
    whisper_enabled: bool = False
    emotion_enabled: bool = False
    post_session_enabled: bool = False

    # 统计
    total_cost_rmb: float = 0.0  # 本月云成本（元）

    @property
    def usage_rate(self) -> float:
        """配额使用率"""
        if self.total_minutes_limit > 0:
            return self.used_minutes / self.total_minutes_limit
        return 0.0


@dataclass
class Subscription:
    """订阅记录"""
    subscription_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    tenant_id: str = ""
    user_id: str = ""
    tier: SubscriptionTier = SubscriptionTier.L0_FREE
    status: SubscriptionStatus = SubscriptionStatus.TRIAL

    # 时间
    created_at: int = 0
    expires_at: int = 0
    last_renewed_at: int = 0

    # 金额
    price_rmb: int = 0           # 实际支付金额
    channel_id: str = ""         # 渠道 ID（若有）
    channel_rate: float = 0.0    # 渠道分润比例

    # 支付
    payment_method: str = ""     # wechat / alipay / bank
    payment_status: str = "pending"  # pending / paid / failed / refunded


@dataclass
class CostBreakdown:
    """成本明细"""
    asr_cost: float = 0.0        # ASR 成本
    llm_cost: float = 0.0        # LLM 成本
    server_cost: float = 0.0     # 服务器成本
    storage_cost: float = 0.0    # 存储成本
    network_cost: float = 0.0    # 网络成本
    total_cost: float = 0.0      # 总成本

    # 对比
    self_hosted_cost: float = 0.0   # 自建方案成本
    cloud_cost: float = 0.0         # 全云方案成本
    savings: float = 0.0            # 节省金额


class SubscriptionManager:
    """
    订阅管理器
    
    管理用户订阅、配额、成本监控。
    """

    # 订阅层级配置
    TIER_CONFIG = {
        SubscriptionTier.L0_FREE: {
            "price_rmb": 0,
            "monthly_sessions": 3,
            "max_duration_minutes": 20,
            "whisper_enabled": False,
            "emotion_enabled": False,
            "post_session_enabled": False,
            "fair_use_hours": 0
        },
        SubscriptionTier.L1_BASIC: {
            "price_rmb": 1980,
            "price_monthly_rmb": 199,
            "monthly_sessions": -1,  # 不限次
            "max_duration_minutes": 600,  # 月 10h
            "whisper_enabled": False,
            "emotion_enabled": False,
            "post_session_enabled": True,
            "fair_use_hours": 10
        },
        SubscriptionTier.L2_PROFESSIONAL: {
            "price_rmb_min": 9800,
            "price_rmb_max": 15800,
            "price_rmb_default": 12800,
            "monthly_sessions": -1,
            "max_duration_minutes": -1,  # 不限时（公平使用）
            "whisper_enabled": True,
            "emotion_enabled": True,
            "post_session_enabled": True,
            "fair_use_hours": 200
        },
        SubscriptionTier.L3_ENTERPRISE: {
            "price_rmb_min": 39800,
            "price_rmb_max": 69800,
            "price_rmb_default": 54800,
            "monthly_sessions": -1,
            "max_duration_minutes": -1,
            "whisper_enabled": True,
            "emotion_enabled": True,
            "post_session_enabled": True,
            "fair_use_hours": -1,  # 不限
            "private_deployment": True,
            "sip_bridge": True
        }
    }

    # 成本参数（元/小时）
    COST_PARAMS = {
        "tencent_asr": 0.96,
        "aliyun_asr": 3.5,
        "self_hosted_asr": 0.2,
        "llm_l1": 0.02,    # LLM L1 便宜档
        "llm_l2": 0.065,   # LLM L2 均衡档
        "llm_post": 0.1,   # 会后强模型
        "server_share": 5.0,  # 单用户月摊薄
        "storage": 0.1,
        "network": 0.4
    }

    # 自建切换阈值
    SELF_HOSTED_SWITCH_USERS = 500
    SELF_HOSTED_SWITCH_CONCURRENT = 100

    def __init__(self, config=None):
        """
        初始化订阅管理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self._subscriptions: dict[str, Subscription] = {}      # subscription_id → Subscription
        self._tenant_subscription: dict[str, str] = {}          # tenant_id → subscription_id
        self._quota_usage: dict[str, QuotaUsage] = {}          # tenant_id → QuotaUsage
        self._cost_history: dict[str, list[CostBreakdown]] = {}  # tenant_id → [CostBreakdown]

    def create_subscription(
        self,
        tenant_id: str,
        user_id: str,
        tier: SubscriptionTier,
        price_rmb: int = 0,
        channel_id: str = "",
        channel_rate: float = 0.0
    ) -> Subscription:
        """
        创建订阅
        
        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID
            tier: 订阅层级
            price_rmb: 实际支付金额
            channel_id: 渠道 ID
            channel_rate: 渠道分润比例
        
        Returns:
            Subscription
        """
        now = int(time.time() * 1000)

        # 计算过期时间（1年）
        expires_at = now + (365 * 24 * 60 * 60 * 1000)

        sub = Subscription(
            tenant_id=tenant_id,
            user_id=user_id,
            tier=tier,
            status=SubscriptionStatus.ACTIVE,
            created_at=now,
            expires_at=expires_at,
            price_rmb=price_rmb or self._get_default_price(tier),
            channel_id=channel_id,
            channel_rate=channel_rate,
            payment_status="paid" if price_rmb == 0 else "pending"
        )

        self._subscriptions[sub.subscription_id] = sub
        self._tenant_subscription[tenant_id] = sub.subscription_id

        # 初始化配额
        self._init_quota(tenant_id, user_id, tier)

        return sub

    def check_access(
        self,
        tenant_id: str,
        user_id: str,
        feature: str
    ) -> dict:
        """
        检查功能访问权限
        
        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID
            feature: 功能名称（whisper / emotion / post_session / realtime）
        
        Returns:
            dict: {"allowed": bool, "reason": str, "upgrade_to": str or None}
        """
        sub = self._get_active_subscription(tenant_id)
        if not sub:
            return {"allowed": False, "reason": "无有效订阅", "upgrade_to": "L1"}

        # 检查过期
        now = int(time.time() * 1000)
        if sub.expires_at < now:
            sub.status = SubscriptionStatus.EXPIRED
            return {"allowed": False, "reason": "订阅已过期", "upgrade_to": sub.tier.value}

        # 检查功能权限
        config = self.TIER_CONFIG[sub.tier]

        feature_map = {
            "whisper": config.get("whisper_enabled", False),
            "emotion": config.get("emotion_enabled", False),
            "post_session": config.get("post_session_enabled", False),
            "realtime": True  # 所有层级都有实时
        }

        allowed = feature_map.get(feature, False)

        if not allowed:
            return {
                "allowed": False,
                "reason": f"当前层级 {sub.tier.value} 不包含 {feature}",
                "upgrade_to": "L2" if feature in ["whisper", "emotion"] else "L1"
            }

        # 检查配额（-1 表示不限时）
        quota = self._quota_usage.get(tenant_id)
        if quota:
            if quota.total_minutes_limit > 0 and quota.remaining_minutes <= 0:
                return {
                    "allowed": False,
                    "reason": "本月时长配额已用完",
                    "upgrade_to": "L2" if sub.tier == SubscriptionTier.L1_BASIC else None
                }

        return {"allowed": True, "reason": "权限正常", "upgrade_to": None}

    def record_usage(
        self,
        tenant_id: str,
        session_id: str,
        duration_seconds: int,
        asr_cost: float = 0.0,
        llm_cost: float = 0.0
    ):
        """
        记录使用量
        
        Args:
            tenant_id: 租户 ID
            session_id: 会话 ID
            duration_seconds: 会话时长（秒）
            asr_cost: ASR 成本（元）
            llm_cost: LLM 成本（元）
        """
        quota = self._quota_usage.get(tenant_id)
        if not quota:
            return

        duration_minutes = duration_seconds / 60.0

        quota.used_minutes += duration_minutes
        quota.used_sessions += 1

        # 更新剩余（-1 表示不限时）
        if quota.total_minutes_limit > 0:
            quota.remaining_minutes = max(0, quota.total_minutes_limit - quota.used_minutes)
        if quota.total_sessions_limit > 0:
            quota.remaining_sessions = max(0, quota.total_sessions_limit - quota.used_sessions)

        # 记录成本
        quota.total_cost_rmb += asr_cost + llm_cost

    def get_monthly_cost(self, tenant_id: str) -> CostBreakdown:
        """
        计算单用户月成本
        
        Returns:
            CostBreakdown
        """
        quota = self._quota_usage.get(tenant_id)
        if not quota:
            return CostBreakdown()

        # 计算各成本项
        hours = quota.used_minutes / 60

        asr_cost = hours * self.COST_PARAMS["tencent_asr"]  # 云方案
        asr_self_hosted = hours * self.COST_PARAMS["self_hosted_asr"]

        # LLM 成本（估算：1h 语音 ≈ 1万 token 转写）
        llm_l1_hours = hours * 0.3  # L1 调用占 30%
        llm_l2_hours = hours * 0.1  # L2 调用占 10%
        llm_post_hours = hours * 0.05  # 会后占 5%

        llm_cost = (llm_l1_hours * self.COST_PARAMS["llm_l1"] +
                   llm_l2_hours * self.COST_PARAMS["llm_l2"] +
                   llm_post_hours * self.COST_PARAMS["llm_post"])

        # 服务器摊薄
        server_cost = self.COST_PARAMS["server_share"]

        # 存储（Opus 约 10MB/h）
        storage_cost = hours * 10 / 1024 * self.COST_PARAMS["storage"]  # GB

        # 网络
        network_cost = hours * 10.8 / 1024 * self.COST_PARAMS["network"]  # GB

        total_cost = asr_cost + llm_cost + server_cost + storage_cost + network_cost
        total_self_hosted = asr_self_hosted + llm_cost + server_cost + storage_cost + network_cost

        return CostBreakdown(
            asr_cost=round(asr_cost, 2),
            llm_cost=round(llm_cost, 2),
            server_cost=round(server_cost, 2),
            storage_cost=round(storage_cost, 2),
            network_cost=round(network_cost, 2),
            total_cost=round(total_cost, 2),
            self_hosted_cost=round(total_self_hosted, 2),
            cloud_cost=round(total_cost, 2),
            savings=round(total_cost - total_self_hosted, 2)
        )

    def should_switch_to_self_hosted(self, total_users: int, peak_concurrent: int) -> bool:
        """
        判断是否应切换到自建 ASR
        
        Args:
            total_users: 总付费用户数
            peak_concurrent: 峰值并发数
        
        Returns:
            bool
        """
        return (total_users >= self.SELF_HOSTED_SWITCH_USERS or
                peak_concurrent >= self.SELF_HOSTED_SWITCH_CONCURRENT)

    def get_quota_summary(self, tenant_id: str) -> dict:
        """获取配额摘要"""
        quota = self._quota_usage.get(tenant_id)
        sub = self._get_active_subscription(tenant_id)

        if not quota or not sub:
            return {}

        return {
            "tier": sub.tier.value,
            "status": sub.status.value,
            "used_minutes": round(quota.used_minutes, 1),
            "total_minutes": quota.total_minutes_limit,
            "remaining_minutes": quota.remaining_minutes if quota.total_minutes_limit > 0 else -1,
            "used_sessions": quota.used_sessions,
            "whisper_enabled": quota.whisper_enabled,
            "emotion_enabled": quota.emotion_enabled,
            "total_cost_rmb": round(quota.total_cost_rmb, 2)
        }

    def get_subscription(self, tenant_id: str) -> Subscription | None:
        """获取活跃订阅"""
        return self._get_active_subscription(tenant_id)

    # ===== 内部方法 =====

    def _get_active_subscription(self, tenant_id: str) -> Subscription | None:
        """获取租户的活跃订阅"""
        sub_id = self._tenant_subscription.get(tenant_id)
        if not sub_id:
            return None

        sub = self._subscriptions.get(sub_id)
        if not sub:
            return None

        # 检查过期
        now = int(time.time() * 1000)
        if sub.expires_at < now:
            sub.status = SubscriptionStatus.EXPIRED
            return None

        return sub

    def _init_quota(self, tenant_id: str, user_id: str, tier: SubscriptionTier):
        """初始化配额"""
        config = self.TIER_CONFIG[tier]

        total_minutes = config["max_duration_minutes"]
        remaining = total_minutes if total_minutes > 0 else -1
        total_sessions = config["monthly_sessions"]
        remaining_sessions = total_sessions if total_sessions > 0 else -1

        self._quota_usage[tenant_id] = QuotaUsage(
            tenant_id=tenant_id,
            user_id=user_id,
            total_minutes_limit=total_minutes,
            used_minutes=0,
            remaining_minutes=remaining,
            total_sessions_limit=total_sessions,
            used_sessions=0,
            remaining_sessions=remaining_sessions,
            whisper_enabled=config.get("whisper_enabled", False),
            emotion_enabled=config.get("emotion_enabled", False),
            post_session_enabled=config.get("post_session_enabled", False)
        )

    def _get_default_price(self, tier: SubscriptionTier) -> int:
        """获取层级默认价格"""
        config = self.TIER_CONFIG[tier]
        return config.get("price_rmb", config.get("price_rmb_default", 0))
