import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import config
from shared.google_client import GoogleSheetClient
from agents.social_manager import SocialManagerAgent

def run():
    print("\n" + "=" * 50)
    print("🤖 启动 Agentic Workflow (Step 4: Social Matrix)")
    print("=" * 50 + "\n")

    # 1. 初始化
    client = GoogleSheetClient()
    agent = SocialManagerAgent()
    base_time = datetime.now()
    
    # 2. 获取所有已发布的文章作为素材库
    # 注意：为了支持多平台分发，我们需要足够的素材。
    # 这里我们获取最近 100 篇 Published 文章。
    print("🔍 [System] 正在加载素材库 (Published Articles)...")
    source_records = client.fetch_records_by_status(status=config.STATUS_PUBLISHED, limit=100)
    print(f"📚 素材库就绪: {len(source_records)} 篇")
    
    if not source_records:
        print("❌ 素材库为空，无法生成社交内容。")
        return

    # 3. 遍历平台矩阵
    for p_key, p_conf in config.SOCIAL_PLATFORMS.items():
        p_name = p_conf['name']
        p_target = p_conf['daily_target']
        p_sheet = p_conf['sheet_name']
        
        print(f"\n🌊 [Platform] 开始处理平台: {p_name} (目标: {p_target}/天)")
        
        # 3.1 检查今日已生成数量
        # 获取该平台对应的 Sheet 数据
        sheet_obj = client._get_sheet(p_sheet)
        if not sheet_obj:
            print(f"   ❌ 无法获取工作表 {p_sheet}，跳过")
            continue
            
        all_rows = sheet_obj.get_all_records()
        today_str = base_time.strftime("%Y-%m-%d")
        
        today_count = 0
        for r in all_rows:
            # 假设有一个 '生成时间' 列
            gen_time = str(r.get('生成时间', ''))
            if today_str in gen_time:
                today_count += 1
                
        remaining_quota = p_target - today_count
        print(f"   📊 今日进度: {today_count}/{p_target} (剩余: {remaining_quota})")
        
        if remaining_quota <= 0:
            print(f"   ✅ 今日配额已满，跳过。")
            continue
            
        # 3.2 生成内容
        # 简单策略: 从素材库中按顺序找，直到填满配额
        # 进阶策略: 需要记录哪些文章在这个平台已经发过了？(目前暂不记录，假设素材库足够大或允许重复利用)
        # 为了避免总是发前几篇，我们可以随机 shuffle 素材库，或者记录已使用的 ID
        
        import random
        pool = list(source_records)
        random.shuffle(pool) # 随机打乱，增加多样性
        
        success_count = 0
        for record in pool:
            if success_count >= remaining_quota:
                break
                
            article_title = record.get("Title", "无标题")
            article_content = record.get("HTML_Content", "")
            
            # 基础完整性校验
            if not article_content or len(article_content) < 100:
                continue
                
            # --- Agent 生成 ---
            post_data = agent.create_social_post(article_title, article_content, p_key)
            # ----------------
            
            if post_data:
                # 3.3 持久化
                # [Data Integrity] 强校验
                if not post_data.get('title') or not post_data.get('content'):
                    print(f"   ⚠️ [Error] 生成内容无效，跳过保存")
                    continue
                
                post_time_str = base_time.strftime("%Y-%m-%d %H:%M:%S")
                
                # 构造符合该平台表头的数据
                # 所有平台 Sheet 结构统一初始化为:
                # ["Title", "Content", "Keywords", "Source", "Status", "Cover", "生成时间", "Link", "Post_Date"]
                new_record = {
                    "Title": post_data['title'],
                    "Content": post_data['content'], # 用户要求纯净文本，不含封面链接
                    "Keywords": post_data['keywords'],
                    "Source": post_data['source_title'], 
                    "Status": "Draft",
                    "Cover": post_data.get('cover_url', ''), # 保留字段但不生成
                    "生成时间": post_time_str
                }
                
                client.create_record(new_record, table_id=p_sheet)
                print(f"   💾 [System] 已保存至 {p_sheet}")
                
                success_count += 1
                
                # 随机间隔防止风控
                time.sleep(2)
                
        print(f"   🎉 {p_name} 任务完成，本次生成: {success_count} 篇")


if __name__ == "__main__":
    run()
