import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.publisher import PublisherAgent
from shared.feishu_client import FeishuClient
from shared import config
from shared import stats

def run():
    print("\n" + "=" * 50)
    print("🤖 启动 Agentic Workflow (Step 3: Publishing)")
    print("=" * 50 + "\n")
    
    agent = PublisherAgent()
    client = FeishuClient()
    
    total_success = 0
    total_fail = 0
    
    # 1. 获取待发布文章 (Status='Pending')
    print("🔍 [System] 正在扫描待发布文章...")
    # 限制根据 Config
    limit = config.MAX_PUBLISH_PER_CATEGORY
    print(f"⚙️  发布上限: {limit} 篇")
    
    pending_records = client.fetch_records_by_status(status=config.STATUS_PENDING, limit=limit)
    
    print(f"📋 发现 {len(pending_records)} 篇待发布文章")
    
    import random
    
    for idx, record in enumerate(pending_records):
        print(f"\n--- [{idx + 1}/{len(pending_records)}] 发布: {record.get('title', '')[:30]}... ---")
        
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
            
            # 4. Asset Write-back (SEO Closed Loop)
            _record_to_assets(article_data, published_url)
            
            total_success += 1
            stats.record_published()
        else:
            total_fail += 1
            stats.record_failed()
        
        # Random Interval
        if idx < len(pending_records) - 1:
            # Optimization: 60-120s for SEO safety
            wait_time = random.uniform(60, 120)
            print(f"   ⏳ 等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)

    # 发送飞书通知
    if total_success > 0 or total_fail > 0:
        notify_content = f"**发布结果**\n- ✅ 成功: {total_success} 篇\n- ❌ 失败: {total_fail} 篇\n- ⏰ 时间: {time.strftime('%Y-%m-%d %H:%M')}\n\n{stats.get_summary()}"
        client.send_notification(
            title="📤 CMS 发布任务完成",
            content=notify_content
        )
        print(f"📢 已发送飞书通知 (成功: {total_success}, 失败: {total_fail})")

def _record_to_assets(article, url):
    """
    将已发布的文章记录到本地资产库，用于 SEO 内链
    """
    import json
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ASSETS_FILE = os.path.join(BASE_DIR, "published_assets.json")
    
    # 构造新记录
    new_record = {
        "title": article.get("title"),
        "url": url,
        "keywords": article.get("keywords"),
        "category_id": article.get("category_id"),
        "summary": article.get("summary"),
        "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        data = []
        if os.path.exists(ASSETS_FILE):
            with open(ASSETS_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except:
                    data = []
        
        # 简单去重 (按 URL)
        existing_idx = next((i for i, item in enumerate(data) if item.get("url") == url), -1)
        if existing_idx >= 0:
            data[existing_idx] = new_record
        else:
            data.append(new_record)
            
        with open(ASSETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"   📚 [SEO] 已收录至资产库 ({len(data)} 篇)")
        
    except Exception as e:
        print(f"   ⚠️ 资产库写入失败: {e}")

if __name__ == "__main__":
    run()
