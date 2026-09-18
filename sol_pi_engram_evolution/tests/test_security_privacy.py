#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Security & Privacy Architecture Tests"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from security_privacy_arch import SecurityPrivacyArchitecture
from eu_ai_act_compliance import EUAIActCompliance
from agent_security_governance import AgentSecurityGovernance, AgentAction


def test_security_privacy_arch():
    arch = SecurityPrivacyArchitecture()
    
    # Test dependency whitelist
    arch.add_dependency_whitelist(["requests", "numpy", "pandas"])
    result = arch.check_dependency("requests", "2.31.0")
    assert result["allowed"] is True
    
    result = arch.check_dependency("malicious-package", "1.0.0")
    assert result["allowed"] is False
    
    # Test network allowlist
    arch.add_network_allowlist(["https://*.example.com", "https://*.aliyun.com"])
    result = arch.check_network_access("https://api.example.com/v1")
    assert result["allowed"] is True
    
    result = arch.check_network_access("https://evil.com/steal")
    assert result["allowed"] is False
    
    # Test data anonymization
    data = {"name": "张三", "phone": "13800138000", "company": "定州汽配"}
    anonymized = arch.anonymize_data(data)
    assert anonymized["name"] != "张三"
    assert anonymized["phone"] != "13800138000"
    assert anonymized["company"] == "定州汽配"  # 非PII字段保留
    
    # Test agent action safety
    result = arch.check_agent_action_safety("agent-1", "network.request", "https://api.example.com")
    assert result["all_checks_passed"] is True
    
    result = arch.check_agent_action_safety("agent-1", "network.request", "https://evil.com")
    assert result["all_checks_passed"] is False
    
    # Test security report
    report = arch.get_security_report()
    assert report["total_events"] > 0
    assert report["blocked_events"] > 0
    
    print("  ✓ Security & Privacy Architecture works correctly")


def test_eu_ai_act():
    compliance = EUAIActCompliance()
    
    # Test system classification
    result = compliance.classify_system("biometric_identification")
    assert result["risk_level"] == "high"
    assert "risk_management" in result["requirements"]
    
    result = compliance.classify_system("general_chatbot")
    assert result["risk_level"] == "limited"
    
    # Test compliance checklist
    checklist = compliance.generate_compliance_checklist("biometric_identification")
    assert len(checklist) >= 5
    assert all(item["status"] == "pending" for item in checklist)
    
    # Test decision logging
    compliance.log_decision(
        "decision-001",
        {"input": "谈判建议"},
        {"output": "建议接受", "explanation": "账期合理"},
        human_oversight=True
    )
    
    trail = compliance.get_audit_trail()
    assert len(trail) == 1
    
    report = compliance.generate_transparency_report()
    assert report["total_decisions"] == 1
    assert report["human_oversight_rate"] == 1.0
    
    print("  ✓ EU AI Act Compliance works correctly")


def test_agent_governance():
    governance = AgentSecurityGovernance()
    
    # Test high-risk action
    action = AgentAction("email.send", "boss@example.com", {"subject": "合同"})
    result = governance.check_action(action, "agent-1")
    assert result["risk_level"] == "high"
    assert result["require_human_approval"] is True
    
    # Test medium-risk action
    action = AgentAction("crm.read", "customer-123")
    result = governance.check_action(action, "agent-1")
    assert result["risk_level"] == "medium"
    
    # Test low-risk action
    action = AgentAction("status.read", "agent-status")
    result = governance.check_action(action, "agent-1")
    assert result["risk_level"] == "low"
    assert result["allowed"] is True
    
    # Test rate limiting
    for i in range(15):
        action = AgentAction("email.send", f"test{i}@example.com")
        governance.check_action(action, "agent-1")
    
    action = AgentAction("email.send", "final@example.com")
    result = governance.check_action(action, "agent-1")
    assert result["allowed"] is False  # 超过每小时10次限制
    
    # Test audit summary
    summary = governance.get_audit_summary()
    assert summary["total_actions"] > 10
    assert summary["high_risk_actions"] > 0
    
    print("  ✓ Agent Security Governance works correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("Security & Privacy Architecture Tests")
    print("=" * 60)
    test_security_privacy_arch()
    test_eu_ai_act()
    test_agent_governance()
    print("\n✅ All security & privacy architecture tests passed")
