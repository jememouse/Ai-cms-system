import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from step2_article.generator import ArticleGenerator

def test_rag():
    print("🧪 开始 RAG 功能测试...")
    generator = ArticleGenerator()
    
    # 1. Test Search Directly
    queries = ["2026年上海国际包装展览会", "上海包装展", "DeepSeek"]
    
    for topic in queries:
        print(f"\n[Test] 尝试搜索: {topic}...")
        results = generator._search_web(topic)
        
        if results:
            print(f"✅ 搜索成功！(长度: {len(results)})")
            print("-" * 30)
            print(results[:200] + "..." if len(results) > 200 else results)
            print("-" * 30)
            break
        else:
            print(f"❌ 搜索 '{topic}' 无结果")

    # 2. Test Generation Trigger
    print(f"\n[Test 2] 测试生成触发逻辑 (Category: 行业资讯)...")
    # We won't actually call the expensive generating API for the full article if search failed, 
    # but let's assume we want to see the search log in the real flow.
    # To save time/tokens, we can just print that we are ready to call generate.
    # But checking if the code *would* trigger is best done by running it.
    
    if results:
        print("🚀 准备调用 DeepSeek API 生成文章 (这也是一次真实消耗)...")
        article = generator.generate(topic, "行业资讯")
        
        if article:
            print("\n" + "="*50)
            print(f"✅ 文章生成成功！标题: {article.get('title')}")
            print("-" * 30)
            print(f"摘要: {article.get('summary')}")
            print("-" * 30)
            print("🔍 检查 RAG 注入情况 (HTML 片段):")
            html = article.get('html_content', '')
            # 简单检查是否包含一些年份或特定词汇
            print(html[:500] + "...")
            print("="*50)
        else:
            print("❌ 文章生成失败")

if __name__ == "__main__":
    test_rag()
