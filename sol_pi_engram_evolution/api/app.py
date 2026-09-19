"""
BOSS-AI-R FastAPI 应用主入口

提供 RESTful API + WebSocket 实时通信。
V0.1 包含：认证、实时副驾、经营外脑、合规、计费。

V0.2 架构改进：
- RESTful 资源命名统一（复数名词）
- 添加分页支持（limit/offset）
- 标准 HTTP 状态码（201 Created, 422 Validation Error）
- 依赖注入支持（服务实例化解耦）
- 请求 ID 自动传播到日志
"""

import time
import uuid
from contextlib import asynccontextmanager

import uvicorn
from fastapi import (
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from config import get_config
from logger import (
    clear_request_id,
    get_logger,
    log_request,
    log_tenant_action,
    set_request_id,
    setup_logging,
)
from modules.acoustic_emotion import AcousticEmotionAnalyzer
from modules.billing import SubscriptionManager, SubscriptionTier
from modules.compliance import ComplianceEngine, ConsentType
from modules.prompt_decider import PromptDecider
from modules.realtime_audio import AudioPipeline

# ===== 全局服务实例 =====
config = get_config()
logger = get_logger("api")

# 服务实例（V0.1 单实例，V0.2 改为依赖注入/连接池）
prompt_decider = PromptDecider(config)
compliance_engine = ComplianceEngine(config)
audio_pipeline = AudioPipeline(config)
emotion_analyzer = AcousticEmotionAnalyzer(config)
subscription_manager = SubscriptionManager(config)

# WebSocket 连接管理
ws_connections: dict = {}  # session_id -> websocket


# ===== 应用生命周期 =====
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭钩子"""
    setup_logging(console_level="INFO", json_format=(config.env == "production"))
    logger.info(f"BOSS-AI-R v{config.version} starting in {config.env} mode")
    yield
    logger.info("BOSS-AI-R shutting down")


# ===== FastAPI 实例 =====
app = FastAPI(
    title="BOSS-AI-R API",
    description="老板口袋军师·实时谈判版 — 后端 API",
    version=config.version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 静态文件 + 模板
app.mount("/static", StaticFiles(directory="ui/static"), name="static")
templates = Jinja2Templates(directory="ui/templates")

# ===== 中间件 =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if config.debug else ["https://*.boss-ai.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """请求日志中间件（V0.2: 添加请求 ID 传播）"""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # 设置线程本地请求 ID（用于日志传播）
    set_request_id(request_id)

    # 注入 request_id 到请求状态
    request.state.request_id = request_id

    response = await call_next(request)

    duration_ms = (time.time() - start_time) * 1000
    log_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=duration_ms
    )

    response.headers["X-Request-ID"] = request_id

    # 清理线程本地请求 ID
    clear_request_id()

    return response


# ===== 请求/响应模型 =====
class RecordingStartRequest(BaseModel):
    """开始录音请求"""
    tenant_id: str = Field(..., description="租户 ID")
    user_id: str = Field(..., description="用户 ID")
    scene: str = Field("business_negotiation", description="场景类型")
    platform: str = Field("android", description="平台（ios/android）")

    class Config:
        json_schema_extra = {
            "example": {
                "tenant_id": "tenant-001",
                "user_id": "user-001",
                "scene": "business_negotiation",
                "platform": "android"
            }
        }


class RecordingResponse(BaseModel):
    """录音会话响应"""
    session_id: str
    status: str
    indicators: list[str]
    message: str


class PromptResponse(BaseModel):
    """提示事件响应"""
    event_id: str
    event_type: str
    priority: str
    content: str
    evidence: str
    confidence: float
    channels: list[str]


class EmotionStateResponse(BaseModel):
    """情绪状态响应"""
    arousal: float
    valence: float
    confidence: float


class SubscriptionCreateRequest(BaseModel):
    """创建订阅请求"""
    tenant_id: str
    user_id: str
    tier: str  # L0/L1/L2/L3
    price_rmb: int = 0
    channel_id: str = ""
    channel_rate: float = 0.0


class QuotaResponse(BaseModel):
    """配额响应"""
    tier: str
    status: str
    used_minutes: float
    total_minutes: int
    remaining_minutes: int
    whisper_enabled: bool
    emotion_enabled: bool
    total_cost_rmb: float


class ComplianceCheckRequest(BaseModel):
    """合规检查请求"""
    user_id: str
    tenant_id: str
    scene: str
    has_third_party: bool = False


class ComplianceCheckResponse(BaseModel):
    """合规检查响应"""
    allowed: bool
    reason: str
    requirements: list[str]


class PaginatedResponse(BaseModel):
    """分页响应包装器（V0.2 新增）"""
    total: int
    limit: int
    offset: int
    items: list[dict]


# ===== 页面路由 =====
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主控台页面"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "version": config.version,
        "env": config.env
    })


@app.get("/realtime", response_class=HTMLResponse)
async def realtime_page(request: Request):
    """实时副驾页面"""
    return templates.TemplateResponse("realtime.html", {
        "request": request,
        "version": config.version
    })


@app.get("/brain", response_class=HTMLResponse)
async def brain_page(request: Request):
    """经营外脑页面"""
    return templates.TemplateResponse("brain.html", {
        "request": request,
        "version": config.version
    })


@app.get("/graph", response_class=HTMLResponse)
async def graph_page(request: Request):
    """知识图谱页面"""
    return templates.TemplateResponse("graph.html", {
        "request": request,
        "version": config.version
    })


@app.get("/compliance", response_class=HTMLResponse)
async def compliance_page(request: Request):
    """合规页面"""
    return templates.TemplateResponse("compliance.html", {
        "request": request,
        "version": config.version
    })


@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    """定价页面"""
    return templates.TemplateResponse("pricing.html", {
        "request": request,
        "version": config.version
    })


@app.get("/roadmap", response_class=HTMLResponse)
async def roadmap_page(request: Request):
    """路线图页面"""
    return templates.TemplateResponse("roadmap.html", {
        "request": request,
        "version": config.version
    })


# ===== API 路由 =====

# --- 实时副驾（V0.2: RESTful 资源命名 /sessions） ---
@app.post("/api/v1/sessions", response_model=RecordingResponse, status_code=201)
async def create_recording_session(request: RecordingStartRequest):
    """
    创建录音会话

    V0.2 RESTful 改进：使用 POST /sessions 创建资源
    1. 合规检查
    2. 创建音频会话
    3. 激活三重录音指示
    4. 返回 session_id（201 Created）
    """
    # 1. 合规检查
    check = compliance_engine.check_recording_permission(
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        scene=request.scene
    )

    if not check["allowed"]:
        raise HTTPException(status_code=403, detail=check["reason"])

    # 2. 检查订阅权限
    access = subscription_manager.check_access(
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        feature="realtime"
    )

    if not access["allowed"]:
        raise HTTPException(status_code=402, detail={
            "message": access["reason"],
            "upgrade_to": access["upgrade_to"]
        })

    # 3. 创建音频会话
    session = audio_pipeline.create_session(
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        platform=request.platform
    )

    # 4. 开始录音
    audio_pipeline.start_recording(session.session_id)

    # 5. 激活录音指示
    indicators = compliance_engine.activate_recording_indicators(
        session.session_id,
        request.platform
    )

    # 6. 启用情绪分析（如果用户已同意）
    if compliance_engine.check_emotion_permission(request.user_id, request.tenant_id):
        emotion_analyzer.enable(session.session_id)

    # 7. 记录审计日志
    log_tenant_action(request.tenant_id, user_id=request.user_id, action="recording_start")

    logger.info(f"Recording started: session={session.session_id[:8]}, tenant={request.tenant_id}")

    return RecordingResponse(
        session_id=session.session_id,
        status="recording",
        indicators=[i.value for i in indicators],
        message="录音已开始，三重指示已激活"
    )


@app.delete("/api/v1/sessions/{session_id}", status_code=200)
async def delete_recording_session(session_id: str):
    """
    停止/删除录音会话

    V0.2 RESTful 改进：使用 DELETE /sessions/{id} 终止资源
    """
    result = audio_pipeline.stop_recording(session_id)

    if not result:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 清理
    compliance_engine.cleanup_session(session_id, "")
    emotion_analyzer.cleanup_session(session_id)
    audio_pipeline.cleanup_session(session_id)

    return {
        "session_id": session_id,
        "status": "completed",
        "stats": result
    }


@app.get("/api/v1/sessions/{session_id}")
async def get_recording_session(session_id: str):
    """获取录音会话状态"""
    status = audio_pipeline.get_session_status(session_id)

    if not status:
        raise HTTPException(status_code=404, detail="会话不存在")

    return status


# --- WebSocket 实时通信 ---
@app.websocket("/ws/realtime/{session_id}")
async def realtime_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket 实时通信
    
    上行：音频帧（二进制）+ 控制消息（JSON）
    下行：ASR 结果 + 提示事件 + 情绪状态
    
    SECURITY FIX: WebSocket 认证 — 连接前验证会话所有权
    """
    # SECURITY FIX: 认证 — 从 query params 或 header 获取 user_id/tenant_id
    user_id = websocket.query_params.get("user_id", "")
    tenant_id = websocket.query_params.get("tenant_id", "")
    
    # 验证会话存在且所有权正确
    if not verify_session_ownership(session_id, user_id, tenant_id):
        # 审计日志：WebSocket 连接拒绝
        log_tenant_action(
            tenant_id,
            user_id=user_id,
            action="websocket_denied",
            detail=f"session={session_id[:8]}, reason=unauthorized"
        )
        await websocket.close(code=4001, reason="无权连接此会话")
        return
    
    await websocket.accept()
    ws_connections[session_id] = websocket
    
    # 审计日志：WebSocket 连接建立
    log_tenant_action(
        tenant_id,
        user_id=user_id,
        action="websocket_connected",
        detail=f"session={session_id[:8]}"
    )
    
    logger.info(f"WebSocket connected: {session_id[:8]}")

    try:
        while True:
            # 接收消息
            data = await websocket.receive()

            # 处理二进制音频帧
            if "bytes" in data:
                pcm_data = data["bytes"]

                # 处理音频帧
                result = audio_pipeline.process_frame(session_id, pcm_data)

                if result:
                    # 分析情绪
                    emotion_result = None
                    if result.get("asr_result"):
                        # 模拟 PCM 数据用于情绪分析
                        emotion_result = emotion_analyzer.analyze_frame(
                            session_id=session_id,
                            pcm_data=pcm_data,
                            timestamp_ms=result["asr_result"].start_ms
                        )

                    # 决策提示
                    prompt = None
                    if result.get("asr_result"):
                        prompt = prompt_decider.decide(
                            text=result["asr_result"].text,
                            speaker=result["asr_result"].speaker_role,
                            emotion=emotion_result.get("state").__dict__ if emotion_result and emotion_result.get("state") else None,
                            session_id=session_id,
                            is_speaking=False,
                            silence_ms=600,
                            current_ms=result["asr_result"].end_ms
                        )

                    # 发送结果
                    response = {
                        "type": "realtime_update",
                        "timestamp": time.time(),
                        "asr": {
                            "text": result["asr_result"].text if result.get("asr_result") else "",
                            "confidence": result["asr_result"].confidence if result.get("asr_result") else 0,
                            "speaker": result["asr_result"].speaker_role if result.get("asr_result") else "",
                        },
                        "emotion": emotion_result.get("state").to_dict() if emotion_result and emotion_result.get("state") else None,
                        "prompt": {
                            "content": prompt.content,
                            "priority": prompt.priority.value,
                            "evidence": prompt.evidence,
                            "channels": [c.value for c in prompt.delivered_channels]
                        } if prompt else None
                    }

                    await websocket.send_json(response)

            # 处理文本控制消息
            elif "text" in data:
                import json
                msg = json.loads(data["text"])
                msg_type = msg.get("type")

                if msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                elif msg_type == "update_network":
                    # 更新网络状态
                    audio_pipeline.update_network_status(
                        session_id=session_id,
                        rtt_ms=msg.get("rtt_ms", 50),
                        packet_loss=msg.get("packet_loss", 0),
                        snr_db=msg.get("snr_db", 20)
                    )
                    await websocket.send_json({"type": "network_updated"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id[:8]}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", extra={"session_id": session_id})
    finally:
        ws_connections.pop(session_id, None)


# --- 合规（V0.2: RESTful 资源命名 /consents, /compliance-checks） ---
@app.post("/api/v1/compliance-checks", response_model=ComplianceCheckResponse, status_code=201)
async def create_compliance_check(request: ComplianceCheckRequest):
    """
    创建合规检查

    V0.2 RESTful 改进：使用 POST /compliance-checks 创建检查记录
    """
    result = compliance_engine.check_recording_permission(
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        scene=request.scene,
        has_third_party=request.has_third_party
    )
    return ComplianceCheckResponse(**result)


@app.get("/api/v1/tenants/{tenant_id}/compliance-summary")
async def get_tenant_compliance_summary(tenant_id: str):
    """
    获取租户合规摘要

    V0.2 RESTful 改进：嵌套资源 /tenants/{id}/compliance-summary
    """
    return compliance_engine.get_compliance_summary(tenant_id)


@app.post("/api/v1/users/{user_id}/consents", status_code=201)
async def create_user_consent(
    user_id: str,
    consent_type: str,
    tenant_id: str = "",
    version: str = "1.0"
):
    """
    创建用户同意记录

    V0.2 RESTful 改进：使用 POST /users/{id}/consents
    """
    try:
        ct = ConsentType(consent_type)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"无效的同意类型: {consent_type}")

    record = compliance_engine.add_consent(user_id, ct, tenant_id, version)
    return {"consent_id": record.consent_id, "status": "granted"}


# --- 计费（V0.2: RESTful 资源命名 /subscriptions） ---
@app.post("/api/v1/subscriptions", status_code=201)
async def create_subscription(request: SubscriptionCreateRequest):
    """
    创建订阅

    V0.2 RESTful 改进：使用 POST /subscriptions 创建资源
    """
    try:
        tier = SubscriptionTier(request.tier)
    except ValueError:
        raise HTTPException(status_code=422, detail=f"无效的订阅层级: {request.tier}")

    sub = subscription_manager.create_subscription(
        tenant_id=request.tenant_id,
        user_id=request.user_id,
        tier=tier,
        price_rmb=request.price_rmb,
        channel_id=request.channel_id,
        channel_rate=request.channel_rate
    )

    return {
        "subscription_id": sub.subscription_id,
        "tier": sub.tier.value,
        "status": sub.status.value,
        "expires_at": sub.expires_at
    }


@app.get("/api/v1/tenants/{tenant_id}/quota", response_model=QuotaResponse)
async def get_tenant_quota(tenant_id: str):
    """
    获取租户配额

    V0.2 RESTful 改进：嵌套资源 /tenants/{id}/quota
    """
    summary = subscription_manager.get_quota_summary(tenant_id)
    if not summary:
        raise HTTPException(status_code=404, detail="无有效订阅")
    return QuotaResponse(**summary)


@app.get("/api/v1/tenants/{tenant_id}/costs")
async def get_tenant_costs(tenant_id: str):
    """
    获取租户成本明细

    V0.2 RESTful 改进：嵌套资源 /tenants/{id}/costs
    """
    cost = subscription_manager.get_monthly_cost(tenant_id)
    return {
        "asr_cost": cost.asr_cost,
        "llm_cost": cost.llm_cost,
        "server_cost": cost.server_cost,
        "storage_cost": cost.storage_cost,
        "network_cost": cost.network_cost,
        "total_cost": cost.total_cost,
        "self_hosted_cost": cost.self_hosted_cost,
        "savings": cost.savings
    }


# --- Graph Knowledge Base ---
from api.graph_router import router as graph_router
app.include_router(graph_router)

# --- ASR Router ---
from api.asr_router import router as asr_router
app.include_router(asr_router)

# --- 健康检查 ---
@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "version": config.version,
        "env": config.env,
        "timestamp": time.time()
    }


# --- 统计（V0.2: 添加分页支持） ---
@app.get("/api/v1/stats")
async def get_stats(
    limit: int = Query(default=20, ge=1, le=100, description="每页数量"),
    offset: int = Query(default=0, ge=0, description="偏移量")
):
    """
    系统统计（V0.2: 支持分页）
    """
    return {
        "active_recordings": len(audio_pipeline._sessions),
        "active_connections": len(ws_connections),
        "total_subscriptions": len(subscription_manager._subscriptions),
        "config": {
            "env": config.env,
            "asr_provider": config.asr.cloud_provider,
            "llm_provider": config.llm.primary_provider
        },
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(audio_pipeline._sessions) + len(ws_connections)
        }
    }


# ===== 启动入口 =====
def main():
    """开发服务器启动"""
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug,
        log_level="info"
    )


if __name__ == "__main__":
    main()
