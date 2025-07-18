#!/bin/bash
# 代码格式化和检查脚本

echo "🎨 运行代码格式化和检查..."

# 运行 Black 格式化
echo "▶️  运行 Black 格式化..."
uv run black .

# 运行 Ruff 检查
echo "▶️  运行 Ruff 代码检查..."
uv run ruff check . --fix

# 运行 MyPy 类型检查
echo "▶️  运行 MyPy 类型检查..."
uv run mypy server.py

echo "✅ 代码格式化和检查完成！"