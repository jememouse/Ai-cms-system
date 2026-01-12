# scripts/test_step2_limited.py
import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient
from shared import config
from agents.chief_editor import ChiefEditorAgent

def main():
    print("🧪 启动 Step 2 (Article Gen) 测试...")
    client = GoogleSheetClient()
    
    # 1. Fetch Ready topics
    # We expect some from previous steps
    print(f"☁️ Fetching 'Ready' topics...")
    topics = client.fetch_records_by_status(config.STATUS_READY, limit=2)
    
    if not topics:
        print("❌ No Ready topics found. Please run Step 1 test first.")
        return

    target_topic = topics[0]
    print(f"🎯 选中测试话题: {target_topic.get('Topic')} (ID: {target_topic.get('record_id')})")
    
    # 2. Mock Agent Generation (or real if fast enough)
    # Let's use real agent but maybe we can just verify the update logic if we trust the agent.
    # To be safe, let's run the real agent for one article.
    
    editor = ChiefEditorAgent()
    print("🧠 Generating article...")
    article = editor.write_article(target_topic.get('Topic'), target_topic.get('大项分类'))
    
    if not article:
        print("❌ Article generation failed")
        return
        
    print("✅ Article generated.")
    
    # 3. Update Record
    fields = {
        "Title": article.get('title'),
        "HTML_Content": "<!-- Test Content -->" + article.get('html_content', '')[:50] + "...",
        "Status": config.STATUS_PENDING,
        "生成的文章摘要": article.get('summary'), # Ensure this key matches header? Header is "摘要"
        "摘要": article.get('summary'),
        "生成时间": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    record_id = target_topic.get('record_id')
    print(f"💾 Updating record {record_id}...")
    success = client.update_record(record_id, fields)
    
    if success:
        print("🎉 Update successful!")
        # Verify
        time.sleep(1)
        # Fetch back? 
        # Since ID is row:N, we can't easily fetch by ID without scanning, 
        # but we can fetch by Status=Pending to see if it appears.
    else:
        print("❌ Update failed")

if __name__ == "__main__":
    main()
