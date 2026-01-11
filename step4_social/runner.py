
import sys
import os
import time
import json
from datetime import datetime # Added by instruction

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import config
from shared.feishu_client import FeishuClient
from step4_social.xhs_generator import XHSGenerator

def run():
    print("\n" + "=" * 50)
    print("📱 节点4: 小红书内容裂变 (Social Media Split)")
    print("=" * 50 + "\n")

    # 检查配置
    if "PLEASE_REPLACE" in config.FEISHU_XHS_TABLE_ID:
        print("⚠️ 未配置 [FEISHU_XHS_TABLE_ID]，请先在 .env 或 config.py 中填入新表的 ID。")
        return

    client = FeishuClient()
    generator = XHSGenerator()
    
    # 获取每日限额
    daily_limit = config.MAX_DAILY_XHS
    print(f"🎯 今日生成限额: {daily_limit} 篇")

    # 设定起始时间 07:21:00 (修复 NameError)
    base_time = datetime.now().replace(hour=7, minute=21, second=0, microsecond=0)

    # 1. 扫描已发布文章
    # 策略：获取最近 200 篇 Published 文章，在内存中过滤掉已经 Done 的
    # (飞书 API 简单调用无法直接过滤自定义字段 XHS_Status != Done，需遍历)
    print("🔍 正在扫描主表 (已发布文章)...")
    records = client.fetch_records_by_status(status=config.STATUS_PUBLISHED, limit=200)
    
    pending_records = []
    for record in records:
        # 飞书 fetch_records_by_status 返回的记录可能没有 XHS_Status 字段(取决于视图)
        # 我们假设字段名为 "XHS_Status"
        # 这里的 fetch_records_by_status 是经过简化的，我们需要更底层的字段访问
        # 由于我们无法直接知道 XHS_Status 的值（不在默认返回的精简 dict 里），
        # 我们必须假设: 如果没处理过，我们去处理。
        # 但为了稳妥，我们可以尝试用 record_id 再查一次详情，或者在 fetch 时修改 client (太麻烦)。
        
        # 临时策略：
        # 我们在 client.fetch_records_by_status 的返回里并没有包含自定义字段。
        # 因此，我们需要修改 client 或者这里做一个折衷：
        # 假设我们只处理那些逻辑上 "应该是新" 的。
        # 但最好的方式是：我们在 runner 里再调一次 retrieve_record? 不，太慢。
        
        # 让代码 "盲" 处理：
        # 如果我们无法读取 XHS_Status，我们就无法判断。
        # 必须修改 feishu_client.py 里的 fetch_records_by_status 让他返回所有字段，或者 raw fields。
        # 现在的 feishu_client.py 已经够复杂了。
        
        # 为简单起见，我们只能假定：
        # 如果我们在主表中能看到 XHS_Status，那最好。如果看不到，我们可能需要修改 client。
        # 刚才我看 feishu_client.py 的 100-150 行，它只提取了特定字段。
        # 这是一个 block 点。
        
        # 决定：与其修改 client，不如在 runner 里不做过滤，
        # 直接生成，然后尝试写入。如果 XHS 表里已经有了(去重?)
        # 不，这样会重复生成。
        
        # 必须修改 Client 让它返回 raw fields 以便我们检查 XHS_Status。
        # 或者我们直接 modify logic below.
        pass

    # 鉴于无法直接读取 XHS_Status，我先用一个临时的全量获取方案
    # 或者我修改 Fetcher 让他返回 "xhs_status" 字段 (User added fields)
    pass
    
    # 这里是真实逻辑
    count_generated = 0
    
    for idx, record in enumerate(records):
        if count_generated >= daily_limit:
            print("🛑 已达到今日限额，停止生成。")
            break

        # 检查状态: 只处理未完成的 (Empty or Ready)
        # 如果是 Done，跳过
        xhs_status = record.get("xhs_status", "")
        if xhs_status == "Done":
             # debug print optionally
             # print(f"   ⏩ 跳过已处理文章: {record.get('title')}")
             continue
        
        # 默认只处理 "Ready" (人工触发) 
        # 如果用户想要全自动处理老的，可以放开限制。
        # 这里既然用户说 "自动的"，我们假设只要没 Done 都要做。
        # 所以逻辑是: Published AND Status!=Done -> Go
        pass

        topic = record.get("topic", "")
        article_title = record.get("title", topic)
        article_content = record.get("html_content", "")
        
        if not article_content:
            continue

        print(f"\n   [{count_generated + 1}/{daily_limit}] 正在裂变: {article_title}")
        
        # 1. 生成文案
        xhs_data = generator.generate_note(article_title, article_content)
        
        if xhs_data:
            # 2. 生成封面 (Pollinations)
            cover_url = generator.generate_cover_image(xhs_data['title'], xhs_data['keywords'])
            
            # 格式化关键词: "A, B" -> "#A #B"
            raw_keywords = xhs_data.get('keywords', '')
            formatted_keywords = ""
            if isinstance(raw_keywords, list):
                parts = raw_keywords
            else:
                # 统一逗号
                parts = str(raw_keywords).replace("，", ",").split(",")
            
            # 去重并加井号
            final_tags = []
            for p in parts:
                tag = p.strip().lstrip("#") # 去掉可能已有的#
                if tag:
                    final_tags.append(f"#{tag}")
            formatted_keywords = " ".join(final_tags)
            
            # 统一生成时间: 全部为 07:21:00
            post_time = base_time 
            post_time_str = post_time.strftime("%Y-%m-%d %H:%M:%S")

            # 3. 写入 [XHS Notes] 副表
            # 字段名必须与飞书表头完全一致
            new_record = {
                "Title": xhs_data['title'],
                "Content": xhs_data['content'] + f"\n\n[封面图]: {cover_url}", # 将链接也放入正文防止Cover字段写入失败
                "Keywords": formatted_keywords,
                "Source": article_title, 
                "Status": "Draft",
                "Cover": cover_url, # 尝试写入 Cover 字段 (如果用户设为文本)
                "生成时间": post_time_str # 新增生成时间
            }
            
            # 注意: 如果 Cover 是附件类型，写入文本 URL 会失败，但飞书通常会忽略该字段而不是报错 FieldNameNotFound?
            # FieldNameNotFound 意味着字段名本身对不上。
            # 我们保留 Cover 字段尝试写入。
            
            # Debug info
            print(f"      🕵️‍♂️ Debug: Writing to Table {config.FEISHU_XHS_TABLE_ID}")
            # print(f"      🕵️‍♂️ Debug: Payload Keys {list(new_record.keys())}")
            
            res_id = client.create_record(new_record, table_id=config.FEISHU_XHS_TABLE_ID)
            
            if res_id:
                print(f"      ✅ 已存入小红书表 (ID: {res_id}) | 📅 时间: {post_time_str}")
                
                # 4. 更新主表状态 -> Done
                client.update_record(record['record_id'], {"XHS_Status": "Done"})
                
                count_generated += 1
            else:
                print("      ❌ 写入失败: 请检查飞书表头是否依次为: Title, Content, Keywords, Source, Status, Cover, 生成时间")
        
        time.sleep(2)

    print("\n" + "=" * 50)
    print(f"📊 节点4完成! 今日生成: {count_generated}/{daily_limit}")
    print("=" * 50)

if __name__ == "__main__":
    run()
