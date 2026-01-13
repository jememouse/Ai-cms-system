from typing import Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import BaseAgent
from skills.social_writing import SocialWriterSkill

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
        self.add_skill(SocialWriterSkill())

    def create_social_post(self, article_title: str, article_content: str, platform_key: str) -> Dict:
        """
        [High-Level Action] 生成指定平台的社交媒体内容
        """
        # 获取平台配置
        from shared import config
        p_conf = config.SOCIAL_PLATFORMS.get(platform_key)
        if not p_conf:
            print(f"❌ 未知平台: {platform_key}")
            return None

        print(f"🤖 [{self.name}] 收到任务: 为《{article_title}》制作【{p_conf['name']}】内容")
        
        # 1. 调用通用写作技能
        post_data = self.use_skill("social_writing", {
            "source_title": article_title, 
            "source_content": article_content,
            "platform_config": p_conf
        })
        
        if not post_data:
            print(f"❌ [{self.name}] 写作失败")
            return None
            
        # 2. 调用美工技能 (封面图)
        # [Config Change] 用户要求不插入图片
        cover_url = "" 
        # cover_url = self.use_skill("cover_design", {
        #     "title": post_data.get('title', article_title),
        #     "keywords": post_data.get('keywords', [])
        # })
        
        # 3. 后处理: 格式化关键词
        raw_keywords = post_data.get('keywords', [])
        formatted_keywords = self._format_keywords(raw_keywords)
        
        # 4. 组装最终结果
        final_post = {
            "title": post_data.get('title'),
            "content": post_data.get('content'),
            "keywords": formatted_keywords,
            "cover_url": cover_url,
            "source_title": article_title,
            "platform": platform_key
        }
        
        print(f"✅ [{self.name}] 内容制作完成: {final_post['title']}")
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
