#!/usr/bin/env python3
"""
IMA 知识库自动备份脚本
集成到 SoL-Pi 融合系统工作流
每天 24:00 由 deployer Bot 自动执行
"""
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# === 配置 ===
CLIENT_ID_PATH = os.path.expanduser("~/.config/ima/client_id")
API_KEY_PATH = os.path.expanduser("~/.config/ima/api_key")
KB_ID = "ADJqUt4se4UZtsZBnXOjxkRn9tODGVg2jR7YeXUyJr4="
SKILL_DIR = os.path.expanduser("~/AppData/Local/hermes/skills")
PROJECT_DIR = os.path.expanduser("~/Desktop/sol-pi-engram-evolution")
LOG_DIR = os.path.expanduser("~/.hermes/logs")
IMA_API_DIR = os.path.expanduser("~/AppData/Local/hermes/skills/ima-skill")

# IMA media_type 映射
EXT_MAP = {
    ".py": (13, "txt"),    # .py 需改 .txt
    ".md": (7, "md"),      # Markdown
    ".txt": (13, "txt"),   # TXT
    ".json": (7, "json"),  # JSON 按 Markdown 处理
    ".yaml": (7, "yaml"),  # YAML
    ".yml": (7, "yml"),    # YML
    ".csv": (13, "csv"),   # CSV
    ".html": (7, "html"),  # HTML
}

# 目标知识库分类
CATEGORY_MAP = {
    "skill": "skills/",
    "doc": "docs/",
    "research": "research/",
    "tool": "tools/",
}


def load_credentials():
    """加载 IMA 凭证"""
    try:
        with open(CLIENT_ID_PATH) as f:
            client_id = f.read().strip()
        with open(API_KEY_PATH) as f:
            api_key = f.read().strip()
        return client_id, api_key
    except FileNotFoundError as e:
        print(f"[ERROR] 凭证文件不存在: {e}")
        sys.exit(1)


def get_file_category(file_path):
    """根据路径判断文件分类"""
    path_lower = file_path.lower()
    if "skill" in path_lower or "skills" in path_lower:
        return "skills/"
    elif "doc" in path_lower or "docs" in path_lower or "document" in path_lower:
        return "docs/"
    elif "research" in path_lower or "study" in path_lower or "研究" in file_path:
        return "research/"
    elif "tool" in path_lower or "tools" in path_lower or "format" in path_lower:
        return "tools/"
    else:
        return "docs/"  # 默认


def scan_files():
    """扫描需要备份的文件"""
    files_to_backup = []

    # 扫描技能目录（SKILL.md 和重要文件）
    skill_dir = Path(SKILL_DIR)
    if skill_dir.exists():
        for skill_md in skill_dir.glob("*/SKILL.md"):
            files_to_backup.append({
                "path": str(skill_md),
                "category": "skills/",
                "name": f"{skill_md.parent.name}_SKILL.md",
            })

    # 扫描项目目录（.py, .md, .txt）
    project_dir = Path(PROJECT_DIR)
    if project_dir.exists():
        for ext in ["*.py", "*.md", "*.txt"]:
            for f in project_dir.rglob(ext):
                if "__pycache__" in str(f) or ".venv" in str(f):
                    continue
                # .py 文件需要改 .txt
                if f.suffix == ".py":
                    files_to_backup.append({
                        "path": str(f),
                        "category": get_file_category(str(f)),
                        "name": f.stem + ".txt",
                        "original_ext": ".py",
                    })
                else:
                    files_to_backup.append({
                        "path": str(f),
                        "category": get_file_category(str(f)),
                        "name": f.name,
                    })

    return files_to_backup


def call_ima_api(endpoint, payload, credentials):
    """调用 IMA API"""
    client_id, api_key = credentials
    auth = json.dumps({"clientId": client_id, "apiKey": api_key})

    cmd = [
        "node", "ima_api.cjs", endpoint, json.dumps(payload), auth
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=IMA_API_DIR, timeout=30
    )

    if result.returncode != 0:
        raise RuntimeError(f"IMA API 调用失败: {result.stderr}")

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"raw": result.stdout, "error": result.stderr}


