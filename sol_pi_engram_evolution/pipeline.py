#!/usr/bin/env python
"""
Pipeline 主入口（V0.2 改进版）
串联阶段 0~5 所有模块

V0.2 改进：
- 使用统一 logger 替代标准 logging
- 使用类型安全的 Config 注入
- 模块初始化失败优雅降级
"""

import json
import os
from datetime import datetime
from typing import Any


# 动态导入所有模块
def _load_module(name, rel_path):
    import importlib.util
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class EvolutionPipeline:
    """进化系统主 Pipeline（V0.2 改进）"""

    def __init__(self, config: dict[str, Any] = None):
        self.config = config or {}
        # V0.2: 使用统一 logger
        from logger import get_logger, log_pipeline_event
        self.logger = get_logger("pipeline")
        self._log_pipeline_event = log_pipeline_event

        # 初始化所有模块
        self.graph_store = None
        self.observation_pack = None
        self.graph_extractor = None
        self.evidence_verifier = None
        self.graph_retriever = None
        self.context_manager = None
        self.action_fusion = None
        self.context_compactor = None
        self.value_evaluator = None
        self.router = None
        self.evolution_interface = None

        self._init_modules()

    def _init_modules(self):
        """初始化所有模块（V0.2: 优雅降级）"""
        errors = []

        try:
            # 阶段 0: 图谱存储
            gs_mod = _load_module('graph_store', 'graph_store.py')
            db_path = self.config.get('db_path', 'evolution.db')
            self.graph_store = gs_mod.GraphStore(db_path=db_path)
        except Exception as e:
            errors.append(f"graph_store: {e}")
            self.logger.error(f"GraphStore 初始化失败: {e}")

        try:
            # 阶段 1: ObservationPack
            op_mod = _load_module('observation_pack', 'observation_pack.py')
            archive_root = self.config.get('archive_root', './observations')
            self.observation_pack = op_mod.ObservationPack(archive_root=archive_root)
        except Exception as e:
            errors.append(f"observation_pack: {e}")
            self.logger.error(f"ObservationPack 初始化失败: {e}")

        try:
            # 阶段 1: 图谱提取
            ge_mod = _load_module('graph_extractor', 'graph_extractor.py')
            self.graph_extractor = ge_mod.GraphExtractor()
        except Exception as e:
            errors.append(f"graph_extractor: {e}")
            self.logger.error(f"GraphExtractor 初始化失败: {e}")

        try:
            # 阶段 1: 证据核验
            ev_mod = _load_module('evidence_verifier', 'evidence_verifier.py')
            archive_root = self.config.get('archive_root', './observations')
            self.evidence_verifier = ev_mod.EvidenceVerifier(archive_dir=archive_root)
        except Exception as e:
            errors.append(f"evidence_verifier: {e}")
            self.logger.error(f"EvidenceVerifier 初始化失败: {e}")

        try:
            # 阶段 2: 图谱检索
            gr_mod = _load_module('graph_retriever', 'graph_retriever.py')
            self.graph_retriever = gr_mod.GraphRetriever(self.graph_store)
        except Exception as e:
            errors.append(f"graph_retriever: {e}")
            self.logger.error(f"GraphRetriever 初始化失败: {e}")

        try:
            # 阶段 2: 上下文管理
            cm_mod = _load_module('context_manager', 'context_manager.py')
            self.context_manager = cm_mod.ContextManager(self.graph_retriever)
        except Exception as e:
            errors.append(f"context_manager: {e}")
            self.logger.error(f"ContextManager 初始化失败: {e}")

        try:
            # 阶段 2: 动作融合
            af_mod = _load_module('action_fusion', 'action_fusion.py')
            self.action_fusion = af_mod
        except Exception as e:
            errors.append(f"action_fusion: {e}")
            self.logger.error(f"ActionFusion 初始化失败: {e}")

        try:
            # 阶段 2: 上下文压缩
            cc_mod = _load_module('context_compactor', 'context_compactor.py')
            self.context_compactor = cc_mod
        except Exception as e:
            errors.append(f"context_compactor: {e}")
            self.logger.error(f"ContextCompactor 初始化失败: {e}")

        try:
            # 阶段 3: 价值评估
            ve_mod = _load_module('value_evaluator', 'value_evaluator.py')
            self.value_evaluator = ve_mod.ValueEvaluator(self.graph_store)
        except Exception as e:
            errors.append(f"value_evaluator: {e}")
            self.logger.error(f"ValueEvaluator 初始化失败: {e}")

        try:
            # 阶段 4: 路由
            r_mod = _load_module('routing', 'routing.py')
            self.router = r_mod.Router(self.graph_store)
        except Exception as e:
            errors.append(f"router: {e}")
            self.logger.error(f"Router 初始化失败: {e}")

        try:
            # 阶段 5: 自主演进
            ei_mod = _load_module('evolution_interface', 'evolution_interface.py')
            self.evolution_interface = ei_mod.EvolutionInterface(self.graph_store)
        except Exception as e:
            errors.append(f"evolution_interface: {e}")
            self.logger.error(f"EvolutionInterface 初始化失败: {e}")

        if errors:
            self.logger.warning(f"模块初始化完成，{len(errors)} 个模块失败: {errors}")
        else:
            self.logger.info("所有模块初始化完成")

    def process_query(self, query: str,
                      messages: list[dict] = None) -> dict[str, Any]:
        """处理查询：完整流程"""
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'routing': None,
            'context': None,
            'guidance': None,
        }

        # 1. 路由决策
        routing = self.router.route(messages or [], query)
        result['routing'] = routing
        self.logger.info(f"路由决策: {routing}", extra={"query": query})

        # 2. 根据路由执行不同流程
        if routing == 'lightweight':
            # 轻量流程：不启动图谱检索
            result['context'] = {'mode': 'lightweight', 'query': query}
        else:
            # 标准/完整流程：图谱检索 + 上下文管理
            context = self.context_manager.build_context(query)
            result['context'] = context

            # 获取决策指导
            guidance = self.evolution_interface.get_decision_guidance(query)
            result['guidance'] = guidance

        return result

    def archive_and_extract(self, content: str,
                            content_type: str = "text",
                            metadata: dict = None) -> dict[str, Any]:
        """归档内容并提取图谱节点"""
        # 1. 归档
        handle = self.observation_pack.archive(content, content_type, metadata)

        # 2. 提取图谱节点
        extraction = self.graph_extractor.extract_from_content(
            content,
            source_pointer=handle['filepath'],
            metadata=metadata
        )

        # 3. 证据核验
        verified_tasks = []
        for task in extraction['tasks']:
            verification = self.evidence_verifier.verify_node(
                task.__dict__,
                handle['filepath']
            )
            if verification['valid']:
                verified_tasks.append(task)

        verified_events = []
        for event in extraction['events']:
            verification = self.evidence_verifier.verify_node(
                event.__dict__,
                handle['filepath']
            )
            if verification['valid']:
                verified_events.append(event)

        # 4. 写入图谱存储
        for task in verified_tasks:
            self.graph_store.add_task_node(
                title=task.title,
                description=task.description,
                status=task.status,
                priority=task.priority,
                source_pointer=task.source_pointer,
                confidence=task.confidence,
            )

        for event in verified_events:
            self.graph_store.add_event_node(
                title=event.title,
                description=event.description,
                event_type=event.event_type,
                entities=event.entities,
                outcome=event.outcome,
                source_pointer=event.source_pointer,
                confidence=event.confidence,
            )

        return {
            'handle': handle,
            'extraction': extraction,
            'verified_tasks': len(verified_tasks),
            'verified_events': len(verified_events),
        }

    def get_stats(self) -> dict[str, Any]:
        """获取系统统计"""
        return {
            'graph': self.graph_store.get_node_stats(),
            'evolution': self.evolution_interface.evaluate_evolution_progress(),
        }

    def get_evolution_status(self) -> dict[str, Any]:
        """获取 RSI 进化引擎状态"""
        try:
            from self_evolution import get_evolution_engine
            engine = get_evolution_engine()
            return engine.get_status()
        except Exception as e:
            return {"error": str(e)}

    def ab_test_prompt(self, task_id: str, template: str, description: str = ""):
        """注册 A/B 测试 Prompt"""
        from self_evolution import get_evolution_engine
        engine = get_evolution_engine()
        return engine.ab_test_prompt(task_id, template, description)

    def get_best_prompt(self, task_id: str) -> str | None:
        """获取当前最佳 Prompt"""
        from self_evolution import get_evolution_engine
        engine = get_evolution_engine()
        return engine.get_best_prompt(task_id)

    def close(self):
        """关闭系统"""
        if self.graph_store:
            self.graph_store.close()


