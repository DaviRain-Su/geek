#!/bin/bash

# Markdown 导出脚本
# 将所有文章导出为分类整理的 Markdown 文件

echo "🚀 Web3极客日报 Markdown 导出工具"
echo "=================================="

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 默认参数
OUTPUT_DIR="export/markdown"
LIMIT=""
CATEGORY="true"
DATE="true"
AUTHOR="true"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -l|--limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        --no-category)
            CATEGORY="false"
            shift
            ;;
        --no-date)
            DATE="false"
            shift
            ;;
        --no-author)
            AUTHOR="false"
            shift
            ;;
        -h|--help)
            echo "使用方法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -o, --output DIR     输出目录 (默认: export/markdown)"
            echo "  -l, --limit NUM      限制导出文章数量"
            echo "  --no-category        不按分类导出"
            echo "  --no-date           不按日期导出"
            echo "  --no-author         不按作者导出"
            echo "  -h, --help          显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                          # 导出所有文章"
            echo "  $0 -l 100                   # 只导出前100篇"
            echo "  $0 -o ~/Documents/articles  # 导出到指定目录"
            echo "  $0 --no-author              # 不按作者分类"
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项: $1${NC}"
            echo "使用 $0 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 构建命令参数
CMD_ARGS="--output $OUTPUT_DIR"
if [[ -n "$LIMIT" ]]; then
    CMD_ARGS="$CMD_ARGS $LIMIT"
fi
if [[ "$CATEGORY" == "false" ]]; then
    CMD_ARGS="$CMD_ARGS --no-category"
fi
if [[ "$DATE" == "false" ]]; then
    CMD_ARGS="$CMD_ARGS --no-date"
fi
if [[ "$AUTHOR" == "false" ]]; then
    CMD_ARGS="$CMD_ARGS --no-author"
fi

# 显示导出配置
echo -e "${YELLOW}导出配置:${NC}"
echo "  输出目录: $OUTPUT_DIR"
if [[ -n "$LIMIT" ]]; then
    echo "  文章数量: 限制为 ${LIMIT#--limit }"
else
    echo "  文章数量: 全部"
fi
echo "  按分类导出: $CATEGORY"
echo "  按日期导出: $DATE"
echo "  按作者导出: $AUTHOR"
echo ""

# 确认执行
read -p "确认开始导出? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消导出"
    exit 0
fi

# 创建输出目录
echo -e "${GREEN}创建输出目录...${NC}"
mkdir -p "$OUTPUT_DIR"

# 执行导出
echo -e "${GREEN}开始导出文章...${NC}"
python3 export_to_markdown.py $CMD_ARGS

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 导出成功！${NC}"
    echo ""
    
    # 显示导出统计
    if [ -f "$OUTPUT_DIR/README.md" ]; then
        echo "📊 导出统计:"
        # 统计文件数量
        TOTAL_FILES=$(find "$OUTPUT_DIR" -name "*.md" -type f | wc -l)
        echo "  总文件数: $TOTAL_FILES"
        
        # 统计分类数量
        if [[ "$CATEGORY" == "true" ]]; then
            CATEGORY_COUNT=$(find "$OUTPUT_DIR" -maxdepth 1 -type d -not -name "by_*" -not -path "$OUTPUT_DIR" | wc -l)
            echo "  分类数量: $CATEGORY_COUNT"
        fi
        
        # 显示占用空间
        SIZE=$(du -sh "$OUTPUT_DIR" | cut -f1)
        echo "  占用空间: $SIZE"
    fi
    
    echo ""
    echo "📁 文件保存在: $OUTPUT_DIR"
    echo "📖 查看索引文件: $OUTPUT_DIR/README.md"
    
    # 询问是否打开目录
    read -p "是否打开输出目录? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open "$OUTPUT_DIR"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            xdg-open "$OUTPUT_DIR"
        fi
    fi
else
    echo -e "${RED}❌ 导出失败！${NC}"
    echo "请检查错误信息并重试"
    exit 1
fi