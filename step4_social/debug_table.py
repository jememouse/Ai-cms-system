
import sys
import os
import requests
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import config
from shared.google_client import GoogleSheetClient

def debug_fields():
    client = GoogleSheetClient()
    table_id = config.FEISHU_XHS_TABLE_ID
    
    print(f"🕵️‍♂️ 正在检查表 [{table_id}] 的字段结构...")
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{client.base_id}/tables/{table_id}/fields"
    
    try:
        resp = requests.get(url, headers=client._headers())
        data = resp.json()
        
        if data.get("code") == 0:
            items = data.get("data", {}).get("items", [])
            print(f"✅ 成功获取字段列表 (共 {len(items)} 个):")
            print("-" * 30)
            for item in items:
                print(f"🔹 字段名: '{item['field_name']}'  (类型: {item['type']})")
            print("-" * 30)
            print("请检查上述字段名是否与 runner.py 中的 Key 完全一致。")
        else:
            print(f"❌ 获取字段失败: {data}")
            
    except Exception as e:
        print(f"❌ 网络错误: {e}")

if __name__ == "__main__":
    debug_fields()
