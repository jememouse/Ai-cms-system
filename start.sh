#!/bin/bash
# 盒艺家热点标题生成 - 一键启动脚本
# 使用方法: ./start.sh [选项]
#   无参数: 启动定时调度器
#   --now: 立即执行一次任务
#   --help: 显示帮助

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "==========================================="
echo "   盒艺家热点标题生成系统"
echo "   heyijiapack.com"
echo "==========================================="
echo -e "${NC}"

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠️  未检测到 uv，正在安装...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env" 2>/dev/null || true
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  未找到 .env 文件，正在从模板创建...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${YELLOW}📝 请编辑 .env 文件填入 API Key 后重新运行${NC}"
        exit 1
    else
        echo "❌ 缺少 .env.example 模板文件"
        exit 1
    fi
fi

# 同步依赖
echo -e "${GREEN}📦 同步依赖...${NC}"
uv sync

# 解析参数
case "${1:-}" in
    --now|-n)
        echo -e "${GREEN}🚀 立即执行一次任务...${NC}"
        uv run python -c "from trends_generator.scheduler import job; job()"
        ;;
    --help|-h)
        echo "用法: ./start.sh [选项]"
        echo ""
        echo "选项:"
        echo "  无参数     启动定时调度器 (后台监听)"
        echo "  --now, -n  立即执行一次任务"
        echo "  --help, -h 显示此帮助信息"
        ;;
    *)
        echo -e "${GREEN}⏰ 启动定时调度器...${NC}"
        uv run python -m trends_generator.scheduler
        ;;
esac
