#!/usr/bin/env python
"""
格式扩展工具集 - 核心转换器
支持 CSV/JSON/XML/Excel/Word/PDF 的读写、结构化提取、格式转换
"""

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


class FormatConverter:
    """格式转换器：支持 CSV/JSON/XML 读写和相互转换"""

    def __init__(self, default_encoding: str = 'utf-8'):
        self.default_encoding = default_encoding

    # ========== CSV 操作 ==========

    def csv_to_list(self, filepath: str,
                    encoding: str = None) -> list[dict[str, str]]:
        """CSV 文件 → 字典列表"""
        enc = encoding or self.default_encoding
        result = []
        with open(filepath, encoding=enc, errors='replace') as f:
            reader = csv.DictReader(f)
            for row in reader:
                result.append(dict(row))
        return result

    def list_to_csv(self, data: list[dict[str, Any]],
                    filepath: str,
                    encoding: str = None,
                    fieldnames: list[str] = None) -> bool:
        """字典列表 → CSV 文件"""
        if not data:
            return False

        enc = encoding or self.default_encoding
        if fieldnames is None:
            fieldnames = list(data[0].keys())

        with open(filepath, 'w', encoding=enc, newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames,
                                     extrasaction='ignore')
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        return True

    def csv_to_json(self, csv_path: str, json_path: str,
                    encoding: str = None) -> bool:
        """CSV → JSON 转换"""
        data = self.csv_to_list(csv_path, encoding)
        return self.list_to_json(data, json_path, encoding)

    # ========== JSON 操作 ==========

    def json_to_list(self, filepath: str,
                     encoding: str = None) -> list[dict]:
        """JSON 文件 → 字典列表"""
        enc = encoding or self.default_encoding
        with open(filepath, encoding=enc, errors='replace') as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        return []

    def list_to_json(self, data: list[dict[str, Any]],
                     filepath: str,
                     encoding: str = None,
                     indent: int = 2,
                     ensure_ascii: bool = False) -> bool:
        """字典列表 → JSON 文件"""
        enc = encoding or self.default_encoding
        with open(filepath, 'w', encoding=enc) as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii,
                      default=str)
        return True

    def json_to_csv(self, json_path: str, csv_path: str,
                    encoding: str = None) -> bool:
        """JSON → CSV 转换"""
        data = self.json_to_list(json_path, encoding)
        return self.list_to_csv(data, csv_path, encoding)

    def extract_json_field(self, data: list[dict],
                           field_path: str) -> list[Any]:
        """从 JSON 数据中提取指定字段（支持嵌套路径，如 "user.name"）"""
        results = []
        keys = field_path.split('.')
        for item in data:
            value = item
            for key in keys:
                if isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break
            results.append(value)
        return results

    def filter_json(self, data: list[dict],
                    condition: dict[str, Any]) -> list[dict]:
        """按条件过滤 JSON 数据"""
        results = []
        for item in data:
            match = True
            for key, expected in condition.items():
                if item.get(key) != expected:
                    match = False
                    break
            if match:
                results.append(item)
        return results

    # ========== XML 操作 ==========

    def xml_to_dict(self, filepath: str,
                    encoding: str = None) -> dict:
        """XML 文件 → 字典"""
        enc = encoding or self.default_encoding
        tree = ET.parse(filepath, parser=ET.XMLParser(encoding=enc))
        root = tree.getroot()
        return self._xml_element_to_dict(root)

    def _xml_element_to_dict(self, element: ET.Element) -> dict:
        """递归转换 XML 元素为字典"""
        result = {}

        # 属性
        if element.attrib:
            result['@attributes'] = dict(element.attrib)

        # 子元素
        children = list(element)
        if children:
            children_dict = {}
            for child in children:
                child_data = self._xml_element_to_dict(child)
                tag = child.tag.split('}')[-1]  # 去掉命名空间
                if tag in children_dict:
                    if not isinstance(children_dict[tag], list):
                        children_dict[tag] = [children_dict[tag]]
                    children_dict[tag].append(child_data)
                else:
                    children_dict[tag] = child_data
            result.update(children_dict)

        # 文本内容
        text = (element.text or '').strip()
        if text:
            if result:
                result['#text'] = text
            else:
                return text

        return result

    def dict_to_xml(self, data: dict, root_tag: str = "root",
                    filepath: str = None,
                    encoding: str = None) -> str | None:
        """字典 → XML 字符串/文件"""
        root = ET.Element(root_tag)
        self._dict_to_xml_element(root, data)

        xml_str = ET.tostring(root, encoding='unicode', xml_declaration=True)

        if filepath:
            enc = encoding or self.default_encoding
            with open(filepath, 'w', encoding=enc) as f:
                f.write(xml_str)
            return None
        return xml_str

    def _dict_to_xml_element(self, parent: ET.Element, data: Any):
        """递归构建 XML 元素"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.startswith('@'):
                    parent.set(key[1:], str(value))
                elif key == '#text':
                    parent.text = str(value)
                else:
                    if isinstance(value, list):
                        for item in value:
                            child = ET.SubElement(parent, key)
                            self._dict_to_xml_element(child, item)
                    else:
                        child = ET.SubElement(parent, key)
                        self._dict_to_xml_element(child, value)
        else:
            parent.text = str(data)

    # ========== 通用转换 ==========

    def convert(self, input_path: str, output_path: str,
                input_format: str = None,
                output_format: str = None) -> bool:
        """通用格式转换（根据文件扩展名自动判断）"""
        in_fmt = input_format or Path(input_path).suffix.lstrip('.').lower()
        out_fmt = output_format or Path(output_path).suffix.lstrip('.').lower()

        # 读取输入
        if in_fmt == 'csv':
            data = self.csv_to_list(input_path)
        elif in_fmt == 'json':
            data = self.json_to_list(input_path)
        elif in_fmt == 'xml':
            data = self.xml_to_dict(input_path)
            if not isinstance(data, list):
                data = [data]
        else:
            raise ValueError(f"不支持的输入格式: {in_fmt}")

        # 写入输出
        if out_fmt == 'csv':
            return self.list_to_csv(data, output_path)
        elif out_fmt == 'json':
            return self.list_to_json(data, output_path)
        elif out_fmt == 'xml':
            return self.dict_to_xml({'item': data}, root_tag="items",
                                    filepath=output_path) or True
        else:
            raise ValueError(f"不支持的输出格式: {out_fmt}")

    # ========== 结构化提取 ==========

    def extract_structured_data(self, filepath: str,
                                fields: list[str]) -> list[dict]:
        """从文件中提取指定字段"""
        ext = Path(filepath).suffix.lstrip('.').lower()

        if ext == 'csv':
            data = self.csv_to_list(filepath)
        elif ext == 'json':
            data = self.json_to_list(filepath)
        elif ext == 'xml':
            data = self.xml_to_dict(filepath)
            if not isinstance(data, list):
                data = [data]
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

        results = []
        for item in data:
            extracted = {}
            for field in fields:
                keys = field.split('.')
                value = item
                for key in keys:
                    if isinstance(value, dict):
                        value = value.get(key)
                    else:
                        value = None
                        break
                extracted[field] = value
            results.append(extracted)

        return results


# 便捷函数
def convert_format(input_path: str, output_path: str,
                   input_format: str = None,
                   output_format: str = None) -> bool:
    """通用格式转换便捷函数"""
    converter = FormatConverter()
    return converter.convert(input_path, output_path,
                             input_format, output_format)


def read_data(filepath: str, encoding: str = None) -> list[dict]:
    """读取任意支持格式的文件"""
    converter = FormatConverter(encoding or 'utf-8')
    ext = Path(filepath).suffix.lstrip('.').lower()
    if ext == 'csv':
        return converter.csv_to_list(filepath)
    elif ext == 'json':
        return converter.json_to_list(filepath)
    elif ext == 'xml':
        data = converter.xml_to_dict(filepath)
        return data if isinstance(data, list) else [data]
    raise ValueError(f"不支持的文件格式: {ext}")


def write_data(data: list[dict], filepath: str,
               encoding: str = None) -> bool:
    """写入任意支持格式的文件"""
    converter = FormatConverter(encoding or 'utf-8')
    ext = Path(filepath).suffix.lstrip('.').lower()
    if ext == 'csv':
        return converter.list_to_csv(data, filepath)
    elif ext == 'json':
        return converter.list_to_json(data, filepath)
    elif ext == 'xml':
        return converter.dict_to_xml({'item': data}, root_tag="items",
                                     filepath=filepath) or True
    raise ValueError(f"不支持的文件格式: {ext}")
