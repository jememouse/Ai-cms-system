import sys
import os
import random
import logging
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.skill import BaseSkill
from shared import llm_utils

# 配置 logger
logger = logging.getLogger(__name__)

class TopicAnalysisSkill(BaseSkill):
    """
    技能: 话题分析师 (使用 LLM 分析热点并生成选题)
    """
    def __init__(self):
        super().__init__(
            name="topic_analysis",
            description="分析热点列表，挑选最有价值的 20 个，并生成 6 个 SEO 标题"
        )

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
        generated_texts = [] # 用于去重检查

        # 2. 第二步：为每个热点生成标题
        for idx, trend in enumerate(analyzed_trends):
            print(f"   🧠 [Analyst] 生成标题 ({idx+1}/{len(analyzed_trends)}): {trend['topic']}")
            titles = self._generate_titles(trend, input_data.get("config", {}))
            
            for t in titles:
                raw_title = t['title'].strip()
                
                # [Deduplication] 查重
                if self._is_text_similar(raw_title, generated_texts):
                    print(f"   🗑️ [Dedupe] 丢弃高相似度标题: {raw_title}")
                    continue
                
                generated_texts.append(raw_title)
                
                results.append({
                    "Topic": raw_title,
                    "大项分类": self._clean_category(t['category']),
                    "Status": "Pending",
                    "Source_Trend": trend['topic'],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        
        return results

    def _is_text_similar(self, new_text: str, existing_texts: List[str], threshold: float = 0.6) -> bool:
        """
        简单的文本相似度去重 (Jaccard Similarity on chars)
        """
        if not existing_texts: return False
        
        s1 = set(new_text)
        for t in existing_texts:
            s2 = set(t)
            intersection = len(s1.intersection(s2))
            union = len(s1.union(s2))
            if union == 0: continue
            
            sim = intersection / union
            # 如果前 5 个字完全一样，也视为重复
            if new_text[:5] == t[:5]:
                return True
                
            if sim > threshold:
                return True
        return False

    def _analyze_trends(self, trends):
        import re
        trends_str = "\n".join([f"- {t}" for t in trends])

        # 动态选择城市 (GEO 策略)
        GEO_CITIES = ["东莞", "深圳", "广州", "上海", "杭州", "苏州", "义乌", "佛山"]
        selected_city = random.choice(GEO_CITIES)

        prompt = f"""
        我们是一家 **"包装在线定制电商平台（强大的供应链及品质管理+交付系统）"** （盒艺家）。
        你是一位拥有10年经验的包装解决方案专家，代表 **盒艺家（包装在线定制平台 + 强大的供应链及品质管理+交付系统）**。擅长同时服务 **B2B企业采购** 和 **B2C/C2M个人定制**。即使是通用话题，也要基于 **{selected_city}** 的地域视角进行解答。

        请从以下全网热点中，**务必挑选出 20 个** 最适合写文章的话题。

        筛选优先级（兼顾 B2B 与 B2C）：
        1. **S级（必选 - 借势营销/高意图）**：
           - **社会热点强关联 (Newsjacking)**：能通过"隐喻/场景/配色"强行关联的破圈热点。
             - *思维模型*：哈尔滨火了 -> 思考"抗寒/冷链包装"；繁花热播 -> 思考"复古/港风礼盒"；多巴胺穿搭 -> 思考"鲜艳配色包装"。
           - **高意图转化**：包含 [搜索需求]、[1688采购]、多少钱、怎么选。
        2. **A级（重点 - 商业场景）**：
           - 包含 小批量、礼品定制、伴手礼、Etsy包装、私域包装。
           - 季节性话题：春节礼盒、电商大促、展会、环保新规。
        3. **B级（特定关联）**：
           - 有明确商业价值的行业长尾词。

        热搜列表：
        {trends_str}

        请严格返回 JSON 格式列表：
        [
            {{"topic": "话题名", "angle": "结合角度(如: 借势哈尔滨热度，切入冷链包装场景)", "priority": "S"}}
        ]
        不要返回 Markdown。
        """
        res = llm_utils.call_llm_json_array(prompt, temperature=0.7, max_retries=2)
        analyzed_trends = res if res else []
        
        # === Fallback: 确保数量达标 (20个) ===
        target_count = 20
        if len(analyzed_trends) < target_count:
            print(f"⚠️ [Topics] LLM仅返回 {len(analyzed_trends)} 个 (目标{target_count})，启动自动补全...")
            
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

        # 动态获取当前年份
        current_year = datetime.now().year

        prompt = f"""
        背景：{brand_name} (既接B2B大单，也接B2C小单，**1个起订**)
        热点：{topic} (角度: {angle})
        当前年份：{current_year}年

        任务：生成 6 个高点击率 Title。
        要求：
        1. **多样化句式（拒绝公式化 - 严厉执行）**：
           - **绝对违禁词** (出现即判定为劣质)：
             - 严禁使用 "高级感(礼盒)的秘密"、"还在为...发愁"、"告别(买家秀)"
             - 严禁使用 "XX的正确打开方式"、"一文看懂"、"一站式平台"
             - 严禁使用 "案例复盘："、"故事："、"1个起订，"、"2026年"（除非必要）
           - **拒绝排比**：6个标题的句式和前半句必须完全不同。
        2. **高点击率风格（Human-written）**：
           - **悬念型**："袜子销量翻倍？没想到仅仅是换了这个包装..."
           - **直击痛点**："小批量定制太贵？源头厂长说了真话"
           - **数据说话**："客单价提升30%的秘密：揭秘大牌礼盒设计逻辑"
           - **避坑指南**："劝退！这3种包装材质千万别踩雷"
        3. **字数控制**：30个字符以内（允许更完整的长标题）。
        4. **内容分布**：
           - 2个 **专业知识** (干货/避坑/材质)
           - 2个 **行业资讯** (趋势/数据/展会)
           - 2个 **产品介绍** (场景/痛点/选购)
           **注意**：不要返回独立的"客户案例"分类，归入以上三类。

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
        res = llm_utils.call_llm_json_array(prompt, temperature=0.7, max_retries=2)
        return res if res else []

    def _clean_category(self, cat):
        valid_cats = ["专业知识", "行业资讯", "产品介绍"]
        for v in valid_cats:
            if v in cat: return v
        return "行业资讯"
