"""
趋势分析模块
分析热门技术栈和关键词趋势、作者活跃度、文章发布频率等
"""

import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import json
import math

from storage.database import DatabaseManager
from utils.logger import logger


@dataclass
class TrendData:
    """趋势数据结构"""
    keyword: str
    count: int
    percentage: float
    growth_rate: Optional[float] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


@dataclass
class AuthorStats:
    """作者统计数据"""
    author: str
    article_count: int
    total_words: int
    avg_article_length: float
    most_active_period: str
    influence_score: float
    top_keywords: List[str]


@dataclass
class TimeSeriesPoint:
    """时间序列数据点"""
    date: str
    count: int
    cumulative: int


class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self, use_mongodb: bool = False):
        self.db = DatabaseManager(use_mongodb=use_mongodb)
        self.tech_keywords = {
            # Web3 & 区块链
            'web3', 'blockchain', 'defi', 'nft', 'dao', 'ethereum', 'bitcoin', 'solana',
            'polygon', 'avalanche', 'binance smart chain', 'arbitrum', 'optimism',
            'layer2', 'rollup', 'zk-snark', 'zk-stark', 'zero knowledge', '零知识证明',
            'smart contract', '智能合约', 'dapp', 'metamask', 'uniswap', 'opensea',
            'minting', 'staking', 'yield farming', 'liquidity mining', 'governance token',
            
            # AI & 机器学习
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'transformer', 'gpt', 'llm', 'chatgpt', 'openai', 'anthropic', 'claude',
            'stable diffusion', 'generative ai', 'prompt engineering', 'fine-tuning',
            'reinforcement learning', 'computer vision', 'natural language processing',
            'ai', '人工智能', '机器学习', '深度学习', '大模型', '生成式ai',
            
            # 编程语言
            'python', 'javascript', 'typescript', 'rust', 'go', 'golang', 'java',
            'c++', 'c#', 'kotlin', 'swift', 'php', 'ruby', 'scala', 'haskell',
            'solidity', 'vyper', 'move', 'cairo',
            
            # 框架和技术
            'react', 'vue', 'angular', 'svelte', 'next.js', 'nuxt', 'express',
            'fastapi', 'django', 'flask', 'spring', 'laravel', 'rails',
            'docker', 'kubernetes', 'microservices', 'serverless', 'lambda',
            'aws', 'azure', 'gcp', 'vercel', 'netlify',
            'postgresql', 'mongodb', 'redis', 'elasticsearch', 'kafka',
            
            # 开发工具
            'git', 'github', 'gitlab', 'vscode', 'vim', 'emacs', 'jetbrains',
            'webpack', 'vite', 'babel', 'eslint', 'prettier', 'jest', 'cypress',
            'figma', 'sketch', 'postman', 'insomnia',
            
            # 其他热门技术
            'graphql', 'rest api', 'websocket', 'grpc', 'oauth', 'jwt',
            'cicd', 'devops', 'terraform', 'ansible', 'jenkins', 'github actions',
            'monitoring', 'logging', 'prometheus', 'grafana', 'elk stack'
        }
    
    def extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取技术关键词"""
        if not text:
            return []
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.tech_keywords:
            # 使用词边界匹配，避免部分匹配
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower):
                found_keywords.append(keyword)
        
        # 提取代码相关的模式
        code_patterns = [
            r'\b[A-Z][a-zA-Z0-9]*\.[a-z][a-zA-Z0-9]*\b',  # API调用模式
            r'\b[a-z]+\-[a-z]+\b',  # kebab-case
            r'\b[a-z]+_[a-z]+\b',   # snake_case
        ]
        
        for pattern in code_patterns:
            matches = re.findall(pattern, text)
            found_keywords.extend(matches)
        
        return list(set(found_keywords))
    
    def analyze_technology_trends(self, days: int = 30) -> Dict[str, Any]:
        """分析技术趋势"""
        logger.info(f"分析最近 {days} 天的技术趋势")
        
        try:
            # 获取指定时间范围内的文章
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if self.db.use_mongodb:
                articles = list(self.db.articles_collection.find({
                    "crawl_time": {"$gte": cutoff_date.isoformat()}
                }))
            else:
                with self.db.get_session() as session:
                    from storage.models import ArticleDB
                    articles = session.query(ArticleDB).filter(
                        ArticleDB.crawl_time >= cutoff_date
                    ).all()
                    articles = [article.to_dict() for article in articles]
            
            if not articles:
                return {"error": "没有找到指定时间范围内的文章"}
            
            # 提取所有关键词
            all_keywords = []
            keyword_by_date = defaultdict(Counter)
            
            for article in articles:
                title = article.get('title', '')
                content = article.get('content', '')
                text = f"{title} {content}"
                
                # 提取关键词
                keywords = self.extract_keywords_from_text(text)
                all_keywords.extend(keywords)
                
                # 按日期分组统计
                article_date = article.get('publish_time', article.get('crawl_time', ''))
                if article_date:
                    try:
                        if isinstance(article_date, str):
                            date_obj = datetime.fromisoformat(article_date.replace('Z', '+00:00'))
                        else:
                            date_obj = article_date
                        date_key = date_obj.strftime('%Y-%m-%d')
                        for keyword in keywords:
                            keyword_by_date[date_key][keyword] += 1
                    except:
                        continue
            
            # 统计总体趋势
            keyword_counts = Counter(all_keywords)
            total_articles = len(articles)
            
            # 生成趋势数据
            trends = []
            for keyword, count in keyword_counts.most_common(50):
                percentage = (count / total_articles) * 100
                trend_data = TrendData(
                    keyword=keyword,
                    count=count,
                    percentage=percentage
                )
                trends.append(trend_data)
            
            # 计算增长率（与前一周期比较）
            if days >= 14:  # 只有当分析周期足够长时才计算增长率
                prev_cutoff = cutoff_date - timedelta(days=days)
                # 这里可以添加增长率计算逻辑
            
            return {
                "period_days": days,
                "total_articles": total_articles,
                "total_keywords": len(keyword_counts),
                "unique_keywords": len(set(all_keywords)),
                "top_trends": [
                    {
                        "keyword": trend.keyword,
                        "count": trend.count,
                        "percentage": round(trend.percentage, 2),
                        "articles_ratio": f"{trend.count}/{total_articles}"
                    }
                    for trend in trends[:20]
                ],
                "daily_distribution": dict(keyword_by_date),
                "analysis_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"技术趋势分析失败: {str(e)}")
            return {"error": str(e)}
    
    def analyze_author_activity(self, days: int = 30) -> Dict[str, Any]:
        """分析作者活跃度和影响力"""
        logger.info(f"分析最近 {days} 天的作者活跃度")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if self.db.use_mongodb:
                articles = list(self.db.articles_collection.find({
                    "crawl_time": {"$gte": cutoff_date.isoformat()}
                }))
            else:
                with self.db.get_session() as session:
                    from storage.models import ArticleDB
                    articles = session.query(ArticleDB).filter(
                        ArticleDB.crawl_time >= cutoff_date
                    ).all()
                    articles = [article.to_dict() for article in articles]
            
            if not articles:
                return {"error": "没有找到指定时间范围内的文章"}
            
            # 按作者统计
            author_stats = defaultdict(lambda: {
                'article_count': 0,
                'total_words': 0,
                'keywords': Counter(),
                'dates': [],
                'titles': []
            })
            
            for article in articles:
                author = article.get('author', 'Unknown')
                if not author or author in ['Unknown', '']:
                    continue
                
                content = article.get('content', '')
                title = article.get('title', '')
                
                # 统计文章数和字数
                author_stats[author]['article_count'] += 1
                author_stats[author]['total_words'] += len(content)
                author_stats[author]['titles'].append(title)
                
                # 提取关键词
                keywords = self.extract_keywords_from_text(f"{title} {content}")
                for keyword in keywords:
                    author_stats[author]['keywords'][keyword] += 1
                
                # 记录发布日期
                article_date = article.get('publish_time', article.get('crawl_time', ''))
                if article_date:
                    try:
                        if isinstance(article_date, str):
                            date_obj = datetime.fromisoformat(article_date.replace('Z', '+00:00'))
                        else:
                            date_obj = article_date
                        author_stats[author]['dates'].append(date_obj)
                    except:
                        continue
            
            # 计算影响力评分和统计信息
            author_analysis = []
            
            for author, stats in author_stats.items():
                if stats['article_count'] == 0:
                    continue
                
                # 计算平均文章长度
                avg_length = stats['total_words'] / stats['article_count']
                
                # 计算影响力评分（基于文章数量、平均长度、关键词多样性）
                keyword_diversity = len(stats['keywords'])
                influence_score = (
                    stats['article_count'] * 0.4 +
                    min(avg_length / 100, 10) * 0.3 +  # 标准化文章长度
                    keyword_diversity * 0.3
                )
                
                # 确定最活跃时期
                if stats['dates']:
                    dates_counter = Counter([d.strftime('%Y-%m') for d in stats['dates']])
                    most_active_period = dates_counter.most_common(1)[0][0]
                else:
                    most_active_period = "未知"
                
                # 获取热门关键词
                top_keywords = [kw for kw, _ in stats['keywords'].most_common(5)]
                
                author_data = AuthorStats(
                    author=author,
                    article_count=stats['article_count'],
                    total_words=stats['total_words'],
                    avg_article_length=avg_length,
                    most_active_period=most_active_period,
                    influence_score=influence_score,
                    top_keywords=top_keywords
                )
                
                author_analysis.append(author_data)
            
            # 按影响力评分排序
            author_analysis.sort(key=lambda x: x.influence_score, reverse=True)
            
            return {
                "period_days": days,
                "total_authors": len(author_analysis),
                "total_articles": len(articles),
                "top_authors": [
                    {
                        "author": author.author,
                        "article_count": author.article_count,
                        "avg_article_length": round(author.avg_article_length, 1),
                        "influence_score": round(author.influence_score, 2),
                        "most_active_period": author.most_active_period,
                        "top_keywords": author.top_keywords[:3],
                        "productivity": round(author.article_count / days, 2)  # 每天文章数
                    }
                    for author in author_analysis[:15]
                ],
                "author_distribution": {
                    "highly_active": len([a for a in author_analysis if a.article_count >= 5]),
                    "moderately_active": len([a for a in author_analysis if 2 <= a.article_count < 5]),
                    "occasionally_active": len([a for a in author_analysis if a.article_count == 1])
                },
                "analysis_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"作者活跃度分析失败: {str(e)}")
            return {"error": str(e)}
    
    def analyze_publication_patterns(self, days: int = 90) -> Dict[str, Any]:
        """分析文章发布频率和时间分布"""
        logger.info(f"分析最近 {days} 天的发布模式")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if self.db.use_mongodb:
                articles = list(self.db.articles_collection.find({
                    "crawl_time": {"$gte": cutoff_date.isoformat()}
                }))
            else:
                with self.db.get_session() as session:
                    from storage.models import ArticleDB
                    articles = session.query(ArticleDB).filter(
                        ArticleDB.crawl_time >= cutoff_date
                    ).all()
                    articles = [article.to_dict() for article in articles]
            
            if not articles:
                return {"error": "没有找到指定时间范围内的文章"}
            
            # 按日期分组统计
            daily_counts = Counter()
            weekly_counts = Counter()
            monthly_counts = Counter()
            hourly_counts = Counter()
            
            for article in articles:
                article_date = article.get('publish_time', article.get('crawl_time', ''))
                if not article_date:
                    continue
                
                try:
                    if isinstance(article_date, str):
                        date_obj = datetime.fromisoformat(article_date.replace('Z', '+00:00'))
                    else:
                        date_obj = article_date
                    
                    daily_counts[date_obj.strftime('%Y-%m-%d')] += 1
                    weekly_counts[date_obj.strftime('%Y-W%U')] += 1
                    monthly_counts[date_obj.strftime('%Y-%m')] += 1
                    hourly_counts[date_obj.hour] += 1
                    
                except:
                    continue
            
            # 计算统计指标
            daily_values = list(daily_counts.values())
            avg_daily = sum(daily_values) / len(daily_values) if daily_values else 0
            max_daily = max(daily_values) if daily_values else 0
            min_daily = min(daily_values) if daily_values else 0
            
            # 找出最活跃的时间段
            most_active_day = daily_counts.most_common(1)[0] if daily_counts else ("", 0)
            most_active_hour = hourly_counts.most_common(1)[0] if hourly_counts else (0, 0)
            most_active_month = monthly_counts.most_common(1)[0] if monthly_counts else ("", 0)
            
            # 生成时间序列数据
            time_series = []
            cumulative = 0
            for date in sorted(daily_counts.keys()):
                count = daily_counts[date]
                cumulative += count
                time_series.append(TimeSeriesPoint(
                    date=date,
                    count=count,
                    cumulative=cumulative
                ))
            
            return {
                "period_days": days,
                "total_articles": len(articles),
                "daily_statistics": {
                    "average": round(avg_daily, 1),
                    "maximum": max_daily,
                    "minimum": min_daily,
                    "most_active_day": {
                        "date": most_active_day[0],
                        "count": most_active_day[1]
                    }
                },
                "temporal_patterns": {
                    "most_active_hour": {
                        "hour": most_active_hour[0],
                        "count": most_active_hour[1]
                    },
                    "most_active_month": {
                        "month": most_active_month[0],
                        "count": most_active_month[1]
                    }
                },
                "time_series": [
                    {
                        "date": point.date,
                        "count": point.count,
                        "cumulative": point.cumulative
                    }
                    for point in time_series[-30:]  # 最近30天
                ],
                "distribution_summary": {
                    "days_with_articles": len(daily_counts),
                    "active_weeks": len(weekly_counts),
                    "active_months": len(monthly_counts),
                    "coverage_rate": round(len(daily_counts) / days * 100, 1)
                },
                "analysis_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"发布模式分析失败: {str(e)}")
            return {"error": str(e)}
    
    def get_comprehensive_trends(self, days: int = 30) -> Dict[str, Any]:
        """获取综合趋势分析报告"""
        logger.info("生成综合趋势分析报告")
        
        try:
            # 获取各项分析结果
            tech_trends = self.analyze_technology_trends(days)
            author_activity = self.analyze_author_activity(days)
            publication_patterns = self.analyze_publication_patterns(days)
            
            # 生成综合报告
            report = {
                "report_info": {
                    "generated_at": datetime.now().isoformat(),
                    "period_days": days,
                    "analysis_version": "1.0"
                },
                "technology_trends": tech_trends,
                "author_activity": author_activity,
                "publication_patterns": publication_patterns,
                "summary": {
                    "total_articles_analyzed": tech_trends.get("total_articles", 0),
                    "total_authors": author_activity.get("total_authors", 0),
                    "most_discussed_tech": tech_trends.get("top_trends", [{}])[0].get("keyword", "N/A") if tech_trends.get("top_trends") else "N/A",
                    "most_productive_author": author_activity.get("top_authors", [{}])[0].get("author", "N/A") if author_activity.get("top_authors") else "N/A",
                    "daily_average": publication_patterns.get("daily_statistics", {}).get("average", 0)
                }
            }
            
            return report
            
        except Exception as e:
            logger.error(f"综合趋势分析失败: {str(e)}")
            return {"error": str(e)}
        finally:
            self.db.close()


def analyze_keyword_growth(db_path: str, keyword: str, days: int = 60) -> Dict[str, Any]:
    """分析特定关键词的增长趋势"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取包含关键词的文章，按时间分组
        query = """
        SELECT DATE(publish_time) as date, COUNT(*) as count
        FROM articles 
        WHERE (title LIKE ? OR content LIKE ?)
        AND datetime(publish_time) >= datetime('now', '-{} days')
        GROUP BY DATE(publish_time)
        ORDER BY date
        """.format(days)
        
        cursor.execute(query, (f'%{keyword}%', f'%{keyword}%'))
        results = cursor.fetchall()
        
        if not results:
            return {"keyword": keyword, "data": [], "growth_rate": 0}
        
        # 计算增长率
        if len(results) >= 2:
            first_half = results[:len(results)//2]
            second_half = results[len(results)//2:]
            
            first_avg = sum([count for _, count in first_half]) / len(first_half) if first_half else 0
            second_avg = sum([count for _, count in second_half]) / len(second_half) if second_half else 0
            
            growth_rate = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
        else:
            growth_rate = 0
        
        conn.close()
        
        return {
            "keyword": keyword,
            "total_mentions": sum([count for _, count in results]),
            "data": [{"date": date, "count": count} for date, count in results],
            "growth_rate": round(growth_rate, 2),
            "analysis_period": days
        }
        
    except Exception as e:
        logger.error(f"关键词增长分析失败: {str(e)}")
        return {"error": str(e)}