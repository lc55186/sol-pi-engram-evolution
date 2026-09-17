"""
BOSS-AI-R 统一配置管理（V0.2 增强版）

支持环境变量覆盖、配置文件加载、多环境切换。
V0.2 改进：类型安全的配置访问、统一 get_config() 调用、
模块级配置注入支持。
"""

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DatabaseConfig:
    """数据库配置"""
    path: str = "evolution.db"
    backup_path: str = "./backups"
    wal_mode: bool = True
    busy_timeout: int = 5000
    foreign_keys: bool = True


@dataclass
class ASRConfig:
    """ASR 配置（双轨制：云起步 → 自建切换）"""
    # 云 ASR（V0.1 起步）
    cloud_provider: str = "tencent"  # tencent / aliyun / funasr
    cloud_app_id: str = ""
    cloud_secret_id: str = ""
    cloud_secret_key: str = ""
    cloud_price_per_hour: float = 0.96  # 元/h

    # 自建 FunASR（目标架构）
    self_hosted_url: str = "http://localhost:8000"
    self_hosted_model: str = "paraformer-online"

    # 端侧兜底
    ondevice_model: str = "SenseVoice-Small"
    ondevice_model_size: str = "int8"  # 约 229MB
    ondevice_vad: bool = True
    ondevice_punctuation: bool = True
    ondevice_itn: bool = True

    # 切换触发阈值
    switch_to_self_hosted_users: int = 500
    switch_to_self_hosted_concurrent: int = 100

    # 热词偏置
    hotwords: list = field(default_factory=list)
    hotword_weight: int = 3


@dataclass
class LLMConfig:
    """LLM 配置（分级调用）"""
    # 主备供应商
    primary_provider: str = "deepseek"  # deepseek / qwen
    fallback_provider: str = "qwen"

    # API Key
    primary_api_key: str = ""
    primary_api_base: str = "https://api.deepseek.com/v1"
    fallback_api_key: str = ""
    fallback_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # 分级模型（2026-09-18 更新：DeepSeek V4.1 Flash 全面超越 Pro，$0.15/M input）
    l1_model: str = "qwen3.8-27b"      # 轻量分类（便宜档，瑞芯微适配）
    l2_model: str = "deepseek-flash"   # 深度分析（均衡档，V4.1 Flash = 原V4 Pro路由）
    post_session_model: str = "deepseek-flash"  # 会后纪要（强模型，V4.1 Flash全面超越Pro）
    # 端侧模型（RK1860+）
    ondevice_model: str = "minicpm5-2b"  # 瑞芯微 Day-0 适配，轻量实时

    # 定价（元/百万token，2026-09-18 更新：V4.1 Flash $0.15/$0.60 per M tokens）
    l1_input_price: float = 1.0
    l1_output_price: float = 2.0
    l2_input_price: float = 1.08   # $0.15/M ≈ ¥1.08/M
    l2_output_price: float = 4.32  # $0.60/M ≈ ¥4.32/M

    # 调用参数
    l1_max_tokens: int = 200
    l2_max_tokens: int = 500
    post_session_max_tokens: int = 2000
    temperature: float = 0.3

    # 超时
    l1_timeout: float = 2.0
    l2_timeout: float = 5.0
    post_session_timeout: float = 30.0

    # 禁用境外模型
    allow_foreign_model: bool = False


@dataclass
class AudioConfig:
    """音频配置"""
    # 采集
    sample_rate: int = 16000
    bit_depth: int = 16
    channels: int = 1
    frame_duration_ms: int = 20

    # 编码
    opus_bitrate: int = 24000  # 24kbps
    opus_complexity: int = 5

    # VAD
    vad_aggressiveness: int = 2
    vad_silence_ms: int = 600  # 端点停顿判定
    vad_min_speech_ms: int = 250

    # 降噪
    noise_suppressor: str = "rnnoise"  # rnnoise / deepfilternet / webrtc
    noise_attenuation_db: float = 15.0

    # 延迟预算（ms）
    max_latency_l0: float = 2500
    max_latency_l1: float = 5000
    max_latency_l2: float = 10000


@dataclass
class EmotionConfig:
    """声学情绪配置"""
    # 维度权重
    arousal_f0_weight: float = 0.4
    arousal_energy_weight: float = 0.3
    arousal_speed_weight: float = 0.3

    valence_pitch_weight: float = 0.5
    valence_energy_weight: float = 0.3
    valence_text_weight: float = 0.2

    confidence_pause_weight: float = 0.4
    confidence_hesitation_weight: float = 0.3
    confidence_speed_weight: float = 0.3

    # 事件阈值
    high_arousal_threshold: float = 0.75
    long_pause_threshold_ms: int = 1500
    speed_change_threshold: float = 0.3
    volume_change_threshold: float = 0.25

    # 输出约束
    min_confidence: float = 0.7  # 低于此值静默
    default_enabled: bool = False  # 默认关闭
    allow_cross_session_profile: bool = False  # 严禁跨会话画像

    # 禁止输出
    forbidden_outputs: tuple = ("撒谎", "欺骗", "心虚", "测谎", "真实意图", "人品")


