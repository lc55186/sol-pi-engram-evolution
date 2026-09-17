# 老板口袋军师·实时谈判版 深度分析与 SoL-Pi 融合报告

> 分析日期：2026-09-16
> 基准文档：老板口袋军师·实时谈判版 —— 全新产品方案主文档（统一版 V2.0）
> 对照系统：SoL-Pi × DeepSeek Engram 融合进化系统（阶段 0~5 + Pipeline 全链路落地）

---

## 一、产品架构深度分析

### 1.1 核心架构：「第六感 + 大脑」双模协同

方案提出了**实时副驾（第六感）**与**经营决策外脑（大脑）**的双模架构：

| 模块 | 功能 | 数据流向 | 价值定位 |
|------|------|----------|----------|
| 实时副驾 | 现场感知→即时提示 | 音频流→边缘处理→震动/耳语 | 谈判现场"救命"级辅助 |
| 经营外脑 | 离线分析→经营决策 | 结构化数据→日/周/月报 | 日常管理"外脑"支撑 |
| 融合闭环 | 现场数据↔后台数据 | 商机/待办/风险双向写入 | 差异化护城河 |

**对 SoL-Pi 的启示**：SoL-Pi 的核心是效率机制，但该方案提出的"实时感知→即时反馈→后台沉淀→反哺实时"闭环，完美补充了 SoL-Pi 在**时间维度**上的缺失——从异步处理升级为实时+异步双轨。

### 1.2 实时音频链路的九段架构

该方案将实时链路拆解为 9 个可执行段：

```
采集(10-20ms帧) → AEC/NS/AGC降噪(10ms级) → VAD端点检测 → 流式ASR(分块,2pass)
  → 增量文本(带时间戳) ┬→ 说话人分离/声纹聚类(滑窗,并行)
                       ├→ 声学情绪/语调(帧级,并行)
                       └→ 流式LLM三级触发分析(L0规则/L1轻分类/L2深分析)
                             ↓
                   提示决策器(去重/分级/择时,排队到对方停顿点)
                             ↓
                   耳语反馈(手表震动→抬腕小字→耳机极短TTS/锁屏悬浮)
                             ↓
                   会后异步:全文高精度ASR校正+离线分离改名→纪要/商机清单/待办/决策卡
                             ↓
                   汇入经营决策外脑(商机进CRM、待办进任务、风险进预警、决策卡进追溯库)
```

**对 SoL-Pi 的对照**：
- **采集→降噪→VAD**：对应 SoL-Pi 的"输入捕获"阶段，但该方案强调**端侧优先**（RNNoise 零 GPU 依赖、C 库好集成），这与 SoL-Pi 的 RK3588 端侧目标完全一致。
- **流式 ASR 2pass**：online 初稿 + offline 纠错的双轨制，与 SoL-Pi 的"渐进式上下文构建"理念一致。
- **三级触发 LLM**（L0 本地规则/L1 轻分类/L2 深度分析）：这与 SoL-Pi 路由.py 的 lightweight/standard/full_graph 三档路由**高度同构**，只是触发条件更精细（数字命中→情绪事件→话题切换→距上次>90s）。
- **提示决策器**：SoL-Pi 缺少这一层——目前 ContextManager 只做信息组织，不做"择时输出"。

### 1.3 多模态融合策略：声学+文本双通道

| 通道 | 输入 | 输出 | 准确率 | 定位 |
|------|------|------|--------|------|
| 声学通道 | F0/能量/语速/停顿/jitter/shimmer | 唤醒度/效价/确定度+事件 | 近场65-78%，饭局45-60% | 触发器与置信度加权 |
| 文本通道 | ASR 文本 | 语义情绪+意图标签+理由 | 75-90%（饭局65-80%） | 主判据，交给 LLM |
| 融合 | 两路结果 | 最终提示 | —— | 声学加权、文本定性、LLM出话术 |

**对 SoL-Pi 的对照**：SoL-Pi 目前只有文本通道（LLM 推理），缺乏声学维度的情绪/语调信号。该方案的"声学只做触发器、文本做主判据、LLM 出话术"的三级分工，可以作为 SoL-Pi 多模态扩展的设计参考。

