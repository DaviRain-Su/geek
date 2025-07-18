# 📝 简单列表导出指南

## 概述

简单列表导出功能可以将所有文章导出为单个 Markdown 文件，每个条目格式为：
```
[标题](链接) -- 作者 | 日期 | 简短描述
```

## 🚀 快速使用

### 1. 导出所有文章
```bash
# 使用 CLI
python3 main.py export --format simple

# 使用脚本
./scripts/export_simple.sh

# 使用 Python 脚本
python3 export_simple_list.py
```

### 2. 导出到指定文件
```bash
# 导出到自定义文件
python3 main.py export --format simple --output my_articles.md

# 使用脚本
./scripts/export_simple.sh -o my_articles.md
```

### 3. 限制导出数量
```bash
# 只导出前 100 篇
python3 main.py export --format simple --limit 100

# 使用脚本
./scripts/export_simple.sh -l 100
```

## 🎯 输出格式

### 基本格式
每篇文章一行，格式为：
```
序号. [标题](链接) -- 作者 | 日期 | 描述
```

### 实际示例
```markdown
1. [Probly](https://github.com/PragmaticMachineLearning/probly) -- by dan | 2025-07-18 | jing Probly 是一款智能电子表格工具，类似 Excel 但功能更强大，集成了 AI 技术...

2. [social-media-agent](https://github.com/langchain-ai/social-media-agent) -- by dan | 2025-07-18 | Survivor 社媒AI Agent，基于langchain开发的社媒自动化内容生成工具...

3. [用 SQL 写页面](https://github.com/sqlpage/SQLPage) -- by Jane | 2025-07-18 | Shooter SQLpage 是一个纯 sql 的 web 应用构建器...
```

## 📊 高级功能

### 1. 排序选项
```bash
# 按日期排序（默认）
python3 export_simple_list.py --sort date

# 按标题排序
python3 export_simple_list.py --sort title

# 按作者排序
python3 export_simple_list.py --sort author
```

### 2. 分组导出
```bash
# 按作者分组
python3 export_simple_list.py --group author

# 按日期分组
python3 export_simple_list.py --group date

# 按账号分组
python3 export_simple_list.py --group account
```

### 3. 分组输出示例
```markdown
## Harry (515 篇)

1. [Solarpunk](https://en.wikipedia.org/wiki/Solarpunk) -- by Harry | 2025-07-18 | Solarpunk 是一种文学和艺术运动...
2. [零知识入门课程](http://zk101.io/) -- by Harry | 2025-01-11 | 主要面向非专业数学人士的开发者打造...

## Jane (96 篇)

1. [用 SQL 写页面](https://github.com/sqlpage/SQLPage) -- by Jane | 2025-07-18 | SQLpage 是一个纯 sql 的 web 应用构建器...
2. [超级中介还是商业奇才？](https://mp.weixin.qq.com/s/XrkzAETC-DctDEiVaqN_kA) -- by Jane | 2025-07-18 | LayerZero 跨链桥分析...
```

## 🛠️ 脚本选项

### CLI 参数
```bash
python3 export_simple_list.py --help
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--output, -o` | 输出文件路径 | `all_articles.md` |
| `--limit, -l` | 限制导出数量 | 无限制 |
| `--sort` | 排序方式 | `date` |
| `--group` | 分组方式 | 无分组 |

### 脚本参数
```bash
./scripts/export_simple.sh --help
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出文件路径 | `all_articles.md` |
| `-l, --limit` | 限制导出数量 | 无限制 |
| `--sort` | 排序方式 | `date` |
| `--group` | 分组方式 | 无分组 |

## 📈 统计信息

导出完成后会显示：
- 总文章数
- 输出文件路径和大小
- 作者统计（Top 10）
- 文件预览

## 🎨 自定义描述

默认描述格式：`作者 | 日期 | 内容摘要`

可以通过修改 `generate_description` 方法来自定义描述格式：

```python
def generate_description(self, article: Dict) -> str:
    """自定义描述生成逻辑"""
    parts = []
    
    # 添加你想要的信息
    if article.get('author'):
        parts.append(f"作者: {article['author']}")
    
    if article.get('account_name'):
        parts.append(f"来源: {article['account_name']}")
    
    # 添加标签
    if article.get('tags'):
        parts.append(f"标签: {', '.join(article['tags'])}")
    
    return " | ".join(parts)
```

## 🔧 常见用例

### 1. 导出所有文章作为索引
```bash
# 生成完整的文章索引
python3 main.py export --format simple --output article_index.md
```

### 2. 按作者分组导出
```bash
# 按作者分组，方便查看每个作者的贡献
python3 export_simple_list.py --group author --output articles_by_author.md
```

### 3. 导出最新文章
```bash
# 导出最新的 50 篇文章
python3 main.py export --format simple --limit 50 --output recent_articles.md
```

### 4. 生成特定时间段的文章
```bash
# 先按日期分组，然后查看特定月份
python3 export_simple_list.py --group date --output articles_by_date.md
```

## 📱 使用场景

1. **快速浏览**: 在一个文件中浏览所有文章标题和描述
2. **搜索定位**: 使用 Ctrl+F 快速搜索特定文章
3. **批量处理**: 作为其他脚本的输入数据
4. **备份索引**: 创建文章的简洁索引备份
5. **分享列表**: 分享给其他人的文章列表

## 🚨 注意事项

1. **文件大小**: 5000+ 篇文章约 1.3MB，可能需要一些时间加载
2. **内存使用**: 大量文章可能占用较多内存
3. **特殊字符**: 标题中的特殊字符会被自动清理
4. **链接格式**: 确保链接格式正确，避免 Markdown 解析问题

## 📊 性能数据

基于 5039 篇文章的测试：
- 导出时间: < 1 秒
- 文件大小: 1.3 MB
- 内存使用: < 100 MB
- 平均每篇文章: 260 字节

## 🎉 完成示例

导出完成后，你会得到一个类似这样的文件：

```markdown
# Web3极客日报 文章列表

> 导出时间: 2025-07-18 21:32:32  
> 总文章数: 5039

---

1. [Probly](https://github.com/PragmaticMachineLearning/probly) -- by dan | 2025-07-18 | 智能电子表格工具...
2. [social-media-agent](https://github.com/langchain-ai/social-media-agent) -- by dan | 2025-07-18 | 社媒AI Agent...
3. [用 SQL 写页面](https://github.com/sqlpage/SQLPage) -- by Jane | 2025-07-18 | 纯 SQL 的 web 应用构建器...
...
5039. [最后一篇文章](https://example.com) -- by author | 2025-01-01 | 文章描述...

---

*共 5039 篇文章 | 导出时间: 2025-07-18 21:32:32*
```

这个文件可以直接在任何 Markdown 阅读器中打开，所有的标题都是可点击的链接！