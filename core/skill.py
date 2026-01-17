from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class BaseSkill(ABC):
    """
    技能原子 (Skill Atom)
    每个技能只做一件事，接收输入，返回结果

    生命周期:
    1. __init__() - 初始化配置
    2. setup() - 资源准备 (可选实现)
    3. execute() - 执行业务逻辑 (必须实现)
    4. teardown() - 资源清理 (可选实现)
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._is_setup = False

    def setup(self):
        """
        资源初始化钩子 (可选实现)

        用途:
        - 启动浏览器 (Playwright)
        - 建立数据库连接
        - 加载大型模型
        - 预热缓存

        示例:
            def setup(self):
                self.browser = playwright.chromium.launch()
                self.page = self.browser.new_page()
        """
        self._is_setup = True
        logger.debug(f"[{self.name}] setup() called (default implementation)")

    def teardown(self):
        """
        资源清理钩子 (可选实现)

        用途:
        - 关闭浏览器
        - 关闭数据库连接
        - 释放内存
        - 清理临时文件

        示例:
            def teardown(self):
                if self.browser:
                    self.browser.close()
        """
        self._is_setup = False
        logger.debug(f"[{self.name}] teardown() called (default implementation)")

    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """
        执行技能逻辑 (必须实现)

        Args:
            input_data: 输入数据

        Returns:
            执行结果
        """
        pass

    def __enter__(self):
        """上下文管理器入口"""
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.teardown()
        return False
