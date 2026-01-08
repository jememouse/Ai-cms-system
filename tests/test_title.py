#!/usr/bin/env python3
"""
标题生成测试脚本
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from step1_trends.generate_topics import SEOGenerator
import json

def test_title_generation():
    print("=" * 50)
    print("🧪 标题生成测试")
    print("=" * 50)
    
    gen = SEOGenerator()
    result = gen.call_deepseek_generate({
        "topic": "[小红书] 春节送礼高级感包装",
        "angle": "年货礼盒消费趋势，年轻人追求颜值包装"
    })
    
    print("\n📝 生成结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # 质量检查
    print("\n" + "=" * 50)
    print("📋 质量检查")
    print("=" * 50)
    
    question_count = sum(1 for t in result if "？" in t.get("title", ""))
    number_count = sum(1 for t in result if any(c.isdigit() for c in t.get("title", "")))
    competitors = ["包你好", "派派盒子", "包装宝", "一呼百盒", "1688", "天猫", "京东"]
    has_competitor = any(c in str(result) for c in competitors)
    
    checks = [
        ("疑问句数量", question_count, ">=2", question_count >= 2),
        ("数字标题数量", number_count, ">=1", number_count >= 1),
        ("无竞品词", "无" if not has_competitor else "存在!", "无", not has_competitor),
        ("总标题数", len(result), "=6", len(result) == 6),
    ]
    
    for name, value, expected, passed in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {name}: {value} (期望{expected})")
    
    # 检查分类分布
    print("\n📊 分类分布:")
    categories = {}
    for t in result:
        cat = t.get("category", "未知")
        categories[cat] = categories.get(cat, 0) + 1
    for cat, count in categories.items():
        print(f"   - {cat}: {count} 个")

if __name__ == "__main__":
    test_title_generation()
