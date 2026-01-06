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
    请分析以下全网热点，**务必挑选出 33 个** 最适合写文章的话题（数量不足扣分）。
    
    **筛选优先级（精准营销版）：**
    1. **S级（必选）**：带有 `[搜索需求]` 标记的内容。以及**技术类长尾需求**（如：**印刷设备介绍/维修、行业标准解读、包装计算公式**）、**行业前沿趋势**（数字化、AI、出海）及**设计营销热点**（如：**国潮设计、品牌视觉升级、热门广告创意**）。
    2. **A级（重点）**：能关联到“实体产品、礼品经济、消费行业（美妆/食品/电子）”的商业热点。例如：“某品牌联名礼盒”、“春节年货消费趋势”。
    3. **B级（特定关联）**：能强行关联此行业标准的社会热点。例如：“环保政策（关联绿色包装）”、“快递新规（关联抗压纸箱）”。
    4. **D级（坚决剔除）**：任何无法转化为“卖包装盒”的纯娱乐八卦、政治敏感、负面社会新闻。**宁缺毋滥，不要凑数。**
    
    **营销思考逻辑：**
    - 看到“明星代言”，思考：他的粉丝会买同款应援礼盒吗？（是->选，否->弃）
    - 看到“节日”，思考：商家需要提前备货礼盒包装吗？（是->选）

    热搜列表（已标记来源）：
    {trends_str}
    
    对于每个挑选出的相关话题，请给出（请保留原始话题中的[来源]标记）：
    1. topic: 话题名称 (e.g. "[搜索需求] 包装定制哪家好")
    2. angle: 结合角度 (例如：分析事件中的礼品包装差异、热点人物带火的同款色系等)
    
    请严格返回 JSON 格式列表：
    [
        {{"topic": "话题名", "angle": "结合角度"}}
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