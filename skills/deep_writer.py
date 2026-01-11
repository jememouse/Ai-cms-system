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
                    "max_tokens": 3500,
                    "stream": False
                },
                timeout=(30, 300)
            )
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                content = content.replace("```json", "").replace("```", "").strip()
                # 简单 JSON 提取
                start = content.find('{')
                end = content.rfind('}')
                if start != -1 and end > start:
                    return json.loads(content[start:end+1])
        except Exception as e:
            print(f"   ❌ Writing Error: {e}")
        return None

    def execute(self, input_data: Dict) -> Dict:
        """
        Input: {"topic": str, "category": str, "rag_context": str (optional)}
        Output: Article JSON
        """
        topic = input_data.get("topic")
        category = input_data.get("category", "行业资讯")
        rag_context = input_data.get("rag_context", "")
        
        # 简化版 Prompt 构建逻辑 (复用原 generator.py 核心)
        category_id = config.CATEGORY_MAP.get(category, "2")
        brand = self.brand_config.get('brand', {})
        brand_name = brand.get('name', '盒艺家')
        
        # 动态构造 RAG 指令
        rag_instruction = ""
        if rag_context:
            rag_instruction = f"""
            【真实性增强 (RAG Context)】
            🔍 系统已搜索到以下信息，请务必基于此写作，严禁编造：
            {rag_context}
            """

        # 动态构造 SEO/GEO 指令 (分层城市策略)
        GEO_TIERS = {
            "core": {  # 核心市场 (工厂所在地周边) - 权重 50%
                "cities": ["东莞", "深圳", "广州", "佛山", "惠州"],
                "context": "我们工厂位于{city}，可提供当日送样、面对面沟通服务"
            },
            "radiation": {  # 辐射市场 (电商/出口集中地) - 权重 35%
                "cities": ["上海", "杭州", "苏州", "宁波", "义乌"],
                "context": "我们为{city}地区提供快速物流支持，3天内可达"
            },
            "growth": {  # 潜力市场 (内陆物流枢纽) - 权重 15%
                "cities": ["成都", "重庆", "武汉", "郑州", "西安"],
                "context": "我们已开通{city}专线物流，助力西部市场拓展"
            }
        }
        
        # 加权随机选择城市
        tier_weights = [("core", 0.5), ("radiation", 0.35), ("growth", 0.15)]
        selected_tier = random.choices([t[0] for t in tier_weights], weights=[t[1] for t in tier_weights])[0]
        tier_data = GEO_TIERS[selected_tier]
        selected_city = random.choice(tier_data["cities"])
        geo_context = tier_data["context"].format(city=selected_city)
        
        prompt = f"""
        你是一位拥有10年经验的 B2B 包装行业内容营销专家，专注于为 **{selected_city}** 地区的包装客户提供解决方案。
        请为主题 "{topic}"（分类：{category}）撰写一篇深度文章。
        
        {rag_instruction}
        
        【写作要求】
        1. **结构**: 定义式开头 -> 核心要点(blockquote) -> 正文(含表格) -> 一句话总结 -> FAQ -> 作者标记。
        2. **GEO优化**: 
           - 全文必须自然植入目标城市 "**{selected_city}**" (例如: "{selected_city}包装厂", "{selected_city}礼盒定制"), 密度至少 3 次。
           - 在文末或服务说明处，自然包含: "**{geo_context}**"。
        3. **配图 (SEO 强化)**:
           - 在正文中插入 2-3 张图片。
           - 格式: `<img src="https://image.pollinations.ai/prompt/{{english_keyword}}?width=1024&height=768&nologo=true" alt="{{中文alt描述}}" title="{brand_name} - {{产品关键词}}" loading="lazy" width="800" height="600">`
           - **alt 必须**: 15-30 个中文字符，包含核心关键词 (如: "东莞高端月饼礼盒定制包装效果图")。
           - **title 必须**: 品牌名 + 产品关键词 (如: "{brand_name} 月饼盒定制")。
           - english_keyword: 提取中文主题翻译为英文短语，用于图片生成。
        4. **标题**: 必须严格控制在 16 字以内。
        5. **格式**: 返回纯 JSON。

        {{
          "title": "标题...",
          "html_content": "HTML内容...",
          "category_id": "{category_id}",
          "summary": "...",
          "keywords": "...",
          "description": "...",
          "tags": "...",
          "schema_faq": [],
          "one_line_summary": "...",
          "key_points": ["要点1", "要点2"]
        }}
        """
        
        return self._call_llm(prompt)
