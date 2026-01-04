# step2_article/runner.py
"""
节点2 执行器: 从飞书读取 Ready -> AI 生成文章 -> 更新为 Pending
"""
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.feishu_client import FeishuClient
from shared import config
from .generator import ArticleGenerator


def run(max_per_category: int = None):
    """
    执行节点2流程
    
    Args:
        max_per_category: 每个分类最多处理几条 (默认从 config 读取)
    """
    if max_per_category is None:
        max_per_category = config.MAX_ARTICLES_PER_CATEGORY
    print("\n" + "=" * 50)
    print("✍️  节点2: AI 文章生成")
    print("=" * 50 + "\n")
    
    client = FeishuClient()
    generator = ArticleGenerator()
    
    # 按分类获取 Ready 记录 (节点1完成的)
    all_records = []
    for category in config.CATEGORY_MAP.keys():
        records = client.fetch_records_by_status(
            status=config.STATUS_READY,  # 读取 Ready 状态
            category=category,
            limit=max_per_category
        )
        all_records.extend(records)
    
    if not all_records:
        print("⚠️ 没有待处理的 Ready 记录")
        return
    
    print(f"\n📝 共获取 {len(all_records)} 条待生成文章\n")
    
    success_count = 0
    
    for idx, record in enumerate(all_records):
        topic = record["topic"]
        category = record["category"]
        
        print(f"\n--- [{idx + 1}/{len(all_records)}] {topic[:30]}... ---")
        
        # 生成文章
        article = generator.generate(topic, category)
        
        if not article:
            print("   ⚠️ 跳过此条")
            continue
        
        # 更新飞书
        fields = {
            "Status": config.STATUS_PENDING,  # 节点2完成: Pending
            "Title": article.get("title", ""),
            "HTML_Content": article.get("html_content", ""),
            "摘要": article.get("summary", ""),
            "关键词": article.get("keywords", ""),
            "描述": article.get("description", ""),
            "Tags": article.get("tags", ""),
        }
        
        if client.update_record(record["record_id"], fields):
            print(f"   ✅ 已更新为 Pending")
            success_count += 1
        
        time.sleep(1)  # 避免 API 限速
    
    print("\n" + "=" * 50)
    print(f"📊 节点2完成! 成功生成 {success_count}/{len(all_records)} 篇文章 (Status=Pending)")
    print("=" * 50)


if __name__ == "__main__":
    run()