### 1.4 合规架构：受托人/工具人设计

该方案提出了一个极其关键的**合规定位**：

> 把产品做成"老板手里的智能录音笔＋会后参谋"（受托人/工具人），而不是"悄悄分析所有人的读心机"（自主处理者）

四个必要条件（缺一即升级为"个人信息处理者"）：
1. 每次处理完全由用户主动发起
2. 平台不擅自留存原始音频文本，用户可一键彻底删除
3. 不用于模型训练、不建跨用户声纹库/画像库
4. 与用户签委托处理协议明确指令边界

**对 SoL-Pi 的对照**：SoL-Pi 目前没有明确的用户数据主权设计。该方案的"受托人架构"可以作为 SoL-Pi 隐私保护模块的设计蓝本——特别是：
- **声纹向量仅当次内存、会后即毁**：对应图谱中节点的 TTL（生存时间）机制
- **数据不出省（阿里云张家口）**：对应 SoL-Pi 的本地化部署需求
- **DLP 脱敏上云**：端侧先转文本→NER 脱敏→仅脱敏文本上云推理→省内还原，这与 SoL-Pi 的端侧推理优先策略一致

---

## 二、与 SoL-Pi 系统的逐层对照

### 2.1 对照总表

| BOSS-AI-R 模块 | SoL-Pi 对应模块 | 差距评估 | 融入建议 |
|----------------|-----------------|----------|----------|
| 实时副驾（9段音频链路） | 无对应 | **缺失** | 新增 realtime_audio.py 模块 |
| 说话人分离（3D-Speaker） | context_tracker.py（跨轮追踪） | 可借鉴 | 扩展 context_tracker 增加说话人维度 |
| 声学情绪识别 | 无对应 | **缺失** | 新增 acoustic_emotion.py 模块 |
| 三级 LLM 触发 | routing.py（三档路由） | **高度同构** | 直接扩展触发条件集 |
| 提示决策器 | 无对应 | **缺失** | 新增 prompt_decider.py 模块 |
| 经营外脑（6场景） | graph_retriever.py + evolution_interface.py | 功能等价 | 对齐场景命名与数据流 |
| 会后异步结构化 | observation_pack.py（归档提取） | 类似但维度不同 | 扩展 observation_pack 增加谈判结构化 |
| 决策追溯卡 | evidence_verifier.py（证据核验） | 互补 | 融合为"证据链追溯" |
| 多租户隔离（RLS） | graph_store.py（SQLite） | SoL-Pi 弱 | 增加 tenant_id + RLS 层 |
| 合规/权利响应 | 无对应 | **缺失** | 新增 compliance.py 模块 |
| 四级订阅/定价 | 无对应 | **缺失** | 新增 billing.py 模块 |
| 数据不出省（部署架构） | 无对应 | **缺失** | 新增 deployment.py 模块 |

### 2.2 需要新建的模块（高优先级）

| 模块 | 职责 | 依赖 |
|------|------|------|
| `realtime_audio.py` | 9段音频链路编排、流式处理、降级策略 | RNNoise/sherpa-onnx/云 ASR 抽象层 |
| `prompt_decider.py` | 提示去重/分级/择时/打断保护、通道选择 | routing.py + context_manager.py |
| `compliance.py` | 录音指示/告知模式/权利响应/PIPIA/数据治理 | observation_pack.py |
| `billing.py` | 四级订阅/配额管理/成本监控/渠道分润 | graph_store.py |

### 2.3 需要扩展的模块

| 模块 | 扩展内容 |
|------|----------|
| `routing.py` | 增加 L0 本地关键词触发、声学事件触发、定频120s摘要触发 |
| `context_manager.py` | 增加说话人维度、声学特征维度、谈判档案注入 |
| `observation_pack.py` | 增加谈判五件套结构化提取（纪要/商机/待办/决策卡/复盘） |
| `evidence_verifier.py` | 增加原声时间轴回跳、决策链可追溯 |
| `graph_store.py` | 增加 RLS 行级安全、tenant_id 强制、加密字段 |
| `evolution_interface.py` | 增加"提示采纳率"作为进化信号 |

