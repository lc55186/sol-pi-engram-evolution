"""
阶段 5：自主演进接口
把优化决策结果写入图谱，下次检索指导决策
渐进迭代约束：禁止一步成飞轮承诺，逐步积累、逐步检索准确度提升
"""

import importlib.util
import os
from datetime import datetime
from typing import Any

# 动态导入
_gs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graph_store.py")
_gs_spec = importlib.util.spec_from_file_location("graph_store", _gs_path)
_gs_mod = importlib.util.module_from_spec(_gs_spec)
_gs_spec.loader.exec_module(_gs_mod)
GraphStore = _gs_mod.GraphStore


class EvolutionStep:
    """记录一次优化决策"""
    def __init__(self, step_type: str, action: str,
                 result: str, confidence: float,
                 metadata: dict = None):
        self.step_type = step_type  # 'action_fusion', 'compaction', 'retrieval'
        self.action = action
        self.result = result
        self.confidence = confidence
        self.metadata = metadata or {}
        self.timestamp = datetime.now().isoformat()


class EvolutionInterface:
    """自主演进接口：经验积累 + 决策指导"""

    def __init__(self, store: GraphStore, config: dict = None):
        self.store = store
        self.config = config or {}
        self.max_history = self.config.get('max_history', 1000)
        self.min_confidence_to_store = self.config.get('min_confidence_to_store', 0.5)

    def record_optimization(self, step: EvolutionStep) -> bool:
        """
        记录一次优化决策（经过核验后写入图谱）
        
        Args:
            step: 优化步骤记录
            
        Returns:
            是否成功写入
        """
        # 置信度过滤
        if step.confidence < self.min_confidence_to_store:
            return False

        # 写入图谱：作为事件节点
        title = f"优化: {step.step_type}"
        description = f"动作: {step.action} | 结果: {step.result}"

        event = self.store.add_event_node(
            title=title,
            description=description,
            event_type="decision",
            entities=[step.step_type, step.action],
            outcome=step.result,
            confidence=step.confidence,
            source_pointer=f"evo://{step.step_type}/{step.timestamp}",
            importance_score=step.confidence,
        )

        # 写入统计信息到 metadata
        meta_path = self.store.get_event_node_by_title(title)
        if meta_path and 'node_id' in meta_path:
            # 尝试读取现有元数据
            pass

        return event is not None

    def get_optimization_history(self, step_type: str = None,
                                  limit: int = 50) -> list[dict]:
        """
        获取优化历史
        
        Args:
            step_type: 筛选特定类型（可选）
            limit: 返回数量限制
            
        Returns:
            优化历史列表
        """
        nodes = self.store.get_all_nodes()
        history = []

        for node in nodes:
            if node.get('node_type') != 'event':
                continue

            title = node.get('title', '')
            if not title.startswith('优化: '):
                continue

            if step_type and step_type not in title:
                continue

            history.append({
                'node_id': node.get('node_id'),
                'title': title,
                'description': node.get('description', ''),
                'confidence': node.get('confidence', 0),
                'created_at': node.get('created_at', ''),
                'access_count': node.get('access_count', 0),
            })

        history.sort(key=lambda x: x['created_at'], reverse=True)
        return history[:limit]

    def get_decision_guidance(self, query: str,
                              context: dict = None) -> dict[str, Any]:
        """
        获取决策指导：从历史优化记录中检索相关经验
        
        Args:
            query: 当前查询
            context: 当前上下文
            
        Returns:
            决策指导：相关历史 + 建议配置
        """
        # 检索相关历史
        relevant_history = self._search_relevant_history(query)

        # 生成指导建议
        guidance = {
            'relevant_history': relevant_history,
            'suggestions': [],
            'confidence': 0.0,
        }

        if not relevant_history:
            return guidance

        # 分析历史，提取建议
        action_counts = {}
        for hist in relevant_history:
            action = hist.get('title', '').replace('优化: ', '')
            action_counts[action] = action_counts.get(action, 0) + 1

        # 如果某种优化历史频繁出现，推荐配置
        for action, count in action_counts.items():
            if count >= 3:
                guidance['suggestions'].append({
                    'action': action,
                    'frequency': count,
                    'suggestion': f"{action} 已被频繁使用，建议启用",
                })

        guidance['confidence'] = min(1.0, len(relevant_history) / 5.0)

        return guidance

    def _search_relevant_history(self, query: str) -> list[dict]:
        """搜索相关历史（使用子串匹配）"""
        query_lower = query.lower()
        history = self.get_optimization_history(limit=20)

        relevant = []
        for hist in history:
            desc = hist.get('description', '').lower()
            title = hist.get('title', '').lower()

            # 子串匹配
            if query_lower in desc or query_lower in title:
                hist['relevance_score'] = 1.0
                relevant.append(hist)

        relevant.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
        return relevant[:5]

    def evaluate_evolution_progress(self) -> dict[str, Any]:
        """评估进化进度"""
        all_history = self.get_optimization_history(limit=1000)

        if not all_history:
            return {
                'status': 'no_history',
                'total_records': 0,
                'avg_confidence': 0,
            }

        total = len(all_history)
        avg_confidence = sum(h.get('confidence', 0) for h in all_history) / total

        # 按类型分组
        type_counts = {}
        for h in all_history:
            action = h.get('title', '').replace('优化: ', 'unknown')
            type_counts[action] = type_counts.get(action, 0) + 1

        return {
            'status': 'active' if total > 10 else 'warming_up',
            'total_records': total,
            'avg_confidence': round(avg_confidence, 3),
            'type_distribution': type_counts,
            'recent_activity': all_history[:5] if all_history else [],
        }

    def incremental_update(self, batch_size: int = 100):
        """渐进更新：批量更新 importance_score"""
        nodes = self.store.get_all_nodes()
        updated = 0

        for node in nodes:
            if updated >= batch_size:
                break

            # 重新计算 importance_score（如果有 value_evaluator）
            try:
                ve_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "value_evaluator.py")
                ve_spec = importlib.util.spec_from_file_location("value_evaluator", ve_path)
                ve_mod = importlib.util.module_from_spec(ve_spec)
                ve_spec.loader.exec_module(ve_mod)
                evaluator = ve_mod.ValueEvaluator(self.store)

                new_score = evaluator.evaluate(node)
                node_id = node.get('node_id')

                if node_id and abs(new_score - node.get('importance_score', 0)) > 0.01:
                    cursor = self.store.conn.cursor()
                    cursor.execute(
                        "UPDATE nodes SET importance_score = ? WHERE node_id = ?",
                        (new_score, node_id)
                    )
                    updated += 1
            except Exception:
                pass

        self.store.conn.commit()
        return updated


# 便捷函数
def record_step(step_type: str, action: str, result: str,
                confidence: float, metadata: dict = None,
                store: GraphStore = None) -> bool:
    """记录优化步骤便捷函数"""
    interface = EvolutionInterface(store)
    step = EvolutionStep(step_type, action, result, confidence, metadata)
    return interface.record_optimization(step)

def get_guidance(query: str, store: GraphStore = None) -> dict:
    """获取决策指导便捷函数"""
    interface = EvolutionInterface(store)
    return interface.get_decision_guidance(query)
