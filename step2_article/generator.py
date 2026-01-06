# step2_article/generator.py
"""
AI 文章生成器
"""
import json
import requests
from typing import Dict, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import config


class ArticleGenerator:
    """AI 文章生成器"""
    
    def __init__(self):
        self.api_key = config.DEEPSEEK_API_KEY
        self.api_url = config.DEEPSEEK_API_URL
        self._load_brand_config()
    
    def _load_brand_config(self):
        """加载品牌配置"""
        self.brand_config = {}
        if os.path.exists(config.CONFIG_FILE):
            with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.brand_config = json.load(f)
    
    def generate(self, topic: str, category: str) -> Optional[Dict]:
        """根据标题生成 SEO 文章"""
        category_id = config.CATEGORY_MAP.get(category, "2")
        
        # 品牌信息
        brand = self.brand_config.get('brand', {})
        brand_name = brand.get('name', '盒艺家')
        
        # 品牌卖点
        selling_points = "、".join(self.brand_config.get('selling_points', [])[:4])
        
        # 针对“专业知识”分类的特殊指令
        tech_requirements = ""
        if "专业知识" in category:
            tech_requirements = """
【专业深度增强（关键）】
本文为"专业知识"科普，必须包含以下硬核干货（至少覆盖 2 点）：
1. **印前与加工知识**：涉及文件处理参数（如：CMYK模式、出血位3mm、陷印处理）或加工流程细节。
2. **工艺技术参数**：提及具体数值（如：烫金温度110℃、UV光固化能量、胶印175线等）。
3. **材料科学**：深度解析材料属性（如：瓦楞楞型A/B/E区别、纸张克重与挺度关系）。
4. **标准引用**：**必须引用至少1个**相关标准（如：ISO 12647 色彩标准、GB/T 6543 纸箱国标、G7认证、FSC森林认证等），展现权威性。
"""

        # 决定是否植入品牌（20% 概率植入，80% 概率纯科普）
        import random
        # 种子设为 None 确保随机，或者用 hash(topic) 保证同一标题结果固定？用随机即可
        is_marketing_article = random.random() < 0.2
        
        if is_marketing_article:
            brand_instruction = f"""
4. **品牌植入（适度营销）**：
   - 本文为**品牌软文**，请在解决痛点时，自然引出“{brand_name}”作为解决方案。
   - 重点提及“3秒AI智能报价”和“1个起订”的优势，解决传统工厂门槛高的问题。
   - 品牌提及次数控制在 3-5 次以内，不要生硬堆砌。
"""
        else:
            brand_instruction = """
4. **纯净科普（去营销化）**：
   - **本文必须是100%纯干货科普**，严禁提及“盒艺家”或任何具体品牌名。
   - 全文侧重于行业标准、工艺参数、设计趋势分析。
   - 即使在解决方案部分，也只能建议“寻找拥有数字化报价系统的现代化工厂”，而不要点名具体商家。
   - 目标是建立中立、权威的行业专家形象，而非推销员形象。
"""

        # 材质库
        materials = self.brand_config.get('database', {}).get('materials', [])
        materials_str = "、".join(materials[:10]) # 取前10个避免过长

        prompt = f"""你是一位拥有10年经验的 B2B 包装行业内容营销专家，精通 SEO（搜索引擎优化）和 GEO（生成式引擎优化）。
请为主题 "{topic}"（分类：{category}）撰写一篇高转化率的深度行业文章。

{tech_requirements}
【核心策略】
1. **PAS 模型写作**：先指出客户痛点（Pain），再描述严重后果，最后给出解决方案（Solution）。
2. **场景化材质推荐**：
   - 你精通以下材质：{materials_str} 等。
   - 在正文中，必须根据产品的使用场景（如：电商运输、高端送礼、食品接触），**指名道姓地推荐 1-2 种最合适的具体材质**（例如：“电商发货建议选高硬度 E坑瓦楞”，“高端礼盒建议选 157g铜版纸裱灰板”），展现行家身份。
3. **GEO (Geographic) 地域优化**：识别该产品的核心产业带或热门市场（如义乌小商品、广州服装、深圳电子、江浙沪包邮区等），在正文中自然植入 2-3 个地域关键词。
4. **GEO (Generative Engine) 结构化**：正文中**必须包含 1 个 HTML 表格**（例如：不同材质成本对比、纸盒 vs 胶盒优劣势对比）。
{brand_instruction}
5. **自动配图（重要）**：
   - 在正文第一段结束后，插入一张高质量配图。
   - 使用标签：`<img src="https://image.pollinations.ai/prompt/{{english_prompt}}?width=800&height=600&nologo=true" alt="{{title}}" style="width:100%; border-radius:8px; margin: 20px 0;">`
   - **注意**：必须将 `{{english_prompt}}` 替换为当前主题的**英文描述**（例如：`luxury_gift_box_packaging_design_minimalist`），单词间用下划线连接。

【JSON 结构要求】
{{
  "title": "标题（15-20字，包含地域或痛点词，吸引点击）",
  "html_content": "纯HTML正文。
    - 使用 <h2> 小标题分段
    - **必须包含一个 <table> 表格**
    - 结尾必须包含 <h3>常见问题 (FAQ)</h3> 和 3 个相关的问答对（其中一个问答必须关联‘如何获取报价’，并回答‘使用我们的AI 3秒报价系统’）
    - 重点词句加粗",
  "category_id": "{category_id}",
  "summary": "文章摘要（100字左右，包含核心痛点和解决方案）",
  "keywords": "5个SEO关键词，包含地域词（如：广州飞机盒定制）",
  "description": "SEO描述（120字以内，吸引点击）",
  "tags": "3-5个标签"
}}

【写作禁忌】
1. 严禁使用 "首先、其次、最后" 这种生硬的 AI 腔调。
2. 严禁出现 "我们是最好的" 这种空洞口号，要用数据说话。
3. 不要输出任何 JSON 之外的文字。无论如何只输出 JSON。

【年份要求】
涉及年份统一使用 **2026年**。

主题：{topic}
"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = requests.post(self.api_url, headers=headers, json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 4096
                }, timeout=120)
                
                # 检查 HTTP 状态码
                if resp.status_code == 429:  # Rate limit
                    wait_time = (attempt + 1) * 10  # 10s, 20s, 30s
                    print(f"   ⏳ API 限流，等待 {wait_time} 秒后重试...")
                    import time
                    time.sleep(wait_time)
                    continue
                
                if resp.status_code != 200:
                    print(f"   ⚠️ API 返回状态码: {resp.status_code}")
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(5)
                        continue
                    return None
                
                content = resp.json()["choices"][0]["message"]["content"]
                content = content.replace("```json", "").replace("```", "").strip()
                
                # 提取 JSON
                first_brace = content.find('{')
                last_brace = content.rfind('}')
                if first_brace != -1 and last_brace > first_brace:
                    content = content[first_brace:last_brace + 1]
                
                article = json.loads(content)
                article["category_id"] = category_id
                
                print(f"   ✅ 文章生成成功: {article.get('title', '无标题')}")
                return article
                
            except json.JSONDecodeError as e:
                print(f"   ⚠️ JSON 解析失败: {e}")
                return None
            except KeyError as e:
                print(f"   ⚠️ API 响应格式异常: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(5)
                    continue
                return None
            except requests.exceptions.Timeout:
                print(f"   ⏳ 请求超时，第 {attempt + 1}/{max_retries} 次重试...")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(5)
                    continue
                return None
            except Exception as e:
                print(f"   ⚠️ 文章生成失败: {e}")
                return None
        
        return None
