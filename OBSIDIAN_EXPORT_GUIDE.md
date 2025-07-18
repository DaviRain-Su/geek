# 📚 Obsidian 导出指南

## 概述

Obsidian 导出功能专为知识管理和笔记记录而设计，将所有文章转换为 Obsidian 友好的格式，包括：

- 🏷️ **丰富的标签系统** - 自动分类和标记
- 🔗 **双向链接** - 连接相关内容
- 📊 **Dataview 查询** - 动态内容展示
- 📝 **YAML 元数据** - 结构化信息
- 🎨 **美观的模板** - 统一的笔记格式

## 🚀 快速开始

### 1. 基本导出

```bash
# 导出索引笔记（推荐开始）
./scripts/export_obsidian.sh

# 导出全部文章
./scripts/export_obsidian.sh --full

# 导出前100篇文章
./scripts/export_obsidian.sh --full --limit 100
```

### 2. 自定义导出

```bash
# 导出到指定目录
./scripts/export_obsidian.sh --vault ~/Documents/MyVault

# 使用 Python 直接调用
python3 export_obsidian.py --type full --limit 50 --vault my_vault
```

## 📁 Vault 结构

导出后的 Obsidian Vault 包含以下结构：

```
obsidian_vault/
├── Articles/           # 所有文章笔记
│   ├── 0001_Probly.md
│   ├── 0002_social-media-agent.md
│   └── ...
├── Authors/           # 作者笔记
│   ├── dan.md
│   ├── Jane.md
│   └── ...
├── Tags/              # 标签分类（自动生成）
├── Daily Notes/       # 日常笔记
├── Templates/         # 模板文件
│   └── Article Template.md
├── .obsidian/         # Obsidian 配置
│   ├── workspace.json
│   └── community-plugins.json
└── 📚 Web3极客日报索引.md  # 主索引笔记
```

## 📝 笔记格式

### 文章笔记示例

```markdown
---
title: "Probly"
url: "https://github.com/PragmaticMachineLearning/probly"
author: "dan"
account: "dan"
created: 2025-07-18T21:42:40.615080
tags:
  - tech/ai
  - author/dan
  - category/general
  - difficulty/beginner
  - quality/C
  - year/2025
published: 2025-07-18T16:02:01
date: 2025-07-18
quality:
  grade: C
  score: 0.43
  word_count: 95
  reading_time: 1
---

# Probly

## 📝 摘要

Probly 是一款智能电子表格工具，类似 Excel 但功能更强大...

## 🔗 链接

- **原文**: [https://github.com/PragmaticMachineLearning/probly](https://github.com/PragmaticMachineLearning/probly)
- **作者**: [[Authors/dan]]
- **来源**: [[Accounts/dan]]

## 🏷️ 标签

#tech/ai #author/dan #category/general #difficulty/beginner

## 📊 相关笔记

### 同作者文章
```dataview
LIST
FROM "Articles"
WHERE author = "dan"
SORT date DESC
LIMIT 5
```

## 💭 我的思考

> [!note] 个人笔记
> 在这里添加你的思考和笔记...

## 📚 相关资源

- 
- 
- 
```

## 🏷️ 智能标签系统

### 标签类型

- **技术栈**: `tech/web3`, `tech/ai`, `tech/blockchain`
- **编程语言**: `lang/rust`, `lang/python`, `lang/javascript`
- **内容类型**: `type/tutorial`, `type/news`, `type/analysis`
- **难度级别**: `difficulty/beginner`, `difficulty/intermediate`, `difficulty/advanced`
- **质量评级**: `quality/A`, `quality/B`, `quality/C`, `quality/D`
- **作者**: `author/dan`, `author/Jane`
- **时间**: `year/2025`, `month/2025-07`
- **长度**: `length/short`, `length/medium`, `length/long`

### 标签使用示例

```dataview
# 查看所有 AI 相关文章
LIST
FROM "Articles"
WHERE contains(tags, "tech/ai")
SORT date DESC
```

## 📊 Dataview 查询

### 常用查询模板

#### 1. 按质量筛选文章

```dataview
TABLE date as "日期", author as "作者", quality.score as "评分"
FROM "Articles"
WHERE quality.grade = "A"
SORT quality.score DESC
LIMIT 10
```

#### 2. 按作者统计

```dataview
TABLE length(rows) as "文章数"
FROM "Articles"
GROUP BY author
SORT length(rows) DESC
```

#### 3. 技术栈分析

```dataview
LIST
FROM "Articles"
WHERE contains(tags, "tech/")
GROUP BY tags
SORT length(rows) DESC
```

#### 4. 时间线视图

```dataview
CALENDAR date
FROM "Articles"
WHERE date >= date(today) - dur(30 days)
```

