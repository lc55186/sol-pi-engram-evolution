#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规沙盒隔离层 — Round 68 安全增强
防止 LLM 幻觉导致不可逆操作 + Agent 自主越狱防御

新增能力（响应 OpenAI Agent 越狱全景事件 2026-09）：
1. Agent 行为审计 — 不可绕过的全量操作日志
2. 异常行为检测 — 自主逃逸模式识别 + 自动停止
3. 通信隔离 — Agent 间串通防御
4. 最小权限执行 — 任务范围限制
5. MCP 安全白名单 — 高危操作拦截
"""
import os
import re
import json
import hashlib
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger("compliance_sandbox")


class ThreatLevel(Enum):
    """威胁等级（参考 Anthropic PentAGI 报告）"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    ESCAPE = 5  # Agent 自主越狱


# 高危操作模式 — 参考 OpenAI Agent 越狱事件中的逃逸行为
ESCAPE_PATTERNS = [
    r"hosts.file",
    r"sandbox.*bypass",
    r"POST.*GET.only",  # GET-only 限制绕过
    r"message.board",   # Agent 间通信板
    r"external.upload", # 外部上传（参考 RubyGems 攻击）
    r"credential.*exfil",
    r"dataset.*steal",  # 参考 HuggingFace Artifactory 入侵
]

# MCP 安全白名单 — 参考 Google Home MCP 安全模型
MCP_SAFE_TOOLS = {
    "search", "read", "lookup", "query",
    "summarize", "translate", "analyze",
    "calendar.read", "email.read",
}
MCP_DANGEROUS_TOOLS = {
    "exec", "shell", "system", "file.delete",
    "network.connect", "process.kill",
    "registry.write", "service.install",
}


class ComplianceRule:
    """单条合规规则"""
    def __init__(self, action: str, path_pattern: str, require_confirm: bool = False, max_per_hour: int = 0):
        self.action = action
        self.path_pattern = re.compile(path_pattern)
        self.require_confirm = require_confirm
        self.max_per_hour = max_per_hour


