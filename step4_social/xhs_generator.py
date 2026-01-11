
import json
import requests
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import config

class XHSGenerator:
    """小红书内容生成器 (The Creator)"""
    
    def __init__(self):
        self.api_key = config.LLM_API_KEY
        self.api_url = config.LLM_API_URL
        self.model = config.LLM_MODEL
        
        # 定义核心 Prompt
        self.SYSTEM_PROMPT = """你是一个在包装行业深耕10年的资深采购经理，人设是“犀利、懂行、爱分享”。
你的目标是将枯燥的行业知识，转化为小红书平台爆火的“种草/避坑”笔记。

请遵循 [K.E.E.P] 创作公式：
1. K (Keywords): 标题必须包含痛点关键词（如“被坑哭”、“血泪教训”、“老板必看”）。
2. E (Emoji): 全文 Emoji 含量 > 15%，每段开头必须用 Emoji 下沉。
3. E (Emotion): 情绪价值拉满，不要讲课，要像闺蜜一样吐槽或安利。
4. P (Call to Action): 结尾引导评论或私信。

语言风格：
- 拒绝爹味，拒绝教科书式的废话。
- 多用短句，多用感叹号！
- 加上 #标签。
"""

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM (复用 Step 2 的逻辑)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if "deepseek" in self.api_url:
             headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        # OpenRouter needs extra headers
        if "openrouter" in self.api_url:
            headers["HTTP-Referer"] = "https://github.com/jememouse/deepseek-feisu-cms"
            headers["X-Title"] = "DeepSeek CMS"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            "temperature": 1.3  # 小红书需要高创造性
        }
        
        try:
            # config.LLM_API_URL 已经是完整路径 (e.g. .../chat/completions)
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
            else:
                print(f"❌ LLM Error: {resp.status_code} - {resp.text}")
                return ""
        except Exception as e:
            print(f"❌ Request Error: {e}")
            return ""

    def generate_note(self, title: str, content: str) -> dict:
        """生成小红书笔记"""
        print(f"   ✍️ 正在将文章重写为小红书风格: {title}...")
        
        # 截取前 2000 字作为上下文，避免 token 溢出
        context = content[:2000] + "..."
        
        prompt = f"""
请将以下长文章改写为一篇小红书笔记。

【原始文章标题】: {title}
【原始文章内容】: 
{context}

---
【要求】
1. 输出格式必须是 JSON，包含 'title' 和 'content' 和 'keywords' 三个字段。
2. 'title': 20字以内，极其吸睛。
3. 'content': 900字以内，分段清晰。
4. 'keywords': 提取 5 个适合做标签的关键词 (e.g. "包装设计", "创业搞钱")。

返回示例:
{{
  "title": "...",
  "content": "...",
  "keywords": "..."
}}
"""
        result = self._call_llm(prompt)
        
        # 清洗 Markdown 标记
        result = result.replace("```json", "").replace("```", "").strip()
        
        try:
            data = json.loads(result)
            return data
        except json.JSONDecodeError:
            print("   ⚠️ JSON 解析失败，返回原始内容")
            # Fallback
            return {
                "title": f"🔥 {title}",
                "content": result,
                "keywords": "包装定制, 避坑指南"
            }

    def generate_cover_image(self, note_title: str, keywords: str) -> str:
        """生成封面图 URL (Pollinations.ai)"""
        print(f"   🖼️ 正在构思封面图: {note_title}...")
        
        # 用 LLM 翻译 prompts 稍微有点慢，这里直接用规则拼接，提升速度
        # 小红书风格：极简、高饱和、特写、文字留白
        
        # 提取英文关键词 (简单映射，实际项目中可以用 LLM 翻)
        # 这里为了演示速度，我们用固定的高美感词 + 标题的英文翻译(假定)
        # 更好的方式是再调一次 LLM 让它生成英文 Prompt。
        
        prompt_prompt = f"Create a stable diffusion prompt for this Xiaohongshu cover: '{note_title}'. Keywords: {keywords}. Style: Minimalist, High Aesthetic, 3D Render, Soft lighting, text space in center. Output ONLY the English prompt string."
        # image_prompt = self._call_llm(prompt_prompt) 
        # 考虑到成本和速度，我们直接构造：
        
        base_prompt = "minimalist aesthetics, packaging design close-up, soft studio lighting, 3d render, blender, pastel colors, high quality, 8k"
        
        # 构造 URL
        # Pollinations 格式: https://image.pollinations.ai/prompt/{prompt}?width={w}&height={h}
        encoded_prompt = requests.utils.quote(f"{base_prompt} {keywords}")
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1360&nologo=true"
        
        return url

