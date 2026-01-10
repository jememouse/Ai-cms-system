
import sys
import os
import time
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.feishu_client import FeishuClient
from step3_publish.wellcms_rpa import WellCMSPublisher
from shared import config
from datetime import datetime

def run_test():
    client = FeishuClient()
    
    # 1. Create a unique test record
    timestamp = int(time.time())
    test_title = f"Test_URL_Writeback_{timestamp}"
    print(f"\n1. Creating test record: {test_title}")
    
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_record = {
        "Topic": test_title,
        "Status": "Pending", # Iterate as if it is ready to publish
        "Title": test_title,
        "HTML_Content": f"<p>This is a test article for URL writeback verification. {timestamp}</p>",
        "大项分类": "行业资讯",
        "关键词": "Test, Writeback",
        "描述": "Test description",
        "生成时间": current_time_str,
        "标题生成时间": current_time_str
    }
    
    if client.batch_create_records([new_record]):
        print("   ✅ Record created.")
    else:
        print("   ❌ Failed to create record.")
        return

    # 2. Find the record_id
    print("2. Fetching record_id...")
    time.sleep(3) # Wait for indexing?

    records = client.fetch_records_by_status("Pending", limit=200) # Increased limit to find it if queue is long
    target_record = None
    
    # Search logic
    for r in records:
        if r.get("topic") == test_title or r.get("title") == test_title:
            target_record = r
            break
            
    if not target_record:
        print("   ⚠️ Could not find the created test record immediately. Waiting 5s...")
        time.sleep(5)
        records = client.fetch_records_by_status("Pending", limit=200)
        for r in records:
            if r.get("topic") == test_title or r.get("title") == test_title:
                target_record = r
                break
                
    if not target_record:
         print("   ❌ Still not found. Aborting.")
         return

    record_id = target_record['record_id']
    print(f"   ✅ Found record_id: {record_id}")
    
    # 3. Publish to WellCMS
    print("3. Publishing to WellCMS...")
    publisher = WellCMSPublisher()
    
    article_data = {
        "title": test_title,
        "html_content": target_record['html_content'],
        "category_id": "2", # 行业资讯
        "keywords": target_record['keywords'],
        "description": target_record['description']
    }
    
    try:
        success, url = publisher.publish_sync(article_data)
    except Exception as e:
        print(f"   ❌ Publish Exception: {e}")
        success = False
        url = ""
    
    if not success:
        print("   ❌ Publishing failed.")
        return
        
    print(f"   ✅ Published successfully. Returned URL: {url}")
    
    # 4. Write back to Feishu
    print("4. Writing URL back to Feishu...")
    publish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    update_fields = {
        "Status": "Published",
        "URL": url,
        "发布时间": publish_time
    }
    
    if client.update_record(record_id, update_fields):
        print("   ✅ Update success.")
    else:
        print("   ❌ Update failed.")
        return
        
    # 5. Verify persistence
    print("5. Verifying persistence...")
    time.sleep(3) # Wait for update to reflect
    
    # Fetch from Published
    published_records = client.fetch_records_by_status("Published", limit=50)
    verified = False
    fetched_url = ""
    fetched_time = ""
    
    for r in published_records:
        if r['record_id'] == record_id:
             fetched_url = r.get("url", "")
             fetched_time = r.get("published_at", "")
             verified = True
             break
             
    if verified:
        print(f"   ✅ Record verified in 'Published' status.")
        print(f"   🔗 Fetched URL: {fetched_url}")
        print(f"   ⏰ Fetched Time: {fetched_time}")
        
        if fetched_url == url:
             print("   🎉 URL MATCHES! Test Passed.")
        else:
             print(f"   ⚠️ URL MISMATCH! Expected {url}, got {fetched_url}")
    else:
        print("   ❌ Record NOT found in 'Published' status after update.")

if __name__ == "__main__":
    run_test()
