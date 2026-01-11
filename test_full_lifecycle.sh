#!/bin/bash

# 全链路测试脚本 (Full Lifecycle Test)
# 依次执行 Step 1 -> Step 4 的 Agent Runner

echo "🚀 开始全链路智能体测试..."
echo "=================================================="

# Step 1: 选题
echo "\n🕵️ [Step 1] 呼叫 TrendHunter (趋势猎手)..."
uv run python step1_trends/agent_runner.py
if [ $? -ne 0 ]; then
    echo "❌ Step 1 失败，测试终止"
    exit 1
fi

# Step 2: 写作
echo "\n\n✍️ [Step 2] 呼叫 ChiefEditor (主编)..."
# 注意: Step 2 默认处理 generated_seo_data.json 里的前 5 个 Pending 选题
uv run python step2_article/agent_runner.py
if [ $? -ne 0 ]; then
    echo "❌ Step 2 失败，测试终止"
    exit 1
fi

# Step 3: 发布
echo "\n\n📮 [Step 3] 呼叫 Publisher (发布专员)..."
# 注意: Step 3 从飞书获取 'Generated' 状态的文章进行发布
uv run python step3_publish/agent_runner.py
if [ $? -ne 0 ]; then
    echo "❌ Step 3 失败，测试终止"
    exit 1
fi

# Step 4: 社交裂变
echo "\n\n📱 [Step 4] 呼叫 SocialBot (社媒经理)..."
# 注意: Step 4 从飞书获取 'Published' 状态且 'XHS_Status'!='Done' 的文章
uv run python step4_social/agent_runner.py
if [ $? -ne 0 ]; then
    echo "❌ Step 4 失败，测试终止"
    exit 1
fi

echo "\n=================================================="
echo "✅ 全链路测试完成！所有 Agents 运行正常。"
