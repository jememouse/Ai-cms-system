
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from skills.deep_writer import DeepWriteSkill

def test_deep_writer_title():
    print("=" * 50)
    print("🧪 DeepWriter Article Generation Test (Title Length & SEO)")
    print("=" * 50)
    
    skill = DeepWriteSkill()
    
    # Test Case
    topic = "月饼礼盒定制厂家"
    category = "行业资讯"
    
    print(f"📝 Input Topic: {topic}")
    print(f"📂 Category: {category}")
    print("🚀 Generating... (Please wait ~20s)")
    
    result = skill.execute({
        "topic": topic,
        "category": category
    })
    
    if not result:
        print("❌ Generation Failed (None returned)")
        return
        
    title = result.get('title', '')
    print(f"\n✅ Generated Title: {title}")
    print(f"📏 Length: {len(title)} chars")
    
    # Constraints Check
    checks = []
    
    # Check 1: Length (8-30)
    checks.append({
        "name": "Title Length (8-30)",
        "passed": 8 <= len(title) <= 30,
        "detail": f"Actual: {len(title)}"
    })
    
    # Check 2: SEO Keywords (Heuristic)
    seo_keywords = ["定制", "厂家", "价格", "直销", "设计", "包装", "月饼"]
    matched = [kw for kw in seo_keywords if kw in title]
    checks.append({
        "name": "SEO Keywords Presence",
        "passed": len(matched) >= 1,
        "detail": f"Matched: {matched}"
    })
    
    print("\n🔍 Verification Results:")
    all_passed = True
    for c in checks:
        icon = "✅" if c['passed'] else "❌"
        print(f"   {icon} {c['name']} -> {c['detail']}")
        if not c['passed']:
            all_passed = False
            
    if all_passed:
        print("\n🎉 All constraints passed!")
    else:
        print("\n⚠️ Some constraints failed. Please review.")

if __name__ == "__main__":
    test_deep_writer_title()
