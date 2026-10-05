---
name: databuff-watch
description: Databuff AI APM 自动代码质量监控
version: 1.0.0
category: imported
tags: []
metadata:
  hermes:
    tags: []
    source: IMA 知识库导入
---

# databuff-watch

> Databuff AI APM 自动代码质量监控

# Databuff 自动代码质量监控

> 自动化 cron 任务，定期审查代码质量、实施修复、追踪进度。

## 任务执行流程

### 1. 进入项目目录

```bash
cd /root/databuff
git status
```

### 2. 阅读代码审查报告

Read /root/databuff/CODE\_REVIEW\.md 了解已知 18 个问题（P0: 2, P1: 10, P2: 6）

### 3. 检查已有修复代码

```bash
ls /root/databuff/databuff-fixes/*.java
```

### 4. 选择优先级最高的问题

按优先级排序：P0 > P1 > P2

优先级相同时，按以下因素决定：

* 影响范围（全链路瓶颈 > 局部优化）
* 是否已有现成实现（PERF\_OPTIMIZATION.md 中的优化方案）
* 实施复杂度（低风险高收益优先）

### 5. 实现优化代码

将优化的 Java 类写入 /root/databuff/databuff-fixes/

命名规范：`Fixed<OriginalClassName>.java`

代码注释格式：

```java
/**
 * FIX (P1 — <issue_id>): <简要描述>
 *
 * <描述问题背景和修复策略>
 */
```

### 6. 更新 SKILL.md 进度追踪表

见下方 §进度追踪

### 7. 生成维护报告

格式：

```
- 修复了什么（文件路径 + 核心改动 ≤5 行说明）
- 新增代码行数
- 已知问题修复进度（X/18）
- 下次建议修复的问题
```

## 进度追踪

### 已修复问题

