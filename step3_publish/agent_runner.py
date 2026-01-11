import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.publisher import PublisherAgent
from shared.feishu_client import FeishuClient
from shared import config

def run():
    print("\n" + "=" * 50)
    print("🤖 启动 Agentic Workflow (Step 3: Publishing)")
    print("=" * 50 + "\n")
    
    agent = PublisherAgent()
    client = FeishuClient()
    
    # 1. 获取待发布文章 (Status='Generated')
    print("🔍 [System] 正在扫描待发布文章...")
    pending_records = client.fetch_records_by_status(status=config.STATUS_GENERATED, limit=5) # 每次限制5篇
    
    print(f"📋 发现 {len(pending_records)} 篇待发布文章")
    
    for record in pending_records:
        # 转换为 Skill 需要的格式
        article_data = {
            "title": record.get('title'),
            "html_content": record.get('html_content'),
            "category_id": config.CATEGORY_MAP.get(record.get('category'), "1"),
            "summary": record.get('summary'),
            "keywords": record.get('keywords'),
            "description": record.get('description'),
            "tags": record.get('tags')
        }
        
        # 2. Agent 发布
        published_url = agent.publish_article(article_data)
        
        if published_url:
            # 3. System Update Feishu
            client.update_record(record['record_id'], {
                "Status": config.STATUS_PUBLISHED,
                "URL": published_url,
                "发布时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            print(f"   💾 [System] 飞书状态已更新为 Published")
        
        time.sleep(5) # 间隔

if __name__ == "__main__":
    run()
