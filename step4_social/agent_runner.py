import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import config
from shared.feishu_client import FeishuClient
from agents.social_manager import SocialManagerAgent

def run():
    print("\n" + "=" * 50)
    print("🤖 启动 Agentic Workflow (Step 4 Refactored)")
    print("=" * 50 + "\n")

    # 1. 初始化基础设施
    client = FeishuClient()
    agent = SocialManagerAgent() # 我们的主角
    
    daily_limit = config.MAX_DAILY_XHS
    base_time = datetime.now().replace(hour=7, minute=21, second=0, microsecond=0)
    
    # 2. 获取任务 (从飞书)
    print("🔍 [System] 正在扫描待处理文章...")
    records = client.fetch_records_by_status(status=config.STATUS_PUBLISHED, limit=200)
    
    count_generated = 0
    
    # 3. Agent 工作循环
    for record in records:
        if count_generated >= daily_limit:
            print("🛑 [System] 今日限额已达，下班啦")
            break

        # 检查状态
        xhs_status = record.get("xhs_status", "")
        if xhs_status == "Done":
             continue
             
        article_title = record.get("title", "无标题")
        article_content = record.get("html_content", "")
        
        if not article_content:
            continue
            
        # --- 让 Agent 干活 ---
        post_data = agent.create_xhs_post(article_title, article_content)
        # -------------------
        
        if post_data:
            # 4. 系统负责持久化 (System Action)
            # Agent 只负责生产内容，Runner/Workflow 负责 IO 写入，这也是一种解耦
            
            post_time_str = base_time.strftime("%Y-%m-%d %H:%M:%S")
            
            new_record = {
                "Title": post_data['title'],
                # 将封面图拼接到正文，防止字段写入失败
                "Content": post_data['content'] + f"\n\n[封面图]: {post_data['cover_url']}", 
                "Keywords": post_data['keywords'],
                "Source": post_data['source_title'], 
                "Status": "Draft",
                "Cover": post_data['cover_url'],
                "生成时间": post_time_str
            }
            
            res_id = client.create_record(new_record, table_id=config.FEISHU_XHS_TABLE_ID)
            
            if res_id:
                print(f"   💾 [System] 已保存至飞书 (ID: {res_id})")
                client.update_record(record['record_id'], {"XHS_Status": "Done"})
                count_generated += 1
            else:
                print("   ❌ [System] 保存失败")
        
        time.sleep(0.5)

if __name__ == "__main__":
    run()