def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description='SoL-Pi × Engram 进化系统')
    parser.add_argument('--db', default='evolution.db', help='数据库路径')
    parser.add_argument('--archive-dir', default='./observations', help='归档目录')
    subparsers = parser.add_subparsers(dest='command')

    # query 命令
    query_parser = subparsers.add_parser('query', help='处理查询')
    query_parser.add_argument('query', help='查询内容')

    # archive 命令
    archive_parser = subparsers.add_parser('archive', help='归档内容')
    archive_parser.add_argument('file', help='要归档的文件')

    # stats 命令
    subparsers.add_parser('stats', help='查看统计')

    # evolution 命令
    p_ev = subparsers.add_parser('evolution', help='RSI 进化引擎状态')
    p_ev.add_argument('--status', action='store_true', help='查看状态')

    # ab-test 命令
    p_ab = subparsers.add_parser('ab-test', help='Prompt A/B 测试')
    p_ab.add_argument('--task', required=True, help='任务 ID')
    p_ab.add_argument('--template', required=True, help='Prompt 模板')
    p_ab.add_argument('--description', default="", help='变体描述')
    p_ab.add_argument('--get-best', action='store_true', help='获取当前最佳 Prompt')

    args = parser.parse_args()

    pipeline = EvolutionPipeline(config={
        'db_path': args.db,
        'archive_root': args.archive_dir,
    })

    if args.command == 'query':
        result = pipeline.process_query(args.query)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == 'archive':
        with open(args.file, 'r', encoding='utf-8') as f:
            content = f.read()
        result = pipeline.archive_and_extract(content, metadata={'source': args.file})
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

    elif args.command == 'stats':
        stats = pipeline.get_stats()
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    elif args.command == 'evolution':
        if args.status:
            status = pipeline.get_evolution_status()
            print(json.dumps(status, indent=2, ensure_ascii=False, default=str))

    elif args.command == 'ab-test':
        if args.get_best:
            best = pipeline.get_best_prompt(args.task)
            print(json.dumps({"task": args.task, "best_prompt": best}, ensure_ascii=False))
        else:
            result = pipeline.ab_test_prompt(args.task, args.template, args.description)
            print(json.dumps(vars(result), indent=2, ensure_ascii=False, default=str))

    else:
        parser.print_help()

    pipeline.close()


if __name__ == '__main__':
    main()
