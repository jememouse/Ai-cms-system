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
        
        # 获取限制值
        title_limit = p_conf.get('title_limit', 18)
        content_limit = p_conf.get('content_limit', 900)
        
        # 1. 调用写作技能
        post_data = self.use_skill("social_writing", {
            "source_title": article_title, 
            "source_content": article_content,
            "platform_config": p_conf
        })
        
        if not post_data:
            print(f"❌ [{self.name}] 写作失败")
            return None
        
        # 2. 检查标题是否超限 → AI 自压缩
        generated_title = post_data.get('title', '')
        if len(generated_title) > title_limit:
            print(f"   ⚠️ [Check] 标题超限 ({len(generated_title)}>{title_limit})，启动 AI 自压缩...")
            compressed_title = self._compress_title(generated_title, title_limit)
            if compressed_title:
                post_data['title'] = compressed_title
                print(f"   ✅ [Compress] 压缩成功: {compressed_title} ({len(compressed_title)}字)")
            
        # 3. 调用美工技能 (封面图) - 已禁用
        cover_url = ""
        
        # 4. 后处理: 格式化关键词
        raw_keywords = post_data.get('keywords', [])
        formatted_keywords = self._format_keywords(raw_keywords)
        
        # 5. 智能截断兜底: 如果 AI 压缩仍超限，作为最后保障
        raw_title = post_data.get('title', '')
        raw_content = post_data.get('content', '')
        
        if len(raw_title) > title_limit:
            print(f"   ⚠️ [Fallback] AI压缩后仍超限，启用智能截断")
            raw_title = self._smart_truncate(raw_title, title_limit)
        
        if len(raw_content) > content_limit:
            print(f"   ⚠️ [Truncate] 内容超限 ({len(raw_content)}>{content_limit}), 智能截断")
            raw_content = self._smart_truncate(raw_content, content_limit)
        
        # 4. 组装最终结果
        final_post = {
            "title": raw_title,
            "content": raw_content,
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
        
        # [Requirement] 强制加入品牌词 "盒艺家"
        # 即使 AI 没生成，也必须要有。放在第一个位置。
        brand_tag = "盒艺家"
        final_tags.append(f"#{brand_tag}")
        
        for p in parts:
            tag = p.strip().lstrip("#")
            # 去重：如果 AI 也生成了盒艺家，不要重复添加
            if tag and tag != brand_tag:
                final_tags.append(f"#{tag}")
        return " ".join(final_tags)

    def _compress_title(self, original_title: str, max_len: int) -> str:
        """
        AI 自压缩: 让 LLM 自己将超限标题压缩到指定长度
        比硬截断更智能，能保持语义完整性
        """
        from shared import config
        from shared.utils import call_llm
        
        compress_prompt = f"""你是一个标题压缩专家。请将以下标题压缩到 {max_len} 字以内，保持核心含义不变。

【原标题】：{original_title}（{len(original_title)}字）
【目标】：≤{max_len}字

【要求】：
1. 必须保留核心关键词和主题
2. 可以删除修饰词、语气词
3. 直接输出压缩后的标题，不要任何解释

【压缩后标题】："""

        try:
            result = call_llm(
                prompt=compress_prompt,
                model=config.LLM_MODEL,
                temperature=0.3  # 低温度保证稳定性
            )
            compressed = result.strip().strip('"').strip('【').strip('】')
            
            # 验证压缩结果
            if compressed and len(compressed) <= max_len:
                return compressed
            else:
                print(f"   ⚠️ [Compress] 压缩结果仍超限或为空，使用原标题")
                return None
        except Exception as e:
            print(f"   ❌ [Compress] 压缩失败: {e}")
            return None

    def _smart_truncate(self, text: str, max_len: int) -> str:
        """
        智能截断: 
        - 优先在句末标点（。！？…）处截断
        - 其次在逗号、分号处截断
        - 最后硬截断并加省略号
        """
        if len(text) <= max_len:
            return text
        
        # 在限制范围内查找最佳截断点
        search_region = text[:max_len]
        
        # 优先级1: 句末标点
        for punct in ['。', '！', '？', '…', '!', '?']:
            pos = search_region.rfind(punct)
            if pos > max_len * 0.5:  # 至少保留一半内容
                return text[:pos+1]
        
        # 优先级2: 逗号、分号
        for punct in ['，', ',', '；', ';', '、']:
            pos = search_region.rfind(punct)
            if pos > max_len * 0.6:
                return text[:pos] + '…'
        
        # 优先级3: 硬截断 + 省略号
        return text[:max_len-1] + '…'
