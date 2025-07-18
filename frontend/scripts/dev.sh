#!/bin/bash
# 开发环境启动脚本

echo "🚀 启动 Web3极客日报前端开发环境..."

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "❌ uv 未安装。请先安装 uv："
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# 安装/更新依赖
echo "📦 检查并安装依赖..."
uv sync

# 启动服务器
echo "🌐 启动前端服务器..."
uv run frontend-server --port 3000