---

## 三、具体融入方案

### 3.1 阶段一：实时感知层接入（V0.1 对应）

**目标**：将 BOSS-AI-R 的实时音频链路拆解为 SoL-Pi 可消化的模块

#### 3.1.1 新增 `realtime_audio.py`

```python
"""
SoL-Pi 实时音频处理模块
对应 BOSS-AI-R 的 9 段音频链路中的 1-6 段
端侧优先、云边协同、四级降级
"""

class RealtimeAudioPipeline:
    """
    实时音频链路编排器
    输入: PCM 音频帧 (10-20ms)
    输出: Segment 列表 (带时间戳/说话人/文本/情绪事件)
    """
    
    def __init__(self, config):
        self.noise_suppressor = RNNoiseSuppressor()  # 端侧降噪
        self.vad = WebRTCVAD()  # 端点检测
        self.asr_router = ASRServiceRouter()  # 云/边/端三档路由
        self.speaker_separator = Speaker3DSpeaker()  # 说话人分离
        self.emotion_detector = AcousticEmotionDetector()  # 声学情绪
        self.prompt_decider = PromptDecider()  # 提示决策
        
    def process_frame(self, frame: bytes) -> Optional[PromptEvent]:
        """处理单帧音频，返回提示事件或 None"""
        # 1. 降噪
        clean_frame = self.noise_suppressor.process(frame)
        # 2. VAD 端点检测
        is_speech = self.vad.process(clean_frame)
        # 3. 音频累积到 chunk
        chunk = self._accumulate(clean_frame, is_speech)
        if chunk:
            # 4. 并行处理
            text_future = self.asr_router.transcribe_async(chunk)
            speaker_future = self.speaker_separator.identify_async(chunk)
            emotion_future = self.emotion_detector.detect_async(chunk)
            # 5. 融合与决策
            return self.prompt_decider.decide(
                text_future.result(),
                speaker_future.result(),
                emotion_future.result()
            )
        return None
```

#### 3.1.2 新增 `prompt_decider.py`

```python
"""
SoL-Pi 提示决策器
对应 BOSS-AI-R 的"提示决策器（自研：去重/分级/择时/打断保护）"
"""

class PromptDecider:
    """
    决定何时、以何种通道、推送什么内容给 Boss
    核心策略: 算完不立即推，排队到对方停顿点
    """
    
    def decide(self, text_result, speaker_result, emotion_result) -> Optional[PromptEvent]:
        # 1. L0 本地关键词匹配（<100ms, 0 成本）
        keyword_match = self._l0_keyword_match(text_result.text)
        if keyword_match:
            return PromptEvent(
                event_type="keyword_alert",
                priority="high",
                content=f"数字/红线: {keyword_match.matched}",
                evidence=text_result.text,
                trigger="L0",
                confidence=0.95
            )
        
        # 2. L1 轻量分类（声学事件触发）
        if emotion_result.event_type in ["high_arousal", "hesitation", "interruption"]:
            return PromptEvent(
                event_type="emotion_signal",
                priority="medium",
                content=f"声学现象: {emotion_result.event_type}",
                evidence=f"F0={emotion_result.f0:.0f}Hz, energy={emotion_result.energy:.2f}",
                trigger="L1",
                confidence=emotion_result.confidence
            )
        
        # 3. L2 深度分析（需 L0/L1 命中或话题切换）
        if self._should_trigger_l2(text_result, emotion_result):
            return PromptEvent(
                event_type="risk",  # 或 opportunity/interjection_suggest
                priority="high",
                content=self._generate_l2_analysis(text_result),
                evidence=text_result.text,
                trigger="L2",
                confidence=0.8
            )
        
        return None
    
    def select_channel(self, event: PromptEvent) -> List[str]:
        """根据优先级和环境选择反馈通道"""
        if event.priority == "high":
            return ["vibration", "watch", "lockscreen"]
        elif event.priority == "medium":
            return ["watch", "lockscreen"]
        else:
            return ["lockscreen"]
```

