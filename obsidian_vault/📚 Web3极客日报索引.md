---
title: "Web3极客日报 - 文章索引"
created: 2025-07-18T21:42:40.624009
tags: [index, web3, articles]
---

# 📚 Web3极客日报 - 文章索引

> 更新时间: 2025-07-18 21:42:40  
> 总文章数: 5

## 📊 统计概览

```dataview
TABLE length(rows) as "文章数"
FROM "Articles"
GROUP BY author
SORT length(rows) DESC
LIMIT 10
```

## 🔍 快速搜索

### 按作者浏览
```dataview
LIST
FROM "Articles"
GROUP BY author
SORT author
```

### 按标签浏览
```dataview
LIST
FROM "Articles"
FLATTEN tags
GROUP BY tags
SORT tags
```

### 按时间浏览
```dataview
CALENDAR date
FROM "Articles"
```

## 📈 最新文章

```dataview
TABLE date as "日期", author as "作者", quality.grade as "质量"
FROM "Articles"
SORT date DESC
LIMIT 20
```

## 🏆 高质量文章

```dataview
TABLE date as "日期", author as "作者", quality.score as "评分"
FROM "Articles"
WHERE quality.grade = "A"
SORT quality.score DESC
LIMIT 10
```

## 📝 使用说明

1. **搜索文章**: 使用 Obsidian 的全局搜索功能
2. **标签导航**: 点击任何标签查看相关文章
3. **作者追踪**: 点击作者名查看其所有文章
4. **质量筛选**: 通过质量标签筛选高质量内容
5. **时间线**: 使用日历视图查看发布时间线

## 🔧 自定义查询

### 技术栈相关
```dataview
LIST
FROM "Articles"
WHERE contains(tags, "tech/")
GROUP BY tags
```

### 编程语言相关
```dataview
LIST
FROM "Articles"
WHERE contains(tags, "lang/")
GROUP BY tags
```

---

*这个索引使用 Dataview 插件自动生成，确保安装了 Dataview 插件以正常显示。*
