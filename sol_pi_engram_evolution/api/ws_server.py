#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Server - BOSS-AI-R 实时通信服务器
支持：音频流传输、转写结果下发、预警推送
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Optional, Set
from dataclasses import dataclass, field

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("ws_server")


@dataclass
class ClientConnection:
    """客户端连接"""
    websocket: WebSocket
    client_id: str
    session_id: Optional[str] = None
    connected_at: float = 0.0
    last_activity: float = 0.0
    is_recording: bool = False


class ConnectionManager:
    """连接管理器"""
    def __init__(self):
        self.active_connections: Dict[str, ClientConnection] = {}
        self.sessions: Dict[str, Set[str]] = {}  # session_id → {client_id}

    async def connect(self, websocket: WebSocket, client_id: str) -> ClientConnection:
        await websocket.accept()
        conn = ClientConnection(
            websocket=websocket,
            client_id=client_id,
            connected_at=time.time(),
            last_activity=time.time()
        )
        self.active_connections[client_id] = conn
        logger.info(f"Client {client_id} connected")
        return conn

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            conn = self.active_connections[client_id]
            # 清理会话
            if conn.session_id and conn.session_id in self.sessions:
                self.sessions[conn.session_id].discard(client_id)
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected")

    async def send_to_client(self, client_id: str, message: dict):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].websocket.send_json(message)
            except Exception as e:
                logger.error(f"Send to {client_id} failed: {e}")
                self.disconnect(client_id)

    async def broadcast_to_session(self, session_id: str, message: dict):
        if session_id in self.sessions:
            for client_id in self.sessions[session_id]:
                await self.send_to_client(client_id, message)


class BOSSAIRServer:
    """BOSS-AI-R WebSocket 服务器"""

    def __init__(self):
        self.app = FastAPI(title="BOSS-AI-R Server", version="0.1.0")
        self.manager = ConnectionManager()
        self.setup_routes()

    def setup_routes(self):
        @self.app.websocket("/ws/{client_id}")
        async def websocket_endpoint(websocket: WebSocket, client_id: str):
            conn = await self.manager.connect(websocket, client_id)
            try:
                while True:
                    data = await websocket.receive_json()
                    await self.handle_message(conn, data)
            except WebSocketDisconnect:
                self.manager.disconnect(client_id)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                self.manager.disconnect(client_id)

        @self.app.get("/health")
        async def health():
            return {
                "status": "ok",
                "active_connections": len(self.manager.active_connections),
                "active_sessions": len(self.manager.sessions)
            }

    async def handle_message(self, conn: ClientConnection, data: dict):
        """处理客户端消息"""
        msg_type = data.get("type")
        conn.last_activity = time.time()

        if msg_type == "start_session":
            await self.handle_start_session(conn, data)
        elif msg_type == "audio_frame":
            await self.handle_audio_frame(conn, data)
        elif msg_type == "stop_session":
            await self.handle_stop_session(conn, data)
        elif msg_type == "ping":
            await self.manager.send_to_client(conn.client_id, {"type": "pong"})

    async def handle_start_session(self, conn: ClientConnection, data: dict):
        """开始录音会话"""
        session_id = data.get("session_id", str(uuid.uuid4()))
        scenario = data.get("scenario", "汽配贸易")
        engine = data.get("engine", "whisper")

        conn.session_id = session_id
        conn.is_recording = True

        # 注册会话
        if session_id not in self.manager.sessions:
            self.manager.sessions[session_id] = set()
        self.manager.sessions[session_id].add(conn.client_id)

        # 确认
        await self.manager.send_to_client(conn.client_id, {
            "type": "session_started",
            "session_id": session_id,
            "scenario": scenario,
            "engine": engine
        })

        logger.info(f"Session {session_id} started (scenario={scenario})")

    async def handle_audio_frame(self, conn: ClientConnection, data: dict):
        """处理音频帧"""
        if not conn.is_recording:
            return

        # TODO: 调用 ASR 处理
        # 临时回显
        await self.manager.send_to_client(conn.client_id, {
            "type": "transcript",
            "text": "[转写中...]",
            "is_final": False
        })

    async def handle_stop_session(self, conn: ClientConnection, data: dict):
        """停止录音会话"""
        conn.is_recording = False

        await self.manager.send_to_client(conn.client_id, {
            "type": "session_stopped",
            "session_id": conn.session_id
        })

        logger.info(f"Session {conn.session_id} stopped")


def create_server() -> FastAPI:
    """创建服务器"""
    server = BOSSAIRServer()
    server.app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return server.app


if __name__ == "__main__":
    import uvicorn
    app = create_server()
    uvicorn.run(app, host="0.0.0.0", port=8000)
