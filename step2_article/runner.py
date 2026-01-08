# step2_article/runner.py
"""
节点2 执行器: 从飞书读取 Ready -> AI 生成文章 -> 更新为 Pending
按分类轮询处理 (Round-Robin)，确保各分类均衡生成
"""
import sys
import os
import time
from datetime import datetime
from itertools import zip_longest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.feishu_client import FeishuClient
from shared import config
from .generator import ArticleGenerator


def run(max_articles: int = None):
    """
    执行节点2流程
    
    Args:
        max_articles: 最多处理几条 (默认 1000，即处理全部)
    """
    if max_articles is None:
        max_articles = config.MAX_GENERATE_PER_CATEGORY
    
    print("\n" + "=" * 50)
    print("✍️  节点2: AI 文章生成 (分类均衡模式)")
    print("=" * 50 + "\n")
    
    client = FeishuClient()
    generator = ArticleGenerator()
    
    # 1. 分别获取各个分类的 Ready 记录
    records_by_category = {}
    total_records_count = 0
    
    # 分类列表：专业知识、行业资讯、产品介绍
    categories = list(config.CATEGORY_MAP.keys())
    
    print("📋 正在按分类获取记录...")
    for category in categories:
        records = client.fetch_records_by_status(
            status=config.STATUS_READY,
            category=category,
            limit=max_articles  # 每个分类获取这么多，确保足够
        )
        records_by_category[category] = records
        count = len(records)
        print(f"   - {category}: {count} 条")
        total_records_count += count
    
    if total_records_count == 0:
        print("\n⚠️ 没有待处理的 Ready 记录")
        return
    
    # 2. Round-Robin 合并列表
    # 例如：[A1, A2], [B1, B2], [C1] -> [A1, B1, C1, A2, B2]
    all_records = []
    # 获取所有分类的记录列表
    lists = [records_by_category[cat] for cat in categories]
    # zip_longest 会把短的列表补 None，我们需要过滤掉 None
    for items in zip_longest(*lists):
        for item in items:
            if item is not None:
                all_records.append(item)
    
    print(f"\n📝 共获取 {len(all_records)} 条待生成文章（已按分类交替排序）\n")
    
    success_count = 0
    stats = {cat: 0 for cat in config.CATEGORY_MAP.keys()}
    
    for idx, record in enumerate(all_records):
        topic = record["topic"]
        category = record["category"]
        
        # 提取分类文本（兼容字典和字符串格式）
        if isinstance(category, dict):
            category_text = category.get("text", "未知分类")
        else:
            category_text = str(category) if category else "未知分类"
        
        print(f"\n--- [{idx + 1}/{len(all_records)}] {category_text} | {topic[:30]}... ---")
        
        # 生成文章
        article = generator.generate(topic, category_text)
        
        if not article:
            print("   ⚠️ 跳过此条")
            continue
        
        # 更新飞书
        # 注意：飞书文本字段需要字符串，JSON 数组需转换
        import json as json_lib
        schema_faq_str = json_lib.dumps(article.get("schema_faq", []), ensure_ascii=False) if article.get("schema_faq") else ""
        key_points_str = json_lib.dumps(article.get("key_points", []), ensure_ascii=False) if article.get("key_points") else ""
        
        # Tags 可能是列表或字符串，统一转为逗号分隔的字符串
        tags_raw = article.get("tags", "")
        if isinstance(tags_raw, list):
            tags_str = ", ".join(str(t) for t in tags_raw)
        else:
            tags_str = str(tags_raw) if tags_raw else ""
        
        # 当前时间（北京时间）
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        fields = {
            "Status": config.STATUS_PENDING,  # 节点2完成: Pending
            "Title": article.get("title", ""),
            "HTML_Content": article.get("html_content", ""),
            "摘要": article.get("summary", ""),
            "关键词": article.get("keywords", ""),
            "描述": article.get("description", ""),
            "Tags": tags_str,  # 已转换为字符串
            # 新增字段 (GEO 优化) - 已转换为字符串
            "Schema_FAQ": schema_faq_str,
            "One_Line_Summary": article.get("one_line_summary", ""),
            "Key_Points": key_points_str,
            # 时间记录
            "生成时间": current_time,
        }
        
        if client.update_record(record["record_id"], fields):
            print(f"   ✅ 已更新为 Pending (时间: {current_time})")
            success_count += 1
            if category_text in stats:
                stats[category_text] += 1
        
        import random
        wait = random.uniform(2, 4)
        print(f"   ⏳ 等待 {wait:.1f} 秒...")
        time.sleep(wait)  # 2-4秒随机等待
    
    print("\n" + "=" * 50)
    print(f"📊 节点2完成! 总计生成 {success_count}/{len(all_records)} 篇文章")
    print("-" * 50)
    print("各分类生成统计:")
    for cat, count in stats.items():
        if count > 0:
            print(f"  - {cat}: {count} 篇")
    print("=" * 50)


if __name__ == "__main__":
    run()
