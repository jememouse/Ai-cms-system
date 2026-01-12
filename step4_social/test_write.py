
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import config
from shared.google_client import GoogleSheetClient

def test_write():
    client = GoogleSheetClient()
    table_id = config.FEISHU_XHS_TABLE_ID
    print(f"🧪 Testing write to table: {table_id}")

    # Test 1: Only Title (Text)
    print("\n[Test 1] Writing only Title...")
    res = client.create_record({"Title": "Test Title 1"}, table_id=table_id)
    if res: print("✅ Success")
    else: print("❌ Failed")

    # Test 2: Title + Status (Select)
    print("\n[Test 2] Writing Title + Status...")
    res = client.create_record({"Title": "Test Title 2", "Status": "Draft"}, table_id=table_id)
    if res: print("✅ Success")
    else: print("❌ Failed")

    # Test 3: Title + Cover (Text) -> assuming user made it Text per debug output (Type 1)
    print("\n[Test 3] Writing Title + Cover...")
    res = client.create_record({"Title": "Test Title 3", "Cover": "http://example.com/img.jpg"}, table_id=table_id)
    if res: print("✅ Success")
    else: print("❌ Failed")
    
    # Test 4: All Fields
    print("\n[Test 4] Writing All Fields...")
    payload = {
        "Title": "Test Title 4",
        "Content": "Test Content",
        "Keywords": "Key, Word",
        "Source": "Source Str",
        "Status": "Draft",
        "Cover": "http://example.com/img.jpg"
    }
    res = client.create_record(payload, table_id=table_id)
    if res: print("✅ Success")
    else: print("❌ Failed")

if __name__ == "__main__":
    test_write()
