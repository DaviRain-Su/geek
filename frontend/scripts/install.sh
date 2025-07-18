#!/bin/bash
# 安装脚本

echo "🔧 设置 Web3极客日报前端项目..."

# 检查 uv 是否安装
if ! command -v uv &> /dev/null; then
    echo "⚠️  uv 未安装。正在安装 uv..."
    
    # 检测操作系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            echo "使用 Homebrew 安装 uv..."
            brew install uv
        else
            echo "使用安装脚本安装 uv..."
            curl -LsSf https://astral.sh/uv/install.sh | sh
        fi
    else
        # Linux/其他
        echo "使用安装脚本安装 uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
fi

# 检查安装是否成功
if ! command -v uv &> /dev/null; then
    echo "❌ uv 安装失败。请手动安装后重试。"
    exit 1
fi

echo "✅ uv 已安装: $(uv --version)"

# 安装项目依赖
echo "📦 安装项目依赖..."
uv sync

echo "✅ 安装完成！"
echo ""
echo "🚀 运行以下命令启动开发服务器："
echo "   ./scripts/dev.sh"
echo "   或"
echo "   uv run frontend-server"