### 3.2 阶段二：知识图谱层扩展

**目标**：将 BOSS-AI-R 的"经营外脑"数据模型映射到 SoL-Pi 知识图谱

#### 3.2.1 新增节点类型（扩展 graph_schema.py）

```python
# 在现有 NODE_TYPES 基础上新增：

NegotiationNode = {
    "type": "negotiation",
    "fields": ["session_id", "tenant_id", "timestamp", "industry",
               "participants", "opportunity_count", "risk_count",
               "audio_duration_ms", "transcript_word_count"],
    "relations": ["captures_opportunity", "flags_risk", "involves_participant",
                   "belongs_to_session", "generates_decision_card"]
}

OpportunityNode = {
    "type": "opportunity",
    "fields": ["tenant_id", "session_id", "client_name", "signal_type",
               "budget_amount", "decision_maker", "time_window",
               "next_action", "evidence_span", "status"],
    "relations": ["captured_in", "assigned_to", "derived_from"
}

DecisionCardNode = {
    "type": "decision_card",
    "fields": ["tenant_id", "session_id", "decision_conclusion",
               "timestamp_ms", "evidence_quote", "audio_jump_url",
               "advice_given", "actual_result"],
    "relations": ["made_by", "based_on", "recorded_in_session"
}

ComplianceEventNode = {
    "type": "compliance_event",
    "fields": ["tenant_id", "session_id", "event_type",
               "indicator_status", "notification_delivered",
               "consent_record_id", "retention_policy"],
    "relations": ["logs_consent", "controls_retention", "triggers_deletion"
}
```

#### 3.2.2 扩展 observation_pack.py

```python
"""
扩展 ObservationPack 以支持 BOSS-AI-R 的会后五件套结构化提取
"""

class NegotiationObservationPack(ObservationPack):
    """
    谈判/会议场景的归档包
    产出: 结构化纪要、商机清单、待办、决策追溯卡、谈判复盘
    """
    
    def extract_post_session(self, session_audio, session_segments):
        """会后异步结构化提取"""
        # 1. 高精度 ASR 校正
        corrected_transcript = self._correct_asr(session_audio, session_segments)
        # 2. 说话人改名（拖拽/确认）
        labeled_transcript = self._label_speakers(corrected_transcript)
        # 3. LLM 生成五件套
        structured = self._generate_five_piece(labeled_transcript)
        return {
            "meeting_minutes": structured.minutes,
            "opportunity_cards": structured.opportunities,
            "todo_cards": structured.todos,
            "decision_cards": structured.decisions,
            "negotiation_review": structured.review
        }
```

### 3.3 阶段三：合规与安全层

**目标**：将 BOSS-AI-R 的"受托人架构"融入 SoL-Pi

#### 3.3.1 新增 `compliance.py`

```python
"""
SoL-Pi 合规引擎
对应 BOSS-AI-R 的受托人架构 + 18 功能模块风险等级表
"""

class ComplianceEngine:
    """
    每次操作前的合规检查、操作中的指示控制、操作后的权利响应
    """
    
    # 合规状态机
    STATES = ["idle", "informed_consent", "recording_indicator", 
              "processing", "storing", "deleting", "responding_to_rights"]
    
    def check_recording_permission(self, context: RecordingContext) -> bool:
        """录音前合规检查"""
        checks = [
            self._is_user_present(context),           # 用户本人在场
            self._is_indicative(context),              # 明示录音指示
            self._is_consent_obtained(context),        # 获得同意（告知模式/自行记录模式）
            self._is_scene_appropriate(context),       # 场景合法
            self._is_not_third_party(context),         # 非参与方偷录
        ]
        return all(checks)
    
    def handle_data_subject_request(self, request: DataSubjectRequest) -> Response:
        """被录音方权利响应（PIPL 第 50 条）"""
        if request.type == "deletion":
            return self._delete_segments_by_speaker(request.speaker_id)
        elif request.type == "access":
            return self._export_segments_by_speaker(request.speaker_id)
        elif request.type == "de_identification":
            return self._de_identify_segments(request.speaker_id)
    
    def enforce_retention_policy(self, tenant_id: str):
        """执行数据保留策略（默认 30/90 天过期）"""
        policy = self._get_retention_policy(tenant_id)
        expired = self._find_expired_sessions(tenant_id, policy.days)
        for session in expired:
            self._delete_session_data(session)
            self._log_deletion(session, policy)
```

