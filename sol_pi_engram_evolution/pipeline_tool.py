#!/usr/bin/env python
"""
格式扩展工具集 - 管道/自动化模块
函数库封装、日志、错误重试、进度输出、HTML 报告生成
"""

import logging
import time
from collections.abc import Callable
from datetime import datetime


class PipelineTool:
    """管道工具：封装处理流程、日志、错误重试、进度输出"""

    def __init__(self, name: str = "pipeline",
                 log_file: str = None,
                 log_level: int = logging.INFO):
        self.name = name
        self.steps = []
        self.results = []
        self.stats = {
            'started_at': None,
            'completed_at': None,
            'total_steps': 0,
            'successful': 0,
            'failed': 0,
            'retried': 0,
        }

        # 配置日志
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)
        self.logger.handlers = []

        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件输出
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def add_step(self, name: str, func: Callable,
                 *args, **kwargs) -> 'PipelineTool':
        """添加处理步骤"""
        self.steps.append({
            'name': name,
            'func': func,
            'args': args,
            'kwargs': kwargs,
        })
        return self

    def run(self, stop_on_error: bool = False,
            max_retries: int = 0) -> list[dict]:
        """执行所有步骤"""
        self.stats['started_at'] = datetime.now().isoformat()
        self.stats['total_steps'] = len(self.steps)
        self.results = []

        self.logger.info(f"管道 '{self.name}' 开始执行，共 {len(self.steps)} 步")

        for i, step in enumerate(self.steps, 1):
            result = self._execute_step(step, i, max_retries)
            self.results.append(result)

            if result['status'] == 'success':
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1
                if stop_on_error:
                    self.logger.error(f"步骤 {i} 失败，停止执行")
                    break

        self.stats['completed_at'] = datetime.now().isoformat()
        self._log_summary()

        return self.results

    def _execute_step(self, step: dict, index: int,
                      max_retries: int) -> dict:
        """执行单个步骤（带重试）"""
        name = step['name']
        func = step['func']
        args = step['args']
        kwargs = step['kwargs']

        result = {
            'step': index,
            'name': name,
            'status': 'pending',
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'error': None,
            'retries': 0,
        }

        self.logger.info(f"步骤 {index}/{len(self.steps)}: {name}")

        for attempt in range(max_retries + 1):
            try:
                start_time = time.time()
                output = func(*args, **kwargs)
                elapsed = time.time() - start_time

                result['status'] = 'success'
                result['output'] = output
                result['elapsed_seconds'] = round(elapsed, 3)
                result['completed_at'] = datetime.now().isoformat()

                self.logger.info(
                    f"  ✓ {name} 完成 ({result['elapsed_seconds']}s)"
                )
                return result

            except Exception as e:
                result['retries'] = attempt
                result['error'] = str(e)

                if attempt < max_retries:
                    self.stats['retried'] += 1
                    self.logger.warning(
                        f"  ⚠ {name} 失败 (尝试 {attempt + 1}/{max_retries + 1}): {e}"
                    )
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    result['status'] = 'failed'
                    result['completed_at'] = datetime.now().isoformat()
                    self.logger.error(f"  ✗ {name} 失败: {e}")

        return result

    def _log_summary(self):
        """输出摘要"""
        self.logger.info("=" * 50)
        self.logger.info(f"管道 '{self.name}' 执行完毕")
        self.logger.info(
            f"  成功: {self.stats['successful']}/{self.stats['total_steps']}"
        )
        self.logger.info(
            f"  失败: {self.stats['failed']}/{self.stats['total_steps']}"
        )
        if self.stats['retried'] > 0:
            self.logger.info(f"  重试: {self.stats['retried']} 次")
        self.logger.info("=" * 50)

    def generate_html_report(self, output_path: str = None) -> str:
        """生成 HTML 报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>管道执行报告 - {self.name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
        .stat-box {{ flex: 1; padding: 15px; border-radius: 6px; text-align: center; }}
        .stat-box.success {{ background: #e8f5e9; color: #2e7d32; }}
        .stat-box.failed {{ background: #ffebee; color: #c62828; }}
        .stat-box.info {{ background: #e3f2fd; color: #1565c0; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; }}
        .status-success {{ color: #4CAF50; font-weight: bold; }}
        .status-failed {{ color: #f44336; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>管道执行报告</h1>
        <p>管道名称: <strong>{self.name}</strong></p>
        <p>开始时间: {self.stats.get('started_at', 'N/A')}</p>
        <p>结束时间: {self.stats.get('completed_at', 'N/A')}</p>

        <div class="stats">
            <div class="stat-box info">
                <div style="font-size:24px;">{self.stats['total_steps']}</div>
                <div>总步骤</div>
            </div>
            <div class="stat-box success">
                <div style="font-size:24px;">{self.stats['successful']}</div>
                <div>成功</div>
            </div>
            <div class="stat-box failed">
                <div style="font-size:24px;">{self.stats['failed']}</div>
                <div>失败</div>
            </div>
        </div>

        <h2>执行详情</h2>
        <table>
            <tr>
                <th>步骤</th>
                <th>名称</th>
                <th>状态</th>
                <th>耗时</th>
                <th>重试</th>
                <th>错误</th>
            </tr>
"""

        for r in self.results:
            status_class = 'status-success' if r['status'] == 'success' else 'status-failed'
            elapsed = r.get('elapsed_seconds', '-')
            error = r.get('error', '-') or '-'
            html += f"""            <tr>
                <td>{r['step']}</td>
                <td>{r['name']}</td>
                <td class="{status_class}">{r['status']}</td>
                <td>{elapsed}s</td>
                <td>{r.get('retries', 0)}</td>
                <td>{error}</td>
            </tr>
"""

        html += """        </table>
    </div>
</body>
</html>"""

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

        return html

    def get_stats(self) -> dict:
        """获取统计"""
        return dict(self.stats)


# 便捷函数
def create_pipeline(name: str, log_file: str = None) -> PipelineTool:
    """创建管道"""
    return PipelineTool(name=name, log_file=log_file)


def retry(func: Callable, max_attempts: int = 3,
          delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器"""
    def wrapper(*args, **kwargs):
        last_error = None
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                if attempt < max_attempts - 1:
                    time.sleep(delay * (backoff ** attempt))
        raise last_error
    return wrapper
