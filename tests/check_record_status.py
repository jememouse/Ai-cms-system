
import sys
import os
import requests
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import config
from shared.feishu_client import FeishuClient

def check_record():
    client = FeishuClient()
    # Record ID captured from the previous test run output (Step 1065)
    record_id = "recv7SraQA4cPx"
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{client.base_id}/tables/{client.table_id}/records/{record_id}"
    # Use the client's internal token which is automatically refreshed
    headers = {
        "Authorization": f"Bearer {client.token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    print(f"🔍 Fetching Record ID from Feishu: {record_id}")
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 0:
                record = data["data"]["record"]
                fields = record["fields"]
                
                print("\n" + "="*40)
                print("📋 飞书记录详情 (Feishu Record Details)")
                print("="*40)
                print(f"📌 Record ID : {record['record_id']}")
                # Handle potentially complex field types (text vs object)
                title = fields.get('Title', '')
                if isinstance(title, list) and title: title = title[0].get('text','')
                print(f"📑 Title     : {title}")
                print(f"📊 Status    : {fields.get('Status', 'N/A')}")
                
                # The target field we want to verify
                url_val = fields.get('URL', '')
                if isinstance(url_val, list) and url_val: url_val = url_val[0].get('text', '') # Feishu text fields are sometimes lists
                elif isinstance(url_val, dict): url_val = url_val.get('text', '')
                
                print(f"🔗 URL       : {url_val}")
                
                # Check for emptiness
                if url_val:
                    print(f"\n✅ 验证通过: URL 字段已成功回写！")
                else:
                    print(f"\n❌ 验证失败: URL 字段为空！")
                    
                print("="*40)
            else:
                print(f"❌ API Error: {data}")
        else:
            print(f"❌ HTTP Error: {resp.status_code} - {resp.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    check_record()
