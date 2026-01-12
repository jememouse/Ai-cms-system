# scripts/add_new_columns.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient

def main():
    print("🔧 正在为 cms 表追加新列...")
    client = GoogleSheetClient()
    sheet = client._get_sheet("cms")
    
    if not sheet:
        print("❌ 无法获取 cms 表")
        return
        
    # 获取当前表头
    current_headers = sheet.row_values(1)
    print(f"📄 当前表头: {current_headers}")
    
    new_cols = ["选题生成时间", "生成时间"]
    added = []
    
    # 计算需要追加的列
    # 简单的做法：直接在最后追加不存在的列
    # 注意：这意味着如果中间有空列，可能会有点乱，但通常没问题
    
    # 找到最后一个非空列的索引
    last_col = len(current_headers)
    
    for col in new_cols:
        if col not in current_headers:
            # 写入新表头
            # gspread 的 update_cell 是 (row, col)，索引从1开始
            # 新列位置 = last_col + 1
            last_col += 1
            sheet.update_cell(1, last_col, col)
            added.append(col)
            print(f"✅ 已追加列: {col} (Col {last_col})")
        else:
            print(f"⚠️ 列 '{col}' 已存在，跳过")
            
    if added:
        print(f"🎉 成功追加 {len(added)} 个新列")
    else:
        print("🎉 没有新列需要追加")

if __name__ == "__main__":
    main()
