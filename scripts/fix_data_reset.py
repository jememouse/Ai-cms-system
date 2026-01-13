import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient

def fix_data():
    print("🚑 Starting Data Cleanup...")
    client = GoogleSheetClient()
    sheet = client._get_sheet("cms")
    
    if not sheet:
        print("❌ Failed to access sheet")
        return

    all_records = sheet.get_all_records()
    print(f"📋 Total Records Scanned: {len(all_records)}")
    
    # Track fixes
    rows_to_reset = []
    rows_to_delete = []
    
    for i, row in enumerate(all_records):
        row_num = i + 2
        status = str(row.get("Status", "")).strip()
        title = str(row.get("Title", "")).strip()
        content = str(row.get("HTML_Content", "")).strip()
        url = str(row.get("URL", "")).strip()
        topic = str(row.get("Topic", "")).strip()
        
        # 1. Reset invalid Published/Pending to Ready
        should_reset = False
        
        # Condition A: Published but empty URL/Content
        if status == "Published" and (not url or not content):
            should_reset = True
            
        # Condition B: Pending but empty Content
        elif status == "Pending" and (not content):
            should_reset = True
            
        if should_reset:
            print(f"   🔧 Marking Row {row_num} for RESET (Topic: {topic[:15]}...)")
            rows_to_reset.append(row_num)
            
        # 2. Cleanup Test Data
        if "Test Atomic Update" in topic or status == "Test_Updated_Atomic":
            print(f"   🗑️ Marking Row {row_num} for DELETION (Test Data)")
            rows_to_delete.append(row_num)

    # Execute Resets
    if rows_to_reset:
        print(f"\n🔄 Resetting {len(rows_to_reset)} records to 'Ready'...")
        # We process separately to be safe, though batch update_cells is better.
        # Let's use update_record for simplicity as we have the atomic fix now.
        for r_num in rows_to_reset:
            client.update_record(f"row:{r_num}", {
                "Status": "Ready",
                "Title": "",        # Clear potentially partial data
                "HTML_Content": "",
                "URL": "",
                "发布时间": "",
                "生成时间": ""      # Reset generated time so it looks new
            })
            print(f"   ✅ Row {r_num} reset.")
    else:
        print("\n✅ No records needed resetting.")

    # Execute Deletions
    if rows_to_delete:
        print(f"\n🗑️ Deleting {len(rows_to_delete)} test records...")
        # Delete from bottom up to avoid index shift issues
        for r_num in sorted(rows_to_delete, reverse=True):
            sheet.delete_rows(r_num)
            print(f"   ✅ Row {r_num} deleted.")
    else:
        print("\n✅ No test records to delete.")
        
    print("\n✨ Cleanup Complete!")

if __name__ == "__main__":
    fix_data()
