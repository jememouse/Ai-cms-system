import sys
import os
import requests
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient
from shared import config
from step4_social.xhs_generator import XHSGenerator

def run():
    print("🚀 开始重新生成笔记内容 (Regenerate)...")
    client = GoogleSheetClient()
    generator = XHSGenerator()
    
    # 1. 先获取主表原文 (此时 client.table_id 是 Main Table)
    print("🔍 扫描主表原文...")
    main_records = client.fetch_records_by_status(status=config.STATUS_PUBLISHED, limit=500)
    title_to_content = {}
    for r in main_records:
        title = r.get("title", "").strip()
        content = r.get("html_content", "")
        if title and content:
            title_to_content[title] = content
    print(f"📖 索引了 {len(title_to_content)} 篇文章内容")

    # 2. 切换到 XHS 表获取待更新记录
    # 临时覆盖 table_id 为 XHS 表
    client.table_id = config.FEISHU_XHS_TABLE_ID
    xhs_table_id = config.FEISHU_XHS_TABLE_ID
    
    print("🔍 扫描 XHS 记录...")
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{client.base_id}/tables/{xhs_table_id}/records/search"
    resp = requests.post(url, headers=client._headers(), json={"page_size": 500})
    
    if resp.json().get("code") != 0:
        print(f"❌ Error: {resp.text}")
        return
    xhs_items = resp.json().get("data", {}).get("items", [])
    print(f"📋 找到 {len(xhs_items)} 条待更新记录")
    
    updated_count = 0
    for item in xhs_items:
        fields = item['fields']
        rid = item['record_id']
        
        # 获取源标题
        source_title_obj = fields.get("Source", "")
        if isinstance(source_title_obj, list):
             source_title = source_title_obj[0]['text'] if source_title_obj else ""
        else:
             source_title = str(source_title_obj)
        
        source_title = source_title.strip()
        
        if not source_title:
            print(f"⚠️ 跳过 {rid}: Source 字段为空")
            continue
            
        if source_title not in title_to_content:
            print(f"⚠️ 跳过 {source_title}: 主表未找到对应原文")
            continue
            
        print(f"♻️ 正在重新生成: {source_title}")
        html_content = title_to_content[source_title]
        
        # 调用生成器 (使用新的 900字 Prompt)
        try:
            xhs_data = generator.generate_note(source_title, html_content)
            
            if xhs_data:
                # 重新组合数据，保留原有封面和时间，只更新 Title, Content, Keywords
                
                # 关键词格式化逻辑
                raw_keywords = xhs_data.get('keywords', '')
                formatted_keywords = ""
                # ... reuse format logic ...
                if isinstance(raw_keywords, list):
                    parts = raw_keywords
                else:
                    parts = str(raw_keywords).replace("，", ",").split(",")
                final_tags = []
                for p in parts:
                    tag = p.strip().lstrip("#")
                    if tag: final_tags.append(f"#{tag}")
                formatted_keywords = " ".join(final_tags)
                
                # 更新
                update_fields = {
                    "Title": xhs_data['title'],
                    "Content": xhs_data['content'] + f"\n\n[封面图]: {fields.get('Cover', '')}", # 保留原来的封面链接逻辑 (如果Cover字段读出来是string)
                    # 注意: 如果飞书里 Cover 是附件，fields.get('Cover') 返回的是 list[dict]。
                    # 我们之前写入的是 URL string 到 Cover字段。
                    # 如果用户没改字段类型，这里读出来应该是 List?
                    # 稳妥起见，我们不把封面链接拼接到content里了？或者只拼新的？
                    # 之前的 runner 逻辑是: Content + \n\n[封面图]: URL
                    # 如果我们重新生成 Content，封面图 URL 会丢失 (如果在Content里)。
                    # 我们需要从 fields 里把封面图 URL 找回来。
                    # 假设 Cover 字段存的是 URL string。
                    
                    "Keywords": formatted_keywords
                }
                
                # 尝试修复封面图链接丢失问题:
                # 获取旧封面图 URL
                old_cover = fields.get("Cover", "")
                cover_url_str = ""
                if isinstance(old_cover, list): # Attachment object
                    if old_cover: cover_url_str = old_cover[0].get("url", "")
                elif isinstance(old_cover, str):
                    cover_url_str = old_cover
                
                # 如果找不到，尝试从旧 Content 里正则提取? 太复杂。
                # 假设 generator.generate_cover_image 不需要重新跑 (省钱/省时间)
                # 直接拼接
                if cover_url_str and cover_url_str.startswith("http"):
                    update_fields["Content"] = xhs_data['content'] + f"\n\n[封面图]: {cover_url_str}"
                else:
                    # 如果没有封面图，可能需要重新生成? 
                    # 暂时保持 Content 原样
                    update_fields["Content"] = xhs_data['content']

                client.update_record(rid, update_fields)
                print(f"   ✅ 已更新")
                updated_count += 1
                time.sleep(1) # 限速
                
        except Exception as e:
            print(f"   ❌ 生成失败: {e}")

    print(f"🎉 全部完成: 更新了 {updated_count} 条记录")

if __name__ == "__main__":
    run()
