#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
谈判工具适配器测试
"""
import os
import sys
import asyncio
import importlib.util

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from negotiation_adapters import (
    CRMAdapter, EmailAdapter, CalendarAdapter, ContractAdapter,
    NegotiationAdapterManager, get_adapter_manager
)


def test_crm_adapter():
    """测试 CRM 适配器"""
    adapter = CRMAdapter()
    
    # 测试 schema
    schema = adapter.get_schema()
    assert schema["name"] == "crm"
    assert "get_customer" in schema["actions"]
    print("  ✓ CRM schema valid")
    
    # 测试验证
    asyncio.run(adapter.validate("get_customer", {"customer_id": "123"}))
    print("  ✓ CRM validation works")


def test_email_adapter():
    """测试邮件适配器"""
    adapter = EmailAdapter()
    
    schema = adapter.get_schema()
    assert schema["name"] == "email"
    assert "send" in schema["actions"]
    print("  ✓ Email schema valid")
    
    # 测试验证失败
    result = asyncio.run(adapter.validate("send", {}))
    assert result is False
    print("  ✓ Email validation rejects missing params")


def test_calendar_adapter():
    """测试日历适配器"""
    adapter = CalendarAdapter()
    
    schema = adapter.get_schema()
    assert schema["name"] == "calendar"
    assert "create_event" in schema["actions"]
    print("  ✓ Calendar schema valid")


def test_contract_adapter():
    """测试合同适配器"""
    adapter = ContractAdapter()
    
    schema = adapter.get_schema()
    assert schema["name"] == "contract"
    assert "analyze" in schema["actions"]
    print("  ✓ Contract schema valid")


def test_adapter_manager():
    """测试适配器管理器"""
    manager = NegotiationAdapterManager()
    
    # 注册适配器
    manager.register("crm", CRMAdapter())
    manager.register("email", EmailAdapter())
    
    # 列出适配器
    adapters = manager.list_adapters()
    assert "crm" in adapters
    assert "email" in adapters
    print(f"  ✓ Manager lists {len(adapters)} adapters")
    
    # 获取适配器
    crm = manager.get("crm")
    assert crm is not None
    assert crm.name == "crm"
    print("  ✓ Manager.get() works")
    
    # 获取所有 schema
    schemas = manager.get_all_schemas()
    assert "crm" in schemas
    assert "email" in schemas
    print("  ✓ Manager.get_all_schemas() works")


def test_default_manager():
    """测试默认管理器"""
    manager = get_adapter_manager()
    
    # 验证默认适配器已注册
    assert "crm" in manager.list_adapters()
    assert "email" in manager.list_adapters()
    assert "calendar" in manager.list_adapters()
    assert "contract" in manager.list_adapters()
    print(f"  ✓ Default manager has {len(manager.list_adapters())} adapters")


if __name__ == "__main__":
    print("=" * 60)
    print("Negotiation Adapter Tests")
    print("=" * 60)
    
    test_crm_adapter()
    test_email_adapter()
    test_calendar_adapter()
    test_contract_adapter()
    test_adapter_manager()
    test_default_manager()
    
    print("\n" + "=" * 60)
    print("✅ All negotiation adapter tests passed")
    print("=" * 60)
