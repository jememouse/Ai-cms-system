"""
Skill 工厂类
提供统一的 Skill 创建和管理接口
"""
import os
import sys
import importlib
import logging
from typing import Dict, Type, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.skill import BaseSkill

logger = logging.getLogger(__name__)


class SkillFactory:
    """
    Skill 工厂类

    功能:
    1. 动态加载 skills 目录下的所有 Skill
    2. 单例模式管理 Skill 实例
    3. 提供便捷的创建和获取接口

    用法:
        # 方式1: 创建新实例
        skill = SkillFactory.create("trend_search")

        # 方式2: 获取单例
        skill = SkillFactory.get_singleton("trend_search")

        # 方式3: 列出所有可用 Skill
        skills = SkillFactory.list_available()
    """

    # 类变量: Skill 注册表
    _registry: Dict[str, Type[BaseSkill]] = {}
    _singletons: Dict[str, BaseSkill] = {}
    _initialized = False

    @classmethod
    def _initialize(cls):
        """初始化工厂: 自动扫描 skills 目录"""
        if cls._initialized:
            return

        skills_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")
        if not os.path.exists(skills_dir):
            logger.warning(f"Skills 目录不存在: {skills_dir}")
            cls._initialized = True
            return

        # 扫描所有 .py 文件
        for filename in os.listdir(skills_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                module_name = filename[:-3]
                try:
                    # 动态导入模块
                    module = importlib.import_module(f"skills.{module_name}")

                    # 查找 BaseSkill 的子类
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, BaseSkill)
                            and attr is not BaseSkill
                        ):
                            # 注册 Skill (使用类名的小写作为 key)
                            skill_name = attr_name.replace("Skill", "").lower()
                            cls._registry[skill_name] = attr
                            logger.debug(f"✅ 注册 Skill: {skill_name} ({attr_name})")

                except Exception as e:
                    logger.warning(f"⚠️ 加载 {module_name} 失败: {e}")

        cls._initialized = True
        logger.info(f"🎯 Skill 工厂初始化完成，共注册 {len(cls._registry)} 个 Skill")

    @classmethod
    def create(cls, skill_name: str) -> Optional[BaseSkill]:
        """
        创建 Skill 实例 (每次创建新实例)

        Args:
            skill_name: Skill 名称 (例如: "trend_search", "deep_write")

        Returns:
            Skill 实例，失败返回 None

        示例:
            skill = SkillFactory.create("trend_search")
            result = skill.execute({"mining_seeds": [...]})
        """
        cls._initialize()

        # 标准化名称
        skill_name = skill_name.lower().replace("_", "").replace("-", "")

        # 在注册表中查找
        skill_class = cls._registry.get(skill_name)
        if not skill_class:
            logger.error(f"❌ Skill 未注册: {skill_name}")
            logger.info(f"   可用 Skill: {list(cls._registry.keys())}")
            return None

        try:
            instance = skill_class()
            logger.debug(f"✅ 创建 Skill 实例: {skill_name}")
            return instance
        except Exception as e:
            logger.error(f"❌ 创建 Skill 失败: {skill_name} - {e}")
            return None

    @classmethod
    def get_singleton(cls, skill_name: str) -> Optional[BaseSkill]:
        """
        获取 Skill 单例 (同一个 Skill 只创建一次)

        Args:
            skill_name: Skill 名称

        Returns:
            Skill 单例，失败返回 None

        示例:
            # 多次调用返回同一实例
            skill1 = SkillFactory.get_singleton("trend_search")
            skill2 = SkillFactory.get_singleton("trend_search")
            assert skill1 is skill2  # True
        """
        cls._initialize()

        skill_name = skill_name.lower().replace("_", "").replace("-", "")

        # 检查是否已创建单例
        if skill_name in cls._singletons:
            return cls._singletons[skill_name]

        # 创建并缓存
        instance = cls.create(skill_name)
        if instance:
            cls._singletons[skill_name] = instance
            logger.debug(f"✅ 创建 Skill 单例: {skill_name}")

        return instance

    @classmethod
    def list_available(cls) -> List[str]:
        """
        列出所有可用的 Skill

        Returns:
            Skill 名称列表

        示例:
            skills = SkillFactory.list_available()
            print(skills)
            # ['trendsearch', 'topicanalysis', 'deepwrite', ...]
        """
        cls._initialize()
        return list(cls._registry.keys())

    @classmethod
    def register(cls, skill_name: str, skill_class: Type[BaseSkill]):
        """
        手动注册 Skill (用于测试或插件)

        Args:
            skill_name: Skill 名称
            skill_class: Skill 类

        示例:
            class CustomSkill(BaseSkill):
                def execute(self, input_data):
                    return {"result": "custom"}

            SkillFactory.register("custom", CustomSkill)
        """
        skill_name = skill_name.lower().replace("_", "").replace("-", "")
        cls._registry[skill_name] = skill_class
        logger.info(f"✅ 手动注册 Skill: {skill_name}")

    @classmethod
    def clear_singletons(cls):
        """
        清理所有单例 (用于测试)

        调用所有 Skill 的 teardown() 方法并清空缓存
        """
        for skill_name, skill in cls._singletons.items():
            try:
                skill.teardown()
                logger.debug(f"✅ 清理 Skill 单例: {skill_name}")
            except Exception as e:
                logger.warning(f"⚠️ 清理 {skill_name} 失败: {e}")

        cls._singletons.clear()
        logger.info("✅ 所有 Skill 单例已清理")

    @classmethod
    def reset(cls):
        """
        重置工厂 (用于测试)

        清空注册表、单例缓存并标记为未初始化
        """
        cls.clear_singletons()
        cls._registry.clear()
        cls._initialized = False
        logger.info("✅ Skill 工厂已重置")


# 便捷函数
def create_skill(skill_name: str) -> Optional[BaseSkill]:
    """
    便捷函数: 创建 Skill

    等价于 SkillFactory.create(skill_name)
    """
    return SkillFactory.create(skill_name)


def get_skill(skill_name: str) -> Optional[BaseSkill]:
    """
    便捷函数: 获取 Skill 单例

    等价于 SkillFactory.get_singleton(skill_name)
    """
    return SkillFactory.get_singleton(skill_name)
