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
        max_per_category: 每个分类最多处理几条 (默认 100，即处理全部)
    """
    if max_per_category is None:
        max_per_category = config.MAX_GENERATE_PER_CATEGORY
    
    print("\n" + "=" * 50)
    print("✍️  节点2: AI 文章生成")
    print("=" * 50 + "\n")
    
    client = FeishuClient()
    generator = ArticleGenerator()
    
    # 按分类获取 Ready 记录 (节点1完成的)
    all_records = []
    
    # 检查是否指定了单一分类运行 (并行策略)
    target_category = os.getenv("TARGET_CATEGORY")
    if target_category:
        print(f"🎯 并行模式: 仅处理 [{target_category}] 分类")
        categories_to_run = [target_category]
    else:
        categories_to_run = config.CATEGORY_MAP.keys()
        
    for category in categories_to_run:
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
    stats = {cat: 0 for cat in config.CATEGORY_MAP.keys()}
    
    for idx, record in enumerate(all_records):
        topic = record["topic"]
        category = record["category"]
        
        print(f"\n--- [{idx + 1}/{len(all_records)}] {category} | {topic[:20]}... ---")
        
        # 生成文章
        article = generator.generate(topic, category)
        
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
        }
        
        if client.update_record(record["record_id"], fields):
            print(f"   ✅ 已更新为 Pending")
            success_count += 1
            if category in stats:
                stats[category] += 1
        
        time.sleep(2)  # 避免 API 限速（增加到 2 秒）
    
    print("\n" + "=" * 50)
    print(f"📊 节点2完成! 总计生成 {success_count}/{len(all_records)} 篇文章")
    print("-" * 50)
    print("各分类生成统计:")
    for cat, count in stats.items():
        print(f"  - {cat}: {count} 篇")
    print("=" * 50)


if __name__ == "__main__":
    run()
