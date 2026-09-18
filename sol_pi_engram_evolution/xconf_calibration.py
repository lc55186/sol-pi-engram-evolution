#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XConf 置信度校准模块
参考剑桥大学 XConf 方法：检索相似历史 episode 并展示历史成功率
无需 logit 访问或权重更新
"""
import os
import json
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger("xconf_calibration")


class XConfCalibrator:
    """XConf 置信度校准器"""
    
    def __init__(self, history_path: str = None):
        self.history_path = history_path or "./xconf_history.json"
        self.episodes: List[Dict] = []
        self._load_history()
    
    def _load_history(self):
        """加载历史 episode"""
        if os.path.exists(self.history_path):
            with open(self.history_path, "r", encoding="utf-8") as f:
                self.episodes = json.load(f)
    
    def _save_history(self):
        """保存历史 episode"""
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.episodes, f, ensure_ascii=False, indent=2)
    
    def record_episode(self, query: str, prediction: str, confidence: float,
                       actual_outcome: bool, metadata: Dict = None):
        """记录一个 episode"""
        episode = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "prediction": prediction,
            "confidence": confidence,
            "actual_outcome": actual_outcome,
            "metadata": metadata or {}
        }
        self.episodes.append(episode)
        
        # 只保留最近 1000 条
        if len(self.episodes) > 1000:
            self.episodes = self.episodes[-1000:]
        
        self._save_history()
    
    def calibrate_confidence(self, query: str, raw_confidence: float,
                              top_k: int = 10) -> Dict[str, Any]:
        """校准置信度"""
        if not self.episodes:
            return {
                "calibrated_confidence": raw_confidence,
                "confidence": raw_confidence,
                "method": "no_history",
                "similar_episodes": []
            }
        
        # 1. 检索相似 episode（基于查询重叠度）
        similar = self._find_similar_episodes(query, top_k)
        
        if not similar:
            return {
                "calibrated_confidence": raw_confidence,
                "confidence": raw_confidence,
                "method": "no_similar",
                "similar_episodes": []
            }
        
        # 2. 计算历史成功率
        success_rate = sum(1 for ep in similar if ep.get("actual_outcome")) / len(similar)
        
        # 3. 校准公式：beta * raw + (1-beta) * historical
        # beta 基于相似 episode 数量（越多越信任历史）
        beta = max(0.3, 1.0 - len(similar) / (top_k * 2))
        calibrated = beta * raw_confidence + (1 - beta) * success_rate
        
        return {
            "calibrated_confidence": round(calibrated, 4),
            "raw_confidence": raw_confidence,
            "historical_success_rate": round(success_rate, 4),
            "similar_count": len(similar),
            "method": "xconf_beta_blend",
            "similar_episodes": [
                {"query": ep["query"], "outcome": ep.get("actual_outcome")}
                for ep in similar[:3]
            ]
        }
    
    def _find_similar_episodes(self, query: str, top_k: int) -> List[Dict]:
        """查找相似 episode（基于关键词重叠）"""
        query_words = set(query.lower().split())
        
        scored = []
        for ep in self.episodes:
            ep_words = set(ep["query"].lower().split())
            if not ep_words:
                continue
            
            # Jaccard 相似度
            overlap = len(query_words & ep_words)
            union = len(query_words | ep_words)
            similarity = overlap / union if union > 0 else 0
            
            if similarity > 0.1:
                scored.append((similarity, ep))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [ep for _, ep in scored[:top_k]]
    
    def get_calibration_stats(self) -> Dict:
        """获取校准统计"""
        if not self.episodes:
            return {"total": 0}
        
        recent = self.episodes[-100:]
        return {
            "total_episodes": len(self.episodes),
            "recent_accuracy": sum(1 for ep in recent if ep.get("actual_outcome")) / len(recent),
            "avg_raw_confidence": sum(ep.get("confidence", 0.5) for ep in recent) / len(recent),
            "overconfidence_rate": sum(
                1 for ep in recent
                if ep.get("confidence", 0.5) > 0.7 and not ep.get("actual_outcome")
            ) / max(len(recent), 1)
        }


_calibrator: Optional[XConfCalibrator] = None

def get_xconf_calibrator() -> XConfCalibrator:
    global _calibrator
    if _calibrator is None:
        _calibrator = XConfCalibrator()
    return _calibrator
