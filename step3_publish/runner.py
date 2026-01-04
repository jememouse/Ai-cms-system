# step3_publish/runner.py
"""
节点3 执行器: 从飞书读取 Pending -> RPA 发布 -> 更新为 Published
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.feishu_client import FeishuClient
from shared import config
from .wellcms_rpa import WellCMSPublisher


def run(max_per_category: int = 2):
    """
    执行节点3流程
    
    Args:
        max_per_category: 每个分类最多发布几条
    """
    print("\n" + "=" * 50)
    print("📤 节点3: RPA 发布到 WellCMS")
    print("=" * 50 + "\n")
    
    client = FeishuClient()
    publisher = WellCMSPublisher()
    
    # 按分类获取 Pending 记录 (节点2完成的)
    all_records = []
    for category in config.CATEGORY_MAP.keys():
        records = client.fetch_records_by_status(
            status=config.STATUS_PENDING,  # 读取 Pending 状态
            category=category,
            limit=max_per_category
        )
        all_records.extend(records)
    
    if not all_records:
        print("⚠️ 没有待发布的 Pending 记录")
        return
    
    print(f"\n📝 共获取 {len(all_records)} 条待发布文章\n")
    
    success_count = 0
    
    for idx, record in enumerate(all_records):
        title = record.get("title") or record.get("topic", "")
        
        print(f"\n--- [{idx + 1}/{len(all_records)}] {title[:30]}... ---")
        
        # 准备文章数据
        article = {
            "title": title,
            "html_content": record.get("html_content", ""),
            "category_id": config.CATEGORY_MAP.get(record.get("category", ""), "2"),
            "summary": record.get("summary", ""),
            "keywords": record.get("keywords", ""),
            "description": record.get("description", ""),
            "tags": record.get("tags", ""),
        }
        
        # RPA 发布
        print("   📤 正在发布...")
        published = publisher.publish_sync(article)
        
        if not published:
            print("   ⚠️ 发布失败，跳过")
            continue
        
        # 更新飞书状态
        if client.update_record(record["record_id"], {"Status": config.STATUS_PUBLISHED}):
            print(f"   ✅ 已更新为 Published")
            success_count += 1
        
        time.sleep(2)  # 避免发布过快
    
    print("\n" + "=" * 50)
    print(f"📊 节点3完成! 成功发布 {success_count}/{len(all_records)} 篇文章")
    print("=" * 50)


if __name__ == "__main__":
    run()
