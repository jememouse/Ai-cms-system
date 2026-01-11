import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.skill import BaseSkill

class CoverDesignSkill(BaseSkill):
    """
    技能: 生成高审美封面图 (Pollinations)
    """
    def __init__(self):
        super().__init__(
            name="cover_design",
            description="根据标题和关键词生成极简高审美封面图"
        )

    def execute(self, input_data: Dict) -> str:
        """
        Input: {"title": str, "keywords": str}
        Output: image_url (str)
        """
        title = input_data.get("title", "")
        keywords = input_data.get("keywords", "")
        
        # 构造 Prompt (复用之前验证过的最佳实践)
        base_prompt = "minimalist aesthetics, packaging design close-up, soft studio lighting, 3d render, blender, pastel colors, high quality, 8k"
        
        # 简单的关键词处理（假设关键词里可能混杂中文，但在 URL encoding 下通常 Pollinations 能处理或忽略）
        # 最好是纯英文，但为了节省一次 LLM 翻译调用，我们直接拼接
        final_prompt = f"{base_prompt} {keywords}"
        
        encoded_prompt = requests.utils.quote(final_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1360&nologo=true"
        
        return url
