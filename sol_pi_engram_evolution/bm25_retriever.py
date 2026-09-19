#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BM25 稀疏检索 + RRF 融合引擎
补齐 WeKnora 混合检索能力，集成到 graph_retriever.py

核心功能：
1. BM25 稀疏检索（SQLite FTS5 + 中文逐字分词）
2. 父子分块（Parent-Child Chunking）
3. RRF（Reciprocal Rank Fusion）多路召回融合
4. 时间衰减评分
"""
import os
import re
import json
import sqlite3
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger("bm25_retriever")


# =============================================
# 数据结构
# =============================================

class DocumentChunk:
    """文档分块"""
    def __init__(self, chunk_id: str, content: str, parent_id: str = None,
                 doc_id: str = None, metadata: Dict = None):
        self.chunk_id = chunk_id
        self.content = content
        self.parent_id = parent_id
        self.doc_id = doc_id
        self.metadata = metadata or {}
        self.score = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "parent_id": self.parent_id,
            "doc_id": self.doc_id,
            "score": self.score,
            "metadata": self.metadata,
        }


# =============================================
# BM25 检索器（SQLite FTS5）
# =============================================

class BM25Retriever:
    """
    BM25 稀疏检索器（基于 SQLite FTS5）
    
    优势：无需额外依赖，SQLite 内置 FTS5
    中文处理：unicode61 + 逐字插入空格实现中文匹配
    """
    
    def __init__(self, db_path: str = "./bm25_index.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化 FTS5 表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # FTS5 虚拟表（unicode61 tokenizer）
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                chunk_id UNINDEXED,
                content,
                parent_id,
                doc_id,
                metadata,
                tokenize='unicode61'
            )
        """)
        
        # 元数据表（含原始内容，用于检索后展示）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chunks_meta (
                chunk_id TEXT PRIMARY KEY,
                parent_id TEXT,
                doc_id TEXT,
                created_at TEXT,
                updated_at TEXT,
                word_count INTEGER,
                original_content TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def _tokenize_chinese(text: str) -> str:
        """
        在中文字符间插入空格，使 unicode61 能逐字索引
        
        示例：'定州汽车' -> '定 州 汽 车 '
        """
        result = []
        for char in text:
            result.append(char)
            if '\u4e00' <= char <= '\u9fff':
                result.append(' ')
        return ''.join(result).strip()
    
    def index_chunk(self, chunk: DocumentChunk):
        """索引单个分块"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tokenized = self._tokenize_chinese(chunk.content)
        
        cursor.execute("""
            INSERT OR REPLACE INTO chunks_fts (chunk_id, content, parent_id, doc_id, metadata)
            VALUES (?, ?, ?, ?, ?)
        """, (chunk.chunk_id, tokenized, chunk.parent_id or "",
              chunk.doc_id or "", json.dumps(chunk.metadata, ensure_ascii=False)))
        
        cursor.execute("""
            INSERT OR REPLACE INTO chunks_meta (chunk_id, parent_id, doc_id, created_at, updated_at, word_count, original_content)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (chunk.chunk_id, chunk.parent_id or "", chunk.doc_id or "",
              datetime.now().isoformat(), datetime.now().isoformat(),
              len(chunk.content), chunk.content))
        
        conn.commit()
        conn.close()
    
    def index_chunks(self, chunks: List[DocumentChunk]):
        """批量索引分块"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for chunk in chunks:
            tokenized = self._tokenize_chinese(chunk.content)
            
            cursor.execute("""
                INSERT OR REPLACE INTO chunks_fts (chunk_id, content, parent_id, doc_id, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (chunk.chunk_id, tokenized, chunk.parent_id or "",
                  chunk.doc_id or "", json.dumps(chunk.metadata, ensure_ascii=False)))
            
            cursor.execute("""
                INSERT OR REPLACE INTO chunks_meta (chunk_id, parent_id, doc_id, created_at, updated_at, word_count, original_content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (chunk.chunk_id, chunk.parent_id or "", chunk.doc_id or "",
                  datetime.now().isoformat(), datetime.now().isoformat(),
                  len(chunk.content), chunk.content))
        
        conn.commit()
        conn.close()
        logger.info(f"Indexed {len(chunks)} chunks")
    
    def search(self, query: str, limit: int = 10) -> List[DocumentChunk]:
        """
        BM25 搜索
        
        使用 FTS5 的 bm25() 函数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tokenized_query = self._tokenize_chinese(query)
        
        # FTS5 查询：使用 bm25() 函数（分数越低越相关，取负值使越高越相关）
        cursor.execute("""
            SELECT c.chunk_id, m.original_content, c.parent_id, c.doc_id, c.metadata,
                   -bm25(chunks_fts) as score
            FROM chunks_fts c
            JOIN chunks_meta m ON c.chunk_id = m.chunk_id
            WHERE c.content MATCH ?
            ORDER BY score DESC
            LIMIT ?
        """, (tokenized_query, limit))
        
        results = []
        for row in cursor.fetchall():
            chunk = DocumentChunk(
                chunk_id=row[0],
                content=row[1],  # original_content
                parent_id=row[2] if row[2] else None,
                doc_id=row[3] if row[3] else None,
                metadata=json.loads(row[4]) if row[4] else {}
            )
            chunk.score = row[5]
            results.append(chunk)
        
        conn.close()
        return results
    
    def delete_doc(self, doc_id: str):
        """删除文档的所有分块"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chunks_fts WHERE doc_id = ?", (doc_id,))
        cursor.execute("DELETE FROM chunks_meta WHERE doc_id = ?", (doc_id,))
        conn.commit()
        conn.close()
    
    def get_stats(self) -> Dict:
        """获取索引统计"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chunks_fts")
        total_chunks = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT doc_id) FROM chunks_meta")
        total_docs = cursor.fetchone()[0]
        conn.close()
        return {
            "total_chunks": total_chunks,
            "total_docs": total_docs,
            "db_size": os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0,
        }


