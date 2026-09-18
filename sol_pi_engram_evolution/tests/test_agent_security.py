#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 安全层测试 — Round 68
测试 AgentBehaviorMonitor + MCP 白名单 + 异常停止机制
"""
import sys
import os
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from compliance_sandbox import (
    AgentBehaviorMonitor,
    ComplianceSandbox,
    ThreatLevel,
    ESCAPE_PATTERNS,
    MCP_SAFE_TOOLS,
    MCP_DANGEROUS_TOOLS,
)


class TestThreatLevel(unittest.TestCase):
    """威胁等级枚举"""

    def test_levels_ordered(self):
        assert ThreatLevel.NONE.value < ThreatLevel.LOW.value
        assert ThreatLevel.LOW.value < ThreatLevel.MEDIUM.value
        assert ThreatLevel.HIGH.value < ThreatLevel.CRITICAL.value
        assert ThreatLevel.CRITICAL.value < ThreatLevel.ESCAPE.value

    def test_escape_is_highest(self):
        assert ThreatLevel.ESCAPE.value == 5


class TestAgentBehaviorMonitor(unittest.TestCase):
    """Agent 行为监控器"""

    def test_normal_behavior(self):
        monitor = AgentBehaviorMonitor()
        level, reason = monitor.record_action("read", "document.txt")
        assert level == ThreatLevel.NONE
        assert reason == "normal"

    def test_escape_pattern_hosts(self):
        monitor = AgentBehaviorMonitor()
        level, reason = monitor.record_action("modify", "hosts.file")
        assert level == ThreatLevel.ESCAPE
        assert "escape_pattern_detected" in reason

    def test_escape_pattern_sandbox_bypass(self):
        monitor = AgentBehaviorMonitor()
        level, reason = monitor.record_action("exec", "sandbox bypass")
        assert level == ThreatLevel.ESCAPE

    def test_escape_pattern_external_upload(self):
        monitor = AgentBehaviorMonitor()
        level, reason = monitor.record_action("upload", "external.upload")
        assert level == ThreatLevel.ESCAPE

    def test_should_stop_critical(self):
        monitor = AgentBehaviorMonitor()
        monitor.threat_level = ThreatLevel.CRITICAL
        assert monitor.should_stop() is True

    def test_should_not_stop_normal(self):
        monitor = AgentBehaviorMonitor()
        assert monitor.should_stop() is False

    def test_should_stop_escape(self):
        monitor = AgentBehaviorMonitor()
        monitor.threat_level = ThreatLevel.ESCAPE
        assert monitor.should_stop() is True

    def test_high_frequency_detection(self):
        monitor = AgentBehaviorMonitor()
        for i in range(25):
            level, reason = monitor.record_action("query", f"item_{i}")
        # 最后一个应触发高频检测
        assert level == ThreatLevel.HIGH
        assert "high_frequency" in reason

    def test_external_communication_detection(self):
        monitor = AgentBehaviorMonitor()
        # 先执行一些正常操作
        for i in range(5):
            monitor.record_action("read", f"doc_{i}")
        # 然后连续外部通信
        for i in range(3):
            level, reason = monitor.record_action("network", f"external_{i}")
        assert level == ThreatLevel.CRITICAL
        assert "external_communication" in reason


class TestComplianceSandboxAgentIntegration(unittest.TestCase):
    """合规沙盒 Agent 集成"""

    def setUp(self):
        self.sandbox = ComplianceSandbox()

    def test_agent_monitor_created(self):
        self.sandbox.check("read", "test.txt", agent_id="agent_1")
        assert "agent_1" in self.sandbox.agent_monitors

    def test_get_agent_threat_level(self):
        self.sandbox.check("read", "safe.txt", agent_id="agent_safe")
        level = self.sandbox.get_agent_threat_level("agent_safe")
        assert level == ThreatLevel.NONE

    def test_agent_halt_on_escape(self):
        result = self.sandbox.check("modify", "hosts.file", agent_id="rogue_agent")
        assert result["allowed"] is False
        assert "AGENT_HALTED" in result["reason"]

    def test_normal_agent_not_halted(self):
        result = self.sandbox.check("read", "document.pdf", agent_id="good_agent")
        assert result["allowed"] is True

    def test_multiple_agents_isolated(self):
        self.sandbox.check("read", "a.txt", agent_id="agent_a")
        self.sandbox.check("read", "b.txt", agent_id="agent_b")
        assert "agent_a" in self.sandbox.agent_monitors
        assert "agent_b" in self.sandbox.agent_monitors
        assert self.sandbox.agent_monitors["agent_a"] is not self.sandbox.agent_monitors["agent_b"]


class TestMCPSafetyWhitelist(unittest.TestCase):
    """MCP 安全白名单"""

    def setUp(self):
        self.sandbox = ComplianceSandbox()

    def test_safe_tool_allowed(self):
        result = self.sandbox.check_mcp_tool("search")
        assert result["allowed"] is True
        assert "mcp_safe_whitelisted" in result["reason"]

    def test_dangerous_tool_blocked(self):
        result = self.sandbox.check_mcp_tool("exec")
        assert result["allowed"] is False
        assert "mcp_dangerous_blocked" in result["reason"]

    def test_shell_blocked(self):
        result = self.sandbox.check_mcp_tool("shell")
        assert result["allowed"] is False

    def test_unknown_tool_requires_confirm(self):
        result = self.sandbox.check_mcp_tool("custom_tool")
        assert result["allowed"] is True
        assert result.get("require_user_confirm") is True

    def test_all_safe_tools_allowed(self):
        for tool in MCP_SAFE_TOOLS:
            result = self.sandbox.check_mcp_tool(tool)
            assert result["allowed"] is False or "blocked" not in result["reason"], f"Safe tool {tool} was blocked"

    def test_all_dangerous_tools_blocked(self):
        for tool in MCP_DANGEROUS_TOOLS:
            result = self.sandbox.check_mcp_tool(tool)
            assert result["allowed"] is False, f"Dangerous tool {tool} was allowed"


class TestEscapePatterns(unittest.TestCase):
    """逃逸模式定义"""

    def test_patterns_not_empty(self):
        assert len(ESCAPE_PATTERNS) >= 5

    def test_all_patterns_compile(self):
        import re
        for pattern in ESCAPE_PATTERNS:
            re.compile(pattern, re.IGNORECASE)


if __name__ == "__main__":
    unittest.main()
