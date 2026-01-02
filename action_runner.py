# action_runner.py
# 专门用于 GitHub Actions 的一次性执行入口
# 避免使用 schedule 的死循环，由 GitHub 的 Cron 触发

import main_scheduler
import sys
import os

def main():
    print("🚀 GitHub Actions Triggered: Starting single job run...")
    
    try:
        # 直接调用 main_scheduler 中的 job 函数
        main_scheduler.job()
        print("✅ Job completed successfully.")
    except Exception as e:
        print(f"❌ Job failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
