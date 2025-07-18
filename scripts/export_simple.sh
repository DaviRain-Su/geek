#!/bin/bash

# 简单列表导出脚本
# 将所有文章导出为单个 Markdown 文件

echo "📝 Web3极客日报 简单列表导出"
echo "=============================="

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 默认参数
OUTPUT_FILE="all_articles.md"
LIMIT=""
SORT="date"
GROUP=""

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -l|--limit)
            LIMIT="--limit $2"
            shift 2
            ;;
        --sort)
            SORT="$2"
            shift 2
            ;;
        --group)
            GROUP="--group $2"
            shift 2
            ;;
        -h|--help)
            echo "使用方法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  -o, --output FILE    输出文件路径 (默认: all_articles.md)"
            echo "  -l, --limit NUM      限制导出文章数量"
            echo "  --sort TYPE         排序方式: date|title|author (默认: date)"
            echo "  --group TYPE        分组方式: author|date|account (可选)"
            echo "  -h, --help          显示帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                              # 导出所有文章"
            echo "  $0 -l 100                       # 只导出前100篇"
            echo "  $0 -o my_articles.md            # 导出到指定文件"
            echo "  $0 --sort author                # 按作者排序"
            echo "  $0 --group author               # 按作者分组"
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
CMD_ARGS="--output $OUTPUT_FILE --sort $SORT"
if [[ -n "$LIMIT" ]]; then
    CMD_ARGS="$CMD_ARGS $LIMIT"
fi
if [[ -n "$GROUP" ]]; then
    CMD_ARGS="$CMD_ARGS $GROUP"
fi

# 显示配置
echo -e "${YELLOW}导出配置:${NC}"
echo "  输出文件: $OUTPUT_FILE"
if [[ -n "$LIMIT" ]]; then
    echo "  文章数量: 限制为 ${LIMIT#--limit }"
else
    echo "  文章数量: 全部"
fi
echo "  排序方式: $SORT"
if [[ -n "$GROUP" ]]; then
    echo "  分组方式: ${GROUP#--group }"
else
    echo "  分组方式: 无"
fi
echo ""

# 确认执行
read -p "确认开始导出? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消导出"
    exit 0
fi

# 执行导出
echo -e "${GREEN}开始导出文章...${NC}"
python3 export_simple_list.py $CMD_ARGS

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ 导出成功！${NC}"
    echo ""
    
    # 显示文件信息
    if [ -f "$OUTPUT_FILE" ]; then
        echo "📄 导出文件: $OUTPUT_FILE"
        
        # 显示文件大小
        if [[ "$OSTYPE" == "darwin"* ]]; then
            SIZE=$(stat -f%z "$OUTPUT_FILE")
            SIZE_KB=$((SIZE / 1024))
        else
            SIZE=$(stat -c%s "$OUTPUT_FILE")
            SIZE_KB=$((SIZE / 1024))
        fi
        echo "📊 文件大小: ${SIZE_KB} KB"
        
        # 显示行数
        LINES=$(wc -l < "$OUTPUT_FILE")
        echo "📝 总行数: $LINES"
        
        # 显示前几行预览
        echo ""
        echo "🔍 文件预览:"
        echo "----------------------------------------"
        head -10 "$OUTPUT_FILE"
        echo "----------------------------------------"
        echo "(显示前10行，查看完整内容: cat $OUTPUT_FILE)"
    fi
    
    echo ""
    echo "🎉 导出完成！"
    
    # 询问是否打开文件
    read -p "是否打开文件查看? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            open "$OUTPUT_FILE"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            xdg-open "$OUTPUT_FILE"
        else
            echo "请手动打开文件: $OUTPUT_FILE"
        fi
    fi
else
    echo -e "${RED}❌ 导出失败！${NC}"
    echo "请检查错误信息并重试"
    exit 1
fi