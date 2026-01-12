# scripts/delete_column.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient

def main():
    print("🗑️ 正在删除 cms 表的第一列 (record_id)...")
    client = GoogleSheetClient()
    sheet = client._get_sheet("cms")
    
    if not sheet:
        print("❌ 无法获取 cms 表")
        return
        
    # 获取表头以确认第一列通常是 record_id
    current_headers = sheet.row_values(1)
    if not current_headers:
        print("❌ 表头为空")
        return

    first_col = current_headers[0]
    print(f"🧐 第一列标题: '{first_col}'")
    
    if first_col == "record_id":
        try:
            # delete_columns(start_index, end_index) - indices are likely 1-based or 0-based?
            # gspread API: delete_columns(start_index, end_index=None)
            # Deletes columns from the worksheet at the specified index.
            # Index is 1-based? Usually gspread uses 1-based for cells, but let's check.
            # Documentation says: index (int) – Index of a column to delete.
            
            # Let's try 1.
            sheet.delete_columns(1)
            print("✅ 成功删除第 1 列")
            
            # 验证新表头
            new_headers = sheet.row_values(1)
            print(f"📝 新表头: {new_headers}")
            
        except Exception as e:
            print(f"❌ 删除失败: {e}")
    else:
        print(f"⚠️ 第一列不是 'record_id' (是 '{first_col}')，跳过删除以免误删")

if __name__ == "__main__":
    main()
