# scripts/sync_headers.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient

def sync_headers(client, sheet_name, expected_headers):
    print(f"🔧 检查工作表: {sheet_name} ...")
    sheet = client._get_sheet(sheet_name)
    if not sheet:
        print(f"❌ 无法获取 {sheet_name}")
        return

    current_headers = sheet.row_values(1)
    print(f"   当前表头: {current_headers}")
    
    # 找出缺失的列
    missing = [h for h in expected_headers if h not in current_headers]
    
    if not missing:
        print("   ✅ 表头完整，无需更新")
        return

    print(f"   ⚠️ 发现缺失列: {missing}")
    
    # 追加新列
    # 策略: 在当前最后一列之后追加
    # 注意: 如果表格中间有数据但第一行是空的（不太可能），row_values(1) 会截断。
    # 假设第一行是连续的 headers。
    
    next_col_idx = len(current_headers) + 1
    
    for col in missing:
        print(f"   ➕ 追加列: {col} -> Col {next_col_idx}")
        sheet.update_cell(1, next_col_idx, col)
        next_col_idx += 1
        
    print(f"   🎉 {sheet_name} 更新完成")

def main():
    print("🚀 开始同步表头...")
    client = GoogleSheetClient()
    
    # 1. CMS 表
    cms_headers = [
        "Topic", "Status", "大项分类", "Title", "HTML_Content", 
        "摘要", "关键词", "描述", "Tags", "Schema_FAQ", "One_Line_Summary",
        "Key_Points", "URL", "发布时间", "XHS_Status", "选题生成时间", "生成时间"
    ]
    sync_headers(client, "cms", cms_headers)
    
    # 2. XHS 表
    xhs_headers = ["Title", "Content", "Keywords", "Source", "Status", "Cover", "生成时间", "XHS_Link", "Post_Date"]
    sync_headers(client, "xhs", xhs_headers)

if __name__ == "__main__":
    main()
