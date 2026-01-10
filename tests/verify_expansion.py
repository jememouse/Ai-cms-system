import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from step1_trends.generate_topics import SEOGenerator

def verify_expansion():
    print("🧪 Verifying Industry Expansion Logic...")
    
    # 1. Verify Config
    print("\n[1] Checking Config...")
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'box_artist_config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    mining_seeds = config.get("mining_seeds", [])
    
    target_kws = ["糖酒会", "美博会", "跨境电商选品会"]
    found = [kw for kw in target_kws if kw in mining_seeds]
    
    if len(found) == len(target_kws):
        print(f"✅ Config check passed. Found: {found}")
    else:
        print(f"❌ Config check failed. Found: {found}, Expected: {target_kws}")
        return

    # 2. Verify Title Generation Prompt Logic (Simulated)
    print("\n[2] Testing Title Generation for Downstream Event...")
    generator = SEOGenerator()
    
    # Simulating a trend found in the "Sugar and Wine Fair"
    mock_trend = {
        "topic": "2026成都糖酒会",
        "angle": "食品礼盒包装需求爆发",
        "priority": "S"
    }
    
    print(f"   Input Trend: {mock_trend['topic']}")
    print("   Calling DeepSeek to generate titles (this consumes tokens)...")
    
    titles = generator.call_deepseek_generate(mock_trend)
    
    if titles:
        print("\n✅ Generated Titles:")
        for t in titles:
            print(f"   - [{t.get('category')}] {t.get('title')}")
            
        # Check if titles are packaging-related
        packaging_keywords = ["包装", "礼盒", "设计", "定制"]
        relevant_titles = [t for t in titles if any(k in t.get('title', '') for k in packaging_keywords)]
        if len(relevant_titles) > 0:
            print(f"\n✅ Relevance Check: {len(relevant_titles)}/{len(titles)} titles contain packaging keywords.")
        else:
            print("\n❌ Relevance Check Failed: Titles do not verify packaging connection.")
    else:
        print("❌ Generation failed.")

if __name__ == "__main__":
    verify_expansion()
