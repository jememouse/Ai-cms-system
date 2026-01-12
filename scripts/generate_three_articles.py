# scripts/generate_three_articles.py
import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient
from shared import config
from agents.chief_editor import ChiefEditorAgent

def main():
    print("🚀 启动批量文章生成任务 (Target: 3 Articles)...")
    client = GoogleSheetClient()
    editor = ChiefEditorAgent()
    
    # 1. Fetch Ready topics
    limit = 3
    print(f"☁️ 正在拉取 {limit} 个 'Ready' 状态的选题...")
    topics = client.fetch_records_by_status(config.STATUS_READY, limit=limit)
    
    if not topics:
        print("❌ 未找到 'Ready' 状态的选题。请确保 Step 1 已运行并生成了选题。")
        return
        
    print(f"📋 获取到 {len(topics)} 个选题，开始逐一生成...")
    
    success_count = 0
    
    for idx, topic_record in enumerate(topics):
        topic_text = topic_record.get('Topic')
        category = topic_record.get('大项分类', '未分类')
        record_id = topic_record.get('record_id')
        
        print(f"\n[{idx+1}/{len(topics)}] 正在生成: {topic_text} ({category})")
        
        # 2. Call Agent
        try:
            start_time = time.time()
            article = editor.write_article(topic_text, category)
            duration = time.time() - start_time
            
            if not article:
                print(f"   ❌ 生成失败: Agent 返回空")
                continue
                
            print(f"   ✅ 生成成功 (耗时 {duration:.1f}s)")
            
            # 3. Update Record
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fields = {
                "Title": article.get('title'),
                "HTML_Content": article.get('html_content'),
                "Status": config.STATUS_PENDING,
                "关键词": article.get('keywords'),
                "摘要": article.get('summary'),
                "描述": article.get('description'),
                "Tags": article.get('tags'),
                "生成时间": current_time,
                "One_Line_Summary": article.get('one_line_summary', ''),
                "Schema_FAQ": json.dumps(article.get('schema_faq', []), ensure_ascii=False),
                "Key_Points": json.dumps(article.get('key_points', []), ensure_ascii=False)
            }
            
            # 兼容：如果表头里有 "生成的文章摘要"，也填一下（之前脚本里有提到这个warn）
            # 但既然 sync_headers 已经确认了表头是 "摘要"，这里 "摘要" key 应该是对的。
            
            print(f"   💾 正在回写 Google Sheets (Row ID: {record_id})...")
            if client.update_record(record_id, fields):
                print(f"   🎉 写入成功！")
                success_count += 1
            else:
                print(f"   ❌ 写入失败")
                
        except Exception as e:
            print(f"   ❌ 发生异常: {e}")
            
        # 避免速率限制
        if idx < len(topics) - 1:
            wait_sec = 2
            print(f"   ⏳ 休息 {wait_sec} 秒...")
            time.sleep(wait_sec)
            
    print(f"\n✨ 任务结束。成功生成: {success_count}/{len(topics)} 篇")

if __name__ == "__main__":
    main()
