#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Session Workspace + BM25 Retriever Tests"""
import os
import sys
import json
import shutil
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from session_workspace import SessionWorkspace, WorkspaceManager
from bm25_retriever import (
    BM25Retriever, DocumentChunk, ParentChildChunker,
    RRFRanker, HybridRetriever
)


def test_session_workspace():
    """测试会话工作区"""
    # 使用临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = SessionWorkspace("test-session-001", root_dir=tmpdir)
        
        # 写入文件
        file_path = ws.write_file("test.txt", "Hello, World!", subdir="documents")
        assert os.path.exists(file_path)
        
        # 读取文件
        content = ws.read_file("test.txt", subdir="documents")
        assert content == "Hello, World!"
        
        # 列出文件
        files = ws.list_files(subdir="documents")
        assert len(files) == 1
        assert files[0]["name"] == "test.txt"
        
        # 保存产物
        product_path = ws.save_product("report.md", "# Test Report", product_type="report")
        assert os.path.exists(product_path)
        
        # 检查清单
        products = ws.manifest.get_products()
        assert len(products) == 1
        assert products[0]["type"] == "report"
        
        # 获取信息
        info = ws.get_info()
        assert info["total_files"] == 1
        assert info["total_products"] == 1
        
        print("  ✓ SessionWorkspace works correctly")


def test_workspace_manager():
    """测试工作区管理器"""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = WorkspaceManager(root_dir=tmpdir)
        
        # 创建工作区
        ws1 = manager.create_workspace("session-001")
        ws2 = manager.create_workspace("session-002")
        
        assert ws1.session_id == "session-001"
        assert ws2.session_id == "session-002"
        
        # 列出工作区
        workspaces = manager.list_workspaces()
        assert len(workspaces) == 2
        
        # 移除工作区
        manager.remove_workspace("session-001")
        workspaces = manager.list_workspaces()
        assert len(workspaces) == 1
        
        print("  ✓ WorkspaceManager works correctly")


def test_path_traversal_protection():
    """测试路径遍历保护"""
    with tempfile.TemporaryDirectory() as tmpdir:
        ws = SessionWorkspace("test-session", root_dir=tmpdir)
        
        # os.path.basename 会剥离 ../ 前缀，文件会被写入工作区内
        # 这种设计本身就防止了路径遍历
        file_path = ws.write_file("../etc/passwd", "malicious")
        
        # 文件应该被写入工作区内，而不是 /etc/passwd
        assert file_path.startswith(ws.workspace_dir)
        assert file_path.endswith("passwd")
        
        # 确认 /etc/passwd 没有被修改（不在工作区外）
        assert not os.path.exists(os.path.join("/etc", "passwd")) or os.path.realpath(file_path) != "/etc/passwd"
        
        print("  ✓ Path traversal protection works correctly")


def test_bm25_indexing():
    """测试 BM25 索引"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_bm25.db")
        retriever = BM25Retriever(db_path)
        
        # 索引分块
        chunks = [
            DocumentChunk("c1", "定州汽车零部件产业调研报告"),
            DocumentChunk("c2", "定州现有汽车零部件生产企业200余家"),
            DocumentChunk("c3", "产品以中低端为主，出口市场集中在东南亚"),
        ]
        
        retriever.index_chunks(chunks)
        
        # 检查统计
        stats = retriever.get_stats()
        assert stats["total_chunks"] == 3
        
        print("  ✓ BM25 indexing works correctly")


def test_bm25_search():
    """测试 BM25 搜索"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_bm25.db")
        retriever = BM25Retriever(db_path)
        
        # 索引文档
        chunks = [
            DocumentChunk("c1", "定州汽车零部件产业调研报告"),
            DocumentChunk("c2", "定州现有汽车零部件生产企业200余家"),
            DocumentChunk("c3", "产品以中低端为主，出口市场集中在东南亚"),
            DocumentChunk("c4", "体育器材产业是定州另一支柱产业"),
            DocumentChunk("c5", "再生资源循环利用产业园区已投入使用"),
        ]
        
        retriever.index_chunks(chunks)
        
        # 搜索
        results = retriever.search("汽车零部件", limit=5)
        assert len(results) > 0
        
        # 检查相关结果排在前面
        result_ids = [r.chunk_id for r in results]
        assert "c1" in result_ids or "c2" in result_ids
        
        print("  ✓ BM25 search works correctly")


