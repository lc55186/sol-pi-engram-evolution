#!/usr/bin/env python
"""
格式扩展工具集 - 部署/工具化模块
参数化通用工具、配置文件、定时任务集成
"""

import argparse
import configparser
import json
import os
from pathlib import Path
from typing import Any


class DeployTool:
    """部署工具：参数化通用工具、配置文件管理"""

    def __init__(self, config_path: str = None):
        self.config = {}
        self.config_path = config_path
        if config_path and os.path.exists(config_path):
            self.load_config(config_path)

    def load_config(self, config_path: str):
        """加载配置文件（支持 JSON 和 INI）"""
        path = Path(config_path)

        if path.suffix.lower() == '.json':
            with open(config_path, encoding='utf-8') as f:
                self.config = json.load(f)
        elif path.suffix.lower() in ('.ini', '.cfg', '.conf'):
            parser = configparser.ConfigParser()
            parser.read(config_path, encoding='utf-8')
            self.config = {section: dict(parser.items(section))
                          for section in parser.sections()}
        else:
            raise ValueError(f"不支持的配置文件格式: {path.suffix}")

        return self.config

    def save_config(self, config_path: str = None):
        """保存配置文件"""
        path = Path(config_path or self.config_path)
        if not path:
            raise ValueError("未指定配置文件路径")

        if path.suffix.lower() == '.json':
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        elif path.suffix.lower() in ('.ini', '.cfg', '.conf'):
            parser = configparser.ConfigParser()
            for section, values in self.config.items():
                parser[section] = {str(k): str(v) for k, v in values.items()}
            with open(path, 'w', encoding='utf-8') as f:
                parser.write(f)

    def get(self, key: str, default: Any = None,
            section: str = None) -> Any:
        """获取配置值"""
        if section:
            return self.config.get(section, {}).get(key, default)
        return self.config.get(key, default)

    def set(self, key: str, value: Any, section: str = None):
        """设置配置值"""
        if section:
            if section not in self.config:
                self.config[section] = {}
            self.config[section][key] = value
        else:
            self.config[key] = value

    def create_default_config(self, config_path: str,
                              defaults: dict[str, Any]):
        """创建默认配置文件"""
        self.config = defaults
        self.config_path = config_path
        self.save_config(config_path)
        return self.config


def create_argument_parser(description: str = "格式扩展工具") -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s convert input.csv output.json
  %(prog)s batch --input "*.csv" --output-format json --output-dir ./converted
  %(prog)s dedup --directory ./data
  %(prog)s rename --pattern "old_" --replacement "new_" --directory ./files
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # convert 命令
    convert_parser = subparsers.add_parser('convert', help='格式转换')
    convert_parser.add_argument('input', help='输入文件路径')
    convert_parser.add_argument('output', help='输出文件路径')
    convert_parser.add_argument('--input-format', help='输入格式（自动检测）')
    convert_parser.add_argument('--output-format', help='输出格式（自动检测）')

    # batch 命令
    batch_parser = subparsers.add_parser('batch', help='批量处理')
    batch_parser.add_argument('--input', required=True, help='输入文件模式（如 "*.csv"）')
    batch_parser.add_argument('--output-format', required=True, help='输出格式')
    batch_parser.add_argument('--output-dir', help='输出目录')
    batch_parser.add_argument('--directory', default='.', help='根目录')
    batch_parser.add_argument('--recursive', action='store_true', help='递归子目录')

    # dedup 命令
    dedup_parser = subparsers.add_parser('dedup', help='文件去重')
    dedup_parser.add_argument('--directory', required=True, help='要扫描的目录')
    dedup_parser.add_argument('--recursive', action='store_true', help='递归子目录')
    dedup_parser.add_argument('--delete', action='store_true', help='删除重复文件')

    # rename 命令
    rename_parser = subparsers.add_parser('rename', help='批量重命名')
    rename_parser.add_argument('--pattern', required=True, help='正则模式')
    rename_parser.add_argument('--replacement', required=True, help='替换字符串')
    rename_parser.add_argument('--directory', default='.', help='根目录')
    rename_parser.add_argument('--recursive', action='store_true', help='递归子目录')
    rename_parser.add_argument('--dry-run', action='store_true', help='预览不执行')

    # archive 命令
    archive_parser = subparsers.add_parser('archive', help='批量归档')
    archive_parser.add_argument('--pattern', required=True, help='文件模式')
    archive_parser.add_argument('--archive-dir', required=True, help='归档目录')
    archive_parser.add_argument('--directory', default='.', help='根目录')
    archive_parser.add_argument('--recursive', action='store_true', help='递归子目录')
    archive_parser.add_argument('--copy', action='store_true', help='复制而非移动')

    # merge 命令
    merge_parser = subparsers.add_parser('merge', help='合并文件')
    merge_parser.add_argument('--files', nargs='+', required=True, help='要合并的文件')
    merge_parser.add_argument('--output', required=True, help='输出文件路径')
    merge_parser.add_argument('--separator', default='\n\n', help='分隔符')

    # split 命令
    split_parser = subparsers.add_parser('split', help='拆分文件')
    split_parser.add_argument('--file', required=True, help='要拆分的文件')
    split_parser.add_argument('--output-dir', required=True, help='输出目录')
    split_parser.add_argument('--chunk-size', type=int, default=1000, help='每块大小')
    split_parser.add_argument('--by-lines', action='store_true', default=True, help='按行拆分')

    return parser


def main():
    """命令行入口"""
    parser = create_argument_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    from batch_processor import BatchProcessor
    from format_converter import FormatConverter

    converter = FormatConverter()

    if args.command == 'convert':
        converter.convert(args.input, args.output,
                         args.input_format, args.output_format)
        print(f"转换完成: {args.input} → {args.output}")

    elif args.command == 'batch':
        processor = BatchProcessor(args.directory)
        processor.batch_convert(args.input, args.output_format,
                                args.output_dir, args.recursive)
        stats = processor.get_stats()
        print(f"批量转换完成: {stats['processed']} 成功, {stats['errors']} 失败")

    elif args.command == 'dedup':
        processor = BatchProcessor(args.directory)
        duplicates = processor.deduplicate_files(args.directory, args.recursive)
        print(f"发现 {len(duplicates)} 个重复文件")
        for dup in duplicates:
            print(f"  {dup['file']} == {dup['duplicate_of']}")

    elif args.command == 'rename':
        processor = BatchProcessor(args.directory)
        results = processor.batch_rename(args.pattern, args.replacement,
                                         args.recursive, args.dry_run)
        print(f"重命名完成: {len(results)} 个文件")

    elif args.command == 'archive':
        processor = BatchProcessor(args.directory)
        processor.batch_archive(args.pattern, args.archive_dir,
                                args.recursive, args.copy)
        stats = processor.get_stats()
        print(f"归档完成: {stats['moved']} 个文件")

    elif args.command == 'merge':
        processor = BatchProcessor(".")
        processor.merge_files(args.files, args.output, args.separator)
        print(f"合并完成: {args.output}")

    elif args.command == 'split':
        processor = BatchProcessor(".")
        output_files = processor.split_file(args.file, args.output_dir,
                                            args.chunk_size, args.by_lines)
        print(f"拆分完成: {len(output_files)} 个文件")


if __name__ == '__main__':
    main()
