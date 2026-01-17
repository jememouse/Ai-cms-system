"""
YAML 配置加载器
支持热更新和环境变量覆盖
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """
    配置加载器

    功能:
    1. 加载 YAML 配置文件
    2. 支持环境变量覆盖
    3. 支持热更新（重新加载）
    4. 提供便捷的访问接口

    用法:
        # 加载配置
        config = ConfigLoader("config/skills_config.yaml")

        # 访问配置
        douyin_config = config.get("social_platforms.douyin")
        title_max = config.get("social_platforms.douyin.limits.title_max", default=18)

        # 热更新
        config.reload()
    """

    def __init__(self, config_path: str):
        """
        初始化配置加载器

        Args:
            config_path: 配置文件路径（相对于项目根目录）
        """
        self.config_path = self._resolve_path(config_path)
        self._config_data: Dict[str, Any] = {}
        self._last_modified: Optional[float] = None
        self.load()

    def _resolve_path(self, config_path: str) -> Path:
        """解析配置文件路径"""
        # 如果是绝对路径，直接使用
        if os.path.isabs(config_path):
            return Path(config_path)

        # 否则相对于项目根目录
        project_root = Path(__file__).parent.parent
        return project_root / config_path

    def load(self):
        """加载配置文件"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._config_data = yaml.safe_load(f) or {}

        self._last_modified = self.config_path.stat().st_mtime

    def reload(self):
        """重新加载配置（热更新）"""
        self.load()

    def is_modified(self) -> bool:
        """检查配置文件是否被修改"""
        if not self.config_path.exists():
            return False

        current_mtime = self.config_path.stat().st_mtime
        return current_mtime != self._last_modified

    def auto_reload_if_modified(self):
        """如果配置文件被修改，自动重新加载"""
        if self.is_modified():
            self.reload()

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的路径）

        Args:
            key_path: 配置键路径（例如: "social_platforms.douyin.limits.title_max"）
            default: 默认值

        Returns:
            配置值

        示例:
            config.get("social_platforms.douyin.name")  # "抖音"
            config.get("social_platforms.douyin.limits.title_max", default=18)  # 18
        """
        # 检查环境变量覆盖
        env_key = key_path.upper().replace(".", "_")
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_type(env_value, type(default) if default is not None else str)

        # 从配置文件获取
        keys = key_path.split(".")
        value = self._config_data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def _convert_type(self, value: str, target_type: type) -> Any:
        """转换环境变量类型"""
        try:
            if target_type == bool:
                return value.lower() in ("true", "1", "yes")
            elif target_type == int:
                return int(value)
            elif target_type == float:
                return float(value)
            else:
                return value
        except ValueError:
            return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取整个配置节

        Args:
            section: 节名称

        Returns:
            配置节字典

        示例:
            platforms = config.get_section("social_platforms")
        """
        return self.get(section, default={})

    def all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config_data.copy()

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)

    def __contains__(self, key: str) -> bool:
        """支持 in 操作"""
        return self.get(key) is not None


# 全局配置实例（单例）
_global_config: Optional[ConfigLoader] = None


def get_config(config_path: str = "config/skills_config.yaml") -> ConfigLoader:
    """
    获取全局配置实例（单例模式）

    Args:
        config_path: 配置文件路径

    Returns:
        ConfigLoader 实例
    """
    global _global_config

    if _global_config is None:
        _global_config = ConfigLoader(config_path)

    return _global_config


def reload_config():
    """重新加载全局配置"""
    global _global_config

    if _global_config is not None:
        _global_config.reload()
