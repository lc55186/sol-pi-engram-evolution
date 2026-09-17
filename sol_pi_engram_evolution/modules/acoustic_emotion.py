"""
BOSS-AI-R 声学情绪分析模块（P2 优先）

核心职责：
1. 声学特征提取：F0 基频、能量、语速、停顿、jitter/shimmer
2. 情绪维度计算：唤醒度(Arousal)、效价(Valence)、确定度(Confidence)
3. 事件检测：高唤醒、长停顿、语速突变、音量突变、被打断
4. 输出约束：仅描述声学现象，严禁测谎/读心

V0.1 实现：基于规则的特征提取 + 简单分类。
V0.2 扩展：集成 SpeechBrain/Wav2Vec2 分类头。
"""

import struct
import uuid
from dataclasses import dataclass, field


@dataclass
class AcousticFeatures:
    """声学特征向量"""
    f0_mean: float = 0.0           # 基频均值 (Hz)
    f0_std: float = 0.0            # 基频标准差
    f0_range: float = 0.0          # 基频范围
    energy_mean: float = 0.0       # 能量均值 (RMS)
    energy_std: float = 0.0        # 能量标准差
    energy_range: float = 0.0      # 能量范围
    speed_wpm: float = 0.0         # 语速 (字/分钟)
    pause_ms: int = 0              # 停顿时长 (ms)
    pause_count: int = 0           # 停顿次数
    jitter: float = 0.0            # 基频微扰
    shimmer: float = 0.0           # 振幅微扰
    hnr_db: float = 0.0            # 谐噪比 (dB)
    speaking_ratio: float = 0.0    # 语音占比 (0-1)

    def to_dict(self) -> dict:
        return {
            "f0_mean": self.f0_mean,
            "f0_std": self.f0_std,
            "energy_mean": self.energy_mean,
            "energy_std": self.energy_std,
            "speed_wpm": self.speed_wpm,
            "pause_ms": self.pause_ms,
            "jitter": self.jitter,
            "shimmer": self.shimmer,
            "hnr_db": self.hnr_db,
            "speaking_ratio": self.speaking_ratio
        }


@dataclass
class EmotionState:
    """情绪状态（三维）"""
    arousal: float = 0.5           # 唤醒度 (0-1): 激动 vs 平静
    valence: float = 0.5           # 效价 (0-1): 积极 vs 消极
    confidence: float = 0.5        # 确定度 (0-1): 笃定 vs 犹豫
    timestamp_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "arousal": round(self.arousal, 3),
            "valence": round(self.valence, 3),
            "confidence": round(self.confidence, 3)
        }


