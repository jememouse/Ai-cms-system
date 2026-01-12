#!/bin/bash

# 全链路测试脚本 (10 Articles + XHS)
# 目标: 完成10篇文章的生成、发布及社媒裂变

echo "🚀 开始10篇文章全链路测试..."
echo "=================================================="

# Step 1: 选题 (TrendHunter)
# 确保生成足够的选题 (目前逻辑是抓取所有热点)
echo "\n🕵️ [Step 1] 呼叫 TrendHunter (趋势猎手)..."
uv run python step1_trends/agent_runner.py
if [ $? -ne 0 ]; then
    echo "❌ Step 1 失败，测试终止"
    exit 1
fi

# Step 2: 写作 (ChiefEditor)
# 确保处理 10 篇文章
echo "\n\n✍️ [Step 2] 呼叫 ChiefEditor (主编)..."
# 通过环境变量强制覆盖配置，确保至少处理 20 个 Pending 选题 (以此保证有10个成功)
export MAX_GENERATE_PER_CATEGORY=20
uv run python step2_article/agent_runner.py
if [ $? -ne 0 ]; then
    echo "❌ Step 2 失败，测试终止"
    exit 1
fi

# Step 3: 发布 (Publisher)
# 确保发布 10 篇文章
echo "\n\n📮 [Step 3] 呼叫 Publisher (发布专员)..."
export MAX_PUBLISH_PER_CATEGORY=20
uv run python step3_publish/agent_runner.py
if [ $? -ne 0 ]; then
    echo "❌ Step 3 失败，测试终止"
    exit 1
fi

# Step 4: 社交裂变 (SocialBot)
# 为已发布的文章生成小红书文案
echo "\n\n📱 [Step 4] 呼叫 SocialBot (社媒经理)..."
export MAX_DAILY_XHS=20
uv run python step4_social/agent_runner.py
if [ $? -ne 0 ]; then
    echo "❌ Step 4 失败，测试终止"
    exit 1
fi

echo "\n=================================================="
echo "✅ 10篇全链路测试完成！"
