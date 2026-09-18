#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Supply chain audit, XConf calibration, Agora collaboration tests"""
import os
import sys
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from supply_chain_audit import SupplyChainAuditor
from xconf_calibration import XConfCalibrator
from agora_collaboration import AgoraCollaboration


def test_supply_chain():
    auditor = SupplyChainAuditor()
    
    # Test vulnerable Dockerfile
    vuln_dockerfile = (
        "FROM python:3.11\n"
        "RUN pip install requests\n"
        "ENV API_KEY=sk-1234567890abcdef1234567890abcdef\n"
        "COPY . /app\n"
        'CMD ["python", "app.py"]'
    )
    
    result = auditor.scan_dockerfile(vuln_dockerfile)
    assert result["risk_score"] > 0
    assert result["recommendation"] == "FAIL"
    
    # Test secure Dockerfile
    secure_dockerfile = (
        "FROM python:3.11\n"
        "RUN pip install requests\n"
        "RUN --mount=type=secret,id=api_key cat /run/secrets/api_key > /app/key.txt\n"
        "COPY --chown=user . /app\n"
        'CMD ["python", "app.py"]'
    )
    
    result = auditor.scan_dockerfile(secure_dockerfile)
    assert result["uses_buildkit_secret"] is True
    
    print("  ✓ Supply chain audit works correctly")


def test_xconf():
    calibrator = XConfCalibrator(history_path=tempfile.mktemp())
    
    # Record some episodes
    calibrator.record_episode("汽配账期谈判 60天", "建议接受", 0.9, False)
    calibrator.record_episode("汽配账期谈判 45天", "建议接受", 0.8, True)
    calibrator.record_episode("体育器材订货 100万", "建议跟进", 0.7, True)
    calibrator.record_episode("再生资源扣杂争议", "建议让步", 0.6, True)
    
    # Calibrate new prediction
    result = calibrator.calibrate_confidence("汽配账期谈判 50天", 0.85)
    assert "calibrated_confidence" in result
    assert result["method"] == "xconf_beta_blend"
    
    stats = calibrator.get_calibration_stats()
    assert stats["total_episodes"] == 4
    
    print("  ✓ XConf calibration works correctly")
    os.unlink(calibrator.history_path)


def test_agora():
    collab = AgoraCollaboration(workspace_id="test")
    
    # Simulate multi-agent contributions
    n1 = collab.contribute("强硬派", "开场报价", {"price": 100000, "tone": "assertive"})
    n2 = collab.contribute("温和派", "关系维护", {"tone": "friendly"}, parents=[n1.hash])
    n3 = collab.contribute("分析师", "竞品调研", {"competitor_price": 95000}, parents=[n1.hash])
    
    graph = collab.get_collaboration_graph()
    assert graph["nodes"] == 3
    assert graph["edges"] == 2
    assert len(graph["agents"]) == 3
    
    conflicts = collab.resolve_conflicts()
    assert isinstance(conflicts, list)
    
    print("  ✓ Agora collaboration works correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("Security & Collaboration Module Tests")
    print("=" * 60)
    test_supply_chain()
    test_xconf()
    test_agora()
    print("\n✅ All security & collaboration tests passed")
