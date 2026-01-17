"""
统一的 Skill 结果类型
提供标准化的成功/失败响应
"""
from typing import Any, Optional, Generic, TypeVar
from dataclasses import dataclass

T = TypeVar('T')


@dataclass
class SkillResult(Generic[T]):
    """
    Skill 执行结果的统一封装

    Attributes:
        success: 执行是否成功
        data: 返回的数据 (成功时)
        error: 错误信息 (失败时)
        metadata: 额外的元数据 (可选)

    Examples:
        # 成功案例
        result = SkillResult.ok({"title": "标题", "content": "正文"})
        if result.success:
            print(result.data)

        # 失败案例
        result = SkillResult.fail("LLM 调用超时")
        if not result.success:
            print(result.error)
    """
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Optional[dict] = None

    @classmethod
    def ok(cls, data: T, metadata: Optional[dict] = None) -> 'SkillResult[T]':
        """
        创建成功结果

        Args:
            data: 返回的数据
            metadata: 额外的元数据 (例如: 耗时、token 数等)

        Returns:
            SkillResult 实例
        """
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def fail(cls, error: str, metadata: Optional[dict] = None) -> 'SkillResult[T]':
        """
        创建失败结果

        Args:
            error: 错误描述
            metadata: 额外的元数据 (例如: 重试次数、错误码等)

        Returns:
            SkillResult 实例
        """
        return cls(success=False, error=error, metadata=metadata)

    def unwrap(self) -> T:
        """
        获取数据，如果失败则抛出异常

        Returns:
            数据内容

        Raises:
            ValueError: 如果结果失败
        """
        if not self.success:
            raise ValueError(f"SkillResult failed: {self.error}")
        return self.data

    def unwrap_or(self, default: T) -> T:
        """
        获取数据，如果失败则返回默认值

        Args:
            default: 失败时的默认值

        Returns:
            数据内容或默认值
        """
        return self.data if self.success else default

    def unwrap_or_else(self, func) -> T:
        """
        获取数据，如果失败则调用回调函数

        Args:
            func: 失败时的回调函数

        Returns:
            数据内容或回调函数的返回值
        """
        return self.data if self.success else func(self.error)

    def map(self, func):
        """
        对成功结果应用转换函数

        Args:
            func: 转换函数

        Returns:
            新的 SkillResult
        """
        if self.success:
            try:
                new_data = func(self.data)
                return SkillResult.ok(new_data, self.metadata)
            except Exception as e:
                return SkillResult.fail(str(e), self.metadata)
        else:
            return self

    def __bool__(self):
        """支持直接用于布尔判断"""
        return self.success

    def __repr__(self):
        if self.success:
            return f"SkillResult.ok({self.data})"
        else:
            return f"SkillResult.fail('{self.error}')"