### 3.4 阶段四：商业模式层

**目标**：将 BOSS-AI-R 的四级定价与成本结构融入 SoL-Pi 部署决策

#### 3.4.1 新增 `billing.py`

```python
"""
SoL-Pi 订阅与成本管理模块
对应 BOSS-AI-R 四级定价（L0/L1/L2/L3）
"""

SUBSCRIPTION_TIERS = {
    "L0": {
        "price": 0,
        "features": ["daily_red_light", "monthly_5_queries", "industry_brief"],
        "realtime_quota": "3_sessions_monthly_20min_each",
        "whisper_enabled": False,
        "emotion_enabled": False
    },
    "L1": {
        "price": 1980,  # 元/年
        "features": ["daily_report", "financial_checkup", "decision_qa"],
        "realtime_quota": "10_hours_monthly_post_session_only",
        "whisper_enabled": False,
        "emotion_enabled": False
    },
    "L2": {
        "price": 9800,  # 元/年（区间 9800-15800）
        "features": ["all_6_scenarios", "realtime_whisper", "emotion_detection"],
        "realtime_quota": "unlimited_fair_use",
        "whisper_enabled": True,
        "emotion_enabled": True
    },
    "L3": {
        "price": 39800,  # 元/年（区间 39800-69800）
        "features": ["all_L2", "private_deployment", "sip_bridge", "custom_scripts"],
        "realtime_quota": "unlimited_private",
        "whisper_enabled": True,
        "emotion_enabled": True
    }
}

class CostMonitor:
    """
    单用户月成本监控
    目标: 自建 ASR 后 5-15 元/用户/月
    警戒线: 云 ASR 过渡期 60-80 元/用户/月
    切换触发: >500 付费或 >100 并发 → 自建 FunASR
    """
    
    def calculate_monthly_cost(self, tenant_id: str) -> float:
        """计算单用户月成本"""
        asr_cost = self._calc_asr_cost(tenant_id)  # 目标 6-24 元
        llm_cost = self._calc_llm_cost(tenant_id)  # 目标 1.2-3.9 元
        server_cost = self._calc_server_share(tenant_id)  # 摊薄 5-15 元
        storage_cost = self._calc_storage_cost(tenant_id)  # ~0.1 元
        network_cost = self._calc_network_cost(tenant_id)  # ~0.3-0.5 元
        return asr_cost + llm_cost + server_cost + storage_cost + network_cost
    
    def should_switch_to_self_hosted(self, total_paying_users: int, peak_concurrent: int) -> bool:
        """自建 ASR 切换决策"""
        return total_paying_users > 500 or peak_concurrent > 100
```

---

## 四、关键设计决策与 BOSS-AI-R 对照

### 4.1 实时性延迟预算与 SoL-Pi 路由策略的融合

BOSS-AI-R 定义了三档延迟目标：

| 提示类型 | 链路 | 现实目标 | SoL-Pi 对应路由 |
|----------|------|----------|-----------------|
| 简单关键词/数字/红线预警 | L0 本地或云 ASR+规则→震动 | 1.5-2.5s | lightweight（纯本地） |
| 情绪变化/态度信号 | ASR+声学事件+L1→手表 | 3-5s | standard（轻量模型） |
| 复杂插话建议/风险推理/商机 | ASR+L2 推理（+可选 TTS） | 5-10s | full_graph（深度分析） |

**融合方案**：将 BOSS-AI-R 的三档延迟目标作为 SoL-Pi routing.py 的 SLA 约束，在路由决策时不仅考虑信息完整度，还考虑延迟要求。

### 4.2 声学情绪识别的"只做触发器"原则

