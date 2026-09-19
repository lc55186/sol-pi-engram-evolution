#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASR Router - 实时语音识别路由
支持多引擎切换：讯飞 / 腾讯云 / Whisper 本地
"""

from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import json
import base64
import tempfile
import os
import asyncio
import logging
from typing import Optional
from enum import Enum

logger = logging.getLogger("asr_router")


class ASREngine(Enum):
    IFLYTEK = "iflytek"
    TENCENT = "tencent"
    WHISPER = "whisper"


# 引擎优先级（高 → 低）
ENGINE_PRIORITY = [ASREngine.IFLYTEK, ASREngine.TENCENT, ASREngine.WHISPER]


class ASRConfig:
    """ASR 引擎配置"""
    def __init__(self):
        self.iflytek_app_id = os.getenv("IFLYTEK_APP_ID", "")
        self.iflytek_api_key = os.getenv("IFLYTEK_API_KEY", "")
        self.iflytek_api_secret = os.getenv("IFLYTEK_API_SECRET", "")
        self.tencent_secret_id = os.getenv("TENCENT_SECRET_ID", "")
        self.tencent_secret_key = os.getenv("TENCENT_SECRET_KEY", "")
        self.whisper_model = os.getenv("WHISPER_MODEL", "large-v3")
        self.hot_words = []  # 热词列表

    def get_available_engines(self) -> list[ASREngine]:
        """获取可用引擎列表"""
        engines = []
        if self.iflytek_app_id and self.iflytek_api_key:
            engines.append(ASREngine.IFLYTEK)
        if self.tencent_secret_id and self.tencent_secret_key:
            engines.append(ASREngine.TENCENT)
        engines.append(ASREngine.WHISPER)  # 本地始终可用
        return engines


class ASRSession:
    """ASR 会话管理"""
    def __init__(self, session_id: str, engine: ASREngine = ASREngine.WHISPER):
        self.session_id = session_id
        self.engine = engine
        self.created_at = asyncio.get_event_loop().time()
        self.is_active = True
        self.transcript_buffer = []
        self.audio_buffer = b""
        self.total_duration = 0.0

    def add_audio(self, audio_data: bytes):
        self.audio_buffer += audio_data

    def add_transcript(self, text: str, is_final: bool = False):
        self.transcript_buffer.append({
            "text": text,
            "is_final": is_final,
            "timestamp": asyncio.get_event_loop().time()
        })

    def get_transcript(self) -> str:
        return " ".join([t["text"] for t in self.transcript_buffer if t.get("is_final", False)])


class ASRManager:
    """ASR 管理器"""
    def __init__(self):
        self.config = ASRConfig()
        self.sessions: dict[str, ASRSession] = {}
        self._engine_health: dict[ASREngine, bool] = {}

    async def create_session(self, session_id: str, preferred_engine: Optional[str] = None) -> ASRSession:
        """创建 ASR 会话"""
        engine = ASREngine.WHISPER  # 默认本地

        if preferred_engine:
            try:
                engine = ASREngine(preferred_engine)
            except ValueError:
                pass

        # 检查引擎可用性
        available = self.config.get_available_engines()
        if engine not in available:
            engine = available[0] if available else ASREngine.WHISPER

        session = ASRSession(session_id, engine)
        self.sessions[session_id] = session
        logger.info(f"Created ASR session {session_id} with engine {engine.value}")
        return session

    async def process_audio(self, session_id: str, audio_data: bytes) -> dict:
        """处理音频数据"""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        session.add_audio(audio_data)

        # 根据引擎选择处理方式
        if session.engine == ASREngine.WHISPER:
            result = await self._process_whisper(session, audio_data)
        elif session.engine == ASREngine.IFLYTEK:
            result = await self._process_iflytek(session, audio_data)
        elif session.engine == ASREngine.TENCENT:
            result = await self._process_tencent(session, audio_data)
        else:
            result = {"error": "Unknown engine"}

        if result.get("text"):
            session.add_transcript(result["text"], result.get("is_final", False))

        return result

    async def _process_whisper(self, session: ASRSession, audio_data: bytes) -> dict:
        """本地 Whisper 处理"""
        try:
            import whisper
            model = whisper.load_model(self.config.whisper_model)

            # 保存临时文件
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name

            result = model.transcribe(temp_path, language="zh")
            os.unlink(temp_path)

            return {
                "text": result["text"],
                "is_final": True,
                "engine": "whisper",
                "confidence": result.get("confidence", 0.8)
            }
        except Exception as e:
            logger.error(f"Whisper error: {e}")
            return {"error": str(e)}

    async def _process_iflytek(self, session: ASRSession, audio_data: bytes) -> dict:
        """讯飞 ASR 处理（预留接口）"""
        # TODO: 实现讯飞 SDK 集成
        return await self._process_whisper(session, audio_data)

    async def _process_tencent(self, session: ASRSession, audio_data: bytes) -> dict:
        """腾讯云 ASR 处理（预留接口）"""
        # TODO: 实现腾讯云 SDK 集成
        return await self._process_whisper(session, audio_data)

    async def close_session(self, session_id: str):
        """关闭会话"""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            del self.sessions[session_id]


# 全局管理器
asr_manager = ASRManager()

router = APIRouter(prefix="/api/v1/asr", tags=["ASR"])


@router.post("/sessions")
async def create_session(engine: Optional[str] = None):
    """创建 ASR 会话"""
    import uuid
    session_id = str(uuid.uuid4())
    session = await asr_manager.create_session(session_id, engine)
    return {
        "session_id": session.session_id,
        "engine": session.engine.value,
        "created_at": session.created_at
    }


@router.delete("/sessions/{session_id}")
async def close_session(session_id: str):
    """关闭 ASR 会话"""
    await asr_manager.close_session(session_id)
    return {"status": "closed"}


@router.post("/sessions/{session_id}/audio")
async def upload_audio(session_id: str, file: UploadFile = File(...)):
    """上传音频文件进行识别"""
    content = await file.read()
    result = await asr_manager.process_audio(session_id, content)
    return result


@router.get("/sessions/{session_id}/transcript")
async def get_transcript(session_id: str):
    """获取当前会话的转写文本"""
    session = asr_manager.sessions.get(session_id)
    if not session:
        return {"error": "Session not found"}

    return {
        "transcript": session.get_transcript(),
        "buffer": session.transcript_buffer[-10:]  # 最近10条
    }


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket 实时转写"""
    await websocket.accept()

    session = asr_manager.sessions.get(session_id)
    if not session:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return

    try:
        while True:
            data = await websocket.receive_bytes()
            result = await asr_manager.process_audio(session_id, data)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        await asr_manager.close_session(session_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_json({"error": str(e)})


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "available_engines": [e.value for e in asr_manager.config.get_available_engines()],
        "active_sessions": len(asr_manager.sessions)
    }
