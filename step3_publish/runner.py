# step3_publish/runner.py
"""
节点3 执行器: 多账号发布到 WellCMS
从 publish_config.json 读取账号配置，按分类和数量发布
"""
import sys
import os
import json
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.feishu_client import FeishuClient
from shared import config
from shared import stats
from .wellcms_rpa import WellCMSPublisher


def load_publish_config():
    """加载发布配置 (优先文件，其次环境变量)"""
    # 1. 尝试从文件加载
    if os.path.exists(config.PUBLISH_CONFIG_FILE):
        try:
            with open(config.PUBLISH_CONFIG_FILE, 'r', encoding='utf-8') as f:
                print(f"📖 读取本地配置文件: {config.PUBLISH_CONFIG_FILE}")
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 读取配置文件失败: {e}")

    # 2. 尝试从环境变量加载 (用于 GitHub Actions Secret)
    config_json = os.getenv("PUBLISH_CONFIG_JSON")
    if config_json:
        try:
            print("🔐 读取环境变量配置: PUBLISH_CONFIG_JSON")
            return json.loads(config_json)
        except json.JSONDecodeError as e:
            print(f"⚠️ 解析环境变量配置失败: {e}")
            
    print(f"⚠️ 未找到有效配置 (文件: {config.PUBLISH_CONFIG_FILE} 或 环境变量)")
    return None

