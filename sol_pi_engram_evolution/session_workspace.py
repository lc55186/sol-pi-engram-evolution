#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话持久化工作区（Session Workspace）
WeKnora 0.8.0 核心能力：每个对话独立持久化运行环境
BOSS-AI-R 适配：谈判场景的多轮对话 + 产物管理
"""
import os
import json
import shutil
import hashlib
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

logger = logging.getLogger("session_workspace")


class WorkspaceManifest:
    """工作区清单"""
    def __init__(self, workspace_dir: str):
        self.manifest_path = os.path.join(workspace_dir, "workspace.manifest.json")
        self.data = self._load()
    
    def _load(self) -> Dict:
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "created_at": datetime.now().isoformat(),
            "session_id": "",
            "files": [],
            "products": [],
            "references": [],
        }
    
    def save(self):
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_file(self, file_path: str, file_type: str, description: str = ""):
        """添加文件记录"""
        rel_path = os.path.relpath(file_path, os.path.dirname(self.manifest_path))
        entry = {
            "path": rel_path,
            "type": file_type,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        }
        self.data["files"].append(entry)
        self.save()
    
    def add_product(self, product_path: str, product_type: str, source: str = ""):
        """添加产物记录"""
        rel_path = os.path.relpath(product_path, os.path.dirname(self.manifest_path))
        entry = {
            "path": rel_path,
            "type": product_type,
            "source": source,
            "created_at": datetime.now().isoformat(),
        }
        self.data["products"].append(entry)
        self.save()
    
    def get_files(self, file_type: str = None) -> List[Dict]:
        """获取文件列表"""
        if file_type:
            return [f for f in self.data["files"] if f["type"] == file_type]
        return self.data["files"]
    
    def get_products(self, product_type: str = None) -> List[Dict]:
        """获取产物列表"""
        if product_type:
            return [p for p in self.data["products"] if p["type"] == product_type]
        return self.data["products"]


class SessionWorkspace:
    """
    会话持久化工作区
    
    每个对话/会话拥有独立的持久化工作目录
    - 文件读写隔离
    - 产物清单自动维护
    - 支持跨会话知识引用
    - 沙箱隔离（路径安全检查）
    """
    
    def __init__(self, session_id: str, root_dir: str = "./workspaces"):
        self.session_id = session_id
        self.root_dir = os.path.abspath(root_dir)
        self.workspace_dir = os.path.join(self.root_dir, session_id)
        self._ensure_workspace()
        self.manifest = WorkspaceManifest(self.workspace_dir)
        self.manifest.data["session_id"] = session_id
        self.manifest.save()
    
    def _ensure_workspace(self):
        """确保工作区目录存在"""
        os.makedirs(self.workspace_dir, exist_ok=True)
        # 创建子目录
        for subdir in ["documents", "products", "temp", "scripts"]:
            os.makedirs(os.path.join(self.workspace_dir, subdir), exist_ok=True)
    
    def _safe_path(self, filename: str) -> str:
        """安全检查：防止目录遍历"""
        safe_name = os.path.basename(filename)
        if not safe_name or safe_name.startswith("."):
            raise ValueError(f"Invalid filename: {filename}")
        target = os.path.join(self.workspace_dir, safe_name)
        # 确保最终路径在工作区内
        if not os.path.abspath(target).startswith(self.workspace_dir):
            raise ValueError(f"Path traversal detected: {filename}")
        return target
    
    def write_file(self, filename: str, content: str, subdir: str = "") -> str:
        """
        写入文件到工作区
        
        Returns:
            文件绝对路径
        """
        if subdir:
            dir_path = os.path.join(self.workspace_dir, subdir)
            os.makedirs(dir_path, exist_ok=True)
        else:
            dir_path = self.workspace_dir
        
        file_path = os.path.join(dir_path, os.path.basename(filename))
        
        # 安全检查
        if not os.path.abspath(file_path).startswith(self.workspace_dir):
            raise ValueError(f"Invalid path: {filename}")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        # 更新清单
        ext = os.path.splitext(filename)[1].lstrip(".")
        self.manifest.add_file(file_path, ext)
        
        logger.info(f"Written: {file_path}")
        return file_path
    
    def read_file(self, filename: str, subdir: str = "") -> str:
        """读取文件"""
        if subdir:
            file_path = os.path.join(self.workspace_dir, subdir, os.path.basename(filename))
        else:
            file_path = os.path.join(self.workspace_dir, os.path.basename(filename))
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def list_files(self, subdir: str = "") -> List[Dict]:
        """列出工作区文件"""
        target_dir = self.workspace_dir
        if subdir:
            target_dir = os.path.join(self.workspace_dir, subdir)
        
        if not os.path.exists(target_dir):
            return []
        
        files = []
        for name in os.listdir(target_dir):
            full_path = os.path.join(target_dir, name)
            if os.path.isfile(full_path):
                files.append({
                    "name": name,
                    "path": full_path,
                    "size": os.path.getsize(full_path),
                    "modified": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat(),
                })
        
        return files
    
    def save_product(self, filename: str, content: str, product_type: str = "document",
                     source: str = "") -> str:
        """
        保存产物（分析结果、合同、报告等）
        
        Returns:
            产物路径
        """
        product_path = os.path.join(self.workspace_dir, "products", os.path.basename(filename))
        
        with open(product_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        self.manifest.add_product(product_path, product_type, source)
        logger.info(f"Product saved: {product_path}")
        return product_path
    
    def save_product_bytes(self, filename: str, data: bytes, product_type: str = "binary") -> str:
        """保存二进制产物"""
        product_path = os.path.join(self.workspace_dir, "products", os.path.basename(filename))
        
        with open(product_path, "wb") as f:
            f.write(data)
        
        self.manifest.add_product(product_path, product_type)
        return product_path
    
    def get_product_path(self, filename: str) -> str:
        """获取产物路径"""
        return os.path.join(self.workspace_dir, "products", os.path.basename(filename))
    
    def get_document_path(self, filename: str) -> str:
        """获取文档路径"""
        return os.path.join(self.workspace_dir, "documents", os.path.basename(filename))
    
    def cleanup(self):
        """清理工作区"""
        if os.path.exists(self.workspace_dir):
            shutil.rmtree(self.workspace_dir)
            logger.info(f"Workspace cleaned: {self.session_id}")
    
    def get_info(self) -> Dict:
        """获取工作区信息"""
        files = self.list_files()
        products = self.manifest.get_products()
        
        return {
            "session_id": self.session_id,
            "workspace_dir": self.workspace_dir,
            "total_files": len(files),
            "total_products": len(products),
            "total_size": sum(f["size"] for f in files),
            "created_at": self.manifest.data.get("created_at", ""),
        }
    
    def to_dict(self) -> Dict:
        """序列化为字典"""
        return {
            "session_id": self.session_id,
            "workspace_dir": self.workspace_dir,
            "files": self.manifest.get_files(),
            "products": self.manifest.get_products(),
        }


class WorkspaceManager:
    """工作区管理器"""
    
    def __init__(self, root_dir: str = "./workspaces"):
        self.root_dir = root_dir
        self._workspaces: Dict[str, SessionWorkspace] = {}
        os.makedirs(root_dir, exist_ok=True)
    
    def get_workspace(self, session_id: str) -> SessionWorkspace:
        """获取或创建工作区"""
        if session_id not in self._workspaces:
            self._workspaces[session_id] = SessionWorkspace(session_id, self.root_dir)
        return self._workspaces[session_id]
    
    def create_workspace(self, session_id: str) -> SessionWorkspace:
        """创建工作区"""
        ws = SessionWorkspace(session_id, self.root_dir)
        self._workspaces[session_id] = ws
        return ws
    
    def remove_workspace(self, session_id: str):
        """移除工作区"""
        if session_id in self._workspaces:
            self._workspaces[session_id].cleanup()
            del self._workspaces[session_id]
    
    def list_workspaces(self) -> List[Dict]:
        """列出所有工作区"""
        workspaces = []
        if os.path.exists(self.root_dir):
            for name in os.listdir(self.root_dir):
                ws_dir = os.path.join(self.root_dir, name)
                if os.path.isdir(ws_dir):
                    manifest_path = os.path.join(ws_dir, "workspace.manifest.json")
                    if os.path.exists(manifest_path):
                        with open(manifest_path, "r") as f:
                            manifest = json.load(f)
                        workspaces.append({
                            "session_id": name,
                            "created_at": manifest.get("created_at", ""),
                            "total_files": len(manifest.get("files", [])),
                            "total_products": len(manifest.get("products", [])),
                        })
        return workspaces


_manager: Optional[WorkspaceManager] = None

def get_workspace_manager(root_dir: str = "./workspaces") -> WorkspaceManager:
    """获取工作区管理器"""
    global _manager
    if _manager is None:
        _manager = WorkspaceManager(root_dir)
    return _manager


if __name__ == "__main__":
    # 示例
    manager = get_workspace_manager("./workspaces")
    ws = manager.get_workspace("negotiation-2026-09-19-001")
    
    # 保存合同
    ws.write_file("contract_draft.txt", "这是一份合同草稿...", subdir="documents")
    
    # 保存产物
    ws.save_product("analysis_report.md", "# 谈判分析报告\n...", product_type="report")
    
    # 查看信息
    info = ws.get_info()
    print(json.dumps(info, indent=2, ensure_ascii=False))
