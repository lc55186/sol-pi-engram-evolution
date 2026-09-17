#!/usr/bin/env python3
"""
Ghidra Headless 实战练习：分析 WinHelloCPP.exe
目标：熟悉 Ghidra 无头模式工作流程
"""
import json
import os
import subprocess
import sys
from datetime import datetime

# 配置
GHIDRA_HOME = r"C:\Program Files\Ghidra\ghidra_12.1.3_PUBLIC"
ANALYZE_HEADLESS = os.path.join(GHIDRA_HOME, "support", "analyzeHeadless.bat")
JAVA_HOME = r"C:\Program Files\Java\jdk-25\jdk-25.0.4+7"

# 目标文件
TARGET = r"C:\Program Files\Ghidra\ghidra_12.1.3_PUBLIC\docs\GhidraClass\ExerciseFiles\WinhelloCPP\WinHelloCPP.exe"

# 项目路径
PROJECT_DIR = r"C:\Users\liuchao\Desktop\ghidra_projects\ioli_test"
PROJECT_NAME = "ioli_test"


def run_headless():
    """执行完整的 headless 分析流程"""

    print("=" * 60)
    print("Ghidra Headless 实战练习")
    print("=" * 60)
    print(f"目标: {TARGET}")
    print(f"项目: {PROJECT_DIR}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 确保项目目录存在
    os.makedirs(PROJECT_DIR, exist_ok=True)

    # 设置环境
    env = os.environ.copy()
    env["JAVA_HOME"] = JAVA_HOME
    env["PATH"] = os.path.join(JAVA_HOME, "bin") + ";" + env.get("PATH", "")

    # Step 1: 导入文件
    print("[Step 1] 导入二进制文件...")
    cmd_import = [
        "cmd", "/c", ANALYZE_HEADLESS,
        PROJECT_DIR,
        PROJECT_NAME,
        "-import", TARGET,
    ]

    result_import = subprocess.run(
        cmd_import, capture_output=True, timeout=120, env=env
    )
    result_import.stdout = result_import.stdout.decode('cp1252', errors='replace') if result_import.stdout else ''
    result_import.stderr = result_import.stderr.decode('cp1252', errors='replace') if result_import.stderr else ''

    print(f"  Return code: {result_import.returncode}")
    if result_import.stdout:
        print(f"  stdout: {result_import.stdout[:500]}")
    if result_import.stderr:
        print(f"  stderr: {result_import.stderr[:500]}")

    if result_import.returncode != 0:
        print("  [ERROR] 导入失败!")
        return False

    print("  [OK] 导入成功")
    print()

    # Step 2: 分析 + 导出报告脚本
    print("[Step 2] 执行分析 + 导出报告...")

    # 创建导出脚本
    script_content = """
import json
import os

result = {
    "program": currentProgram.getName(),
    "language": currentProgram.getLanguage().toString(),
    "compiler": currentProgram.getCompiler(),
    "entry_points": [],
    "functions": [],
    "strings": [],
    "imports": [],
    "sections": []
}

# 入口点
entry = currentProgram.getMinAddress()
if entry:
    result["entry_points"].append(str(entry))

# 函数列表
funcs = currentProgram.getFunctionManager().getFunctions(True)
for f in funcs:
    func_info = {
        "name": f.getName(),
        "address": str(f.getEntryPoint()),
        "size": f.getBody().getNumAddresses(),
    }
    result["functions"].append(func_info)

# 字符串
from ghidra.program.model.data import StringDataInstance
try:
    for s in StringDataInstance.getStringInstances(currentProgram.getListing(), None, None):
        result["strings"].append({
            "address": str(s.getAddress()),
            "value": str(s),
            "length": len(str(s)),
        })
        if len(result["strings"]) >= 500:
            break
except:
    pass

# 符号/导入
sym_table = currentProgram.getSymbolTable()
try:
    for sym in sym_table.getExternalSymbols():
        result["imports"].append({
            "name": sym.getName(),
            "address": str(sym.getAddress()) if sym.getAddress() else "N/A",
        })
        if len(result["imports"]) >= 200:
            break
except:
    pass

# 节区
block = currentProgram.getMemory()
for m in block.getBlocks():
    result["sections"].append({
        "name": m.getName(),
        "start": str(m.getStart()),
        "end": str(m.getEnd()),
        "size": m.getSize(),
        "permissions": {
            "read": m.isRead(),
            "write": m.isWrite(),
            "execute": m.isExecute(),
        }
    })

# 写出到临时目录
output_dir = os.path.join("C:", "Users", "liuchao", "Desktop", "ghidra_projects", "ioli_test")
output_path = os.path.join(output_dir, "WinHelloCPP_report.json")

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"Report saved to: {output_path}")
"""

    script_dir = os.path.join(PROJECT_DIR, "scripts")
    os.makedirs(script_dir, exist_ok=True)
    script_path = os.path.join(script_dir, "export_report.py")

    with open(script_path, "w", encoding="utf-8") as f:
        f.write(script_content)

    cmd_analyze = [
        "cmd", "/c", ANALYZE_HEADLESS,
        PROJECT_DIR,
        PROJECT_NAME,
        "-process", "WinHelloCPP.exe",
        "-postScript", "export_report.py",
    ]

    result_analyze = subprocess.run(
        cmd_analyze, capture_output=True, timeout=300, env=env
    )
    result_analyze.stdout = result_analyze.stdout.decode('cp1252', errors='replace') if result_analyze.stdout else ''
    result_analyze.stderr = result_analyze.stderr.decode('cp1252', errors='replace') if result_analyze.stderr else ''

    print(f"  Return code: {result_analyze.returncode}")
    if result_analyze.stdout:
        print(f"  stdout: {result_analyze.stdout[:800]}")
    if result_analyze.stderr:
        print(f"  stderr: {result_analyze.stderr[:500]}")

    if result_analyze.returncode != 0:
        print("  [WARN] 分析可能有警告，检查输出...")

    print("  [OK] 分析完成")
    print()

    # Step 3: 读取报告
    print("[Step 3] 读取分析报告...")
    report_path = os.path.join(PROJECT_DIR, "WinHelloCPP_report.json")

    if os.path.exists(report_path):
        with open(report_path, encoding="utf-8") as f:
            report = json.load(f)

        print(f"  [OK] 报告已生成: {report_path}")
        print()
        print("=" * 60)
        print("分析报告摘要")
        print("=" * 60)
        print(f"程序: {report.get('program')}")
        print(f"语言: {report.get('language')}")
        print(f"编译器: {report.get('compiler')}")
        print(f"入口点: {report.get('entry_points')}")
        print(f"函数数量: {len(report.get('functions', []))}")
        print(f"字符串数量: {len(report.get('strings', []))}")
        print(f"导入符号: {len(report.get('imports', []))}")
        print(f"节区数量: {len(report.get('sections', []))}")
        print()

        # 显示函数列表（前10个）
        funcs = report.get("functions", [])
        if funcs:
            print("函数列表 (前10个):")
            for f in funcs[:10]:
                print(f"  {f['address']} | {f['name']} | {f['size']} addrs")
            if len(funcs) > 10:
                print(f"  ... 还有 {len(funcs) - 10} 个函数")
            print()

        # 显示字符串（前10个）
        strings = report.get("strings", [])
        if strings:
            print("字符串列表 (前10个):")
            for s in strings[:10]:
                print(f"  {s['address']} | {s['value'][:60]}")
            if len(strings) > 10:
                print(f"  ... 还有 {len(strings) - 10} 个字符串")
            print()

        # 显示节区
        sections = report.get("sections", [])
        if sections:
            print("节区列表:")
            for sec in sections:
                print(f"  {sec['name']} | {sec['start']} - {sec['end']} | "
                      f"R={'Y' if sec['permissions']['read'] else 'N'} "
                      f"W={'Y' if sec['permissions']['write'] else 'N'} "
                      f"X={'Y' if sec['permissions']['execute'] else 'N'}")
            print()

        return True
    else:
        print(f"  [ERROR] 报告文件不存在: {report_path}")
        return False


if __name__ == "__main__":
    success = run_headless()
    sys.exit(0 if success else 1)
