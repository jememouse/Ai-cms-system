# trends_generator/fetch_trends.py
"""
热点抓取与 AI 分析模块
"""
import requests
import json
import os
import re
import time
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env 环境变量
load_dotenv()

# 配置 DeepSeek API
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-your-key-here")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# URLs
BAIDU_HOT_URL = "https://top.baidu.com/board?tab=realtime"
WEIBO_HOT_URL = "https://s.weibo.com/top/summary"
TOUTIAO_HOT_URL = "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc"
BILIBILI_HOT_URL = "https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all"
KR36_HOT_URL = "https://36kr.com/newsflashes"

# 文件路径 (指向项目根目录)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRENDS_FILE = os.path.join(BASE_DIR, "trends_data.json")
CONFIG_FILE = os.path.join(BASE_DIR, "box_artist_config.json")
CACHE_FILE = os.path.join(BASE_DIR, ".cache", "trends_cache.json")
CACHE_EXPIRY_HOURS = 4  # 缓存有效期

def _load_cache():
    """加载缓存数据"""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def _save_cache(cache_data):
    """保存缓存数据"""
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=2)

def _get_cached(key):
    """获取缓存，检查是否过期"""
    cache = _load_cache()
    if key in cache:
        cached_time = datetime.fromisoformat(cache[key].get("time", "2000-01-01"))
        if (datetime.now() - cached_time).total_seconds() < CACHE_EXPIRY_HOURS * 3600:
            print(f"   📦 使用缓存: {key}")
            return cache[key].get("data", [])
    return None

def _set_cached(key, data):
    """设置缓存"""
    cache = _load_cache()
    cache[key] = {"time": datetime.now().isoformat(), "data": data}
    _save_cache(cache)

# 通用 Header
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Cookie": "SUB=_2AkMSb-1af8NxqwJRmP0SzGvmZY1yyA_EieKkA3HJJRMxHRl-yT9kqmsstRB6POKqfE_JzXqqfE_JzXqqfE_JzXqq; _zap=a1b2c3d4; d_c0=abcd1234;" # 简单的 Mock Cookie 增加成功率
}

def fetch_baidu_hot():
    """抓取百度热搜榜"""
    print("📡 [Baidu] 正在抓取...")
    try:
        resp = requests.get(BAIDU_HOT_URL, headers=HEADERS, timeout=10)
        resp.encoding = 'utf-8'
        html = resp.text
        titles = re.findall(r'<div class="c-single-text-ellipsis">\s*(.*?)\s*</div>', html)
        clean_titles = [t.strip() for t in titles if t.strip() and "置顶" not in t][:15] # 取前15
        print(f"   -> 获取到 {len(clean_titles)} 条")
        return clean_titles
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return []

def fetch_weibo_hot():
    """抓取微博热搜"""
    print("📡 [Weibo] 正在抓取...")
    try:
        resp = requests.get(WEIBO_HOT_URL, headers=HEADERS, timeout=10)
        html = resp.text
        # 微博格式: <a href="/weibo?q=xxx" target="_blank">xxx</a>
        # 排除 "javascript:void(0)" 等置顶广告
        titles = re.findall(r'<a href="/weibo\?q=[^"]+" target="_blank">([^<]+)</a>', html)
        clean_titles = [t.strip() for t in titles if t.strip()][:15]
        print(f"   -> 获取到 {len(clean_titles)} 条")
        return clean_titles
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return []

def fetch_toutiao_hot():
    """抓取头条热榜 (抖音/字节系数据)"""
    print("📡 [Toutiao] 正在抓取...")
    try:
        resp = requests.get(TOUTIAO_HOT_URL, headers=HEADERS, timeout=10)
        data = resp.json()
        
        # 解析头条 JSON 结构
        clean_titles = []
        if "fixed_top_data" in data:
            for item in data["fixed_top_data"]:
                clean_titles.append(item.get("Title"))
                
        if "data" in data:
            for item in data["data"]:
                clean_titles.append(item.get("Title"))
                
        # 取前15
        clean_titles = clean_titles[:15]
        print(f"   -> 获取到 {len(clean_titles)} 条")
        return clean_titles
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return []

