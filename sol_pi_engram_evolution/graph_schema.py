"""
阶段 0：图谱 Schema 定义
定义所有节点类型、字段、约束
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TaskNode:
    """任务节点：表示一个任务/工作项"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    status: str = "not_started"  # not_started, in_progress, completed, failed, cancelled
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    priority: int = 3  # 1-5, 5=最高
    related_event_ids: list[str] = field(default_factory=list)
    related_task_ids: list[str] = field(default_factory=list)
    confidence: float = 1.0  # 提取置信度 0-1
    source_pointer: str = ""  # 指向原始归档/对话片段的指针
    access_count: int = 0
    last_accessed: datetime | None = None
    importance_score: float = 0.5
    decay_rate: float = 0.95  # 衰减因子

    VALID_STATUSES = {"not_started", "in_progress", "completed", "failed", "cancelled"}

    def __post_init__(self):
        if self.status not in self.VALID_STATUSES:
            raise ValueError(f"status must be in {self.VALID_STATUSES}")
        if not 1 <= self.priority <= 5:
            raise ValueError("priority must be 1-5")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be 0-1")
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError("importance_score must be 0-1")
        if not 0.0 <= self.decay_rate <= 1.0:
            raise ValueError("decay_rate must be 0-1")


@dataclass
class EventNode:
    """事件节点：表示发生的事件/决策/里程碑/错误等"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    event_type: str = "other"  # decision, outcome, milestone, error, discovery, change, other
    timestamp: datetime = field(default_factory=datetime.now)
    entities: list[str] = field(default_factory=list)  # 涉及实体
    outcome: str = ""  # 结果摘要
    related_task_ids: list[str] = field(default_factory=list)
    related_event_ids: list[str] = field(default_factory=list)
    confidence: float = 1.0
    source_pointer: str = ""
    access_count: int = 0
    last_accessed: datetime | None = None
    importance_score: float = 0.5
    decay_rate: float = 0.95

    VALID_EVENT_TYPES = {"decision", "outcome", "milestone", "error", "discovery", "change", "other"}

    def __post_init__(self):
        if self.event_type not in self.VALID_EVENT_TYPES:
            raise ValueError(f"event_type must be in {self.VALID_EVENT_TYPES}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be 0-1")
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError("importance_score must be 0-1")
        if not 0.0 <= self.decay_rate <= 1.0:
            raise ValueError("decay_rate must be 0-1")


@dataclass
class RelationNode:
    """关系节点：表示两个节点之间的关系"""
    relation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str = ""
    target_node_id: str = ""
    relation_type: str = "related_to"  # depends_on, causes, during, part_of, related_to, blocks, triggers, other
    weight: float = 0.5  # 关联强度 0-1
    description: str = ""
    confidence: float = 1.0
    source_pointer: str = ""
    access_count: int = 0
    last_accessed: datetime | None = None
    importance_score: float = 0.5
    decay_rate: float = 0.95

    VALID_RELATION_TYPES = {"depends_on", "causes", "during", "part_of", "related_to", "blocks", "triggers", "other"}

    def __post_init__(self):
        if self.relation_type not in self.VALID_RELATION_TYPES:
            raise ValueError(f"relation_type must be in {self.VALID_RELATION_TYPES}")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("weight must be 0-1")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be 0-1")
        if not 0.0 <= self.importance_score <= 1.0:
            raise ValueError("importance_score must be 0-1")
        if not 0.0 <= self.decay_rate <= 1.0:
            raise ValueError("decay_rate must be 0-1")


# 节点工厂
def create_task_node(title: str, description: str = "", status: str = "not_started",
                     priority: int = 3, confidence: float = 1.0, source_pointer: str = "") -> TaskNode:
    return TaskNode(title=title, description=description, status=status,
                    priority=priority, confidence=confidence, source_pointer=source_pointer)


def create_event_node(title: str, description: str = "", event_type: str = "other",
                      entities: list[str] = None, outcome: str = "",
                      confidence: float = 1.0, source_pointer: str = "") -> EventNode:
    return EventNode(title=title, description=description, event_type=event_type,
                     entities=entities or [], outcome=outcome,
                     confidence=confidence, source_pointer=source_pointer)


def create_relation_node(source_node_id: str, target_node_id: str, relation_type: str = "related_to",
                         weight: float = 0.5, description: str = "",
                         confidence: float = 1.0, source_pointer: str = "") -> RelationNode:
    return RelationNode(source_node_id=source_node_id, target_node_id=target_node_id,
                        relation_type=relation_type, weight=weight, description=description,
                        confidence=confidence, source_pointer=source_pointer)
