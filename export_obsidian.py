#!/usr/bin/env python3
"""
Obsidian 导出脚本
专门为 Obsidian 优化的文章导出功能
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
from collections import defaultdict
import argparse

from storage.database import DatabaseManager
from analytics.tag_extractor import TagExtractor
from analytics.content_evaluator import ContentEvaluator
from utils.logger import logger


class ObsidianExporter:
    """Obsidian 导出器"""
    
    def __init__(self, vault_path: str = "obsidian_vault"):
        self.vault_path = Path(vault_path)
        self.db = DatabaseManager(use_mongodb=False)
        self.tag_extractor = TagExtractor(use_mongodb=False)
        self.content_evaluator = ContentEvaluator(use_mongodb=False)
        
        # 创建 Obsidian Vault 目录结构
        self.vault_path.mkdir(parents=True, exist_ok=True)
        (self.vault_path / "Articles").mkdir(exist_ok=True)
        (self.vault_path / "Authors").mkdir(exist_ok=True)
        (self.vault_path / "Tags").mkdir(exist_ok=True)
        (self.vault_path / "Daily Notes").mkdir(exist_ok=True)
        (self.vault_path / "Templates").mkdir(exist_ok=True)
        
        # 标签映射
        self.tag_mapping = {
            # 技术栈
            'web3': 'tech/web3',
            'blockchain': 'tech/blockchain',
            'defi': 'tech/defi',
            'nft': 'tech/nft',
            'dao': 'tech/dao',
            'ai': 'tech/ai',
            'rust': 'lang/rust',
            'python': 'lang/python',
            'javascript': 'lang/javascript',
            'typescript': 'lang/typescript',
            'go': 'lang/go',
            'solidity': 'lang/solidity',
            
            # 来源
            'github': 'source/github',
            'twitter': 'source/twitter',
            'medium': 'source/medium',
            'wechat': 'source/wechat',
            
            # 类型
            'tutorial': 'type/tutorial',
            'news': 'type/news',
            'analysis': 'type/analysis',
            'tool': 'type/tool',
            'project': 'type/project',
        }
    
    def clean_filename(self, filename: str) -> str:
        """清理文件名，符合 Obsidian 规范"""
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = re.sub(r'[\[\]]', '', filename)  # 移除方括号
        filename = filename.strip()
        
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename or "untitled"
    
    def generate_obsidian_tags(self, article: Dict) -> List[str]:
        """生成 Obsidian 格式的标签"""
        tags = []
        
        # 从内容中提取关键词
        text = f"{article.get('title', '')} {article.get('content', '')}".lower()
        
        # 映射预定义标签
        for keyword, tag in self.tag_mapping.items():
            if keyword in text:
                tags.append(tag)
        
        # 添加作者标签
        if article.get('author'):
            author = self.clean_filename(article['author'])
            tags.append(f"author/{author}")
        
        # 添加来源标签
        if article.get('account_name'):
            account = self.clean_filename(article['account_name'])
            tags.append(f"account/{account}")
        
        # 添加时间标签
        if article.get('publish_time'):
            try:
                dt = datetime.fromisoformat(article['publish_time'].replace('Z', '+00:00'))
                tags.append(f"year/{dt.year}")
                tags.append(f"month/{dt.year}-{dt.month:02d}")
            except:
                pass
        
        # 使用智能标签提取
        try:
            tag_result = self.tag_extractor.extract_article_tags(article)
            
            # 技术栈标签
            for tech in tag_result.tech_stack[:5]:
                tech_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', tech)
                if tech_clean:
                    tags.append(f"tech/{tech_clean.lower()}")
            
            # 难度标签
            if tag_result.difficulty_level:
                tags.append(f"difficulty/{tag_result.difficulty_level}")
            
            # 主要分类
            if tag_result.main_category:
                tags.append(f"category/{tag_result.main_category}")
        except Exception as e:
            logger.warning(f"智能标签提取失败: {e}")
        
        # 质量标签
        try:
            quality = self.content_evaluator.evaluate_article_quality(article)
            tags.append(f"quality/{quality.quality_grade}")
            
            # 文章长度标签
            if quality.word_count < 500:
                tags.append("length/short")
            elif quality.word_count < 1500:
                tags.append("length/medium")
            else:
                tags.append("length/long")
        except Exception as e:
            logger.warning(f"质量评估失败: {e}")
        
        # 去重并排序
        return sorted(list(set(tags)))
    
    def create_frontmatter(self, article: Dict) -> Dict:
        """创建 Obsidian YAML frontmatter"""
        frontmatter = {
            'title': article.get('title', ''),
            'url': article.get('url', ''),
            'author': article.get('author', ''),
            'account': article.get('account_name', ''),
            'created': datetime.now().isoformat(),
            'tags': self.generate_obsidian_tags(article)
        }
        
        # 添加发布时间
        if article.get('publish_time'):
            try:
                dt = datetime.fromisoformat(article['publish_time'].replace('Z', '+00:00'))
                frontmatter['published'] = dt.isoformat()
                frontmatter['date'] = dt.strftime('%Y-%m-%d')
            except:
                pass
        
        # 添加质量评估
        try:
            quality = self.content_evaluator.evaluate_article_quality(article)
            frontmatter['quality'] = {
                'grade': quality.quality_grade,
                'score': round(quality.quality_metrics.overall_score, 2),
                'word_count': quality.word_count,
                'reading_time': quality.reading_time
            }
        except Exception as e:
            logger.warning(f"质量评估失败: {e}")
        
        return frontmatter
    
    def create_wikilinks(self, article: Dict) -> List[str]:
        """创建 Obsidian 风格的双向链接"""
        links = []
        
        # 作者链接
        if article.get('author'):
            author = self.clean_filename(article['author'])
            links.append(f"[[Authors/{author}]]")
        
        # 账号链接
        if article.get('account_name'):
            account = self.clean_filename(article['account_name'])
            links.append(f"[[Accounts/{account}]]")
        
        # 标签链接
        tags = self.generate_obsidian_tags(article)
        for tag in tags[:10]:  # 限制标签数量
            tag_clean = tag.replace('/', '-')
            links.append(f"[[Tags/{tag_clean}]]")
        
        return links
    
    def generate_article_note(self, article: Dict) -> str:
        """生成单篇文章的 Obsidian 笔记"""
        # 创建 frontmatter
        frontmatter = self.create_frontmatter(article)
        
        # 创建YAML frontmatter 手动格式化
        yaml_content = []
        for key, value in frontmatter.items():
            if isinstance(value, list):
                yaml_content.append(f"{key}:")
                for item in value:
                    yaml_content.append(f"  - {item}")
            elif isinstance(value, dict):
                yaml_content.append(f"{key}:")
                for k, v in value.items():
                    yaml_content.append(f"  {k}: {v}")
            else:
                yaml_content.append(f"{key}: {value}")
        
        # 创建内容
        content = f"""---
{chr(10).join(yaml_content)}
---

