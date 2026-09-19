#!/usr/bin/env python
"""
阶段 1：图谱提取模块
负责从归档内容中提取 TaskNode、EventNode、RelationNode
"""

import re
from datetime import datetime

from graph_schema import (
    EventNode,
    TaskNode,
    create_event_node,
    create_relation_node,
    create_task_node,
)


class GraphExtractor:
    """
    图谱提取器
    
    功能:
    - 从归档内容中提取结构化节点
    - 基于启发式规则识别 Task、Event、Relation
    - 支持小模型辅助提取 (预留接口)
    - 置信度标注 + source_pointer 追踪
    """

    def __init__(self, config: dict | None = None):
        """
        初始化提取器
        
        Args:
            config: 配置字典
                - min_confidence: 最低置信度 (默认 0.5)
                - enable_heuristic: 启用启发式提取 (默认 True)
                - enable_llm_assist: 启用 LLM 辅助 (默认 False)
                - llm_model: LLM 模型名称 (可选)
                - chunk_size: 分块大小 (默认 5000)
        """
        self.config = config or {}
        self.min_confidence = self.config.get('min_confidence', 0.5)
        self.enable_heuristic = self.config.get('enable_heuristic', True)
        self.enable_llm_assist = self.config.get('enable_llm_assist', False)
        self.llm_model = self.config.get('llm_model', None)
        self.chunk_size = self.config.get('chunk_size', 5000)

    def extract_from_content(self, content: str,
                             source_pointer: str = "",
                             metadata: dict | None = None) -> dict[str, list]:
        """
        从内容中提取图谱节点
        
        Args:
            content: 要提取的内容
            source_pointer: 原始归档指针 (用于追踪来源)
            metadata: 额外元数据
            
        Returns:
            包含提取结果的字典:
            {
                'tasks': [TaskNode, ...],
                'events': [EventNode, ...],
                'relations': [RelationNode, ...],
                'extraction_meta': {...}
            }
        """
        result = {
            'tasks': [],
            'events': [],
            'relations': [],
            'extraction_meta': {
                'extracted_at': datetime.now().isoformat(),
                'content_size': len(content),
                'source_pointer': source_pointer,
                'heuristic_enabled': self.enable_heuristic,
                'llm_assist_enabled': self.enable_llm_assist,
            }
        }

        if not content or not content.strip():
            result['extraction_meta']['reason'] = '空内容'
            return result

        # 分块处理
        chunks = self._chunk(content)
        result['extraction_meta']['chunk_count'] = len(chunks)

        # 启发式提取
        if self.enable_heuristic:
            for chunk in chunks:
                chunk_result = self._extract_heuristic(chunk, source_pointer, metadata)
                result['tasks'].extend(chunk_result['tasks'])
                result['events'].extend(chunk_result['events'])
                result['relations'].extend(chunk_result['relations'])

        # LLM 辅助提取 (预留接口)
        if self.enable_llm_assist:
            llm_result = self._extract_with_llm(content, source_pointer)
            if llm_result:
                result['tasks'].extend(llm_result.get('tasks', []))
                result['events'].extend(llm_result.get('events', []))
                result['relations'].extend(llm_result.get('relations', []))

        # 去重
        result = self._deduplicate(result)

        # 应用置信度阈值
        result = self._apply_confidence_threshold(result)

        # 更新提取元数据
        result['extraction_meta']['task_count'] = len(result['tasks'])
        result['extraction_meta']['event_count'] = len(result['events'])
        result['extraction_meta']['relation_count'] = len(result['relations'])

        return result

    def _chunk(self, content: str) -> list[str]:
        """将内容分块"""
        chunks = []
        for i in range(0, len(content), self.chunk_size):
            chunk = content[i:i + self.chunk_size]
            # 尝试在自然边界处分割
            if i > 0:
                # 查找最近的段落/换行边界
                search_start = max(0, i - 200)
                search_end = min(len(content), i + self.chunk_size)
                boundary = self._find_boundary(content[search_start:search_end])
                if boundary is not None:
                    chunk = content[i:i + boundary]
            chunks.append(chunk)
        return chunks

    def _find_boundary(self, text: str) -> int | None:
        """查找最佳分割边界"""
        # 优先查找双换行符
        double_newline = text.find('\n\n')
        if double_newline > 100:
            return double_newline + 2

        # 查找单换行符
        newline = text.find('\n')
        if newline > 50:
            return newline + 1

        # 查找句号
        period = text.find('。')
        if period > 30:
            return period + 1

        return None

    def _extract_heuristic(self, chunk: str,
                          source_pointer: str,
                          metadata: dict | None) -> dict[str, list]:
        """基于启发式规则提取"""
        tasks = []
        events = []
        relations = []

        # === 任务提取规则 ===
        # 识别任务模式: "任务X:", "任务X：", "TODO:", "目标:", "需要做..." 等
        task_patterns = [
            r'(?:任务|task)\s*\d*\s*[：:][\s]*(.{1,100}?)(?=\n|\r|\Z)',
            r'(?:TODO|待办|待完成|需要做|要解决|待办事项)[\s:：]*(.{1,100}?)(?=\n|\r|\Z)',
            r'(?:目标|objective|goal| aim|目的)[\s:：]*[【]?(.{1,100}?)[】]?(?=\n|\r|\Z)',
            r'[【【]任务[】】][\s:：]*(.{1,100}?)(?=\n|\r|\Z)',
            r'待办[：:](.{1,100}?)(?=\n|\r|\Z)',
        ]

        for pattern in task_patterns:
            matches = re.finditer(pattern, chunk, re.IGNORECASE | re.DOTALL)
            for match in matches:
                task_title = match.group(1).strip()
                task_title = self._clean_text(task_title)
                if task_title and len(task_title) > 2:
                    task = create_task_node(
                        title=task_title,
                        description=self._extract_task_description(chunk, task_title),
                        status="not_started",
                        confidence=self._estimate_task_confidence(task_title, chunk),
                        source_pointer=source_pointer,
                    )
                    tasks.append(task)

        # === 事件提取规则 ===
        # 识别事件模式: "决策:", "结果:", "里程碑:", "错误:", "发生了...", "完成了..." 等
        event_patterns = [
            (r'(?:决策|decision|决定|选择|判定)[\s:：]*(.{1,200}?)(?=\n|\r|\Z)', 'decision'),
            (r'(?:结果|outcome|结论|结论是|最终)[-：\s]*(.{1,200}?)(?=\n|\r|\Z)', 'outcome'),
            (r'(?:里程碑|milestone|里程碑事件|阶段性成果)[\s:：]*(.{1,200}?)(?=\n|\r|\Z)', 'milestone'),
            (r'(?:错误|error|异常|failure|失败|出错|bug)[\s:：]*(.{1,200}?)(?=\n|\r|\Z)', 'error'),
            (r'(?:发现|discovery|发现了|注意到|意识到)[\s:：]*(.{1,200}?)(?=\n|\r|\Z)', 'discovery'),
            (r'(?:变化|change|变动|调整|修改|更新)[\s:：]*(.{1,200}?)(?=\n|\r|\Z)', 'change'),
            (r'(?:完成|completed|done|结束|结束了|达成|实现了)[\s:：]*(.{1,200}?)(?=\n|\r|\Z)', 'outcome'),
            (r'(?:开始|started|开始了|启动| initiated)[\s:：]*(.{1,200}?)(?=\n|\r|\Z)', 'milestone'),
            (r'[【\[]事件[\]】](.{1,200}?)(?=\n|\r|\Z)', 'other'),
            (r'(?:发生|occurred|happened|出现|遇到)[\s:：]*(.{1,200}?)(?=\n|\r|\Z)', 'other'),
        ]

        for pattern, event_type in event_patterns:
            matches = re.finditer(pattern, chunk, re.IGNORECASE | re.DOTALL)
            for match in matches:
                event_title = match.group(1).strip()
                event_title = self._clean_text(event_title)
                if event_title and len(event_title) > 2:
                    event = create_event_node(
                        title=event_title,
                        description=self._extract_event_description(chunk, event_title),
                        event_type=event_type,
                        entities=self._extract_entities(chunk),
                        outcome=self._extract_outcome(chunk, event_type),
                        confidence=self._estimate_event_confidence(event_title, chunk, event_type),
                        source_pointer=source_pointer,
                    )
                    events.append(event)

        # === 关系提取规则 ===
        # 识别关系模式: "依赖...", "导致...", "因为...所以...", "包含...", "属于..." 等
        relation_patterns = [
            (r'(?:任务A|第一个任务|前一个任务)[\s:]*(.{1,100})?\s*(?:依赖| depends on|依赖于|依靠)\s*(?:任务B|第二个任务|后一个任务|后者|另一项任务|【?(.{1,100}?)】?)',
             'depends_on'),
            (r'(?:原因|cause|导致| leads to|造成|使得|让)\s*【?(.{1,100}?)】?\s*(?:导致|导致了| leads to|造成|使得)\s*【?(.{1,100}?)】?',
             'causes'),
            (r'【?(.{1,100}?)】?\s*(?:触发| triggers|引发|引起|启动)\s*【?(.{1,100}?)】?',
             'triggers'),
            (r'【?(.{1,100}?)】?\s*(?:阻塞| blocks|阻碍|阻止|影响)\s*【?(.{1,100}?)】?',
             'blocks'),
            (r'【?(.{1,100}?)】?\s*(?:属于| part of|包含|包括|组成|构成)\s*【?(.{1,100}?)】?',
             'part_of'),
            (r'【?(.{1,100}?)】?\s*(?:相关| related|关联|联系|配合|协作)\s*【?(.{1,100}?)】?',
             'related_to'),
            (r'(?:.{1,100}?)和(?:.{1,100}?)的协作', 'related_to'),  # 协作关系
        ]

        # 提取出的实体列表 (用于构建关系)
        entities = self._extract_entities(chunk)

        for pattern, relation_type in relation_patterns:
            matches = re.finditer(pattern, chunk, re.IGNORECASE | re.DOTALL)
            for match in matches:
                groups = match.groups()
                if len(groups) >= 2:
                    source = self._clean_text(groups[0]) if groups[0] else None
                    target = self._clean_text(groups[-1]) if groups[-1] else None

                    if source and target and len(source) > 1 and len(target) > 1:
                        # 尝试查找已提取的节点 ID
                        source_id = self._find_node_id(source, tasks, events)
                        target_id = self._find_node_id(target, tasks, events)

                        relation = create_relation_node(
                            source_node_id=source_id or f"entity:{source}",
                            target_node_id=target_id or f"entity:{target}",
                            relation_type=relation_type,
                            weight=self._estimate_relation_weight(source, target, chunk),
                            description=self._extract_relation_description(chunk, source, target),
                            confidence=self._estimate_relation_confidence(source, target, chunk),
                            source_pointer=source_pointer,
                        )
                        relations.append(relation)

        return {
            'tasks': tasks,
            'events': events,
            'relations': relations,
        }

    def _extract_with_llm(self, content: str,
                         source_pointer: str) -> dict | None:
        """
        使用 LLM 辅助提取 (预留接口)
        
        当前实现为占位符，实际使用时需要集成具体的 LLM API
        """
        # TODO: 集成 LLM 提取逻辑
        # 示例:
        # prompt = f"从以下内容中提取任务、事件和关系...\n\n{content}"
        # response = call_llm(prompt, model=self.llm_model)
        # return parse_llm_response(response)

        # 当前返回 None 表示不使用 LLM
        return None

    def _clean_text(self, text: str) -> str:
        """清洗文本"""
        if not text:
            return ""

        # 移除多余的空白
        text = re.sub(r'\s+', ' ', text)

        # 移除特殊标记
        text = re.sub(r'【.*?】', '', text)
        text = re.sub(r'\[.*?\]', '', text)

        # 移除多余的标点
        text = re.sub(r'[\.。！？\?!]+$', '', text)

        return text.strip()

    def _extract_task_description(self, chunk: str, task_title: str) -> str:
        """从上下文中提取任务描述"""
        # 查找任务标题后面的内容
        idx = chunk.find(task_title)
        if idx == -1:
            return ""

        # 获取任务标题后的 200 个字符
        start = idx + len(task_title)
        end = min(start + 200, len(chunk))
        description = chunk[start:end].strip()

        # 清洗
        description = self._clean_text(description)

        return description[:500]  # 限制长度

    def _extract_event_description(self, chunk: str, event_title: str) -> str:
        """从上下文中提取事件描述"""
        idx = chunk.find(event_title)
        if idx == -1:
            return ""

        start = idx + len(event_title)
        end = min(start + 200, len(chunk))
        description = chunk[start:end].strip()

        description = self._clean_text(description)

        return description[:500]

    def _extract_entities(self, chunk: str) -> list[str]:
        """从内容中提取实体"""
        entities = []

        # 识别人名 (简单模式)
        person_pattern = r'[\u4e00-\u9fff]{2,4}(?:先生|女士|博士|经理|经理|开发|设计师|工程师|测试|经理|老师|同学|同事|领导|团队成员|负责人|PM|CTO|CEO|创始人|开发者|用户|客户|管理员|编辑|作者|译者|审校|审核|评审|指导|顾问|教练|导师|讲师|演讲者|主持|主持人|嘉宾|参与者|参与|签约|合作|加盟|招聘|面试|候选人)?'
        for match in re.finditer(person_pattern, chunk):
            entity = match.group(0).strip()
            if entity and len(entity) > 2:
                entities.append(entity)

        # 识别组织/产品名称
        org_pattern = r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[\u4e00-\u9fff]{2,8}(?:公司|团队|组织|项目|系统|平台|工具|软件|应用|服务|API|接口|数据库|框架|库|包|模块|插件|组件|服务|功能|特性|版本|分支|仓库|提交|PR| Issue|任务|工单|缺陷| bug|错误|异常|事件|日志|记录|文档|手册|指南|教程|课程|培训|研讨会|会议|讨论|论坛|群组|频道|聊天|消息|通知|提醒|日程|计划|日历|时间|日期|期限|截止| deadline|里程碑|阶段|周期|迭代| sprint|冲刺|回顾|总结|报告|分析|研究|调查|问卷|数据|统计|图表|可视化|仪表盘| dashboard|指标| metric|KPI|目标|OKR|绩效|考核|评估|评审| review|代码|提交| branch|合并| merge|冲突| conflict|解决| resolve|测试|测试用例|用例| case|自动化| CI| CD| pipeline|部署| deployment|发布| release|版本| version| tag|标签| issue|工单|缺陷| bug|错误|异常|事件|日志|记录|文档|手册|指南|教程|课程|培训|研讨会|会议|讨论|论坛|群组|频道|聊天|消息|通知|提醒|日程|计划|日历|时间|日期|期限|截止| deadline|里程碑|阶段|周期|迭代| sprint|冲刺|回顾|总结|报告|分析|研究|调查|问卷|数据|统计|图表|可视化|仪表盘| dashboard|指标| metric|KPI|目标|OKR|绩效|考核|评估|评审| review|代码|提交| branch|合并| merge|冲突| conflict|解决| resolve)'
        for match in re.finditer(org_pattern, chunk):
            entity = match.group(0).strip()
            if entity and len(entity) > 2:
                entities.append(entity)

        # 去重
        unique_entities = []
        seen = set()
        for entity in entities:
            if entity.lower() not in seen:
                unique_entities.append(entity)
                seen.add(entity.lower())

        return unique_entities

    def _extract_outcome(self, chunk: str, event_type: str) -> str:
        """提取事件结果"""
        if event_type == 'outcome':
            return "已完成"
        elif event_type == 'error':
            return "已记录"
        elif event_type == 'decision':
            return "已决策"
        elif event_type == 'milestone':
            return "已达成"
        elif event_type == 'discovery':
            return "已发现"
        elif event_type == 'change':
            return "已变更"
        else:
            return ""

    def _estimate_task_confidence(self, task_title: str, chunk: str) -> float:
        """估计任务提取置信度"""
        confidence = 0.5  # 基础置信度

        # 标题越长，置信度越高 (通常更具体)
        confidence += min(0.3, len(task_title) / 100)

        # 在上下文中出现频率
        count = chunk.count(task_title)
        confidence += min(0.2, count * 0.05)

        # 是否有明确的任务标记
        if re.search(r'(?:任务|task|TODO|待办)', chunk, re.IGNORECASE):
            confidence += 0.2

        return min(1.0, confidence)

    def _estimate_event_confidence(self, event_title: str, chunk: str,
                                   event_type: str) -> float:
        """估计事件提取置信度"""
        confidence = 0.5  # 基础置信度

        confidence += min(0.3, len(event_title) / 100)

        count = chunk.count(event_title)
        confidence += min(0.2, count * 0.05)

        # 不同事件类型有不同的基础权重
        type_weight = {
            'decision': 0.1,  # 决策通常明确
            'outcome': 0.1,   # 结果通常明确
            'error': 0.05,    # 错误可能更模糊
            'milestone': 0.1,
            'discovery': 0.05,
            'change': 0.05,
            'other': 0.0,
        }
        confidence += type_weight.get(event_type, 0.0)

        return min(1.0, confidence)

    def _estimate_relation_weight(self, source: str, target: str,
                                  chunk: str) -> float:
        """估计关系权重"""
        weight = 0.5  # 基础权重

        # 来源和目标越接近，权重越高
        source_idx = chunk.find(source)
        target_idx = chunk.find(target)

        if source_idx != -1 and target_idx != -1:
            distance = abs(target_idx - source_idx)
            if distance < 100:
                weight += 0.3
            elif distance < 500:
                weight += 0.1

        # 在上下文中共同出现次数
        common_count = min(chunk.count(source), chunk.count(target))
        weight += min(0.2, common_count * 0.05)

        return min(1.0, weight)

    def _estimate_relation_confidence(self, source: str, target: str,
                                      chunk: str) -> float:
        """估计关系置信度"""
        confidence = 0.5  # 基础置信度

        # 关系模式匹配越明确，置信度越高
        if re.search(r'(?:依赖| depends|依赖于)', chunk, re.IGNORECASE):
            confidence += 0.2
        if re.search(r'(?:导致|cause|导致了|造成)', chunk, re.IGNORECASE):
            confidence += 0.2
        if re.search(r'(?:触发| triggers|引发|引起)', chunk, re.IGNORECASE):
            confidence += 0.15

        return min(1.0, confidence)

    def _find_node_id(self, entity_text: str,
                     tasks: list[TaskNode],
                     events: list[EventNode]) -> str | None:
        """尝试在已提取节点中查找匹配的实体"""
        # 检查任务节点
        for task in tasks:
            if entity_text in task.title or task.title in entity_text:
                return task.task_id

        # 检查事件节点
        for event in events:
            if entity_text in event.title or event.title in entity_text:
                return event.event_id

        return None

    def _deduplicate(self, result: dict) -> dict:
        """去重"""
        # 按任务标题去重
        seen_tasks = {}
        unique_tasks = []
        for task in result['tasks']:
            key = task.title.lower()
            if key not in seen_tasks:
                seen_tasks[key] = task
                unique_tasks.append(task)
            else:
                # 合并描述
                existing = seen_tasks[key]
                new_desc = task.description
                if new_desc and new_desc not in existing.description:
                    existing.description = existing.description + " " + new_desc

        # 按事件标题去重
        seen_events = {}
        unique_events = []
        for event in result['events']:
            key = event.title.lower()
            if key not in seen_events:
                seen_events[key] = event
                unique_events.append(event)

        # 按关系键去重 (source, target, type)
        seen_relations = {}
        unique_relations = []
        for rel in result['relations']:
            key = (rel.source_node_id, rel.target_node_id, rel.relation_type)
            if key not in seen_relations:
                seen_relations[key] = rel
                unique_relations.append(rel)
            else:
                # 合并权重 (取平均)
                existing = seen_relations[key]
                existing.weight = (existing.weight + rel.weight) / 2

        return {
            'tasks': unique_tasks,
            'events': unique_events,
            'relations': unique_relations,
            'extraction_meta': result['extraction_meta'],
        }

    def _apply_confidence_threshold(self, result: dict) -> dict:
        """应用置信度阈值，过滤低置信度节点"""
        threshold = self.min_confidence

        result['tasks'] = [t for t in result['tasks'] if t.confidence >= threshold]
        result['events'] = [e for e in result['events'] if e.confidence >= threshold]
        result['relations'] = [r for r in result['relations'] if r.confidence >= threshold]

        return result


# 便捷函数
def extract_graph(content: str, source_pointer: str = "",
                 metadata: dict | None = None,
                 config: dict | None = None) -> dict[str, list]:
    """提取图谱的便捷函数"""
    extractor = GraphExtractor(config=config)
    return extractor.extract_from_content(content, source_pointer, metadata)
