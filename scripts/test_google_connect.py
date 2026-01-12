# scripts/test_google_connect.py
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.google_client import GoogleSheetClient

def main():
    print("🚀 开始测试 Google Sheets 连接...")
    
    client = GoogleSheetClient()
    if not client.client:
        print("❌ 连接失败，请检查 service_account.json 和网络。")
        return
        
    print(f"✅ 连接成功!")
    print(f"📄 当前工作表: {client.worksheet_name}")
    
    # 1. 尝试写入一条测试记录
    print("\n[Test 1] 创建记录...")
    test_data = {
        "Topic": "Test Connectivity",
        "Status": "Test",
        "Title": "This is a test row from migration script",
        "大项分类": "System Test"
    }
    
    record_id = client.create_record(test_data)
    if record_id:
        print(f"✅ 创建成功, ID: {record_id}")
    else:
        print("❌ 创建失败")
        
    # 2. 尝试读取
    print("\n[Test 2] 读取记录...")
    records = client.fetch_records_by_status("Test", limit=1)
    if records:
        print(f"✅ 读取成功: {records[0].get('Title')}")
    else:
        print("⚠️ 未读取到 Test 状态记录")
        
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