BOSS-AI-R 对情绪识别极其谨慎：
- 只输出声学现象（语速加快/音量升高/长停顿/语调上扬/被打断）
- **严禁**输出"对方在撒谎/真实意图/测谎"
- 默认关闭，用户主动开启
- 不建跨会话情绪画像

**融入 SoL-Pi**：在 evolution_interface.py 中增加"声学事件→进化信号"的采集，但严格遵守"只描述现象、不做人格推断"原则。

### 4.3 四级自动降级阶梯

| 级别 | 触发条件 | 工作模式 |
|------|----------|----------|
| L-A 优 | 网络良好、算力正常 | 云 ASR + 云 L2 全功能 |
| L-B 弱网/高延迟 | RTT>500ms 或丢包 | 端侧 sherpa-onnx ASR + 本地关键词/声学事件 |
| L-C 嘈杂环境 | 信噪比低/多人重叠 | 提高置信度阈值，只报高级风险与明确数字 |
| L-D LLM 超时 | 深度分析 >3s 未回 | 丢弃本次 L2，只保留 L0/L1 结果 |

**融入 SoL-Pi**：在 context_manager.py 中增加"环境质量评估"维度，动态调整路由策略和输出置信度阈值。

### 4.4 "数据不出河北"的部署架构

BOSS-AI-R 要求：
- 主用阿里云华北 3（张家口，物理在河北）
- 腾讯云无河北标准公有云地域
- 备份同地域
- 原始 PCM 不落盘，只存 Opus（约 10MB/h）
- 音频默认 30/90 天策略过期删除

**融入 SoL-Pi**：
1. 在 graph_store.py 中增加数据驻留策略配置
2. 在 observation_pack.py 中增加 TTL 过期自动清理
3. 端侧推理优先（RK3588 NPU）天然满足"数据不出场"

---

## 五、风险与合规的 SoL-Pi 映射

### 5.1 BOSS-AI-R 18 功能模块风险等级表 → SoL-Pi 约束规则

| BOSS-AI-R 风险等级 | 对应 SoL-Pi 约束 |
|-------------------|------------------|
| 红线·禁止（偷录/远程静默/伪装录音） | **系统级禁止**：不提供远程唤起/隐藏图标 API |
| 高·不可行（蜂窝通话录音） | 不做、不宣传 |
| 高（声纹跨会话建库） | 向量仅内存、会后即毁、不跨会话复用 |
| 高（测谎/读心） | 输出仅限声学现象、不做人格推断 |
| 中（情绪识别默认关闭） | 默认关闭、用户主动开启、带置信度 |
| 中（云端实时转写） | 受托人架构、告知模式、最小上传、DLP 脱敏 |
| 低（自录音证据） | 合法使用承诺、原始件存证 |

### 5.2 PIPIA（个人信息保护影响评估）四章必备

BOSS-AI-R 要求上线前完成：
1. 声纹处理 PIPIA
2. 情绪处理 PIPIA
3. 云处理 PIPIA
4. 数据出境 PIPIA

**融入 SoL-Pi**：在 compliance.py 中增加 PIPIA 报告生成器，作为上线前的强制检查门。

---

## 六、路线图建议

### 6.1 BOSS-AI-R 四阶段路线与 SoL-Pi 阶段对照

| BOSS-AI-R 版本 | 时间 | 核心交付 | SoL-Pi 对应阶段 |
|----------------|------|----------|----------------|
| V0.1 MVP | 0-4 月 | 纯 APP 跑通现场 1v1/小型谈判 + 经营外脑 | 阶段 0-2 巩固 + 实时音频模块 |
| V0.2 | 6 月 | 情绪双通道 + L2 复杂插话 + 自建 ASR 降本 | 阶段 3-4 扩展 + 声学情绪模块 |
| V0.3 | 12 月 | 行业话术库 + SIP 桥 + 私有化一体机 | 阶段 5 演进 + 合规引擎 |
| V1.0 | 18 月 | 完整矩阵 + 城市合伙人 + 外省复制 | SoL-Pi 全域部署 |

### 6.2 融入 SoL-Pi 的优先级建议