def fetch_bilibili_hot():
    """抓取B站热门视频 (年轻人趋势)"""
    print("📡 [Bilibili] 正在抓取...")
    try:
        # B站 API 对 Cookie 很敏感，有时甚至不需要 Cookie 只要 UA
        # 这里单独定义 Header，不带 Cookie
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(BILIBILI_HOT_URL, headers=headers, timeout=10)
        data = resp.json()
        
        clean_titles = []
        if data.get("code") == 0 and "data" in data and "list" in data["data"]:
            for item in data["data"]["list"]:
                clean_titles.append(item.get("title"))
                
        clean_titles = clean_titles[:15]
        print(f"   -> 获取到 {len(clean_titles)} 条")
        return clean_titles
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return []

def fetch_36kr_hot():
    """抓取36氪快讯 (行业/商业)"""
    print("📡 [36Kr] 正在抓取...")
    try:
        resp = requests.get(KR36_HOT_URL, headers=HEADERS, timeout=10)
        html = resp.text
        
        # 优化提取逻辑，不用简单的正则防止提前截断
        start_marker = "window.initialState="
        if start_marker in html:
            start_idx = html.find(start_marker) + len(start_marker)
            # 找到随后的脚本结束标签或者分号
            # 但 JSON 可能包含分号，最稳的是找 </script>
            end_idx = html.find("</script>", start_idx)
            
            json_str = html[start_idx:end_idx].strip()
            # 去掉末尾可能的分号
            if json_str.endswith(";"):
                json_str = json_str[:-1]
                
            try:
                data = json.loads(json_str)
                clean_titles = []
                # 路径: newsflashCatalogData -> data -> newsflashList -> data -> itemList
                items = data.get("newsflashCatalogData", {}).get("data", {}).get("newsflashList", {}).get("data", {}).get("itemList", [])
                for item in items:
                    title = item.get("templateMaterial", {}).get("widgetTitle")
                    if title:
                        clean_titles.append(title)
                
                clean_titles = clean_titles[:15]
                print(f"   -> 获取到 {len(clean_titles)} 条")
                return clean_titles
                
            except json.JSONDecodeError:
                print("   ⚠️ 36Kr: JSON 解析失败")
                return []
        else:
            print("   ⚠️ 36Kr: 未找到数据源标记")
            return []
            
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        return []

def fetch_zhihu_hot_questions(seed_words):
    """抓取知乎热门问答 (高意图问答，适合 GEO 优化)"""
    if not seed_words:
        return []
        
    print(f"❓ 开始挖掘知乎问答（高意图需求）...")
    questions = []
    import random
    # 随机选取 8 个种子词进行挖掘
    target_seeds = random.sample(seed_words, min(8, len(seed_words)))
    
    for seed in target_seeds:
        try:
            # 知乎搜索 API (简化版，通过网页接口)
            url = f"https://www.zhihu.com/api/v4/search_v3?t=general&q={seed}&offset=0&limit=5"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://www.zhihu.com/search"
            }
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                if "data" in data:
                    for item in data["data"][:3]:  # 每个种子词取前3条
                        obj = item.get("object", {})
                        # 优先获取问题标题
                        if item.get("type") == "search_result":
                            title = obj.get("title", "") or obj.get("question", {}).get("title", "")
                            if title and len(title) > 5:
                                # 清理 HTML 标签
                                clean_title = re.sub(r'<[^>]+>', '', title)
                                questions.append(f"[知乎问答] {clean_title}")
                    print(f"   -> '{seed}' 挖到: {min(3, len(data.get('data', [])))} 条")
            
            time.sleep(0.8)  # 知乎反爬严格，增加间隔
        except Exception as e:
            print(f"   ⚠️ 知乎挖掘 '{seed}' 失败: {e}")
            
    # 去重
    questions = list(set(questions))
    print(f"   -> 总计获取 {len(questions)} 个知乎高意图问答")
    return questions

