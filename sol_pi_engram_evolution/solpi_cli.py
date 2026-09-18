#!/usr/bin/env python3
"""
SoL-Pi Engram 融合系统命令行工具
提供格式转换、批量处理、图谱操作、归档管理的 CLI 接口
"""

import argparse
import importlib.util
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_mod(name, rel_path):
    """动态加载兄弟模块"""
    path = os.path.join(BASE_DIR, rel_path)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cmd_format_convert(args):
    """格式转换命令"""
    fc = load_mod("format_converter", "format_converter.py")
    converter = fc.FormatConverter()

    with open(args.input, encoding='utf-8') as f:
        content = f.read()

    input_ext = os.path.splitext(args.input)[1].lower()

    if input_ext == '.csv':
        data = converter.csv_to_json(content)
    elif input_ext == '.json':
        data = json.loads(content)
    elif input_ext == '.xml':
        data = converter.xml_to_json(content)
    else:
        print(json.dumps({"error": f"Unsupported input: {input_ext}"}, ensure_ascii=False))
        return

    if args.format == 'json':
        result = json.dumps(data, ensure_ascii=False, indent=2)
    elif args.format == 'csv':
        result = converter.json_to_csv(data)
    elif args.format == 'xml':
        result = converter.json_to_xml(data, root_name=args.root or "records")
    else:
        print(json.dumps({"error": f"Unsupported output: {args.format}"}, ensure_ascii=False))
        return

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
    else:
        print(result)


def cmd_format_batch(args):
    """批量转换"""
    fc = load_mod("format_converter", "format_converter.py")
    converter = fc.FormatConverter()

    results = converter.batch_convert(args.input_dir, args.output_dir, args.format)

    print(json.dumps({
        "total": len(results),
        "success": sum(1 for r in results if r.get("success")),
        "failed": sum(1 for r in results if not r.get("success")),
    }, ensure_ascii=False, indent=2))


def cmd_graph_stats(args):
    """图谱统计"""
    gs = load_mod("graph_store", "graph_store.py")
    store = gs.GraphStore(db_path=args.db)
    stats = store.get_node_stats()
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    store.close()


def cmd_graph_search(args):
    """图谱搜索"""
    gs = load_mod("graph_store", "graph_store.py")
    gr = load_mod("graph_retriever", "graph_retriever.py")
    store = gs.GraphStore(db_path=args.db)
    retriever = gr.GraphRetriever(store)

    results = retriever.retrieve(args.query, top_k=args.top_k)
    output = []
    for node, score in results:
        output.append({
            "node_id": node.get("node_id"),
            "node_type": node.get("node_type"),
            "title": node.get("title"),
            "score": round(score, 2),
        })

    print(json.dumps(output, ensure_ascii=False, indent=2))
    store.close()


def cmd_graph_add_task(args):
    """添加任务节点"""
    gs = load_mod("graph_store", "graph_store.py")
    store = gs.GraphStore(db_path=args.db)

    node_id = store.add_task_node(
        title=args.title,
        description=args.description or "",
        priority=args.priority,
    )

    print(json.dumps({"node_id": node_id, "status": "created"}, ensure_ascii=False))
    store.close()


def cmd_archive(args):
    """归档内容"""
    op = load_mod("observation_pack", "observation_pack.py")
    pack = op.ObservationPack(archive_root=args.archive_dir)

    with open(args.file, encoding='utf-8') as f:
        content = f.read()

    handle = pack.archive(content, content_type=args.content_type)
    print(json.dumps({
        "content_id": handle["content_id"],
        "filepath": handle["filepath"],
        "content_hash": handle["content_hash"],
    }, ensure_ascii=False, indent=2))


def cmd_archive_retrieve(args):
    """召回归档内容"""
    op = load_mod("observation_pack", "observation_pack.py")
    pack = op.ObservationPack(archive_root=args.archive_dir)

    handle = {"content_id": args.content_id, "filepath": args.filepath}
    result = pack.retrieve(handle, chunk_index=args.chunk)

    print(json.dumps({
        "content": result["content"],
        "chunk_index": result["chunk_index"],
        "total_chunks": result["total_chunks"],
    }, ensure_ascii=False, indent=2))


def cmd_value_evaluate(args):
    """评估节点价值"""
    gs = load_mod("graph_store", "graph_store.py")
    ve = load_mod("value_evaluator", "value_evaluator.py")
    store = gs.GraphStore(db_path=args.db)
    evaluator = ve.ValueEvaluator(store)

    node = store.get_node_by_id(args.node_id)
    if node:
        score = evaluator.evaluate(node)
        print(json.dumps({"node_id": args.node_id, "score": round(score, 4)}, ensure_ascii=False))
    else:
        print(json.dumps({"error": "Node not found"}))

    store.close()


