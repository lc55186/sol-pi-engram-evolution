"""
BOSS-AI-R 提示决策器模块（P0 优先）

核心职责：
1. 提示去重：相似度 >0.85 合并，避免重复打扰
2. 分级：L0(高)/L1(中)/L2(低) 三级优先级
3. 择时：检测对方停顿点（VAD 端点后 500ms），排队推送
4. 打断保护：对方说话中不推复杂建议

V0.1 实现：基于规则的提示生成 + 简单择时策略。
V0.2 扩展：引入更复杂的择时模型（考虑话题转换、对方情绪等）。
"""

import hashlib
import uuid
from dataclasses import dataclass, field
from enum import Enum


class PromptType(Enum):
    """提示类型"""
    KEYWORD_ALERT = "keyword_alert"          # L0: 关键词/数字/红线
    EMOTION_SIGNAL = "emotion_signal"        # L1: 情绪变化/态度
    RISK = "risk"                            # L2: 风险推理
    OPPORTUNITY = "opportunity"              # L2: 商机识别
    INTERJECTION_SUGGEST = "interjection_suggest"  # L2: 插话建议
    PERIODIC_SUMMARY = "periodic_summary"    # 定频摘要（120s）


class PromptPriority(Enum):
    """提示优先级"""
    HIGH = "high"      # P0: 风险预警
    MEDIUM = "medium"  # P1: 商机/情绪
    LOW = "low"        # P2: 一般信息


class DeliveryChannel(Enum):
    """推送通道"""
    VIBRATION = "vibration"    # 手机震动
    WATCH = "watch"            # 智能手表
    TTS = "tts"                # 耳机 TTS
    LOCKSCREEN = "lockscreen"  # 锁屏/悬浮窗


