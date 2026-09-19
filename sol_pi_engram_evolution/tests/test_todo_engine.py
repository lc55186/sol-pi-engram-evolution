#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Autonomous TODO Engine
"""
import os
import sys
import tempfile
import sqlite3
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from todo_engine import TodoEngine


def _copy_test_db():
    """Copy the real graph.db to a temp location"""
    tmp = tempfile.mktemp(suffix=".db")
    import shutil
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "graph.db")
    shutil.copy2(db_path, tmp)
    return tmp


def test_engine_initialization():
    """Test engine initializes correctly"""
    tmp = _copy_test_db()
    
    # Override DB_PATH in engine module
    import todo_engine
    todo_engine.DB_PATH = tmp
    
    engine = TodoEngine()
    assert engine.conn is not None
    engine.close()
    
    # Cleanup
    os.unlink(tmp)
    print("  ✓ Engine initialization works")


def test_check_pending():
    """Test checking pending tasks"""
    tmp = _copy_test_db()
    
    import todo_engine
    todo_engine.DB_PATH = tmp
    
    engine = TodoEngine()
    pending = engine.check_pending()
    assert isinstance(pending, list)
    assert len(pending) > 0
    
    engine.close()
    os.unlink(tmp)
    print(f"  ✓ Check pending: found {len(pending)} tasks")


def test_complete_task():
    """Test completing a task"""
    tmp = _copy_test_db()
    
    import todo_engine
    todo_engine.DB_PATH = tmp
    
    engine = TodoEngine()
    
    # Complete a task
    result = engine.complete_task("todo-001", "Test completion")
    assert result is True
    
    # Verify
    pending = engine.check_pending()
    todo_001_found = any(t["node_id"] == "todo-001" for t in pending)
    assert not todo_001_found, "todo-001 should not be in pending"
    
    engine.close()
    os.unlink(tmp)
    print("  ✓ Complete task works correctly")


def test_add_task():
    """Test adding a new task"""
    tmp = _copy_test_db()
    
    import todo_engine
    todo_engine.DB_PATH = tmp
    
    engine = TodoEngine()
    
    new_id = engine.add_task("测试任务", "测试描述", 3, "test-event")
    assert new_id is not None
    
    # Verify it exists
    pending = engine.check_pending()
    found = any(t["node_id"] == new_id for t in pending)
    assert found, f"{new_id} should be in pending"
    
    engine.close()
    os.unlink(tmp)
    print("  ✓ Add task works correctly")


def test_generate_report():
    """Test report generation"""
    tmp = _copy_test_db()
    
    import todo_engine
    todo_engine.DB_PATH = tmp
    
    engine = TodoEngine()
    report = engine.generate_report()
    
    assert "待办报告" in report or "待处理" in report
    assert "已完成" in report
    
    engine.close()
    os.unlink(tmp)
    print("  ✓ Report generation works")


if __name__ == "__main__":
    print("=" * 60)
    print("Autonomous TODO Engine Tests")
    print("=" * 60)
    
    test_engine_initialization()
    test_check_pending()
    test_complete_task()
    test_add_task()
    test_generate_report()
    
    print("\n✅ All TODO engine tests passed")
