#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供应链安全审计模块
响应 Strix AI 25分钟攻破 $13B Baseten 事件
强制 BuildKit secret mount，禁止 Docker 构建历史泄露凭证
"""
import os
import re
import hashlib
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger("supply_chain_audit")


class SupplyChainAuditor:
    """供应链安全审计器"""
    
    # 危险模式：Docker 构建历史中可能泄露的凭证
    DANGEROUS_PATTERNS = [
        r'(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{20,}',
        r'(?i)GITHUB_[A-Z_]+=[a-zA-Z0-9]{30,}',
        r'(?i)AWS_[A-Z_]+=[a-zA-Z0-9/+=]{20,}',
        r'(?i)(ssh[_-]?key|private[_-]?key)',
        r'(?i)-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
    ]
    
    # 安全的 BuildKit secret mount 模板
    BUILDKIT_SECRET_TEMPLATE = """# syntax=docker/dockerfile:1
FROM {base_image}
RUN --mount=type=secret,id={secret_name} \
    cat /run/secrets/{secret_name} > /app/config/{output_file}
"""
    
    def __init__(self):
        self.audit_log: List[Dict] = []
    
    def scan_dockerfile(self, content: str) -> Dict[str, Any]:
        """扫描 Dockerfile 中的安全风险"""
        findings = []
        
        for pattern in self.DANGEROUS_PATTERNS:
            matches = re.findall(pattern, content)
            if matches:
                findings.append({
                    "pattern": pattern,
                    "matches": len(matches),
                    "severity": "critical",
                    "recommendation": "Use BuildKit secret mount instead of hardcoded credentials"
                })
        
        # 检查是否使用了 BuildKit secret mount
        uses_buildkit_secret = "mount=type=secret" in content
        
        # 检查 COPY 指令是否可能泄露敏感文件
        copy_matches = re.findall(r'COPY\s+(\S+)\s+', content)
        sensitive_files = [f for f in copy_matches if any(
            s in f.lower() for s in ['.env', '.git', 'credentials', 'secret', 'token', '.ssh']
        )]
        
        if sensitive_files:
            findings.append({
                "pattern": "sensitive_file_copy",
                "matches": sensitive_files,
                "severity": "high",
                "recommendation": "Remove sensitive files from COPY or use .dockerignore"
            })
        
        risk_score = len(findings) * 25 + len(sensitive_files) * 15
        
        return {
            "scan_time": datetime.now().isoformat(),
            "findings": findings,
            "risk_score": min(risk_score, 100),
            "uses_buildkit_secret": uses_buildkit_secret,
            "recommendation": "PASS" if risk_score == 0 else "FAIL"
        }
    
    def generate_secure_dockerfile(self, base_image: str, secrets: Dict[str, str]) -> str:
        """生成安全的 Dockerfile（使用 BuildKit secret mount）"""
        lines = [f"# syntax=docker/dockerfile:1", f"FROM {base_image}", ""]
        
        for secret_name, output_file in secrets.items():
            lines.append(f"RUN --mount=type=secret,id={secret_name} \\")
            lines.append(f"    cat /run/secrets/{secret_name} > /app/config/{output_file}")
            lines.append("")
        
        return "\n".join(lines)
    
    def audit_docker_compose(self, content: str) -> Dict[str, Any]:
        """审计 docker-compose.yml 安全"""
        findings = []
        
        # 检查环境变量中的明文密码
        env_secrets = re.findall(r'(?i)(environment:|env_file:)', content)
        if env_secrets:
            findings.append({
                "type": "environment_secrets",
                "severity": "medium",
                "recommendation": "Use Docker secrets or external vault"
            })
        
        # 检查 volume 挂载是否包含敏感路径
        volume_mounts = re.findall(r'volumes:(.*?)(?=\n\n|\Z)', content, re.DOTALL)
        sensitive_mounts = []
        for mount_block in volume_mounts:
            if any(s in mount_block.lower() for s in ['/etc/shadow', '/root/.ssh', '.env']):
                sensitive_mounts.append(mount_block.strip())
        
        if sensitive_mounts:
            findings.append({
                "type": "sensitive_volume_mount",
                "matches": sensitive_mounts,
                "severity": "high",
                "recommendation": "Remove sensitive volume mounts"
            })
        
        return {
            "scan_time": datetime.now().isoformat(),
            "findings": findings,
            "risk_score": len(findings) * 20,
            "recommendation": "PASS" if not findings else "FAIL"
        }
    
    def log_audit(self, target: str, result: Dict):
        """记录审计日志"""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "target": target,
            "result": result
        })
    
    def get_audit_summary(self) -> Dict:
        """获取审计摘要"""
        total = len(self.audit_log)
        passed = sum(1 for log in self.audit_log if log["result"].get("recommendation") == "PASS")
        failed = total - passed
        
        return {
            "total_scans": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / max(total, 1),
            "recent_failures": [
                log for log in self.audit_log[-10:]
                if log["result"].get("recommendation") == "FAIL"
            ]
        }


_auditor: Optional[SupplyChainAuditor] = None

def get_supply_chain_auditor() -> SupplyChainAuditor:
    global _auditor
    if _auditor is None:
        _auditor = SupplyChainAuditor()
    return _auditor
