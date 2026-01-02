# main_scheduler.py
import schedule
import time
import os
import fetch_trends_ai
import generate_topics
import feishu_uploader
import datetime

def job():
    print(f"\n⏰ 任务开始执行: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 抓取与分析
    print(">>> Step 1: Fetching & Analyzing Trends")
    fetch_trends_ai.main()
    
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
    print("   Box Artist DeepSeek Automation Scheduler")
    print("   [每天 02:00, 04:00, 06:00, 07:00 自动执行]")
    print("=========================================")
    
    # 定义定时任务
    schedule.every().day.at("02:00").do(job)
    schedule.every().day.at("04:00").do(job)
    schedule.every().day.at("06:00").do(job)
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
