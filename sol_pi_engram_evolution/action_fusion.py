"""
阶段 2：动作融合模块
确定性任务流合并
"""

from typing import Any


def fuse_operations(operations: list[dict[str, Any]],
                    config: dict = None) -> list[dict[str, Any]]:
    """合并可融合的确定性操作序列，减少模型往返"""
    config = config or {}
    merged = []
    i = 0
    while i < len(operations):
        op = operations[i]
        if _is_fusable(op, operations, i, config):
            fused = _fuse_sequence(operations, i, config)
            merged.append(fused)
            i += len(fused['steps'])
        else:
            merged.append(op)
            i += 1
    return merged


def _is_fusable(op: dict[str, Any], operations: list[dict],
                idx: int, config: dict) -> bool:
    """判断当前操作是否可融合（需要有后续可融合操作）"""
    fusable_types = {'edit', 'run', 'read'}
    if op.get('type') not in fusable_types:
        return False

    # 检查后续是否有可融合操作可以合并
    for j in range(idx + 1, min(idx + 3, len(operations))):
        next_op = operations[j]
        if next_op.get('type') in fusable_types:
            return True  # 有后续可融合操作
        else:
            return False  # 被非确定性操作阻断

    return False  # 无后续操作，无需融合


def _fuse_sequence(operations: list[dict], start_idx: int,
                   config: dict) -> dict[str, Any]:
    """将一系列确定性操作合并为本地执行序列"""
    steps = []
    i = start_idx
    fusable_types = {'edit', 'run', 'read'}
    while i < len(operations):
        op = operations[i]
        if op.get('type') in fusable_types:
            steps.append(op)
            i += 1
        else:
            break
    return {
        'type': 'fused_sequence',
        'steps': steps,
        'execution_mode': 'local',
        'reduced_rounds': max(0, len(steps) - 1),
    }
