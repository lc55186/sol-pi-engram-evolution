#!/usr/bin/env python3
"""
CSV 销售数据 → 报告生成器
集成到 SoL-Pi 融合系统工作流
功能：合并清洗 → 计算统计 → 画图 → 写结论 → 输出 Markdown 报告
"""
import csv
import os
from datetime import datetime
from pathlib import Path
from typing import Any


# 动态加载兄弟模块
def _load_module(name, rel_path):
    import importlib.util
    base_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, rel_path)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class CSVReportGenerator:
    """CSV 销售数据报告生成器"""

    def __init__(self, input_dir: str, output_dir: str = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir or os.path.join(input_dir, "..", "reports"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.raw_data: list[dict] = []
        self.clean_data: list[dict] = []
        self.stats: dict[str, Any] = {}

    def load_csv_files(self) -> list[dict]:
        """加载目录下所有 CSV 文件"""
        csv_files = sorted(self.input_dir.glob("*.csv"))
        print(f"找到 {len(csv_files)} 个 CSV 文件: {[f.name for f in csv_files]}")

        all_rows = []
        for csv_file in csv_files:
            with open(csv_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    row["_source"] = csv_file.name
                    all_rows.append(row)

        self.raw_data = all_rows
        print(f"原始记录: {len(all_rows)} 条")
        return all_rows

    def clean_data_rows(self, amount_field: str = "amount", date_field: str = "date", region_field: str = "region") -> list[dict]:
        """清洗数据：去重、去负金额、去空字段"""
        if not self.raw_data:
            self.load_csv_files()

        original_count = len(self.raw_data)
        cleaned = []
        seen = set()

        removed_duplicate = 0
        removed_negative = 0
        removed_empty = 0

        for row in self.raw_data:
            # 去重：基于完整行内容
            row_key = tuple(sorted(row.items()))
            if row_key in seen:
                removed_duplicate += 1
                continue
            seen.add(row_key)

            # 获取金额
            amount_str = row.get(amount_field, "").strip()
            if not amount_str:
                removed_empty += 1
                continue

            try:
                amount = float(amount_str)
            except ValueError:
                removed_empty += 1
                continue

            # 去负金额
            if amount < 0:
                removed_negative += 1
                continue

            # 检查必填字段
            date_val = row.get(date_field, "").strip()
            region_val = row.get(region_field, "").strip()
            if not date_val or not region_val:
                removed_empty += 1
                continue

            # 标准化日期格式
            try:
                # 支持 YYYY-MM-DD 和 YYYY/MM/DD
                date_normalized = date_val.replace("/", "-")
                datetime.strptime(date_normalized, "%Y-%m-%d")
            except ValueError:
                removed_empty += 1
                continue

            cleaned.append({
                date_field: date_normalized,
                region_field: region_val,
                amount_field: amount,
                **{k: v for k, v in row.items() if k not in (date_field, region_field, amount_field) and not k.startswith("_")}
            })

        self.clean_data = cleaned

        print("清洗完成:")
        print(f"  去重: {removed_duplicate} 行")
        print(f"  负金额: {removed_negative} 行")
        print(f"  缺字段: {removed_empty} 行")
        print(f"  有效: {len(cleaned)} 行 (原始 {original_count})")

        return cleaned

    def calculate_stats(self, amount_field: str = "amount", date_field: str = "date", region_field: str = "region") -> dict[str, Any]:
        """计算每个大区的月度销售额和环比"""
        if not self.clean_data:
            self.clean_data_rows(amount_field, date_field, region_field)

        # 按月份+大区分组
        monthly: dict[str, dict[str, float]] = {}
        for row in self.clean_data:
            date_str = row[date_field]
            region = row[region_field]
            amount = row[amount_field]

            # 取年月
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                month_key = dt.strftime("%Y-%m")
            except:
                continue

            if month_key not in monthly:
                monthly[month_key] = {}

            if region not in monthly[month_key]:
                monthly[month_key][region] = 0.0

            monthly[month_key][region] += amount

        # 计算环比
        sorted_months = sorted(monthly.keys())
        growth = {}
        for i, month in enumerate(sorted_months):
            growth[month] = {}
            for region, amount in monthly[month].items():
                if i > 0:
                    prev_month = sorted_months[i - 1]
                    prev_amount = monthly.get(prev_month, {}).get(region, 0)
                    if prev_amount > 0:
                        growth[month][region] = (amount - prev_amount) / prev_amount * 100
                    else:
                        growth[month][region] = 0.0
                else:
                    growth[month][region] = 0.0

        # 生成统计结果
        stats = {
            "monthly_totals": monthly,
            "growth_rates": growth,
            "regions": list(set(r for m in monthly.values() for r in m.keys())),
            "months": sorted_months,
            "total_amount": sum(r[amount_field] for r in self.clean_data),
            "record_count": len(self.clean_data),
        }

        self.stats = stats
        return stats

    def generate_chart(self, format: str = "ascii") -> str:
        """生成趋势图"""
        if not self.stats:
            self.calculate_stats()

        monthly = self.stats["monthly_totals"]
        regions = self.stats["regions"]
        months = self.stats["months"]

        if format == "ascii":
            return self._generate_ascii_chart(monthly, regions, months)
        elif format == "html":
            return self._generate_html_chart(monthly, regions, months)
        else:
            return ""

    def _generate_ascii_chart(self, monthly: dict, regions: list[str], months: list[str]) -> str:
        """生成 ASCII 趋势图"""
        if not months:
            return "无数据"

        # 按月份生成每个大区的销售额柱状图
        lines = []
        lines.append("月度销售额趋势 (万元)")
        lines.append("=" * 50)

        # 收集所有值用于缩放
        all_values = []
        for month in months:
            for region in regions:
                val = monthly.get(month, {}).get(region, 0) / 10000
                all_values.append(val)

        max_val = max(all_values) if all_values else 1
        bar_width = 40

        for month in months:
            lines.append(f"\n[{month}]")
            for region in sorted(regions):
                val = monthly.get(month, {}).get(region, 0) / 10000
                bar_len = int((val / max_val) * bar_width) if max_val > 0 else 0
                bar = "█" * bar_len + "░" * (bar_width - bar_len)
                lines.append(f"  {region:8s} │{bar}│ {val:8.1f}")

        return "\n".join(lines)

    def _generate_html_chart(self, monthly: dict, regions: list[str], months: list[str]) -> str:
        """生成 HTML/SVG 图表"""
        # 简化的 HTML 表格图表
        html_parts = ["<table border='1' cellpadding='5'>"]
        html_parts.append("<tr><th>月份</th>" + "".join(f"<th>{r}</th>" for r in sorted(regions)) + "</tr>")

        for month in months:
            html_parts.append(f"<tr><td>{month}</td>")
            for region in sorted(regions):
                val = monthly.get(month, {}).get(region, 0)
                html_parts.append(f"<td>{val:,.0f}</td>")
            html_parts.append("</tr>")

        html_parts.append("</table>")
        return "\n".join(html_parts)

    def generate_conclusion(self) -> str:
        """生成三句话结论"""
        if not self.stats:
            self.calculate_stats()

        monthly = self.stats["monthly_totals"]
        growth = self.stats["growth_rates"]
        months = sorted(monthly.keys())

        if not months:
            return "数据不足，无法生成结论。"

        last_month = months[-1]
        prev_month = months[-2] if len(months) > 1 else None

        regions_data = monthly.get(last_month, {})

        if not regions_data:
            return "本月无数据。"

        # 找出表现最好的大区
        best_region = max(regions_data, key=regions_data.get)
        best_amount = regions_data[best_region]

        # 找出下滑大区
        declining = []
        if prev_month:
            for region, amount in regions_data.items():
                prev = monthly.get(prev_month, {}).get(region, 0)
                if prev > 0 and amount < prev:
                    declining.append((region, (amount - prev) / prev * 100))

        # 结论
        conclusions = []

        # 结论 1: 总览
        total = sum(regions_data.values())
        conclusions.append(f"**{last_month}** 总销售额 **{total:,.0f}** 元，覆盖 {len(regions_data)} 个大区。")

        # 结论 2: 亮点
        best_growth = growth.get(last_month, {}).get(best_region, 0)
        conclusions.append(f"{best_region}表现突出，销售额 **{best_amount:,.0f}** 元，环比 {'+' if best_growth >= 0 else ''}{best_growth:.1f}%。")

        # 结论 3: 风险
        if declining:
            worst = min(declining, key=lambda x: x[1])
            conclusions.append(f"⚠ {worst[0]} 环比下滑 {abs(worst[1]):.1f}%，建议关注。")
        else:
            conclusions.append("各大区整体运行平稳，无明显下滑。")

        return "\n".join(f"- {c}" for c in conclusions)

    def generate_report(self, title: str = "销售数据报告") -> str:
        """生成完整 Markdown 报告"""
        if not self.stats:
            self.calculate_stats()

        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        report_lines = [
            f"# {title}",
            "",
            f"> 生成时间: {now}",
            f"> 数据来源: `{self.input_dir.name}/`",
            "",
            "## 结论",
            self.generate_conclusion(),
            "",
            "## 月度销售额",
            self.generate_chart(format="ascii"),
            "",
            "## 环比增长",
            "",
        ]

        # 环比表格
        growth = self.stats["growth_rates"]
        months = sorted(growth.keys())
        regions = sorted(self.stats["regions"])

        header = "│".join(f" {r:8s} " for r in ["月份"] + regions)
        report_lines.append(f"| {header} |")
        report_lines.append("|" + "|".join("--------" for _ in range(len(regions) + 1)) + "|")

        for month in months:
            row = f"| {month} |"
            for region in regions:
                g = growth.get(month, {}).get(region, 0)
                row += f" {g:+6.1f}% |"
            report_lines.append(row)

        report_lines.extend([
            "",
            "## 数据明细",
            f"- 总记录: **{self.stats['record_count']}** 条",
            f"- 有效金额: **{self.stats['total_amount']:,.0f}** 元",
            f"- 大区: {', '.join(self.stats['regions'])}",
            f"- 月份: {', '.join(self.stats['months'])}",
            "",
            "---",
            "*本报告由 SoL-Pi 融合系统自动生成*",
        ])

        return "\n".join(report_lines)

    def save_report(self, filename: str = None) -> str:
        """保存报告到文件"""
        report_md = self.generate_report()

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"report_{timestamp}.md"

        output_path = self.output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        print(f"\n报告已保存: {output_path}")
        return str(output_path)


def generate_demo_data(output_dir: str):
    """生成示例 CSV 数据（用于测试）"""
    os.makedirs(output_dir, exist_ok=True)

    import random
    random.seed(42)

    regions = ["华东区", "华南区", "华北区", "西南区", "西北区", "东北区"]
    months = ["2026-07", "2026-08"]

    for month in months:
        filename = os.path.join(output_dir, f"{month}_sales.csv")
        rows = []

        # 生成正常数据
        for region in regions:
            for _ in range(random.randint(5, 15)):
                day = random.randint(1, 28)
                amount = round(random.uniform(1000, 50000), 2)
                rows.append({
                    "date": f"{month}-{day:02d}",
                    "region": region,
                    "amount": amount,
                    "product": random.choice(["A", "B", "C"]),
                })

        # 添加脏数据
        # 重复行
        for _ in range(21):
            rows.append(random.choice(rows[:len(rows)//2]).copy())

        # 负金额
        for _ in range(9):
            row = random.choice(rows).copy()
            row["amount"] = -row["amount"]
            rows.append(row)

        # 缺字段
        for _ in range(7):
            rows.append({"date": f"{month}-01", "region": random.choice(regions), "amount": ""})

        random.shuffle(rows)

        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["date", "region", "amount", "product"])
            writer.writeheader()
            writer.writerows(rows)

        print(f"生成: {filename} ({len(rows)} 行)")


# === CLI 入口 ===

def main():
    import argparse

    parser = argparse.ArgumentParser(description="CSV 销售数据报告生成器")
    sub = parser.add_subparsers(dest="command")

    # generate-demo 命令
    p_demo = sub.add_parser("generate-demo", help="生成示例 CSV 数据")
    p_demo.add_argument("-d", "--dir", default=os.path.expanduser("~/Downloads/sales_demo"))

    # report 命令
    p_report = sub.add_parser("report", help="生成报告")
    p_report.add_argument("input_dir", help="CSV 文件目录")
    p_report.add_argument("-o", "--output", help="报告输出目录")
    p_report.add_argument("--title", default="销售数据报告")
    p_report.add_argument("--demo", action="store_true", help="自动生成示例数据")

    args = parser.parse_args()

    if args.command == "generate-demo":
        generate_demo_data(args.dir)

    elif args.command == "report":
        if args.demo:
            # 生成示例数据
            demo_dir = os.path.join(args.input_dir, "sales_demo")
            generate_demo_data(demo_dir)
            args.input_dir = demo_dir

        generator = CSVReportGenerator(args.input_dir, args.output)
        generator.load_csv_files()
        generator.clean_data_rows()
        generator.calculate_stats()
        report_md = generator.generate_report(args.title)
        output_path = generator.save_report()

        # 同时输出到控制台
        print("\n" + "=" * 60)
        print(report_md)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
