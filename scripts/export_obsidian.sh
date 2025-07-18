#!/bin/bash

# Obsidian 导出脚本
# 使用示例：
#   ./scripts/export_obsidian.sh                    # 导出索引笔记
#   ./scripts/export_obsidian.sh --full             # 导出全部文章  
#   ./scripts/export_obsidian.sh --full --limit 50  # 导出前50篇文章

set -e

# 默认参数
EXPORT_TYPE="index"
LIMIT=""
VAULT_PATH="obsidian_vault"

# 显示帮助信息
show_help() {
    echo "📚 Obsidian 导出工具"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --full              导出全部文章（默认：仅导出索引）"
    echo "  --limit NUM         限制导出文章数量"
    echo "  --vault PATH        指定 Obsidian Vault 路径（默认：obsidian_vault）"
    echo "  --help              显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                           # 导出索引笔记"
    echo "  $0 --full                    # 导出全部文章"
    echo "  $0 --full --limit 100       # 导出前100篇文章"
    echo "  $0 --vault ~/Documents/vault # 导出到指定目录"
    echo ""
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            EXPORT_TYPE="full"
            shift
            ;;
        --limit)
            LIMIT="$2"
            shift 2
            ;;
        --vault)
            VAULT_PATH="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 构建命令
CMD="python3 export_obsidian.py --type $EXPORT_TYPE --vault \"$VAULT_PATH\""

if [[ -n "$LIMIT" ]]; then
    CMD="$CMD --limit $LIMIT"
fi

echo "🚀 开始导出到 Obsidian..."
echo "📁 Vault 路径: $VAULT_PATH"
echo "📊 导出类型: $EXPORT_TYPE"
if [[ -n "$LIMIT" ]]; then
    echo "🔢 限制数量: $LIMIT"
fi
echo ""

# 执行导出
eval $CMD

echo ""
echo "✅ 导出完成！"
echo ""
echo "📝 接下来的步骤:"
echo "1. 用 Obsidian 打开 Vault: $VAULT_PATH"
echo "2. 安装推荐的插件（详见上方输出）"
echo "3. 开始探索你的知识库！"
echo ""
echo "🎯 推荐从索引笔记开始: 📚 Web3极客日报索引.md"