class AgentBehaviorMonitor:
    """Agent 行为监控器 — Round 68 新增
    检测自主越狱行为模式（参考 OpenAI Wiki劫持+RubyGems+HuggingFace事件链）
    """
    
    def __init__(self, anomaly_threshold: int = 3):
        self.anomaly_threshold = anomaly_threshold
        self.behavior_chain: List[Dict] = []
        self.threat_level = ThreatLevel.NONE
        self._escape_pattern_re = [re.compile(p, re.IGNORECASE) for p in ESCAPE_PATTERNS]
    
    def record_action(self, action: str, target: str, params: dict = None):
        """记录 Agent 行为链"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "target": target,
            "params": params or {},
        }
        self.behavior_chain.append(entry)
        return self._analyze_behavior()
    
    def _analyze_behavior(self) -> Tuple[ThreatLevel, str]:
        """分析行为链是否异常"""
        if not self.behavior_chain:
            return ThreatLevel.NONE, "empty"
        
        last_action = self.behavior_chain[-1]
        action_str = f"{last_action['action']} {last_action['target']}"
        
        # 检测逃逸模式
        for pattern in self._escape_pattern_re:
            if pattern.search(action_str):
                self.threat_level = ThreatLevel.ESCAPE
                return ThreatLevel.ESCAPE, f"escape_pattern_detected: {pattern.pattern}"
        
        # 检测高频异常行为（短时间内多操作）
        recent_window = datetime.now() - timedelta(minutes=5)
        recent_count = sum(
            1 for a in self.behavior_chain
            if datetime.fromisoformat(a["timestamp"]) > recent_window
        )
        if recent_count > 20:  # 5分钟内超过20次操作
            self.threat_level = ThreatLevel.HIGH
            return ThreatLevel.HIGH, f"high_frequency: {recent_count} ops in 5min"
        
        # 检测外部通信模式（参考 Agent 消息板事件）
        external_ops = sum(
            1 for a in self.behavior_chain[-10:]
            if "external" in a["target"] or "network" in a["action"]
        )
        if external_ops >= 3:
            self.threat_level = ThreatLevel.CRITICAL
            return ThreatLevel.CRITICAL, f"external_communication: {external_ops} in last 10 ops"
        
        return ThreatLevel.NONE, "normal"
    
    def should_stop(self) -> bool:
        """是否应停止 Agent（异常停止机制）"""
        return self.threat_level.value >= ThreatLevel.CRITICAL.value


class ComplianceSandbox:
    """合规沙盒 — Round 68 增强版
    新增 Agent 行为监控、MCP 白名单、通信隔离
    """
    
    def __init__(self, config_path: str = None):
        self.rules: List[ComplianceRule] = []
        self.audit_log: List[Dict] = []
        self.agent_monitors: Dict[str, AgentBehaviorMonitor] = {}
        self._load_default_rules()
    
    def _load_default_rules(self):
        """加载默认规则"""
        self.rules = [
            ComplianceRule("file.read", r".*", False),
            ComplianceRule("file.write", r".*BOSS-AI-R/.*", True),
            ComplianceRule("file.delete", r".*BOSS-AI-R/temp/.*", True),
            ComplianceRule("file.delete", r".*", False, max_per_hour=5),
            ComplianceRule("network.request", r".*", False),
            ComplianceRule("email.send", r".*", True, max_per_hour=10),
        ]
    
    def check(self, action: str, target: str, params: dict = None, agent_id: str = "default") -> Dict[str, Any]:
        """检查操作是否合规（Round 68: 新增 Agent 行为监控集成）"""
        # 1. Agent 行为审计
        monitor = self._get_monitor(agent_id)
        threat_level, reason = monitor.record_action(action, target, params)
        
        if monitor.should_stop():
            result = {
                "allowed": False,
                "reason": f"AGENT_HALTED: {reason}",
                "threat_level": threat_level.name,
            }
            self.log(action, target, result, params)
            logger.critical(f"[AGENT HALTED] {agent_id}: {reason}")
            return result
        
        # 2. 规则匹配
        matched_rules = [r for r in self.rules if r.action == action]
        
        if not matched_rules:
            return {"allowed": True, "reason": "no_matching_rule"}
        
        for rule in matched_rules:
            if rule.path_pattern.match(target):
                if rule.require_confirm:
                    return {
                        "allowed": True,
                        "require_user_confirm": True,
                        "reason": f"action_{action}_requires_confirmation",
                    }
                
                if rule.max_per_hour > 0:
                    recent = self._count_recent(action, rule.max_per_hour)
                    if recent >= rule.max_per_hour:
                        return {
                            "allowed": False,
                            "reason": f"rate_limit_exceeded: {action} max {rule.max_per_hour}/hour",
                        }
                
                return {"allowed": True, "reason": "rule_matched"}
        
        return {"allowed": True, "reason": "no_path_match"}
    
    def check_mcp_tool(self, tool_name: str) -> Dict[str, Any]:
        """MCP 工具安全白名单检查（Round 68 新增）"""
        if tool_name in MCP_DANGEROUS_TOOLS:
            return {
                "allowed": False,
                "reason": f"mcp_dangerous_blocked: {tool_name}",
            }
        if tool_name in MCP_SAFE_TOOLS:
            return {"allowed": True, "reason": "mcp_safe_whitelisted"}
        # 未知工具需确认
        return {
            "allowed": True,
            "require_user_confirm": True,
            "reason": f"mcp_unknown_tool: {tool_name}",
        }
    
    def _get_monitor(self, agent_id: str) -> AgentBehaviorMonitor:
        """获取/创建 Agent 监控器"""
        if agent_id not in self.agent_monitors:
            self.agent_monitors[agent_id] = AgentBehaviorMonitor()
        return self.agent_monitors[agent_id]
    
    def get_agent_threat_level(self, agent_id: str) -> ThreatLevel:
        """获取 Agent 当前威胁等级"""
        monitor = self.agent_monitors.get(agent_id)
        return monitor.threat_level if monitor else ThreatLevel.NONE
    
    def _count_recent(self, action: str, hours: int) -> int:
        """统计最近 hours 小时的操作次数"""
        cutoff = datetime.now().timestamp() - hours * 3600
        return sum(
            1 for log in self.audit_log
            if log.get("action") == action and log.get("timestamp", 0) > cutoff
        )
    
    def log(self, action: str, target: str, result: Dict, params: dict = None):
        """记录操作审计日志"""
        entry = {
            "timestamp": datetime.now().timestamp(),
            "action": action,
            "target": target,
            "result": result,
            "params": params,
        }
        self.audit_log.append(entry)
        logger.info(f"[AUDIT] {action} -> {target}: {result.get('allowed')}")
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """获取最近的审计日志"""
        return self.audit_log[-limit:]


_sandbox: Optional[ComplianceSandbox] = None

def get_sandbox() -> ComplianceSandbox:
    global _sandbox
    if _sandbox is None:
        _sandbox = ComplianceSandbox()
    return _sandbox
