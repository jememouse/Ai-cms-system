# step2_article/generator.py
"""
AI 文章生成器
"""
import json
import requests
from typing import Dict, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import config


class ArticleGenerator:
    """AI 文章生成器"""
    
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.api_url = config.DEEPSEEK_API_URL
        self._load_brand_config()
    
    def _load_brand_config(self):
        """加载品牌配置"""
        self.brand_config = {}
        if os.path.exists(config.CONFIG_FILE):
            with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.brand_config = json.load(f)
    
    def generate(self, topic: str, category: str) -> Optional[Dict]:
        """根据标题生成 SEO 文章"""
        category_id = config.CATEGORY_MAP.get(category, "2")
        
        # 品牌信息
        brand = self.brand_config.get('brand', {})
        brand_name = brand.get('name', '盒艺家')
        
        prompt = f"""你是一个资深的行业内容编辑，专注于包装印刷行业。请根据用户提供的主题，撰写一篇专业、深入、有价值的文章。

【写作要求】
1. 文章字数在 1000 字左右，内容充实、逻辑清晰
2. 开篇要有引人入胜的导语，结尾要有总结或行动号召
3. 使用专业术语，但要通俗易懂
4. 可以适当使用数据、案例来增强说服力
5. 段落分明，便于阅读

【重要格式指令】
1. 必须直接输出标准的 JSON 字符串
2. 严禁使用 Markdown 代码块
3. 不要输出任何 JSON 之外的解释性文字

【JSON 结构要求】
{{
  "title": "标题（必须15字以内）",
  "html_content": "纯HTML格式的正文（使用<h2>小标题，<p>分段，可用<ul><li>列表）",
  "category_id": "{category_id}",
  "summary": "文章摘要（120字以内）",
  "keywords": "3-5个SEO关键词，逗号分隔",
  "description": "SEO描述（120字以内）",
  "tags": "3-5个标签，逗号分隔"
}}

【标题要求】
- 标题控制在15个中文字符以内
- 简洁有力、吸引眼球

【品牌植入】
- 仅在涉及"找工厂"、"定制"、"推荐"时可提及"{brand_name}"
- 不要强制植入

【年份要求】
- 涉及年份时使用 **2026年**，不用过时年份

主题：{topic}
分类：{category}"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            resp = requests.post(self.api_url, headers=headers, json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 4096
            }, timeout=120)
            
            content = resp.json()["choices"][0]["message"]["content"]
            content = content.replace("```json", "").replace("```", "").strip()
            
            # 提取 JSON
            first_brace = content.find('{')
            last_brace = content.rfind('}')
            if first_brace != -1 and last_brace > first_brace:
                content = content[first_brace:last_brace + 1]
            
            article = json.loads(content)
            article["category_id"] = category_id
            
            print(f"   ✅ 文章生成成功: {article.get('title', '无标题')}")
            return article
            
        except Exception as e:
            print(f"   ⚠️ 文章生成失败: {e}")
            return None
