
import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from step2_article.generator import ArticleGenerator

def test_full_flow():
    print("🚀 开始全分类生成测试...\n")
    generator = ArticleGenerator()
    
    test_cases = [
        {
            "category": "专业知识",
            "topic": "化妆品礼盒烫金工艺的温度控制与材料选择",
            "check_points": ["温度", "烫金", "ISO", "表格", "FAQ"]
        },
        {
            "category": "行业资讯",
            "topic": "2026年春节礼品包装市场趋势预测",
            "check_points": ["趋势", "2026", "表格", "FAQ", "地域"]
        },
        {
            "category": "产品介绍",
            "topic": "加厚特硬飞机盒",
            "check_points": ["材质", "硬度", "表格", "FAQ"]
        }
    ]
    
    results = {}
    
    for case in test_cases:
        cat = case["category"]
        topic = case["topic"]
        print(f"Testing [{cat}] Topic: {topic}...")
        
        start_time = time.time()
        article = generator.generate(topic, cat)
        duration = time.time() - start_time
        
        if article:
            print(f"   ✅ 生成成功 ({duration:.1f}s)")
            print(f"   📄 标题: {article.get('title')}")
            
            html = article.get('html_content', '')
            checks = case["check_points"]
            passed_checks = []
            
            # 通用检查
            if '<table' in html: passed_checks.append("表格")
            if 'FAQ' in html or '常见问题' in html: passed_checks.append("FAQ")
            
            # 地域词检查 (Geographic)
            geo_keywords = ['义乌', '广州', '深圳', '江浙沪', '上海', '北京']
            found_geo = [g for g in geo_keywords if g in html]
            if found_geo: passed_checks.append("地域")
            
            # 关键词检查
            for kw in checks:
                if kw in ["表格", "FAQ", "地域"]: continue
                if kw in html or kw in article.get('summary', ''):
                    passed_checks.append(kw)
            
            print(f"   🔍 检查点覆盖: {passed_checks}")
            
            # 专门检查专业知识的标准引用
            if cat == "专业知识":
                standards = ['ISO', 'GB', 'G7', 'FSC']
                found_stds = [s for s in standards if s in html]
                if found_stds:
                    print(f"   🏆 标准引用: {found_stds}")
                else:
                    print(f"   ❌ 缺少标准引用")
            
            results[cat] = "PASS"
        else:
            print("   ❌ 生成失败")
            results[cat] = "FAIL"
            
        print("-" * 40)
        time.sleep(2) # 模拟间隔
        
    print("\n📊 测试汇总:")
    for cat, res in results.items():
        print(f"  {cat}: {res}")

if __name__ == "__main__":
    test_full_flow()
