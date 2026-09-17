"""
BOSS-AI-R 实时音频处理模块（P1 优先）

核心职责：
1. 音频采集：16kHz/16bit 单声道 PCM，10-20ms 帧
2. 端侧降噪：RNNoise（首选）/ DeepFilterNet / WebRTC NS
3. VAD 端点检测：WebRTC VAD / silero-VAD
4. 编码传输：Opus 24kbps，WebSocket 长连
5. 降级策略：四级自动降级（L-A/L-B/L-C/L-D）

V0.1 实现：简化版音频流水线（含模拟 ASR/提示触发）。
V0.2 扩展：集成真实 ASR SDK（腾讯云/FunASR）。
"""

import struct
import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class AudioLevel(Enum):
    """音频处理级别（降级阶梯）"""
    L_A_OPTIMAL = "L_A"      # 网络良好、算力正常
    L_B_WEAK_NETWORK = "L_B"  # 弱网/高延迟
    L_C_NOISY = "L_C"        # 嘈杂环境
    L_D_TIMEOUT = "L_D"      # LLM 超时


class NoiseSuppressor(Enum):
    """降噪算法"""
    RNNOISE = "rnnoise"
    DEEPFILTERNET = "deepfilternet"
    WEBRTC_NS = "webrtc_ns"


class VADType(Enum):
    """VAD 类型"""
    WEBRTC = "webrtc"
    SILERO = "silero"


@dataclass
class AudioFrame:
    """音频帧"""
    frame_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str = ""
    timestamp_ms: int = 0          # 相对会话开始的毫秒时间戳
    samples: bytes = b""           # PCM 16-bit 采样数据
    sample_rate: int = 16000
    channels: int = 1
    duration_ms: int = 20          # 帧时长

    @property
    def size_bytes(self) -> int:
        return len(self.samples)

    @property
    def sample_count(self) -> int:
        return len(self.samples) // 2  # 16-bit = 2 bytes/sample


@dataclass
class AudioChunk:
    """音频块（多帧累积，发送到 ASR）"""
    chunk_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str = ""
    timestamp_ms: int = 0
    frames: list[AudioFrame] = field(default_factory=list)
    duration_ms: int = 0
    is_endpoint: bool = False      # VAD 检测为端点

    @property
    def pcm_data(self) -> bytes:
        return b"".join(f.samples for f in self.frames)

    @property
    def frame_count(self) -> int:
        return len(self.frames)


@dataclass
class ASRResult:
    """ASR 结果"""
    segment_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    session_id: str = ""
    chunk_id: str = ""
    text: str = ""                 # ASR 文本
    confidence: float = 0.0        # ASR 置信度
    is_final: bool = False         # 是否为最终结果（offline 二次纠错后）
    is_endpoint: bool = False      # 是否为句末端点
    speaker_id: str = ""           # 说话人 ID
    speaker_role: str = ""         # owner / opponent / other
    start_ms: int = 0
    end_ms: int = 0
    processing_time_ms: int = 0


@dataclass
class EmotionEvent:
    """声学情绪事件"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    session_id: str = ""
    timestamp_ms: int = 0
    event_type: str = ""           # high_arousal / long_pause / speed_up / volume_up / interruption
    arousal: float = 0.5           # 唤醒度 0-1
    valence: float = 0.5           # 效价 0-1
    confidence: float = 0.0        # 置信度
    features: dict = field(default_factory=dict)  # 原始特征快照


@dataclass
class AudioSession:
    """音频会话状态"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    user_id: str = ""
    start_time_ms: int = 0
    end_time_ms: int = 0
    current_level: AudioLevel = AudioLevel.L_A_OPTIMAL
    is_recording: bool = False
    is_paused: bool = False
    is_speaking: bool = False
    silence_ms: int = 0            # 当前静音时长
    network_rtt_ms: int = 50       # 网络往返时间
    packet_loss_rate: float = 0.0
    snr_db: float = 20.0           # 信噪比
    total_frames: int = 0
    total_chunks: int = 0
    total_segments: int = 0