def cos_upload(file_path, cos_info):
    """上传到 COS"""
    cmd = [
        "node", "knowledge-base/scripts/cos-upload.cjs",
        "--file", file_path,
        "--secret-id", cos_info["secret_id"],
        "--secret-key", cos_info["secret_key"],
        "--token", cos_info["token"],
        "--bucket", cos_info["bucket"],
        "--region", cos_info["region"],
        "--cos-key", cos_info["cos_key"],
        "--content-type", cos_info.get("content_type", "text/plain"),
    ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=IMA_API_DIR, timeout=60
    )

    if result.returncode != 0:
        raise RuntimeError(f"COS 上传失败: {result.stderr}")

    return True


def upload_file(file_info, credentials):
    """上传单个文件到 IMA"""
    original_path = file_info["path"]
    file_name = file_info["name"]
    category = file_info["category"]

    # 获取文件扩展名
    ext = Path(file_name).suffix.lower()
    if file_info.get("original_ext"):
        ext = file_info["original_ext"].lower()

    media_type, file_ext = EXT_MAP.get(ext, (13, "txt"))

    # 如果是 .py，创建临时 .txt 文件用于上传
    upload_path = original_path
    temp_file = None
    if file_info.get("original_ext") == ".py":
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        )
        with open(original_path, encoding='utf-8') as src:
            temp_file.write(src.read())
        temp_file.close()
        upload_path = temp_file.name

    try:
        file_size = os.path.getsize(upload_path)

        # Step 1: 创建媒体
        create_payload = {
            "file_name": file_name,
            "file_size": file_size,
            "content_type": "text/plain" if media_type == 13 else "text/markdown",
            "knowledge_base_id": KB_ID,
            "file_ext": file_ext,
        }

        create_resp = call_ima_api(
            "openapi/wiki/v1/create_media", create_payload, credentials
        )

        if create_resp.get("code") != 0:
            print(f"  [ERROR] create_media 失败: {create_resp}")
            return False

        media_id = create_resp["data"]["media_id"]
        cos_info = create_resp["data"]["cos_credentials"]
        cos_key = create_resp["data"]["file_info"]["cos_key"]

        # Step 2: COS 上传
        cos_upload_info = {
            "secret_id": cos_info["secret_id"],
            "secret_key": cos_info["secret_key"],
            "token": cos_info["token"],
            "bucket": cos_info["bucket"],
            "region": cos_info["region"],
            "cos_key": cos_key,
            "content_type": "text/plain" if media_type == 13 else "text/markdown",
        }

        cos_upload(upload_path, cos_upload_info)

        # Step 3: 完成写入
        add_payload = {
            "media_type": media_type,
            "media_id": media_id,
            "title": file_name,
            "knowledge_base_id": KB_ID,
            "file_info": {
                "cos_key": cos_key,
                "file_size": file_size,
                "file_name": file_name,
            },
        }

        add_resp = call_ima_api(
            "openapi/wiki/v1/add_knowledge", add_payload, credentials
        )

        if add_resp.get("code") != 0:
            print(f"  [ERROR] add_knowledge 失败: {add_resp}")
            return False

        return True

    finally:
        if temp_file and os.path.exists(temp_file.name):
            os.unlink(temp_file.name)


def run_backup():
    """执行完整备份流程"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"backup_{timestamp}.log")
    os.makedirs(LOG_DIR, exist_ok=True)

    def log(msg):
        line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    log("=" * 60)
    log("IMA 知识库自动备份开始")
    log("=" * 60)

    # 加载凭证
    credentials = load_credentials()
    log("凭证加载成功")

    # 扫描文件
    files = scan_files()
    log(f"扫描到 {len(files)} 个文件")

    if not files:
        log("没有需要备份的文件，结束")
        return

    # 分类统计
    categories = {}
    for f in files:
        cat = f["category"]
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in categories.items():
        log(f"  {cat}: {count} 个文件")

    # 逐个上传
    success_count = 0
    fail_count = 0

    for i, file_info in enumerate(files, 1):
        log(f"\n[{i}/{len(files)}] 上传: {file_info['name']} ({file_info['category']})")
        try:
            if upload_file(file_info, credentials):
                log("  ✅ 成功")
                success_count += 1
            else:
                log("  ❌ 失败")
                fail_count += 1
        except Exception as e:
            log(f"  ❌ 异常: {e}")
            fail_count += 1

    log("\n" + "=" * 60)
    log(f"备份完成: 成功 {success_count}, 失败 {fail_count}")
    log("=" * 60)

    return success_count, fail_count


if __name__ == "__main__":
    run_backup()
