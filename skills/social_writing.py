import sys
import os
import json
from typing import Dict, Any

from core.skill import BaseSkill
from shared import config
from shared.utils import call_llm

class SocialWriterSkill(BaseSkill):
    """
    技能: 全平台社交媒体文案创作 (矩阵版)
    集成 7 种不同的创作人格，针对不同平台输出定制化风格的文章。
    """
    def __init__(self):
        super().__init__(
            name="social_writing",
            description="根据平台特性，将长文章重写为适应不同社交媒体的内容"
        )
        self._init_prompts()

    def _init_prompts(self):
        """初始化各平台的专属人设和指令"""
        self.PROMPTS = {
            "douyin": {
                "role": "抖音爆款文案大神",
                "style": "情绪饱满、反转强烈、黄金三秒法则、引导互动",
                "desc": "你擅长写那种让人看了就想点赞的短视频文案。切记：只写口播文案，不要写分镜脚本！不要出现【只是画面】这种描述。",
                "rule": "1. 必须是纯文案，严禁出现'画面：'、'镜头：'等脚本格式。\n2. 开篇必须通过提问或痛点抓住用户。\n3. 结尾必须有强引导（点赞/关注）。"
            },
            "kuaishou": {
                "role": "快手老铁/接地气实干家",
                "style": "大白话、实在、热情、称兄道弟",
                "desc": "通过朴实的语言分享行业干货。切记：只写口播文案，不要写分镜脚本！",
                "rule": "1. 必须是纯文案，严禁脚本格式。\n2. 语气要像跟朋友聊天。\n3. 多用'咱们'、'老铁'、'这款'。"
            },
            "wechat_video": {
                "role": "微信视频号情感导师/行业专家",
                "style": "沉稳、有温度、正能量、讲故事",
                "desc": "面向成熟人群，内容要有深度。切记：只写口播文案，不要写分镜脚本！",
                "rule": "1. 必须是纯文案，严禁脚本格式。\n2. 逻辑清晰，娓娓道来。\n3. 传递'品质'和'匠心'。"
            },
            "xhs": {
                "role": "小红书种草达人/精致生活家",
                "style": "K.E.E.P原则、Emoji丰富、集美/宝子画风",
                "desc": "分享好物和避坑指南，图片感强（虽然只写文字）。",
                "rule": "1. 标题要用【】符号和惊叹号。\n2. 全文Emoji含量>20%。\n3. 结尾求关注求交作业。"
            },
            "baijiahao": {
                "role": "资深行业评论员/自媒体人",
                "style": "新闻资讯风、客观理性、权威感、标题党",
                "desc": "面向搜索用户，内容要干货满满，条理分明。",
                "rule": "1. 标题要包含热点或强行业关键词。\n2. 采用'总-分-总'结构。\n3. 第一段需包含核心摘要。"
            },
            "weibo": {
                "role": "微博段子手/热点观察员",
                "style": "短小精悍、毒舌或幽默、话题感强 (Hashtag)",
                "desc": "利用碎片化时间阅读，一针见血。",
                "rule": "1. 全文不要太长。\n2. 必须带2-3个超级话题 (#...#)。\n3. 设置悬念或槽点。"
            },
            "bilibili": {
                "role": "B站硬核UP主/二次元科普君",
                "style": "玩梗、硬核、深度解析、互动强",
                "desc": "面向年轻求知欲强的用户。切记：只写文案，不要写分镜脚本！",
                "rule": "1. 必须是纯文案，严禁脚本格式。\n2. 适当玩梗 (如: '要素察觉', '下次一定')。\n3. 开头要喊'各位观众老爷好'。"
            }
        }

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Input: source_title, source_content, platform_config
        """
        s_title = input_data.get("source_title", "")
        s_content = input_data.get("source_content", "")
        p_conf = input_data.get("platform_config", {})
        
        # 识别平台 Key (config 中 key 应与 prompts key 对应)
        # 我们在 config.py 中定义的 key 就是 douyin, xhs 等
        # 但 runner 传过来的是 p_conf 字典，我们需要反推 key 或者让 runner 传 key
        # 修正: Agent runner 并没有把 key 塞进 platform_config，agent_runner 传了 key 给 agent, agent传了 p_conf
        # 我们需要在 Agent 中把 'key' 也塞进去，或者通过 p_conf['name'] 模糊匹配
        # 最稳妥：在 agent.py 里把 key 塞入 p_conf 或 input_data
        
        # 暂时用 name 模糊匹配，或者增加一个 mapping
        p_name = p_conf.get("name", "")
        p_key = "xhs" # default
        
        if "抖音" in p_name: p_key = "douyin"
        elif "快手" in p_name: p_key = "kuaishou"
        elif "微信" in p_name: p_key = "wechat_video"
        elif "小红书" in p_name: p_key = "xhs"
        elif "百家" in p_name: p_key = "baijiahao"
        elif "微博" in p_name: p_key = "weibo"
        elif "B" in p_name or "bili" in p_name.lower(): p_key = "bilibili"
        
        prompt_setting = self.PROMPTS.get(p_key, self.PROMPTS["xhs"])
        
        limit_title = p_conf.get("title_limit", 20)
        limit_content = p_conf.get("content_limit", 900)
        limit_kw = p_conf.get("keywords_limit", 4)
        
        print(f"      ✍️ [Skill] 激活人设: 【{prompt_setting['role']}】 -> 创作 {p_name} 内容...")
        
        # 1. 构造 System Prompt
        system_prompt = f"""你现在的身份是：{prompt_setting['role']}。
你的写作风格是：{prompt_setting['style']}。
任务描述：{prompt_setting['desc']}

【核心规则】
{prompt_setting['rule']}
4. 严格遵守字数限制：标题<{limit_title}字，正文严格控制在{limit_content}字以内(可少不可多)。
5. 提取 {limit_kw} 个关键词。
6. 输出仅限纯文本，严禁包含任何图片URLs、[图片]占位符或Markdown图片语法 ![](...)。
"""

        # 2. 构造 User Prompt
        user_prompt = f"""
请将这篇枯燥的文章重写为一篇精彩的【{p_name}】爆款内容：

【原文标题】：{s_title}
【原文片段】：
{s_content[:2000]}...

【输出格式】(JSON):
{{
    "title": "你的神标题",
    "content": "你的精彩正文",
    "keywords": ["tag1", "tag2"]
}}
"""

        # 3. 调用 LLM
        try:
            resp = call_llm(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=config.LLM_MODEL,
                temperature=0.85 # 稍微高一点增加创意
            )
            
            # 4. 解析
            content_str = resp.strip()
            start = content_str.find("{")
            end = content_str.rfind("}")
            if start != -1 and end != -1:
                json_str = content_str[start:end+1]
                data = json.loads(json_str)
                return data
            else:
                # Fallback extraction if JSON fails
                return {
                    "title": f"🔥 {s_title[:15]}",
                    "content": resp, # Return raw text as content
                    "keywords": []
                }
                
        except Exception as e:
            print(f"      ❌ 生成异常: {e}")
            return None
