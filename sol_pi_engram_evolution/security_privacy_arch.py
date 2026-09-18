#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全与隐私保护架构
整合所有安全需求：Agent攻击防御、隐私保护、防供应链攻击、AI安全标准
"""
import os
import hashlib
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

logger = logging.getLogger("security_privacy")


class SecurityPrivacyArchitecture:
    """安全与隐私保护架构"""
    
    def __init__(self):
        self.dependency_whitelist: Set[str] = set()
        self.network_allowlist: Set[str] = set()
        self.sandbox_rules: Dict[str, Any] = {}
        self.privacy_config: Dict[str, Any] = {
            "local_processing": True,
            "e2e_encryption": True,
            "data_retention_days": 30,
            "anonymize_before_upload": True,
        }
        self.security_log: List[Dict] = []
    
    def add_dependency_whitelist(self, packages: List[str]):
        """添加依赖包白名单（防供应链攻击）"""
        self.dependency_whitelist.update(packages)
        self._log_security_event("dependency_whitelist_update", {"packages": packages})
    
    def check_dependency(self, package: str, version: str) -> Dict:
        """检查依赖包是否在白名单中"""
        key = f"{package}=={version}"
        is_allowed = any(
            package in allowed for allowed in self.dependency_whitelist
        )
        
        result = {
            "package": package,
            "version": version,
            "allowed": is_allowed,
            "hash": hashlib.sha256(key.encode()).hexdigest()[:16],
        }
        
        if not is_allowed:
            self._log_security_event("blocked_dependency", result)
        
        return result
    
    def add_network_allowlist(self, domains: List[str]):
        """添加网络访问白名单"""
        self.network_allowlist.update(domains)
    
    def check_network_access(self, url: str) -> Dict:
        """检查网络访问是否允许"""
        from urllib.parse import urlparse
        import fnmatch
        
        parsed = urlparse(url)
        host = parsed.hostname or url
        
        allowed = False
        for pattern in self.network_allowlist:
            # Strip scheme for matching
            clean_pattern = pattern.replace("https://", "").replace("http://", "")
            pattern_host = clean_pattern.split("/")[0]
            
            if fnmatch.fnmatch(host, pattern_host):
                allowed = True
                break
        
        result = {
            "url": url,
            "allowed": allowed,
            "timestamp": datetime.now().isoformat(),
        }
        
        if not allowed:
            self._log_security_event("blocked_network_access", result)
        
        return result
    
    def apply_privacy_config(self, config: Dict[str, Any]):
        """应用隐私配置"""
        self.privacy_config.update(config)
    
    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """数据匿名化（上传前处理）"""
        anonymized = data.copy()
        
        # 移除/哈希化 PII
        pii_fields = ["name", "phone", "email", "id_card", "address"]
        for field in pii_fields:
            if field in anonymized:
                original = str(anonymized[field])
                anonymized[field] = hashlib.sha256(original.encode()).hexdigest()[:12]
        
        return anonymized
    
    def encrypt_for_upload(self, data: str, key: str = None) -> Dict:
        """加密数据准备上传"""
        if not key:
            key = "default_key"
        
        # 简化的加密（实际应使用 AES-256-GCM）
        encrypted = hashlib.sha256(f"{key}:{data}".encode()).hexdigest()
        
        return {
            "encrypted": True,
            "algorithm": "sha256_hash_demo",
            "data": encrypted,
            "key_id": hashlib.sha256(key.encode()).hexdigest()[:16],
        }
    
    def check_agent_action_safety(self, agent_id: str, action: str,
                                   target: str, params: Dict = None) -> Dict:
        """综合 Agent 动作安全检查"""
        checks = []
        
        # 1. 网络访问检查
        if action.startswith("network.") or action.startswith("http."):
            net_result = self.check_network_access(target)
            checks.append(("network", net_result))
        
        # 2. 依赖包检查
        if action == "install.package":
            dep_result = self.check_dependency(params.get("package", ""), params.get("version", ""))
            checks.append(("dependency", dep_result))
        
        # 3. 隐私数据处理
        if action in ["upload", "sync", "backup"]:
            if params and "data" in params:
                anonymized = self.anonymize_data(params["data"])
                checks.append({"check": "privacy", "anonymized": True})
        
        all_passed = all(
            c[1].get("allowed", True) for c in checks if isinstance(c, tuple)
        )
        
        return {
            "agent_id": agent_id,
            "action": action,
            "target": target,
            "all_checks_passed": all_passed,
            "checks": checks,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _log_security_event(self, event_type: str, details: Dict):
        """记录安全事件"""
        self.security_log.append({
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "details": details,
        })
    
    def get_security_report(self) -> Dict:
        """生成安全报告"""
        total_events = len(self.security_log)
        blocked_events = sum(
            1 for log in self.security_log
            if "blocked" in log.get("event", "")
        )
        
        return {
            "report_date": datetime.now().isoformat(),
            "total_events": total_events,
            "blocked_events": blocked_events,
            "block_rate": blocked_events / max(total_events, 1),
            "privacy_config": self.privacy_config,
            "dependency_whitelist_size": len(self.dependency_whitelist),
            "network_allowlist_size": len(self.network_allowlist),
        }


_arch: Optional[SecurityPrivacyArchitecture] = None

def get_security_privacy() -> SecurityPrivacyArchitecture:
    global _arch
    if _arch is None:
        _arch = SecurityPrivacyArchitecture()
    return _arch
