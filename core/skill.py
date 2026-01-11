from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseSkill(ABC):
    """
    技能原子 (Skill Atom)
    每个技能只做一件事，接收输入，返回结果
    """
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """执行技能逻辑"""
        pass