@dataclass
class ComplianceConfig:
    """合规配置"""
    # PIPL
    require_separate_consent: bool = True
    consent_expiry_days: int = 365
    data_retention_days: int = 90  # 默认 90 天过期
    retention_options: tuple = (30, 90, 365)

    # 声纹
    voiceprint_retention: str = "session_only"  # session_only / consent_based
    voiceprint_encryption: str = "AES-256"
    voiceprint_destroy_after_session: bool = True

    # 录音指示
    triple_indicator: bool = True
    ios_indicator_color: str = "red"
    android_indicator_type: str = "notification"

    # 权利响应
    rights_response_days: int = 15
    rights_contact_email: str = "privacy@boss-ai.com"

    # PIPIA
    pipia_required_chapters: tuple = ("声纹", "情绪", "云处理", "数据出境")
    pipia_retention_years: int = 3

    # 禁止功能
    allow_third_party_recording: bool = False  # 非参与方偷录
    allow_call_recording: bool = False  # 通话录音
    allow_lie_detection: bool = False  # 测谎


@dataclass
class BillingConfig:
    """订阅计费配置"""
    # L0 免费
    l0_monthly_sessions: int = 3
    l0_max_duration_minutes: int = 20
    l0_whisper_enabled: bool = False
    l0_emotion_enabled: bool = False

    # L1 基础
    l1_price_annual: int = 1980
    l1_price_monthly: int = 199
    l1_monthly_hours: int = 10
    l1_whisper_enabled: bool = False
    l1_emotion_enabled: bool = False

    # L2 专业
    l2_price_annual_min: int = 9800
    l2_price_annual_max: int = 15800
    l2_fair_use_hours: int = 200  # 公平使用政策
    l2_whisper_enabled: bool = True
    l2_emotion_enabled: bool = True

    # L3 陪跑
    l3_price_annual_min: int = 39800
    l3_price_annual_max: int = 69800
    l3_private_deployment: bool = True
    l3_sip_bridge: bool = True

    # 渠道分润
    channel_first_year_rate: float = 0.30
    channel_renewal_rate: float = 0.15
    channel_tiers: tuple = (0.30, 0.35, 0.40)  # 阶梯分润

    # 数智券
    digital_voucher_rate: float = 0.30
    digital_voucher_max: int = 300000
    digital_voucher_min_purchase: int = 300000


@dataclass
class NPUConfig:
    """NPU 硬件抽象配置（RK1828 / RK1860 / RK1880 兼容）
    
    支持自动探测 NPU 型号，按算力自动选择模型版本。
    切换芯片只需重新编译 RKNN 模型，代码无需修改。
    """
    # NPU 型号（auto = 启动时自动探测）
    # 注: rk1828 → rk182x（瑞芯微官方命名已更新，RK182X 系列）
    # rk3688 为旗舰 SoC，2027 年才贡献营收，暂不纳入 auto 探测
    npu_type: str = "auto"  # "rk182x" | "rk1860" | "rk3688" | "none"
    
    # 算力等级（TOPS INT8，auto 时自动填充）
    compute_tops: int = 0  # 0 = 自动探测
    
    # 模型选择映射（按 NPU 型号自动匹配）
    # 2026-09-17 更新: RK182X 已量产(数百客户/几十个行业), RK1860 研发完成即将推出
    # 瑞芯微 Day-0 适配: Qwen3.8-27B(复杂推理) + MiniCPM5-2B(轻量实时)
    model_map: dict = field(default_factory=lambda: {
        "rk182x": {
            "llm": "qwen3.8-27b-int4",       # 瑞芯微 Day-0 适配
            "asr": "minicpm5-2b-ondevice",    # 轻量级端侧 ASR 兜底
            "emotion": "acoustic-cnn-small",
        },
        "rk1860": {
            "llm": "qwen3.8-27b-int4",       # 瑞芯微 Day-0 适配，协处理器
            "asr": "minicpm5-2b-ondevice",
            "emotion": "acoustic-cnn-full",
        },
        "rk3688": {
            "llm": "qwen3.8-72b-int4",       # 旗舰 SoC，2027 营收
            "asr": "whisper-large-v3-int8",
            "emotion": "acoustic-cnn-full",
        },
    })
    
    # 能力开关（按算力自动设置）
    offline_llm: bool = False        # RK1860+ 开启
    offline_asr: bool = False        # RK1860+ 开启
    offline_emotion: bool = False    # RK1860+ 开启
    multi_role_parallel: int = 1     # RK1860+ 设为 3
    
    # 内存预算（MB，按 NPU 自动设置）
    memory_budget_mb: int = 2048     # RK1828: 2GB, RK1860: 8GB, RK1880: 16GB
    
    # 降级策略
    fallback_to_cloud: bool = True   # NPU 不足时回退云端
    min_tops_for_llm: int = 10       # 低于此算力不跑端侧 LLM
    
    def resolve_npu(self) -> str:
        """解析 NPU 型号（自动探测或返回手动设置）"""
        if self.npu_type != "auto":
            return self.npu_type
        # 尝试探测 RKNN 设备
        try:
            from pyrknn.api import RKNN
            rknn = RKNN()
            target = rknn.query(cmd='platform', rknn_version=self.npu_type)
            rknn.release()
            if '1860' in str(target):
                return "rk1860"
            elif '3688' in str(target):
                return "rk3688"
            elif '182' in str(target):
                return "rk182x"
        except Exception:
            pass
        return "none"
    
    def auto_configure(self) -> None:
        """根据 NPU 型号自动配置所有参数"""
        npu = self.resolve_npu()
        self.npu_type = npu
        
        presets = {
            "rk182x": dict(
                compute_tops=10, offline_llm=False, offline_asr=False,
                offline_emotion=False, multi_role_parallel=1,
                memory_budget_mb=2048,
            ),
            "rk1860": dict(
                compute_tops=60, offline_llm=True, offline_asr=True,
                offline_emotion=True, multi_role_parallel=3,
                memory_budget_mb=8192,
            ),
            "rk3688": dict(
                compute_tops=120, offline_llm=True, offline_asr=True,
                offline_emotion=True, multi_role_parallel=5,
                memory_budget_mb=16384,
            ),
            "none": dict(
                compute_tops=0, offline_llm=False, offline_asr=False,
                offline_emotion=False, multi_role_parallel=1,
                memory_budget_mb=0,
            ),
        }
        
        for key, value in presets.get(npu, presets["none"]).items():
            setattr(self, key, value)
    
    def get_model_name(self, task: str) -> str:
        """获取当前 NPU 对应的模型名称"""
        return self.model_map.get(self.npu_type, {}).get(task, "")