def fetch_xiaohongshu_trends(seed_words):
    """抓取小红书热门话题 (C端消费趋势，年轻群体偏好)"""
    if not seed_words:
        return []
        
    print(f"📕 开始挖掘小红书消费趋势...")
    trends = []
    import random
    # 随机选取 6 个种子词
    target_seeds = random.sample(seed_words, min(6, len(seed_words)))
    
    for seed in target_seeds:
        try:
            # 小红书搜索建议 API (公开接口)
            url = f"https://edith.xiaohongshu.com/api/sns/web/v1/search/hot_list"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://www.xiaohongshu.com/"
            }
            resp = requests.get(url, headers=headers, timeout=8)
            
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success") and "data" in data:
                    hot_list = data["data"].get("list", [])[:10]
                    for item in hot_list:
                        title = item.get("title", "")
                        if title and any(kw in title for kw in ["包装", "礼盒", "送礼", "开箱", "好物"]):
                            trends.append(f"[小红书] {title}")
                    print(f"   -> 获取到 {len(hot_list)} 个热门话题")
                    break  # 热榜只需请求一次
            
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ 小红书抓取失败: {e}")
    
    # 备用：基于种子词构造消费场景话题
    consumption_scenes = [
        "开箱体验", "送礼推荐", "高级感包装", "拆快递", 
        "好物分享", "颜值包装", "精致生活"
    ]
    for seed in target_seeds[:3]:
        for scene in random.sample(consumption_scenes, 2):
            trends.append(f"[小红书] {seed}{scene}")
    
    trends = list(set(trends))
    print(f"   -> 总计获取 {len(trends)} 个小红书趋势")
    return trends

def fetch_google_trends(seed_words):
    """获取谷歌趋势数据 (海外市场洞察，跨境电商需求)"""
    if not seed_words:
        return []
        
    print(f"🌍 开始获取谷歌全球趋势...")
    trends = []
    
    # 包装行业海外关键词
    overseas_keywords = [
        "custom packaging", "gift box wholesale", "mailer box",
        "packaging design trends", "sustainable packaging",
        "luxury packaging", "eco friendly packaging",
        "packaging supplier", "corrugated box manufacturer"
    ]
    
    for kw in overseas_keywords[:5]:
        try:
            # Google Trends 建议 API (简化版)
            url = f"https://trends.google.com/trends/api/autocomplete/{kw.replace(' ', '%20')}?hl=en-US"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            resp = requests.get(url, headers=headers, timeout=8)
            
            if resp.status_code == 200:
                # Google Trends 返回需要处理前缀
                text = resp.text
                if text.startswith(")]}'"):
                    text = text[5:]
                try:
                    data = json.loads(text)
                    if "default" in data and "topics" in data["default"]:
                        for topic in data["default"]["topics"][:3]:
                            title = topic.get("title", "")
                            if title:
                                trends.append(f"[谷歌趋势] {title}")
                except:
                    pass
            
            time.sleep(0.3)
        except Exception as e:
            print(f"   ⚠️ 谷歌趋势 '{kw}' 获取失败: {e}")
    
    # 备用：预设海外热门话题
    preset_trends = [
        "[谷歌趋势] sustainable packaging solutions 2026",
        "[谷歌趋势] custom mailer boxes for small business",
        "[谷歌趋势] eco friendly packaging alternatives",
        "[谷歌趋势] luxury gift box packaging design",
        "[谷歌趋势] corrugated shipping boxes wholesale"
    ]
    trends.extend(preset_trends)
    
    trends = list(set(trends))
    print(f"   -> 总计获取 {len(trends)} 个海外趋势")
    return trends

def fetch_baidu_suggestions(seed_words):
    """挖掘百度下拉推荐词 (精准搜索需求)"""
    if not seed_words:
        return []
        
    print(f"⛏️  开始挖掘 {len(seed_words)} 个种子词的长尾需求...")
    suggestions = []
    
    for seed in seed_words:
        try:
            # Baidu Suggest API: window.bdsug.sug({q:"...",s:["..."]})
            url = f"http://suggestion.baidu.com/su?wd={seed}&p=3&cb=window.bdsug.sug"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            # 简单的正则提取 s:[...] 内容
            match = re.search(r's:(\[.*?\])', resp.text)
            if match:
                # 转换类似 JSON 的数组字符串 (虽然它是 JS 数组，但 python json 也能解大部分)
                # 注意：Baidu 有时返回单引号，py json 需要双引号
                raw_list = match.group(1).replace("'", '"')
                try:
                    words = json.loads(raw_list)
                    # 选取前 5 个最相关的
                    top_words = words[:5]
                    for w in top_words:
                        suggestions.append(f"[搜索需求] {w}")
                    print(f"   -> '{seed}' 挖到: {len(top_words)} 个")
                except:
                    pass
            time.sleep(0.5) 
        except Exception as e:
            print(f"   ❌ 挖掘 '{seed}' 失败: {e}")
            
    print(f"   -> 总计获取 {len(suggestions)} 个百度长尾需求")
    return suggestions

