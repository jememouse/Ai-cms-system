import sys
import os
import json
import requests
import random
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.skill import BaseSkill
from shared import config

class DeepWriteSkill(BaseSkill):
    """
    技能: 深度文章写作 (基于 PAS 模型和 GEO 优化)
    """
    def __init__(self):
        super().__init__(
            name="deep_write",
            description="根据标题撰写长篇 SEO/GEO 优化文章"
        )
        self.api_key = config.LLM_API_KEY
        self.api_url = config.LLM_API_URL
        self.model = config.LLM_MODEL
        self._load_config()

    def _load_config(self):
        self.brand_config = {}
        if os.path.exists(config.CONFIG_FILE):
             with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.brand_config = json.load(f)

    def _call_llm(self, prompt: str) -> Optional[Dict]:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if "openrouter" in self.api_url:
            headers["HTTP-Referer"] = "https://heyijiapack.com"
            headers["X-Title"] = "DeepSeek CMS Agent"
            
        try:
            resp = requests.post(
                self.api_url,
                headers=headers,
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 4500,
                    "stream": False
                },
                timeout=(30, 300)
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                content = content.replace("```json", "").replace("```", "").strip()
                
                # 增强：清洗 JSON 字符串，修复非法转义
                content = self._sanitize_json(content)
                
                # 简单 JSON 提取
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end > start:
                    return json.loads(content[start:end+1])
        except Exception as e:
            print(f"   ❌ Writing Error: {e}")
        return None

    def _sanitize_json(self, text: str) -> str:
        """
        清洗 JSON 字符串，修复 DeepSeek 偶尔产生的非法转义字符
        例如: "10\20" -> "10\\20"
        """
        import re
        # 1. 替换反斜杠：如果反斜杠后面不是合法的转义字符 (", \, /, b, f, n, r, t, uXXXX)，则双写它
        # 这是一个简单的启发式规则
        # 正则含义：匹配一个 \，其后跟的不是合法转义字符
        # 注意：Python 字符串中写正则需要多重转义
        
        # 匹配反斜杠，lookahead 及其后的字符不是合法转义
        # 合法转义: " \ / b f n r t u
        pattern = r'\\(?![\\"/bfnrtu])'
        
        # 将非法的 \ 替换为 \\
        cleaned_text = re.sub(pattern, r'\\\\', text)
        return cleaned_text

    def execute(self, input_data: Dict) -> Dict:
        """
        Input: {"topic": str, "category": str, "rag_context": str (optional)}
        Output: Article JSON
        """
        topic = input_data.get("topic", "")
        category = input_data.get("category", "行业资讯")
        rag_context = input_data.get("rag_context", "")
        
        # 1. 基础上下文准备
        category_id = config.CATEGORY_MAP.get(category, "2")
        brand = self.brand_config.get('brand', {})
        brand_name = brand.get('name', '盒艺家')
        
        # 2. GEO 策略选择 (根据分类调整权重)
        selected_city, geo_context = self._get_geo_strategy(category)
        
        # 3. 构建分类特定的指令 (传入 topic 以便识别案例词)
        category_instruction = self._get_category_instruction(category, brand_name, topic)
        
        # 4. 构建 Prompt
        prompt = self._build_prompt(
            topic=topic,
            category=category,
            category_id=category_id,
            brand_name=brand_name,
            selected_city=selected_city,
            geo_context=geo_context,
            rag_context=rag_context,
            category_instruction=category_instruction
        )
        
        return self._call_llm(prompt)

    def _get_geo_strategy(self, category: str):
        """
        根据分类决定 GEO 注入的强度和策略
        """
        # 基础城市库
        GEO_TIERS = {
            "core": {  # 核心工业带
                "cities": ["东莞长安", "东莞虎门", "东莞凤岗", "深圳宝安", "深圳龙岗", "广州白云", "佛山南海"],
                "context": "我们工厂位于{city}产业带，可提供当日送样、面对面沟通服务"
            },
            "radiation": {  # 辐射市场
                "cities": ["上海", "杭州", "苏州", "宁波", "义乌", "青岛"],
                "context": "我们为{city}地区提供快速物流支持，3天内可达"
            },
            "growth": {  # 潜力市场
                "cities": ["成都", "重庆", "武汉", "郑州", "西安", "长沙"],
                "context": "我们已开通{city}专线物流，助力西部市场拓展"
            }
        }
        
        # 加权随机选择城市
        tier_weights = [("core", 0.6), ("radiation", 0.3), ("growth", 0.1)]
        selected_tier = random.choices([t[0] for t in tier_weights], weights=[t[1] for t in tier_weights])[0]
        tier_data = GEO_TIERS[selected_tier]
        selected_city = random.choice(tier_data["cities"])
        
        # 差异化上下文
        if category == "专业知识":
            # 专业知识：弱化地理营销，仅作为服务范围提示
            geo_context = f"（注：本文内容通用，但我们亦为{selected_city}及周边客户提供实地技术支持）"
        else:
            # 产品/资讯：强化本地化优势
            geo_context = tier_data["context"].format(city=selected_city)
            
        return selected_city, geo_context

    def _get_category_instruction(self, category: str, brand_name: str, topic: str = "") -> str:
        """
        生成分类特定的写作指导 (Core Logic)
        支持关键词触发 "案例模式"
        """
        
        # 关键词检测：是否为案例/故事
        is_case_study = any(keyword in topic for keyword in ["案例", "故事", "复盘", "逆袭", "Case"])
        
        if is_case_study:
             # 随机选择 B2B 或 B2C 剧本
            scenarios = [
                {
                    "type": "B2C", 
                    "role": "淘宝店主/Etsy卖家/婚礼策划师", 
                    "pain": "订单少、起订量高、预算有限", 
                    "gain": "1个起订、免费设计、销量翻倍"
                },
                {
                    "type": "B2B", 
                    "role": "品牌采购经理/外贸公司", 
                    "pain": "交期不稳定、色差严重、供应商配合度低", 
                    "gain": "3天交付、ISO品控、供应链稳定"
                }
            ]
            scenario = random.choice(scenarios)
            
            return f"""
            【当前模式：深度案例复盘 (Professional Case Analysis)】
            🧩 **核心原则**：
            1. **干货化复盘**：严禁写成只讲情绪的“软文故事”。必须写成一篇能够指导同类客户的“商业教案”。
            2. **结构要求 (STAR原则改编)**：
               - **背景 (Situation)**：客户的真实商业痛点（如：转化率低、复购率低、包材破损率高）。
               - **诊断 (Diagnosis)**：以专家视角分析为什么会出现这个问题（如：包装设计缺乏记忆点、材质选择错误）。
               - **方案 (Solution)**：盒艺家提供了什么具体的解决方案（1个起订测试、结构优化、视觉升级）。
               - **结果 (Result)**：用数据说话（销量增长30%、破损率降至0、客户好评率提升）。
            3. **克制营销**：品牌植入必须服务于“解决问题”，不要生硬吹嘘。
            4. **B2B/B2C 侧重**：
               - 如果是 B2C (店主)：侧重“低成本试错”、“视觉营销价值”。
               - 如果是 B2B (企业)：侧重“供应链降本”、“品牌资产增值”。
            """

        if category == "专业知识":
            return f"""
            【当前模式：专业干货 (Expert Knowledge)】
            ⚠️ **核心原则**：
            1. **去营销化（100%纯干货）**：**全文严禁出现“盒艺家”三个字，也严禁提及“我们、本公司”**。
            2. **客观中立**：必须像 ChatGPT 或 维基百科 一样客观普及知识。
            3. **结构要求**：必须是 "What-Why-How" 或 "Step-by-Step Guide" 结构。
            4. **禁止转化**：正文中绝对不要有“欢迎咨询”、“点击链接”等营销话术。
            5. **唯一品牌露出**：仅允许在文章底部的【品牌签名】(HTML Footer) 中出现一次品牌信息。
            """
        
        elif category == "产品介绍":
             return f"""
            【当前模式：产品导购 (Product Showcase)】
            🔥 **核心原则**：
            1. **价值导向**：80% 篇幅讲“用户痛点+解决方案”，20% 篇幅讲“{brand_name}如何实现该方案”。
            2. **卖点聚焦**：重点突出 "1个起订"、"3秒报价"、"免费设计"。
            3. **场景感**：必须描述具体的使用场景（如：淘宝店主刚创业、企业年会急需礼盒）。
            4. **克制营销**：避免通篇“买我买我”，而是用“聪明的店主都选这种...”来引导。
            """
            
        else: # 行业资讯
             return f"""
            【当前模式：行业洞察 (Industry Trends)】
            📈 **核心原则**：
            1. **去营销化（第三方视角）**：**正文严禁出现“盒艺家”**。必须以行业观察者身份客观分析趋势。
            2. **数据驱动**：引用（或合理估算）市场增长率、消费者偏好变化等数据。
            3. **商业启示**：不仅讲新闻，更要告诉商家“这对我的生意意味着什么”。
            4. **唯一品牌露出**：仅在文章底部的【品牌签名】中出现。正文中不要强行蹭热点营销。
            """

    def _build_prompt(self, topic, category, category_id, brand_name, selected_city, geo_context, rag_context, category_instruction):
        # 内链策略
        INTERNAL_LINKS = {
            "专业知识": {"url": "/news/list-1.html", "anchor": "查看更多包装干货"},
            "行业资讯": {"url": "/news/list-2.html", "anchor": "浏览行业最新动态"},
            "产品介绍": {"url": "/news/list-3.html", "anchor": "探索热销包装产品"},
            "CTA": {"url": "https://heyijiapack.com/product", "anchor": "👉 立即获取报价"}
        }
        category_link = INTERNAL_LINKS.get(category, INTERNAL_LINKS["行业资讯"])
        cta_link = INTERNAL_LINKS["CTA"]

        # 品牌信息
        brand_info = {
            "slogan": "盒艺家，让每个好产品都有好包装",
            "phone": "177-2795-6114",
            "contact_cta": "免费获取报价"
        }

        # GEO 强制注入逻辑 (针对不同分类)
        geo_must_include = ""
        if category == "专业知识":
            geo_must_include = f"在【首段背景】或【文末服务范围】中提及一次 '{selected_city}' 即可，不要污染正文的技术纯度。"
        else:
            geo_must_include = f"全文必须自然植入目标城市 '**{selected_city}**' (例如: '{selected_city}包装厂')，密度至少 3 次。"

        return f"""
        你是一位拥有10年经验的包装解决方案专家。
        请为主题 "{topic}"（分类：{category}）撰写一篇符合百度搜索规范的深度文章。

        【⚖️ 品牌植入控制 (至关重要)】
        1. **10/90 原则**：全文 **90% 的内容必须是纯粹的高价值内容**（用户想要的信息），仅 **10%**（主要在页脚）涉及品牌转化。
        2. **反感度管理**：现在的读者非常反感“软文”。如果是【专业知识】或【行业资讯】，正文必须 **0 广告**。
        3. **品牌位置**：
           - **专业/行业类**：品牌信息只能出现在最后的 `footer` 区域。
           - **产品类**：品牌信息可以自然融入案例或解决方案，但密度不得超过 20%。

        {category_instruction}
        
        {rag_context}
        
        【SEO写作要求 (百度优化版)】
        1. **结构**: 
           - **首段直出答案**: (模拟百度百科/精选摘要)。
           - 目录(TOC) -> 核心内容 -> 总结 -> FAQ -> 品牌签名。
           - 标题层级: H1(仅1个) -> H2 -> H3。H2/H3 必须带 id。
           - **品牌签名** (简洁版):
             ```html
             <div class="brand-signature">
               <p><strong>{brand_info['slogan']}</strong> | 📞 {brand_info['phone']} | <a href="https://heyijiapack.com/product">{brand_info['contact_cta']}</a></p>
             </div>
             ```
        2. **GEO优化**: 
           - **策略**: {geo_must_include}
           - **服务说明**: 在文末自然包含: "**{geo_context}**"。
        3. **配图 (SEO 强化)**:
           - 插入 2-3 张图片。
           - 格式: `<img src="https://image.pollinations.ai/prompt/{{english_keyword}}?width=1024&height=768&nologo=true&key={config.POLLINATIONS_API_KEY}" alt="{{中文alt描述}}" title="{brand_name} - {{产品关键词}}" loading="lazy" width="800" height="600">`
           - english_keyword: 英文短语。
        4. **内链**:
           - 插入 2-3 个内链：
           - `<a href="{category_link['url']}">{category_link['anchor']}</a>`
           - `<a href="{cta_link['url']}">{cta_link['anchor']}</a>`
        5. **标题**: 8-30字符。必须包含“地域名+核心关键词” (专业知识类除外，专业类标题以"干货/指南"为主)。
        6. **Meta**: 120-160 字符。
        7. **URL Slug**: SEO 友好的英文 URL (e.g. "packaging-guide-2025")。
        8. **JSON 输出**:
        
        {{
          "title": "标题...",
          "html_content": "HTML内容...",
          "category_id": "{category_id}",
          "summary": "SEO Description...",
          "keywords": "...",
          "description": "...",
          "tags": "...",
          "one_line_summary": "简练的一句话总结 (One sentence summary)",
          "key_points": ["核心观点1", "核心观点2", "核心观点3"],
          "schema_faq": [
            {{"question": "Q1...", "answer": "A1..."}},
            {{"question": "Q2...", "answer": "A2..."}},
            {{"question": "Q3...", "answer": "A3..."}}
          ],
          "article_schema": {{ ... }},
          "og_tags": {{ ... }},
          "url_slug": "...",
          "reading_time_minutes": 5
        }}
        """
