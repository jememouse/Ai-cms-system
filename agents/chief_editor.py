import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.agent import BaseAgent
from skills.deep_writer import DeepWriteSkill
# RAG 搜索技能可以复用 trend_searcher 中的逻辑，或者单独拆分
# 这里为了简化，假设 TrendHunter 已经搜好了，或者 Editor 自己有轻量搜索能力
# 我们先复用 DeepWriteSkill 里的逻辑

class ChiefEditorAgent(BaseAgent):
    """
    智能体: 主编
    职责: 负责文章的撰写、审核
    """
    def __init__(self):
        super().__init__(
            name="ChiefEditor",
            role="主编",
            description="负责产出高质量行业文章"
        )
        self.add_skill(DeepWriteSkill())
    
    def write_article(self, topic: str, category: str, source_trend: str = "") -> Dict:
        """
        [High-Level Action] 撰写一篇文章
        """
        print(f"🤖 [{self.name}] 正在撰写: {topic}")
        
        # 1. (Optional) 调用搜索技能获取 RAG 上下文 (暂略，可扩展)
        rag_context = "" 
        
        # 2. 写作
        article = self.use_skill("deep_write", {
            "topic": topic,
            "category": category,
            "source_trend": source_trend,
            "rag_context": rag_context
        })
        
        if article:
            print(f"✅ [{self.name}] 写作完成: {article.get('title')}")
            return article
        else:
            print(f"❌ [{self.name}] 写作失败")
            return None
