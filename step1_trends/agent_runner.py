import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.trend_hunter import TrendHunterAgent

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, 'box_artist_config.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'generated_seo_data.json')

def run():
    print("\n" + "=" * 50)
    print("🤖 启动 Agentic Workflow (Step 1: Trend Hunting)")
    print("=" * 50 + "\n")
    
    # Load Config
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = {"mining_seeds": ["包装", "礼盒"]}
        
    hunter = TrendHunterAgent()
    topics = hunter.hunt_and_analyze(config)
    
    if topics:
        # Save results
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(topics, f, ensure_ascii=False, indent=2)
        print(f"💾 结果已保存至 {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
