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
FEISHU_TABLE_ID = "cms" # Mapped to Google Worksheet Name
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "https://open.feishu.cn/open-apis/bot/v2/hook/009c15b4-fb99-4eaa-82a7-f1a190083bfc")

# Google Sheets Configuration
GOOGLE_CREDENTIALS_FILE = os.path.join(PROJECT_ROOT, "service_account.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "1EZePBUdlJa_nn_OVQJie4sFqgG4UxDJm56ZPah92eKY")
GOOGLE_WORKSHEET_NAME = "cms" # Default

# 社交媒体平台配置 (矩阵系统)
SOCIAL_PLATFORMS = {
    "douyin": {
        "name": "抖音",
        "type": "article", # User requested Article
        "sheet_name": "douyin",
        "title_limit": 20,
        "content_limit": 900,
        "keywords_limit": 4,
        "daily_target": 12
    },
    "wechat_video": {
        "name": "微信视频",
        "type": "article", # User requested Article
        "sheet_name": "wechat_video",
        "title_limit": 20,
        "content_limit": 900,
        "keywords_limit": 4,
        "daily_target": 9
    },
    "xhs": {
        "name": "小红书",
        "type": "note",
        "sheet_name": "xhs",
        "title_limit": 20,
        "content_limit": 900,
        "keywords_limit": 4,
        "daily_target": 12
    },
    "kuaishou": {
        "name": "快手",
        "type": "article", # User requested Article
        "sheet_name": "kuaishou",
        "title_limit": 20,
        "content_limit": 400, # 短快
        "keywords_limit": 4,
        "daily_target": 12
    },
    "baijiahao": {
        "name": "百家号",
        "type": "article",
        "sheet_name": "baijiahao",
        "title_limit": 20,
        "content_limit": 900,
        "keywords_limit": 1, # 只要一个精准词
        "daily_target": 12
    },
    "weibo": {
        "name": "微博",
        "type": "microblog",
        "sheet_name": "weibo",
        "title_limit": 20, # 微博其实没标题，这里指第一句
        "content_limit": 900,
        "keywords_limit": 4,
        "daily_target": 12
    },
    "bilibili": {
        "name": "BILIBILI",
        "type": "article", # User requested Article
        "sheet_name": "bilibili",
        "title_limit": 20,
        "content_limit": 900,
        "keywords_limit": 10, # B站tag多
        "daily_target": 3
    }
}
# 旧配置兼容
FEISHU_XHS_TABLE_ID = "xhs"
MAX_DAILY_XHS = 12 # Default fallback

# WellCMS 配置
WELLCMS_USERNAME = os.getenv("WELLCMS_USERNAME", "product_manager")
WELLCMS_PASSWORD = os.getenv("WELLCMS_PASSWORD", "5227756c4aae247b")
WELLCMS_LOGIN_URL = os.getenv("WELLCMS_LOGIN_URL", "https://heyijiapack.com/news/user-login.html")
WELLCMS_ADMIN_URL = os.getenv("WELLCMS_ADMIN_URL", "https://heyijiapack.com/news/admin/index.php")
WELLCMS_POST_URL = os.getenv("WELLCMS_POST_URL", "https://heyijiapack.com/news/admin/index.php?0=content&1=create&fid=0")

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
MAX_PUBLISH_PER_CATEGORY = int(os.getenv("MAX_PUBLISH_PER_CATEGORY", "18"))      # 节点3: RPA 发布

# 发布配置文件路径
PUBLISH_CONFIG_FILE = os.path.join(PROJECT_ROOT, "publish_config.json")

# Pollinations AI Configuration
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "pk_stu33lc2AgU55DRp")
