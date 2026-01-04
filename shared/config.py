# shared/config.py
"""
共享配置模块
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 飞书配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_BASE_ID = os.getenv("FEISHU_BASE_ID", "ROVGbzfTfaEGjosDkxHck65Cnmx")
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID", "tblxkLHxg9K3uHyp")

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

# 每分类最大处理数量
MAX_GENERATE_PER_CATEGORY = int(os.getenv("MAX_GENERATE_PER_CATEGORY", "100"))  # 节点2: 文章生成 (默认全部)
MAX_PUBLISH_PER_CATEGORY = int(os.getenv("MAX_PUBLISH_PER_CATEGORY", "2"))      # 节点3: RPA 发布

# 发布配置文件路径
PUBLISH_CONFIG_FILE = os.path.join(PROJECT_ROOT, "publish_config.json")