def fetch_1688_suggestions(seed_words):
    """挖掘1688下拉推荐词 (B2B源头采购需求)"""
    if not seed_words:
        return []
        
    print(f"🏭 开始挖掘 1688 (B2B) 长尾需求...")
    suggestions = []
    import random
    # 随机选取 10 个词进行挖掘，防止请求过多
    target_seeds = random.sample(seed_words, min(10, len(seed_words)))
    
    for seed in target_seeds:
        try:
            # 1688 Suggest API
            url = f"https://suggest.1688.com/bin/suggest?code=utf-8&q={seed}"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            data = resp.json()
            if "result" in data:
                top_words = [item['q'] for item in data['result'][:5]]
                for w in top_words:
                    suggestions.append(f"[1688采购] {w}")
                print(f"   -> '{seed}' 挖到: {len(top_words)} 个")
            time.sleep(0.5)
        except Exception as e:
            print(f"   ❌ 1688挖掘 '{seed}' 失败: {e}")
            
    print(f"   -> 总计获取 {len(suggestions)} 个1688长尾需求")
    return suggestions

def fetch_taobao_suggestions(seed_words):
    """挖掘淘宝下拉推荐词 (C端消费趋势)"""
    if not seed_words:
        return []

    print(f"🛍️  开始挖掘淘宝 (C端) 消费趋势...")
    suggestions = []
    import random
    target_seeds = random.sample(seed_words, min(10, len(seed_words)))

    for seed in target_seeds:
        try:
            # Taobao Suggest API
            url = f"https://suggest.taobao.com/sug?code=utf-8&q={seed}&k=1&area=c2c"
            resp = requests.get(url, headers=HEADERS, timeout=5)
            data = resp.json()
            if "result" in data:
                top_words = [item[0] for item in data['result'][:5]]
                for w in top_words:
                    suggestions.append(f"[淘宝热搜] {w}")
                print(f"   -> '{seed}' 挖到: {len(top_words)} 个")
            time.sleep(0.5)
        except Exception as e:
            print(f"   ❌ 淘宝挖掘 '{seed}' 失败: {e}")

    print(f"   -> 总计获取 {len(suggestions)} 个淘宝长尾需求")
    return suggestions

