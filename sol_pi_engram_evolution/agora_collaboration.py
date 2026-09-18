#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agora 多Agent协作模块
参考 NVIDIA Agora：Git-backed immutable DAG 作为共享记忆
支持多角色谈判Agent协作
"""
import os
import json
import hashlib
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime

logger = logging.getLogger("agora_collaboration")


class AgoraNode:
    """Agora DAG 节点"""
    def __init__(self, agent_id: str, action: str, data: Dict, parents: List[str] = None):
        self.agent_id = agent_id
        self.action = action
        self.data = data
        self.parents = parents or []
        self.timestamp = datetime.now().isoformat()
        self.hash = self._compute_hash()
    
    def _compute_hash(self) -> str:
        content = f"{self.agent_id}:{self.action}:{json.dumps(self.data, sort_keys=True)}:{self.parents}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class AgoraCollaboration:
    """Agora 多Agent协作引擎"""
    
    def __init__(self, workspace_id: str = "default"):
        self.workspace_id = workspace_id
        self.nodes: Dict[str, AgoraNode] = {}
        self.agent_contributions: Dict[str, List[str]] = {}
    
    def contribute(self, agent_id: str, action: str, data: Dict,
                   parents: List[str] = None) -> AgoraNode:
        """Agent 提交贡献"""
        node = AgoraNode(agent_id, action, data, parents)
        self.nodes[node.hash] = node
        
        if agent_id not in self.agent_contributions:
            self.agent_contributions[agent_id] = []
        self.agent_contributions[agent_id].append(node.hash)
        
        logger.info(f"Agent {agent_id} contributed: {action} -> {node.hash[:8]}")
        return node
    
    def get_shared_knowledge(self, agent_id: str) -> List[Dict]:
        """获取其他 Agent 的共享知识"""
        knowledge = []
        for hash_id, node in self.nodes.items():
            if node.agent_id != agent_id:
                knowledge.append({
                    "from_agent": node.agent_id,
                    "action": node.action,
                    "data": node.data,
                    "timestamp": node.timestamp,
                    "hash": node.hash
                })
        return sorted(knowledge, key=lambda x: x["timestamp"], reverse=True)
    
    def get_collaboration_graph(self) -> Dict:
        """获取协作 DAG"""
        return {
            "nodes": len(self.nodes),
            "edges": sum(len(n.parents) for n in self.nodes.values()),
            "agents": list(self.agent_contributions.keys()),
            "contributions": {agent: len(hashes) for agent, hashes in self.agent_contributions.items()}
        }
    
    def resolve_conflicts(self) -> List[Dict]:
        """检测并解决冲突"""
        conflicts = []
        # 检测同一 action 的多个贡献
        action_map: Dict[str, List[str]] = {}
        for hash_id, node in self.nodes.items():
            action_key = f"{node.action}"
            if action_key not in action_map:
                action_map[action_key] = []
            action_map[action_key].append(hash_id)
        
        for action, hashes in action_map.items():
            if len(hashes) > 1:
                conflicts.append({
                    "action": action,
                    "contributors": [self.nodes[h].agent_id for h in hashes],
                    "resolution": "latest_wins",
                    "winner": self.nodes[hashes[-1]].agent_id
                })
        
        return conflicts


_agora: Optional[AgoraCollaboration] = None

def get_agora(workspace_id: str = "default") -> AgoraCollaboration:
    global _agora
    if _agora is None:
        _agora = AgoraCollaboration(workspace_id)
    return _agora
