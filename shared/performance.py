"""
性能监控工具
提供装饰器和上下文管理器来监控代码执行时间
"""
import time
import logging
import functools
from typing import Callable, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    性能监控器

    功能:
    1. 记录函数执行时间
    2. 统计平均耗时
    3. 识别性能瓶颈
    4. 输出性能报告

    用法:
        monitor = PerformanceMonitor()

        # 装饰器方式
        @monitor.track
        def slow_function():
            time.sleep(1)

        # 上下文管理器方式
        with monitor.track_block("数据库查询"):
            db.query(...)

        # 获取报告
        report = monitor.get_report()
    """

    def __init__(self, enable: bool = True):
        """
        初始化性能监控器

        Args:
            enable: 是否启用监控（生产环境可以禁用）
        """
        self.enable = enable
        self._stats = {}  # {function_name: [duration1, duration2, ...]}

    def track(self, func: Callable = None, name: Optional[str] = None):
        """
        装饰器: 监控函数执行时间

        Args:
            func: 被装饰的函数
            name: 自定义名称（默认使用函数名）

        示例:
            @monitor.track
            def my_function():
                pass

            @monitor.track(name="自定义名称")
            def my_function():
                pass
        """
        if func is None:
            # 带参数的装饰器
            return functools.partial(self.track, name=name)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.enable:
                return func(*args, **kwargs)

            func_name = name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                self._record(func_name, duration)
                logger.debug(f"⏱️ [{func_name}] 耗时: {duration:.3f}s")

        return wrapper

    @contextmanager
    def track_block(self, block_name: str):
        """
        上下文管理器: 监控代码块执行时间

        Args:
            block_name: 代码块名称

        示例:
            with monitor.track_block("数据库查询"):
                db.query(...)
        """
        if not self.enable:
            yield
            return

        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self._record(block_name, duration)
            logger.debug(f"⏱️ [{block_name}] 耗时: {duration:.3f}s")

    def _record(self, name: str, duration: float):
        """记录执行时间"""
        if name not in self._stats:
            self._stats[name] = []
        self._stats[name].append(duration)

    def get_stats(self, name: str) -> dict:
        """
        获取指定函数的统计信息

        Args:
            name: 函数名称

        Returns:
            统计信息字典
        """
        if name not in self._stats:
            return {}

        durations = self._stats[name]
        return {
            "name": name,
            "call_count": len(durations),
            "total_time": sum(durations),
            "avg_time": sum(durations) / len(durations),
            "min_time": min(durations),
            "max_time": max(durations),
        }

    def get_report(self) -> list:
        """
        获取性能报告

        Returns:
            所有函数的统计信息列表（按平均耗时降序）
        """
        report = [self.get_stats(name) for name in self._stats]
        report.sort(key=lambda x: x.get("avg_time", 0), reverse=True)
        return report

    def print_report(self):
        """打印性能报告"""
        report = self.get_report()

        if not report:
            logger.info("📊 性能报告: 暂无数据")
            return

        logger.info("=" * 80)
        logger.info("📊 性能监控报告")
        logger.info("=" * 80)
        logger.info(
            f"{'函数名':<40} {'调用次数':>8} {'总耗时':>10} {'平均':>10} {'最小':>10} {'最大':>10}"
        )
        logger.info("-" * 80)

        for stats in report:
            logger.info(
                f"{stats['name']:<40} "
                f"{stats['call_count']:>8} "
                f"{stats['total_time']:>9.3f}s "
                f"{stats['avg_time']:>9.3f}s "
                f"{stats['min_time']:>9.3f}s "
                f"{stats['max_time']:>9.3f}s"
            )

        logger.info("=" * 80)

    def reset(self):
        """重置所有统计数据"""
        self._stats.clear()
        logger.info("✅ 性能监控数据已重置")


# 全局性能监控器
_global_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """获取全局性能监控器（单例）"""
    global _global_monitor

    if _global_monitor is None:
        # 从环境变量读取是否启用
        import os

        enable = os.getenv("ENABLE_PERFORMANCE_MONITOR", "true").lower() in (
            "true",
            "1",
            "yes",
        )
        _global_monitor = PerformanceMonitor(enable=enable)

    return _global_monitor


# 便捷函数
def track(func: Callable = None, name: Optional[str] = None):
    """
    便捷装饰器: 使用全局监控器

    示例:
        from shared.performance import track

        @track
        def my_function():
            pass
    """
    monitor = get_monitor()
    return monitor.track(func, name)


@contextmanager
def track_block(block_name: str):
    """
    便捷上下文管理器: 使用全局监控器

    示例:
        from shared.performance import track_block

        with track_block("数据库查询"):
            db.query(...)
    """
    monitor = get_monitor()
    with monitor.track_block(block_name):
        yield


def print_performance_report():
    """打印全局性能报告"""
    monitor = get_monitor()
    monitor.print_report()


def reset_performance_stats():
    """重置全局性能统计"""
    monitor = get_monitor()
    monitor.reset()
