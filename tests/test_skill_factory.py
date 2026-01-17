"""
测试 SkillFactory 工厂类
"""
import sys
import os
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.skill import BaseSkill
from shared.skill_factory import SkillFactory, create_skill, get_skill


class MockSkill(BaseSkill):
    """测试用 Mock Skill"""

    def __init__(self):
        super().__init__(name="mock_skill", description="Mock skill for testing")
        self.executed = False

    def execute(self, input_data):
        self.executed = True
        return {"result": "mock_result", "input": input_data}


class TestSkillFactory(unittest.TestCase):
    """SkillFactory 测试套件"""

    def setUp(self):
        """每个测试前重置工厂"""
        SkillFactory.reset()

    def tearDown(self):
        """每个测试后清理"""
        SkillFactory.reset()

    def test_manual_register(self):
        """测试手动注册 Skill"""
        SkillFactory.register("mock", MockSkill)
        available = SkillFactory.list_available()
        self.assertIn("mock", available)

    def test_create_skill(self):
        """测试创建 Skill 实例"""
        SkillFactory.register("mock", MockSkill)

        # 创建实例
        skill = SkillFactory.create("mock")
        self.assertIsNotNone(skill)
        self.assertIsInstance(skill, MockSkill)

        # 执行
        result = skill.execute({"test": "data"})
        self.assertTrue(skill.executed)
        self.assertEqual(result["result"], "mock_result")

    def test_create_multiple_instances(self):
        """测试创建多个实例（非单例）"""
        SkillFactory.register("mock", MockSkill)

        skill1 = SkillFactory.create("mock")
        skill2 = SkillFactory.create("mock")

        # 应该是不同的实例
        self.assertIsNot(skill1, skill2)

    def test_get_singleton(self):
        """测试单例模式"""
        SkillFactory.register("mock", MockSkill)

        skill1 = SkillFactory.get_singleton("mock")
        skill2 = SkillFactory.get_singleton("mock")

        # 应该是同一个实例
        self.assertIs(skill1, skill2)

    def test_create_nonexistent_skill(self):
        """测试创建不存在的 Skill"""
        skill = SkillFactory.create("nonexistent")
        self.assertIsNone(skill)

    def test_name_normalization(self):
        """测试名称标准化（下划线、连字符）"""
        SkillFactory.register("mock_skill", MockSkill)

        # 各种格式都应该能找到
        skill1 = SkillFactory.create("mock_skill")
        skill2 = SkillFactory.create("mock-skill")
        skill3 = SkillFactory.create("mockskill")

        self.assertIsNotNone(skill1)
        self.assertIsNotNone(skill2)
        self.assertIsNotNone(skill3)

    def test_clear_singletons(self):
        """测试清理单例"""
        SkillFactory.register("mock", MockSkill)

        # 创建单例
        skill = SkillFactory.get_singleton("mock")
        self.assertIsNotNone(skill)

        # 清理
        SkillFactory.clear_singletons()

        # 再次获取应该是新实例
        skill2 = SkillFactory.get_singleton("mock")
        self.assertIsNot(skill, skill2)

    def test_convenience_functions(self):
        """测试便捷函数"""
        SkillFactory.register("mock", MockSkill)

        # 测试 create_skill
        skill1 = create_skill("mock")
        self.assertIsNotNone(skill1)

        # 测试 get_skill
        skill2 = get_skill("mock")
        skill3 = get_skill("mock")
        self.assertIs(skill2, skill3)


class TestBaseSkillLifecycle(unittest.TestCase):
    """测试 BaseSkill 生命周期钩子"""

    def test_setup_teardown(self):
        """测试 setup 和 teardown 方法"""
        skill = MockSkill()

        # 初始状态
        self.assertFalse(skill._is_setup)

        # 调用 setup
        skill.setup()
        self.assertTrue(skill._is_setup)

        # 调用 teardown
        skill.teardown()
        self.assertFalse(skill._is_setup)

    def test_context_manager(self):
        """测试上下文管理器"""
        skill = MockSkill()

        with skill as s:
            # 在 with 块内，setup 已被调用
            self.assertTrue(s._is_setup)
            self.assertIs(s, skill)

        # 退出 with 块后，teardown 已被调用
        self.assertFalse(skill._is_setup)

    def test_context_manager_with_exception(self):
        """测试上下文管理器处理异常"""
        skill = MockSkill()

        try:
            with skill:
                raise ValueError("Test exception")
        except ValueError:
            pass

        # 即使有异常，teardown 也应该被调用
        self.assertFalse(skill._is_setup)


if __name__ == "__main__":
    unittest.main()
