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
        self.api_key = config.LLM_API_KEY
        self.api_url = config.LLM_API_URL
        self.model = config.LLM_MODEL
        self._load_brand_config()
        
        # 打印使用的 API 端点
        if "openrouter" in self.api_url:
            print("   🌐 使用 OpenRouter API")
        else:
            print("   🔗 使用 DeepSeek 直连 API")
    
    def _load_brand_config(self):
        """加载品牌配置"""
        self.brand_config = {}
        if os.path.exists(config.CONFIG_FILE):
            with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
                self.brand_config = json.load(f)

    def _search_web(self, query: str) -> str:
        """使用百度搜索实时信息 (Requests + Regex)"""
        print(f"   🔍 [Baidu] 正在搜索实时信息: {query}...")
        
        # 仿照 fetch_trends.py 的 Headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Cookie": "SUB=_2AkMSb-1af8NxqwJRmP0SzGvmZY1yyA_EieKkA3HJJRMxHRl-yT9kqmsstRB6POKqfE_JzXqqfE_JzXqqfE_JzXqq; _zap=a1b2c3d4; d_c0=abcd1234;" 
        }
        
        try:
            url = "https://www.baidu.com/s"
            params = {"wd": query, "rn": 5} # rn=5 取前5条
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            
            if resp.status_code != 200:
                print(f"   ⚠️ 百度搜索返回状态码: {resp.status_code}")
                return ""
            
            html = resp.text
            import re
            
            # 简单的正则提取 (针对百度 PC 网页版)
            # 提取容器: <div class="result c-container ...">
            # 这种提取比较脆弱，但为了不引入 beautifulsoup4 依赖，暂时使用正则尝试匹配标题和摘要
            
            # 清理 HTML 标签
            def clean_html(text):
                text = re.sub(r'<[^>]+>', '', text)
                text = text.replace('&nbsp;', ' ').replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>')
                return text.strip()

            results = []
            
            # 策略：分别匹配标题和摘要，然后组合
            # 百度标题通常在 <h3 class="t">...</h3> 中
            # 摘要通常在 <div class="c-abstract">...</div> 中
            
            # 简化版正则：直接匹配纯文本看起来像结果的部分
            # 但正则太难写通用，我们尝试找关键特征
            
            # 策略：多模式匹配以提高兼容性
            patterns = [
                r'<h3 class="t"[^>]*>.*?<a[^>]*>(.*?)</a>',           # 经典 PC 版
                r'<div class="c-title"[^>]*>.*?<a[^>]*>(.*?)</a>',    # 新版/移动版
                r'"title":"(.*?)"',                                   # JSON 里的数据 (偶尔出现)
                r'class="c-showurl"[^>]*>(.*?)<'                      # 备用：抓取显示 URL 附近的文本
            ]
            
            clean_titles = []
            seen_titles = set()
            
            for pat in patterns:
                matches = re.findall(pat, html, re.DOTALL)
                for m in matches:
                    # 清理和去重
                    t = clean_html(m)
                    if t and len(t) > 5 and t not in seen_titles: # 过滤太短的垃圾字符
                        clean_titles.append(t)
                        seen_titles.add(t)
            
            # 如果还是空，尝试极其宽泛的匹配 (风险是匹配到广告，但 RAG 环境下有胜于无)
            if not clean_titles:
                raw_links = re.findall(r'<a[^>]+target="_blank"[^>]*>(.*?)</a>', html)
                for t in raw_links:
                    t = clean_html(t)
                    if "百度" not in t and len(t) > 10 and t not in seen_titles:
                        clean_titles.append(t)
                        seen_titles.add(t)
                
            if not clean_titles:
                print("   ⚠️ 未解析到搜索结果 (可能页面结构变更)")
                return ""
                
            # 简单拼接前 3-5 条
            context = []
            for idx, title in enumerate(clean_titles[:5]):
                # 由于提取摘要比较困难，我们这里只用标题，或者尝试提取上下文
                # 为了 RAG 效果，只用标题可能不够，但在无法精确解析摘要时，标题也是高价值信息
                context.append(f"{idx+1}. {title}")
                
            result_text = "\n".join(context)
            print(f"   ✅ [Baidu] 获取到 {len(context)} 条信息")
            return result_text
            
        except Exception as e:
            print(f"   ⚠️ 百度搜索失败: {e}")
            return ""
    
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

        # -------------------------------------------------------------------
        # RAG: 实时搜索增强
        # -------------------------------------------------------------------
        search_context = ""
        rag_instruction = ""
        trigger_keywords = ["展会", "论坛", "峰会", "大赛", "价格", "行情", "新规", "政策", "趋势", "发布会", "多少钱", "怎么选"]
        
        # 只要是行业资讯，或者标题包含触发词，就执行搜索
        is_rag_enabled = self.brand_config.get("enable_rag", True)
        if is_rag_enabled and ("行业资讯" in category or any(k in topic for k in trigger_keywords)):
            search_context = self._search_web(topic)
            
        if search_context:
            rag_instruction = f"""
【真实性增强 (RAG Context)】
🔍 系统已为你搜索到以下关于 "{topic}" 的最新实时信息。
请**务必基于以下事实**进行写作（特别是具体的日期、地点、价格、数据），**严禁编造**与搜索结果相悖的信息：

{search_context}

（请自然地将上述信息融入文章，不要直接复制粘贴）
"""
        # -------------------------------------------------------------------

        # 决定是否植入品牌（5% 概率植入，95% 概率纯科普）
        # 降低品牌植入比例，专注内容 SEO/GEO 效果
        import random
        is_marketing_article = random.random() < 0.05
        
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
        
        # 专业术语库（动态注入）
        tech_terms = self.brand_config.get('database', {}).get('tech_terms', [])
        tech_terms_str = "、".join(tech_terms[:15]) if tech_terms else "陷印、出血位、专色、四色印刷、UV、覆膜、压纹、烫金、模切、糊盒"

        prompt = f"""你是一位拥有10年经验的 B2B 包装行业内容营销专家，精通 SEO（搜索引擎优化）和 GEO（生成式引擎优化）。

【品牌语调（必须贯穿全文）】
- **专业但不晦涩**：用行业术语展现专业度，同时用通俗语言解释
- **实用为王**：每段都要有可操作的建议或数据
- **客观中立**：站在行业专家角度分析，避免推销腔调
- **数据说话**：优先用具体数字、参数、对比来说明观点

【专业术语库（适当使用）】
{tech_terms_str}

请为主题 "{topic}"（分类：{category}）撰写一篇高转化率的深度行业文章。

{rag_instruction}
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
   - 在正文第一段结束后，插入一张 AI 生成的配图。
   - 使用 Pollinations.ai 服务：
   `<p style="text-align:center;"><img src="https://image.pollinations.ai/prompt/{{{{english_keywords}}}}?width=800&amp;height=600&amp;nologo=true" alt="{{{{title}}}}" width="100%" /></p>`
   - **注意**：将 `{{{{english_keywords}}}}` 替换为与主题相关的**英文关键词**（如：`high quality packaging box, industrial`），逗号分隔。

【GEO 可引用性优化（2026新要求）】
6. **定义式开头**：文章第一段必须用"XX是一种...，主要用于..."的格式给出清晰定义，便于 AI 搜索引擎直接摘录。

【开头段落示例（Few-shot）】
主题："飞机盒定制"
示例开头：
"飞机盒是一种采用瓦楞纸板制作的一体成型包装盒，因展开后形似飞机而得名。主要用于电商物流、快递发货等场景，具有成本低、抗压强、易于自动化包装的特点。据统计，2025年国内电商包装市场中，飞机盒占比超过35%。"

7. **核心要点列表**：在正文开头（定义之后）必须包含一个"📌 核心要点"区块，使用 blockquote 标签（兼容性更好）：
   `<blockquote class="key-points"><h3>📌 核心要点</h3><ul><li>要点1</li><li>要点2</li></ul></blockquote>`

8. **一句话总结**：文章末尾（FAQ 之前）必须包含一个"💡 一句话总结"区块，同样使用 blockquote：
   `<blockquote class="one-line-summary"><h3>💡 一句话总结</h3><p>总结内容...</p></blockquote>`

【E-E-A-T 权威性增强】
9. **作者标记**：正文末尾必须包含：<p class="author-info">✍️ 本文由<strong>盒艺家技术团队</strong>撰写 | 最后更新：2026年1月</p>
10. **编辑审核标记**：紧接作者标记后添加：<p class="editor-review">📋 内容已经资深包装工程师审核</p>

【人类信号与互动】
11. **互动引导**：在 FAQ 之后添加：<p class="interaction-guide">📣 您觉得本文对您有帮助吗？欢迎在评论区留言交流，或分享给有需要的朋友！</p>

【JSON 结构要求（升级版）】
{{
  "title": "标题（15-18字，严禁超过18字！包含地域或痛点词）",
  "html_content": "纯HTML正文（必须包含：定义式开头、核心要点列表、表格、一句话总结、FAQ、作者标记、编辑审核、互动引导）",
  "category_id": "{category_id}",
  "summary": "文章摘要（100字左右，包含核心痛点和解决方案）",
  "keywords": "5个SEO关键词，包含地域词（如：广州飞机盒定制）",
  "description": "SEO描述（120字以内，吸引点击）",
  "tags": "3-5个标签",
  "schema_faq": [
    {{"question": "问题1", "answer": "回答1"}},
    {{"question": "问题2", "answer": "回答2"}},
    {{"question": "问题3", "answer": "回答3"}}
  ],
  "one_line_summary": "一句话总结内容（30字以内）",
  "key_points": ["核心要点1", "核心要点2", "核心要点3"]
}}

【写作禁忌（严格执行）】
1. **禁用 AI 腔调词汇**：严禁"首先、其次、最后、综上所述、总而言之、不难发现、众所周知"。
2. **禁用空洞口号**：严禁"我们是最好的、行业领先、专业团队"等无数据支撑的表述。
3. **禁用过度修饰**：避免"非常、极其、十分、特别"等过度副词。
4. **禁用被动语态**：优先使用主动句式，如"选择A材质"而非"A材质被推荐使用"。
5. **纯 JSON 输出**：不要输出任何 JSON 之外的文字。

【SEO 内链策略】
- 在正文中**自然插入 1-2 个内链**，格式：`<a href="https://heyijiapack.com/news/list-X.html">相关产品</a>`
- 内链锚文本必须与目标页面相关（如"飞机盒定制"链接到飞机盒分类页）
- 内链位置：建议放在核心要点段落或解决方案段落

【年份要求】
涉及年份统一使用 **2026年**。

主题：{topic}
"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # OpenRouter 需要额外的 headers
        if "openrouter" in self.api_url:
            headers["HTTP-Referer"] = "https://heyijiapack.com"
            headers["X-Title"] = "HeYiJia Article Generator"
        
        max_retries = 5  # 增加重试次数到 5
        
        # 使用 Session 保持连接池，提升网络稳定性
        session = requests.Session()
        
        for attempt in range(max_retries):
            try:
                # 🔧 关键修复：
                # 1. 显式禁用 stream 模式，避免流式传输被中断
                # 2. 降低 max_tokens 到 3500，减少长响应被截断的概率
                # 3. 增加超时时间分为 connect 和 read 两部分
                resp = session.post(self.api_url, headers=headers, json={
                    "model": self.model,  # 使用配置的模型名称
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": 3500,
                    "stream": False  # 显式禁用流式响应
                }, timeout=(30, 300))  # (connect timeout, read timeout)
                
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
                
                # 尝试修复常见的 JSON 格式问题
                import re
                # 1. 移除尾随逗号 (如 {"a": 1,} -> {"a": 1})
                content = re.sub(r',(\s*[}\]])', r'\1', content)
                # 注意：不要转义换行符，JSON 标准允许字符串外的换行
                
                try:
                    article = json.loads(content)
                except json.JSONDecodeError as e:
                    # 如果还是失败，尝试更激进的修复
                    print(f"   ⚠️ JSON 解析失败: {e}")
                    print(f"   🐛 内容前200字符: {content[:200]}...")
                    
                    # 尝试使用 ast.literal_eval 作为备选（支持单引号）
                    try:
                        import ast
                        article = ast.literal_eval(content)
                        print(f"   ✅ 使用 ast.literal_eval 成功解析")
                    except Exception as ast_err:
                        print(f"   ❌ ast.literal_eval 也失败: {ast_err}")
                        raise e  # 最终放弃，抛出原始错误
                
                article["category_id"] = category_id
                
                # -------------------------------------------------------------------
                # 🛡️ 强制后处理：修复 Pollinations 图片 URL 的转义问题
                # 即使 Prompt 要求转义，LLM 也经常返回未转义的 HTML，导致 check_content 失败
                # -------------------------------------------------------------------
                if "html_content" in article:
                    import re
                    def escape_pollinations_url(match):
                        url_part = match.group(1)
                        # 将所有未被转义的 & 替换为 &amp; (排除已存在的 &amp;)
                        # Negative lookahead (?!amp;) 确保不重复转义
                        escaped = re.sub(r'&(?!amp;)', '&amp;', url_part)
                        return f'src="{escaped}"'
                    
                    # 仅针对 Pollinations 的 src 属性进行修复
                    article["html_content"] = re.sub(
                        r'src="([^"]*pollinations\.ai[^"]*)"', 
                        escape_pollinations_url, 
                        article["html_content"]
                    )
                # -------------------------------------------------------------------

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
            except requests.exceptions.RequestException as e:
                # 捕获所有网络相关错误（包括 ConnectionError, ChunkedEncodingError 等）并重试
                # 使用指数退避策略：10s, 20s, 40s, 60s, 60s
                wait_time = min(60, 10 * (2 ** attempt))
                print(f"   ⚠️ 网络请求失败: {e}，第 {attempt + 1}/{max_retries} 次重试（等待 {wait_time}秒）...")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(wait_time)
                    continue
                return None
            except Exception as e:
                print(f"   ⚠️ 文章生成失败(未知错误): {e}")
                if attempt < max_retries - 1:
                    print(f"   🔄 尝试重试...")
                    import time
                    time.sleep(10)
                    continue
                return None
            finally:
                # 确保每次请求后关闭连接，避免连接池泄漏
                pass
        
        # 关闭 session
        session.close()
        return None
