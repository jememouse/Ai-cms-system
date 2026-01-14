#!/bin/bash
# 激活虚拟环境并运行 Step 4: 小红书裂变

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ 错误: 未找到 uv。请先安装 uv: pip install uv"
    exit 1
fi

echo "🚀 启动节点4: 小红书内容裂变..."
uv run python step4_social/agent_runner.py
echo "✅ 节点4执行完毕."