# {article.get('title', '无标题')}

## 📝 摘要

{article.get('content', '无内容')[:200]}...

## 🔗 链接

- **原文**: [{article.get('url', '#')}]({article.get('url', '#')})
- **作者**: [[Authors/{self.clean_filename(article.get('author', ''))}]]
- **来源**: [[Accounts/{self.clean_filename(article.get('account_name', ''))}]]

## 🏷️ 标签

{' '.join([f'#{tag}' for tag in frontmatter['tags']])}

## 📊 相关笔记

### 同作者文章
```dataview
LIST
FROM "Articles"
WHERE author = "{article.get('author', '')}"
AND file.name != this.file.name
SORT date DESC
LIMIT 5
```

### 相似标签文章
```dataview
LIST
FROM "Articles"
WHERE contains(tags, "{frontmatter['tags'][0] if frontmatter['tags'] else 'none'}")
AND file.name != this.file.name
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

---

*创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*来源: Web3极客日报*
"""
        
        return content
    
    def create_index_note(self, articles: List[Dict]) -> str:
        """创建索引笔记"""
        content = f"""---
title: "Web3极客日报 - 文章索引"
created: {datetime.now().isoformat()}
tags: [index, web3, articles]
---

# 📚 Web3极客日报 - 文章索引

> 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> 总文章数: {len(articles)}

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
"""
        
        return content
    
    def create_author_notes(self, articles: List[Dict]) -> None:
        """创建作者笔记"""
        authors = defaultdict(list)
        
        # 按作者分组
        for article in articles:
            author = article.get('author', 'Unknown')
            authors[author].append(article)
        
        # 为每个作者创建笔记
        for author, author_articles in authors.items():
            if not author or author == 'Unknown':
                continue
                
            author_clean = self.clean_filename(author)
            author_file = self.vault_path / "Authors" / f"{author_clean}.md"
            
            # 统计信息
            total_articles = len(author_articles)
            quality_stats = defaultdict(int)
            
            for article in author_articles:
                try:
                    quality = self.content_evaluator.evaluate_article_quality(article)
                    quality_stats[quality.quality_grade] += 1
                except:
                    quality_stats['Unknown'] += 1
            
            content = f"""---
title: "{author}"
type: author
created: {datetime.now().isoformat()}
tags: [author, person]
---

# 👤 {author}

## 📊 统计信息

- **总文章数**: {total_articles}
- **质量分布**:
  - A级: {quality_stats.get('A', 0)} 篇
  - B级: {quality_stats.get('B', 0)} 篇  
  - C级: {quality_stats.get('C', 0)} 篇
  - D级: {quality_stats.get('D', 0)} 篇

## 📚 所有文章

```dataview
TABLE date as "日期", quality.grade as "质量", quality.score as "评分"
FROM "Articles"
WHERE author = "{author}"
SORT date DESC
```

## 🏷️ 常用标签

```dataview
TABLE length(rows) as "文章数"
FROM "Articles"
WHERE author = "{author}"
FLATTEN tags
GROUP BY tags
SORT length(rows) DESC
LIMIT 10
```

## 📈 发布时间线

```dataview
CALENDAR date
FROM "Articles"
WHERE author = "{author}"
```

---

*作者信息自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            
            with open(author_file, 'w', encoding='utf-8') as f:
                f.write(content)
    
    def create_templates(self) -> None:
        """创建 Obsidian 模板"""
        
        # 文章模板
        article_template = """---
title: "{{title}}"
url: "{{url}}"
author: "{{author}}"
account: "{{account}}"
created: {{date:YYYY-MM-DD}}
tags: []
---

# {{title}}

## 📝 摘要

{{content}}

## 🔗 链接

- **原文**: [{{url}}]({{url}})
- **作者**: [[Authors/{{author}}]]

## 🏷️ 标签

#

## 💭 我的思考

> [!note] 个人笔记
> 在这里添加你的思考和笔记...

## 📚 相关资源

- 
- 
- 

---

*创建时间: {{date:YYYY-MM-DD HH:mm:ss}}*
"""
        
        template_file = self.vault_path / "Templates" / "Article Template.md"
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(article_template)
    
    def create_obsidian_config(self) -> None:
        """创建 Obsidian 配置文件"""
        obsidian_dir = self.vault_path / ".obsidian"
        obsidian_dir.mkdir(exist_ok=True)
        
        # 工作区配置
        workspace_config = {
            "main": {
                "id": "web3-articles",
                "type": "split",
                "children": [
                    {
                        "id": "file-explorer",
                        "type": "leaf",
                        "state": {
                            "type": "file-explorer",
                            "state": {}
                        }
                    }
                ]
            },
            "left": {
                "id": "sidebar",
                "type": "split",
                "children": [
                    {
                        "id": "file-explorer-tab",
                        "type": "leaf",
                        "state": {
                            "type": "file-explorer",
                            "state": {}
                        }
                    },
                    {
                        "id": "search-tab",
                        "type": "leaf",
                        "state": {
                            "type": "search",
                            "state": {}
                        }
                    },
                    {
                        "id": "tag-tab",
                        "type": "leaf",
                        "state": {
                            "type": "tag",
                            "state": {}
                        }
                    }
                ]
            }
        }
        
        import json
        with open(obsidian_dir / "workspace.json", 'w', encoding='utf-8') as f:
            json.dump(workspace_config, f, indent=2, ensure_ascii=False)
        
        # 推荐插件配置
        plugins_config = {
            "dataview": True,
            "tag-wrangler": True,
            "calendar": True,
            "templater-obsidian": True,
            "obsidian-git": True
        }
        
        with open(obsidian_dir / "community-plugins.json", 'w', encoding='utf-8') as f:
            json.dump(list(plugins_config.keys()), f, indent=2)
    
    def export_for_obsidian(self, 
                           export_type: str = "index", 
                           limit: Optional[int] = None) -> None:
        """导出到 Obsidian"""
        
        logger.info(f"开始导出到 Obsidian Vault: {self.vault_path}")
        
        # 获取所有文章
        articles = []
        try:
            with self.db.get_session() as session:
                from storage.models import ArticleDB
                query = session.query(ArticleDB).order_by(ArticleDB.publish_time.desc())
                
                if limit:
                    query = query.limit(limit)
                
                articles = [article.to_dict() for article in query.all()]
        except Exception as e:
            logger.error(f"获取文章失败: {e}")
            return
        
        if not articles:
            logger.warning("没有找到任何文章")
            return
        
        logger.info(f"找到 {len(articles)} 篇文章")
        
        if export_type == "index":
            # 创建索引笔记
            index_content = self.create_index_note(articles)
            index_file = self.vault_path / "📚 Web3极客日报索引.md"
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(index_content)
            logger.info(f"索引笔记已创建: {index_file}")
            
        elif export_type == "full":
            # 创建所有文章笔记
            for i, article in enumerate(articles):
                try:
                    title = article.get('title', '无标题')
                    clean_title = self.clean_filename(title)
                    filename = f"{i+1:04d}_{clean_title}.md"
                    
                    article_content = self.generate_article_note(article)
                    article_file = self.vault_path / "Articles" / filename
                    
                    with open(article_file, 'w', encoding='utf-8') as f:
                        f.write(article_content)
                    
                    if (i + 1) % 100 == 0:
                        logger.info(f"已创建 {i + 1} 篇文章笔记")
                        
                except Exception as e:
                    logger.error(f"创建文章笔记失败: {e}")
            
            # 创建作者笔记
            self.create_author_notes(articles)
            
            # 创建索引笔记
            index_content = self.create_index_note(articles)
            index_file = self.vault_path / "📚 Web3极客日报索引.md"
            with open(index_file, 'w', encoding='utf-8') as f:
                f.write(index_content)
        
        # 创建模板和配置
        self.create_templates()
        self.create_obsidian_config()
        
        logger.info(f"导出完成！Vault 路径: {self.vault_path}")
        
        # 打印统计信息
        print(f"\n=== Obsidian 导出统计 ===")
        print(f"总文章数: {len(articles)}")
        print(f"Vault 路径: {self.vault_path}")
        print(f"导出类型: {export_type}")
        
        if export_type == "full":
            print(f"文章笔记: {len(articles)} 个")
            authors = set(article.get('author', '') for article in articles)
            print(f"作者笔记: {len(authors)} 个")
        
        print(f"\n📝 推荐安装的 Obsidian 插件:")
        print("  - Dataview (数据查询)")
        print("  - Calendar (日历视图)")
        print("  - Tag Wrangler (标签管理)")
        print("  - Templater (模板)")
        print("  - Obsidian Git (版本控制)")
        
        # 关闭数据库连接
        self.db.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="导出到 Obsidian")
    parser.add_argument('--vault', default='obsidian_vault',
                        help='Obsidian Vault 路径 (默认: obsidian_vault)')
    parser.add_argument('--type', choices=['index', 'full'], default='index',
                        help='导出类型 (默认: index)')
    parser.add_argument('--limit', '-l', type=int,
                        help='限制导出文章数量')
    
    args = parser.parse_args()
    
    # 创建导出器
    exporter = ObsidianExporter(vault_path=args.vault)
    
    # 执行导出
    exporter.export_for_obsidian(
        export_type=args.type,
        limit=args.limit
    )


if __name__ == "__main__":
    main()