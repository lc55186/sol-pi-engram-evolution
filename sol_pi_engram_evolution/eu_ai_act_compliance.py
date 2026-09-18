#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EU AI Act 合规模块
响应 2026年8月2日 EU AI Act 全面执行
高风险AI系统合规路径
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("eu_ai_act")


class EUAIActCompliance:
    """EU AI Act 合规检查器"""
    
    # 高风险AI系统分类（Annex III）
    HIGH_RISK_CATEGORIES = [
        "biometric_identification",
        "critical_infrastructure",
        "education_vocational",
        "employment_workers",
        "law_enforcement",
        "migration_asylum",
        "administration_of_justice",
    ]
    
    # 合规要求
    COMPLIANCE_REQUIREMENTS = {
        "risk_management": "建立风险管理体系",
        "data_governance": "训练数据治理",
        "technical_documentation": "技术文档",
        "record_keeping": "记录保存（日志）",
        "transparency": "透明度与信息提供",
        "human_oversight": "人类监督",
        "accuracy_robustness": "准确性、鲁棒性和网络安全",
    }
    
    def __init__(self):
        self.audit_trail: List[Dict] = []
    
    def classify_system(self, system_type: str) -> Dict:
        """分类AI系统风险等级"""
        is_high_risk = system_type in self.HIGH_RISK_CATEGORIES
        
        return {
            "system_type": system_type,
            "risk_level": "high" if is_high_risk else "limited",
            "requirements": list(self.COMPLIANCE_REQUIREMENTS.keys()) if is_high_risk else ["transparency"],
            "conformity_assessment": "required" if is_high_risk else "self_assessment",
        }
    
    def generate_compliance_checklist(self, system_type: str) -> List[Dict]:
        """生成合规检查清单"""
        classification = self.classify_system(system_type)
        checklist = []
        
        for req_key, req_desc in self.COMPLIANCE_REQUIREMENTS.items():
            if req_key in classification["requirements"]:
                checklist.append({
                    "requirement": req_key,
                    "description": req_desc,
                    "status": "pending",
                    "evidence_required": True,
                })
        
        return checklist
    
    def log_decision(self, decision_id: str, inputs: Dict, outputs: Dict,
                     human_oversight: bool = False):
        """记录AI决策（透明度要求）"""
        entry = {
            "decision_id": decision_id,
            "timestamp": datetime.now().isoformat(),
            "inputs": inputs,
            "outputs": outputs,
            "human_oversight": human_oversight,
            "explanation": outputs.get("explanation", ""),
        }
        self.audit_trail.append(entry)
        return entry
    
    def get_audit_trail(self, limit: int = 100) -> List[Dict]:
        """获取审计追踪"""
        return self.audit_trail[-limit:]
    
    def generate_transparency_report(self) -> Dict:
        """生成透明度报告"""
        total = len(self.audit_trail)
        human_oversight_count = sum(1 for e in self.audit_trail if e.get("human_oversight"))
        
        return {
            "report_date": datetime.now().isoformat(),
            "total_decisions": total,
            "human_oversight_rate": human_oversight_count / max(total, 1),
            "audit_trail_available": True,
            "data_retention_days": 365,
        }


_compliance: Optional[EUAIActCompliance] = None

def get_eu_ai_act_compliance() -> EUAIActCompliance:
    global _compliance
    if _compliance is None:
        _compliance = EUAIActCompliance()
    return _compliance