# =============================================
# 父子分块器
# =============================================

class ParentChildChunker:
    """
    父子分块（Parent-Child Chunking）
    
    策略：
    - 父块：大块文本（段落/章节），提供完整上下文
    - 子块：小块文本（句子/片段），精确匹配
    - 检索时先匹配子块，再召回父块
    """
    
    def __init__(self, parent_size: int = 1000, child_size: int = 200, overlap: int = 50):
        self.parent_size = parent_size
        self.child_size = child_size
        self.overlap = overlap
    
    def chunk_document(self, content: str, doc_id: str) -> List[DocumentChunk]:
        """对文档进行父子分块"""
        chunks = []
        parents = self._split_text(content, self.parent_size, self.overlap)
        
        for i, parent_text in enumerate(parents):
            parent_id = f"{doc_id}_parent_{i}"
            
            parent_chunk = DocumentChunk(
                chunk_id=parent_id,
                content=parent_text,
                doc_id=doc_id,
                metadata={"type": "parent", "index": i}
            )
            chunks.append(parent_chunk)
            
            # 子块
            children = self._split_text(parent_text, self.child_size, self.overlap // 2)
            for j, child_text in enumerate(children):
                child_id = f"{doc_id}_parent_{i}_child_{j}"
                child_chunk = DocumentChunk(
                    chunk_id=child_id,
                    content=child_text,
                    parent_id=parent_id,
                    doc_id=doc_id,
                    metadata={"type": "child", "parent_index": i, "child_index": j}
                )
                chunks.append(child_chunk)
        
        return chunks
    
    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """切分文本"""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            if end < len(text):
                # 尝试在句子边界切分
                sentence_end = -1
                for sep in ['。', '？', '！', '\n', '. ', '? ', '! ']:
                    pos = text.rfind(sep, start, end)
                    if pos > sentence_end:
                        sentence_end = pos
                
                if sentence_end > start:
                    end = sentence_end + 1
            
            chunks.append(text[start:end])
            start = max(end - overlap, start + 1)  # 确保至少前进1个字符
        
        return chunks


# =============================================
# RRF 排名融合
# =============================================

class RRFRanker:
    """
    RRF（Reciprocal Rank Fusion）多路召回融合
    
    公式：RRF_score(d) = Σ 1/(k + rank_i(d))
    k=60（默认值，防止排名第一的文档权重过大）
    """
    
    def __init__(self, k: int = 60):
        self.k = k
    
    def fuse(self, ranked_lists: List[List[DocumentChunk]]) -> List[DocumentChunk]:
        """
        融合多个排名列表
        
        Args:
            ranked_lists: 多个检索结果列表，每个列表按分数降序排列
        
        Returns:
            融合后的结果列表
        """
        scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}
        
        for ranked_list in ranked_lists:
            for rank, chunk in enumerate(ranked_list):
                chunk_id = chunk.chunk_id
                rrf_score = 1.0 / (self.k + rank + 1)
                
                if chunk_id in scores:
                    scores[chunk_id] += rrf_score
                else:
                    scores[chunk_id] = rrf_score
                    chunk_map[chunk_id] = chunk
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        results = []
        for chunk_id in sorted_ids:
            chunk = chunk_map[chunk_id]
            chunk.score = scores[chunk_id]
            results.append(chunk)
        
        return results
    
    def fuse_with_time_decay(self, ranked_lists: List[List[DocumentChunk]],
                              half_life_days: int = 30) -> List[DocumentChunk]:
        """
        带时间衰减的 RRF 融合
        
        适用于：谈判案例库（新案例权重更高）
        """
        scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}
        
        for ranked_list in ranked_lists:
            for rank, chunk in enumerate(ranked_list):
                chunk_id = chunk.chunk_id
                rrf_score = 1.0 / (self.k + rank + 1)
                
                # 时间衰减
                time_factor = 1.0
                if "created_at" in chunk.metadata:
                    try:
                        created = datetime.fromisoformat(chunk.metadata["created_at"])
                        age_days = (datetime.now() - created).days
                        time_factor = 0.5 ** (age_days / half_life_days)
                    except:
                        pass
                
                final_score = rrf_score * time_factor
                
                if chunk_id in scores:
                    scores[chunk_id] += final_score
                else:
                    scores[chunk_id] = final_score
                    chunk_map[chunk_id] = chunk
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        results = []
        for chunk_id in sorted_ids:
            chunk = chunk_map[chunk_id]
            chunk.score = scores[chunk_id]
            results.append(chunk)
        
        return results