## 🔧 推荐插件

### 必装插件

1. **Dataview** - 数据查询和动态列表
2. **Calendar** - 日历视图和时间线
3. **Tag Wrangler** - 标签管理和重命名
4. **Templater** - 高级模板功能

### 推荐插件

1. **Obsidian Git** - 版本控制和同步
2. **Advanced Tables** - 表格编辑增强
3. **Excalidraw** - 绘图和思维导图
4. **Kanban** - 看板式项目管理

## 🎯 使用场景

### 1. 知识管理

- 📚 **学习笔记**: 为每篇文章添加个人思考和总结
- 🔍 **快速检索**: 使用标签和搜索快速找到相关内容
- 📈 **进度追踪**: 通过 Dataview 查看学习进度

### 2. 研究工作

- 📊 **文献管理**: 按主题和作者组织技术文章
- 🔗 **关联分析**: 通过双向链接发现内容关联
- 📝 **研究笔记**: 结合原文和个人见解

### 3. 内容创作

- 💡 **灵感收集**: 从技术文章中提取创作灵感
- 📖 **素材整理**: 按主题整理写作素材
- 🎨 **创意连接**: 通过标签发现意想不到的连接

## 📱 移动端使用

### Obsidian 移动应用

1. **同步设置**: 使用 Obsidian Sync 或 Git 同步
2. **离线阅读**: 所有笔记可离线访问
3. **快速编辑**: 在移动端添加思考和标记

### 第三方应用

- **Markor** (Android) - Markdown 编辑器
- **iA Writer** (iOS) - 专业写作工具
- **Logseq** - 另一个知识管理工具

## 🔄 工作流程建议

### 日常使用流程

1. **晨间回顾**: 查看索引笔记，了解最新内容
2. **深度阅读**: 选择感兴趣的文章深入阅读
3. **添加笔记**: 在 "💭 我的思考" 部分添加个人见解
4. **标签整理**: 定期整理和优化标签系统
5. **关联探索**: 通过双向链接发现相关内容

### 定期维护

- **周回顾**: 总结一周的学习收获
- **月度整理**: 清理无用标签，优化分类
- **季度分析**: 通过 Dataview 分析阅读趋势

## 🚨 注意事项

### 性能优化

1. **大型 Vault**: 5000+ 文章可能影响性能
2. **索引重建**: 定期重建 Obsidian 索引
3. **插件管理**: 只安装必要插件

### 数据备份

1. **定期备份**: 使用 Git 或云同步
2. **版本控制**: 追踪笔记变化
3. **多设备同步**: 确保数据一致性

## 🎨 自定义选项

### 修改模板

编辑 `Templates/Article Template.md` 来自定义笔记格式：

```markdown
---
title: "{{title}}"
url: "{{url}}"
author: "{{author}}"
custom_field: "{{custom_value}}"
tags: []
---

# {{title}}

## 🎯 核心要点

- 

## 💡 个人思考

> [!tip] 重要观点
> 

## 📋 行动项

- [ ] 
- [ ] 
- [ ] 
```

### 自定义标签

修改 `export_obsidian.py` 中的 `tag_mapping` 字典：

```python
self.tag_mapping = {
    'your_keyword': 'your/custom/tag',
    'important': 'priority/high',
    'todo': 'action/todo',
    # 添加你的自定义标签映射
}
```

## 🔗 集成其他工具

### 与其他应用集成

1. **Zotero**: 学术文献管理
2. **Notion**: 项目管理和数据库
3. **Readwise**: 阅读笔记同步
4. **Anki**: 间隔重复记忆

### API 和自动化

```python
# 自定义导出脚本示例
from export_obsidian import ObsidianExporter

exporter = ObsidianExporter("my_vault")
exporter.export_for_obsidian(
    export_type="full",
    limit=100
)
```

## 🎉 完整示例

### 导出和设置流程

```bash
# 1. 导出文章到 Obsidian
./scripts/export_obsidian.sh --full --limit 100

# 2. 用 Obsidian 打开 Vault
open obsidian_vault

# 3. 安装推荐插件
# (在 Obsidian 设置中手动安装)

# 4. 开始使用
# 从 📚 Web3极客日报索引.md 开始探索
```

导出完成后，你将拥有一个功能完整的知识管理系统，可以：

- 🔍 **智能搜索**: 通过标签和内容快速找到相关文章
- 📊 **数据分析**: 使用 Dataview 分析阅读模式和趋势
- 💭 **思考记录**: 为每篇文章添加个人见解和思考
- 🔗 **关联发现**: 通过双向链接发现内容间的隐藏联系
- 📱 **多设备同步**: 在所有设备上访问你的知识库

开始你的知识管理之旅吧！🚀