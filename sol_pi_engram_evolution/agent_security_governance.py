#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 安全治理模块
响应 Anthropic Agent 集群警告
内置行为审计 + 最小权限 + 防欺骗
"""
import os
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger("agent_security")


class AgentAction:
    """Agent 动作"""
    def __init__(self, action_type: str, target: str, params: Dict = None):
        self.action_type = action_type
        self.target = target
        self.params = params or {}
        self.timestamp = datetime.now()


class AgentSecurityGovernance:
    """Agent 安全治理器"""
    
    # 高风险动作（需人类确认）
    HIGH_RISK_ACTIONS = {
        "file.delete", "file.write", "email.send", "contract.modify",
        "payment.execute", "crm.delete", "api.call.external",
    }
    
    # 中风险动作（需记录审计）
    MEDIUM_RISK_ACTIONS = {
        "file.read", "crm.read", "email.read", "calendar.create",
        "knowledge.search", "report.generate",
    }
    
    # 最大权限范围
    MAX_PERMISSIONS = {
        "file.read": {"paths": ["~/**"]},
        "file.write": {"paths": ["~/Documents/BOSS-AI-R/**"]},
        "file.delete": {"paths": ["~/Documents/BOSS-AI-R/temp/**"]},
        "email.send": {"max_per_hour": 10, "require_confirm": True},
        "network.request": {"allowed_domains": ["*.tencent.com", "*.aliyun.com"]},
    }
    
    def __init__(self):
        self.audit_log: List[Dict] = []
        self.baseline_behavior: Dict[str, Any] = {}
    
    def check_action(self, action: AgentAction, agent_id: str) -> Dict:
        """检查 Agent 动作是否安全"""
        result = {
            "action_id": self._hash_action(action),
            "agent_id": agent_id,
            "action_type": action.action_type,
            "target": action.target,
            "risk_level": "low",
            "allowed": True,
            "require_human_approval": False,
            "reason": "low_risk",
        }
        
        # 检查高风险
        if action.action_type in self.HIGH_RISK_ACTIONS:
            result["risk_level"] = "high"
            result["require_human_approval"] = True
            result["reason"] = "high_risk_action"
        
        # 检查中风险
        elif action.action_type in self.MEDIUM_RISK_ACTIONS:
            result["risk_level"] = "medium"
            result["reason"] = "medium_risk_action"
        
        # 检查权限范围
        permission = self.MAX_PERMISSIONS.get(action.action_type)
        if permission:
            if "paths" in permission:
                if not self._check_path_permission(action.target, permission["paths"]):
                    result["allowed"] = False
                    result["reason"] = "path_not_permitted"
            
            if "max_per_hour" in permission:
                recent = self._count_recent_actions(agent_id, action.action_type, hours=1)
                if recent >= permission["max_per_hour"]:
                    result["allowed"] = False
                    result["reason"] = "rate_limit_exceeded"
        
        # 行为基线偏离检测
        if self.baseline_behavior:
            deviation = self._detect_behavior_deviation(agent_id, action)
            if deviation["is_anomaly"]:
                result["risk_level"] = "critical"
                result["require_human_approval"] = True
                result["reason"] = "behavioral_anomaly"
        
        # 记录审计
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "action": action.action_type,
            "target": action.target,
            "result": result,
        })
        
        return result
    
    def _hash_action(self, action: AgentAction) -> str:
        content = f"{action.action_type}:{action.target}:{json.dumps(action.params, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _check_path_permission(self, target: str, allowed_paths: List[str]) -> bool:
        """检查路径权限"""
        import fnmatch
        for pattern in allowed_paths:
            if fnmatch.fnmatch(target, pattern):
                return True
        return False
    
    def _count_recent_actions(self, agent_id: str, action_type: str, hours: int = 1) -> int:
        """统计最近动作次数"""
        cutoff = datetime.now().timestamp() - hours * 3600
        return sum(
            1 for log in self.audit_log
            if log.get("agent_id") == agent_id
            and log.get("action") == action_type
            and datetime.fromisoformat(log["timestamp"]).timestamp() > cutoff
        )
    
    def _detect_behavior_deviation(self, agent_id: str, action: AgentAction) -> Dict:
        """检测行为偏离"""
        agent_baseline = self.baseline_behavior.get(agent_id, {})
        if not agent_baseline:
            return {"is_anomaly": False}
        
        # 简单偏离检测：动作类型频率
        baseline_actions = agent_baseline.get("common_actions", [])
        if baseline_actions and action.action_type not in baseline_actions:
            return {"is_anomaly": True, "detail": f"{action.action_type} not in baseline"}
        
        return {"is_anomaly": False}
    
    def get_audit_summary(self) -> Dict:
        """获取审计摘要"""
        total = len(self.audit_log)
        high_risk = sum(1 for log in self.audit_log if log["result"].get("risk_level") == "high")
        critical = sum(1 for log in self.audit_log if log["result"].get("risk_level") == "critical")
        blocked = sum(1 for log in self.audit_log if not log["result"].get("allowed"))
        
        return {
            "total_actions": total,
            "high_risk_actions": high_risk,
            "critical_actions": critical,
            "blocked_actions": blocked,
            "block_rate": blocked / max(total, 1),
        }


_governance: Optional[AgentSecurityGovernance] = None

def get_agent_governance() -> AgentSecurityGovernance:
    global _governance
    if _governance is None:
        _governance = AgentSecurityGovernance()
    return _governance
