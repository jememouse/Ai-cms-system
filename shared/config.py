# shared/config.py
"""
共享配置模块
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# LLM API 配置 (支持 OpenRouter 和 DeepSeek)
# 优先使用 OpenRouter，如果没有配置则回退到 DeepSeek
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# 根据可用的 API Key 选择端点
if OPENROUTER_API_KEY:
    LLM_API_KEY = OPENROUTER_API_KEY
    LLM_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    LLM_MODEL = "deepseek/deepseek-chat"  # DeepSeek V3 - JSON 格式更稳定
else:
    LLM_API_KEY = DEEPSEEK_API_KEY
    LLM_API_URL = "https://api.deepseek.com/v1/chat/completions"
    LLM_MODEL = "deepseek-chat"  # DeepSeek 原生模型名称

# 飞书配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_BASE_ID = os.getenv("FEISHU_BASE_ID", "ROVGbzfTfaEGjosDkxHck65Cnmx")
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID", "tblxkLHxg9K3uHyp")
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "https://open.feishu.cn/open-apis/bot/v2/hook/009c15b4-fb99-4eaa-82a7-f1a190083bfc")

# 小红书配置
# 注意：这是新表的 ID，不是原来的主表 ID
FEISHU_XHS_TABLE_ID = os.getenv("FEISHU_XHS_TABLE_ID", "tblf1DMg5p9HXcwD") 
MAX_DAILY_XHS = int(os.getenv("MAX_DAILY_XHS", "20")) # 每日/单次运行最大生成数

# WellCMS 配置
WELLCMS_USERNAME = os.getenv("WELLCMS_USERNAME", "product_manager")
WELLCMS_PASSWORD = os.getenv("WELLCMS_PASSWORD", "5227756c4aae247b")
WELLCMS_LOGIN_URL = os.getenv("WELLCMS_LOGIN_URL", "https://heyijiapack.com/news/user-login.html")
WELLCMS_ADMIN_URL = os.getenv("WELLCMS_ADMIN_URL", "https://heyijiapack.com/news/admin/index.php")
WELLCMS_POST_URL = os.getenv("WELLCMS_POST_URL", "https://heyijiapack.com/news/admin/index.php?0=content&1=create&fid=2")

# 配置文件
CONFIG_FILE = os.path.join(PROJECT_ROOT, "box_artist_config.json")

# 分类映射
CATEGORY_MAP = {
    "专业知识": "1",
    "行业资讯": "2",
    "产品介绍": "3"
}

# 状态常量 (按节点流转)
STATUS_READY = "Ready"         # 节点1完成: 标题已生成，等待文章生成
STATUS_PENDING = "Pending"     # 节点2完成: 文章已生成，等待发布
STATUS_PUBLISHED = "Published" # 节点3完成: 已发布
# STATUS_GENERATED 已废弃，合并入 STATUS_PENDING

# 每分类最大处理数量
MAX_GENERATE_PER_CATEGORY = int(os.getenv("MAX_GENERATE_PER_CATEGORY", "100"))  # 节点2: 文章生成 (默认全部)
MAX_PUBLISH_PER_CATEGORY = int(os.getenv("MAX_PUBLISH_PER_CATEGORY", "10"))      # 节点3: RPA 发布

# 发布配置文件路径
PUBLISH_CONFIG_FILE = os.path.join(PROJECT_ROOT, "publish_config.json")
