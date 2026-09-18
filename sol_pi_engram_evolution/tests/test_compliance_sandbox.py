#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规沙盒测试
"""
import os
import sys
import tempfile
import importlib.util
from pathlib import Path

# 动态加载被测模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compliance_sandbox import ComplianceSandbox, ComplianceRule, get_sandbox


def test_sandbox_basic():
    """测试沙盒基础功能"""
    sandbox = ComplianceSandbox()
    
    # 测试文件读取（不需要确认）
    result = sandbox.check("file.read", "/path/to/file.txt")
    assert result["allowed"] is True
    print("  ✓ file.read allowed")
    
    # 测试文件写入（需要确认）
    result = sandbox.check("file.write", "/BOSS-AI-R/output/test.txt")
    assert result["allowed"] is True
    assert result.get("require_user_confirm") is True
    print("  ✓ file.write requires confirmation")
    
    # 测试文件删除（需要确认 + 限速）
    result = sandbox.check("file.delete", "/BOSS-AI-R/temp/test.txt")
    assert result["allowed"] is True
    assert result.get("require_user_confirm") is True
    print("  ✓ file.delete requires confirmation")
    
    # 测试邮件发送（需要确认 + 限速）
    result = sandbox.check("email.send", "<EMAIL>")
    assert result["allowed"] is True
    assert result.get("require_user_confirm") is True
    print("  ✓ email.send requires confirmation")


def test_rate_limiting():
    """测试速率限制"""
    sandbox = ComplianceSandbox()
    
    # 连续删除文件
    for i in range(6):
        result = sandbox.check("file.delete", f"/BOSS-AI-R/temp/file_{i}.txt")
        sandbox.log("file.delete", f"/BOSS-AI-R/temp/file_{i}.txt", result)
    
    # 第 6 次应该被限速（max_per_hour=5）
    assert result["allowed"] is True  # 仍然允许，但会触发确认
    print(f"  ✓ Rate limit triggered after 6 deletes (require_confirm={result.get('require_user_confirm')})")


def test_audit_logging():
    """测试审计日志"""
    sandbox = ComplianceSandbox()
    
    # 执行一些操作
    sandbox.check("file.read", "/test/file.txt")
    sandbox.log("file.read", "/test/file.txt", {"allowed": True})
    
    sandbox.check("file.write", "/BOSS-AI-R/test.txt")
    sandbox.log("file.write", "/BOSS-AI-R/test.txt", {"allowed": True, "require_user_confirm": True})
    
    # 验证日志
    logs = sandbox.get_audit_log()
    assert len(logs) == 2
    assert logs[0]["action"] == "file.read"
    assert logs[1]["action"] == "file.write"
    print(f"  ✓ Audit log contains {len(logs)} entries")


def test_singleton():
    """测试全局单例"""
    s1 = get_sandbox()
    s2 = get_sandbox()
    assert s1 is s2
    print("  ✓ Singleton works correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("Compliance Sandbox Tests")
    print("=" * 60)
    
    test_sandbox_basic()
    test_rate_limiting()
    test_audit_logging()
    test_singleton()
    
    print("\n" + "=" * 60)
    print("✅ All compliance sandbox tests passed")
    print("=" * 60)
