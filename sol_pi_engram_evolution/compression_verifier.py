"""
压缩质量验证模块
参考 Headroom 的大海捞针测试：验证压缩/归档后的检索准确率，
确保没有丢失关键信息。
"""

import random
from datetime import datetime
from typing import Any

from graph_store import GraphStore


class CompressionVerifier:
    """
    压缩质量验证器
    执行大海捞针测试，验证归档/压缩后的检索准确率
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.needle_count = self.config.get('needle_count', 5)
        self.haystack_size = self.config.get('haystack_size', 100)
        self.needle_length = self.config.get('needle_length', 50)
        self.pass_threshold = self.config.get('pass_threshold', 0.95)

    def generate_haystack(self, seed: str = None) -> str:
        """
        生成大海捞针测试的海量内容
        返回海量内容字符串
        """
        if seed:
            random.seed(seed)

        lines = []
        for i in range(self.haystack_size):
            line = f"日志条目 {i}: 这是第 {i} 条日志，用于测试压缩质量验证。"
            lines.append(line)

        return "\n".join(lines)

    def insert_needles(self, haystack: str,
                       needles: list[str]) -> str:
        """
        在海量内容中插入针（关键信息）
        返回插入针后的内容
        """
        lines = haystack.split('\n')
        # 随机选择位置插入针
        positions = random.sample(range(len(lines)), min(len(needles), len(lines)))

        for i, (pos, needle) in enumerate(zip(positions, needles)):
            lines.insert(pos, f"[关键信息 {i+1}] {needle}")

        return "\n".join(lines)

    def generate_needles(self, count: int = None) -> list[str]:
        """生成测试用针（关键信息）"""
        count = count or self.needle_count
        needles = []
        for i in range(count):
            needles.append(
                f"关键信息 {i+1}: 错误代码 500，服务宕机，"
                f"请立即处理。定位到模块 auth-service，"
                f"堆栈跟踪表明是数据库连接池耗尽。"
            )
        return needles

    def run_needle_test(self, archive_fn: callable,
                        retrieve_fn: callable,
                        needle_count: int = None) -> dict[str, Any]:
        """
        运行大海捞针测试

        Args:
            archive_fn: 归档函数，接收内容字符串，返回 handle
            retrieve_fn: 召回函数，接收 handle，返回内容字典
            needle_count: 针的数量

        Returns:
            测试结果字典
        """
        needle_count = needle_count or self.needle_count

        # 生成海量内容
        haystack = self.generate_haystack(seed="compression_verifier_test")

        # 生成针
        needles = self.generate_needles(needle_count)

        # 插入针到海量内容
        content_with_needles = self.insert_needles(haystack, needles)

        # 归档
        handle = archive_fn(content_with_needles)

        # 召回
        retrieved = retrieve_fn(handle)
        retrieved_content = retrieved.get('content', '')

        # 验证针是否都被召回
        found_needles = []
        missing_needles = []

        for needle in needles:
            if needle in retrieved_content:
                found_needles.append(needle)
            else:
                missing_needles.append(needle)

        # 计算准确率
        accuracy = len(found_needles) / len(needles) if needles else 1.0
        pass_test = accuracy >= self.pass_threshold

        return {
            'test_name': ' Needle-in-Haystack Test',
            'needle_count': len(needles),
            'found_count': len(found_needles),
            'missing_count': len(missing_needles),
            'accuracy': accuracy,
            'pass': pass_test,
            'threshold': self.pass_threshold,
            'found_needles': found_needles,
            'missing_needles': missing_needles,
            'timestamp': datetime.now().isoformat(),
        }

    def run_graph_needle_test(self, store: GraphStore,
                              node_count: int = 50,
                              needle_count: int = 5) -> dict[str, Any]:
        """
        运行图谱大海捞针测试
        向图谱插入大量节点，其中包含关键针节点，
        然后检索，验证针节点是否被检索到
        """
        # 插入大量普通节点
        for i in range(node_count):
            store.add_task_node(
                title=f"任务 {i}: 常规任务",
                description=f"这是第 {i} 个常规任务，用于填充图谱"
            )

        # 插入针节点（关键信息）
        needles = []
        for i in range(needle_count):
            needle_title = "[关键] 错误代码 500，服务宕机"
            needle = store.add_task_node(
                title=needle_title,
                description="定位到模块 auth-service，堆栈跟踪表明是数据库连接池耗尽。优先级最高。",
                priority=5,
                status="failed"
            )
            needles.append(needle['node_id'])

        # 检索（使用简单关键词）
        retriever = __import__('graph_retriever').GraphRetriever(store)
        results = retriever.retrieve("错误代码 500 服务宕机", top_k=20)

        # 检查针节点是否被检索到
        found_needles = []
        for node, score in results:
            if node['node_id'] in needles:
                found_needles.append(node['node_id'])

        accuracy = len(found_needles) / len(needles) if needles else 1.0

        return {
            'test_name': 'Graph Needle Test',
            'node_count': node_count,
            'needle_count': needle_count,
            'found_count': len(found_needles),
            'missing_count': len(needles) - len(found_needles),
            'accuracy': accuracy,
            'pass': accuracy >= self.pass_threshold,
            'threshold': self.pass_threshold,
            'found_needles': found_needles,
            'timestamp': datetime.now().isoformat(),
        }

    def run_retrieval_accuracy_test(self, store: GraphStore,
                                    query: str,
                                    expected_node_count: int,
                                    expected_min_score: float = 0.5) -> dict[str, Any]:
        """
        运行检索准确率测试
        验证检索结果是否符合预期
        """
        from graph_retriever import GraphRetriever
        retriever = GraphRetriever(store)
        results = retriever.retrieve(query, top_k=expected_node_count)

        return {
            'query': query,
            'retrieved_count': len(results),
            'expected_count': expected_node_count,
            'min_score_met': all(score >= expected_min_score for _, score in results),
            'scores': [score for _, score in results],
            'pass': len(results) >= expected_node_count and \
                    all(score >= expected_min_score for _, score in results),
        }


# 便捷函数
def verify_compression_quality(
    archive_fn: callable,
    retrieve_fn: callable,
    needle_count: int = 5,
    haystack_size: int = 100,
    pass_threshold: float = 0.95,
) -> dict[str, Any]:
    """验证压缩质量"""
    verifier = CompressionVerifier({
        'needle_count': needle_count,
        'haystack_size': haystack_size,
        'pass_threshold': pass_threshold,
    })
    return verifier.run_needle_test(archive_fn, retrieve_fn)


def verify_graph_retrieval(
    store: GraphStore,
    query: str,
    expected_node_count: int,
    pass_threshold: float = 0.5,
) -> dict[str, Any]:
    """验证图谱检索质量"""
    verifier = CompressionVerifier({'pass_threshold': pass_threshold})
    return verifier.run_retrieval_accuracy_test(store, query, expected_node_count)
