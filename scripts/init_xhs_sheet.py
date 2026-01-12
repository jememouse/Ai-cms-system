# scripts/init_xhs_sheet.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient

def main():
    print("🚀 初始化 XHS 工作表...")
    client = GoogleSheetClient()
    
    # 获取 'xhs' 表 (会自动创建)
    # 这里的 "xhs" 即对应 config.FEISHU_XHS_TABLE_ID
    sheet = client._get_sheet("xhs")
    
    if sheet:
        print(f"✅ XHS 表检查通过: {sheet.title}")
        header = sheet.row_values(1)
        print(f"📝 表头: {header}")
        
        # 测试写入
        new_id = client.create_record({
            "Topic": "Test XHS Note",
            "Status": "Draft",
            "Note_Content": "This is a test note for XHS."
        }, table_id="xhs")
        print(f"✅ 测试写入 ID: {new_id}")
    else:
        print("❌ XHS 表初始化失败")

if __name__ == "__main__":
    main()