class AudioPipeline:
    """
    实时音频流水线
    
    完整链路：采集 → 降噪 → VAD → 编码 → wss 上行 → ASR → 分析 → 提示 → wss 下行
    """

    # 降噪配置
    NOISE_SUPPRESSORS = {
        NoiseSuppressor.RNNOISE: {"latency_ms": 10, "cpu_usage": "low", "quality": "good"},
        NoiseSuppressor.DEEPFILTERNET: {"latency_ms": 20, "cpu_usage": "medium", "quality": "excellent"},
        NoiseSuppressor.WEBRTC_NS: {"latency_ms": 5, "cpu_usage": "low", "quality": "moderate"}
    }

    # VAD 配置
    VAD_CONFIG = {
        "aggressiveness": 2,            # 0-3，越高越激进
        "min_speech_ms": 250,           # 最小语音段
        "silence_ms": 600,              # 静音判定为端点
        "energy_threshold": 40,         # 能量阈值
    }

    # 降级触发阈值
    DEGRADE_THRESHOLDS = {
        "weak_network_rtt_ms": 500,
        "weak_network_packet_loss": 0.05,
        "noisy_snr_db": 10,
        "llm_timeout_ms": 3000
    }

    def __init__(self, config=None):
        """
        初始化音频流水线
        
        Args:
            config: 配置对象
        """
        self.config = config
        self._sessions: dict[str, AudioSession] = {}
        self._chunk_buffer: dict[str, AudioChunk] = {}
        self._current_chunk_id: dict[str, str] = {}
        self._asr_callback: Callable | None = None
        self._emotion_callback: Callable | None = None

        # 初始化降噪器
        self._noise_suppressor = self._init_noise_suppressor()
        self._vad = self._init_vad()

    def create_session(
        self,
        tenant_id: str,
        user_id: str,
        platform: str = "android"
    ) -> AudioSession:
        """
        创建音频会话
        
        Args:
            tenant_id: 租户 ID
            user_id: 用户 ID
            platform: 平台（ios / android）
        
        Returns:
            AudioSession
        """
        session = AudioSession(
            tenant_id=tenant_id,
            user_id=user_id,
            start_time_ms=int(time.time() * 1000)
        )
        self._sessions[session.session_id] = session

        # 初始化当前 chunk
        chunk_id = str(uuid.uuid4())[:8]
        self._chunk_buffer[chunk_id] = AudioChunk(
            chunk_id=chunk_id,
            session_id=session.session_id,
            timestamp_ms=session.start_time_ms
        )
        self._current_chunk_id[session.session_id] = chunk_id

        return session

    def start_recording(self, session_id: str) -> bool:
        """
        开始录音
        
        Args:
            session_id: 会话 ID
        
        Returns:
            bool: 是否成功开始
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.is_recording = True
        session.is_paused = False

        return True

    def pause_recording(self, session_id: str):
        """暂停录音"""
        session = self._sessions.get(session_id)
        if session:
            session.is_paused = True

    def resume_recording(self, session_id: str):
        """恢复录音"""
        session = self._sessions.get(session_id)
        if session:
            session.is_paused = False

    def stop_recording(self, session_id: str) -> dict:
        """
        结束录音
        
        Returns:
            dict: 会话统计
        """
        session = self._sessions.get(session_id)
        if session:
            session.is_recording = False
            session.end_time_ms = int(time.time() * 1000)

            # 清理当前 chunk
            chunk_id = self._current_chunk_id.pop(session_id, None)
            if chunk_id:
                self._chunk_buffer.pop(chunk_id, None)

            return {
                "session_id": session_id,
                "duration_ms": session.end_time_ms - session.start_time_ms,
                "total_frames": session.total_frames,
                "total_chunks": session.total_chunks,
                "total_segments": session.total_segments
            }
        return {}

    def process_frame(self, session_id: str, pcm_data: bytes) -> dict | None:
        """
        处理单帧音频（核心流水线入口）
        
        Args:
            session_id: 会话 ID
            pcm_data: PCM 16-bit 采样数据
        
        Returns:
            dict: 处理结果（如果有 ASR 结果或提示事件）
        """
        session = self._sessions.get(session_id)
        if not session or not session.is_recording or session.is_paused:
            return None

        # 创建音频帧
        frame = AudioFrame(
            session_id=session_id,
            timestamp_ms=int(time.time() * 1000) - session.start_time_ms,
            samples=pcm_data
        )
        session.total_frames += 1

        # 1. 降噪
        clean_frame = self._apply_noise_suppression(frame)

        # 2. VAD 端点检测
        is_speech = self._vad_process(clean_frame)

        # 3. 累积到 chunk
        chunk_id = self._current_chunk_id.get(session_id)
        if chunk_id:
            chunk = self._chunk_buffer[chunk_id]
            chunk.frames.append(clean_frame)
            chunk.duration_ms = sum(f.duration_ms for f in chunk.frames)

            # 检查是否为端点
            if self._check_endpoint(chunk, is_speech, session):
                chunk.is_endpoint = True
                return self._process_chunk(session_id, chunk)
            else:
                # 检查 chunk 是否过长（强制切分）
                if chunk.duration_ms >= 5000:  # 5s 强制切分
                    chunk.is_endpoint = True
                    return self._process_chunk(session_id, chunk)

        return None

    def _process_chunk(self, session_id: str, chunk: AudioChunk) -> dict:
        """
        处理完整 chunk（编码 + ASR + 分析 + 提示）
        
        Args:
            session_id: 会话 ID
            chunk: 音频块
        
        Returns:
            dict: 包含 ASR 结果和提示事件
        """
        session = self._sessions[session_id]
        session.total_chunks += 1

        # 编码 Opus（模拟）
        encoded = self._encode_opus(chunk)

        # ASR 转写（模拟）
        asr_result = self._transcribe(chunk)

        # 声学情绪分析（模拟）
        emotion_event = self._analyze_emotion(chunk)

        # 更新会话状态
        session.is_speaking = asr_result.is_final if asr_result else False
        session.total_segments += 1 if asr_result else 0

        # 清理当前 chunk
        self._chunk_buffer.pop(chunk.chunk_id, None)
        new_chunk_id = str(uuid.uuid4())[:8]
        self._chunk_buffer[new_chunk_id] = AudioChunk(
            chunk_id=new_chunk_id,
            session_id=session_id,
            timestamp_ms=int(time.time() * 1000) - session.start_time_ms
        )
        self._current_chunk_id[session_id] = new_chunk_id

        return {
            "asr_result": asr_result,
            "emotion_event": emotion_event,
            "session_stats": {
                "total_frames": session.total_frames,
                "total_chunks": session.total_chunks,
                "total_segments": session.total_segments
            }
        }

    def update_network_status(
        self,
        session_id: str,
        rtt_ms: int,
        packet_loss: float,
        snr_db: float
    ):
        """
        更新网络状态，自动降级
        
        Args:
            session_id: 会话 ID
            rtt_ms: 往返时间（ms）
            packet_loss: 丢包率（0-1）
            snr_db: 信噪比（dB）
        """
        session = self._sessions.get(session_id)
        if not session:
            return

        session.network_rtt_ms = rtt_ms
        session.packet_loss_rate = packet_loss
        session.snr_db = snr_db

        # 自动降级判断
        if rtt_ms > self.DEGRADE_THRESHOLDS["weak_network_rtt_ms"] or packet_loss > self.DEGRADE_THRESHOLDS["weak_network_packet_loss"]:
            session.current_level = AudioLevel.L_B_WEAK_NETWORK
        elif snr_db < self.DEGRADE_THRESHOLDS["noisy_snr_db"]:
            session.current_level = AudioLevel.L_C_NOISY
        else:
            session.current_level = AudioLevel.L_A_OPTIMAL
        
        # PERF FIX: L_D LLM 超时由 prompt_decider 触发（通过环境变量标记）
        # 此处仅设置网络/环境降级，LLM 超时在决策器中处理

    def get_session_status(self, session_id: str) -> dict:
        """获取会话状态"""
        session = self._sessions.get(session_id)
        if not session:
            return {}

        return {
            "session_id": session_id,
            "is_recording": session.is_recording,
            "is_paused": session.is_paused,
            "current_level": session.current_level.value,
            "duration_ms": int(time.time() * 1000) - session.start_time_ms if session.is_recording else 0,
            "network_rtt_ms": session.network_rtt_ms,
            "packet_loss": session.packet_loss_rate,
            "snr_db": session.snr_db,
            "total_frames": session.total_frames,
            "total_chunks": session.total_chunks,
            "total_segments": session.total_segments
        }

    def cleanup_session(self, session_id: str):
        """清理会话数据"""
        self._sessions.pop(session_id, None)
        chunk_id = self._current_chunk_id.pop(session_id, None)
        if chunk_id:
            self._chunk_buffer.pop(chunk_id, None)

    # ===== 内部方法 =====

    def _init_noise_suppressor(self) -> NoiseSuppressor:
        """初始化降噪器（默认 RNNoise）"""
        return NoiseSuppressor.RNNOISE

    def _init_vad(self) -> VADType:
        """初始化 VAD（默认 WebRTC）"""
        return VADType.WEBRTC

    def _apply_noise_suppression(self, frame: AudioFrame) -> AudioFrame:
        """降噪处理（V0.1 模拟直通）"""
        # V0.1 不做真实降噪，保留原始数据
        # V0.2 集成 RNNoise C 库
        return frame

    def _vad_process(self, frame: AudioFrame) -> bool:
        """
        VAD 端点检测（简化版）
        
        基于能量检测：
        - 计算帧能量（RMS）
        - 高于阈值判定为语音
        - 连续静音超过阈值判定为端点
        """
        if not frame.samples:
            return False

        # 计算 RMS 能量
        samples = struct.unpack(f"<{frame.sample_count}h", frame.samples)
        energy = (sum(s * s for s in samples) / len(samples)) ** 0.5 if samples else 0

        return energy > (10 ** (self.VAD_CONFIG["energy_threshold"] / 20)) * 32768

    def _check_endpoint(self, chunk: AudioChunk, is_speech: bool, session: AudioSession) -> bool:
        """
        检查是否为句末端点
        
        条件：
        1. VAD 检测到语音结束
        2. 静音时长超过阈值（600ms）
        3. 总时长超过最小语音段（250ms）
        """
        if not is_speech:
            session.silence_ms += 20  # 假设每帧 20ms
            if session.silence_ms >= self.VAD_CONFIG["silence_ms"] and chunk.duration_ms >= self.VAD_CONFIG["min_speech_ms"]:
                return True
        else:
            session.silence_ms = 0

        return False

    def _encode_opus(self, chunk: AudioChunk) -> bytes:
        """Opus 编码（V0.1 模拟直通 PCM）"""
        # V0.1 直接返回 PCM（V0.2 集成 opus 编码）
        return chunk.pcm_data

    def _transcribe(self, chunk: AudioChunk) -> ASRResult | None:
        """
        ASR 转写（V0.1 模拟）
        
        实际应调用：
        - 腾讯云实时 ASR（云起步）
        - FunASR Paraformer-online（自建目标）
        - sherpa-onnx SenseVoice（端侧兜底）
        """
        # 模拟 ASR 结果
        import random

        # 模拟文本（Demo 用）
        demo_texts = [
            "李总，这次我们希望账期能放到 60 天。",
            "60 天太长了，我们公司一般 30 天。",
            "上次我们订的那批货，质量有点小问题啊。",
        ]

        text = random.choice(demo_texts)

        return ASRResult(
            session_id=chunk.session_id,
            chunk_id=chunk.chunk_id,
            text=text,
            confidence=random.uniform(0.85, 0.95),
            is_final=True,
            is_endpoint=chunk.is_endpoint,
            speaker_id="opponent_main",
            speaker_role="opponent",
            start_ms=chunk.timestamp_ms,
            end_ms=chunk.timestamp_ms + chunk.duration_ms,
            processing_time_ms=random.randint(200, 800)
        )

    def _analyze_emotion(self, chunk: AudioChunk) -> EmotionEvent | None:
        """
        声学情绪分析（V0.1 简化版）
        
        实际应提取：
        - F0 基频
        - 能量响度
        - 语速
        - 停顿时长
        - jitter/shimmer
        """
        import random

        # 随机生成情绪事件（Demo 用）
        if random.random() < 0.3:  # 30% 概率触发
            event_types = ["high_arousal", "long_pause", "speed_up", "volume_up"]
            return EmotionEvent(
                session_id=chunk.session_id,
                timestamp_ms=chunk.timestamp_ms,
                event_type=random.choice(event_types),
                arousal=random.uniform(0.5, 0.8),
                valence=random.uniform(0.3, 0.7),
                confidence=random.uniform(0.6, 0.9),
                features={
                    "f0_mean": random.uniform(100, 300),
                    "energy_mean": random.uniform(0.3, 0.8),
                    "speed_wpm": random.uniform(120, 200),
                    "pause_ms": random.randint(200, 1500)
                }
            )
        return None
