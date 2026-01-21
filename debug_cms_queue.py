
import sys
import os
import json
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.getcwd())

from shared.google_client import GoogleSheetClient
from shared import config

def debug_queue():
    print("🔍 Debugging CMS Queue Status...")
    client = GoogleSheetClient()
    
    # 1. Check all pending records without limit
    print(f"📡 Fetching records with Status='{config.STATUS_PENDING}'...")
    
    # We use the internal _get_sheet to count total raw rows to be sure
    sheet = client._get_sheet("cms")
    all_records = sheet.get_all_records()
    
    pending_count = 0
    ready_count = 0
    published_count = 0
    
    pending_samples = []
    
    for i, row in enumerate(all_records):
        status = str(row.get("Status", "")).strip()
        if status == config.STATUS_PENDING:
            pending_count += 1
            if len(pending_samples) < 3:
                pending_samples.append({
                    "row": i + 2,
                    "title": row.get("Title"),
                    "url": row.get("URL"),
                    "gen_time": row.get("生成时间")
                })
        elif status == config.STATUS_READY:
            ready_count += 1
        elif status == config.STATUS_PUBLISHED:
            published_count += 1
            
    print(f"📊 Stats:")
    print(f"   - Pending (待发布): {pending_count}")
    print(f"   - Ready   (待生成): {ready_count}")
    print(f"   - Published (已发布): {published_count}")
    print(f"   - Total Rows: {len(all_records)}")
    
    if pending_count > 0:
        print("\n🧐 First 3 Pending Articles Analysis:")
        for p in pending_samples:
            print(f"   Row {p['row']}:")
            print(f"     Title: {p['title']}")
            print(f"     URL:   {p['url']} (Should be empty!)")
            print(f"     Time:  {p['gen_time']}")
            
            # Check for Zombie state (Pending but has URL)
            if p['url'] and str(p['url']).startswith('http'):
                 print("     ⚠️ WARNING: This article is 'Pending' but has a URL. Step 3 might skip it or mark as Published without posting!")
    else:
        print("\n⚠️ NO Pending articles found. This explains why publishing skips!")

if __name__ == "__main__":
    debug_queue()
