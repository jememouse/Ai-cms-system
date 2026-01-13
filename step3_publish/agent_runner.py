import sys
import os
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.publisher import PublisherAgent
from shared.google_client import GoogleSheetClient
from shared import config
from shared import stats


def load_publish_config():
    """加载发布配置 (优先环境变量，其次本地文件)"""
    # 1. 尝试从环境变量加载 (用于 GitHub Actions Secret)
    config_json = os.getenv("PUBLISH_CONFIG_JSON")
    if config_json:
        try:
            print("🔐 读取环境变量配置: PUBLISH_CONFIG_JSON")
            return json.loads(config_json)
        except json.JSONDecodeError as e:
            print(f"⚠️ 解析环境变量配置失败: {e}")
    
    # 2. 尝试从文件加载
    if os.path.exists(config.PUBLISH_CONFIG_FILE):
        try:
            with open(config.PUBLISH_CONFIG_FILE, 'r', encoding='utf-8') as f:
                print(f"📖 读取本地配置文件: {config.PUBLISH_CONFIG_FILE}")
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 读取配置文件失败: {e}")
            
    print(f"⚠️ 未找到有效配置")
    return None


def run():
    print("\n" + "=" * 50)
    print("🤖 启动 Agentic Workflow (Step 3: Publishing)")
    print("=" * 50 + "\n")
    
    # 加载配置获取账号信息
    publish_config = load_publish_config()
    accounts = publish_config.get("accounts", []) if publish_config else []
    
    # 使用第一个账号 (单账号模式)
    if accounts:
        first_account = accounts[0]
        username = first_account.get("username")
        password = first_account.get("password")
        print(f"👤 使用账号: {username}")
    else:
        username = None
        password = None
        print("⚠️ 未找到账号配置，将使用默认值")
    
    agent = PublisherAgent(username=username, password=password)
    client = GoogleSheetClient()
    
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
        print(f"\n--- [{idx + 1}/{len(pending_records)}] 发布: {record.get('Title', '')[:30]}... ---")
        
        # [Idempotency Check] 防止重复发布
        # 如果状态是 Pending 但已经有 URL，说明上次发布成功但状态更新失败
        existing_url = record.get('URL', '').strip()
        if existing_url and existing_url.startswith('http'):
            print(f"   ⚠️ 检测到该文章已有 URL ({existing_url})，判断为已发布。")
            print(f"   🔄 正在修复状态为 Published...")
            
            # 修复状态
            client.update_record(record['record_id'], {
                "Status": config.STATUS_PUBLISHED
            })
            
            # 同时也确保写入 asset，防止漏掉 SEO 内链
            article_data_fix = {
                "title": record.get('Title'),
                "url": existing_url,
                "keywords": record.get('关键词'),
                "category_id": config.CATEGORY_MAP.get(str(record.get('大项分类', '')).strip(), "1"),
                "summary": record.get('摘要')
            }
            _record_to_assets(article_data_fix, existing_url)
            
            print(f"   ✅ 状态修复完成，跳过本次重复发布。")
            continue
            
        # [Data Integrity] 发布前强校验
        title_chk = record.get('Title', '').strip()
        content_chk = record.get('HTML_Content', '').strip()
        
        if not title_chk or len(content_chk) < 50:
            print(f"   🛑 检测到无效内容 (Title: {bool(title_chk)}, Content Len: {len(content_chk)})")
            print(f"   🔄 正在将状态重置为 Ready 以便重新生成...")
            client.update_record(record['record_id'], {"Status": config.STATUS_READY})
            continue

        # 转换为 Skill 需要的格式
        article_data = {
            "title": record.get('Title'),
            "html_content": record.get('HTML_Content'),
            "category_id": config.CATEGORY_MAP.get(str(record.get('大项分类', '')).strip(), "1"),
            "summary": record.get('摘要'),
            "keywords": record.get('关键词'),
            "description": record.get('描述'),
            "tags": record.get('Tags')
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
            # Optimization: speed up for testing (5-15s)
            wait_time = random.uniform(5, 15)
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
