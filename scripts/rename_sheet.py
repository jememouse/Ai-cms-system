import sys
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import config

def rename_sheet():
    print(f"🔧 Attempting to rename worksheet to '{config.GOOGLE_WORKSHEET_NAME}'...")
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    
    spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID)
    
    # Check if 'cms' already exists
    try:
        cms_sheet = spreadsheet.worksheet(config.GOOGLE_WORKSHEET_NAME)
        print(f"✅ Worksheet '{config.GOOGLE_WORKSHEET_NAME}' already exists.")
        return
    except gspread.WorksheetNotFound:
        pass

    # If not, rename the first sheet (usually 'Sheet1' or '工作表1')
    try:
        first_sheet = spreadsheet.sheet1
        old_name = first_sheet.title
        print(f"📝 Renaming '{old_name}' -> '{config.GOOGLE_WORKSHEET_NAME}'")
        first_sheet.update_title(config.GOOGLE_WORKSHEET_NAME)
        print("✅ Rename successful!")
    except Exception as e:
        print(f"❌ Rename failed: {e}")

if __name__ == "__main__":
    rename_sheet()
