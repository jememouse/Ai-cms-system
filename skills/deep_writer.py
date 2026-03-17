import sys
import os
import json
import random
import logging
from datetime import datetime
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.skill import BaseSkill
from shared import config, llm_utils

# 配置 logger
logger = logging.getLogger(__name__)

class DeepWriteSkill(BaseSkill):
    """
    技能: 深度文章写作 (基于 PAS 模型和 GEO 优化)
    """
    def __init__(self):
        super().__init__(
            name="deep_write",
            description="根据标题撰写长篇 SEO/GEO 优化文章"
        )
        self._load_config()

    def _load_config(self):
        self.brand_config = {}
        if os.path.exists(config.CONFIG_FILE):
             with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.brand_config = json.load(f)

    def execute(self, input_data: Dict) -> Dict:
        """
        Input: {"topic": str, "category": str, "rag_context": str (optional)}
        Output: Article JSON
        """
        topic = input_data.get("topic", "")
        category = input_data.get("category", "行业资讯")
        source_trend = input_data.get("source_trend", "")
        rag_context = input_data.get("rag_context", "")
        
        # 1. 基础上下文准备
        category_id = config.CATEGORY_MAP.get(category, "2")
        brand = self.brand_config.get('brand', {})
        brand_name = brand.get('name', '盒艺家')
        
        # 2. GEO 策略选择 (根据分类调整权重)
        selected_city, geo_context, industry_focus = self._get_geo_strategy(category)
        
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
            industry_focus=industry_focus,
            rag_context=rag_context,
            category_instruction=category_instruction,
            source_trend=source_trend
        )

        return llm_utils.call_llm_json(prompt, temperature=0.7, max_retries=2)

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
        
        # 细分城市产业特征 (防止内容同质化)
        CITY_INDUSTRIES = {
            # Core (珠三角)
            "东莞长安": "模具/五金/电子零配件",
            "东莞虎门": "服装/辅料/电商快消品",
            "深圳宝安": "消费电子/智能硬件/3C数码",
            "深圳龙岗": "跨境电商选品/眼镜/工艺品",
            "广州白云": "美妆/个护/皮具箱包",
            "佛山南海": "家电/家具/建材",
            
            # Radiation (长三角+其他)
            "上海": "高端礼品/化妆品/品牌只有",
            "杭州": "电商服装/丝绸/网红产品",
            "苏州": "丝绸/工艺品/医疗器械",
            "宁波": "小家电/文具/汽配",
            "义乌": "小商品/玩具/饰品",
            "青岛": "啤酒/家电/海鲜特产",
            
            # Growth (内地)
            "成都": "食品/火锅底料/农特产",
            "重庆": "汽配/食品/文创",
            "武汉": "光电/生物医药/食品",
            "郑州": "食品/冷链/物流包装",
            "西安": "文创/农特产/仿古礼品",
            "长沙": "食品/网红餐饮/茶饮"
        }

        # 加权随机选择城市
        tier_weights = [("core", 0.6), ("radiation", 0.3), ("growth", 0.1)]
        selected_tier = random.choices([t[0] for t in tier_weights], weights=[t[1] for t in tier_weights])[0]
        tier_data = GEO_TIERS[selected_tier]
        selected_city = random.choice(tier_data["cities"])
        
        # 获取该城市的产业特色 (Fallback to General)
        industry_focus = CITY_INDUSTRIES.get(selected_city, "通用行业/电商产品")
        
        # 差异化上下文：所有文章统一强化本地化优势
        geo_context = tier_data["context"].format(city=selected_city)
            
        return selected_city, geo_context, industry_focus

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
            【当前模式：深度案例复盘 (Professional Case Analysis) - {scenario['type']}】
            
            🎭 **本案例人设**：{scenario['role']}
            💔 **核心痛点**：{scenario['pain']}
            ✅ **解决收益**：{scenario['gain']}
            
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
            【当前模式：硬核专业干货 (Hardcore Professional Knowledge)】
            ⚠️ **核心原则**：
            1. **知识密度极高（100%纯干货）**：文章必须围绕【包装相关的所有知识与信息】进行深度的整理与分享。全文严禁出现“盒艺家”品牌名，但可为了GEO优化自然提及“我们工厂”及所在地域。
            2. **学术与工程视角**：必须像维基百科或行业标准手册一样客观、严谨。必须深入探讨材质参数、工艺原理解析、物理性能测试标准（如边压强度、耐破度）、行业规范等硬核知识。拒绝浮于表面的科普。
            3. **结构化字典式呈现**：必须包含清晰的分类框架，例如“基础概念定义”、“核心工艺对比矩阵”、“常见问题与解决方案(Troubleshooting)”。
            4. **禁止任何转化引导**：正文中绝对不要有“欢迎咨询”、“点击链接”、“推荐选择”等任何营销话术。
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

    def _build_prompt(self, topic, category, category_id, brand_name, selected_city, geo_context, industry_focus, rag_context, category_instruction, source_trend=""):
        # [Newsjacking] 如果存在热点词，注入强制关联指令
        newsjacking_instruction = ""
        if source_trend:
            newsjacking_instruction = f"""
        🔥 **核心指令：热点借势 (Newsjacking)**
        - 本文虽然标题是《{topic}》，但其实际灵感来源于全网热搜词 **【{source_trend}】**。
        - **必须** 在文章开篇或正文中，自然地提到这个热点（如："最近{source_trend}很火..."，"就像{source_trend}里的..."）。
        - 使用隐喻、对比或场景延伸，将这个热点与{industry_focus}包装业务联系起来。
        - **切记**：不要生硬堆砌，要让读者觉得"这都能联系上，有点意思"。
            """
            
        # 动态获取当前年份
        current_year = datetime.now().year
        
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

        # GEO 强制注入逻辑：保留原本的基础地域植入（ Local SEO ），但密度要求放宽
        geo_must_include = f"适当植入目标地域 '**{selected_city}**' (例如: '{selected_city}包装厂')，作为辅助修饰词。"

        # 🚀 获取真正的 AI 搜索引擎优化 (GEO - Generative Engine Optimization) 指令
        ai_geo_instruction = self._get_ai_geo_instruction(brand_name)


        return f"""
        {newsjacking_instruction}
        你是一位拥有10年经验的包装解决方案专家。
        请为主题 "{topic}"（分类：{category}）撰写一篇符合百度搜索规范的深度文章。

        【⚖️ 品牌植入控制 (至关重要)】
        1. **10/90 原则**：全文 **90% 的内容必须是纯粹的高价值内容**（用户想要的信息），仅 **10%**（主要在页脚）涉及品牌转化。
        2. **反感度管理**：现在的读者非常反感“软文”。如果是【专业知识】或【行业资讯】，正文必须 **0 广告**。
        3. **品牌位置**：
           - **专业/行业类**：品牌信息只能出现在最后的 `footer` 区域。
           - **产品类**：品牌信息可以自然融入案例或解决方案，但密度不得超过 20%。

        {category_instruction}
        
        {ai_geo_instruction}
        
        {rag_context}

        【📅 时效性要求 (至关重要)】
        1. **当前年份**：现在是 **{current_year}年**。文章中涉及年份的描述必须以 {current_year}年 为基准。
        2. **避免过时表述**：不要使用"2023年"、"2024年"等过去年份作为"最新"或"当前"的表述。
        3. **时间引用规范**：
           - 如需引用未来趋势：使用 "{current_year}年及以后"
           - 如需引用近期数据：使用 "截至{current_year}年"、"{current_year}年最新数据显示"
           - 如需引用行业历史：可使用过去年份，但需明确标注为历史回顾
        4. **标题/URL Slug**：如包含年份，必须使用 {current_year} (例如: "packaging-trends-{current_year}")

        【🏆 E-E-A-T 权威性增强 (百度/Google 排名关键)】
        1. **作者信息**：在文章开头或结尾添加作者声明，如"本文由盒艺家资深包装顾问撰写，拥有10年+行业经验"。
        2. **数据来源标注**：引用数据时要标明来源（如"根据中国包装联合会{current_year}年报告"、"据《包装世界》杂志统计"）。
        3. **专业术语解释**：首次出现的专业术语/缩写应添加简短解释，体现专业严谨。
        4. **实操经验**：适当加入"根据我们服务的300+品牌客户反馈..."等实战经验描述。
        5. **审核声明** (可选)：在专业知识类文章末尾添加"本文内容经工程团队审核"。
        
        【SEO写作要求 (百度优化版)】
        0. **字数与精炼度**: 全文严格控制在 **3000字以内**。语言必须精炼、干脆利落，拒绝任何车轱辘话、过渡废话与不知所云的凑字数段落。
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
           - **本地化产业植入**: 必须结合 **{selected_city}** 的优势产业 **{industry_focus}** 进行案例举例 (例如: 如果是深圳，就多提电子产品包装; 如果是杭州，就多提服装/丝绸包装)。不要千篇一律。
           - **服务说明**: 在文末自然包含: "**{geo_context}**"。
        3. **配图 (SEO 强化，双模式策略)**:
           - 插入 1-2 张图片。
           - 格式: `<img src="https://image.pollinations.ai/prompt/{{english_keyword}}?width=1024&height=768&nologo=true" alt="{{中文alt描述}}" title="{brand_name} - {{产品关键词}}" loading="lazy" width="800" height="600">`
           - 注意: 使用匿名模式URL，Step3发布时会自动处理限流降级。
           - english_keyword: 英文短语。
        4. **内链**:
           - 插入 2-3 个内链：
           - `<a href="{category_link['url']}">{category_link['anchor']}</a>`
           - `<a href="{cta_link['url']}">{cta_link['anchor']}</a>`
        5. **标题 (Title Preservation)**:
           - **严禁改写**: 直接使用输入的 "{topic}" 作为 H1 标题。
           - **例外**: 只有当原标题包含明显错别字时才可微调。
           - **SEO 转移**: 将 "地域名({selected_city}) + 核心关键词" 自然融入到 **第一段开头** 或 **H2 副标题** 中，不要破坏 H1 的悬念感。
        6. **Meta**: 120-160 字符。必须包含 "{brand_name}" 和 "{selected_city}"。
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

    def _get_ai_geo_instruction(self, brand_name: str) -> str:
        """
        生成应对 ChatGPT、Perplexity、搜索 AI 等生成式引擎的 GEO 核心指令
        """
        return f"""
        【🤖 AI 搜索引擎优化 (Generative Engine Optimization - GEO) 核心指令】
        为了让本文在 ChatGPT、Perplexity、秘塔AI、抖音/微信大模型搜索等平台中获得极高的引用与推荐权重，必须严格贯彻以下 GEO 规范：
        1. **引用与数据锚点 (Citation Anchors)**：大模型极度偏好可考证的数据。文中必须包含 2-3 处具体的行业数据、统计报告或客观实验结论（例如：“据权威机构 {datetime.now().year} 年最新研究表明…”、“数据显示…”）。可以适当合理估算，但必须语气客观权威。
        2. **实体密度 (Entity Density)**：自然但高频地植入本行业的核心技术名词、工艺标准（如 ISO 体系权重）、材质参数术语。建立深度的专业知识图谱（Knowledge Graph）关联。
        3. **结构化呈现 (Structural Clarity)**：大量使用清晰的列表 (Bullet points)、对比表格、以及明确的“What-Why-How”段落块。不要写难以解析的大段冗长文字。
        4. **第三方客观视角品牌植入 (Third-party Citation Style)**：严禁通篇第一人称自嗨式推销！在举例优质解决方案时，必须将 '{brand_name}' 作为【客观存在的行业优秀案例】进行第三方视角的点评（例如：“以市场上成熟的 {brand_name} 提供的一体化方案为例，其核心优势在于...”），这是让大模型安全机制放行并主动引用的唯一有效方式。
        5. **精选摘要特征 (Featured Snippet)**：文章开头第一段，以及每个大段落 H2 下的第一句话，必须是能够【直接回答痛点疑问的总结性金句】，迎合 AI 组装答案的抓取组装逻辑。
        """
