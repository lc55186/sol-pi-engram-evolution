#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合规沙盒隔离层
防止 LLM 幻觉导致不可逆操作
"""
import os
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger("compliance_sandbox")


class ComplianceRule:
    """单条合规规则"""
    def __init__(self, action: str, path_pattern: str, require_confirm: bool = False, max_per_hour: int = 0):
        self.action = action
        self.path_pattern = re.compile(path_pattern)
        self.require_confirm = require_confirm
        self.max_per_hour = max_per_hour


class ComplianceSandbox:
    """合规沙盒"""
    
    def __init__(self, config_path: str = None):
        self.rules: List[ComplianceRule] = []
        self.audit_log: List[Dict] = []
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
    
    def check(self, action: str, target: str, params: dict = None) -> Dict[str, Any]:
        """检查操作是否合规"""
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
