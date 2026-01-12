# scripts/test_timestamp.py
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient
from shared import config

def main():
    print("🚀 测试时间戳写入...")
    client = GoogleSheetClient()
    
    # 构建包含“选题生成时间”的记录
    now_str = time.strftime("%Y-%m-%d %H:%M:%S")
    topic_time = "2024-01-01 12:00:00" # Fake past time to distinguish from system time
    
    record = {
        "Topic": "Test Timestamp Row",
        "Status": "Draft",
        "选题生成时间": topic_time,
        "生成时间": "" # Should be auto-filled by client
    }
    
    print(f"📝 写入数据: {record}")
    
    # 写入 cms 表
    client.create_record(record, table_id="cms")
    
    print("✅ 写入完成，请检查 Google Sheet 最新一行")
    print(f"   预期 [选题生成时间]: {topic_time}")
    print(f"   预期 [生成时间]: (Current System Time)")

if __name__ == "__main__":
    main()
