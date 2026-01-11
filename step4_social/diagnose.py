
import sys
import os
import requests
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import config
from shared.feishu_client import FeishuClient

def check_llm():
    print("\n🔍 1. Testing LLM Connection...")
    print(f"   URL: {config.LLM_API_URL}")
    print(f"   Model: {config.LLM_MODEL}")
    
    headers = {
        "Authorization": f"Bearer {config.LLM_API_KEY}",
        "Content-Type": "application/json"
    }
    # OpenRouter specific
    if "openrouter" in config.LLM_API_URL:
        headers["HTTP-Referer"] = "https://github.com/debug"
        headers["X-Title"] = "Debug"

    payload = {
        "model": config.LLM_MODEL,
        "messages": [{"role": "user", "content": "Hi"}],
        "max_tokens": 5
    }
    
    try:
        resp = requests.post(config.LLM_API_URL, headers=headers, json=payload, timeout=10)
        print(f"   Status Code: {resp.status_code}")
        if resp.status_code == 200:
            print(f"   ✅ LLM Response: {resp.json()['choices'][0]['message']['content']}")
        else:
            print(f"   ❌ LLM Failed: {resp.text}")
            
            # Try fallback URL if DeepSeek for debugging
            if "deepseek" in config.LLM_API_URL and resp.status_code == 404:
                alt_url = config.LLM_API_URL.replace("/v1/chat/completions", "/chat/completions")
                print(f"   🔄 Retrying with alternative URL: {alt_url}")
                resp2 = requests.post(alt_url, headers=headers, json=payload, timeout=10)
                print(f"   Status Code: {resp2.status_code}")
                if resp2.status_code == 200:
                     print(f"   ✅ Alternative URL Worked!")
    except Exception as e:
        print(f"   ❌ Network Error: {e}")

def check_main_table():
    print("\n🔍 2. Checking Main Table Fields (for XHS_Status)...")
    client = FeishuClient()
    print(f"   Base ID: {config.FEISHU_BASE_ID}")
    print(f"   Main Table ID: {config.FEISHU_TABLE_ID}")
    
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{config.FEISHU_BASE_ID}/tables/{config.FEISHU_TABLE_ID}/fields"
    
    try:
        resp = requests.get(url, headers=client._headers())
        data = resp.json()
        if data.get("code") == 0:
            items = data.get("data", {}).get("items", [])
            found = False
            print(f"   Found {len(items)} fields.")
            for item in items:
                if "XHS" in item['field_name'] or "Status" in item['field_name']:
                     print(f"   👉 Candidate: {item['field_name']} (Type: {item['type']})")
                
                if item['field_name'] == "XHS_Status":
                    found = True
                    print("   ✅ Field 'XHS_Status' Found!")
                    # Check options
                    ops = item.get("property", {}).get("options", [])
                    print(f"      Options: {[op['name'] for op in ops]}")
            
            if not found:
                 print("   ❌ Field 'XHS_Status' NOT FOUND in Main Table.")
                 print("      Please create 'XHS_Status' (Single Select) in the Main Article Table.")
        else:
            print(f"   ❌ Feishu API Error: {data}")
    except Exception as e:
        print(f"   ❌ Network Error: {e}")

if __name__ == "__main__":
    check_llm()
    check_main_table()
