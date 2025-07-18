#!/usr/bin/env python3
"""
简单列表导出脚本
将所有文章导出为单个 Markdown 文件，每个条目格式: [title](url) -- 说明
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import argparse

from storage.database import DatabaseManager
from utils.logger import logger


class SimpleListExporter:
    """简单列表导出器"""
    
    def __init__(self):
        self.db = DatabaseManager(use_mongodb=False)  # 强制使用 SQLite
    
    def clean_text(self, text: str) -> str:
        """清理文本，移除换行符和多余空格"""
        if not text:
            return ""
        
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除前后空格
        text = text.strip()
        
        return text
    
    def truncate_text(self, text: str, max_length: int = 100) -> str:
        """截断文本到指定长度"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        # 在最后一个空格处截断，避免截断单词
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        
        if last_space > max_length * 0.8:  # 如果最后一个空格离结尾不太远
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def generate_description(self, article: Dict) -> str:
        """生成文章描述"""
        parts = []
        
        # 添加作者信息
        if article.get('author'):
            parts.append(f"by {article['author']}")
        
        # 添加发布时间
        if article.get('publish_time'):
            try:
                dt = datetime.fromisoformat(article['publish_time'].replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
                parts.append(date_str)
            except:
                pass
        
        # 添加内容摘要
        content = article.get('content', '')
        if content:
            content_clean = self.clean_text(content)
            content_summary = self.truncate_text(content_clean, 80)
            if content_summary:
                parts.append(content_summary)
        
        return " | ".join(parts) if parts else "No description"
    
    def export_to_single_file(self, 
                             output_file: str = "all_articles.md",
                             limit: Optional[int] = None,
                             sort_by: str = "date",
                             group_by: Optional[str] = None) -> None:
        """导出所有文章到单个文件"""
        
        logger.info(f"开始导出文章到单个文件: {output_file}")
        
        # 获取所有文章
        articles = []
        try:
            with self.db.get_session() as session:
                from storage.models import ArticleDB
                query = session.query(ArticleDB)
                
                # 排序
                if sort_by == "date":
                    query = query.order_by(ArticleDB.publish_time.desc())
                elif sort_by == "title":
                    query = query.order_by(ArticleDB.title)
                elif sort_by == "author":
                    query = query.order_by(ArticleDB.author)
                
                # 限制数量
                if limit:
                    query = query.limit(limit)
                
                articles = [article.to_dict() for article in query.all()]
        except Exception as e:
            logger.error(f"获取文章失败: {e}")
            return
        
        if not articles:
            logger.warning("没有找到任何文章")
            return
        
        logger.info(f"找到 {len(articles)} 篇文章，开始生成文件...")
        
        # 生成 Markdown 内容
        content = self.generate_markdown_content(articles, group_by)
        
        # 写入文件
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"导出完成！文件保存在: {output_path}")
        
        # 打印统计信息
        print(f"\n=== 导出统计 ===")
        print(f"总文章数: {len(articles)}")
        print(f"输出文件: {output_path}")
        print(f"文件大小: {output_path.stat().st_size / 1024:.1f} KB")
        
        # 统计作者
        authors = {}
        for article in articles:
            author = article.get('author', 'Unknown')
            authors[author] = authors.get(author, 0) + 1
        
        print(f"\n作者统计 (Top 10):")
        for author, count in sorted(authors.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {author}: {count} 篇")
        
        # 关闭数据库连接
        self.db.close()
    
    def generate_markdown_content(self, articles: List[Dict], group_by: Optional[str] = None) -> str:
        """生成 Markdown 内容"""
        
        # 文件头部
        content = f"""# Web3极客日报 文章列表

> 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
> 总文章数: {len(articles)}

---

"""
        
        if group_by:
            content += self.generate_grouped_content(articles, group_by)
        else:
            content += self.generate_simple_list(articles)
        
        # 文件尾部
        content += f"""

---

*共 {len(articles)} 篇文章 | 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return content
    
    def generate_simple_list(self, articles: List[Dict]) -> str:
        """生成简单列表"""
        content = ""
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', '无标题')
            url = article.get('url', '#')
            description = self.generate_description(article)
            
            # 清理标题中的特殊字符
            title_clean = self.clean_text(title)
            
            content += f"{i}. [{title_clean}]({url}) -- {description}\n"
        
        return content
    
    def generate_grouped_content(self, articles: List[Dict], group_by: str) -> str:
        """生成分组内容"""
        from collections import defaultdict
        
        groups = defaultdict(list)
        
        # 分组文章
        for article in articles:
            if group_by == "author":
                key = article.get('author', 'Unknown')
            elif group_by == "date":
                try:
                    dt = datetime.fromisoformat(article['publish_time'].replace('Z', '+00:00'))
                    key = dt.strftime('%Y-%m')
                except:
                    key = 'Unknown'
            elif group_by == "account":
                key = article.get('account_name', 'Unknown')
            else:
                key = 'All'
            
            groups[key].append(article)
        
        # 生成内容
        content = ""
        for group_name in sorted(groups.keys()):
            group_articles = groups[group_name]
            content += f"## {group_name} ({len(group_articles)} 篇)\n\n"
            
            for i, article in enumerate(group_articles, 1):
                title = article.get('title', '无标题')
                url = article.get('url', '#')
                description = self.generate_description(article)
                
                # 清理标题中的特殊字符
                title_clean = self.clean_text(title)
                
                content += f"{i}. [{title_clean}]({url}) -- {description}\n"
            
            content += "\n"
        
        return content


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="导出所有文章到单个 Markdown 文件")
    parser.add_argument('--output', '-o', default='all_articles.md',
                        help='输出文件路径 (默认: all_articles.md)')
    parser.add_argument('--limit', '-l', type=int,
                        help='限制导出文章数量')
    parser.add_argument('--sort', choices=['date', 'title', 'author'], default='date',
                        help='排序方式 (默认: date)')
    parser.add_argument('--group', choices=['author', 'date', 'account'],
                        help='分组方式 (可选)')
    
    args = parser.parse_args()
    
    # 创建导出器
    exporter = SimpleListExporter()
    
    # 执行导出
    exporter.export_to_single_file(
        output_file=args.output,
        limit=args.limit,
        sort_by=args.sort,
        group_by=args.group
    )


if __name__ == "__main__":
    main()