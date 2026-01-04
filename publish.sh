#!/bin/bash
# 盒艺家自动发文 - 一键启动脚本
# 使用方法: ./publish.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "==========================================="
echo "   盒艺家自动发文系统"
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
    echo -e "${YELLOW}⚠️  未找到 .env 文件${NC}"
    exit 1
fi

# 同步依赖
echo -e "${GREEN}📦 同步依赖...${NC}"
uv sync

# 运行自动发文
echo -e "${GREEN}🚀 启动自动发文...${NC}"
uv run python -m auto_publisher.publisher