def cmd_ghidra(args):
    """Ghidra 无头分析"""
    from ghidra_headless import run_ghidra_analysis
    result = run_ghidra_analysis(args.file, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_csv_report(args):
    """CSV 销售数据报告"""
    import os

    from csv_report import CSVReportGenerator, generate_demo_data

    input_dir = os.path.expanduser(args.input_dir)
    output_dir = os.path.expanduser(args.output) if args.output else None

    if args.demo:
        from csv_report import generate_demo_data
        demo_dir = os.path.join(input_dir, "sales_demo")
        generate_demo_data(demo_dir)
        input_dir = demo_dir

    generator = CSVReportGenerator(input_dir, output_dir)
    generator.load_csv_files()
    generator.clean_data_rows()
    generator.calculate_stats()
    report_md = generator.generate_report(args.title)
    output_path = generator.save_report()
    print(f"\n报告已保存: {output_path}")


def cmd_adapters(args):
    """谈判工具适配器管理"""
    from negotiation_adapters import get_adapter_manager
    manager = get_adapter_manager()
    
    if args.action:
        # 执行动作
        import asyncio
        params = json.loads(args.params) if args.params else {}
        result = asyncio.run(manager.execute(args.adapter, args.action, params))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 列出所有适配器
        schemas = manager.get_all_schemas()
        print(json.dumps(schemas, ensure_ascii=False, indent=2))


def cmd_sandbox(args):
    """合规沙盒检查"""
    from compliance_sandbox import get_sandbox
    sandbox = get_sandbox()
    result = sandbox.check(args.action, args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_tokenjuice(args):
    """TokenJuice 压缩测试"""
    from observation_pack import ObservationPack
    pack = ObservationPack()
    
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif args.text:
        text = args.text
    else:
        print("Error: --file or --text required")
        return
    
    # 创建临时文件测试压缩
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(text)
        tmp_path = f.name
    
    result = pack.compress_with_tokenjuice(tmp_path, args.tier)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    import os
    os.unlink(tmp_path)


def main():
    parser = argparse.ArgumentParser(
        description="SoL-Pi Engram Evolution System CLI",
        prog="solpi",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # format convert
    p_conv = sub.add_parser("convert", help="Convert between CSV/JSON/XML")
    p_conv.add_argument("input", help="Input file path")
    p_conv.add_argument("-f", "--format", required=True, choices=["json", "csv", "xml"])
    p_conv.add_argument("-o", "--output", help="Output file path")
    p_conv.add_argument("--root", help="XML root element name")

    # format batch
    p_batch = sub.add_parser("batch", help="Batch convert directory")
    p_batch.add_argument("input_dir", help="Input directory")
    p_batch.add_argument("output_dir", help="Output directory")
    p_batch.add_argument("-f", "--format", required=True, choices=["json", "csv", "xml"])

    # graph stats
    sub.add_parser("stats", help="Graph statistics").add_argument("--db", default="evolution.db")

    # graph search
    p_search = sub.add_parser("search", help="Search graph nodes")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--db", default="evolution.db")
    p_search.add_argument("--top-k", type=int, default=5)

    # graph add-task
    p_task = sub.add_parser("add-task", help="Add task node")
    p_task.add_argument("title", help="Task title")
    p_task.add_argument("-d", "--description", help="Task description")
    p_task.add_argument("-p", "--priority", type=int, default=3, choices=[1, 2, 3, 4, 5])
    p_task.add_argument("--db", default="evolution.db")

    # archive
    p_arch = sub.add_parser("archive", help="Archive file")
    p_arch.add_argument("file", help="File to archive")
    p_arch.add_argument("--content-type", default="text")
    p_arch.add_argument("--archive-dir", default="./observations")

    # archive retrieve
    p_retr = sub.add_parser("retrieve", help="Retrieve archived content")
    p_retr.add_argument("--content-id", required=True)
    p_retr.add_argument("--filepath", required=True)
    p_retr.add_argument("--chunk", type=int, default=None)
    p_retr.add_argument("--archive-dir", default="./observations")

    # value evaluate
    p_val = sub.add_parser("evaluate", help="Evaluate node value")
    p_val.add_argument("node_id", help="Node ID")
    p_val.add_argument("--db", default="evolution.db")

    # csv report
    p_csv = sub.add_parser("csv-report", help="Generate sales report from CSV files")
    p_csv.add_argument("input_dir", help="CSV files directory")
    p_csv.add_argument("-o", "--output", help="Output directory")
    p_csv.add_argument("--title", default="销售数据报告")
    p_csv.add_argument("--demo", action="store_true", help="Generate demo data")

    # ghidra analyze
    p_ghidra = sub.add_parser("ghidra", help="Ghidra headless binary analysis")
    p_ghidra.add_argument("file", help="Binary file to analyze")
    p_ghidra.add_argument("-o", "--output", help="Report output directory")
    p_ghidra.add_argument("-p", "--project", help="Project name", default="analysis")
    p_ghidra.add_argument("--no-report", action="store_true", help="Skip report export")

    # negotiation adapters
    p_adapt = sub.add_parser("adapters", help="List negotiation tool adapters")
    p_adapt.add_argument("--action", help="Action to execute")
    p_adapt.add_argument("--adapter", help="Adapter name", default="crm")
    p_adapt.add_argument("--params", help="Action params (JSON)")

    # compliance sandbox
    p_sandbox = sub.add_parser("sandbox", help="Test compliance sandbox")
    p_sandbox.add_argument("--action", required=True, help="Action to check")
    p_sandbox.add_argument("--target", required=True, help="Target path/URL")

    # tokenjuice compression
    p_tj = sub.add_parser("tokenjuice", help="Test TokenJuice compression")
    p_tj.add_argument("--file", help="File to compress")
    p_tj.add_argument("--text", help="Text to compress")
    p_tj.add_argument("--tier", default="short_term", choices=["ephemeral", "short_term", "long_term"])

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "convert": cmd_format_convert,
        "batch": cmd_format_batch,
        "stats": cmd_graph_stats,
        "search": cmd_graph_search,
        "add-task": cmd_graph_add_task,
        "archive": cmd_archive,
        "retrieve": cmd_archive_retrieve,
        "evaluate": cmd_value_evaluate,
        "ghidra": cmd_ghidra,
        "csv-report": cmd_csv_report,
        "adapters": cmd_adapters,
        "sandbox": cmd_sandbox,
        "tokenjuice": cmd_tokenjuice,
    }

    func = commands.get(args.command)
    if func:
        func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
