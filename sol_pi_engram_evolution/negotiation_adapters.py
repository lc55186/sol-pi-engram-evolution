#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
谈判工具适配器生态
统一接口适配 CRM/邮件/日历/合同/支付等谈判相关工具
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class ToolAdapter(ABC):
    """统一工具适配器接口"""
    
    @abstractmethod
    async def execute(self, action: str, params: dict) -> dict:
        """执行工具操作"""
        pass
    
    @abstractmethod
    async def validate(self, action: str, params: dict) -> bool:
        """验证操作参数"""
        pass
    
    @abstractmethod
    def get_schema(self) -> dict:
        """返回工具能力描述（给 LLM 调用）"""
        pass


class CRMAdapter(ToolAdapter):
    """CRM 系统适配器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.name = "crm"
    
    async def execute(self, action: str, params: dict) -> dict:
        actions = {
            "get_customer": self._get_customer,
            "update_customer": self._update_customer,
            "get_history": self._get_history,
        }
        handler = actions.get(action, self._unknown)
        return await handler(params)
    
    async def validate(self, action: str, params: dict) -> bool:
        if action == "get_customer":
            return "customer_id" in params
        return True
    
    def get_schema(self) -> dict:
        return {
            "name": "crm",
            "description": "CRM 客户管理系统",
            "actions": {
                "get_customer": {"params": {"customer_id": "string"}, "returns": "customer_info"},
                "update_customer": {"params": {"customer_id": "string", "data": "object"}, "returns": "success"},
                "get_history": {"params": {"customer_id": "string"}, "returns": "history_list"},
            }
        }
    
    async def _get_customer(self, params: dict) -> dict:
        return {"status": "mock", "customer": {"id": params.get("customer_id"), "name": "Mock Customer"}}
    
    async def _update_customer(self, params: dict) -> dict:
        return {"status": "mock", "updated": True}
    
    async def _get_history(self, params: dict) -> dict:
        return {"status": "mock", "history": []}
    
    async def _unknown(self, params: dict) -> dict:
        return {"error": "unknown_action"}


class EmailAdapter(ToolAdapter):
    """邮件系统适配器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.name = "email"
    
    async def execute(self, action: str, params: dict) -> dict:
        actions = {
            "send": self._send,
            "draft": self._draft,
        }
        handler = actions.get(action, self._unknown)
        return await handler(params)
    
    async def validate(self, action: str, params: dict) -> bool:
        if action == "send":
            return "to" in params and "subject" in params
        return True
    
    def get_schema(self) -> dict:
        return {
            "name": "email",
            "description": "邮件系统",
            "actions": {
                "send": {"params": {"to": "string", "subject": "string", "body": "string"}, "returns": "send_result"},
                "draft": {"params": {"to": "string", "subject": "string", "body": "string"}, "returns": "draft_id"},
            }
        }
    
    async def _send(self, params: dict) -> dict:
        return {"status": "mock", "message_id": "mock_123", "sent": True}
    
    async def _draft(self, params: dict) -> dict:
        return {"status": "mock", "draft_id": "draft_456"}
    
    async def _unknown(self, params: dict) -> dict:
        return {"error": "unknown_action"}


class CalendarAdapter(ToolAdapter):
    """日历系统适配器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.name = "calendar"
    
    async def execute(self, action: str, params: dict) -> dict:
        actions = {
            "create_event": self._create_event,
            "get_schedule": self._get_schedule,
        }
        handler = actions.get(action, self._unknown)
        return await handler(params)
    
    async def validate(self, action: str, params: dict) -> bool:
        if action == "create_event":
            return "title" in params and "start_time" in params
        return True
    
    def get_schema(self) -> dict:
        return {
            "name": "calendar",
            "description": "日历系统",
            "actions": {
                "create_event": {"params": {"title": "string", "start_time": "datetime", "end_time": "datetime"}, "returns": "event_id"},
                "get_schedule": {"params": {"date": "string"}, "returns": "events_list"},
            }
        }
    
    async def _create_event(self, params: dict) -> dict:
        return {"status": "mock", "event_id": "event_789"}
    
    async def _get_schedule(self, params: dict) -> dict:
        return {"status": "mock", "events": []}
    
    async def _unknown(self, params: dict) -> dict:
        return {"error": "unknown_action"}


class ContractAdapter(ToolAdapter):
    """合同系统适配器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.name = "contract"
    
    async def execute(self, action: str, params: dict) -> dict:
        actions = {
            "analyze": self._analyze,
            "get_risks": self._get_risks,
        }
        handler = actions.get(action, self._unknown)
        return await handler(params)
    
    async def validate(self, action: str, params: dict) -> bool:
        if action == "analyze":
            return "contract_text" in params
        return True
    
    def get_schema(self) -> dict:
        return {
            "name": "contract",
            "description": "合同审查系统",
            "actions": {
                "analyze": {"params": {"contract_text": "string"}, "returns": "analysis_result"},
                "get_risks": {"params": {"contract_text": "string"}, "returns": "risks_list"},
            }
        }
    
    async def _analyze(self, params: dict) -> dict:
        return {"status": "mock", "risk_level": "medium", "issues": []}
    
    async def _get_risks(self, params: dict) -> dict:
        return {"status": "mock", "risks": []}
    
    async def _unknown(self, params: dict) -> dict:
        return {"error": "unknown_action"}


class NegotiationAdapterManager:
    """谈判工具适配器管理器"""
    
    def __init__(self):
        self._adapters: Dict[str, ToolAdapter] = {}
    
    def register(self, name: str, adapter: ToolAdapter):
        self._adapters[name] = adapter
    
    def get(self, name: str) -> Optional[ToolAdapter]:
        return self._adapters.get(name)
    
    def list_adapters(self) -> List[str]:
        return list(self._adapters.keys())
    
    def get_all_schemas(self) -> Dict[str, dict]:
        return {name: adapter.get_schema() for name, adapter in self._adapters.items()}
    
    async def execute(self, adapter_name: str, action: str, params: dict) -> dict:
        adapter = self.get(adapter_name)
        if not adapter:
            return {"error": f"adapter_not_found: {adapter_name}"}
        
        if not await adapter.validate(action, params):
            return {"error": "validation_failed"}
        
        return await adapter.execute(action, params)


# 全局单例
_manager: Optional[NegotiationAdapterManager] = None

def get_adapter_manager() -> NegotiationAdapterManager:
    global _manager
    if _manager is None:
        _manager = NegotiationAdapterManager()
        # 注册默认适配器
        _manager.register("crm", CRMAdapter())
        _manager.register("email", EmailAdapter())
        _manager.register("calendar", CalendarAdapter())
        _manager.register("contract", ContractAdapter())
    return _manager