@dataclass
class EmotionEvent:
    """情绪事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str = ""
    timestamp_ms: int = 0
    event_type: str = ""           # high_arousal / long_pause / speed_up / volume_up / interruption
    intensity: float = 0.0         # 强度 0-1
    confidence: float = 0.0        # 置信度 0-1
    description: str = ""          # 人类可读描述
    features: dict = field(default_factory=dict)  # 触发时的特征快照


class AcousticEmotionAnalyzer:
    """
    声学情绪分析器
    
    输入：PCM 音频帧
    输出：三维情绪状态 + 离散情绪事件
    
    约束：
    - 仅输出声学现象（语速加快/音量升高/长停顿/语调上扬/被打断）
    - 严禁输出"撒谎/心虚/测谎/真实意图"
    - 默认关闭，用户主动开启
    - 不建跨会话情绪画像
    """

    # 事件类型定义（仅声学现象）
    EVENT_TYPES = {
        "high_arousal": "情绪激动",
        "long_pause": "长停顿（犹豫）",
        "speed_up": "语速加快",
        "speed_down": "语速放慢",
        "volume_up": "音量升高",
        "volume_down": "音量降低",
        "pitch_up": "语调上扬",
        "pitch_down": "语调下沉",
        "interruption": "被打断",
        "hesitation": "犹豫（支吾）"
    }

    # 禁止输出（合规红线）
    FORBIDDEN_OUTPUTS = [
        "撒谎", "欺骗", "心虚", "测谎", "真实意图",
        "人品", "性格", "内心", "想法", "动机"
    ]

    # 阈值配置
    THRESHOLDS = {
        "high_arousal": 0.75,
        "low_arousal": 0.25,
        "long_pause_ms": 1500,
        "speed_change_ratio": 0.3,
        "volume_change_ratio": 0.25,
        "pitch_change_ratio": 0.2,
        "min_confidence": 0.6
    }

    def __init__(self, config=None):
        """
        初始化分析器
        
        Args:
            config: 配置对象
        """
        self.config = config
        self._session_history: dict[str, list[EmotionState]] = {}
        self._session_baseline: dict[str, AcousticFeatures] = {}
        self._enabled: dict[str, bool] = {}  # session_id → enabled

    def enable(self, session_id: str):
        """启用情绪分析（用户主动开启）"""
        self._enabled[session_id] = True

    def disable(self, session_id: str):
        """关闭情绪分析"""
        self._enabled[session_id] = False

    def is_enabled(self, session_id: str) -> bool:
        """检查是否启用"""
        return self._enabled.get(session_id, False)

    def analyze_frame(
        self,
        session_id: str,
        pcm_data: bytes,
        sample_rate: int = 16000,
        timestamp_ms: int = 0
    ) -> dict | None:
        """
        分析单帧音频
        
        Args:
            session_id: 会话 ID
            pcm_data: PCM 16-bit 采样数据
            sample_rate: 采样率
            timestamp_ms: 时间戳
        
        Returns:
            dict: {"state": EmotionState, "event": EmotionEvent or None}
        """
        if not self.is_enabled(session_id):
            return None

        if not pcm_data:
            return None

        # 1. 提取声学特征
        features = self._extract_features(pcm_data, sample_rate)

        # 2. 计算情绪维度
        state = self._compute_emotion_state(features)
        state.timestamp_ms = timestamp_ms

        # 3. 检测情绪事件
        event = self._detect_event(session_id, state, features, timestamp_ms)
        
        # SECURITY FIX: 输出过滤 — 确保不包含禁止词汇（测谎/读心/意图等）
        if event:
            event.description = self._filter_forbidden_outputs(event.description)
        
        # 4. 记录历史
        if session_id not in self._session_history:
            self._session_history[session_id] = []
        self._session_history[session_id].append(state)
        
        # 保持历史长度合理（最近 100 个状态）
        if len(self._session_history[session_id]) > 100:
            self._session_history[session_id] = self._session_history[session_id][-100:]
        
        return {
            "state": state,
            "event": event,
            "features": features.to_dict()
        }

    def _filter_forbidden_outputs(self, text: str) -> str:
        """
        过滤禁止输出（合规红线）
        
        禁止的词汇包括：撒谎、欺骗、心虚、测谎、真实意图、人品、性格、内心、想法、动机
        
        这是合规硬要求，不是软建议：
        - 不得暗示对方在说谎
        - 不得推断对方人品或性格
        - 不得猜测"真实意图"
        - 仅描述可观察的声学现象
        """
        if not text:
            return text
        
        for forbidden in self.FORBIDDEN_OUTPUTS:
            if forbidden in text:
                # 替换为合规描述
                text = text.replace(forbidden, "[行为观察]")
                # 记录告警（不暴露原始文本）
                import logging
                logger = logging.getLogger("compliance")
                logger.warning("情绪分析触发禁止输出过滤: 已替换敏感词")
                break
        
        return text

    def get_session_trend(self, session_id: str) -> dict | None:
        """
        获取会话情绪趋势
        
        Returns:
            dict: 情绪变化趋势统计
        """
        history = self._session_history.get(session_id, [])
        if not history:
            return None

        arousal_values = [s.arousal for s in history]
        valence_values = [s.valence for s in history]
        confidence_values = [s.confidence for s in history]

        return {
            "arousal_trend": {
                "mean": sum(arousal_values) / len(arousal_values),
                "max": max(arousal_values),
                "min": min(arousal_values),
                "trend": "rising" if arousal_values[-1] > arousal_values[0] else "falling"
            },
            "valence_trend": {
                "mean": sum(valence_values) / len(valence_values),
                "max": max(valence_values),
                "min": min(valence_values),
                "trend": "rising" if valence_values[-1] > valence_values[0] else "falling"
            },
            "confidence_trend": {
                "mean": sum(confidence_values) / len(confidence_values),
                "max": max(confidence_values),
                "min": min(confidence_values),
                "trend": "rising" if confidence_values[-1] > confidence_values[0] else "falling"
            },
            "sample_count": len(history)
        }

    def cleanup_session(self, session_id: str):
        """清理会话数据（合规：不保留跨会话数据）"""
        self._session_history.pop(session_id, None)
        self._session_baseline.pop(session_id, None)
        self._enabled.pop(session_id, None)

    # ===== 内部方法 =====

    def _extract_features(self, pcm_data: bytes, sample_rate: int) -> AcousticFeatures:
        """
        提取声学特征
        
        V0.1 实现：基于时域分析的简化特征。
        V0.2 扩展：集成 librosa/praat 进行更精确分析。
        """
        # 解析 PCM 数据
        sample_count = len(pcm_data) // 2
        if sample_count == 0:
            return AcousticFeatures()

        samples = struct.unpack(f"<{sample_count}h", pcm_data)

        # 1. 能量 (RMS)
        energy = (sum(s * s for s in samples) / sample_count) ** 0.5 if samples else 0
        energy_normalized = energy / 32768.0  # 归一化到 0-1

        # 2. 基频 F0（简化：使用自相关法）
        f0 = self._estimate_f0(samples, sample_rate)

        # 3. 停顿检测（基于能量）
        frame_size = int(sample_rate * 0.02)  # 20ms 帧
        pauses = 0
        pause_duration_ms = 0
        is_silence = False

        for i in range(0, sample_count - frame_size, frame_size):
            frame = samples[i:i + frame_size]
            frame_energy = (sum(s * s for s in frame) / len(frame)) ** 0.5 if frame else 0

            if frame_energy < 500:  # 静音阈值
                if not is_silence:
                    pauses += 1
                    is_silence = True
                pause_duration_ms += 20
            else:
                is_silence = False

        # 4. 语音占比
        speaking_frames = sum(1 for i in range(0, sample_count - frame_size, frame_size)
                            if (sum(s * s for s in samples[i:i + frame_size]) / frame_size) ** 0.5 >= 500)
        total_frames = max(1, sample_count // frame_size)
        speaking_ratio = speaking_frames / total_frames

        # 5. 语速（简化：基于能量变化频率）
        speed_wpm = self._estimate_speed(samples, sample_rate, speaking_ratio)

        return AcousticFeatures(
            f0_mean=f0,
            f0_std=0.0,  # V0.1 简化
            energy_mean=energy_normalized,
            energy_std=0.0,
            speed_wpm=speed_wpm,
            pause_ms=pause_duration_ms,
            pause_count=pauses,
            jitter=0.0,  # V0.1 简化
            shimmer=0.0,
            hnr_db=0.0,
            speaking_ratio=speaking_ratio
        )

    def _estimate_f0(self, samples: tuple, sample_rate: int) -> float:
        """
        基频估计（自相关法简化版）
        
        实际 V0.2 应使用：
        - YIN 算法
        - CREPE 深度学习模型
        - Praat 精确分析
        """
        if not samples:
            return 0.0

        # 简化：使用能量加权平均频率
        # 实际应计算自相关函数并寻找峰值
        sample_count = len(samples)
        if sample_count < 2:
            return 0.0

        # 计算过零率（粗略估计）
        zero_crossings = sum(1 for i in range(1, sample_count) if (samples[i] >= 0) != (samples[i-1] >= 0))
        zcr = zero_crossings / sample_count

        # 基频 ≈ 采样率 × ZCR / 2
        f0 = sample_rate * zcr / 2

        # 限制在合理范围 (80-400 Hz)
        return max(80, min(400, f0))

    def _estimate_speed(self, samples: tuple, sample_rate: int, speaking_ratio: float) -> float:
        """
        语速估计（字/分钟）
        
        简化版：基于能量包络的变化频率。
        实际 V0.2 应使用 ASR 结果 + 时间戳精确计算。
        """
        if speaking_ratio < 0.1:
            return 0.0

        # 假设平均语速 150 字/分钟，根据语音占比调整
        base_speed = 150
        adjusted_speed = base_speed * speaking_ratio

        return max(80, min(250, adjusted_speed))

    def _compute_emotion_state(self, features: AcousticFeatures) -> EmotionState:
        """
        计算三维情绪状态
        
        基于声学特征映射到情绪维度：
        - 唤醒度：F0 + 能量 + 语速
        - 效价：F0 变化 + 能量分布
        - 确定度：停顿 + 语速稳定性
        """
        # 唤醒度 (Arousal)
        # 高 F0 + 高能量 + 快语速 → 高唤醒
        f0_norm = min(1.0, features.f0_mean / 300)  # 300Hz 为参考
        energy_norm = features.energy_mean
        speed_norm = min(1.0, features.speed_wpm / 200)

        arousal = (
            f0_norm * self.config.emotion.arousal_f0_weight +
            energy_norm * self.config.emotion.arousal_energy_weight +
            speed_norm * self.config.emotion.arousal_speed_weight
        ) if self.config else (f0_norm * 0.4 + energy_norm * 0.3 + speed_norm * 0.3)

        # 效价 (Valence)
        # 语调上扬 + 中等能量 → 积极
        # 语调下沉 + 低能量 → 消极
        pitch_valence = 0.5 + (features.f0_mean - 200) / 400  # 简化
        energy_valence = 0.5 + (features.energy_mean - 0.3) * 0.5

        valence = pitch_valence * 0.5 + energy_valence * 0.3 + 0.5 * 0.2
        valence = max(0, min(1, valence))

        # 确定度 (Confidence)
        # 少停顿 + 稳定语速 → 高确定度
        pause_penalty = min(0.3, features.pause_ms / 5000)
        speed_stability = 0.7 if 100 < features.speed_wpm < 180 else 0.4

        confidence = speed_stability * 0.4 + (1 - pause_penalty) * 0.3 + 0.6 * 0.3
        confidence = max(0, min(1, confidence))

        return EmotionState(
            arousal=round(max(0, min(1, arousal)), 3),
            valence=round(valence, 3),
            confidence=round(confidence, 3)
        )

    def _detect_event(
        self,
        session_id: str,
        state: EmotionState,
        features: AcousticFeatures,
        timestamp_ms: int
    ) -> EmotionEvent | None:
        """
        检测情绪事件
        
        仅检测高置信度的声学现象，低置信度静默。
        """
        # 高唤醒检测
        if state.arousal > self.THRESHOLDS["high_arousal"]:
            return EmotionEvent(
                session_id=session_id,
                timestamp_ms=timestamp_ms,
                event_type="high_arousal",
                intensity=state.arousal,
                confidence=state.arousal,
                description="对方情绪升高（语速加快/音量升高）",
                features=features.to_dict()
            )

        # 长停顿检测
        if features.pause_ms > self.THRESHOLDS["long_pause_ms"]:
            return EmotionEvent(
                session_id=session_id,
                timestamp_ms=timestamp_ms,
                event_type="long_pause",
                intensity=min(1.0, features.pause_ms / 3000),
                confidence=0.8,
                description="对方长停顿（可能在犹豫/思考）",
                features=features.to_dict()
            )

        # 语速突变检测（需要历史数据）
        history = self._session_history.get(session_id, [])
        if len(history) >= 3:
            recent_speed = features.speed_wpm
            avg_speed = sum(s.arousal for s in history[-3:]) / 3 * 200  # 简化
            if avg_speed > 0 and abs(recent_speed - avg_speed) / avg_speed > self.THRESHOLDS["speed_change_ratio"]:
                event_type = "speed_up" if recent_speed > avg_speed else "speed_down"
                return EmotionEvent(
                    session_id=session_id,
                    timestamp_ms=timestamp_ms,
                    event_type=event_type,
                    intensity=min(1.0, abs(recent_speed - avg_speed) / avg_speed),
                    confidence=0.7,
                    description=f"对方语速{'加快' if event_type == 'speed_up' else '放慢'}",
                    features=features.to_dict()
                )

        return None
