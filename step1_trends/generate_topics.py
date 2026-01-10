# trends_generator/generate_topics.py
"""
SEO 标题生成模块
"""
import json
import os
import requests
import time
import re
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# 文件路径 (指向项目根目录)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        # 加载历史标题用于去重
        self.history_titles = self._load_history_titles()
        
    def _load_history_titles(self):
        """加载历史生成的标题，用于去重"""
        history = set()
        # 从输出文件加载
        if os.path.exists(OUTPUT_FILE):
            try:
                with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        if item.get('Topic'):
                            history.add(item['Topic'])
            except:
                pass
        print(f"   📚 加载 {len(history)} 条历史标题用于去重")
        return history
    
    def _is_similar_title(self, new_title, threshold=0.7):
        """检查标题是否与历史标题过于相似"""
        new_words = set(new_title)
        for old_title in self.history_titles:
            old_words = set(old_title)
            if len(new_words & old_words) / max(len(new_words | old_words), 1) > threshold:
                return True
        return False

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

        # 获取品牌信息
        brand = self.config.get('brand', {})
        brand_name = brand.get('name', '盒艺家')
        website = brand.get('website', 'https://heyijiapack.com/')
        tagline = brand.get('tagline', '让每个好产品都有好包装')
        selling_points = self.config.get('selling_points', [])
        sp_text = '、'.join(selling_points[:5]) if selling_points else '3秒智能报价、1个起订、最快1天交付'

        prompt = f"""
        背景：我们是【{brand_name}】（{website}），定位于全品类包装在线定制电商。
        品牌口号：{tagline}
        核心卖点：{sp_text}
        主营产品：{products}
        目标客户：{users}
        
        任务：请结合热点话题"{clean_topic}"和我们的包装业务，生成 6 个吸引人的 SEO 标题。
        
        结合角度参考：{angle}
        
        【核心要求】
        1. **品牌植入规则（重要调整）**：
           - **绝大部分标题（5-6 个）不要提及"盒艺家"**，应该是纯 SEO 内容标题，自然吸引搜索流量。
           - **最多只能有 1 个标题植入"盒艺家"**，且仅限于以下场景：
             - 明确的找厂需求（如"哪家好"、"推荐厂家"）
           - 如果话题与找厂无关，则 6 个标题全部为纯内容标题，不植入任何品牌。
           - 原则：**内容为王，品牌隐身**，通过优质内容吸引流量而非硬推品牌。
        2. **竞品屏蔽（非常重要）**：绝对**不要**出现除"盒艺家"以外的任何其他包装厂、印刷厂或竞品平台的名称。
        3. **字数限制（极度严格）**：必须控制在 **16 个字以内**！严禁超过 18 字！如果太长会被截断，导致点击率为 0。
           - 正确示例："广州飞机盒定制：3天出货1个起订" (14字)
           - 错误示例："广州飞机盒定制哪家好？深入解析材质工艺与成本控制指南" (26字 - 太长！)
        4. **关键词**：必须包含我们的核心产品词（如飞机盒、礼盒等）。
        5. **风格**：标题风格要"说人话"，可带"避坑"、"价格揭秘"、"源头"、"拿货"等吸引精准客户的词。
        6. **分类**：每个标题只能归属于一个分类，绝对不要出现多个分类。
        7. **可选分类**：【专业知识】、【行业资讯】、【产品介绍】。
        8. **年份要求（重要）**：如果标题涉及年份，必须使用当前年份 **2026年**，绝对不要使用 2025、2024 等过时年份。
        
        【GEO 可引用性优化（2026新要求）】
        9. **搜索意图适配**：标题需匹配以下搜索意图之一：
           - **信息型**：如"XX是什么"、"XX有哪些类型"、"XX怎么选"
           - **商业型**：如"XX多少钱"、"XX哪家好"、"XX厂家推荐"
           - **导航型**：如"XX定制流程"、"XX在线报价"
        10. **疑问句式优先**：至少 2 个标题使用疑问句（如"？"结尾），更易被 AI 搜索引擎摘录为答案。
        11. **数字型标题**：至少 1 个标题包含具体数字（如"5种"、"3个步骤"、"10元起"）。
        12. **长尾关键词**：必须包含地域词或场景词（如"广州"、"电商专用"、"春节礼盒"）。
        13. **跨行业转化策略**：
           - 遇到下游行业展会（如"糖酒会"），必须转化为**包装解决方案**视角。
           - 错误："2026糖酒会开幕"
           - 正确："2026糖酒会新趋势：食品礼盒如何设计更吸睛？"
        
        【竞品词黑名单（严禁出现）】
        包你好、派派盒子、包装宝、一呼百盒、吉印通、万印网、阿里巴巴1688、天猫、京东、拼多多
        
        【高质量标题示例（Few-shot）】
        热点："春节年货消费趋势"
        示例输出：
        [
            {{"title": "2026年春节礼盒定制避坑指南", "category": "专业知识", "intent": "信息型"}},
            {{"title": "广州年货礼盒多少钱一个？", "category": "行业资讯", "intent": "商业型"}},
            {{"title": "找盒艺家定制年货礼盒3天出货", "category": "产品介绍", "intent": "导航型"}}
        ]
        
        热点："电商包装破损投诉"
        示例输出：
        [
            {{"title": "电商飞机盒防破损的5个技巧", "category": "专业知识", "intent": "信息型"}},
            {{"title": "抗压飞机盒怎么选不踩坑？", "category": "行业资讯", "intent": "商业型"}},
            {{"title": "江浙沪抗压飞机盒源头厂批发", "category": "产品介绍", "intent": "导航型"}}
        ]
        
        请严格返回 JSON 格式列表：
        [
            {{"title": "标题1", "category": "专业知识", "intent": "信息型"}},
            {{"title": "标题2", "category": "行业资讯", "intent": "商业型"}},
            {{"title": "标题3", "category": "产品介绍", "intent": "导航型"}}
            ...
        ]
        
        【数量分布要求（非常重要）】
        请务必保证生成的 6 个标题覆盖以下分类，分布如下：
        - 2 个【专业知识】（硬核干货、工艺解析）
        - 2 个【行业资讯】（市场趋势、价格行情、**所有展会/活动/峰会**）
        - 2 个【产品介绍】（特定盒型优势、应用场景）
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = requests.post(DEEPSEEK_API_URL, headers=headers, json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.8
                }, timeout=60)
                
                # 限流处理
                if resp.status_code == 429:
                    wait_time = (attempt + 1) * 5
                    print(f"   ⏳ API 限流，等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                
                if resp.status_code != 200:
                    print(f"   ⚠️ API 返回状态码: {resp.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return []
                
                content = resp.json()["choices"][0]["message"]["content"]
                content = content.replace("```json", "").replace("```", "").strip()
                return json.loads(content)
            except json.JSONDecodeError as e:
                print(f"   ⚠️ JSON 解析失败: {e}")
                return []
            except Exception as e:
                print(f"   ⚠️ 生成失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                return []
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
                        "Source_Trend": trend['topic'],
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
            
            time.sleep(1)

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"✅ 生成完毕！共生成 {len(results)} 条标题，保存至 {OUTPUT_FILE}")

if __name__ == "__main__":
    import re # 补丁 import
    SEOGenerator().generate()
