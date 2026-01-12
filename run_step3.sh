#!/bin/bash
# 节点3: RPA 发布到 WellCMS
set -e
cd "$(dirname "$0")"

# === 新增：随机启动抖动 (0-600秒) ===
# 模拟真人不会每小时准点坐在电脑前
DELAY=$((RANDOM % 30))
echo "⏳ 随机等待 ${DELAY} 秒以模拟人工操作..."
sleep $DELAY
# ==================================

echo -e "\033[0;36m"
echo "==========================================="
echo "   节点3: RPA 发布到 WellCMS"
echo "==========================================="
echo -e "\033[0m"

# 检查 uv
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env" 2>/dev/null || true
fi

uv sync
uv run python -m step3_publish.agent_runner