def _record_to_assets(article, url):
    """
    将已发布的文章记录到本地资产库，用于 SEO 内链
    """
    ASSETS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "published_assets.json")
    
    # 构造新记录
    new_record = {
        "title": article.get("title"),
        "url": url,
        "keywords": article.get("keywords"),
        "category_id": article.get("category_id"),
        "summary": article.get("summary"),
        "published_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    try:
        data = []
        if os.path.exists(ASSETS_FILE):
            with open(ASSETS_FILE, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except:
                    data = []
        
        # 简单去重 (按 URL)
        # 如果 URL 对应的记录已存在，更新它；否则追加
        existing_idx = next((i for i, item in enumerate(data) if item.get("url") == url), -1)
        if existing_idx >= 0:
            data[existing_idx] = new_record
        else:
            data.append(new_record)
            
        with open(ASSETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"      📚 已收录至 SEO 资产库 ({len(data)} 篇)")
        
    except Exception as e:
        print(f"      ⚠️ 资产库写入失败: {e}")



def run(config_file: str = None):
    """
    执行节点3流程 - 多账号发布
    
    Args:
        config_file: 可选的配置文件路径
    """
    print("\n" + "=" * 50)
    print("📤 节点3: 多账号 RPA 发布到 WellCMS")
    print("=" * 50 + "\n")
    
    # 加载配置
    publish_config = load_publish_config()
    if not publish_config:
        return
    
    accounts = publish_config.get("accounts", [])
    default_interval = publish_config.get("default_interval_minutes", 1)
    
    # 获取 Schema 配置 (默认: FAQ开启, Article关闭以避免冲突)
    schema_config = publish_config.get("schema_config", {})
    inject_faq = schema_config.get("inject_faq_schema", True)
    inject_article = schema_config.get("inject_article_schema", False)
    
    print(f"⚙️ Schema 配置: FAQ={inject_faq}, Article={inject_article}")
    
    if not accounts:
        print("⚠️ 没有配置任何账号")
        return
    
    print(f"📋 共 {len(accounts)} 个账号\n")
    
    client = FeishuClient()
    
    total_success = 0
    total_fail = 0
    
    # 遍历每个账号
    for acc_idx, account in enumerate(accounts):
        username = account.get("username")
        password = account.get("password")
        categories = account.get("categories", {})
        interval_min = account.get("interval_minutes", default_interval)  # 账号独立间隔(分钟)
        interval_sec = interval_min * 60  # 转换为秒
        
        print(f"\n{'='*40}")
        print(f"👤 账号 [{acc_idx + 1}/{len(accounts)}]: {username} (间隔 {interval_min} 分钟)")
        print(f"{'='*40}")
        
        # 创建该账号的发布器
        publisher = WellCMSPublisher(username=username, password=password)
        
        # 遍历该账号负责的分类
        for category, limit in categories.items():
            if limit <= 0:
                continue
            
            print(f"\n📂 分类: {category} (发布 {limit} 篇)")
            
            # 获取该分类的 Pending 记录
            records = client.fetch_records_by_status(
                status=config.STATUS_PENDING,
                category=category,
                limit=limit
            )
            
            if not records:
                print(f"   ⚠️ 没有待发布的文章")
                continue
            
            # 发布每篇文章
            for idx, record in enumerate(records):
                title = record.get("title") or record.get("topic", "")
                
                print(f"\n   [{idx + 1}/{len(records)}] {title[:30]}...")
                
                # 准备文章数据
                html_content = record.get("html_content", "")
                
                # === Schema 结构化数据注入 ===
                schema_faq_raw = record.get("schema_faq", "")
                schema_faq = []
                
                # 1. FAQ Schema (可配置开关)
                if inject_faq:
                    # 解析 schema_faq (可能是 JSON 字符串或列表)
                    if schema_faq_raw:
                        if isinstance(schema_faq_raw, str):
                            try:
                                schema_faq = json.loads(schema_faq_raw)
                            except json.JSONDecodeError:
                                schema_faq = []
                        elif isinstance(schema_faq_raw, list):
                            schema_faq = schema_faq_raw
                    
                    if schema_faq and isinstance(schema_faq, list) and len(schema_faq) > 0:
                        # 构建 FAQ Schema JSON-LD
                        faq_schema = {
                            "@context": "https://schema.org",
                            "@type": "FAQPage",
                            "mainEntity": [
                                {
                                    "@type": "Question",
                                    "name": q.get("question", ""),
                                    "acceptedAnswer": {
                                        "@type": "Answer",
                                        "text": q.get("answer", "")
                                    }
                                }
                                for q in schema_faq if isinstance(q, dict) and q.get("question")
                            ]
                        }
                        # 注入到 HTML 末尾
                        schema_script = f'<script type="application/ld+json">{json.dumps(faq_schema, ensure_ascii=False)}</script>'
                        html_content = html_content + "\n" + schema_script
                        print("      📊 已注入 FAQ Schema")
                else:
                     print("      ⏩ 跳过 FAQ Schema (配置已禁用)")

                # === Article Schema 注入 (可配置开关) ===
                if inject_article:
                    from datetime import datetime
                    article_schema = {
                        "@context": "https://schema.org",
                        "@type": "Article",
                        "headline": title,
                        "author": {
                            "@type": "Organization",
                            "name": "盒艺家技术团队",
                            "url": "https://heyijiapack.com/"
                        },
                        "publisher": {
                            "@type": "Organization",
                            "name": "盒艺家",
                            "logo": {
                                "@type": "ImageObject",
                                "url": "https://heyijiapack.com/logo.png"
                            }
                        },
                        "datePublished": datetime.now().strftime("%Y-%m-%d"),
                        "dateModified": datetime.now().strftime("%Y-%m-%d"),
                        "description": record.get("description", "")[:160],
                        "keywords": record.get("keywords", "")
                    }
                    article_schema_script = f'<script type="application/ld+json">{json.dumps(article_schema, ensure_ascii=False)}</script>'
                    html_content = html_content + "\n" + article_schema_script
                    print("      📰 已注入 Article Schema")
                else:
                    print("      ⏩ 跳过 Article Schema (配置已禁用)")
                
                # === 内容质量检测 ===
                # 清理 HTML 标签获取纯文本
                import re
                plain_text = re.sub(r'<[^>]+>', '', html_content)
                content_length = len(plain_text)
                quality_issues = []
                quality_score = 100  # 初始满分
                
                # 1. 字数检测
                if content_length < 500:
                    quality_issues.append(f"字数过少 ({content_length} 字)")
                    quality_score -= 20
                elif content_length < 800:
                    quality_score -= 5
                
                # 2. 必填字段检测
                if not record.get("keywords"):
                    quality_issues.append("缺少关键词")
                    quality_score -= 15
                if not record.get("description"):
                    quality_issues.append("缺少描述")
                    quality_score -= 10
                
                # 3. 关键词密度检测
                keywords_str = record.get("keywords", "")
                if keywords_str:
                    keywords_list = [kw.strip() for kw in keywords_str.replace("，", ",").split(",") if kw.strip()]
                    keyword_counts = {}
                    for kw in keywords_list[:3]:  # 检测前3个关键词
                        count = plain_text.count(kw)
                        keyword_counts[kw] = count
                        if count == 0:
                            quality_issues.append(f"关键词 '{kw}' 未出现")
                            quality_score -= 5
                        elif count < 2:
                            quality_score -= 2
                    if keyword_counts:
                        print(f"      🔍 关键词密度: {keyword_counts}")
                
                # 输出质量结果
                if quality_issues:
                    print(f"      ⚠️ 质量提醒 (评分:{quality_score}): {', '.join(quality_issues)}")
                else:
                    print(f"      ✅ 质量检测通过 ({content_length} 字, 评分:{quality_score})")
                
                article = {
                    "title": title,
                    "html_content": html_content,
                    "category_id": config.CATEGORY_MAP.get(category, "2"),
                    "summary": record.get("summary", ""),
                    "keywords": record.get("keywords", ""),
                    "description": record.get("description", ""),
                    "tags": record.get("tags", ""),
                }
                
                # RPA 发布
                print("      📤 正在发布...")
                success, url_link = publisher.publish_sync(article)
                
                if not success:
                    print("      ⚠️ 发布失败")
                    total_fail += 1
                    continue
                
                # 更新飞书状态和链接
                update_fields = {"Status": config.STATUS_PUBLISHED}
                if url_link:
                    update_fields["URL"] = url_link

                # 记录发布时间 (独立字段)
                from datetime import datetime
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_fields["发布时间"] = current_time
                print(f"      ⏰ 发布时间已记录: {current_time}")
                    
                if client.update_record(record["record_id"], update_fields):
                    print(f"      ✅ 已发布 -> Published")
                    if url_link:
                        print(f"      🔗 链接已保存: {url_link}")
                        # === SEO 闭环：记录到资产库 ===
                        _record_to_assets(article, url_link)
                    total_success += 1
                    stats.record_published()  # 记录发布成功
                
                # 间隔等待
                if idx < len(records) - 1:
                    import random
                    wait_sec = random.uniform(10, 20)
                    print(f"      ⏳ 等待 {wait_sec:.1f} 秒...")
                    time.sleep(wait_sec)
        
        # 账号轮换等待
        if acc_idx < len(accounts) - 1:
            print(f"\n   ⏳ 账号 [{username}] 任务完成，休息 {interval_min} 分钟 ({interval_sec}秒)...")
            time.sleep(interval_sec)
    
    # 记录失败数
    if total_fail > 0:
        stats.record_failed(total_fail)
    
    print("\n" + "=" * 50)
    print(f"📊 节点3完成!")
    print(f"   ✅ 成功: {total_success}")
    print(f"   ❌ 失败: {total_fail}")
    print("=" * 50)
    
    # 打印统计汇总
    stats.print_summary()
    
    # 发送飞书通知
    if total_success > 0 or total_fail > 0:
        notify_content = f"**发布结果**\n- ✅ 成功: {total_success} 篇\n- ❌ 失败: {total_fail} 篇\n- ⏰ 时间: {time.strftime('%Y-%m-%d %H:%M')}\n\n{stats.get_summary()}"
        client.send_notification(
            title="📤 CMS 发布任务完成",
            content=notify_content
        )


if __name__ == "__main__":
    run()