@dataclass
class PromptEvent:
    """提示事件数据结构"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    event_type: PromptType = PromptType.KEYWORD_ALERT
    priority: PromptPriority = PromptPriority.MEDIUM
    content: str = ""              # 提示文案（≤25字）
    evidence: str = ""             # 触发依据（原话片段，强制非空）
    trigger: str = "L0"            # L0/L1/L2
    confidence: float = 0.0        # 置信度 0-1
    delivered_channels: list[DeliveryChannel] = field(default_factory=list)
    triggered_ms: int = 0          # 生成时间戳
    delivered_ms: int = 0          # 实际送达时间戳
    feedback: str = ""             # 用户反馈：lift_watch/adopted/ignored/false_positive
    fingerprint: str = ""          # 去重指纹

    def __post_init__(self):
        """生成去重指纹 (SHA-256) — PERF FIX: 包含 evidence 避免错误去重"""
        if not self.fingerprint:
            # V0.2: fingerprint 包含 evidence 摘要，避免相同红线词不同数值被错误去重
            evidence_prefix = self.evidence[:30] if self.evidence else ""
            raw = f"{self.session_id}:{self.event_type.value}:{self.content}:{evidence_prefix}"
            self.fingerprint = hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class PromptDecision:
    """提示决策结果"""
    should_deliver: bool = True
    channel: DeliveryChannel = DeliveryChannel.VIBRATION
    delay_ms: int = 0              # 延迟推送时间（择时）
    reason: str = ""               # 决策原因（用于调试）


class PromptDecider:
    """
    提示决策器
    
    根据当前对话状态、声学事件、文本分析结果，决定：
    1. 是否生成提示
    2. 以何种优先级
    3. 通过何种通道
    4. 何时推送（择时）
    """

    # 优先级 → 通道映射
    PRIORITY_CHANNELS = {
        PromptPriority.HIGH: [DeliveryChannel.VIBRATION, DeliveryChannel.WATCH, DeliveryChannel.LOCKSCREEN],
        PromptPriority.MEDIUM: [DeliveryChannel.WATCH, DeliveryChannel.LOCKSCREEN],
        PromptPriority.LOW: [DeliveryChannel.LOCKSCREEN]
    }

    # 延迟策略（ms）
    IMMEDIATE_DELAY = 0           # L0 关键词预警立即推
    EMOTION_DELAY = 500           # L1 情绪等 500ms（等停顿）
    COMPLEX_DELAY = 1000          # L2 复杂建议等 1s（等说话窗口）
    MAX_DELAY = 3000              # 最大延迟 3s，超时丢弃

    # 择时窗口
    MIN_INTER_PROMPT_MS = 2000    # 两次提示最小间隔
    SILENCE_BEFORE_PROMPT_MS = 300  # 需要前方有 300ms 静音

    def __init__(self, config=None):
        """
        初始化决策器
        
        Args:
            config: 配置对象（可选）
        """
        self.config = config
        self._session_prompts: dict[str, list[PromptEvent]] = {}
        self._session_fingerprints: dict[str, set] = {}
        self._session_last_prompt_time: dict[str, int] = {}

    def decide(
        self,
        text: str,
        speaker: str,
        emotion: dict | None = None,
        session_id: str = "",
        is_speaking: bool = False,
        silence_ms: int = 0,
        current_ms: int = 0,
        **kwargs
    ) -> PromptEvent | None:
        """
        决策入口：根据当前输入决定是否生成提示
        
        Args:
            text: 当前 ASR 文本片段
            speaker: 说话人标识（owner/opponent/other）
            emotion: 声学情绪数据（可选）
            session_id: 会话 ID
            is_speaking: 当前是否有人在说话
            silence_ms: 当前静音时长（ms）
            current_ms: 当前时间戳（ms）
        
        Returns:
            PromptEvent 或 None（不推送）
        """
        # 1. L0 关键词匹配
        prompt = self._check_keyword_alert(text, speaker, session_id, current_ms)
        if prompt:
            return self._apply_decision(prompt, is_speaking, silence_ms, current_ms)

        # 2. L1 情绪事件
        if emotion:
            prompt = self._check_emotion_signal(emotion, speaker, session_id, current_ms)
            if prompt:
                return self._apply_decision(prompt, is_speaking, silence_ms, current_ms)

        # 3. 不需要生成提示
        return None

    def _check_keyword_alert(
        self,
        text: str,
        speaker: str,
        session_id: str,
        current_ms: int
    ) -> PromptEvent | None:
        """
        L0 关键词/数字/红线匹配
        
        匹配规则：
        - 金额数字（如"50万"、"3.5%"）
        - 红线词（如"账期"、"独家"、"担保"、"违约"）
        - 质量词（如"不良率"、"扣款"、"问题"）
        - 场景词（如"回去商量"、"研究下"、"考虑考虑"）
        """
        if speaker == "owner":
            return None  # 不分析老板自己的话

        # 红线关键词库（按行业可扩展）
        RED_KEYWORDS = [
            "账期", "独家", "排他", "担保", "违约", "诉讼", "仲裁",
            "质量扣款", "不良率", "违约责任", "赔偿责任", "无限连带",
            "回去商量", "研究下", "考虑考虑", "再评估", "汇报领导",
            "还有一家在谈", "比价", "别家", "竞争对手"
        ]

        # 数字模式（金额/百分比/天数）
        import re
        has_number = bool(re.search(r'\d+[\.\d]*[%％万千百十]', text))

        # 红线词检测
        matched_red = [kw for kw in RED_KEYWORDS if kw in text]

        if matched_red or has_number:
            # 构建提示
            if matched_red:
                content = f"⚠️ 红线词: {matched_red[0]}"
                evidence = text[:50]
            else:
                # 提取数字
                numbers = re.findall(r'\d+[\.\d]*[%％万千百十]', text)
                content = f"💡 数字: {numbers[0]}" if numbers else "⚠️ 关键信息"
                evidence = text[:50]

            return PromptEvent(
                session_id=session_id,
                event_type=PromptType.KEYWORD_ALERT,
                priority=PromptPriority.HIGH if matched_red else PromptPriority.MEDIUM,
                content=content[:25],  # 限制25字
                evidence=evidence,
                trigger="L0",
                confidence=0.9 if matched_red else 0.7,
                triggered_ms=current_ms
            )

        return None

    def _check_emotion_signal(
        self,
        emotion: dict,
        speaker: str,
        session_id: str,
        current_ms: int
    ) -> PromptEvent | None:
        """
        L1 声学情绪事件检测
        
        仅检测高置信事件：
        - 高唤醒（arousal > 0.75）
        - 长停顿（pause > 1500ms）
        - 语速突变（speed_change > 0.3）
        - 被打断（interruption detected）
        """
        if speaker == "owner":
            return None

        arousal = emotion.get("arousal", 0.5)
        event_type = emotion.get("event_type", "")
        confidence = emotion.get("confidence", 0.0)

        # 置信度阈值
        if confidence < 0.7:
            return None

        # 事件映射
        EVENT_MAP = {
            "high_arousal": ("⚠️ 对方情绪升高", PromptPriority.MEDIUM),
            "long_pause": ("⏸️ 对方长停顿（犹豫）", PromptPriority.LOW),
            "speed_up": ("⚡ 对方语速加快", PromptPriority.LOW),
            "interruption": ("🔇 对方被打断", PromptPriority.MEDIUM),
        }

        if event_type in EVENT_MAP:
            content, priority = EVENT_MAP[event_type]
            return PromptEvent(
                session_id=session_id,
                event_type=PromptType.EMOTION_SIGNAL,
                priority=priority,
                content=content,
                evidence=f"arousal={arousal:.2f}",
                trigger="L1",
                confidence=confidence,
                triggered_ms=current_ms
            )

        return None

    def _apply_decision(
        self,
        prompt: PromptEvent,
        is_speaking: bool,
        silence_ms: int,
        current_ms: int
    ) -> PromptEvent | None:
        """
        应用决策规则：择时、去重、打断保护
        
        Args:
            prompt: 待推送的提示事件
            is_speaking: 当前是否有人在说话
            silence_ms: 当前静音时长
            current_ms: 当前时间戳
        """
        session_id = prompt.session_id

        # 1. 去重检查
        if self._is_duplicate(session_id, prompt):
            return None

        # 2. 择时决策
        delay = self._calculate_delay(prompt, is_speaking, silence_ms)

        # 3. 打断保护：对方正在说话 + 非高风险 → 延迟或丢弃
        if is_speaking and prompt.priority != PromptPriority.HIGH:
            if delay > self.MAX_DELAY:
                return None  # 超时丢弃，不做"马后炮"
            prompt.delay_ms = delay



        # 5. 记录状态
        self._record_prompt(session_id, prompt, current_ms)

        # 6. 确定通道
        prompt.delivered_channels = self.PRIORITY_CHANNELS[prompt.priority]

        return prompt

    def _is_duplicate(self, session_id: str, prompt: PromptEvent) -> bool:
        """去重：检查是否重复"""
        fingerprints = self._session_fingerprints.get(session_id, set())
        if prompt.fingerprint in fingerprints:
            return True
        return False

    def _calculate_delay(
        self,
        prompt: PromptEvent,
        is_speaking: bool,
        silence_ms: int
    ) -> int:
        """
        择时策略：决定延迟多久推送
        
        策略：
        - 高优先级（L0 风险）：立即或等短暂停顿（100ms）
        - 中优先级（L1 情绪）：等对方停顿 500ms 后
        - 低优先级（L2 分析）：等对方说完 + 1000ms 说话窗口
        """
        if prompt.priority == PromptPriority.HIGH:
            return self.IMMEDIATE_DELAY if not is_speaking else 100
        elif prompt.priority == PromptPriority.MEDIUM:
            return max(0, self.EMOTION_DELAY - silence_ms)
        else:
            return max(0, self.COMPLEX_DELAY - silence_ms)

    def _record_prompt(self, session_id: str, prompt: PromptEvent, current_ms: int):
        """记录提示状态（用于去重和间隔控制）"""
        # 添加到会话提示列表
        if session_id not in self._session_prompts:
            self._session_prompts[session_id] = []
        self._session_prompts[session_id].append(prompt)

        # 记录指纹
        if session_id not in self._session_fingerprints:
            self._session_fingerprints[session_id] = set()
        self._session_fingerprints[session_id].add(prompt.fingerprint)

        # 更新时间
        self._session_last_prompt_time[session_id] = current_ms

    def get_session_prompts(self, session_id: str) -> list[PromptEvent]:
        """获取会话的所有提示"""
        return self._session_prompts.get(session_id, [])

    def get_session_stats(self, session_id: str) -> dict:
        """获取会话提示统计"""
        prompts = self.get_session_prompts(session_id)
        return {
            "total": len(prompts),
            "high_priority": sum(1 for p in prompts if p.priority == PromptPriority.HIGH),
            "medium_priority": sum(1 for p in prompts if p.priority == PromptPriority.MEDIUM),
            "low_priority": sum(1 for p in prompts if p.priority == PromptPriority.LOW),
            "avg_confidence": sum(p.confidence for p in prompts) / len(prompts) if prompts else 0,
            "adopted": sum(1 for p in prompts if p.feedback == "adopted"),
            "ignored": sum(1 for p in prompts if p.feedback == "ignored"),
        }

    def cleanup_session(self, session_id: str):
        """清理会话数据（合规：会话结束后清除）"""
        self._session_prompts.pop(session_id, None)
        self._session_fingerprints.pop(session_id, None)
        self._session_last_prompt_time.pop(session_id, None)