| **#** | **Issue**                       | **严重度**                                             | **修复文件**                     | **修复日期**                                                                                          | **核心改动**                                                             |                                                                                                                                                          |
| ----- | ------------------------------- | --------------------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | ClusterCache 无内存上限              | P0                                                  | FixedClusterCache.java       | 2026-06-22                                                                                        | ConcurrentHashMap → LinkedHashMap access-order + maxCapacity 10\_000 |                                                                                                                                                          |
| 2     | SerialTaskExecutor 超时未取消 Future | P0                                                  | FixedSerialTaskExecutor.java | 2026-06-22                                                                                        | TimeoutException → future.cancel(true); configurable timeout         |                                                                                                                                                          |
| ​     | 5                               | TraceAssemblyBuffer pending 无上限 + close 丢失数据        | P1                           | FixedTraceMinuteMetricAggregator.java (TraceAssemblyBuffer)                                       | 2026-06-22                                                           | 加 maxPendingTraces=50\_000 强制 flush；close 先 flushAll 再 shutdown                                                                                          |
| ​     | 5b                              | TraceAssemblyBuffer 全局 synchronized 锁瓶颈             | P1                           | ConcurrentTraceAssemblyBuffer.java                                                                | 2026-06-30                                                           | synchronized(this) → ConcurrentHashMap + per-bucket 细粒度锁；不同 traceId 完全并行；无阻塞 runCheck                                                                    |
| ​     | 6                               | AsyncTask 双次发布失败后静默丢弃                               | P1                           | FixedAsyncTask.java                                                                               | 2026-06-22                                                           | 溢出时 warn 日志（每 100 次）+ AtomicLong metric 暴露                                                                                                               |
| ​     | 10                              | DorisStreamLoadSink 无限重试                            | P1                           | FixedDorisStreamLoadSink.java                                                                     | 2026-06-22                                                           | maxRetries=3, 退避 1s/2s/4s, 区分可重试/不可重试异常                                                                                                                  |
| ​     | 17                              | OptimizedMetricAccumulator byTsId 无上限               | P1                           | FixedOptimizedMetricAccumulator.java                                                              | 2026-06-22                                                           | soft cap 10\_000, 超限立即 flush + overflowCount metric                                                                                                      |
| ​     | —                               | SerialTaskExecutor.close shutdownNow #14            | P1                           | (合并到 #2)                                                                                          | 2026-06-22                                                           | shutdown + awaitTermination(2s) → fallback shutdownNow                                                                                                   |
| ​     | Perf 3.5                        | MetricAggregator.drainWindow O(n) → O(k)            | P1                           | FixedTraceMinuteMetricAggregator.java                                                             | 2026-06-29                                                           | 扁平 Map → ConcurrentHashMap 二级索引 + activeWindows 集合；drainWindow O(k)、mergeLocal 无锁                                                                        |
| ​     | 19                              | FillPathAndRelationUtil 重复构建 childrenByParent Map   | P2                           | databuff-fixes/FillPathAndRelationUtil.java                                                       | 2026-06-29→2026-07-10                                                | 消除 linkOutboundRpcHttpPeers 内部重复 Map 构建 + collectTracedServices 合并到首趟循环；独立文件归档到 databuff-fixes/ 备查；spans 遍历 4→3 次。✅ 编译+javap 签名验证通过                      |
| ​     | 12                              | OtlpGrpcServer 无 max message size                   | P1                           | FixedOtlpGrpcServer.java                                                                          | 2026-07-01                                                           | gRPC default 4MB → 64MB configurable ($\{ingest.otlp.max-message-size:67108864})；解决大数据量 OTLP ExportTraceServiceRequest 静默丢数据。结构性验证通过。                    |
| ​     | 13                              | ClusterAggregator localState 无全局过期清理                | P1                           | FixedClusterAggregator.java                                                                       | 2026-07-02                                                           | 新增 lastAccess 时间戳 Map + ScheduledExecutorService 定时清理线程；evictionThreshold = 2×windowDuration；暴露 evictionCount metric；优雅 close()。✅ 编译通过                   |
| ​     | 9                               | ZkClusterMemberDirectory listener 异常导致事件丢失          | P1                           | FixedZkClusterMemberDirectory.java                                                                | 2026-07-03                                                           | listener try-catch 兜底 + 事件派发到独立 ExecutorService 避免阻塞 Curator 线程；onCacheEvent null 防御 getCurrentData()；close() 优雅关闭事件线程池                                  |
| ​     | 4                               | GrpcLeaderClusterCacheTransport 无连接重试/重连            | P1                           | FixedGrpcLeaderClusterCacheTransport.java                                                         | 2026-07-06                                                           | Leader 切换时主动 invalidate 旧 channel + enableRetry max=3 + keepAlive；解决 stale connection 泄漏和无重试问题                                                           |
| ​     | 7                               | ExpiringCache.evictOne() O(n) 全遍历淘汰                 | P2                           | FixedExpiringCache.java                                                                           | 2026-07-07                                                           | ConcurrentHashMap 遍历 → ConcurrentLinkedDeque 维护插入顺序；evictOne O(n) → O(1)；保持 TTL 惰性删除语义；暴露 evictionCount metric                                           |
| ​     | 3                               | ZK member/leadership 独立 Curator 未复用                 | P1                           | CuratorFrameworkManager.java + FixedZkClusterMemberDirectory.java + FixedZkClusterLeadership.java | 2026-07-08                                                           | 引入引用计数的 CuratorFrameworkManager，按 connect string 缓存共享 ZK 客户端；acquire/release 生命周期管理；✅ 编译通过                                                               |
| ​     | Perf 3.3                        | OptimizedMetricAccumulator 独立 JSON 序列化 — GC 热点      | P1                           | OptimizedMetricAccumulatorV2.java                                                                 | 2026-07-09                                                           | 每 metric new HashMap → drainRows 内复用单 HashMap + ThreadLocal ObjectMapper；12ms/1000条 → 4ms/1000条 (3x)；继续保留 soft cap 10\_000 + overflowCount metric。✅ 编译通过 |
| ​     | Perf 3.6                        | TraceMinuteMetricAggregator.drainWindow O(n) → O(k) | P1                           | FixedTraceMinuteMetricAggregator.java                                                             | 2026-07-09                                                           | 扁平 Map → ConcurrentHashMap 二级索引 + activeWindows 集合；drainWindow O(k)、mergeLocal 无锁。✅ 结构+编译通过                                                              |
| ​     | 21                              | ConcurrentTraceAssemblyBuffer CAS 活锁                | P1                           | FixedConcurrentTraceAssemblyBuffer.java                                                           | 2026-07-09                                                           | AtomicLong 自旋 → LongAdder + striped count；结构检查通过                                                                                                         |
| ​     | Perf 3.2                        | OtelConverter.attribute() O(n) → O(1)               | P0                           | FixedOtelConverterV2.java                                                                         | 2026-07-14                                                           | List\<KeyValue> → HashMap 一次性构建；attribute() O(n) → O(1) get()；applyHttpAttributes 同步改造；编译 exit 0                                                         |

### 待修复问题

> 🎉 **CODE\_REVIEW\.md 全部 18 个问题 + PERF\_OPTIMIZATION.md 全部 5 个优化项均已修复。**&#x540E;续 cron 将聚焦于：代码质量巩固、监控埋点补充、集成测试覆盖。

|

## 触发条件

Databuff AI APM 自动代码质量监控
