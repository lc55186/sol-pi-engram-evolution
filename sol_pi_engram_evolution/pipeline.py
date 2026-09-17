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
    import sys
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), rel_path)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # Python 3.14 dataclass 兼容
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
        self.role_router = None
        self.knowledge_isolation = None
        self.engram = None
        self.engram_bridge = None

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

        try:
            # Engram 条件记忆层（热缓存）
            em_mod = _load_module('engram_memory', 'engram_memory.py')
            engram_db = self.config.get('engram_db', 'engram_memory.db')
            engram_config = em_mod.EngramConfig(db_path=engram_db)
            self.engram = em_mod.EngramMemory(engram_config)
            self.engram_bridge = em_mod.EngramSoLPiBridge(self.engram)
        except Exception as e:
            errors.append(f"engram_memory: {e}")
            self.logger.error(f"EngramMemory 初始化失败: {e}")
            self.engram = None
            self.engram_bridge = None

        try:
            # P1-6: 多角色顾问系统
            rs_mod = _load_module('role_system', 'role_system.py')
            tier = self.config.get('subscription_tier', 'free')
            self.role_router = rs_mod.create_router(tier)
            self.knowledge_isolation = rs_mod.KnowledgeIsolation()
            # P1-6a: A2A 协议适配层（多 Agent 会诊）
            self.a2a_adapter = rs_mod.A2ARoleAdapter(self.role_router)
        except Exception as e:
            errors.append(f"role_system: {e}")
            self.logger.error(f"RoleSystem 初始化失败: {e}")
            self.role_router = None
            self.knowledge_isolation = None
            self.a2a_adapter = None

        if errors:
            self.logger.warning(f"模块初始化完成，{len(errors)} 个模块失败: {errors}")
        else:
            self.logger.info("所有模块初始化完成")

    def process_query(self, query: str,
                      messages: list[dict] = None,
                      tier: str = None) -> dict[str, Any]:
        """处理查询：完整流程（含 Engram 记忆召回 + 角色路由）"""
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'routing': None,
            'context': None,
            'guidance': None,
            'engram_hits': [],
            'role': None,
            'role_prompt': None,
        }

        # 0. Engram 快速记忆召回（热缓存）
        if self.engram_bridge:
            engram_result = self.engram_bridge.pre_query(query)
            result['engram_hits'] = engram_result.get('engram_hits', [])
            if engram_result.get('has_memory'):
                self.logger.info(f"Engram 召回 {len(result['engram_hits'])} 条记忆")

        # 0.5 角色路由（P1-6: 多角色顾问）
        active_role = None
        if self.role_router:
            if tier:
                from role_system import SubscriptionTier
                tier_map = {
                    'free': SubscriptionTier.FREE,
                    'professional': SubscriptionTier.PROFESSIONAL,
                    'flagship': SubscriptionTier.FLAGSHIP,
                    'enterprise': SubscriptionTier.ENTERPRISE,
                }
                if tier in tier_map:
                    self.role_router.tier = tier_map[tier]
            active_role = self.role_router.auto_route(query)
            result['role'] = active_role.value
            result['role_prompt'] = self.role_router.get_current_prompt()
            self.logger.info(f"角色路由: {active_role.value}")

        # 1. 路由决策
        routing = self.router.route(messages or [], query)
        result['routing'] = routing
        self.logger.info(f"路由决策: {routing}", extra={"query": query})

        # 2. 根据路由执行不同流程
        if routing == 'lightweight':
            result['context'] = {'mode': 'lightweight', 'query': query}
        else:
            context = self.context_manager.build_context(query)
            result['context'] = context
            guidance = self.evolution_interface.get_decision_guidance(query)
            result['guidance'] = guidance

        # 3. A2A 多 Agent 会诊（旗舰版/企业版启用）
        if self.a2a_adapter and active_role:
            from role_system import SubscriptionTier
            if self.role_router.tier in (SubscriptionTier.FLAGSHIP, SubscriptionTier.ENTERPRISE):
                consult = self.a2a_adapter.multi_agent_consult(query)
                result['a2a_consult'] = consult
                self.logger.info(f"A2A 会诊: {len(consult['participating_roles'])} 角色参与")

        # 4. 后处理：将查询+角色信息存入 Engram（P1-7 增强）
        if self.engram_bridge and active_role:
            role_name = active_role.value
            self.engram_bridge.post_response(
                query=query,
                response=f"role_routed:{role_name}",
                extracted_facts=[{
                    'text': f"[{role_name}] {query}",
                    'importance': 0.4,
                    'data': {
                        'type': 'query_role_binding',
                        'role': role_name,
                        'query': query[:200],
                    }
                }]
            )

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
        stats = {
            'graph': self.graph_store.get_node_stats(),
            'evolution': self.evolution_interface.evaluate_evolution_progress(),
        }
        # Engram 记忆统计
        if self.engram:
            stats['engram'] = self.engram.stats()
        # 角色系统统计
        if self.role_router:
            stats['role_system'] = {
                'current_role': self.role_router.current_role.value,
                'switch_count': self.role_router.switch_count,
                'available_roles': [r.value for r in self.role_router.available_roles],
            }
            # A2A 适配器统计
            if self.a2a_adapter:
                stats['a2a_adapter'] = {
                    'task_count': len(self.a2a_adapter._task_log),
                    'cancelled_count': len(self.a2a_adapter._cancelled_tasks),
                    'agent_cards': len(self.a2a_adapter.list_agent_cards()),
                }
        return stats

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
    query_parser.add_argument('--tier', default=None, help='套餐等级 (free/professional/flagship/enterprise)')

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

    # role 命令（P1-6: 多角色系统）
    p_role = subparsers.add_parser('role', help='角色系统')
    p_role.add_argument('--list', action='store_true', help='列出可用角色')
    p_role.add_argument('--tier', default='free', help='套餐等级')
    p_role.add_argument('--switch', default=None, help='切换到指定角色 (negotiator/psychologist/cfo/legal/industry)')
    p_role.add_argument('--query', default=None, help='测试角色路由')

    # a2a-consult 命令（A2A 多 Agent 会诊）
    p_a2a = subparsers.add_parser('a2a-consult', help='A2A 多 Agent 会诊')
    p_a2a.add_argument('query', help='会诊查询内容')

    args = parser.parse_args()

    pipeline = EvolutionPipeline(config={
        'db_path': args.db,
        'archive_root': args.archive_dir,
        'subscription_tier': getattr(args, 'tier', 'free') or 'free',
    })

    if args.command == 'query':
        result = pipeline.process_query(args.query, tier=args.tier)
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

    elif args.command == 'role':
        from role_system import RoleType, ROLE_REGISTRY
        if args.list:
            roles = pipeline.role_router.available_roles if pipeline.role_router else []
            tier_config = {}
            for r in roles:
                cfg = ROLE_REGISTRY[r]
                tier_config[r.value] = {
                    'name_cn': cfg.name_cn,
                    'capability': cfg.core_capability,
                    'priority': cfg.priority,
                }
            print(json.dumps({'tier': args.tier, 'roles': tier_config}, indent=2, ensure_ascii=False))
        elif args.switch:
            role_map = {r.value: r for r in RoleType}
            if args.switch in role_map:
                success = pipeline.role_router.force_role(role_map[args.switch]) if pipeline.role_router else False
                print(json.dumps({'switched': success, 'role': args.switch}, ensure_ascii=False))
            else:
                print(json.dumps({'error': f'unknown role: {args.switch}'}, ensure_ascii=False))
        elif args.query:
            routed = pipeline.role_router.auto_route(args.query) if pipeline.role_router else None
            print(json.dumps({'query': args.query, 'routed_role': routed.value if routed else None}, ensure_ascii=False))
        else:
            current = pipeline.role_router.current_role if pipeline.role_router else None
            print(json.dumps({'current_role': current.value if current else None}, ensure_ascii=False))

    elif args.command == 'a2a-consult':
        # A2A 多 Agent 会诊（需旗舰版/企业版）
        from role_system import SubscriptionTier
        tier = pipeline.role_router.tier if pipeline.role_router else SubscriptionTier.FREE
        if tier not in (SubscriptionTier.FLAGSHIP, SubscriptionTier.ENTERPRISE):
            print(json.dumps({'error': 'A2A 会诊需旗舰版或企业版', 'current_tier': tier.value}, ensure_ascii=False))
        else:
            consult = pipeline.a2a_adapter.multi_agent_consult(args.query) if pipeline.a2a_adapter else None
            print(json.dumps(consult, indent=2, ensure_ascii=False) if consult else '{"error": "A2A adapter not available"}')

    else:
        parser.print_help()

    pipeline.close()


if __name__ == '__main__':
    main()
