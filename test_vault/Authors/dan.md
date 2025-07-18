---
title: "dan"
type: author
created: 2025-07-18T21:44:45.297537
tags: [author, person]
---

# 👤 dan

## 📊 统计信息

- **总文章数**: 3
- **质量分布**:
  - A级: 0 篇
  - B级: 0 篇  
  - C级: 1 篇
  - D级: 2 篇

## 📚 所有文章

```dataview
TABLE date as "日期", quality.grade as "质量", quality.score as "评分"
FROM "Articles"
WHERE author = "dan"
SORT date DESC
```

## 🏷️ 常用标签

```dataview
TABLE length(rows) as "文章数"
FROM "Articles"
WHERE author = "dan"
FLATTEN tags
GROUP BY tags
SORT length(rows) DESC
LIMIT 10
```

## 📈 发布时间线

```dataview
CALENDAR date
FROM "Articles"
WHERE author = "dan"
```

---

*作者信息自动生成于 2025-07-18 21:44:45*
