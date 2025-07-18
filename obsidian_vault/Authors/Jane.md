---
title: "Jane"
type: author
created: 2025-07-18T21:42:40.623935
tags: [author, person]
---

# 👤 Jane

## 📊 统计信息

- **总文章数**: 2
- **质量分布**:
  - A级: 0 篇
  - B级: 0 篇  
  - C级: 1 篇
  - D级: 1 篇

## 📚 所有文章

```dataview
TABLE date as "日期", quality.grade as "质量", quality.score as "评分"
FROM "Articles"
WHERE author = "Jane"
SORT date DESC
```

## 🏷️ 常用标签

```dataview
TABLE length(rows) as "文章数"
FROM "Articles"
WHERE author = "Jane"
FLATTEN tags
GROUP BY tags
SORT length(rows) DESC
LIMIT 10
```

## 📈 发布时间线

```dataview
CALENDAR date
FROM "Articles"
WHERE author = "Jane"
```

---

*作者信息自动生成于 2025-07-18 21:42:40*
