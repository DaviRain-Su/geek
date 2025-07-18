# Markdown 导出指南

## 📖 概述

本项目提供了强大的 Markdown 导出功能，可以将所有文章导出为结构化的 Markdown 文件，并自动进行分类和标签生成。

## 🚀 快速开始

### 1. 使用脚本导出（推荐）

```bash
# 导出所有文章
./scripts/export_markdown.sh

# 导出前 100 篇文章
./scripts/export_markdown.sh -l 100

# 导出到指定目录
./scripts/export_markdown.sh -o ~/Documents/articles

# 只按分类导出，不按作者和日期
./scripts/export_markdown.sh --no-author --no-date
```

### 2. 使用 CLI 命令导出

```bash
# 基本导出
python3 main.py export --format markdown

# 带参数导出
python3 main.py export --format markdown --output export/my_articles --limit 50

# 自定义导出选项
python3 main.py export --format markdown --no-category --no-author
```

### 3. 直接使用 Python 脚本

```bash
# 导出所有文章
python3 export_to_markdown.py

# 导出前 10 篇文章
python3 export_to_markdown.py --limit 10

# 指定输出目录
python3 export_to_markdown.py --output /path/to/export

# 自定义导出选项
python3 export_to_markdown.py --no-date --no-author
```

## 📁 导出结构

导出后的文件结构如下：

```
export/markdown/
├── README.md                    # 索引文件和统计信息
├── Web3与区块链/                 # 按分类组织
│   ├── 0001_文章标题.md
│   └── 0002_文章标题.md
├── AI与机器学习/
│   ├── 0003_文章标题.md
│   └── 0004_文章标题.md
├── 编程语言/
│   ├── Rust/
│   │   └── 0005_文章标题.md
│   └── Python/
│       └── 0006_文章标题.md
├── by_author/                   # 按作者组织
│   ├── 作者A/
│   │   ├── 0001_文章标题.md
│   │   └── 0002_文章标题.md
│   └── 作者B/
│       └── 0003_文章标题.md
└── by_date/                     # 按日期组织
    ├── 2025-01/
    │   ├── 0001_文章标题.md
    │   └── 0002_文章标题.md
    └── 2024-12/
        └── 0003_文章标题.md
```

## 📄 文章格式

每篇导出的文章包含以下内容：

### 1. 文章标题
```markdown
# 文章标题
```

### 2. 元信息
```markdown
## 元信息

- **作者**: 作者名
- **发布账号**: 账号名
- **发布时间**: 2025-01-11 10:30:00
- **原文链接**: [链接](https://example.com)
- **标签**: #Web3 #区块链 #难度_中级 #质量等级_B #中文
```

### 3. 文章正文
```markdown
## 正文

文章的完整内容...
```

### 4. 自动化分析
```markdown
## 文章分析

### 质量评估
- **总体评分**: 0.75/1.00
- **质量等级**: B
- **字数**: 1,200
- **预计阅读时间**: 6 分钟

#### 详细指标
| 指标 | 分数 |
|------|------|
| 原创性 | 0.85 |
| 技术深度 | 0.70 |
| 可读性 | 0.80 |
| 结构化 | 0.75 |
| 参与度 | 0.60 |
| 完整性 | 0.80 |

#### 文章要点
- 要点1
- 要点2
- 要点3

#### 改进建议
- 建议1
- 建议2
```

## 🏷️ 自动标签系统

### 技术栈标签
- `#Web3` - Web3 相关技术
- `#区块链` - 区块链技术
- `#AI` - 人工智能
- `#Rust` - Rust 编程语言
- `#Python` - Python 编程语言

### 难度标签
- `#难度_初级` - 入门级内容
- `#难度_中级` - 中等难度
- `#难度_高级` - 高级内容

### 内容类型标签
- `#教程` - 技术教程
- `#新闻` - 新闻资讯
- `#分析` - 技术分析
- `#案例研究` - 案例分析

### 质量等级标签
- `#质量等级_A` - 优秀质量（≥80%）
- `#质量等级_B` - 良好质量（60-80%）
- `#质量等级_C` - 一般质量（40-60%）
- `#质量等级_D` - 待改进（<40%）

### 长度标签
- `#短文` - 少于 500 字
- `#中文` - 500-1500 字
- `#长文` - 超过 1500 字

## 🎯 自动分类系统

