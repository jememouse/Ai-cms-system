# trends_generator/scheduler.py
"""
热点标题生成调度器
"""
import schedule
import time
import os
import datetime
from . import fetch_trends
from . import generate_topics
from . import feishu_uploader

def job():
    print(f"\n⏰ 任务开始执行: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 抓取与分析
    print(">>> Step 1: Fetching & Analyzing Trends")
    fetch_trends.main()
    
    # 2. 生成标题
    print(">>> Step 2: Generating Topics")
    generator = generate_topics.SEOGenerator()
    generator.generate()
    
    # 3. 上传飞书
    print(">>> Step 3: Uploading to Feishu")
    uploader = feishu_uploader.FeishuBitable()
    uploader.upload()
    
    print(f"✅ 任务执行完毕: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

def run_once():
    """立即运行一次（用于测试）"""
    print("🚀 立即触发一次全流程测试...")
    job()

def main():
    print("=========================================")
    print("   盒艺家 SEO 自动化调度器")
    print("   [每天 01:00, 03:00, 05:00, 07:00 自动执行]")
    print("=========================================")
    
    # 定义定时任务 (北京时间)
    schedule.every().day.at("01:00").do(job)
    schedule.every().day.at("03:00").do(job)
    schedule.every().day.at("05:00").do(job)
    schedule.every().day.at("07:00").do(job)
    
    # 也可以每小时运行一次
    # schedule.every().hour.do(job)
    
    # 启动时询问是否立即运行一次
    # 启动时询问是否立即运行一次
    # Check env var for auto-run (Docker mode)
    if os.getenv('RUN_ON_STARTUP', 'false').lower() == 'true':
        print("🚀 检测到 RUN_ON_STARTUP=true，立即运行一次任务...")
        run_once()
    else:
        confirm = input("⚠️ 是否立即运行一次测试？(y/n): ")
        if confirm.lower() == 'y':
            run_once()
        
    print("⏳ 定时任务监听中... (按 Ctrl+C 退出)")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