def analyze_trends_with_ai(trends):
    """使用 DeepSeek 分析热搜与包装行业的关联"""
    if not trends:
        return []
        
    print(f"🧠 正在请求 DeepSeek 分析 {len(trends)} 个话题...")
    
    # 构造 Prompt
    trends_str = "\n".join([f"- {t}" for t in trends])
    prompt = f"""
    我是一个做【包装印刷、礼盒定制、品牌设计】的工厂。
    请分析以下全网热点，**务必挑选出 25 个** 最适合写文章的话题（数量不足扣分）。
    
    **筛选优先级（GEO 时代精准营销版 2026）：**
    1. **S级（必选 - 高意图需求）**：
       - 带有 `[搜索需求]` 或 `[1688采购]` 标记的内容（用户已有明确采购意向）
       - **问答类话题**：如"XX怎么选"、"XX多少钱"、"XX哪家好"（适合 AI 搜索引擎摘录）
       - **技术类长尾需求**：印刷设备介绍/维修、行业标准解读、包装计算公式
       - **行业前沿趋势**：数字化、AI、出海、可持续包装
    2. **A级（重点 - 商业关联）**：
       - 能关联到"实体产品、礼品经济、消费行业（美妆/食品/电子）"的商业热点
       - 带有明确场景的话题（如："春节礼盒"、"电商包装"、"外卖包装"）
       - **行业活动（新增重点）**：包装展会、设计大赛、高峰论坛、技术交流会（必须归类为'行业资讯'）
       - **下游行业展会（S级商机）**：食品展、美博会、电子展、礼品展（需分析其对包装的新需求）
    3. **B级（特定关联）**：
       - 能强行关联行业标准的社会热点（如："环保政策→绿色包装"、"快递新规→抗压纸箱"）
    4. **D级（坚决剔除）**：
       - 纯娱乐八卦、政治敏感、负面社会新闻
       - 无法提供"实用价值"的话题（AI 搜索引擎不会推荐无价值内容）

    **GEO 时代营销思考（新增）：**
    - 看到"XX怎么选"，思考：这是高意图问答，AI 会优先推荐有清晰答案的文章 ✓
    - 看到"XX多少钱"，思考：用户有采购意向，可以写价格科普+报价引导 ✓
    - 看到"XX展会/论坛/大赛"，思考：这是行业资讯的高价值内容，**优先保留**，用户关注行业动态 ✓
    - 看到纯热点事件，思考：能否转化为"实用教程"或"避坑指南"？能→选，否→弃

    热搜列表（已标记来源）：
    {trends_str}
    
    对于每个挑选出的相关话题，请给出（请保留原始话题中的[来源]标记）：
    1. topic: 话题名称 (e.g. "[搜索需求] 包装定制哪家好")
    2. angle: 结合角度 (例如：分析事件中的礼品包装差异、热点人物带火的同款色系等)
    3. content_type: 建议的内容形式，可选值：
       - "问答科普"：适合"XX是什么"类话题
       - "对比评测"：适合"XX vs XX"、"哪个好"类话题
       - "教程指南"：适合"怎么做"、"如何"类话题
       - "价格揭秘"：适合"多少钱"、"价格"类话题
       - "趋势分析"：适合行业动态类话题
    4. priority: 优先级 (S/A/B)
    
    请严格返回 JSON 格式列表：
    [
        {{"topic": "话题名", "angle": "结合角度", "content_type": "问答科普", "priority": "S"}}
    ]
    不要返回 Markdown。
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    try:
        if "sk-your-key-here" in DEEPSEEK_API_KEY:
            print("⚠️ 未配置 DeepSeek Key，跳过 AI 分析。")
            return []

        # 数据量大时，API 响应较慢，增加超时时间到 120秒
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=120)
        result = resp.json()
        
        if "choices" in result:
            content = result["choices"][0]["message"]["content"]
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        else:
            print(f"❌ API 调用错误: {result}")
            return []
            
    except Exception as e:
        print(f"❌ AI 分析失败: {e}")
        return []

def main():
    # 0. 读取配置获取种子词
    mining_seeds = []
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
            mining_seeds = cfg.get("mining_seeds", [])

    # 1. 多源抓取
    all_trends = []
    
    # 挖掘长尾需求 (优先)
    all_trends.extend(fetch_baidu_suggestions(mining_seeds))
    all_trends.extend(fetch_1688_suggestions(mining_seeds))
    all_trends.extend(fetch_taobao_suggestions(mining_seeds))
    all_trends.extend(fetch_zhihu_hot_questions(mining_seeds))  # 知乎高意图问答
    all_trends.extend(fetch_xiaohongshu_trends(mining_seeds))   # 小红书消费趋势
    all_trends.extend(fetch_google_trends(mining_seeds))        # 谷歌海外趋势
    
    # 手动标记来源
    for t in fetch_baidu_hot():
        all_trends.append(f"[百度] {t}")
        
    for t in fetch_weibo_hot():
        all_trends.append(f"[微博] {t}")
        
    for t in fetch_toutiao_hot():
        all_trends.append(f"[头条] {t}")
        
    # B站反爬严重暂跳过
    # for t in fetch_bilibili_hot():
    #     all_trends.append(f"[B站] {t}")
        
    for t in fetch_36kr_hot():
        all_trends.append(f"[36氪] {t}")
    
    # 去重
    unique_trends = list(set(all_trends))
    print(f"📊 共收集到 {len(unique_trends)} 个唯一热点话题")

    # 2. 分析
    analyzed_data = analyze_trends_with_ai(unique_trends)
    
    # 3. 存储
    output = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "raw_trends_count": len(unique_trends),
        "all_trends_list": unique_trends,  # 保存所有原始热点
        "analyzed_trends": analyzed_data
    }
    
    with open(TRENDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    print(f"💾 结果已保存至 {TRENDS_FILE}")

if __name__ == "__main__":
    main()