# feishu_uploader.py
import requests

import json
import time
import os
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# ================= 配置区域 =================
# 优先从环境变量获取，兜底使用默认值 (方便本地测试)
APP_ID = os.getenv("FEISHU_APP_ID", "cli_a9d821dd2cb89bcb")
APP_SECRET = os.getenv("FEISHU_APP_SECRET", "lCRZc6MbLMZwQ55mEXYivhxL2Ey7uJzb")
APP_TOKEN = os.getenv("FEISHU_BASE_ID", "ROVGbzfTfaEGjosDkxHck65Cnmx") # Base Token
TABLE_ID = os.getenv("FEISHU_TABLE_ID", "tblxkLHxg9K3uHyp")         # Table ID

# 数据源文件
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "generated_seo_data.json")
# ==========================================

class FeishuBitable:
    def __init__(self):
        self.app_id = APP_ID
        self.app_secret = APP_SECRET
        # 自动获取 Token
        self.token = self.get_tenant_access_token()

    def get_tenant_access_token(self):
        """获取飞书应用凭证"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        try:
            resp = requests.post(url, headers=headers, json={
                "app_id": self.app_id,
                "app_secret": self.app_secret
            })
            if resp.status_code == 200 and resp.json().get("code") == 0:
                print("✅ 飞书鉴权成功")
                return resp.json().get("tenant_access_token")
            else:
                print(f"❌ 飞书鉴权失败: {resp.text}")
                return None
        except Exception as e:
            print(f"❌ 鉴权网络错误: {e}")
            return None

    def upload(self):
        if not self.token:
            return

        if not os.path.exists(DATA_FILE):
            print(f"❌ 找不到数据文件 {DATA_FILE}")
            return

        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            records = json.load(f)

        if not records:
            print("⚠️ 数据文件为空，无需上传。")
            return

        print(f"🚀 准备上传 {len(records)} 条数据到飞书...")
        
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/batch_create"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8"
        }

        # 分批上传 (飞书限制每次最多 100 条，建议 50 条比较稳)
        batch_size = 50
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            payload_records = []
            
            for item in batch:
                payload_records.append({
                    "fields": {
                        "Topic": item.get("Topic", "无标题"),
                        "大项分类": item.get("大项分类", "未分类"),
                        "Status": "Pending"
                    }
                })

            try:
                resp = requests.post(url, headers=headers, json={"records": payload_records})
                if resp.json().get("code") == 0:
                    print(f"   -> [Batch {i//batch_size + 1}] 成功上传 {len(batch)} 条")
                else:
                    print(f"   ❌ [Batch {i//batch_size + 1}] 上传失败: {resp.text}")
            except Exception as e:
                print(f"   ⚠️ 网络请求失败: {e}")
            
            time.sleep(0.5)
        
        print("✨ 上传任务完成！")

if __name__ == "__main__":
    FeishuBitable().upload()
