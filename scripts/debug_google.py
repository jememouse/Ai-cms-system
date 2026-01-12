import sys
import os
import traceback
import gspread
from oauth2client.service_account import ServiceAccountCredentials

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared import config

def main():
    print("🔎 Running Diagnostics...")
    print(f"File: {config.GOOGLE_CREDENTIALS_FILE}")
    print(f"Exists: {os.path.exists(config.GOOGLE_CREDENTIALS_FILE)}")
    
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(config.GOOGLE_CREDENTIALS_FILE, scope)
        client = gspread.authorize(creds)
        print("✅ Auth successful")
        
        print(f"Attempting to open Sheet ID: {config.GOOGLE_SHEET_ID}")
        # explicit try
        sheet = client.open_by_key(config.GOOGLE_SHEET_ID)
        print(f"✅ Open successful: {sheet.title}")
        
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    main()