### 主要分类
- **Web3与区块链** - 区块链相关技术
- **DeFi** - 去中心化金融
- **NFT** - 非同质化代币
- **AI与机器学习** - 人工智能技术
- **编程语言** - 各种编程语言
  - Rust
  - Python
  - JavaScript
  - TypeScript
  - Go
  - Solidity
- **Layer2技术** - 区块链扩容方案
- **零知识证明** - 零知识相关技术

### 分类规则
1. **关键词匹配** - 基于标题和内容中的关键词
2. **技术栈识别** - 自动识别文章中提到的技术栈
3. **语义分析** - 智能分析文章主题和内容
4. **默认分类** - 未匹配的文章归入"其他"分类

## ⚙️ 高级配置

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--output, -o` | 输出目录 | `export/markdown` |
| `--limit, -l` | 限制导出文章数量 | 无限制 |
| `--no-category` | 不按分类导出 | 按分类导出 |
| `--no-date` | 不按日期导出 | 按日期导出 |
| `--no-author` | 不按作者导出 | 按作者导出 |

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `EXPORT_OUTPUT_DIR` | 默认输出目录 | `export/markdown` |
| `EXPORT_BATCH_SIZE` | 批处理大小 | 100 |

## 📊 性能优化

### 大量文章导出
对于大量文章（>1000篇），建议：

1. **分批导出**
   ```bash
   # 分批导出，每次1000篇
   python3 export_to_markdown.py --limit 1000 --output batch1
   python3 export_to_markdown.py --limit 1000 --offset 1000 --output batch2
   ```

2. **选择性导出**
   ```bash
   # 只导出必要的分类
   python3 export_to_markdown.py --no-author --no-date
   ```

3. **并行处理**
   ```bash
   # 使用多进程（需要修改代码）
   python3 export_to_markdown.py --workers 4
   ```

## 🔧 自定义配置

### 1. 修改分类映射
编辑 `export_to_markdown.py` 中的 `category_mapping` 字典：

```python
self.category_mapping = {
    'your_keyword': '你的分类',
    'another_keyword': '另一个分类',
    # ... 更多映射
}
```

### 2. 自定义标签生成
修改 `generate_tags` 方法来自定义标签生成逻辑：

```python
def generate_tags(self, article: Dict) -> List[str]:
    tags = []
    
    # 你的自定义标签逻辑
    if 'blockchain' in article.get('content', '').lower():
        tags.append('#区块链')
    
    return tags
```

### 3. 自定义 Markdown 格式
修改 `format_article_to_markdown` 方法来自定义输出格式：

```python
def format_article_to_markdown(self, article: Dict) -> str:
    # 自定义 Markdown 格式
    return f"""
    # {article.get('title', '无标题')}
    
    你的自定义格式...
    """
```

## 📈 统计和报告

导出完成后，会生成详细的统计报告：

- **总文章数** - 导出的文章总数
- **分类统计** - 各分类的文章数量
- **作者统计** - 各作者的文章数量
- **时间分布** - 按月份的文章分布
- **质量分析** - 文章质量等级分布

## 🐛 常见问题

### Q: 导出的文章没有内容？
A: 检查数据库连接是否正常，确保文章数据完整。

### Q: 标签生成失败？
A: 检查是否安装了所有依赖，特别是 analytics 模块。

### Q: 分类不准确？
A: 可以修改 `category_mapping` 来调整分类规则。

### Q: 导出速度慢？
A: 对于大量文章，使用 `--limit` 参数分批导出。

### Q: 文件名包含特殊字符？
A: 导出器会自动清理文件名中的非法字符。

## 💡 使用建议

1. **定期导出** - 建议定期导出最新文章作为备份
2. **分类整理** - 利用自动分类功能整理文章库
3. **质量分析** - 使用质量评估功能筛选高质量文章
4. **标签搜索** - 使用标签系统快速找到相关文章
5. **版本控制** - 将导出的 Markdown 文件纳入版本控制

## 🔮 未来计划

- [ ] 支持导出到 Notion
- [ ] 支持导出到 Obsidian
- [ ] 添加图表生成功能
- [ ] 支持多语言翻译
- [ ] 添加 AI 摘要功能
- [ ] 支持自定义模板
- [ ] 添加增量导出功能

---

**💬 需要帮助？** 请查看项目 README 或提交 Issue。