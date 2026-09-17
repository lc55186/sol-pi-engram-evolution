"""
BOSS-AI-R 提示决策器测试

覆盖场景：
1. L0 关键词匹配（红线词 + 数字）
2. L1 情绪事件检测
3. 去重逻辑
4. 择时延迟
5. 打断保护
6. 会话统计
"""

import os
import sys

import pytest

# 动态导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from modules.prompt_decider import (
    DeliveryChannel,
    PromptDecider,
    PromptEvent,
    PromptPriority,
    PromptType,
)


class TestPromptDecider:
    """提示决策器测试类"""

    def setup_method(self):
        """每个测试方法前初始化"""
        self.decider = PromptDecider()
        self.session_id = "test-session-001"

    def test_l0_red_keyword_match(self):
        """L0 红线词匹配测试"""
        # 账期红线词
        prompt = self.decider.decide(
            text="李总，这次我们希望账期能放到 60 天。",
            speaker="opponent",
            session_id=self.session_id,
            is_speaking=False,
            silence_ms=600,
            current_ms=1000
        )

        assert prompt is not None
        assert prompt.event_type == PromptType.KEYWORD_ALERT
        assert prompt.priority == PromptPriority.HIGH
        assert "账期" in prompt.content
        assert "60" in prompt.evidence

    def test_l0_number_match(self):
        """L0 红线词 + 数字匹配测试"""
        # 百分比数字 + 红线词
        prompt = self.decider.decide(
            text="不良率达到了 5%，这太高了。",
            speaker="opponent",
            session_id=self.session_id,
            is_speaking=False,
            silence_ms=600,
            current_ms=2000
        )

        assert prompt is not None
        assert prompt.event_type == PromptType.KEYWORD_ALERT
        # V0.2: content 包含红线词名，evidence 包含完整原文
        assert "不良率" in prompt.content or "5%" in prompt.evidence

    def test_l0_no_match_for_owner(self):
        """老板自己的话不触发提示"""
        prompt = self.decider.decide(
            text="我们的账期标准是 30 天。",
            speaker="owner",
            session_id=self.session_id,
            is_speaking=False,
            silence_ms=600,
            current_ms=3000
        )

        assert prompt is None

    def test_l1_emotion_event_high_arousal(self):
        """L1 高唤醒事件检测"""
        emotion_data = {
            "arousal": 0.85,
            "valence": 0.4,
            "confidence": 0.85,
            "event_type": "high_arousal"
        }

        prompt = self.decider.decide(
            text="这个价格绝对不能接受！",
            speaker="opponent",
            emotion=emotion_data,
            session_id=self.session_id,
            is_speaking=False,
            silence_ms=600,
            current_ms=4000
        )

        assert prompt is not None
        assert prompt.event_type == PromptType.EMOTION_SIGNAL
        assert prompt.priority == PromptPriority.MEDIUM

    def test_l1_emotion_low_confidence_silence(self):
        """L1 低置信度静默"""
        emotion_data = {
            "arousal": 0.85,
            "valence": 0.4,
            "confidence": 0.5,  # 低于阈值 0.7
            "event_type": "high_arousal"
        }

        prompt = self.decider.decide(
            text="这个价格绝对不能接受！",
            speaker="opponent",
            emotion=emotion_data,
            session_id=self.session_id,
            is_speaking=False,
            silence_ms=600,
            current_ms=5000
        )

        # 低置信度情绪不触发提示，但 L0 可能匹配
        # 这句话没有 L0 红线词，所以应该是 None
        assert prompt is None or prompt.trigger == "L0"

    def test_deduplication(self):
        """去重测试：相同内容不重复推送"""
        # 第一次
        prompt1 = self.decider.decide(
            text="我们希望账期能放到 90 天。",
            speaker="opponent",
            session_id=self.session_id,
            is_speaking=False,
            silence_ms=600,
            current_ms=6000
        )

        assert prompt1 is not None

        # 第二次（相同内容）
        prompt2 = self.decider.decide(
            text="我们希望账期能放到 90 天。",
            speaker="opponent",
            session_id=self.session_id,
            is_speaking=False,
            silence_ms=600,
            current_ms=7000
        )

        # 应该被去重（或间隔太短）
        # 由于 MIN_INTER_PROMPT_MS = 2000，这里间隔 1000ms 应该被拦截
        assert prompt2 is None

    def test_interrupt_protection(self):
        """打断保护：对方说话中不推非高优先级"""
        prompt = self.decider.decide(
            text="对方还在说话，我们等等看。",
            speaker="opponent",
            session_id=self.session_id,
            is_speaking=True,  # 对方正在说话
            silence_ms=0,
            current_ms=8000
        )

        # 没有 L0/L1 触发，返回 None
        assert prompt is None

    def test_channel_mapping_high_priority(self):
        """高优先级通道映射"""
        prompt = self.decider.decide(
            text="这是独家代理协议，必须签。",
            speaker="opponent",
            session_id=self.session_id,
            is_speaking=False,
            silence_ms=600,
            current_ms=10000
        )

        assert prompt is not None
        assert prompt.priority == PromptPriority.HIGH
        assert DeliveryChannel.VIBRATION in prompt.delivered_channels
        assert DeliveryChannel.WATCH in prompt.delivered_channels
        assert DeliveryChannel.LOCKSCREEN in prompt.delivered_channels

    def test_session_stats(self):
        """会话统计测试"""
        # 清空之前的数据
        self.decider.cleanup_session(self.session_id)
        self.session_id = "test-session-stats"

        # 触发几个提示
        self.decider.decide(
            text="账期要 90 天",
            speaker="opponent",
            session_id=self.session_id,
            is_speaking=False,
            silence_ms=600,
            current_ms=1000
        )

        self.decider.decide(
            text="还有别家在谈",
            speaker="opponent",
            session_id=self.session_id,
            is_speaking=False,
            silence_ms=600,
            current_ms=5000
        )

        stats = self.decider.get_session_stats(self.session_id)

        assert stats["total"] >= 1
        assert stats["high_priority"] >= 1

    def test_cleanup_session(self):
        """清理会话数据测试"""
        self.decider.cleanup_session(self.session_id)

        prompts = self.decider.get_session_prompts(self.session_id)
        assert prompts == []

    def test_delay_calculation(self):
        """择时延迟计算测试"""
        prompt = PromptEvent(
            session_id=self.session_id,
            event_type=PromptType.KEYWORD_ALERT,
            priority=PromptPriority.HIGH,
            content="测试",
            evidence="测试",
            trigger="L0",
            confidence=0.9,
            triggered_ms=1000
        )

        # 高优先级 → 短延迟
        delay = self.decider._calculate_delay(prompt, is_speaking=False, silence_ms=0)
        assert delay == 0  # 立即推送

        # 低优先级 → 较长延迟
        prompt.priority = PromptPriority.LOW
        delay = self.decider._calculate_delay(prompt, is_speaking=True, silence_ms=0)
        assert delay >= self.decider.COMPLEX_DELAY


# ===== 运行测试 =====
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
