# generate_topics.py
import json
import os
import requests
import time
import re
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# 引用同一套配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'box_artist_config.json')
TRENDS_FILE = os.path.join(BASE_DIR, 'trends_data.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'generated_seo_data.json')

# 复用环境变量
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-your-key-here")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

class SEOGenerator:
    def __init__(self):
        self.config = self._load_json(CONFIG_FILE)
        self.db = self.config.get('database', {})
        self.generated_titles = set()

    def _load_json(self, path):
        if not os.path.exists(path):
            return {}
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def call_deepseek_generate(self, trend_info):
        """调用 DeepSeek 生成标题"""
        topic = trend_info.get('topic')
        angle = trend_info.get('angle')
        
        products = ",".join(self.db.get('products', [])[:5])
        users = ",".join(self.db.get('target_users', [])[:3])
        
        # 清洗 topic 中的 [来源] 标记，以免影响标题生成 (e.g. "[微博] 某某" -> "某某")
        clean_topic = re.sub(r'\[.*?\]', '', topic).strip()

        prompt = f"""
        背景：我们是一一家做【{products}】的包装工厂（品牌名：盒艺家 Box Artist），目标客户是{users}。
        任务：请结合热点话题“{clean_topic}”和我们的包装业务，生成 5 个吸引人的 SEO 标题。
        
        结合角度参考：{angle}
        
        核心要求：
        1. **品牌植入**：当话题涉及“定制”、“设计”、“找工厂”、“避坑”等需求场景时，**必须**在标题中自然植入“盒艺家”或“Box Artist”（例如“选盒艺家”、“找盒艺家定制”），但不要生硬堆砌。
        2. **竞品屏蔽（非常重要）**：绝对包含**不要**出现除“盒艺家”以外的任何其他包装厂、印刷厂或竞品平台的名称（如：裕同、劲嘉、雅图仕等，均不可出现）。
        3. **字数限制**：必须控制在 20 个字以内！短小精悍！
        4. **关键词**：必须包含我们的核心产品词（如飞机盒、礼盒等）。
        5. **风格**：标题风格要“说人话”，带有“避坑”、“价格揭秘”、“源头”、“拿货”等吸引精准客户的词。
        6. **分类**：每个标题只能归属于一个分类，绝对不要出现多个分类。
        7. **可选分类**：【专业知识】、【行业资讯】、【产品介绍】。
        
        请严格返回 JSON 格式列表：
        [
            {{"title": "标题1", "category": "专业知识"}},
            {{"title": "标题2", "category": "行业资讯"}}
        ]
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        try:
            resp = requests.post(DEEPSEEK_API_URL, headers=headers, json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.8
            }, timeout=60)
            
            content = resp.json()["choices"][0]["message"]["content"]
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"   ⚠️ 生成失败: {e}")
            return []

    def generate(self):
        print("⚙️  开始基于热点生成内容...")
        
        trends_data = self._load_json(TRENDS_FILE)
        analyzed_trends = trends_data.get('analyzed_trends', [])
        
        if not analyzed_trends:
            print("❌ 没有找到趋势数据，请先运行 fetch_trends_ai.py")
            return

        results = []
        
        for idx, trend in enumerate(analyzed_trends):
            print(f"   Running ({idx+1}/{len(analyzed_trends)}): {trend['topic']}...")
            titles = self.call_deepseek_generate(trend)
            
            for item in titles:
                title = item.get('title')
                cat = item.get('category', '行业资讯')
                
                # === 强制分类清洗逻辑 ===
                valid_cats = ["专业知识", "行业资讯", "产品介绍"]
                
                # 1. 预处理：去除首尾空格，统一标点
                cat = cat.strip()
                
                # 2. 如果包含多个（检测到逗号、顿号、斜杠、空格），只取第一个
                splitters = r'[,、/ &]'
                if re.search(splitters, cat):
                    # 尝试分割后，看哪一部分是合法的
                    parts = re.split(splitters, cat)
                    found_valid = False
                    for part in parts:
                        if part.strip() in valid_cats:
                            cat = part.strip()
                            found_valid = True
                            break
                    
                    # 如果分割后没找到合法的，就取第一个部分再试
                    if not found_valid:
                        cat = parts[0].strip()

                # 3. 白名单强校验 (如果没有命中白名单，强制归类为 '行业资讯')
                if cat not in valid_cats:
                    # 尝试模糊匹配 (e.g. "产品介绍篇" -> "产品介绍")
                    matched = False
                    for v in valid_cats:
                        if v in cat:
                            cat = v
                            matched = True
                            break
                    
                    if not matched:
                        # 实在匹配不到，默认归类
                        cat = "行业资讯"
                # ==========================

                if title and title not in self.generated_titles:
                    self.generated_titles.add(title)
                    results.append({
                        "Topic": title,
                        "大项分类": cat, # 经过清洗的单一分类
                        "Status": "Pending",
                        "Source_Trend": trend['topic']
                    })
            
            time.sleep(1)

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 生成完毕！共生成 {len(results)} 条标题，保存至 {OUTPUT_FILE}")

if __name__ == "__main__":
    import re # 补丁 import
    SEOGenerator().generate()