@dataclass
class SecurityConfig:
    """安全配置"""
    # JWT
    jwt_secret: str = ""  # SECURITY FIX: 生产环境必须从环境变量读取，绝不用空字符串
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24
    
    # 加密
    encryption_algorithm: str = "AES-256-GCM"
    key_derivation: str = "PBKDF2"
    kdf_iterations: int = 100000
    
    # 审计日志
    audit_log_retention_days: int = 180
    audit_log_tamper_proof: bool = True
    
    # RLS
    force_rls: bool = True
    tenant_id_required: bool = True
    
    # 出口网关
    egress_whitelist: tuple = ("*.deepseek.com", "*.aliyuncs.com", "*.weixin.qq.com")
    egress_dlp_enabled: bool = True
    
    # SECURITY FIX: 生产环境强制要求 jwt_secret
    def __post_init__(self):
        if not self.jwt_secret and os.getenv("ENV") == "production":
            raise ValueError("生产环境必须设置 JWT_SECRET 环境变量")


@dataclass
class Config:
    """总配置（V0.2 改进：类型安全 + 统一注入）"""
    env: str = "development"  # development / testing / production
    debug: bool = True
    version: str = "0.1.0"

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    asr: ASRConfig = field(default_factory=ASRConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    audio: AudioConfig = field(default_factory=AudioConfig)
    emotion: EmotionConfig = field(default_factory=EmotionConfig)
    compliance: ComplianceConfig = field(default_factory=ComplianceConfig)
    billing: BillingConfig = field(default_factory=BillingConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    npu: NPUConfig = field(default_factory=NPUConfig)

    # 项目根目录
    project_root: Path = Path(__file__).resolve().parent

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        config = cls()

        # 数据库
        if db_path := os.getenv("DATABASE_PATH"):
            config.database.path = db_path

        # ASR
        if asr_provider := os.getenv("ASR_PROVIDER"):
            config.asr.cloud_provider = asr_provider
        if asr_secret := os.getenv("ASR_SECRET_KEY"):
            config.asr.cloud_secret_key = asr_secret

        # LLM
        if llm_key := os.getenv("LLM_API_KEY"):
            config.llm.primary_api_key = llm_key

        # JWT
        if jwt_secret := os.getenv("JWT_SECRET"):
            config.security.jwt_secret = jwt_secret

        # 环境
        if env := os.getenv("ENV"):
            config.env = env
            config.debug = env == "development"

        return config

    def get_asr_cost_per_user_monthly(self, hours: float = 60) -> float:
        """计算单用户月 ASR 成本"""
        if self.asr.cloud_provider == "funasr":
            return hours * 0.2  # 自建约 0.2 元/h
        elif self.asr.cloud_provider == "tencent":
            return hours * self.asr.cloud_price_per_hour
        else:
            return hours * 3.5  # 阿里约 3.5 元/h

    def to_dict(self) -> dict[str, Any]:
        """转换为字典（用于模块间传递）"""
        from dataclasses import asdict
        return asdict(self)


# 线程安全的配置单例
_config: Config | None = None
_config_lock = threading.Lock()


def get_config() -> Config:
    """获取全局配置单例（线程安全）"""
    global _config
    if _config is None:
        with _config_lock:
            if _config is None:
                _config = Config.from_env()
    return _config


def set_config(config: Config) -> None:
    """设置全局配置（主要用于测试注入）"""
    global _config
    with _config_lock:
        _config = config


def reset_config() -> None:
    """重置配置单例（测试用）"""
    global _config
    with _config_lock:
        _config = None
