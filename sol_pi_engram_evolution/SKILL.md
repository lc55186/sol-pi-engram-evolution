# SoL-Pi Engram CLI 能力清单

## 命令列表

### 1. convert — 格式转换
```
python solpi_cli.py convert <input> -f <format> [-o output] [--root name]
```
- 输入：CSV / JSON / XML
- 输出：JSON / CSV / XML
- 参数：
  - `-f, --format`: 目标格式 (json/csv/xml)
  - `-o, --output`: 输出文件路径
  - `--root`: XML 根元素名

### 2. batch — 批量转换
```
python solpi_cli.py batch <input_dir> <output_dir> -f <format>
```
- 批量转换目录下的所有文件
- 参数：
  - `-f, --format`: 目标格式 (json/csv/xml)

### 3. stats — 图谱统计
```
python solpi_cli.py stats [--db path]
```
- 返回：总节点数、任务节点数、事件节点数、关系数

### 4. search — 图谱搜索
```
python solpi_cli.py search <query> [--db path] [--top-k N]
```
- 返回：匹配的节点列表（node_id, node_type, title, score）

### 5. add-task — 添加任务节点
```
python solpi_cli.py add-task <title> [-d desc] [-p 1-5] [--db path]
```
- 参数：
  - `-d, --description`: 任务描述
  - `-p, --priority`: 优先级 (1-5, 默认 3)

### 6. archive — 归档文件
```
python solpi_cli.py archive <file> [--content-type text] [--archive-dir path]
```
- 返回：content_id, filepath, content_hash

### 7. retrieve — 召回归档
```
python solpi_cli.py retrieve --content-id <id> --filepath <path> [--chunk N] [--archive-dir path]
```
- 返回：content, chunk_index, total_chunks

### 8. evaluate — 评估节点价值
```
python solpi_cli.py evaluate <node_id> [--db path]
```
- 返回：node_id, score (0.0-1.0)

## 示例

```bash
# CSV 转 JSON
python solpi_cli.py convert data.csv -f json -o data.json

# 搜索图谱
python solpi_cli.py search "SoL-Pi 机制" --top-k 10

# 添加任务
python solpi_cli.py add-task "优化 Token 消耗" -p 4

# 归档文件
python solpi_cli.py archive report.md --content-type markdown
```
