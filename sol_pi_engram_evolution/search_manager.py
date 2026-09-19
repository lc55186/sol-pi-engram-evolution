#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索引擎管理器 — 多引擎故障转移 + 负载均衡
避免单点故障导致搜索服务不可用

支持引擎：
- nous (meituan/longcat-2.0:free) ← 当前主力
- bing (需 API key)
- google (需 API key)
- serpapi (需 API key)
- meilisearch_local (本地引擎，需 Docker)
- typesense_local (本地引擎，需 Docker)
"""
import os
import time
import json
import random
import hashlib
import logging
import asyncio
import threading
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger("search_manager")


@dataclass
class EngineStatus:
    """引擎状态"""
    name: str
    is_healthy: bool = True
    last_check: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    avg_latency_ms: float = 0.0
    cooldown_until: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def is_available(self) -> bool:
        if self.cooldown_until and datetime.now() < self.cooldown_until:
            return False
        # 冷却结束后自动恢复
        if self.cooldown_until and datetime.now() >= self.cooldown_until:
            self.is_healthy = True
            self.consecutive_failures = 0
            self.cooldown_until = None
        return self.is_healthy


@dataclass
class SearchEngine:
    """搜索引擎定义"""
    name: str
    priority: int  # 数字越小优先级越高
    enabled: bool = True
    weight: int = 1  # 负载均衡权重
    max_failures: int = 3  # 连续失败多少次后进入冷却
    cooldown_seconds: int = 60  # 冷却时间
    timeout_seconds: int = 30
    config: Dict[str, Any] = field(default_factory=dict)
    status: EngineStatus = field(default_factory=lambda: EngineStatus(""))
    
    def __post_init__(self):
        if not self.status.name:
            self.status = EngineStatus(name=self.name)


class SearchResult:
    """搜索结果"""
    def __init__(self, engine: str, query: str, results: List[Dict],
                 latency_ms: float, is_cached: bool = False):
        self.engine = engine
        self.query = query
        self.results = results
        self.latency_ms = latency_ms
        self.is_cached = is_cached
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "engine": self.engine,
            "query": self.query,
            "result_count": len(self.results),
            "latency_ms": round(self.latency_ms, 2),
            "is_cached": self.is_cached,
            "timestamp": self.timestamp.isoformat(),
        }


class SearchEngineManager:
    """
    搜索引擎管理器
    
    功能：
    1. 多引擎注册与管理
    2. 自动故障转移（优先级 + 健康检查）
    3. 加权负载均衡
    4. 结果缓存
    5. 健康状态监控
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "./search_engines.yaml"
        self.engines: Dict[str, SearchEngine] = {}
        self.cache: Dict[str, SearchResult] = {}
        self.cache_ttl_seconds: int = 300  # 5分钟缓存
        self._cache_lock = threading.Lock()
        self._status_lock = threading.Lock()
        
        # 注册引擎后端
        self._backends: Dict[str, Callable] = {}
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_path):
            logger.info(f"Config not found: {self.config_path}, using defaults")
            self._init_default_engines()
            return
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f) if self.config_path.endswith(".json") else yaml.safe_load(f)
            
            for engine_config in config.get("engines", []):
                engine = SearchEngine(
                    name=engine_config["name"],
                    priority=engine_config.get("priority", 99),
                    enabled=engine_config.get("enabled", True),
                    weight=engine_config.get("weight", 1),
                    max_failures=engine_config.get("max_failures", 3),
                    cooldown_seconds=engine_config.get("cooldown_seconds", 60),
                    timeout_seconds=engine_config.get("timeout_seconds", 30),
                    config=engine_config.get("config", {}),
                )
                self.engines[engine.name] = engine
                logger.info(f"Loaded engine: {engine.name} (priority={engine.priority})")
            
            self.cache_ttl_seconds = config.get("cache_ttl_seconds", 300)
            
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._init_default_engines()
    
    def _init_default_engines(self):
        """初始化默认引擎配置"""
        self.engines = {
            "nous_meituan": SearchEngine(
                name="nous_meituan",
                priority=1,
                enabled=True,
                weight=5,
                config={"model": "meituan/longcat-2.0:free", "provider": "nous"}
            ),
            "bing_api": SearchEngine(
                name="bing_api",
                priority=2,
                enabled=False,
                weight=3,
                config={"api_key": "", "endpoint": "https://api.bing.microsoft.com/v7.0/search"}
            ),
            "google_api": SearchEngine(
                name="google_api",
                priority=3,
                enabled=False,
                weight=3,
                config={"api_key": "", "cx": "", "endpoint": "https://www.googleapis.com/customsearch/v1"}
            ),
            "serpapi": SearchEngine(
                name="serpapi",
                priority=4,
                enabled=False,
                weight=2,
                config={"api_key": "", "endpoint": "https://serpapi.com/search"}
            ),
            "meilisearch_local": SearchEngine(
                name="meilisearch_local",
                priority=10,
                enabled=False,
                weight=1,
                config={"url": "http://localhost:7700", "api_key": "", "index": "documents"}
            ),
            "typesense_local": SearchEngine(
                name="typesense_local",
                priority=11,
                enabled=False,
                weight=1,
                config={"url": "http://localhost:8108", "api_key": "", "collection": "documents"}
            ),
        }
    
    def register_backend(self, name: str, backend: Callable):
        """
        注册搜索引擎后端
        
        backend 签名: (query: str, limit: int, config: Dict) -> List[Dict]
        """
        self._backends[name] = backend
        logger.info(f"Registered backend: {name}")
    
    def _get_cache_key(self, query: str, limit: int, engine: str = None) -> str:
        """生成缓存 key"""
        content = f"{query}:{limit}:{engine or 'any'}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_from_cache(self, cache_key: str) -> Optional[SearchResult]:
        """从缓存获取结果"""
        with self._cache_lock:
            result = self.cache.get(cache_key)
            if result:
                age = (datetime.now() - result.timestamp).total_seconds()
                if age > self.cache_ttl_seconds:
                    del self.cache[cache_key]
                    return None
                result.is_cached = True
                return result
        return None
    
    def _save_to_cache(self, cache_key: str, result: SearchResult):
        """保存结果到缓存"""
        with self._cache_lock:
            self.cache[cache_key] = result
    
    def get_available_engines(self) -> List[SearchEngine]:
        """获取所有可用引擎（按优先级排序）"""
        available = []
        for engine in self.engines.values():
            if engine.enabled and engine.status.is_available:
                available.append(engine)
        
        available.sort(key=lambda e: (e.priority, -e.weight))
        return available
    
    def select_engine(self, strategy: str = "priority") -> Optional[SearchEngine]:
        """
        选择搜索引擎
        
        strategy:
        - priority: 按优先级选择（默认）
        - weighted: 加权随机
        - fastest: 选择平均延迟最低
        - all: 返回所有可用引擎（用于并行搜索）
        """
        available = self.get_available_engines()
        if not available:
            return None
        
        if strategy == "priority":
            return available[0]
        
        elif strategy == "weighted":
            weights = [e.weight for e in available]
            return random.choices(available, weights=weights, k=1)[0]
        
        elif strategy == "fastest":
            return min(available, key=lambda e: e.status.avg_latency_ms)
        
        return available[0]
    
    def search(self, query: str, limit: int = 5, strategy: str = "priority",
               use_cache: bool = True, engine_name: str = None) -> Optional[SearchResult]:
        """
        执行搜索
        
        自动选择引擎，支持故障转移
        """
        cache_key = self._get_cache_key(query, limit, engine_name)
        
        # 1. 检查缓存
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached:
                logger.debug(f"Cache hit for query: {query[:50]}...")
                return cached
        
        # 2. 选择引擎
        if engine_name:
            engine = self.engines.get(engine_name)
            if not engine or not engine.status.is_available:
                logger.warning(f"Engine {engine_name} unavailable, fallback...")
                engine = self.select_engine(strategy)
        else:
            engine = self.select_engine(strategy)
        
        if not engine:
            logger.error("No search engine available!")
            return None
        
        # 3. 执行搜索
        backend = self._backends.get(engine.name)
        if not backend:
            logger.error(f"No backend registered for engine: {engine.name}")
            return None
        
        start_time = time.time()
        try:
            results = backend(query, limit, engine.config)
            latency_ms = (time.time() - start_time) * 1000
            
            # 更新引擎状态
            self._record_success(engine, latency_ms)
            
            search_result = SearchResult(
                engine=engine.name,
                query=query,
                results=results,
                latency_ms=latency_ms,
            )
            
            # 保存缓存
            if use_cache:
                self._save_to_cache(cache_key, search_result)
            
            logger.info(f"Search via {engine.name}: {len(results)} results in {latency_ms:.1f}ms")
            return search_result
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_failure(engine, str(e))
            logger.error(f"Search failed on {engine.name}: {e}")
            
            # 故障转移：尝试下一个引擎
            return self._failover_search(query, limit, strategy, engine.name, use_cache)
    
    def _failover_search(self, query: str, limit: int, strategy: str,
                         failed_engine: str, use_cache: bool) -> Optional[SearchResult]:
        """故障转移搜索"""
        available = self.get_available_engines()
        available = [e for e in available if e.name != failed_engine]
        
        if not available:
            logger.error("Failover failed: no other engine available!")
            return None
        
        # 使用下一个优先级最高的引擎
        next_engine = available[0]
        logger.info(f"Failover: {failed_engine} -> {next_engine.name}")
        
        backend = self._backends.get(next_engine.name)
        if not backend:
            logger.error(f"No backend for failover engine: {next_engine.name}")
            return None
        
        start_time = time.time()
        try:
            results = backend(query, limit, next_engine.config)
            latency_ms = (time.time() - start_time) * 1000
            self._record_success(next_engine, latency_ms)
            
            return SearchResult(
                engine=next_engine.name,
                query=query,
                results=results,
                latency_ms=latency_ms,
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._record_failure(next_engine, str(e))
            logger.error(f"Failover also failed on {next_engine.name}: {e}")
            return None
    
    def parallel_search(self, query: str, limit: int = 5,
                        engines: List[str] = None) -> List[SearchResult]:
        """
        并行搜索多个引擎
        
        用于对比结果质量或获取更全面的信息
        """
        if not engines:
            available = self.get_available_engines()
            engines = [e.name for e in available[:3]]  # 最多3个引擎并行
        
        results = []
        threads = []
        
        def search_worker(engine_name: str):
            result = self.search(query, limit, engine_name=engine_name, use_cache=False)
            if result:
                results.append(result)
        
        for engine_name in engines:
            thread = threading.Thread(target=search_worker, args=(engine_name,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join(timeout=30)
        
        return results
    
    def _record_success(self, engine: SearchEngine, latency_ms: float):
        """记录成功请求"""
        with self._status_lock:
            status = engine.status
            status.last_check = datetime.now()
            status.consecutive_failures = 0
            status.total_requests += 1
            status.successful_requests += 1
            status.is_healthy = True
            
            # 更新平均延迟（指数移动平均）
            alpha = 0.3
            status.avg_latency_ms = alpha * latency_ms + (1 - alpha) * status.avg_latency_ms
    
    def _record_failure(self, engine: SearchEngine, error: str):
        """记录失败请求"""
        with self._status_lock:
            status = engine.status
            status.last_check = datetime.now()
            status.consecutive_failures += 1
            status.total_requests += 1
            
            if status.consecutive_failures >= engine.max_failures:
                status.is_healthy = False
                status.cooldown_until = datetime.now() + timedelta(seconds=engine.cooldown_seconds)
                logger.warning(
                    f"Engine {engine.name} entered cooldown for {engine.cooldown_seconds}s "
                    f"({status.consecutive_failures} failures)"
                )
    
    def health_check(self) -> Dict[str, EngineStatus]:
        """执行健康检查"""
        statuses = {}
        for name, engine in self.engines.items():
            if not engine.enabled:
                continue
            
            # 触发 is_available 属性以自动恢复冷却完成的引擎
            _ = engine.status.is_available
            
            statuses[name] = engine.status
        
        return statuses
    
    def get_status_report(self) -> Dict:
        """获取状态报告"""
        health = self.health_check()
        total_requests = sum(s.total_requests for s in health.values())
        healthy_count = sum(1 for s in health.values() if s.is_healthy)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_engines": len(self.engines),
            "healthy_engines": healthy_count,
            "total_requests": total_requests,
            "cache_size": len(self.cache),
            "cache_ttl": self.cache_ttl_seconds,
            "engines": {
                name: {
                    "healthy": status.is_healthy,
                    "available": status.is_available,
                    "success_rate": round(status.success_rate, 3),
                    "avg_latency_ms": round(status.avg_latency_ms, 2),
                    "total_requests": status.total_requests,
                    "consecutive_failures": status.consecutive_failures,
                    "cooldown_until": status.cooldown_until.isoformat() if status.cooldown_until else None,
                }
                for name, status in health.items()
            }
        }


# ============================================
# 搜索引擎后端实现
# ============================================

def nous_meituan_backend(query: str, limit: int, config: Dict) -> List[Dict]:
    """
    Nous/Meituan 搜索后端
    实际调用 Hermes web_search 或 API
    """
    # 这里模拟调用，实际应集成到 Hermes 工具或调用 API
    import urllib.request
    import urllib.parse
    import json
    
    # 示例：调用某个搜索 API
    # 实际实现需要根据 nous 提供的 API 文档
    return [
        {
            "url": f"https://example.com/search?q={urllib.parse.quote(query)}",
            "title": f"搜索结果 via Nous: {query[:30]}...",
            "description": "Nous Meituan Longcat 2.0 搜索后端（需配置实际 API）",
            "source": "nous_meituan",
        }
    ] * min(limit, 3)


def bing_backend(query: str, limit: int, config: Dict) -> List[Dict]:
    """Bing Search API 后端"""
    api_key = config.get("api_key", "")
    if not api_key:
        raise ValueError("Bing API key not configured")
    
    import urllib.request
    import urllib.parse
    import json
    
    endpoint = config.get("endpoint", "https://api.bing.microsoft.com/v7.0/search")
    url = f"{endpoint}?q={urllib.parse.quote(query)}&count={limit}"
    
    req = urllib.request.Request(url)
    req.add_header("Ocp-Apim-Subscription-Key", api_key)
    
    with urllib.request.urlopen(req, timeout=config.get("timeout", 30)) as response:
        data = json.loads(response.read().decode())
    
    results = []
    if "webPages" in data and "value" in data["webPages"]:
        for item in data["webPages"]["value"][:limit]:
            results.append({
                "url": item.get("url", ""),
                "title": item.get("name", ""),
                "description": item.get("snippet", ""),
                "source": "bing_api",
            })
    
    return results


def google_backend(query: str, limit: int, config: Dict) -> List[Dict]:
    """Google Custom Search API 后端"""
    api_key = config.get("api_key", "")
    cx = config.get("cx", "")
    if not api_key or not cx:
        raise ValueError("Google API key or CX not configured")
    
    import urllib.request
    import urllib.parse
    import json
    
    endpoint = config.get("endpoint", "https://www.googleapis.com/customsearch/v1")
    url = f"{endpoint}?key={api_key}&cx={cx}&q={urllib.parse.quote(query)}&num={limit}"
    
    with urllib.request.urlopen(url, timeout=config.get("timeout", 30)) as response:
        data = json.loads(response.read().decode())
    
    results = []
    if "items" in data:
        for item in data["items"][:limit]:
            results.append({
                "url": item.get("link", ""),
                "title": item.get("title", ""),
                "description": item.get("snippet", ""),
                "source": "google_api",
            })
    
    return results


def serpapi_backend(query: str, limit: int, config: Dict) -> List[Dict]:
    """SerpAPI 后端（支持 Google/Bing/Yahoo 等）"""
    api_key = config.get("api_key", "")
    if not api_key:
        raise ValueError("SerpAPI key not configured")
    
    import urllib.request
    import urllib.parse
    import json
    
    endpoint = config.get("endpoint", "https://serpapi.com/search")
    url = f"{endpoint}?api_key={api_key}&q={urllib.parse.quote(query)}&num={limit}"
    
    with urllib.request.urlopen(url, timeout=config.get("timeout", 30)) as response:
        data = json.loads(response.read().decode())
    
    results = []
    if "organic_results" in data:
        for item in data["organic_results"][:limit]:
            results.append({
                "url": item.get("link", ""),
                "title": item.get("title", ""),
                "description": item.get("snippet", ""),
                "source": "serpapi",
            })
    
    return results


def meilisearch_backend(query: str, limit: int, config: Dict) -> List[Dict]:
    """Meilisearch 本地引擎后端"""
    url = config.get("url", "http://localhost:7700")
    api_key = config.get("api_key", "")
    index = config.get("index", "documents")
    
    import urllib.request
    import json
    
    req = urllib.request.Request(
        f"{url}/indexes/{index}/search?q={urllib.parse.quote(query)}&limit={limit}",
        headers={"Authorization": f"Bearer {api_key}"} if api_key else {}
    )
    
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
    
    results = []
    for hit in data.get("hits", [])[:limit]:
        results.append({
            "url": hit.get("url", "#"),
            "title": hit.get("title", ""),
            "description": hit.get("description", hit.get("content", ""))[:200],
            "source": "meilisearch_local",
        })
    
    return results


def typesense_backend(query: str, limit: int, config: Dict) -> List[Dict]:
    """Typesense 本地引擎后端"""
    url = config.get("url", "http://localhost:8108")
    api_key = config.get("api_key", "")
    collection = config.get("collection", "documents")
    
    import urllib.request
    import json
    
    req = urllib.request.Request(
        f"{url}/collections/{collection}/documents/search?q={urllib.parse.quote(query)}&per_page={limit}",
        headers={"X-TYPESENSE-API-KEY": api_key} if api_key else {}
    )
    
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode())
    
    results = []
    for hit in data.get("hits", [])[:limit]:
        doc = hit.get("document", {})
        results.append({
            "url": doc.get("url", "#"),
            "title": doc.get("title", ""),
            "description": doc.get("description", doc.get("content", ""))[:200],
            "source": "typesense_local",
        })
    
    return results


# ============================================
# 全局实例
# ============================================

_manager: Optional[SearchEngineManager] = None


def get_search_manager(config_path: str = None) -> SearchEngineManager:
    """获取搜索引擎管理器全局实例"""
    global _manager
    if _manager is None:
        _manager = SearchEngineManager(config_path)
        
        # 注册默认后端
        _manager.register_backend("nous_meituan", nous_meituan_backend)
        _manager.register_backend("bing_api", bing_backend)
        _manager.register_backend("google_api", google_backend)
        _manager.register_backend("serpapi", serpapi_backend)
        _manager.register_backend("meilisearch_local", meilisearch_backend)
        _manager.register_backend("typesense_local", typesense_backend)
    
    return _manager


if __name__ == "__main__":
    # 示例用法
    manager = get_search_manager()
    
    # 查看状态
    report = manager.get_status_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))
