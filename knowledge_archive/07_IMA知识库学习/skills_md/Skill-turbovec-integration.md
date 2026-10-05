# Skill-turbovec-integration

***

name: turbovec-integration
description: 向量索引集成工作流。通过 Turbovec 将 Hermes 知识库升级为向量语义搜索，支持百万级文档检索。触发词：向量搜索 / 语义检索 / turbovec / 知识库升级 / 向量索引。
category: knowledge
tags: \[向量搜索, turbovec, RAG, 语义检索, 知识库]
---------------------------------------

# Turbovec 向量索引集成

## 概述

Turbovec 是高性能向量索引库，基于 Google Research TurboQuant 算法。

核心价值：用更少内存跑更大知识库（1000万向量仅需\~4GB，8x压缩比）。

## 何时使用

* 知识库需要语义搜索能力
* 文档数量超过 BM25 检索效率上限（>10万）
* 需要长期保留向量索引（持久化到磁盘）
* 内存受限但需要大规模向量检索

## 安装

```bash
pip install turbovec
```

## 核心 API

### TurboQuantIndex（轻量级，自动ID）

```python
from turbovec import TurboQuantIndex
import numpy as np

index = TurboQuantIndex(dim=1536, bit_width=4)
index.add(vectors)  # vectors: np.ndarray (N, dim), float32
scores, ids = index.search(query, k=10)
index.remove(12345)  # 按索引删除
index.write('/path/to/index.tvq')
```

### IdMapIndex（稳定ID）

```python
from turbovec import IdMapIndex

ids = np.arange(1000, 1000 + n, dtype=np.uint64)
index = IdMapIndex(dim=1536, bit_width=4)
index.add_with_ids(vectors, ids)

# 搜索时返回原始ID
scores, doc_ids = index.search(query, k=10)

# 按ID删除
index.remove(doc_id)
```

## Hermes 集成示例

```python
# engine.py
from turbovec import IdMapIndex

class KnowledgeBaseEngine:
    def __init__(self, index_path="/root/.hermes/knowledge/index.tvim"):
        self.index_path = index_path
        self.index = None
    
    def load(self):
        if os.path.exists(self.index_path):
            self.index = IdMapIndex.load(self.index_path)
        else:
            self.index = IdMapIndex(dim=1536, bit_width=4)
        return self
    
    def add_documents(self, embeddings, documents):
        ids = np.arange(start_id, start_id + len(documents), dtype=np.uint64)
        self.index.add_with_ids(embeddings, ids)
        return ids
    
    def search(self, query, k=10):
        scores, ids = self.index.search(query.reshape(1, -1), k=k)
        return list(zip(scores[0], ids[0]))
```

## 性能基准

| **操作**     | **100K向量(1536d)** |
| ---------- | ----------------- |
| 构建索引       | \~6.8s            |
| 单次搜索(k=10) | 150ms             |
| 持久化(写)     | 160ms             |
| 索引大小       | 74MB (8x压缩)       |

## 推算千万级

| **向量数** | **内存**  | **构建时间** |
| ------- | ------- | -------- |
| 100万    | \~740MB | \~70s    |
| 1000万   | \~7.4GB | \~12min  |
| 3000万   | \~22GB  | \~35min  |

## Pitfalls

1. **搜索速度**：单线程搜索约150ms，千万级可能需秒级。适合离线场景。
2. **归一化**：添加前必须归一化向量，否则搜索结果偏差。
3. **ID类型**：IdMapIndex 使用 uint64，不要混用 int64。
4. **维度固定**：创建索引时固定 dim，后续无法修改。

## 参考文件

* `references/turbovec-integration.md` — 详细集成指南和性能数据

## 步骤

1. **明确查询目标** — 确认要查找的信息
2. **检索相关内容** — 从知识库/文档中检索
3. **整理输出** — 结构化呈现结果
4. **标注来源** — 引用原始出处

## 验证

- [ ] 检索结果与查询目标相关

- [ ] 信息准确且最新

- [ ] 来源可追溯
