
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
        
        # 定义 4 种差异化人设 (Personas)
        self.STYLES = {
            "insider": {
                "role": "行业老炮 (The Insider)",
                "tone": "揭秘、犀利、警告",
                "instruction": """这里是包装行业的'内幕揭秘'现场。你的语气要像一个老行家在警告新人，多用'千万别'、'听句劝'，不讲废话，只讲干货。重点通过'避坑'来带出产品优势。"""
            },
            "bestie": {
                "role": "种草闺蜜 (The Bestie)",
                "tone": "情绪化、热情、夸张",
                "instruction": """你是一个爱分享的种草博主。语气要超级激动，多用 Emoji (✨💖🔥)，像发现新大陆一样跟姐妹们分享。多用感叹号，重点强调'颜值'、'仪式感'和'开箱体验'。"""
            },
            "boss": {
                "role": "精明老板 (The Boss)",
                "tone": "理性、数据驱动、省钱",
                "instruction": """你是一个精打细算的老板。只关心'性价比'、'转化率'和'成本控制'。用数据说话，告诉大家怎么用最少的钱做出最高级的包装。风格要专业但接地气，直击B2B痛点。"""
            },
            "artist": {
                "role": "美学设计师 (The Artist)",
                "tone": "高冷、极简、诗意",
                "instruction": """你是一个追求极致美学的设计师。文字要少而精，注重排版留白。多谈'质感'、'触感'、'视觉语言'。语气要高冷一点，不屑于谈价格，只谈品味。"""
            }
        }

    def _call_llm(self, prompt: str, system_prompt: str) -> str:
        """调用 LLM"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if "openrouter" in self.api_url:
            headers["HTTP-Referer"] = "https://github.com/jememouse/deepseek-feisu-cms"
            headers["X-Title"] = "DeepSeek CMS"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 1.3  # 高创造性
        }
        
        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content']
                if not content: return ""
                return content
            else:
                print(f"❌ LLM Error: {resp.status_code} - {resp.text}")
                return ""
        except Exception as e:
            print(f"❌ Request Error: {e}")
            return ""

    def generate_note(self, title: str, content: str) -> dict:
        """生成小红书笔记"""
        import random
        
        # 1. 随机选择一种风格
        style_key = random.choice(list(self.STYLES.keys()))
        style = self.STYLES[style_key]
        
        print(f"   ✍️ 正在重写为小红书风格: {title}")
        print(f"      🎭 本次人设: {style['role']} ({style['tone']})")
        
        # 截取前 2000 字
        context = content[:2000] + "..."
        
        system_prompt = f"""你现在是：{style['role']}。
核心人设指令：
{style['instruction']}

通用规则 [K.E.E.P]:
1. 关键词(Keywords)要痛点密集。
2. Emoji 含量 > 15%，作为视觉锚点。
3. 结尾要有互动钩子。
"""

        prompt = f"""
请将以下长文章改写为一篇完全符合你当前人设的小红书笔记。

【原始文章标题】: {title}
【原始文章内容】: 
{context}

---
【严格限制】
1. **标题**: 必须在 **18个字以内**！严禁超时！
   - **借势要求**: 如果原文提到社会热点（如繁花/哈尔滨/流行色），**必须**把它提炼到标题里！
   - **禁止**: 严禁使用 "分享"、"推荐"、"安利" 等平庸词汇。
2. **正文**: 必须在 **850字以内**！严禁超时！
3. **风控安全 (Critical Safety)**:
   - **广告法红线**: 严禁出现 "第一"、"最"、"绝对"、"100%"、"首选" 等极限词。
   - **平台红线**: 严禁出现 "私信"、"加V"、"赚钱"、"暴利"、"引流" 等敏感词。
   - **防AI检测**: 严禁使用 "家人们"、"今天给大家分享"、"宝宝们" 等模板化开场。第一句必须直接抛出痛点、悬念或反直觉结论。
4. **差异化**: 你的每一次输出都必须独一无二，不要雷同。
5. **输出格式**: 仅返回 JSON。

返回 JSON 示例:
{{
  "title": "...",
  "content": "...",
  "keywords": "..."
}}
"""
        result = self._call_llm(prompt, system_prompt)
        
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
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1360&nologo=true&key={config.POLLINATIONS_API_KEY}"
        
        return url

