# scripts/test_step1_limited.py
import sys
import os
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from skills.topic_analyst import TopicAnalysisSkill
from shared.google_client import GoogleSheetClient
from shared import config

def main():
    print("🧪 启动小批量标题生成测试 (Target: ~6 Titles)...")
    
    # 1. 准备 Mock 数据
    mock_trend = {
        "topic": "环保茶叶礼盒定制",
        "angle": "绿色可持续包装趋势",
        "priority": "S"
    }
    mock_config = {"brand": {"name": "盒艺家"}}
    
    # 2. 调用 Skill 生成标题
    print(f"🧠 调用 LLM 生成标题，热点: {mock_trend['topic']}...")
    skill = TopicAnalysisSkill()
    
    # 直接调用内部方法 _generate_titles 避免触发 20个热点的自动补全逻辑
    titles = skill._generate_titles(mock_trend, mock_config)
    
    if not titles:
        print("❌ LLM 未返回任何标题")
        return
        
    print(f"✅ LLM 返回 {len(titles)} 个标题")
    
    # 3. 构造记录 (模拟 agent_runner 逻辑)
    records_to_upload = []
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    
    for t in titles:
        # 清洗分类
        category = skill._clean_category(t.get('category', ''))
        
        record = {
            "Topic": t['title'],
            "大项分类": category,
            "Status": config.STATUS_READY,
            # 测试重点：时间戳逻辑
            "选题生成时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
        }
        records_to_upload.append(record)
        print(f"   - [{category}] {t['title']}")

    # 4. 同步到 Google Sheets
    print(f"☁️ 正在同步 {len(records_to_upload)} 条记录到 Google Sheets (表: cms)...")
    client = GoogleSheetClient()
    
    # 使用 batch_create
    # 注意：AgentRunner 里是先去重再写入，这里直接写入用于测试
    success = client.batch_create_records(records_to_upload)
    
    if success:
        print("🎉 测试数据同步成功！")
    else:
        print("❌ 同步失败")

if __name__ == "__main__":
    main()
