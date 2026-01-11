import sys
import os
import json
import requests
import re
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.skill import BaseSkill
from shared import config

class TopicAnalysisSkill(BaseSkill):
    """
    技能: 话题分析师 (使用 LLM 分析热点并生成选题)
    """
    def __init__(self):
        super().__init__(
            name="topic_analysis",
            description="分析热点列表，挑选最有价值的 33 个，并生成 6 个 SEO 标题"
        )
        self.api_key = config.LLM_API_KEY
        self.api_url = config.LLM_API_URL

    def _call_deepseek(self, prompt: str) -> Dict:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if "openrouter" in self.api_url:
            headers["HTTP-Referer"] = "https://github.com/jememouse/deepseek-feisu-cms"
        
        try:
            resp = requests.post(
                self.api_url, 
                headers=headers, 
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7},
                timeout=120
            )
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content']
                content = content.replace("```json", "").replace("```", "").strip()
                return json.loads(content)
        except Exception as e:
            print(f"   ❌ LLM Error: {e}")
        return None

    def execute(self, input_data: Dict) -> List[Dict]:
        """
        Input: {"trends": [], "config": {}}
        Output: [{"Topic": "...", "大项分类": "...", ...}]
        """
        trends = input_data.get("trends", [])
        if not trends: return []

        # 1. 第一步：筛选 33 个热点
        analyzed_trends = self._analyze_trends(trends)
        
        results = []
        # 2. 第二步：为每个热点生成标题
        for idx, trend in enumerate(analyzed_trends):
            print(f"   🧠 [Analyst] 生成标题 ({idx+1}/{len(analyzed_trends)}): {trend['topic']}")
            titles = self._generate_titles(trend, input_data.get("config", {}))
            
            for t in titles:
                results.append({
                    "Topic": t['title'],
                    "大项分类": self._clean_category(t['category']),
                    "Status": "Pending",
                    "Source_Trend": trend['topic'],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        return results

    def _analyze_trends(self, trends):
        trends_str = "\n".join([f"- {t}" for t in trends])
        # Define selected_city or get it from config if needed, for now, a placeholder
        selected_city = "上海" # Placeholder for demonstration
        prompt = f"""
        我们是一家 **"包装在线定制电商平台（配套专业加工工厂）"** （盒艺家）。
        你是一位拥有10年经验的包装解决方案专家，代表 **盒艺家（包装在线定制平台 + 自有工厂）**。擅长同时服务 **B2B企业采购** 和 **B2C/C2M个人定制**。即使是通用话题，也要基于 **{selected_city}** 的地域视角进行解答。
        
        请从以下全网热点中，**务必挑选出 1 个** (为了演示速度改为1个) 最适合写文章的话题。
        
        筛选优先级（兼顾 B2B 与 B2C）：
        1. **高意图转化**：包含 [搜索需求]、[1688采购]、多少钱、怎么选。
        2. **长尾个性化**：包含 小批量、礼品定制、伴手礼、Etsy包装、私域包装。
        3. **商业关联**：春节礼盒、电商包装、展会、环保包装。
        
        热搜列表：
        {trends_str}
        
        请严格返回 JSON 格式列表：
        [
            {{"topic": "话题名", "angle": "结合角度(如: 适合小批量试单)", "priority": "S"}}
        ]
        """
        res = self._call_deepseek(prompt)
        return res if isinstance(res, list) else []

    def _generate_titles(self, trend, brand_config):
        brand_name = brand_config.get('brand', {}).get('name', '盒艺家')
        topic = trend.get('topic', '')
        angle = trend.get('angle', '')
        
        prompt = f"""
        背景：{brand_name} (既接B2B大单，也接B2C小单，**1个起订**)
        热点：{topic} (角度: {angle})
        
        任务：生成 5 个高点击率 Title。
        要求：
        1. **混合策略**：生成的5个标题中，至少有2个体现 "小批量/定制/个性化" 等 B2C 痛点，其余体现 B2B 专业性。
        2. 2026年，**严格控制在 16 个字符以内 (按双字节汉字计算)**。
        3. 绝大部分不要出现品牌词。
        4. 必须包含分类：【专业知识】、【行业资讯】、【产品介绍】。
        
        返回 JSON:
        [
            {{"title": "标题1", "category": "专业知识"}},
            ...
        ]
        """
        res = self._call_deepseek(prompt)
        # 兼容旧代码，确保至少返回列表
        return res if isinstance(res, list) else []

    def _clean_category(self, cat):
        valid_cats = ["专业知识", "行业资讯", "产品介绍"]
        for v in valid_cats:
            if v in cat: return v
        return "行业资讯"
