import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.agent import BaseAgent
from skills.trend_searcher import TrendSearchSkill
from skills.topic_analyst import TopicAnalysisSkill

class TrendHunterAgent(BaseAgent):
    """
    智能体: 趋势猎手
    职责: 全网搜集热点，分析并生成 SEO 选题
    """
    def __init__(self):
        super().__init__(
            name="TrendHunter",
            role="数据分析师",
            description="负责全网热点挖掘与选题决策"
        )
        self.add_skill(TrendSearchSkill())
        self.add_skill(TopicAnalysisSkill())

    def hunt_and_analyze(self, config_data: Dict) -> List[Dict]:
        """
        [High-Level Action] 执行完整的选题流程
        """
        print(f"🤖 [{self.name}] 开始执行选题任务...")
        
        # 1. 搜集
        seeds = config_data.get("mining_seeds", [])
        trends = self.use_skill("trend_search", {"mining_seeds": seeds})
        
        if not trends:
            print(f"❌ [{self.name}] 未找到任何热点")
            return []
            
        print(f"🤖 [{self.name}] 已收集 {len(trends)} 个热点，开始分析...")
        
        # 2. 分析
        generated_topics = self.use_skill("topic_analysis", {
            "trends": trends, 
            "config": config_data
        })
        
        print(f"✅ [{self.name}] 选题完成，共产出 {len(generated_topics)} 个标题")
        return generated_topics
