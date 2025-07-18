#!/usr/bin/env python3
"""
将所有文章导出为 Markdown 格式，支持分类和标签
"""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
import argparse

from storage.database import DatabaseManager
from analytics.tag_extractor import TagExtractor
from analytics.content_evaluator import ContentEvaluator
from utils.logger import logger


class MarkdownExporter:
    """Markdown 导出器"""
    
    def __init__(self, output_dir: str = "export/markdown"):
        self.output_dir = Path(output_dir)
        self.db = DatabaseManager(use_mongodb=False)  # 强制使用 SQLite
        self.tag_extractor = TagExtractor(use_mongodb=False)
        self.content_evaluator = ContentEvaluator(use_mongodb=False)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 分类映射
        self.category_mapping = {
            # Web3 & 区块链
            'web3': 'Web3与区块链',
            'blockchain': 'Web3与区块链',
            'defi': 'DeFi',
            'nft': 'NFT',
            'dao': 'DAO',
            'ethereum': '以太坊',
            'bitcoin': '比特币',
            'solana': 'Solana',
            'polygon': 'Polygon',
            
            # 开发技术
            'rust': '编程语言/Rust',
            'python': '编程语言/Python',
            'javascript': '编程语言/JavaScript',
            'typescript': '编程语言/TypeScript',
            'go': '编程语言/Go',
            'solidity': '智能合约',
            
            # AI & 机器学习
            'ai': 'AI与机器学习',
            'chatgpt': 'AI与机器学习/ChatGPT',
            'gpt': 'AI与机器学习/GPT',
            'llm': 'AI与机器学习/LLM',
            'machine learning': 'AI与机器学习',
            
            # 工具 & 平台
            'github': '开发工具/GitHub',
            'docker': '开发工具/Docker',
            'kubernetes': '开发工具/Kubernetes',
            'vscode': '开发工具/VSCode',
            
            # Layer2 & 扩容
            'rollup': 'Layer2技术',
            'optimism': 'Layer2技术/Optimism',
            'arbitrum': 'Layer2技术/Arbitrum',
            'layer2': 'Layer2技术',
            
            # 其他
            'zero knowledge': '零知识证明',
            '零知识证明': '零知识证明',
            'zk-snark': '零知识证明',
            'staking': 'Staking',
            'mining': '挖矿',
        }
    
    def clean_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除或替换非法字符
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)
        filename = filename.strip()
        # 限制长度
        if len(filename) > 100:
            filename = filename[:100]
        return filename or "untitled"
    
    def extract_categories(self, article: Dict) -> Set[str]:
        """从文章中提取分类"""
        categories = set()
        
        # 从标题和内容中提取
        text = f"{article.get('title', '')} {article.get('content', '')}".lower()
        
        for keyword, category in self.category_mapping.items():
            if keyword in text:
                categories.add(category)
        
        # 使用标签提取器获取更多分类信息
        try:
            tags = self.tag_extractor.extract_article_tags(article)
            for tech in tags.tech_stack:
                tech_lower = tech.lower()
                for keyword, category in self.category_mapping.items():
                    if keyword in tech_lower:
                        categories.add(category)
                        break
        except Exception as e:
            logger.warning(f"标签提取失败: {e}")
        
        # 如果没有分类，设置默认分类
        if not categories:
            categories.add("其他")
        
        return categories
    
    def generate_tags(self, article: Dict) -> List[str]:
        """生成文章标签"""
        tags = []
        
        try:
            # 使用标签提取器
            tag_result = self.tag_extractor.extract_article_tags(article)
            
            # 技术栈标签
            tags.extend([f"#{tech}" for tech in tag_result.tech_stack[:5]])
            
            # 难度标签
            if tag_result.difficulty_level:
                tags.append(f"#难度_{tag_result.difficulty_level}")
            
            # 内容类型标签
            content_type_tag = next((tag for tag in tag_result.tags if tag.category == "内容类型"), None)
            if content_type_tag:
                tags.append(f"#{content_type_tag.name}")
            
            # 质量评估标签
            quality = self.content_evaluator.evaluate_article_quality(article)
            tags.append(f"#质量等级_{quality.quality_grade}")
            
            # 字数标签
            word_count = quality.word_count
            if word_count < 500:
                tags.append("#短文")
            elif word_count < 1500:
                tags.append("#中文")
            else:
                tags.append("#长文")
            
        except Exception as e:
            logger.warning(f"生成标签失败: {e}")
            tags = ["#未分类"]
        
        return tags
    
    def format_article_to_markdown(self, article: Dict) -> str:
        """将文章格式化为 Markdown"""
        # 提取基本信息
        title = article.get('title', '无标题')
        author = article.get('author', '未知作者')
        account = article.get('account_name', '未知账号')
        publish_time = article.get('publish_time', '')
        url = article.get('url', '')
        content = article.get('content', '')
        
        # 生成标签
        tags = self.generate_tags(article)
        
        # 格式化发布时间
        if publish_time:
            try:
                dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                publish_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                pass
        
        # 构建 Markdown 内容
        md_content = f"""# {title}

## 元信息

- **作者**: {author}
- **发布账号**: {account}
- **发布时间**: {publish_time}
- **原文链接**: [{url}]({url})
- **标签**: {' '.join(tags)}

---

## 正文

{content}

---

## 文章分析

"""
        
        # 添加质量评估信息
        try:
            quality = self.content_evaluator.evaluate_article_quality(article)
            md_content += f"""### 质量评估

- **总体评分**: {quality.quality_metrics.overall_score:.2f}/1.00
- **质量等级**: {quality.quality_grade}
- **字数**: {quality.word_count}
- **预计阅读时间**: {quality.reading_time} 分钟

#### 详细指标

| 指标 | 分数 |
|------|------|
| 原创性 | {quality.quality_metrics.originality_score:.2f} |
| 技术深度 | {quality.quality_metrics.technical_depth_score:.2f} |
| 可读性 | {quality.quality_metrics.readability_score:.2f} |
| 结构化 | {quality.quality_metrics.structure_score:.2f} |
| 参与度 | {quality.quality_metrics.engagement_score:.2f} |
| 完整性 | {quality.quality_metrics.completeness_score:.2f} |

"""
            
            # 添加要点和建议
            if quality.key_points:
                md_content += "#### 文章要点\n\n"
                for point in quality.key_points:
                    md_content += f"- {point}\n"
                md_content += "\n"
            
            if quality.improvement_suggestions:
                md_content += "#### 改进建议\n\n"
                for suggestion in quality.improvement_suggestions:
                    md_content += f"- {suggestion}\n"
                md_content += "\n"
                
        except Exception as e:
            logger.warning(f"质量评估失败: {e}")
        
        return md_content
    
    def export_by_category(self, articles: List[Dict]) -> Dict[str, int]:
        """按分类导出文章"""
        category_stats = defaultdict(int)
        
        # 为每篇文章分类并导出
        for i, article in enumerate(articles):
            try:
                # 提取分类
                categories = self.extract_categories(article)
                
                # 生成 Markdown 内容
                md_content = self.format_article_to_markdown(article)
                
                # 为每个分类创建文件
                for category in categories:
                    # 创建分类目录
                    category_dir = self.output_dir / category.replace('/', '_')
                    category_dir.mkdir(parents=True, exist_ok=True)
                    
                    # 生成文件名
                    title = article.get('title', '无标题')
                    clean_title = self.clean_filename(title)
                    filename = f"{i+1:04d}_{clean_title}.md"
                    
                    # 写入文件
                    file_path = category_dir / filename
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(md_content)
                    
                    category_stats[category] += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f"已导出 {i + 1} 篇文章")
                    
            except Exception as e:
                logger.error(f"导出文章失败 (ID: {article.get('id')}): {e}")
        
        return dict(category_stats)
    
    def export_by_date(self, articles: List[Dict]) -> Dict[str, int]:
        """按日期导出文章"""
        date_stats = defaultdict(int)
        
        for i, article in enumerate(articles):
            try:
                # 提取日期
                publish_time = article.get('publish_time', '')
                if publish_time:
                    try:
                        dt = datetime.fromisoformat(publish_time.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m')
                    except:
                        date_str = 'unknown'
                else:
                    date_str = 'unknown'
                
                # 创建日期目录
                date_dir = self.output_dir / 'by_date' / date_str
                date_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成文件名
                title = article.get('title', '无标题')
                clean_title = self.clean_filename(title)
                filename = f"{i+1:04d}_{clean_title}.md"
                
                # 生成并写入 Markdown
                md_content = self.format_article_to_markdown(article)
                file_path = date_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                date_stats[date_str] += 1
                
            except Exception as e:
                logger.error(f"按日期导出失败 (ID: {article.get('id')}): {e}")
        
        return dict(date_stats)
    
    def export_by_author(self, articles: List[Dict]) -> Dict[str, int]:
        """按作者导出文章"""
        author_stats = defaultdict(int)
        
        for i, article in enumerate(articles):
            try:
                # 提取作者
                author = article.get('author', '未知作者')
                clean_author = self.clean_filename(author)
                
                # 创建作者目录
                author_dir = self.output_dir / 'by_author' / clean_author
                author_dir.mkdir(parents=True, exist_ok=True)
                
                # 生成文件名
                title = article.get('title', '无标题')
                clean_title = self.clean_filename(title)
                filename = f"{i+1:04d}_{clean_title}.md"
                
                # 生成并写入 Markdown
                md_content = self.format_article_to_markdown(article)
                file_path = author_dir / filename
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                
                author_stats[author] += 1
                
            except Exception as e:
                logger.error(f"按作者导出失败 (ID: {article.get('id')}): {e}")
        
        return dict(author_stats)
    
    def generate_index(self, articles: List[Dict], stats: Dict[str, Dict[str, int]]):
        """生成索引文件"""
        index_content = f"""# Web3极客日报 Markdown 导出

导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
总文章数: {len(articles)}

## 统计信息

### 分类统计

| 分类 | 文章数 |
|------|--------|
"""
        
        # 分类统计
        if 'category' in stats:
            for category, count in sorted(stats['category'].items(), key=lambda x: x[1], reverse=True):
                index_content += f"| {category} | {count} |\n"
        
        index_content += "\n### 作者统计 (Top 20)\n\n| 作者 | 文章数 |\n|------|--------|\n"
        
        # 作者统计
        if 'author' in stats:
            author_sorted = sorted(stats['author'].items(), key=lambda x: x[1], reverse=True)[:20]
            for author, count in author_sorted:
                index_content += f"| {author} | {count} |\n"
        
        index_content += "\n### 时间分布\n\n| 月份 | 文章数 |\n|------|--------|\n"
        
        # 时间统计
        if 'date' in stats:
            for date, count in sorted(stats['date'].items(), reverse=True)[:12]:
                index_content += f"| {date} | {count} |\n"
        
        index_content += """

## 目录结构

```
export/markdown/
├── README.md (本文件)
├── Web3与区块链/
├── DeFi/
├── NFT/
├── AI与机器学习/
├── 编程语言/
│   ├── Rust/
│   ├── Python/
│   └── ...
├── by_author/
│   ├── 作者名/
│   └── ...
└── by_date/
    ├── 2025-01/
    └── ...
```

## 使用说明

1. **按分类浏览**: 进入相应的分类文件夹查看该类别的所有文章
2. **按作者浏览**: 进入 `by_author` 文件夹查看特定作者的所有文章
3. **按时间浏览**: 进入 `by_date` 文件夹查看特定月份的文章

每篇文章都包含：
- 元信息（作者、发布时间、原文链接等）
- 完整的文章内容
- 自动生成的标签
- 质量评估报告
- 文章要点提取

## 标签说明

- `#技术栈名称`: 文章涉及的技术
- `#难度_级别`: 文章难度（入门/进阶/高级）
- `#内容类型`: 教程/新闻/分析等
- `#质量等级_X`: 文章质量评级（A/B/C/D）
- `#短文/#中文/#长文`: 文章长度分类
"""
        
        # 写入索引文件
        index_path = self.output_dir / "README.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        logger.info(f"索引文件已生成: {index_path}")
    
    def export_all(self, 
                   by_category: bool = True,
                   by_date: bool = True,
                   by_author: bool = True,
                   limit: Optional[int] = None):
        """导出所有文章"""
        logger.info("开始导出文章到 Markdown...")
        
        # 获取所有文章
        articles = []
        try:
            if self.db.use_mongodb:
                cursor = self.db.articles_collection.find({})
                if limit:
                    cursor = cursor.limit(limit)
                articles = list(cursor)
            else:
                with self.db.get_session() as session:
                    from storage.models import ArticleDB
                    query = session.query(ArticleDB)
                    if limit:
                        query = query.limit(limit)
                    articles = [article.to_dict() for article in query.all()]
        except Exception as e:
            logger.error(f"获取文章失败: {e}")
            return
        
        if not articles:
            logger.warning("没有找到任何文章")
            return
        
        logger.info(f"找到 {len(articles)} 篇文章，开始导出...")
        
        stats = {}
        
        # 按分类导出
        if by_category:
            logger.info("按分类导出...")
            stats['category'] = self.export_by_category(articles)
        
        # 按日期导出
        if by_date:
            logger.info("按日期导出...")
            stats['date'] = self.export_by_date(articles)
        
        # 按作者导出
        if by_author:
            logger.info("按作者导出...")
            stats['author'] = self.export_by_author(articles)
        
        # 生成索引
        self.generate_index(articles, stats)
        
        # 关闭数据库连接
        self.db.close()
        
        logger.info(f"导出完成！文件保存在: {self.output_dir}")
        
        # 打印统计信息
        print("\n=== 导出统计 ===")
        print(f"总文章数: {len(articles)}")
        
        if 'category' in stats:
            print(f"\n分类数: {len(stats['category'])}")
            print("Top 5 分类:")
            for cat, count in sorted(stats['category'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {cat}: {count} 篇")
        
        if 'author' in stats:
            print(f"\n作者数: {len(stats['author'])}")
            print("Top 5 作者:")
            for author, count in sorted(stats['author'].items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  - {author}: {count} 篇")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="将文章导出为 Markdown 格式")
    parser.add_argument('--output', '-o', default='export/markdown',
                        help='输出目录 (默认: export/markdown)')
    parser.add_argument('--limit', '-l', type=int,
                        help='限制导出文章数量')
    parser.add_argument('--no-category', action='store_true',
                        help='不按分类导出')
    parser.add_argument('--no-date', action='store_true',
                        help='不按日期导出')
    parser.add_argument('--no-author', action='store_true',
                        help='不按作者导出')
    
    args = parser.parse_args()
    
    # 创建导出器
    exporter = MarkdownExporter(output_dir=args.output)
    
    # 执行导出
    exporter.export_all(
        by_category=not args.no_category,
        by_date=not args.no_date,
        by_author=not args.no_author,
        limit=args.limit
    )


if __name__ == "__main__":
    main()