import sys
import os
import requests
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.google_client import GoogleSheetClient
from shared import config

def run():
    print("🚀 开始迁移旧关键词...")
    client = GoogleSheetClient()
    # 临时覆盖 table_id 为 XHS 表
    client.table_id = config.FEISHU_XHS_TABLE_ID
    
    # 1. Fetch All Records from XHS Table
    # 直接调用 search 接口获取所有记录 (默认 limit 500 够用)
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{client.base_id}/tables/{client.table_id}/records/search"
    resp = requests.post(url, headers=client._headers(), json={"page_size": 500})
    
    if resp.json().get("code") != 0:
        print(f"❌ Fetch Error: {resp.text}")
        return
        
    items = resp.json().get("data", {}).get("items", [])
    print(f"📋 找到 {len(items)} 条记录")
    
    import re
    updated_count = 0
    for item in items:
        fields = item['fields']
        rid = item['record_id']
        raw_kw_obj = fields.get("Keywords", "")
        
        # 1. 解析真实文本
        kw_text = ""
        if isinstance(raw_kw_obj, list):
            kw_text = "".join([i.get('text', '') for i in raw_kw_obj if isinstance(i, dict)])
        else:
            kw_text = str(raw_kw_obj)
            
        # 2. 清洗数据 (含修复之前的错误)
        # 提取所有有效的中英文词汇 (忽略标点和 JSON 垃圾字符)
        # 假设关键词是中文、英文、数字组合
        # 如果包含 "text": 这种代码特征，说明是之前的脏数据，强行正则提取
        clean_text = kw_text
        if "text" in kw_text or "{" in kw_text:
            clean_text = kw_text # 直接从脏数据里提取
        
        # 正则提取所有标签候选项 (只要原本是词)
        # 匹配: 汉字, 字母, 数字
        candidates = re.findall(r"[\u4e00-\u9fa5a-zA-Z0-9]+", clean_text)
        
        # 过滤掉 JSON 关键字
        black_list = {"text", "type", "list", "dict", "None", "Keywords"}
        real_tags = []
        for c in candidates:
            if c not in black_list and len(c) > 1: # 忽略单个字符的噪音
                 real_tags.append(f"#{c}")
        
        # 3. 构造新格式
        new_kw = " ".join(real_tags)
        
        # 4. 判断是否需要更新
        # 只有当新格式与旧文本看起来不同 (忽略已有#和空格的差异) 时才更新
        # 简单判断: 如果旧文本包含 "text" 垃圾，必须更新
        # 或者旧文本没有 #
        should_update = False
        if "text" in kw_text or "{" in kw_text:
            should_update = True
        elif "," in kw_text or "，" in kw_text:
            should_update = True
        elif kw_text and not kw_text.strip().startswith("#"):
             should_update = True
             
        if should_update and new_kw:
             print(f"   🔄 修复/更新 {rid}: {kw_text[:20]}... -> {new_kw}")
             client.update_record(rid, {"Keywords": new_kw})
             updated_count += 1
    
    print(f"✅ 迁移完成，共更新 {updated_count} 条记录")

if __name__ == "__main__":
    run()
