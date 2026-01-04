# trends_generator/config.py
"""
配置管理模块
"""
import os
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# 路径配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
CONFIG_FILE = os.path.join(PROJECT_ROOT, 'box_artist_config.json')
TRENDS_FILE = os.path.join(PROJECT_ROOT, 'trends_data.json')
OUTPUT_FILE = os.path.join(PROJECT_ROOT, 'generated_seo_data.json')

# DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# 飞书配置
FEISHU_APP_ID = os.getenv("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.getenv("FEISHU_APP_SECRET", "")
FEISHU_BASE_ID = os.getenv("FEISHU_BASE_ID", "ROVGbzfTfaEGjosDkxHck65Cnmx")
FEISHU_TABLE_ID = os.getenv("FEISHU_TABLE_ID", "tblxkLHxg9K3uHyp")
