"""
BOSS-AI-R 模块包
"""

from modules.acoustic_emotion import (
    AcousticEmotionAnalyzer,
    AcousticFeatures,
    EmotionState,
)
from modules.billing import (
    CostBreakdown,
    QuotaUsage,
    Subscription,
    SubscriptionManager,
    SubscriptionStatus,
    SubscriptionTier,
)
from modules.compliance import (
    ComplianceEngine,
    ConsentRecord,
    ConsentStatus,
    ConsentType,
    PIPIAReport,
    RecordingIndicator,
    RightsRequest,
    RightsRequestType,
)
from modules.prompt_decider import (
    DeliveryChannel,
    PromptDecider,
    PromptDecision,
    PromptEvent,
    PromptPriority,
    PromptType,
)
from modules.realtime_audio import (
    ASRResult,
    AudioChunk,
    AudioFrame,
    AudioLevel,
    AudioPipeline,
    AudioSession,
    EmotionEvent,
)
