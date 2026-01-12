#!/usr/bin/env python3
"""
重置脚本：将 'Pending' 状态的文章重置为 'Ready'
用于重新生成文章（例如应用新的 HTML 结构优化）
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.google_client import GoogleSheetClient
from shared import config
import time

def reset_pending_to_ready():
    client = GoogleSheetClient()
    
    # 1. 获取所有 Pending 记录
    print("🔍 正在查找 Pending 状态的记录...")
    records = client.fetch_records_by_status(config.STATUS_PENDING)
    
    if not records:
        print("✅ 没有找到 Pending 记录，无需重置。")
        return
    
    print(f"📋 找到 {len(records)} 条 Pending 记录，准备重置为 Ready...")
    print("⚠️  这将清除已生成的标题和内容，以便重新生成。5秒后开始...")
    time.sleep(5)
    
    count = 0
    for record in records:
        # 重置字段：状态改回 Ready，清空内容字段
        fields = {
            "Status": config.STATUS_READY,
            "HTML_Content": "",
            # "Title": "", # 标题通常是 Step 1 生成的 Topic ? 不，Title是文章标题。Topic是Step1输出。
            # Step 2 根据 Topic 生成 Title 和 Content。
            # 所以是否清空 Title 取决于 Title 是否完美。
            # 既然是重置，就全部清空吧。
            "Title": "",
            "摘要": "",
            "关键词": "",
            "描述": "",
            "One_Line_Summary": "",
            "Key_Points": "",
            "Schema_FAQ": ""
        }
        
        if client.update_record(record["record_id"], fields):
            print(f"   🔄 重置成功: {record.get('topic', 'Unknown')}")
            count += 1
        else:
            print(f"   ❌ 重置失败: {record.get('record_id')}")
            
    print(f"\n✅ 完成！共重置 {count} 条记录。")
    print("👉 请运行 ./run_step2.sh 重新生成高质量文章。")

if __name__ == "__main__":
    reset_pending_to_ready()
