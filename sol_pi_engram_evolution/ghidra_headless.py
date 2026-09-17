#!/usr/bin/env python3
"""
Ghidra Headless 无头模式自动化分析引擎
集成到 SoL-Pi 融合系统工作流
支持：二进制导入、自动分析、脚本执行、报告导出
"""
import json
import logging
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

# === 配置 ===
GHIDRA_HOME = r"C:\Program Files\Ghidra\ghidra_12.1.3_PUBLIC"
ANALYZE_HEADLESS = os.path.join(GHIDRA_HOME, "support", "analyzeHeadless.bat")
JAVA_HOME = r"C:\Program Files\Java\jdk-25\jdk-25.0.4+7"

# 项目存储位置
PROJECT_DIR = os.path.expanduser("~/Desktop/ghidra_projects")
REPORT_DIR = os.path.expanduser("~/Desktop/ghidra_reports")


class GhidraHeadless:
    """Ghidra 无头模式引擎"""

    def __init__(self, project_name: str = "analysis", project_path: str = None):
        self.logger = self._setup_logger()
        self.project_name = project_name
        self.project_path = project_path or os.path.join(PROJECT_DIR, datetime.now().strftime("%Y%m%d"))
        self.current_program = None

        os.makedirs(self.project_path, exist_ok=True)
        os.makedirs(REPORT_DIR, exist_ok=True)

        # 设置 JAVA_HOME
        os.environ["JAVA_HOME"] = JAVA_HOME
        os.environ["PATH"] = os.path.join(JAVA_HOME, "bin") + ";" + os.environ.get("PATH", "")

    def _setup_logger(self):
        logger = logging.getLogger("ghidra_headless")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s"))
            logger.addHandler(handler)
        return logger

    def _run_cmd(self, cmd: list[str], timeout: int = 300) -> dict[str, Any]:
        """执行命令并返回结果"""
        self.logger.info(f"执行: {' '.join(cmd[:10])}...")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy(),
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"超时 ({timeout}s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def import_file(self, file_path: str, recursive: bool = False) -> dict[str, Any]:
        """
        导入二进制文件到 Ghidra 项目
        analyzeHeadless <project_location> <project_name> -import <file>
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": f"文件不存在: {file_path}"}

        cmd = [
            "cmd", "/c", ANALYZE_HEADLESS,
            self.project_path,
            self.project_name,
            "-import", file_path,
        ]

        if recursive:
            cmd.append("-recursive")

        result = self._run_cmd(cmd, timeout=120)

        if result["success"]:
            self.current_program = os.path.basename(file_path)
            self.logger.info(f"导入成功: {file_path}")
        else:
            self.logger.error(f"导入失败: {result.get('stderr', result.get('error', ''))}")

        return result

    def analyze(self, script_path: str = None, script_args: list[str] = None) -> dict[str, Any]:
        """
        执行分析脚本
        analyzeHeadless <project_location> <project_name> -process -postScript <script> [args]
        """
        if not self.current_program:
            return {"success": False, "error": "没有导入的程序，请先调用 import_file"}

        cmd = [
            "cmd", "/c", ANALYZE_HEADLESS,
            self.project_path,
            self.project_name,
            "-process", self.current_program,
        ]

        if script_path:
            cmd.extend(["-postScript", script_path])
            if script_args:
                cmd.extend(script_args)

        result = self._run_cmd(cmd, timeout=300)

        if result["success"]:
            self.logger.info(f"分析完成: {self.current_program}")

        return result

    def auto_analyze(self, file_path: str) -> dict[str, Any]:
        """快速分析：导入 + 自动分析"""
        self.logger.info(f"开始自动分析: {file_path}")

        # 导入
        import_result = self.import_file(file_path)
        if not import_result["success"]:
            return import_result

        # 分析
        return self.analyze()

    def export_report(self, output_path: str = None, format: str = "json") -> str:
        """
        导出分析报告
        使用 Ghidra 的内置脚本导出函数列表、字符串等信息
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(REPORT_DIR, f"report_{timestamp}.{format}")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 创建临时脚本：导出函数列表和字符串
        script_content = """
# Ghidra Headless Script - Export Report
# @category Analysis

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
    "exports": [],
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
for s in StringDataInstance.getStringInstances(currentProgram.getListing(), None, None):
    result["strings"].append({
        "address": str(s.getAddress()),
        "value": str(s),
        "length": len(str(s)),
    })
    if len(result["strings"]) >= 200:
        break

# 符号/导入
sym_table = currentProgram.getSymbolTable()
for sym in sym_table.getExternalSymbols():
    result["imports"].append({
        "name": sym.getName(),
        "address": str(sym.getAddress()) if sym.getAddress() else "N/A",
    })
    if len(result["imports"]) >= 100:
        break

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

# 写出
output_file = askFile("Save Report", "Save")
output_path = str(output_file.getAbsolutePath())

with open(output_file.getAbsolutePath(), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print("Report exported to: " + str(output_file.getAbsolutePath()))
"""

        # 写出临时脚本
        script_dir = os.path.join(self.project_path, "scripts")
        os.makedirs(script_dir, exist_ok=True)
        script_file = os.path.join(script_dir, "export_report.py")

        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_content)

        # 执行脚本
        cmd = [
            "cmd", "/c", ANALYZE_HEADLESS,
            self.project_path,
            self.project_name,
            "-process", self.current_program,
            "-postScript", "export_report.py",
        ]

        result = self._run_cmd(cmd, timeout=300)
        result["report_path"] = output_path

        return result

    def run_custom_script(self, script_path: str, args: list[str] = None) -> dict[str, Any]:
        """运行自定义 Ghidra 脚本"""
        if not os.path.exists(script_path):
            return {"success": False, "error": f"脚本不存在: {script_path}"}

        cmd = [
            "cmd", "/c", ANALYZE_HEADLESS,
            self.project_path,
            self.project_name,
            "-process", self.current_program,
            "-postScript", script_path,
        ]

        if args:
            cmd.extend(args)

        return self._run_cmd(cmd, timeout=300)

    def batch_analyze(self, directory: str, recursive: bool = True) -> list[dict]:
        """批量分析目录下所有二进制文件"""
        results = []
        dir_path = Path(directory)

        # 常见二进制扩展名
        binary_exts = {".exe", ".dll", ".sys", ".bin", ".elf", ".so", ".o", ".lib", ".obj"}

        pattern = "**/*" if recursive else "*"
        for file_path in dir_path.glob(pattern):
            if file_path.suffix.lower() in binary_exts:
                self.logger.info(f"分析: {file_path}")
                result = self.auto_analyze(str(file_path))
                result["file"] = str(file_path)
                results.append(result)

        return results


