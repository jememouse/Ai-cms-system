import sys
import os
import json
import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import config, feishu_client

def get_feishu_count(client, status):
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{client.base_id}/tables/{client.table_id}/records/search"
    conditions = [{"field_name": "Status", "operator": "is", "value": [status]}]
    payload = {
        "filter": {"conjunction": "and", "conditions": conditions},
        "page_size": 1 # We only care about total
    }
    try:
        resp = requests.post(url, headers=client._headers(), json=payload, timeout=10)
        data = resp.json()
        if data.get("code") == 0:
            return data.get("data", {}).get("total", 0)
    except:
        pass
    return -1

def main():
    print("📊 System Status Report")
    print("======================")

    # 1. Step 1 Status (Local File)
    step1_count = 0
    seo_file = os.path.join(config.PROJECT_ROOT, 'generated_seo_data.json')
    if os.path.exists(seo_file):
        try:
            with open(seo_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                step1_count = len(data)
        except:
            pass
    print(f"1️⃣  Step 1 (Generated Titles/Topics): {step1_count}")

    # 2. Feishu Status
    client = feishu_client.FeishuClient()
    
    ready_count = get_feishu_count(client, "Ready")
    pending_count = get_feishu_count(client, "Pending")
    published_count = get_feishu_count(client, "Published")

    print(f"2️⃣  Step 2 Queue (Status='Ready'):    {ready_count}")
    print(f"3️⃣  Step 3 Queue (Status='Pending'):  {pending_count}")
    print(f"✅  Published (Status='Published'):   {published_count}")
    print("======================")

if __name__ == "__main__":
    main()
