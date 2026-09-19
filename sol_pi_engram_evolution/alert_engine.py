#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keyword Alert Engine - 关键词预警引擎
三级预警：P0高风险 / P1中风险 / P2低风险
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("alert_engine")


class AlertPriority(Enum):
    HIGH = "high"      # P0: 账期/红线/担保
    MEDIUM = "medium"  # P1: 商机/预算/决策链
    LOW = "low"        # P2: 情绪/态度


class AlertType(Enum):
    KEYWORD_ALERT = "keyword_alert"
    RISK = "risk"
    OPPORTUNITY = "opportunity"
    EMOTION = "emotion"


@dataclass
class AlertRule:
    """预警规则"""
    name: str
    pattern: str
    alert_type: AlertType
    priority: AlertPriority
    action: str  # vibrate_long / vibrate_double / vibrate_short / lockscreen
    message_template: str
    enabled: bool = True
    cooldown_seconds: int = 30  # 同一规则冷却时间


@dataclass
class AlertEvent:
    """预警事件"""
    rule_name: str
    alert_type: AlertType
    priority: AlertPriority
    content: str  # 实际触发文本
    action: str
    timestamp: float = 0.0
    confidence: float = 0.0
    delivered: bool = False


# 预定义规则库
DEFAULT_RULES = {
    "汽配贸易": [
        AlertRule("账期风险", r"账期.*?(\d+)\s*天", AlertType.RISK, AlertPriority.HIGH,
                  "vibrate_long", "⚠️ 账期预警：对方要求 {0} 天账期"),
        AlertRule("质量扣款", r"扣款|质量.*问题|退货", AlertType.RISK, AlertPriority.HIGH,
                  "vibrate_long", "⚠️ 质量风险：{0}"),
        AlertRule("价格陷阱", r"降价.*%\s*以上|低于成本", AlertType.RISK, AlertPriority.HIGH,
                  "vibrate_long", "⚠️ 价格风险：{0}"),
        AlertRule("商机信号", r"需求|询单|预算|采购计划", AlertType.OPPORTUNITY, AlertPriority.MEDIUM,
                  "vibrate_double", "💰 商机信号：{0}"),
        AlertRule("决策链", r"负责人|总经理|董事长|采购总监", AlertType.OPPORTUNITY, AlertPriority.MEDIUM,
                  "vibrate_double", "👤 决策链：{0}"),
        AlertRule("担保要求", r"担保|保证金|抵押", AlertType.RISK, AlertPriority.HIGH,
                  "vibrate_long", "⚠️ 担保要求：{0}"),
    ],
    "体育器材": [
        AlertRule("窜货风险", r"窜货|跨区域|低价.*销售", AlertType.RISK, AlertPriority.HIGH,
                  "vibrate_long", "⚠️ 窜货风险：{0}"),
        AlertRule("返点争议", r"返点|提成|返利", AlertType.RISK, AlertPriority.MEDIUM,
                  "vibrate_double", "💰 返点争议：{0}"),
        AlertRule("区域保护", r"区域.*保护|独家代理|排他", AlertType.RISK, AlertPriority.HIGH,
                  "vibrate_long", "⚠️ 区域保护：{0}"),
        AlertRule("订货量", r"(\d+)\s*件|(\d+)\s*箱", AlertType.OPPORTUNITY, AlertPriority.MEDIUM,
                  "vibrate_double", "📦 订货量：{0}"),
        AlertRule("排他条款", r"排他|独家|唯一代理", AlertType.RISK, AlertPriority.HIGH,
                  "vibrate_long", "⚠️ 排他条款：{0}"),
    ],
    "再生资源": [
        AlertRule("扣杂争议", r"扣杂|杂质|水分|含量", AlertType.RISK, AlertPriority.HIGH,
                  "vibrate_long", "⚠️ 扣杂预警：{0}"),
        AlertRule("现款条款", r"现款|现金.*结算|预付", AlertType.RISK, AlertPriority.MEDIUM,
                  "vibrate_double", "💰 现款条款：{0}"),
        AlertRule("价格红线", r"底线|最低.*价|不能再降", AlertType.RISK, AlertPriority.HIGH,
                  "vibrate_long", "⚠️ 价格红线：{0}"),
        AlertRule("货源信息", r"有货|货源|供应.*稳定", AlertType.OPPORTUNITY, AlertPriority.MEDIUM,
                  "vibrate_double", "📦 货源信息：{0}"),
        AlertRule("付款条件", r"月结|季结|赊销", AlertType.RISK, AlertPriority.HIGH,
                  "vibrate_long", "⚠️ 付款条件：{0}"),
    ],
}


class KeywordAlertEngine:
    """关键词预警引擎"""

    def __init__(self, scenario: str = "汽配贸易"):
        self.scenario = scenario
        self.rules: List[AlertRule] = []
        self._compile_rules()
        self._alert_history: Dict[str, float] = {}  # rule_name → last_alert_time

    def _compile_rules(self):
        """编译规则正则"""
        self.rules = []
        for rule in DEFAULT_RULES.get(self.scenario, []):
            if rule.enabled:
                self.rules.append(rule)

    def set_scenario(self, scenario: str):
        """切换行业场景"""
        self.scenario = scenario
        self._compile_rules()

    def add_rule(self, rule: AlertRule):
        """添加自定义规则"""
        self.rules.append(rule)

    def process_transcript(self, text: str) -> List[AlertEvent]:
        """处理转写文本，返回触发的预警"""
        import time
        current_time = time.time()
        alerts = []

        for rule in self.rules:
            # 检查冷却时间
            last_alert = self._alert_history.get(rule.name, 0)
            if current_time - last_alert < rule.cooldown_seconds:
                continue

            # 匹配规则
            match = re.search(rule.pattern, text, re.IGNORECASE)
            if match:
                # 构建预警内容
                content = rule.message_template.format(match.group(0))

                event = AlertEvent(
                    rule_name=rule.name,
                    alert_type=rule.alert_type,
                    priority=rule.priority,
                    content=content,
                    action=rule.action,
                    timestamp=current_time,
                    confidence=self._estimate_confidence(match, text)
                )
                alerts.append(event)
                self._alert_history[rule.name] = current_time

        return alerts

    def _estimate_confidence(self, match: re.Match, text: str) -> float:
        """估计预警置信度"""
        confidence = 0.7  # 基础置信度

        # 匹配长度越长，置信度越高
        match_len = match.end() - match.start()
        confidence += min(0.2, match_len / 50)

        # 上下文越长，置信度越高
        confidence += min(0.1, len(text) / 1000)

        return min(1.0, confidence)

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "scenario": self.scenario,
            "total_rules": len(self.rules),
            "high_priority": len([r for r in self.rules if r.priority == AlertPriority.HIGH]),
            "medium_priority": len([r for r in self.rules if r.priority == AlertPriority.MEDIUM]),
            "low_priority": len([r for r in self.rules if r.priority == AlertPriority.LOW]),
        }


# 便捷函数
def create_alert_engine(scenario: str = "汽配贸易") -> KeywordAlertEngine:
    """创建预警引擎"""
    return KeywordAlertEngine(scenario=scenario)


if __name__ == "__main__":
    # 测试
    engine = KeywordAlertEngine("汽配贸易")

    test_texts = [
        "对方要求60天账期，我们公司标准是30天",
        "这批货有质量问题，需要扣款5000元",
        "王总说他们有500万的采购预算",
        "需要提供银行担保才能签合同",
    ]

    for text in test_texts:
        alerts = engine.process_transcript(text)
        if alerts:
            for alert in alerts:
                print(f"[{alert.priority.value.upper()}] {alert.content}")
