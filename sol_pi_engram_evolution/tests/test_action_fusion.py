"""
阶段 2：动作融合测试
验证可合并判定、不可合并判定、合并结果
"""

import importlib.util
import os


def _load_module(name, rel_path):
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", rel_path
    )
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_action_fusion = _load_module("action_fusion", "action_fusion.py")


def test_fuse_simple_sequence():
    """测试简单确定性序列合并"""
    ops = [
        {'type': 'edit', 'payload': '修改文件 A'},
        {'type': 'run', 'payload': '运行测试'},
        {'type': 'read', 'payload': '读取结果'},
    ]
    result = _action_fusion.fuse_operations(ops)

    assert len(result) == 1
    assert result[0]['type'] == 'fused_sequence'
    assert len(result[0]['steps']) == 3
    assert result[0]['reduced_rounds'] == 2

    print("✓ Fuse simple sequence passed")


def test_fuse_with_non_fusable_break():
    """测试不可合并：中间有非确定性操作"""
    ops = [
        {'type': 'edit', 'payload': '修改文件 A'},
        {'type': 'think', 'payload': '模型思考'},
        {'type': 'run', 'payload': '运行测试'},
    ]
    result = _action_fusion.fuse_operations(ops)

    # edit 和 think 不可融合，think 和 run 也不可融合
    assert len(result) == 3
    assert result[0]['type'] == 'edit'
    assert result[1]['type'] == 'think'
    assert result[2]['type'] == 'run'

    print("✓ Fuse with non-fusable break passed")


def test_fuse_single_operation():
    """测试单个操作不合并"""
    ops = [
        {'type': 'edit', 'payload': '修改文件 A'},
    ]
    result = _action_fusion.fuse_operations(ops)

    assert len(result) == 1
    assert result[0]['type'] == 'edit'

    print("✓ Fuse single operation passed")


def test_fuse_mixed_sequence():
    """测试混合序列：部分可融合，部分不可"""
    ops = [
        {'type': 'edit', 'payload': '修改文件 A'},
        {'type': 'run', 'payload': '运行测试'},
        {'type': 'think', 'payload': '模型思考'},
        {'type': 'edit', 'payload': '修改文件 B'},
        {'type': 'read', 'payload': '读取结果'},
    ]
    result = _action_fusion.fuse_operations(ops)

    # edit + run 可融合，think 独立，edit + read 可融合
    assert result[0]['type'] == 'fused_sequence'
    assert result[1]['type'] == 'think'
    assert result[2]['type'] == 'fused_sequence'

    print("✓ Fuse mixed sequence passed")


def test_fuse_empty():
    """测试空序列"""
    result = _action_fusion.fuse_operations([])
    assert result == []

    print("✓ Fuse empty passed")


def test_fuse_non_fusable_types():
    """测试非可融合类型操作"""
    ops = [
        {'type': 'think', 'payload': '思考'},
        {'type': 'decide', 'payload': '决策'},
        {'type': 'wait', 'payload': '等待'},
    ]
    result = _action_fusion.fuse_operations(ops)

    assert len(result) == 3
    assert all(r['type'] in ('think', 'decide', 'wait') for r in result)

    print("✓ Fuse non-fusable types passed")


if __name__ == "__main__":
    test_fuse_simple_sequence()
    test_fuse_with_non_fusable_break()
    test_fuse_single_operation()
    test_fuse_mixed_sequence()
    test_fuse_empty()
    test_fuse_non_fusable_types()
    print("\n✅ 阶段 2 动作融合测试全部通过")
