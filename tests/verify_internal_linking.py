import sys
import os
import json
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from step2_article.generator import ArticleGenerator

def verify_internal_linking():
    print("🧪 Verifying Smart Internal Linking Logic...")
    
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ASSETS_FILE = os.path.join(BASE_DIR, "published_assets.json")
    BACKUP_FILE = os.path.join(BASE_DIR, "published_assets.json.bak")
    
    # 1. Backup existing assets
    if os.path.exists(ASSETS_FILE):
        shutil.copy(ASSETS_FILE, BACKUP_FILE)
        
    try:
        # 2. Seed Dummy Data
        print("\n[1] Seeding Dummy Assets...")
        dummy_assets = [
            {
                "title": "食品礼盒设计指南",
                "url": "https://heyijiapack.com/news/read-1001.html",
                "keywords": "礼盒,食品包装,设计",
                "summary": "关于食品礼盒设计的深度解析"
            },
            {
                "title": "飞机盒定制价格揭秘",
                "url": "https://heyijiapack.com/news/read-1002.html",
                "keywords": "飞机盒,价格,成本",
                "summary": "飞机盒成本计算公式"
            },
            {
                "title": "化妆品包装合规要求",
                "url": "https://heyijiapack.com/news/read-1003.html",
                "keywords": "化妆品,法规,合规",
                "summary": "解读最新的化妆品包装法规"
            }
        ]
        with open(ASSETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(dummy_assets, f, ensure_ascii=False)
            
        # 3. Test Link Finding
        print("\n[2] Testing Link Retrieval...")
        generator = ArticleGenerator()
        
        # Case A: Relevant Topic
        topic_a = "2026食品礼盒包装趋势"
        links_a = generator._find_related_links(topic_a)
        print(f"   Topic: {topic_a}")
        print(f"   Found Links: {[l['title'] for l in links_a]}")
        
        if len(links_a) > 0 and "食品礼盒设计指南" in [l['title'] for l in links_a]:
             print("   ✅ Case A Passed: Found relevant link.")
        else:
             print("   ❌ Case A Failed: Did not find expected link.")

        # Case B: Irrelevant Topic
        topic_b = "完全无关的物理学话题"
        links_b = generator._find_related_links(topic_b)
        print(f"   Topic: {topic_b}")
        print(f"   Found Links: {[l['title'] for l in links_b]}")
        
        if len(links_b) == 0:
             print("   ✅ Case B Passed: No irrelevant links found.")
        else:
             print("   ⚠️ Case B Warning: Found links (might be weak match).")

    finally:
        # 4. Restore Backup
        if os.path.exists(BACKUP_FILE):
            shutil.move(BACKUP_FILE, ASSETS_FILE)
            print("\nRestored original assets file.")
        elif os.path.exists(ASSETS_FILE):
             # If no backup existed (file was new), delete the dummy
             os.remove(ASSETS_FILE)

if __name__ == "__main__":
    verify_internal_linking()