| 优先级 | 模块 | 工作量 | 价值 |
|--------|------|--------|------|
| P0 | prompt_decider.py | 2 周 | 实时提示是核心差异化 |
| P0 | compliance.py | 1 周 | 合规是上线前提 |
| P1 | realtime_audio.py（简化版） | 3 周 | 端侧降噪+VAD+L0 触发 |
| P1 | billing.py | 1 周 | 商业化必需 |
| P2 | acoustic_emotion.py | 2 周 | 情绪触发器 |
| P2 | graph_schema 扩展 | 1 周 | 谈判/商机/决策卡节点 |
| P3 | speaker_separator 集成 | 2 周 | 说话人分离 |
| P3 | deployment.py | 1 周 | 数据不出省部署 |

---

## 七、核心结论

### 7.1 BOSS-AI-R 对 SoL-Pi 的最大价值

1. **实时维度补充**：SoL-Pi 目前只有异步处理，BOSS-AI-R 的 9 段音频链路提供了完整的实时感知层设计。
2. **"第六感+大脑"双模架构**：实时提示（震动/耳语）与后台分析（经营外脑）的闭环，是 SoL-Pi 从效率工具升级为决策伙伴的关键。
3. **合规先行设计**：受托人架构、数据不出省、声纹会后即毁，为 SoL-Pi 的端侧部署提供了合规蓝本。
4. **四级降级策略**：云全功能→端侧 ASR 兜底→只报高级→超时丢弃，为 SoL-Pi 的端侧降级提供了工程模板。

### 7.2 需要警惕的设计陷阱

1. **"不上云"宣传**：NBBOSS 被供应商案例稿打脸，SoL-Pi 宣传必须"架构可验证、措辞可举证"。
2. **纯云 ASR 成本**：72-210 元/用户/月不可持续，必须在第一天设计"云起步、自建切换"。
3. **情绪识别测谎**：学术界公认不可迁移，SoL-Pi 必须严守"只描述现象"红线。
4. **硬件陷阱**：公模 100-390 元遍地，不自研私模、不压库存。

### 7.3 一句话总结

> BOSS-AI-R 的核心洞察是"**实时感知与后台决策的闭环**"——这与 SoL-Pi 的"效率机制+图谱记忆"天然互补。融入后，SoL-Pi 将从异步效率工具升级为"实时第六感 + 经营外脑"的决策伙伴。

---

## 附录 A：BOSS-AI-R 关键数字速查

| 指标 | 数值 |
|------|------|
| 公模录音卡 BOM | 55-70 元 |
| 公模出厂价 | 100-260 元 |
| NBBOSS 加价倍率 | 7-15 倍 |
| 实时提示延迟目标 | <2.5s / 3-5s / 5-10s |
| 自建 ASR 月成本 | 6-24 元/用户 |
| 纯云 ASR 月成本 | 58-210 元/用户 |
| LLM 月成本（便宜档） | ~1.2 元/用户 |
| LLM 月成本（均衡档） | ~3.9 元/用户 |
| L2 定价 | 9,800-15,800 元/年 |
| 定州 90 天目标 | 付费 50-80 家、收入 8-15 万 |
| 90 天预算 | 29-41.5 万 |

## 附录 B：BOSS-AI-R 与 SoL-Pi 概念映射

| BOSS-AI-R 概念 | SoL-Pi 概念 |
|----------------|-------------|
| 实时副驾 | 实时音频处理模块（新增） |
| 经营外脑 | graph_retriever + evolution_interface |
| 三级 LLM 触发 | routing.py 三档路由 |
| 说话人分离 | context_tracker 扩展 |
| 声学情绪 | 新增多模态维度 |
| 会后五件套 | observation_pack 扩展 |
| 决策追溯卡 | evidence_verifier 扩展 |
| 受托人架构 | compliance.py 新增 |
| 数据不出省 | 端侧优先 + 部署约束 |
| 四级订阅 | billing.py 新增 |
| PIPIA | compliance.py 新增 |
| 提示决策器 | prompt_decider.py 新增 |
