from typing import Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import BaseAgent
from skills.xhs_rewriter import XHSRewriterSkill
from skills.cover_designer import CoverDesignSkill

class SocialManagerAgent(BaseAgent):
    """
    智能体: 社交媒体经理
    职责: 负责将已有内容裂变分发到社交平台
    """
    def __init__(self):
        super().__init__(
            name="SocialBot",
            role="社交媒体经理",
            description="负责根据长文章生成小红书、推特等社交媒体内容"
        )
        # 自动装配技能
        self.add_skill(XHSRewriterSkill())
        self.add_skill(CoverDesignSkill())

    def create_xhs_post(self, article_title: str, article_content: str) -> Dict:
        """
        [High-Level Action] 从文章生成一篇完整的小红书笔记数据
        """
        print(f"🤖 [{self.name}] 收到任务: 为《{article_title}》制作小红书笔记")
        
        # 1. 调用写作技能
        note_data = self.use_skill("xhs_rewrite", {
            "title": article_title, 
            "content": article_content
        })
        
        if not note_data:
            print(f"❌ [{self.name}] 写作失败")
            return None
            
        # 2. 调用美工技能
        cover_url = self.use_skill("cover_design", {
            "title": note_data['title'],
            "keywords": note_data['keywords']
        })
        
        # 3. 后处理: 格式化关键词
        raw_keywords = note_data.get('keywords', '')
        formatted_keywords = self._format_keywords(raw_keywords)
        
        # 4. 组装最终结果
        final_post = {
            "title": note_data['title'],
            "content": note_data['content'],
            "keywords": formatted_keywords,
            "cover_url": cover_url,
            "source_title": article_title
        }
        
        print(f"✅ [{self.name}] 笔记制作完成: {final_post['title']}")
        return final_post

    def _format_keywords(self, raw_keywords: Any) -> str:
        """内部工具: 格式化关键词为 Hashtag"""
        if isinstance(raw_keywords, list):
            parts = raw_keywords
        else:
            parts = str(raw_keywords).replace("，", ",").split(",")
        
        final_tags = []
        for p in parts:
            tag = p.strip().lstrip("#")
            if tag:
                final_tags.append(f"#{tag}")
        return " ".join(final_tags)
