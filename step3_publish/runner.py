# step3_publish/runner.py
"""
节点3 执行器: 多账号发布到 WellCMS
从 publish_config.json 读取账号配置，按分类和数量发布
"""
import sys
import os
import json
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.feishu_client import FeishuClient
from shared import config
from .wellcms_rpa import WellCMSPublisher


def load_publish_config():
    """加载发布配置"""
    if not os.path.exists(config.PUBLISH_CONFIG_FILE):
        print(f"⚠️ 配置文件不存在: {config.PUBLISH_CONFIG_FILE}")
        return None
    
    with open(config.PUBLISH_CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def run(config_file: str = None):
    """
    执行节点3流程 - 多账号发布
    
    Args:
        config_file: 可选的配置文件路径
    """
    print("\n" + "=" * 50)
    print("📤 节点3: 多账号 RPA 发布到 WellCMS")
    print("=" * 50 + "\n")
    
    # 加载配置
    publish_config = load_publish_config()
    if not publish_config:
        return
    
    accounts = publish_config.get("accounts", [])
    interval = publish_config.get("interval_seconds", 30)
    
    if not accounts:
        print("⚠️ 没有配置任何账号")
        return
    
    print(f"📋 共 {len(accounts)} 个账号，每篇间隔 {interval} 秒\n")
    
    client = FeishuClient()
    
    total_success = 0
    total_fail = 0
    
    # 遍历每个账号
    for acc_idx, account in enumerate(accounts):
        username = account.get("username")
        password = account.get("password")
        categories = account.get("categories", {})
        
        print(f"\n{'='*40}")
        print(f"👤 账号 [{acc_idx + 1}/{len(accounts)}]: {username}")
        print(f"{'='*40}")
        
        # 创建该账号的发布器
        publisher = WellCMSPublisher(username=username, password=password)
        
        # 遍历该账号负责的分类
        for category, limit in categories.items():
            if limit <= 0:
                continue
            
            print(f"\n📂 分类: {category} (发布 {limit} 篇)")
            
            # 获取该分类的 Pending 记录
            records = client.fetch_records_by_status(
                status=config.STATUS_PENDING,
                category=category,
                limit=limit
            )
            
            if not records:
                print(f"   ⚠️ 没有待发布的文章")
                continue
            
            # 发布每篇文章
            for idx, record in enumerate(records):
                title = record.get("title") or record.get("topic", "")
                
                print(f"\n   [{idx + 1}/{len(records)}] {title[:30]}...")
                
                # 准备文章数据
                article = {
                    "title": title,
                    "html_content": record.get("html_content", ""),
                    "category_id": config.CATEGORY_MAP.get(category, "2"),
                    "summary": record.get("summary", ""),
                    "keywords": record.get("keywords", ""),
                    "description": record.get("description", ""),
                    "tags": record.get("tags", ""),
                }
                
                # RPA 发布
                print("      📤 正在发布...")
                published = publisher.publish_sync(article)
                
                if not published:
                    print("      ⚠️ 发布失败")
                    total_fail += 1
                    continue
                
                # 更新飞书状态
                if client.update_record(record["record_id"], {"Status": config.STATUS_PUBLISHED}):
                    print(f"      ✅ 已发布 -> Published")
                    total_success += 1
                
                # 间隔等待
                if idx < len(records) - 1:
                    print(f"      ⏳ 等待 {interval} 秒...")
                    time.sleep(interval)
    
    print("\n" + "=" * 50)
    print(f"📊 节点3完成!")
    print(f"   ✅ 成功: {total_success}")
    print(f"   ❌ 失败: {total_fail}")
    print("=" * 50)


if __name__ == "__main__":
    run()
