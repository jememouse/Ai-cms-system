import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.chief_editor import ChiefEditorAgent
from shared.feishu_client import FeishuClient
from shared import config

def run():
    print("\n" + "=" * 50)
    print("🤖 启动 Agentic Workflow (Step 2: Article Gen)")
    print("=" * 50 + "\n")
    
    # Init
    editor = ChiefEditorAgent()
    client = FeishuClient()
    
    # Load Topics (From Feishu for Persistence)
    print("☁️ 正在从飞书拉取 Ready 状态的选题...")
    
    # Fetch Ready topics from Feishu
    # Use pagination loop if needed, but for now we fetch up to MAX_GENERATE_PER_CATEGORY * 3 to be safe
    # We fetch by status 'Ready'
    
    pending_topics = client.fetch_records_by_status(config.STATUS_READY, limit=100)
    
    if not pending_topics:
        print("❌ 飞书中没有找到 Ready 状态的选题，请先运行 Step 1")
        return

    print(f"📋 从飞书获取到 {len(pending_topics)} 个 Ready 选题")
    
    # Load Config Limit
    max_limit = config.MAX_GENERATE_PER_CATEGORY
    print(f"⚙️  每分类处理上限: {max_limit}")

    # 3. 分组与 Round-Robin 排序
    # Group by Category
    from collections import defaultdict
    grouped_topics = defaultdict(list)
    for t in pending_topics:
        # Note: fetch_records_by_status returns dict with keys: record_id, topic, category...
        # We need to map them to the format expected below or adjust below code
        # The return dict keys are: record_id, topic, category, title, html_content...
        # We need 'Topic', '大项分类'
        
        # Mapping for compatibility
        t['Topic'] = t['topic']
        t['大项分类'] = t['category']
        
        cat = t.get('大项分类', '未分类')
        grouped_topics[cat].append(t)
    
    print("📊 待处理选题分布:")
    for cat, items in grouped_topics.items():
        print(f"   - {cat}: {len(items)} 条")
        
    # Round-Robin Merge
    sorted_topics = []
    from itertools import zip_longest
    # 取每个分类的前 max_limit 条
    lists = [items[:max_limit] for items in grouped_topics.values()]
    
    for items in zip_longest(*lists):
        for item in items:
            if item is not None:
                sorted_topics.append(item)
                
    print(f"🔄 均衡排序后共 {len(sorted_topics)} 条任务")
    
    import random
    from datetime import datetime
    
    # 4. Execute
    for idx, item in enumerate(sorted_topics):
        print(f"\n--- [{idx + 1}/{len(sorted_topics)}] {item['大项分类']} | {item['Topic'][:30]}... ---")
        
        article = editor.write_article(item['Topic'], item['大项分类'])
        
        if article:
            # Update Feishu Record (Status: Ready -> Pending)
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Fields to update
            fields = {
                "Title": article.get('title'),
                "HTML_Content": article.get('html_content'),
                "Status": config.STATUS_PENDING,
                "关键词": article.get('keywords'),
                "摘要": article.get('summary'),
                "描述": article.get('description'),
                "Tags": article.get('tags'),
                "生成时间": current_time, 
                # "选题生成时间": item.get('created_at', ''), # 选题时间已存在，无需更新
                "One_Line_Summary": article.get('one_line_summary', ''),
                "Schema_FAQ": json.dumps(article.get('schema_faq', []), ensure_ascii=False),
                "Key_Points": json.dumps(article.get('key_points', []), ensure_ascii=False)
            }
            
            # Check if we have record_id (From Feishu Fetch)
            record_id = item.get('record_id')
            if record_id:
                success = client.update_record(record_id, fields)
                if success:
                    print(f"   💾 已在飞书更新记录 (ID: {record_id}, Status: Pending)")
            else:
                # Fallback: Create new (Should not happen in new flow)
                client.create_record(fields)
                print("   ⚠️ 未找到 record_id，创建了新记录")
        
        # Random Interval
        # Optimization: 5-10s to avoid rate limit
        wait_time = random.uniform(5, 10)
        print(f"   ⏳ 等待 {wait_time:.1f} 秒...")
        time.sleep(wait_time)
        
    # Update JSON
    with open(INPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run()