# =============================================
# 混合检索器
# =============================================

class HybridRetriever:
    """
    混合检索器（BM25 + Graph + RRF 融合）
    
    集成到现有 graph_retriever.py 的增强接口
    """
    
    def __init__(self, db_path: str = "./bm25_index.db"):
        self.bm25 = BM25Retriever(db_path)
        self.chunker = ParentChildChunker()
        self.ranker = RRFRanker()
    
    def index_document(self, content: str, doc_id: str, metadata: Dict = None) -> int:
        """
        索引文档
        
        流程：文档 → 父子分块 → BM25 索引
        
        Returns:
            分块数量
        """
        chunks = self.chunker.chunk_document(content, doc_id)
        
        for chunk in chunks:
            if metadata:
                chunk.metadata.update(metadata)
            chunk.metadata["created_at"] = datetime.now().isoformat()
        
        self.bm25.index_chunks(chunks)
        
        return len(chunks)
    
    def search(self, query: str, limit: int = 10,
               use_parent_recall: bool = True) -> List[Dict]:
        """
        混合搜索
        
        流程：查询 → BM25 子块检索 → 父块召回 → RRF 融合
        """
        chunks = self.bm25.search(query, limit=limit * 3)
        
        if not chunks:
            return []
        
        results = []
        
        if use_parent_recall:
            parent_ids = set()
            for chunk in chunks:
                if chunk.parent_id:
                    parent_ids.add(chunk.parent_id)
            
            seen_parents = set()
            final_results = []
            
            for chunk in chunks:
                if chunk.parent_id and chunk.parent_id not in seen_parents:
                    parent_content = self._get_parent_content(chunk.parent_id)
                    if parent_content:
                        parent_chunk = DocumentChunk(
                            chunk_id=chunk.parent_id,
                            content=parent_content,
                            doc_id=chunk.doc_id,
                            metadata={**chunk.metadata, "type": "parent_recall"}
                        )
                        parent_chunk.score = chunk.score * 0.8
                        final_results.append(parent_chunk)
                        seen_parents.add(chunk.parent_id)
                elif not chunk.parent_id:
                    final_results.append(chunk)
            
            results = [c.to_dict() for c in final_results[:limit]]
        else:
            results = [c.to_dict() for c in chunks[:limit]]
        
        return results
    
    def _get_parent_content(self, parent_id: str) -> Optional[str]:
        """获取父块内容"""
        conn = sqlite3.connect(self.bm25.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT original_content FROM chunks_meta WHERE chunk_id = ?",
            (parent_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def delete_document(self, doc_id: str):
        """删除文档"""
        self.bm25.delete_doc(doc_id)
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return self.bm25.get_stats()


if __name__ == "__main__":
    retriever = HybridRetriever("./test_hybrid.db")
    
    doc = """
    定州汽车零部件产业调研报告
    
    一、产业概况
    定州市位于河北省中部，是京津冀协同发展的重要节点城市。
    汽车零部件产业是定州市的传统优势产业，已有30余年发展历史。
    
    二、主要企业
    定州现有汽车零部件生产企业200余家，其中规模以上企业50余家。
    主要产品包括发动机零部件、底盘零部件、电气系统等。
    
    三、市场特点
    1. 产业集群效应明显
    2. 产品以中低端为主
    3. 出口市场集中在东南亚和非洲
    """
    
    count = retriever.index_document(doc, "dingzhou_auto_parts")
    print(f"Indexed {count} chunks")
    
    results = retriever.search("汽车零部件 出口")
    print(f"\nSearch results:")
    for r in results:
        print(f"  [{r['chunk_id']}] {r['content'][:50]}...")
    
    stats = retriever.get_stats()
    print(f"\nStats: {stats}")
