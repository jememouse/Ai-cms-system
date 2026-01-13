import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import config
from shared.google_client import GoogleSheetClient

def init_sheets():
    print("🚀 Initializing Social Media Matrix Sheets...")
    client = GoogleSheetClient()
    
    # Standard Headers for Social Content
    # 统一表头: 标题, 正文(含脚本/笔记), 关键词, 来源文章, 状态, 封面图, 生成时间, 这里还可以加 "Review_Link" 等
    headers = [
        "Title", 
        "Content", 
        "Keywords", 
        "Source", 
        "Status", 
        "Cover", 
        "生成时间", 
        "Link", 
        "Post_Date"
    ]
    
    platforms = config.SOCIAL_PLATFORMS
    
    for key, conf in platforms.items():
        sheet_name = conf['sheet_name']
        p_name = conf['name']
        
        print(f"\n🌊 Checking Sheet: [{p_name}] ({sheet_name})...")
        
        # Check if exists
        try:
            sheet = client.spreadsheet.worksheet(sheet_name)
            print(f"   ✅ Sheet already exists.")
            # Optional: check headers? 
            # Let's assume if it exists, it's fine, or we could strict check.
        except:
            print(f"   ⚠️ Sheet not found, creating...")
            try:
                new_sheet = client.spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)
                new_sheet.append_row(headers)
                print(f"   🎉 Created '{sheet_name}' with headers.")
            except Exception as e:
                print(f"   ❌ Failed to create '{sheet_name}': {e}")

    print("\n✨ All matrix sheets initialized.")

if __name__ == "__main__":
    init_sheets()
