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
import time
import struct
from typing import Optional
from enum import Enum

logger = logging.getLogger("asr_router")


class TencentASRClient:
    """腾讯云 ASR 客户端（异步识别）

    使用 CreateRecTask + DescribeTaskStatus 轮询模式。
    每次 process_audio 调用创建一个新任务（不支持流式，适合短音频块）。
    """

    def __init__(self, secret_id: str = "", secret_key: str = "", app_id: str = ""):
        self.secret_id = secret_id or os.getenv("TENCENTCLOUD_SECRET_ID", "")
        self.secret_key = secret_key or os.getenv("TENCENTCLOUD_SECRET_KEY", "")
        self.app_id = app_id or os.getenv("TENCENTCLOUD_ASR_APP_ID", "")
        self._client = None

    def _get_client(self):
        """延迟初始化 SDK 客户端（线程安全）"""
        if self._client is None:
            from tencentcloud.common import credential
            from tencentcloud.asr.v20190614 import asr_client
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile

            cred = credential.Credential(self.secret_id, self.secret_key)
            http_profile = HttpProfile()
            http_profile.timeout = 60

            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile

            self._client = asr_client.AsrClient(
                cred, "ap-guangzhou", client_profile
            )
        return self._client

    async def transcribe(self, audio_data: bytes) -> dict:
        """提交音频并等待识别结果

        Args:
            audio_data: 原始 PCM 16-bit 数据

        Returns:
            dict: {"text": str, "confidence": float, "is_final": bool, "task_id": str}
        """
        import asyncio
        from tencentcloud.asr.v20190614 import models

        client = self._get_client()

        # 构建请求
        req = models.CreateRecTaskRequest()
        req.EngineModelType = "16k_zh"
        req.ChannelNum = 1
        req.ResTextFormat = 2  # 词时间戳 + 标点
        req.SourceType = 1     # 音频数据（base64）

        # 添加 WAV 头
        wav_data = self._wrap_wav(audio_data, sample_rate=16000, channels=1, bits_per_sample=16)
        audio_base64 = base64.b64encode(wav_data).decode("utf-8")
        req.Data = audio_base64
        req.DataLen = len(audio_data)  # 注意是 PCM 原始长度

        # 在线程池中执行同步 SDK 调用
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(
            None, lambda: client.CreateRecTask(req)
        )
        task_id = resp.Data.TaskId
        logger.info(f"Tencent ASR task created: {task_id}")

        # 轮询任务状态
        result_text = ""
        result_confidence = 0.0
        is_final = False

        for _ in range(60):  # 最多等待 60s
            await asyncio.sleep(1)

            status_req = models.DescribeTaskStatusRequest()
            status_req.TaskId = task_id

            status_resp = await loop.run_in_executor(
                None, lambda: client.DescribeTaskStatus(status_req)
            )
            status = status_resp.Data.Status

            if status == 2:  # 完成
                # 优先使用 Result 字符串
                result_text = status_resp.Data.Result or ""
                # 从 ResultDetail 提取置信度（SentenceDetail 无 Confidence 字段，使用默认值）
                details = status_resp.Data.ResultDetail or []
                if details:
                    # 拼接 FinalSentence
                    parts = [d.FinalSentence for d in details if d.FinalSentence]
                    if parts:
                        result_text = "".join(parts)
                result_confidence = 0.9  # SDK 不返回置信度，使用默认值
                is_final = True
                break
            elif status == 3:  # 失败
                raise RuntimeError(f"Tencent ASR task {task_id} failed")

        return {
            "text": result_text,
            "confidence": result_confidence,
            "is_final": is_final,
            "task_id": task_id,
            "engine": "tencent",
        }

    @staticmethod
    def _wrap_wav(pcm_data: bytes, sample_rate: int, channels: int, bits_per_sample: int) -> bytes:
        """PCM 裸数据 → WAV 文件"""
        byte_rate = sample_rate * channels * (bits_per_sample // 8)
        block_align = channels * (bits_per_sample // 8)

        header = (
            b"RIFF"
            + struct.pack("<I", 36 + len(pcm_data))
            + b"WAVE"
            + b"fmt "
            + struct.pack("<IHHIIHH", 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample)
            + b"data"
            + struct.pack("<I", len(pcm_data))
        )
        return header + pcm_data

    def health_check(self) -> bool:
        """检查凭证是否配置"""
        return bool(self.secret_id and self.secret_key)


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
        self.tencent_secret_id = os.getenv("TENCENTCLOUD_SECRET_ID", "")
        self.tencent_secret_key = os.getenv("TENCENTCLOUD_SECRET_KEY", "")
        self.tencent_app_id = os.getenv("TENCENTCLOUD_ASR_APP_ID", "")
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
        self._tencent_client: Optional[TencentASRClient] = None

    @property
    def tencent_client(self) -> TencentASRClient:
        """延迟初始化腾讯云客户端"""
        if self._tencent_client is None:
            self._tencent_client = TencentASRClient(
                secret_id=self.config.tencent_secret_id,
                secret_key=self.config.tencent_secret_key,
                app_id=self.config.tencent_app_id,
            )
        return self._tencent_client

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
        """腾讯云 ASR 处理（CreateRecTask + DescribeTaskStatus 轮询）"""
        try:
            client = self.tencent_client
            if not client.health_check():
                logger.warning("Tencent ASR credentials not configured, falling back to Whisper")
                return await self._process_whisper(session, audio_data)

            result = await client.transcribe(audio_data)
            return {
                "text": result["text"],
                "is_final": result["is_final"],
                "engine": "tencent",
                "confidence": result["confidence"],
                "task_id": result["task_id"],
            }
        except Exception as e:
            logger.error(f"Tencent ASR error: {e}")
            # 降级到 Whisper
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
