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
            description="分析热点列表，挑选最有价值的 20 个，并生成 6 个 SEO 标题"
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

        # 1. 第一步：筛选 20 个热点
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
        我们是一家 **"包装在线定制电商平台（强大的供应链及品质管理+交付系统）"** （盒艺家）。
        你是一位拥有10年经验的包装解决方案专家，代表 **盒艺家（包装在线定制平台 + 强大的供应链及品质管理+交付系统）**。擅长同时服务 **B2B企业采购** 和 **B2C/C2M个人定制**。即使是通用话题，也要基于 **{selected_city}** 的地域视角进行解答。
        
        请从以下全网热点中，**务必挑选出 20 个** 最适合写文章的话题。
        
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
        analyzed_trends = res if isinstance(res, list) else []
        
        # === Fallback: 确保数量达标 (20个) ===
        target_count = 20
        if len(analyzed_trends) < target_count:
            print(f"⚠️ [Topics] LLM仅返回 {len(analyzed_trends)} 个 (目标{target_count})，启动自动补全...")
            import random
            
            # 1. 提取已有的 topics 以避免重复
            existing_topics = {t.get("topic", "") for t in analyzed_trends}
            
            # 2. 从原始列表中寻找候选
            candidates = []
            for raw_t in trends:
                # 简单清理：去除 "[平台]" 前缀
                clean_t = re.sub(r'\[.*?\]\s*', '', raw_t)
                if clean_t and clean_t not in existing_topics:
                    candidates.append(clean_t)
            
            # 3. 随机抽取补全
            needed = target_count - len(analyzed_trends)
            if candidates:
                fillers = random.sample(candidates, min(needed, len(candidates)))
                for f in fillers:
                    analyzed_trends.append({
                        "topic": f,
                        "angle": "全网热点流量承接",
                        "priority": "A"
                    })
            print(f"✅ [Topics] 已补全至 {len(analyzed_trends)} 个")
            
        return analyzed_trends[:target_count]

    def _generate_titles(self, trend, brand_config):
        brand_name = brand_config.get('brand', {}).get('name', '盒艺家')
        topic = trend.get('topic', '')
        angle = trend.get('angle', '')
        
        prompt = f"""
        背景：{brand_name} (既接B2B大单，也接B2C小单，**1个起订**)
        热点：{topic} (角度: {angle})
        
        任务：生成 6 个高点击率 Title。
        要求：
        1. **混合策略**：生成的6个标题中，必须严格按照 **2个专业知识 + 2个行业资讯 + 2个产品介绍** 的比例分配。至少有2个体现 "小批量/定制/个性化" 等 B2C 痛点，其余体现 B2B 专业性。
        2. 2026年，**严格控制在 16 个字符以内 (按双字节汉字计算)**。
        3. 绝大部分不要出现品牌词。
        4. 必须覆盖以下3种分类风格，并**随机(10-20%概率)插入“案例/故事”类标题**：
           - **专业知识**：风格为“干货/指南/避坑/解析”。**必须包含“结合当前热点({topic})的深度案例复盘”**（如：“案例解析：{topic}如何帮助这家店销量翻倍...”）。
           - **行业资讯**：风格为“趋势/数据/新规/行情”。
           - **产品介绍**：风格为“场景/痛点/选购”。但也包含“客户故事”（如：“淘宝店主用{topic}定制逆袭...”）。
           
           **注意**：不要返回独立的“客户案例”分类，而是将案例类标题归入【专业知识】或【产品介绍】。
        
        返回 JSON:
        [
            {{"title": "标题1", "category": "专业知识"}},
            {{"title": "标题2", "category": "专业知识"}},
            {{"title": "标题3", "category": "行业资讯"}},
            {{"title": "标题4", "category": "行业资讯"}},
            {{"title": "标题5", "category": "产品介绍"}},
            {{"title": "标题6", "category": "产品介绍"}}
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
