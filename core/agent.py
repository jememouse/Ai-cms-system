from typing import Dict, List, Any
from .skill import BaseSkill

class BaseAgent:
    """
    智能体基类 (Base Agent)
    Agent 拥有人设 (Persona) 和技能 (Skills)
    """
    def __init__(self, name: str, role: str, description: str):
        self.name = name
        self.role = role          # 角色 (e.g. "资深编辑")
        self.description = description
        self.skills: Dict[str, BaseSkill] = {}
        self.memory: List[Dict] = [] # 简单的短期记忆
        
    def add_skill(self, skill: BaseSkill):
        """装备技能"""
        self.skills[skill.name] = skill
        print(f"🤖 [{self.name}] 已装备技能: {skill.name}")

    def use_skill(self, skill_name: str, input_data: Any) -> Any:
        """使用技能"""
        if skill_name not in self.skills:
            raise ValueError(f"Agent {self.name} 不具备技能 {skill_name}")
        
        print(f"🤖 [{self.name}] 正在施放技能: {skill_name} ...")
        try:
            result = self.skills[skill_name].execute(input_data)
            return result
        except Exception as e:
            print(f"❌ 技能 {skill_name} 施放失败: {e}")
            return None
