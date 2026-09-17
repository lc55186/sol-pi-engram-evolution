#!/usr/bin/env python
"""
格式扩展工具集 - 批量处理器
扫目录树、按规则批量转换、重命名、归档、合并、分拆、去重
"""

import hashlib
import os
import re
import shutil
from collections.abc import Callable
from datetime import datetime
from pathlib import Path


class BatchProcessor:
    """批量处理器：扫目录树、按规则批量转换、重命名、归档"""

    def __init__(self, root_dir: str = ".",
                 log_callback: Callable = None):
        self.root_dir = root_dir
        self.log_callback = log_callback or print
        self.stats = {
            'processed': 0,
            'skipped': 0,
            'errors': 0,
            'renamed': 0,
            'moved': 0,
        }

    def scan_directory(self, pattern: str = "*",
                       recursive: bool = True,
                       file_only: bool = True) -> list[str]:
        """扫描目录树，返回匹配的文件路径列表"""
        results = []
        root = Path(self.root_dir)

        if recursive:
            files = root.rglob(pattern)
        else:
            files = root.glob(pattern)

        for f in files:
            if file_only and not f.is_file():
                continue
            results.append(str(f))

        return sorted(results)

    def batch_rename(self, pattern: str,
                     replacement: str,
                     recursive: bool = True,
                     dry_run: bool = False) -> list[dict]:
        """批量重命名文件"""
        files = self.scan_directory("*", recursive)
        results = []

        for filepath in files:
            old_name = os.path.basename(filepath)
            new_name = re.sub(pattern, replacement, old_name)

            if new_name != old_name:
                new_path = os.path.join(os.path.dirname(filepath), new_name)
                result = {
                    'old': filepath,
                    'new': new_path,
                    'status': 'pending'
                }

                if not dry_run:
                    try:
                        os.rename(filepath, new_path)
                        result['status'] = 'renamed'
                        self.stats['renamed'] += 1
                    except Exception as e:
                        result['status'] = f'error: {e}'
                        self.stats['errors'] += 1
                else:
                    result['status'] = 'dry_run'

                results.append(result)
                self.log_callback(
                    f"{'[预览] ' if dry_run else ''}重命名: {old_name} → {new_name}"
                )

        return results

    def batch_convert(self, input_pattern: str,
                      output_format: str,
                      output_dir: str = None,
                      recursive: bool = True,
                      converter = None) -> list[dict]:
        """批量转换文件格式"""
        from format_converter import FormatConverter
        converter = converter or FormatConverter()

        files = self.scan_directory(input_pattern, recursive)
        results = []

        for filepath in files:
            input_path = Path(filepath)
            stem = input_path.stem

            if output_dir:
                out_dir = Path(output_dir)
                out_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(out_dir / f"{stem}.{output_format}")
            else:
                output_path = str(input_path.with_suffix(f".{output_format}"))

            result = {
                'input': filepath,
                'output': output_path,
                'status': 'pending'
            }

            try:
                converter.convert(filepath, output_path)
                result['status'] = 'converted'
                self.stats['processed'] += 1
            except Exception as e:
                result['status'] = f'error: {e}'
                self.stats['errors'] += 1

            results.append(result)
            self.log_callback(
                f"转换: {input_path.name} → {Path(output_path).name} ({result['status']})"
            )

        return results

    def batch_archive(self, pattern: str,
                      archive_dir: str,
                      recursive: bool = True,
                      copy: bool = False) -> list[dict]:
        """批量归档文件到指定目录"""
        files = self.scan_directory(pattern, recursive)
        results = []

        archive_path = Path(archive_dir)
        archive_path.mkdir(parents=True, exist_ok=True)

        for filepath in files:
            src = Path(filepath)
            dst = archive_path / src.name

            # 处理重名
            if dst.exists():
                stem = src.stem
                suffix = src.suffix
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dst = archive_path / f"{stem}_{timestamp}{suffix}"

            result = {
                'source': filepath,
                'destination': str(dst),
                'status': 'pending'
            }

            try:
                if copy:
                    shutil.copy2(filepath, str(dst))
                else:
                    shutil.move(filepath, str(dst))
                result['status'] = 'archived'
                self.stats['moved'] += 1
            except Exception as e:
                result['status'] = f'error: {e}'
                self.stats['errors'] += 1

            results.append(result)
            self.log_callback(
                f"归档: {src.name} → {archive_dir}"
            )

        return results

    def batch_delete(self, pattern: str,
                     recursive: bool = True,
                     dry_run: bool = True) -> list[dict]:
        """批量删除文件（默认 dry_run）"""
        files = self.scan_directory(pattern, recursive)
        results = []

        for filepath in files:
            result = {
                'file': filepath,
                'status': 'pending'
            }

            if not dry_run:
                try:
                    os.remove(filepath)
                    result['status'] = 'deleted'
                    self.stats['processed'] += 1
                except Exception as e:
                    result['status'] = f'error: {e}'
                    self.stats['errors'] += 1
            else:
                result['status'] = 'dry_run'

            results.append(result)
            self.log_callback(
                f"{'[预览] ' if dry_run else ''}删除: {filepath}"
            )

        return results

    def deduplicate_files(self, directory: str,
                          recursive: bool = True) -> list[dict]:
        """文件去重（基于 SHA256 哈希）"""
        files = self.scan_directory("*", recursive)
        hashes = {}
        duplicates = []

        for filepath in files:
            file_hash = self._file_hash(filepath)
            if file_hash in hashes:
                duplicates.append({
                    'file': filepath,
                    'duplicate_of': hashes[file_hash],
                    'hash': file_hash,
                })
            else:
                hashes[file_hash] = filepath

        return duplicates

    def _file_hash(self, filepath: str, chunk_size: int = 8192) -> str:
        """计算文件 SHA256 哈希"""
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()

    def merge_files(self, file_list: list[str],
                    output_path: str,
                    separator: str = "\n\n") -> bool:
        """合并多个文件"""
        contents = []
        for filepath in file_list:
            try:
                with open(filepath, encoding='utf-8', errors='replace') as f:
                    contents.append(f.read())
            except Exception as e:
                self.log_callback(f"读取失败 {filepath}: {e}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(separator.join(contents))

        return True

    def split_file(self, filepath: str,
                   output_dir: str,
                   chunk_size: int = 1000,
                   by_lines: bool = True) -> list[str]:
        """拆分文件"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        output_files = []

        with open(filepath, encoding='utf-8', errors='replace') as f:
            if by_lines:
                lines = f.readlines()
                total_chunks = (len(lines) + chunk_size - 1) // chunk_size
                for i in range(total_chunks):
                    chunk_lines = lines[i * chunk_size:(i + 1) * chunk_size]
                    output_path = os.path.join(
                        output_dir,
                        f"{Path(filepath).stem}_part{i + 1:04d}{Path(filepath).suffix}"
                    )
                    with open(output_path, 'w', encoding='utf-8') as out:
                        out.writelines(chunk_lines)
                    output_files.append(output_path)
            else:
                content = f.read()
                total_chunks = (len(content) + chunk_size - 1) // chunk_size
                for i in range(total_chunks):
                    chunk = content[i * chunk_size:(i + 1) * chunk_size]
                    output_path = os.path.join(
                        output_dir,
                        f"{Path(filepath).stem}_part{i + 1:04d}{Path(filepath).suffix}"
                    )
                    with open(output_path, 'w', encoding='utf-8') as out:
                        out.write(chunk)
                    output_files.append(output_path)

        return output_files

    def get_stats(self) -> dict[str, int]:
        """获取处理统计"""
        return dict(self.stats)

    def reset_stats(self):
        """重置统计"""
        self.stats = dict.fromkeys(self.stats, 0)


# 便捷函数
def batch_rename(root_dir: str, pattern: str, replacement: str,
                 recursive: bool = True, dry_run: bool = False) -> list[dict]:
    """批量重命名便捷函数"""
    processor = BatchProcessor(root_dir)
    return processor.batch_rename(pattern, replacement, recursive, dry_run)


def batch_convert(root_dir: str, input_pattern: str,
                  output_format: str, output_dir: str = None,
                  recursive: bool = True) -> list[dict]:
    """批量转换便捷函数"""
    processor = BatchProcessor(root_dir)
    return processor.batch_convert(input_pattern, output_format,
                                   output_dir, recursive)


def deduplicate(directory: str, recursive: bool = True) -> list[dict]:
    """文件去重便捷函数"""
    processor = BatchProcessor(directory)
    return processor.deduplicate_files(directory, recursive)