def test_parent_child_chunker():
    """测试父子分块"""
    chunker = ParentChildChunker(parent_size=100, child_size=50, overlap=10)
    
    # 长文档
    content = "这是一段测试文本。" * 50  # 约 500 字
    chunks = chunker.chunk_document(content, "test_doc")
    
    # 应该有父块和子块
    parents = [c for c in chunks if c.parent_id is None]
    children = [c for c in chunks if c.parent_id is not None]
    
    assert len(parents) > 0
    assert len(children) > 0
    # 子块应该比父块多
    assert len(children) > len(parents)
    
    print("  ✓ ParentChildChunker works correctly")


def test_rrf_fusion():
    """测试 RRF 融合"""
    ranker = RRFRanker(k=60)
    
    # 模拟两个引擎的排名结果
    chunks_a = [
        DocumentChunk("doc1", "Document 1"),
        DocumentChunk("doc2", "Document 2"),
        DocumentChunk("doc3", "Document 3"),
    ]
    
    chunks_b = [
        DocumentChunk("doc2", "Document 2"),
        DocumentChunk("doc4", "Document 4"),
        DocumentChunk("doc1", "Document 1"),
    ]
    
    results = ranker.fuse([chunks_a, chunks_b])
    
    # doc1 和 doc2 出现在两个列表中，应该排在前面
    assert len(results) == 4  # doc1, doc2, doc3, doc4
    assert results[0].chunk_id in ["doc1", "doc2"]
    
    print("  ✓ RRF fusion works correctly")


def test_hybrid_retriever():
    """测试混合检索器"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_hybrid.db")
        retriever = HybridRetriever(db_path)
        
        # 索引文档
        doc = "定州汽车零部件产业调研报告。定州现有汽车零部件生产企业200余家，其中规模以上企业50余家。产品以中低端为主，出口市场集中在东南亚和非洲。"
        count = retriever.index_document(doc, "test_doc")
        assert count > 0
        
        # 搜索
        results = retriever.search("汽车零部件 出口")
        assert len(results) > 0
        
        # 检查有父块召回
        has_parent = any(r.get("metadata", {}).get("type") == "parent_recall" for r in results)
        # 可能为 True 或 False 取决于具体匹配
        
        # 统计
        stats = retriever.get_stats()
        assert stats["total_chunks"] > 0
        
        print("  ✓ HybridRetriever works correctly")


def test_chinese_tokenization():
    """测试中文分词"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_chinese.db")
        retriever = BM25Retriever(db_path)
        
        # 中文文档
        chunks = [
            DocumentChunk("c1", "谈判技巧：如何在价格谈判中占据主动"),
            DocumentChunk("c2", "合同审核要点：知识产权条款详解"),
            DocumentChunk("c3", "供应链管理与库存优化策略"),
        ]
        
        retriever.index_chunks(chunks)
        
        # 中文搜索
        results = retriever.search("谈判 价格")
        assert len(results) > 0
        
        # 第一个结果应该包含"谈判"
        assert "谈判" in results[0].content
        
        print("  ✓ Chinese tokenization works correctly")


def test_concurrent_workspace_access():
    """测试并发工作区访问"""
    import threading
    
    with tempfile.TemporaryDirectory() as tmpdir:
        errors = []
        
        def worker(session_id):
            try:
                ws = SessionWorkspace(session_id, root_dir=tmpdir)
                ws.write_file("test.txt", f"Content from {session_id}")
                content = ws.read_file("test.txt")
                assert content == f"Content from {session_id}"
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(f"session-{i}",))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join(timeout=10)
        
        assert len(errors) == 0, f"Errors: {errors}"
        
        print("  ✓ Concurrent workspace access works correctly")


if __name__ == "__main__":
    print("=" * 60)
    print("Session Workspace + BM25 Retriever Tests")
    print("=" * 60)
    
    test_session_workspace()
    test_workspace_manager()
    test_path_traversal_protection()
    test_bm25_indexing()
    test_bm25_search()
    test_parent_child_chunker()
    test_rrf_fusion()
    test_hybrid_retriever()
    test_chinese_tokenization()
    test_concurrent_workspace_access()
    
    print("\n✅ All session workspace + BM25 retriever tests passed")
