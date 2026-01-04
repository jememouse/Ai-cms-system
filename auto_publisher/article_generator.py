# auto_publisher/article_generator.py
"""
AI 文章生成器
使用 DeepSeek 生成 SEO 优化的文章
"""
import json
import re
import requests
from typing import Dict, Optional
from .config import config


class ArticleGenerator:
    """AI 文章生成器"""
    
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.api_url = config.DEEPSEEK_API_URL
    
    def generate(self, topic: str, category: str) -> Optional[Dict]:
        """
        根据主题生成 SEO 文章
        
        Args:
            topic: 文章主题/标题
            category: 分类 (专业知识/行业资讯/产品介绍)
            
        Returns:
            包含 title, html_content, summary, keywords, description, tags, category_id
        """
        category_id = config.CATEGORY_MAP.get(category, "2")
        
        prompt = f"""你是一个资深的行业内容编辑，专注于包装印刷行业。请根据用户提供的主题，撰写一篇专业、深入、有价值的文章。

【写作要求】
1. 文章字数在 1000 字左右，内容充实、逻辑清晰
2. 开篇要有引人入胜的导语，结尾要有总结或行动号召
3. 使用专业术语，但要通俗易懂
4. 可以适当使用数据、案例来增强说服力
5. 段落分明，便于阅读

【重要格式指令】
1. 必须直接输出标准的 JSON 字符串
2. 严禁使用 Markdown 代码块（即不要用 ```json ... ``` 包裹）
3. 不要输出任何 JSON 之外的解释性文字

【JSON 结构要求】
{{
  "title": "标题（必须15字以内，超过15字会被拒绝）",
  "html_content": "纯HTML格式的正文（不含<html><body>标签，使用<h2>作为小标题，<p>分段落，可使用<ul><li>列表）",
  "category_id": "{category_id}",
  "summary": "文章摘要（120字以内，概括文章核心观点）",
  "keywords": "3-5个SEO关键词，用逗号分隔",
  "description": "SEO描述（120字以内，用于搜索引擎展示）",
  "tags": "3-5个相关标签，用逗号分隔"
}}

【标题要求 - 非常重要】
- 标题必须控制在15个中文字符以内
- 要简洁有力、吸引眼球
- 避免使用冒号、破折号等分隔符拉长标题

【品牌植入】
- 仅在涉及"找工厂"、"定制"、"推荐"等场景时，可以提及"盒艺家"
- 不要强制植入，保持内容自然

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
            
            # 清理可能的 Markdown 代码块
            content = content.replace("```json", "").replace("```", "").strip()
            
            # 提取 JSON
            content = self._extract_json(content)
            
            article = json.loads(content)
            article["category_id"] = category_id  # 确保分类正确
            
            print(f"   ✅ 文章生成成功: {article.get('title', '无标题')}")
            return article
            
        except json.JSONDecodeError as e:
            print(f"   ⚠️ JSON 解析失败: {e}")
            return None
        except Exception as e:
            print(f"   ⚠️ 文章生成失败: {e}")
            return None
    
    def _extract_json(self, text: str) -> str:
        """从文本中提取 JSON 字符串"""
        first_brace = text.find('{')
        last_brace = text.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return text[first_brace:last_brace + 1]
        return text
