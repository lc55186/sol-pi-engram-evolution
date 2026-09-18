"""
格式扩展工具集 - 测试
验证 FormatConverter、BatchProcessor、PipelineTool、DeployTool
"""

import csv
import importlib.util
import sys
import os
import tempfile


def _load_module(name, rel_path):
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", rel_path
    )
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_format_converter_csv_json():
    """测试 CSV ↔ JSON 转换"""
    FormatConverter = _load_module("format_converter", "format_converter.py").FormatConverter

    with tempfile.TemporaryDirectory() as tmpdir:
        converter = FormatConverter()

        # CSV → JSON
        csv_path = os.path.join(tmpdir, 'test.csv')
        json_path = os.path.join(tmpdir, 'test.json')

        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'age', 'city'])
            writer.writerow(['Alice', 30, 'Beijing'])
            writer.writerow(['Bob', 25, 'Shanghai'])

        converter.csv_to_json(csv_path, json_path)
        data = converter.json_to_list(json_path)
        assert len(data) == 2
        assert data[0]['name'] == 'Alice'

        # JSON → CSV
        csv_path2 = os.path.join(tmpdir, 'test2.csv')
        converter.json_to_csv(json_path, csv_path2)
        data2 = converter.csv_to_list(csv_path2)
        assert len(data2) == 2

    print("✓ Format converter CSV/JSON passed")


def test_format_converter_xml():
    """测试 XML 转换"""
    FormatConverter = _load_module("format_converter", "format_converter.py").FormatConverter

    with tempfile.TemporaryDirectory() as tmpdir:
        converter = FormatConverter()

        xml_path = os.path.join(tmpdir, 'test.xml')
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8"?>
<root>
    <item>
        <name>Alice</name>
        <age>30</age>
    </item>
    <item>
        <name>Bob</name>
        <age>25</age>
    </item>
</root>''')

        data = converter.xml_to_dict(xml_path)
        assert 'item' in data

    print("✓ Format converter XML passed")


def test_batch_processor_scan():
    """测试目录扫描"""
    BatchProcessor = _load_module("batch_processor", "batch_processor.py").BatchProcessor

    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(3):
            with open(os.path.join(tmpdir, f'file_{i}.txt'), 'w') as f:
                f.write(f'content {i}')

        processor = BatchProcessor(tmpdir)
        files = processor.scan_directory('*.txt')
        assert len(files) == 3

    print("✓ Batch processor scan passed")


def test_batch_processor_rename():
    """测试批量重命名"""
    BatchProcessor = _load_module("batch_processor", "batch_processor.py").BatchProcessor

    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(3):
            with open(os.path.join(tmpdir, f'old_name_{i}.txt'), 'w') as f:
                f.write(f'content {i}')

        processor = BatchProcessor(tmpdir)
        results = processor.batch_rename(r'old_name_', 'new_name_', dry_run=True)
        assert len(results) == 3

    print("✓ Batch processor rename passed")


def test_batch_processor_dedup():
    """测试文件去重"""
    BatchProcessor = _load_module("batch_processor", "batch_processor.py").BatchProcessor

    with tempfile.TemporaryDirectory() as tmpdir:
        content = "duplicate content"
        with open(os.path.join(tmpdir, 'file1.txt'), 'w') as f:
            f.write(content)
        with open(os.path.join(tmpdir, 'file2.txt'), 'w') as f:
            f.write(content)
        with open(os.path.join(tmpdir, 'file3.txt'), 'w') as f:
            f.write("unique content")

        processor = BatchProcessor(tmpdir)
        duplicates = processor.deduplicate_files(tmpdir)
        assert len(duplicates) >= 1

    print("✓ Batch processor dedup passed")


def test_batch_processor_merge_split():
    """测试合并和拆分"""
    BatchProcessor = _load_module("batch_processor", "batch_processor.py").BatchProcessor

    with tempfile.TemporaryDirectory() as tmpdir:
        files = []
        for i in range(3):
            path = os.path.join(tmpdir, f'part_{i}.txt')
            with open(path, 'w') as f:
                f.write(f'Part {i} content\n')
            files.append(path)

        processor = BatchProcessor(tmpdir)

        merged_path = os.path.join(tmpdir, 'merged.txt')
        processor.merge_files(files, merged_path)
        assert os.path.exists(merged_path)

        split_dir = os.path.join(tmpdir, 'split')
        output_files = processor.split_file(merged_path, split_dir, chunk_size=100, by_lines=False)
        assert len(output_files) >= 1

    print("✓ Batch processor merge/split passed")


def test_pipeline_tool():
    """测试管道工具"""
    PipelineTool = _load_module("pipeline_tool", "pipeline_tool.py").PipelineTool

    pipeline = PipelineTool(name='test_pipeline')

    def step1():
        return "result1"

    def step2():
        return "result2"

    pipeline.add_step("步骤1", step1)
    pipeline.add_step("步骤2", step2)

    results = pipeline.run()
    assert len(results) == 2
    assert results[0]['status'] == 'success'
    assert results[1]['status'] == 'success'

    stats = pipeline.get_stats()
    assert stats['successful'] == 2

    print("✓ Pipeline tool passed")


def test_pipeline_tool_with_retry():
    """测试管道工具重试"""
    PipelineTool = _load_module("pipeline_tool", "pipeline_tool.py").PipelineTool

    pipeline = PipelineTool(name='test_retry')
    call_count = [0]

    def flaky_step():
        call_count[0] += 1
        if call_count[0] < 3:
            raise RuntimeError("临时错误")
        return "success"

    pipeline.add_step("重试步骤", flaky_step)
    results = pipeline.run(max_retries=3)
    assert results[0]['status'] == 'success'
    assert call_count[0] == 3

    print("✓ Pipeline tool retry passed")


def test_pipeline_html_report():
    """测试 HTML 报告生成"""
    PipelineTool = _load_module("pipeline_tool", "pipeline_tool.py").PipelineTool

    pipeline = PipelineTool(name='test_report')

    def step():
        return "ok"

    pipeline.add_step("步骤", step)
    pipeline.run()

    with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
        html_path = f.name

    pipeline.generate_html_report(html_path)
    assert os.path.exists(html_path)

    with open(html_path, encoding='utf-8') as f:
        content = f.read()
    assert 'test_report' in content
    assert '步骤' in content

    os.remove(html_path)
    print("✓ Pipeline HTML report passed")


def test_deploy_tool_config():
    """测试配置管理"""
    DeployTool = _load_module("deploy_tool", "deploy_tool.py").DeployTool

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, 'config.json')
        tool = DeployTool()
        tool.set('db_path', 'test.db')
        tool.set('archive_root', './archives')
        tool.save_config(config_path)

        tool2 = DeployTool(config_path)
        assert tool2.get('db_path') == 'test.db'
        assert tool2.get('archive_root') == './archives'

    print("✓ Deploy tool config passed")


if __name__ == '__main__':
    test_format_converter_csv_json()
    test_format_converter_xml()
    test_batch_processor_scan()
    test_batch_processor_rename()
    test_batch_processor_dedup()
    test_batch_processor_merge_split()
    test_pipeline_tool()
    test_pipeline_tool_with_retry()
    test_pipeline_html_report()
    test_deploy_tool_config()
    print("\n✅ 格式扩展工具集测试全部通过")
