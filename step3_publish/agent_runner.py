import random
import sys
import os
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.publisher import PublisherAgent
from shared.google_client import GoogleSheetClient
from shared import config
from shared import stats


def load_publish_config():
    """加载发布配置 (优先环境变量，其次本地文件)"""
    # 1. 尝试从环境变量加载 (用于 GitHub Actions Secret)
    config_json = os.getenv("PUBLISH_CONFIG_JSON")
    if config_json:
        try:
            print("🔐 读取环境变量配置: PUBLISH_CONFIG_JSON")
            return json.loads(config_json)
        except json.JSONDecodeError as e:
            print(f"⚠️ 解析环境变量配置失败: {e}")
    
    # 2. 尝试从文件加载
    if os.path.exists(config.PUBLISH_CONFIG_FILE):
        try:
            with open(config.PUBLISH_CONFIG_FILE, 'r', encoding='utf-8') as f:
                print(f"📖 读取本地配置文件: {config.PUBLISH_CONFIG_FILE}")
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 读取配置文件失败: {e}")
            
    print(f"⚠️ 未找到有效配置")
    return None


def run():
    print("\n" + "=" * 50)
    print("🤖 启动 Agentic Workflow (Step 3: Publishing)")
    print("=" * 50 + "\n")
    
    # 加载配置获取账号信息
    publish_config = load_publish_config()
    accounts = publish_config.get("accounts", []) if publish_config else []
    
    # 准备账号列表 (用于轮换)
    active_accounts = []
    if accounts:
        active_accounts = accounts
        print(f"👥 加载了 {len(active_accounts)} 个发布账号 (启用轮换模式)")
    else:
        # Fallback to defaults or single env var
        default_user = config.WELLCMS_USERNAME
        default_pass = config.WELLCMS_PASSWORD
        if default_user:
             active_accounts.append({"username": default_user, "password": default_pass})
             print(f"👤 加载默认账号: {default_user}")
        else:
             print("⚠️ 未找到任何账号配置")

    client = GoogleSheetClient()
    
    total_success = 0
    total_fail = 0
    
    # 1. 获取待发布文章 (Status='Pending')
    print("🔍 [System] 正在扫描待发布文章...")
    # 限制根据 Config
    # 1. 获取待发布文章 (Status='Pending')
    print("🔍 [System] 正在扫描待发布文章...")
    # 限制根据 Config
    # [Target Capacity Strategy]
    # 每1小时 20 篇 (16次/天 × 20 = 320篇/天)
    # Total = 20 (Round-robin 分配给多个账号)
    
    limit = 20
    
    # 还是打印一下账号信息只是为了调试
    num_accounts = len(active_accounts) if active_accounts else 1
    print(f"⚙️  [Target Mode] 账号数: {num_accounts} | 本次锁定发布: {limit} 篇")
    
    pending_records = client.fetch_records_by_status(status=config.STATUS_PENDING, limit=limit)
    
    print(f"📋 发现 {len(pending_records)} 篇待发布文章")
    
    
    for idx, record in enumerate(pending_records):
        print(f"\n--- [{idx + 1}/{len(pending_records)}] 发布: {record.get('Title', '')[:30]}... ---")
        
        # [Idempotency Check] 防止重复发布
        # 如果状态是 Pending 但已经有 URL，说明上次发布成功但状态更新失败
        # [Idempotency Check] 防止重复发布，但需处理重生成的情况
        # 如果状态是 Pending 但已经有 URL:
        # 1. 如果 GenTime > PubTime -> 说明是重生成的新文章，旧 URL 是过期的，应该重新发布。
        # 2. 如果 GenTime < PubTime -> 说明是状态回滚了，URL 是有效的，应该恢复为 Published。
        existing_url = record.get('URL', '').strip()
        
        if existing_url and existing_url.startswith('http'):
            gen_time_str = record.get('生成时间', '2000-01-01 00:00:00')
            pub_time_str = record.get('发布时间', '2099-12-31 23:59:59') # 默认为未来，防止误判
            
            try:
                gen_time = datetime.strptime(gen_time_str, "%Y-%m-%d %H:%M:%S")
                # 有些记录可能没有发布时间，如果为空，则认为是 1970
                if not record.get('发布时间'):
                    pub_time = datetime.min
                else:
                    pub_time = datetime.strptime(pub_time_str, "%Y-%m-%d %H:%M:%S")
            except:
                # 解析失败，保守起见认为是 Stale
                gen_time = datetime.max
                pub_time = datetime.min

            if gen_time > pub_time:
                print(f"   🔄 [Stale Check] 检测到内容已重生成 (Gen: {gen_time_str} > Pub: {pub_time_str})")
                print(f"   🗑️ 忽略旧 URL，执行重新发布...")
                # 不 continue，继续往下执行发布逻辑
            else:
                print(f"   ⚠️ 检测到该文章已有 URL ({existing_url}) 且未重生成。")
                print(f"   🔄 正在修复状态为 Published...")
                
                # 修复状态
                client.update_record(record['record_id'], {
                    "Status": config.STATUS_PUBLISHED
                })
                
                # 同时也确保写入 asset
                article_data_fix = {
                    "title": record.get('Title'),
                    "url": existing_url,
                    "keywords": record.get('关键词'),
                    "category_id": config.CATEGORY_MAP.get(str(record.get('大项分类', '')).strip(), "1"),
                    "summary": record.get('摘要')
                }
                _record_to_assets(article_data_fix, existing_url)
                
                print(f"   ✅ 状态修复完成，跳过本次重复发布。")
                continue
            
        # [Data Integrity] 发布前强校验
        title_chk = record.get('Title', '').strip()
        content_chk = record.get('HTML_Content', '').strip()
        
        if not title_chk or len(content_chk) < 50:
            print(f"   🛑 检测到无效内容 (Title: {bool(title_chk)}, Content Len: {len(content_chk)})")
            print(f"   🔄 正在将状态重置为 Ready 以便重新生成...")
            client.update_record(record['record_id'], {"Status": config.STATUS_READY})
            continue

        # 转换为 Skill 需要的格式
        article_data = {
            "title": record.get('Title'),
            "html_content": record.get('HTML_Content'),
            "category_id": config.CATEGORY_MAP.get(str(record.get('大项分类', '')).strip(), "1"),
            "summary": record.get('摘要'),
            "keywords": record.get('关键词'),
            "description": record.get('描述'),
            "tags": record.get('Tags')
        }
        
        # 2. Agent 发布 (账号轮换 & 负载均衡)
        current_account = {}
        if active_accounts:
            # Round-Robin 轮询分配
            current_account = active_accounts[idx % len(active_accounts)]
        else:
            # Fallback (理论上不会走到这，前面有检查)
            current_account = {"username": config.WELLCMS_USERNAME, "password": config.WELLCMS_PASSWORD}
            
        cur_user = current_account.get("username")
        cur_pass = current_account.get("password")
        
        print(f"   👤 [Account] 本次使用账号 ({idx + 1}): {cur_user}")
        
        try:
            # 实例化 Agent (每次独立实例化以确保 Session 隔离)
            agent = PublisherAgent(username=cur_user, password=cur_pass)
            published_url = agent.publish_article(article_data)
            
            if published_url:
                # 3. System Update Feishu
                client.update_record(record['record_id'], {
                    "Status": config.STATUS_PUBLISHED,
                    "URL": published_url,
                    "发布时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                print(f"   💾 [System] 飞书状态已更新为 Published")
                
                # 4. Asset Write-back (SEO Closed Loop)
                _record_to_assets(article_data, published_url)
                
                total_success += 1
                stats.record_published()
            else:
                total_fail += 1
                stats.record_failed()
                print(f"   ❌ [Failed] 发布失败，未返回 URL")
        except Exception as e:
            total_fail += 1
            stats.record_failed()
            print(f"   ❌ [Error] 发布过程中发生异常: {e}")
            import traceback
            traceback.print_exc()
        
        # Random Interval
        if idx < len(pending_records) - 1:
            # Optimized: faster interval (0.5-1.5s)
            wait_time = random.uniform(0.5, 1.5)
            print(f"   ⏳ 等待 {wait_time:.1f} 秒...")
            time.sleep(wait_time)

    # 发送飞书通知
    if total_success > 0 or total_fail > 0:
        notify_content = f"**发布结果**\n- ✅ 成功: {total_success} 篇\n- ❌ 失败: {total_fail} 篇\n- ⏰ 时间: {time.strftime('%Y-%m-%d %H:%M')}\n\n{stats.get_summary()}"
        client.send_notification(
            title="📤 CMS 发布任务完成",
            content=notify_content
        )
        print(f"📢 已发送飞书通知 (成功: {total_success}, 失败: {total_fail})")
    else:
        # Debug Mode: Notify even if empty to confirm scheduling
        print(f"⚠️ 本次未找到待发布文章 (Status=Pending)")
        client.send_notification(
            title="⚠️ CMS 发布轮空",
            content=f"本次运行未找到 'Pending' 状态的文章。\n⏰ 时间: {time.strftime('%Y-%m-%d %H:%M')}\n请检查 Step 1/2 是否生成了足够内容。"
        )

def _record_to_assets(article, url):
    """
    将已发布的文章记录到本地资产库，用于 SEO 内链
    """
    import json
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ASSETS_FILE = os.path.join(BASE_DIR, "published_assets.json")
    
    # 构造新记录
    new_record = {
        "title": article.get("title"),
        "url": url,
        "keywords": article.get("keywords"),
        "category_id": article.get("category_id"),
        "summary": article.get("summary"),
        "published_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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
        existing_idx = next((i for i, item in enumerate(data) if item.get("url") == url), -1)
        if existing_idx >= 0:
            data[existing_idx] = new_record
        else:
            data.append(new_record)
            
        with open(ASSETS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"   📚 [SEO] 已收录至资产库 ({len(data)} 篇)")
        
    except Exception as e:
        print(f"   ⚠️ 资产库写入失败: {e}")

if __name__ == "__main__":
    run()
