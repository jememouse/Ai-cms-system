# scripts/test_step4_limited.py
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient
from shared import config
from agents.social_manager import SocialManagerAgent

def main():
    print("🚀 启动 Step 4 (Social XHS) 测试...")
    client = GoogleSheetClient()
    
    # 1. Fetch Published to process
    print(f"☁️ 正在拉取 'Published' 状态的文章...")
    records = client.fetch_records_by_status(config.STATUS_PUBLISHED, limit=1)
    
    # Find one that is NOT done
    target_record = None
    for r in records:
        if r.get('XHS_Status') != 'Done':
            target_record = r
            break
            
    if not target_record:
        print("❌ 未找到待分发(Published 且 XHS_Status!=Done) 的文章。请先检查数据。")
        # For testing, we might want to force one? 
        # Or just pick the first one and pretend.
        if records:
            print("⚠️ 没找到未处理的，将强制复用第一条 Published 文章进行测试...")
            target_record = records[0]
        else:
            return

    title = target_record.get('Title', 'No Title')
    print(f"🎯 选中测试文章: {title}")
    
    # 2. Mock Agent Generation
    # We want to test the SHEET writing logic mainly. 
    # Calling the real agent takes time and cost, but let's do real agent execution 
    # if it's not too expensive, or mock it.
    # User asked for "Real Execution" for previous step, so let's try real here too OR mock for speed?
    # Let's Mock Agent output to isolate Sheet logic verification.
    
    print("🧠 (Mock) 生成小红书笔记...")
    post_data = {
        "title": f"XHS笔记: {title[:10]}...",
        "content": "这里是小红书的种草文案... #测试 #包装",
        "keywords": "#包装 #定制",
        "cover_url": "http://mock-url/cover.jpg",
        "source_title": title
    }
    
    # 3. Write to XHS Sheet
    print("💾 正在写入 Google Sheet (表: xhs)...")
    new_record = {
        "Title": post_data['title'],
        "Content": post_data['content'] + f"\n\n[封面图]: {post_data['cover_url']}", 
        "Keywords": post_data['keywords'],
        "Source": post_data['source_title'], 
        "Status": "Draft",
        "Cover": post_data['cover_url'],
        "生成时间": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    res_id = client.create_record(new_record, table_id="xhs") # Use "xhs" directly or from config
    
    if res_id:
        print(f"🎉 写入成功! ID: {res_id}")
        
        # 4. Update CMS Sheet
        print(f"🔄 更新原文章 XHS_Status -> Done ...")
        cms_success = client.update_record(target_record['record_id'], {"XHS_Status": "Done"})
        
        if cms_success:
             print("🎉 CMS 状态更新成功")
        else:
             print("❌ CMS 状态更新失败")
             
    else:
        print("❌ 写入 XHS 表失败")

if __name__ == "__main__":
    main()