class AnalysisVerifier:
    """分析结果验证器"""

    @staticmethod
    def verify_report(report_path: str) -> dict[str, Any]:
        """验证分析报告的完整性"""
        if not os.path.exists(report_path):
            return {"valid": False, "error": "报告文件不存在"}

        with open(report_path, encoding="utf-8") as f:
            report = json.load(f)

        checks = {
            "has_functions": len(report.get("functions", [])) > 0,
            "has_sections": len(report.get("sections", [])) > 0,
            "has_entry": len(report.get("entry_points", [])) > 0,
            "has_language": bool(report.get("language")),
        }

        return {
            "valid": all(checks.values()),
            "checks": checks,
            "summary": {
                "functions": len(report.get("functions", [])),
                "strings": len(report.get("strings", [])),
                "sections": len(report.get("sections", [])),
                "imports": len(report.get("imports", [])),
            }
        }


# === 工作流集成 ===

def run_ghidra_analysis(file_path: str, output_dir: str = None) -> dict[str, Any]:
    """
    一键分析入口：导入 → 分析 → 导出报告
    供 Pipeline 调用
    """
    engine = GhidraHeadless()

    result = {
        "file": file_path,
        "timestamp": datetime.now().isoformat(),
        "steps": {}
    }

    # Step 1: 导入和分析
    analysis = engine.auto_analyze(file_path)
    result["steps"]["analysis"] = analysis

    if not analysis["success"]:
        result["success"] = False
        result["error"] = analysis.get("error", "分析失败")
        return result

    # Step 2: 导出报告
    if output_dir:
        report_path = os.path.join(output_dir, f"{Path(file_path).stem}_report.json")
        export_result = engine.export_report(report_path)
        result["steps"]["export"] = export_result
        result["report_path"] = report_path

        # Step 3: 验证报告
        verifier = AnalysisVerifier()
        verification = verifier.verify_report(report_path)
        result["verification"] = verification

    result["success"] = True
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ghidra Headless 分析工具")
    parser.add_argument("file", help="要分析的二进制文件路径")
    parser.add_argument("-o", "--output", help="报告输出目录", default=REPORT_DIR)
    parser.add_argument("-p", "--project", help="项目名称", default="analysis")

    args = parser.parse_args()

    result = run_ghidra_analysis(args.file, args.output)
    print(json.dumps(result, indent=2, ensure_ascii=False))
