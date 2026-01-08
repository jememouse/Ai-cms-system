#!/usr/bin/env python3
"""
检查飞书中文章内容是否完整
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.feishu_client import FeishuClient
from shared import config

client = FeishuClient()

# 获取一条 Pending 状态的记录查看内容长度
records = client.fetch_records_by_status(config.STATUS_PENDING, limit=1)
if records:
    record = records[0]
    html_content = record.get("html_content", "")
    title = record.get("title", "")
    print(f"标题: {title}")
    print(f"内容长度: {len(html_content)} 字符")
    print(f"\n内容前500字符:\n{html_content[:500]}...")
    print(f"\n内容后500字符:\n...{html_content[-500:]}")
    
    # 检查关键结构是否存在
    print("\n" + "=" * 50)
    print("📋 内容结构检查")
    print("=" * 50)
    checks = [
        ("核心要点", "📌" in html_content or "核心要点" in html_content),
        ("FAQ 区块", "FAQ" in html_content or "常见问题" in html_content),
        ("一句话总结", "💡" in html_content or "一句话总结" in html_content),
        ("表格", "<table" in html_content),
        ("作者标记", "author-info" in html_content or "盒艺家技术团队" in html_content),
        ("图片", "<img" in html_content),
    ]
    for name, present in checks:
        status = "✅" if present else "❌"
        print(f"{status} {name}")
else:
    print("没有 Pending 状态的记录")
