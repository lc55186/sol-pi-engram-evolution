#!/usr/bin/env python
"""
阶段 1：观测包归档模块
负责将大输出/大文档/长对话归档到本地磁盘，返回稳定的 handle
并保留原始内容以便分页召回
"""

import hashlib
import json
import os
import uuid
from datetime import datetime
from typing import Any


class ObservationPack:
    """
    ObservationPack 模块
    
    负责:
    - 接收大输出/大文档/长对话内容
    - 原文归档到本地磁盘 (按日期分目录)
    - 返回稳定 handle (归档文件路径 + metadata)
    - 保留原始内容供后续分页/按需召回
    - 提供元数据访问 (创建时间, 大小, 内容类型, 摘要等)
    """

    def __init__(self, archive_root: str = "./observations",
                 max_file_size_mb: int = 100,
                 compress_large_files: bool = True,
                 default_chunk_size: int = 5000):
        """
        初始化 ObservationPack
        
        Args:
            archive_root: 归档根目录
            max_file_size_mb: 单文件最大大小 (MB)
            compress_large_files: 是否对大文件进行压缩
            default_chunk_size: 默认分块大小 (字符数)
        """
        self.archive_root = archive_root
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.compress_large_files = compress_large_files
        self.default_chunk_size = default_chunk_size
        self._ensure_archive_root()

    def _ensure_archive_root(self):
        """确保归档根目录存在"""
        if not os.path.exists(self.archive_root):
            os.makedirs(self.archive_root, exist_ok=True)

        # 创建日期分目录
        today = datetime.now().strftime("%Y-%m-%d")
        daily_dir = os.path.join(self.archive_root, today)
        if not os.path.exists(daily_dir):
            os.makedirs(daily_dir, exist_ok=True)

    def archive(self, content: str, content_type: str = "text",
                metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        归档大输出内容
        
        Args:
            content: 要归档的内容 (字符串)
            content_type: 内容类型 (text, json, markdown, code 等)
            metadata: 额外元数据 (可选)
            
        Returns:
            包含 handle 和元数据的字典
        """
        timestamp = datetime.now().isoformat()
        content_id = str(uuid.uuid4())

        # 生成文件名
        file_ext = self._get_extension(content_type)
        filename = f"{content_id}{file_ext}"

        # 日期目录
        today = datetime.now().strftime("%Y-%m-%d")
        daily_dir = os.path.join(self.archive_root, today)
        filepath = os.path.join(daily_dir, filename)

        # 计算内容哈希 (用于验证完整性)
        content_hash = self._compute_hash(content)

        # 计算大小
        byte_size = len(content.encode('utf-8'))

        # 构建元数据
        meta = {
            'content_id': content_id,
            'content_type': content_type,
            'original_size': byte_size,
            'content_hash': content_hash,
            'archived_at': timestamp,
            'daily_dir': today,
            'filepath': filepath,
            'chunk_size': self.default_chunk_size,
        }

        if metadata:
            meta.update(metadata)

        # 写入文件
        self._write_archive(filepath, content, meta)

        # 生成 handle
        handle = {
            'type': 'observation_pack_handle',
            'content_id': content_id,
            'filepath': filepath,
            'daily_dir': today,
            'content_type': content_type,
            'original_size': byte_size,
            'content_hash': content_hash,
            'archived_at': timestamp,
            'metadata': meta,
        }

        return handle

    def _write_archive(self, filepath: str, content: str,
                       meta: dict[str, Any]):
        """写入归档文件"""
        # 检查大小
        if len(content.encode('utf-8')) > self.max_file_size_bytes:
            raise ValueError(
                f"Content size ({len(content.encode('utf-8'))} bytes) "
                f"exceeds max file size ({self.max_file_size_bytes} bytes)"
            )

        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # 写入内容
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        # 存储元数据文件
        meta_path = f"{filepath}.meta.json"
        meta['file_size'] = os.path.getsize(filepath)
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def _get_extension(self, content_type: str) -> str:
        """根据内容类型获取文件扩展名"""
        ext_map = {
            'text': '.txt',
            'json': '.json',
            'markdown': '.md',
            'code': '.code.txt',
            'html': '.html',
            'xml': '.xml',
            'csv': '.csv',
            'log': '.log',
        }
        return ext_map.get(content_type, '.txt')

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希值"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def retrieve(self, handle: dict[str, Any],
                 chunk_index: int | None = None) -> dict[str, Any]:
        """
        从归档中召回内容
        
        Args:
            handle: 归档 handle
            chunk_index: 分块索引 (None = 返回全部)
            
        Returns:
            包含召回内容和元数据的字典
        """
        filepath = handle.get('filepath')
        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError(f"Archive file not found: {filepath}")

        with open(filepath, encoding='utf-8') as f:
            content = f.read()

        # 验证完整性
        content_hash = self._compute_hash(content)
        if content_hash != handle.get('content_hash'):
            raise ValueError("Content integrity check failed")

        # 分块处理
        if chunk_index is not None:
            chunks = self._chunk(content, handle.get('chunk_size', self.default_chunk_size))
            if chunk_index >= len(chunks):
                raise IndexError(f"Chunk index {chunk_index} out of range (total: {len(chunks)})")
            content = chunks[chunk_index]
            is_chunked = True
            total_chunks = len(chunks)
        else:
            chunks = self._chunk(content, handle.get('chunk_size', self.default_chunk_size))
            is_chunked = False
            total_chunks = len(chunks)

        # 读取元数据
        meta_path = f"{filepath}.meta.json"
        meta = {}
        if os.path.exists(meta_path):
            with open(meta_path, encoding='utf-8') as f:
                meta = json.load(f)

        return {
            'content': content,
            'handle': handle,
            'chunk_index': chunk_index,
            'is_chunked': is_chunked,
            'total_chunks': total_chunks,
            'current_chunk_size': len(content),
            'content_hash': content_hash,
            'metadata': meta,
        }

    def _chunk(self, content: str, chunk_size: int) -> list:
        """将内容分块"""
        if chunk_size <= 0:
            return [content]

        chunks = []
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            chunks.append(chunk)

        return chunks

    def delete(self, handle: dict[str, Any]) -> bool:
        """
        删除归档
        
        Args:
            handle: 归档 handle
            
        Returns:
            是否成功删除
        """
        filepath = handle.get('filepath')
        if not filepath or not os.path.exists(filepath):
            return False

        # 删除主文件
        os.remove(filepath)

        # 删除元数据文件
        meta_path = f"{filepath}.meta.json"
        if os.path.exists(meta_path):
            os.remove(meta_path)

        return True

    def list_archives(self, date: str | None = None) -> list:
        """
        列出归档列表
        
        Args:
            date: 指定日期 (格式: YYYY-MM-DD), None = 今天
            
        Returns:
            归档列表
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        daily_dir = os.path.join(self.archive_root, date)
        if not os.path.exists(daily_dir):
            return []

        archives = []
        for filename in os.listdir(daily_dir):
            if filename.endswith('.meta.json'):
                continue

            filepath = os.path.join(daily_dir, filename)
            meta_path = f"{filepath}.meta.json"

            meta = {}
            if os.path.exists(meta_path):
                with open(meta_path, encoding='utf-8') as f:
                    meta = json.load(f)

            archives.append({
                'filepath': filepath,
                'daily_dir': date,
                'content_id': meta.get('content_id', ''),
                'content_type': meta.get('content_type', 'unknown'),
                'original_size': meta.get('original_size', 0),
                'archived_at': meta.get('archived_at', ''),
                'content_hash': meta.get('content_hash', ''),
            })

        return sorted(archives, key=lambda x: x['archived_at'], reverse=True)

    def cleanup_old_archives(self, retention_days: int = 30) -> int:
        """
        清理旧归档
        
        Args:
            retention_days: 保留天数
            
        Returns:
            删除的归档数量
        """
        deleted_count = 0
        cutoff_date = datetime.now()

        for root, dirs, files in os.walk(self.archive_root):
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    dir_date = datetime.strptime(dir_name, "%Y-%m-%d")
                    if (cutoff_date - dir_date).days > retention_days:
                        # 删除整个日期目录
                        for file in os.listdir(dir_path):
                            file_path = os.path.join(dir_path, file)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                        os.rmdir(dir_path)
                        deleted_count += 1
                except ValueError:
                    # 不是日期格式的目录，跳过
                    pass

        return deleted_count


# 全局单例 (用于模块内共享)
_observation_pack_instance = None


def get_observation_pack(**kwargs) -> ObservationPack:
    """获取 ObservationPack 实例 (单例模式)"""
    global _observation_pack_instance
    if _observation_pack_instance is None:
        _observation_pack_instance = ObservationPack(**kwargs)
    return _observation_pack_instance


# 便捷函数
def archive_content(content: str, content_type: str = "text",
                   metadata: dict | None = None) -> dict[str, Any]:
    """归档内容的便捷函数"""
    pack = get_observation_pack()
    return pack.archive(content, content_type, metadata)


def retrieve_content(handle: dict[str, Any],
                    chunk_index: int | None = None) -> dict[str, Any]:
    """召回内容的便捷函数"""
    pack = get_observation_pack()
    return pack.retrieve(handle, chunk_index)


def delete_content(handle: dict[str, Any]) -> bool:
    """删除内容的便捷函数"""
    pack = get_observation_pack()
    return pack.delete(handle)
