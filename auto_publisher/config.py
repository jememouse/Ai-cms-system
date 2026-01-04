# auto_publisher/config.py
"""
配置管理模块
从环境变量和配置文件读取配置
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """配置类"""
    
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
    
    # 发布配置
    MAX_ARTICLES_PER_CATEGORY = int(os.getenv("MAX_ARTICLES_PER_CATEGORY", "2"))
    
    # 分类映射 (飞书分类名 -> WellCMS category_id)
    CATEGORY_MAP = {
        "专业知识": "1",
        "行业资讯": "2",
        "产品介绍": "3"
    }


config = Config()
