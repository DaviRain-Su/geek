"""
智能标签提取模块
基于文章内容自动提取技术栈、领域、难度等级标签
"""

import re
import json
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from storage.database import DatabaseManager
from utils.logger import logger


@dataclass
class TagInfo:
    """标签信息"""
    name: str
    category: str
    confidence: float
    frequency: int
    related_keywords: List[str]


@dataclass
class ArticleTagging:
    """文章标签结果"""
    article_id: str
    tags: List[TagInfo]
    difficulty_level: str
    main_category: str
    tech_stack: List[str]
    confidence_score: float


class TagExtractor:
    """智能标签提取器"""
    
    def __init__(self, use_mongodb: bool = False):
        self.db = DatabaseManager(use_mongodb=use_mongodb)
        self.initialize_tag_categories()
    
    def initialize_tag_categories(self):
        """初始化标签分类体系"""
        self.tag_categories = {
            # 技术栈分类
            "frontend": {
                "keywords": [
                    'react', 'vue', 'angular', 'svelte', 'next.js', 'nuxt', 'gatsby',
                    'html', 'css', 'javascript', 'typescript', 'scss', 'sass', 'less',
                    'webpack', 'vite', 'rollup', 'parcel', 'babel', 'eslint', 'prettier',
                    'tailwind', 'bootstrap', 'material-ui', 'ant-design', 'chakra-ui'
                ],
                "weight": 1.0
            },
            "backend": {
                "keywords": [
                    'node.js', 'express', 'koa', 'fastify', 'nestjs',
                    'python', 'django', 'flask', 'fastapi', 'tornado',
                    'java', 'spring', 'springboot', 'mybatis', 'hibernate',
                    'go', 'gin', 'echo', 'fiber', 'beego',
                    'rust', 'actix', 'rocket', 'warp', 'axum',
                    'php', 'laravel', 'symfony', 'codeigniter',
                    'ruby', 'rails', 'sinatra'
                ],
                "weight": 1.0
            },
            "database": {
                "keywords": [
                    'mysql', 'postgresql', 'sqlite', 'oracle', 'sql server',
                    'mongodb', 'redis', 'elasticsearch', 'cassandra', 'dynamodb',
                    'neo4j', 'influxdb', 'prometheus', 'clickhouse',
                    'prisma', 'typeorm', 'sequelize', 'mongoose', 'sqlalchemy'
                ],
                "weight": 0.8
            },
            "devops": {
                "keywords": [
                    'docker', 'kubernetes', 'k8s', 'helm', 'istio',
                    'aws', 'azure', 'gcp', 'alibaba cloud', 'tencent cloud',
                    'terraform', 'ansible', 'puppet', 'chef',
                    'jenkins', 'gitlab ci', 'github actions', 'circle ci',
                    'nginx', 'apache', 'traefik', 'envoy',
                    'monitoring', 'grafana', 'prometheus', 'elk', 'datadog'
                ],
                "weight": 0.9
            },
            "ai_ml": {
                "keywords": [
                    'machine learning', 'deep learning', 'neural network',
                    'tensorflow', 'pytorch', 'keras', 'scikit-learn',
                    'opencv', 'pandas', 'numpy', 'matplotlib', 'seaborn',
                    'jupyter', 'anaconda', 'conda',
                    'gpt', 'llm', 'transformer', 'bert', 'chatgpt', 'openai',
                    'computer vision', 'nlp', 'reinforcement learning',
                    'stable diffusion', 'midjourney', 'dall-e'
                ],
                "weight": 1.2
            },
            "blockchain": {
                "keywords": [
                    'blockchain', 'bitcoin', 'ethereum', 'solana', 'polygon',
                    'web3', 'defi', 'nft', 'dao', 'dapp',
                    'smart contract', 'solidity', 'vyper', 'rust', 'move',
                    'metamask', 'uniswap', 'opensea', 'compound',
                    'layer2', 'rollup', 'zk-snark', 'zk-stark',
                    'staking', 'yield farming', 'liquidity mining'
                ],
                "weight": 1.1
            },
            "mobile": {
                "keywords": [
                    'ios', 'android', 'swift', 'kotlin', 'objective-c', 'java',
                    'react native', 'flutter', 'ionic', 'cordova', 'phonegap',
                    'xamarin', 'unity', 'unreal engine',
                    'app store', 'google play', 'testflight'
                ],
                "weight": 0.9
            },
            "security": {
                "keywords": [
                    'cybersecurity', 'penetration testing', 'vulnerability',
                    'encryption', 'ssl', 'tls', 'oauth', 'jwt', 'saml',
                    'firewall', 'waf', 'ddos', 'sql injection', 'xss',
                    'auth', 'authentication', 'authorization', 'rbac',
                    'security audit', 'compliance', 'gdpr', 'hipaa'
                ],
                "weight": 1.0
            }
        }
        
        # 难度级别关键词
        self.difficulty_indicators = {
            "beginner": {
                "keywords": [
                    'tutorial', 'introduction', 'getting started', 'basic', 'simple',
                    'beginner', 'learn', 'guide', 'step by step', 'how to',
                    '入门', '基础', '初学者', '简单', '教程', '指南'
                ],
                "patterns": [
                    r'how\s+to\s+\w+',
                    r'getting\s+started\s+with',
                    r'introduction\s+to',
                    r'basic\s+\w+\s+tutorial'
                ]
            },
            "intermediate": {
                "keywords": [
                    'advanced', 'deep dive', 'best practices', 'optimization',
                    'performance', 'scalability', 'architecture', 'design patterns',
                    '进阶', '优化', '架构', '设计模式', '最佳实践'
                ],
                "patterns": [
                    r'advanced\s+\w+',
                    r'deep\s+dive\s+into',
                    r'best\s+practices\s+for',
                    r'optimizing\s+\w+'
                ]
            },
            "expert": {
                "keywords": [
                    'internals', 'source code', 'implementation', 'algorithm',
                    'complexity', 'research', 'paper', 'thesis', 'academic',
                    '源码', '算法', '原理', '内核', '底层', '研究'
                ],
                "patterns": [
                    r'source\s+code\s+analysis',
                    r'algorithm\s+implementation',
                    r'under\s+the\s+hood',
                    r'research\s+paper'
                ]
            }
        }
        
        # 内容类型指示词
        self.content_types = {
            "tutorial": ['tutorial', 'guide', 'how-to', 'walkthrough', '教程', '指南'],
            "news": ['news', 'announcement', 'release', 'update', '新闻', '发布', '更新'],
            "analysis": ['analysis', 'review', 'comparison', 'benchmark', '分析', '评测', '对比'],
            "opinion": ['opinion', 'thoughts', 'perspective', 'view', '观点', '看法', '思考'],
            "case_study": ['case study', 'example', 'implementation', '案例', '实践', '实现'],
            "tool_review": ['tool', 'library', 'framework', 'review', '工具', '库', '框架', '评测']
        }
    
    def extract_keywords_from_text(self, text: str) -> List[str]:
        """从文本中提取技术关键词"""
        if not text:
            return []
        
        text_lower = text.lower()
        found_keywords = []
        
        # 遍历所有分类的关键词
        for category, info in self.tag_categories.items():
            for keyword in info["keywords"]:
                if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text_lower):
                    found_keywords.append((keyword, category, info["weight"]))
        
        return found_keywords
    
    def assess_difficulty_level(self, title: str, content: str) -> Tuple[str, float]:
        """评估文章难度级别"""
        text = f"{title} {content}".lower()
        scores = {"beginner": 0, "intermediate": 0, "expert": 0}
        
        for level, indicators in self.difficulty_indicators.items():
            # 关键词匹配
            for keyword in indicators["keywords"]:
                if keyword in text:
                    scores[level] += 1
            
            # 模式匹配
            for pattern in indicators.get("patterns", []):
                if re.search(pattern, text):
                    scores[level] += 2
        
        # 内容长度也是难度指标
        content_length = len(content)
        if content_length > 5000:
            scores["expert"] += 1
        elif content_length > 2000:
            scores["intermediate"] += 1
        else:
            scores["beginner"] += 1
        
        # 技术术语密度
        tech_keywords = self.extract_keywords_from_text(text)
        if len(tech_keywords) > 10:
            scores["expert"] += 1
        elif len(tech_keywords) > 5:
            scores["intermediate"] += 1
        
        # 确定最终难度级别
        max_score = max(scores.values())
        if max_score == 0:
            return "intermediate", 0.5  # 默认中等难度
        
        best_level = max(scores, key=scores.get)
        confidence = max_score / sum(scores.values())
        
        return best_level, confidence
    
    def detect_content_type(self, title: str, content: str) -> Tuple[str, float]:
        """检测内容类型"""
        text = f"{title} {content}".lower()
        type_scores = defaultdict(int)
        
        for content_type, keywords in self.content_types.items():
            for keyword in keywords:
                if keyword in text:
                    type_scores[content_type] += 1
        
        if not type_scores:
            return "article", 0.5  # 默认为一般文章
        
        best_type = max(type_scores, key=type_scores.get)
        confidence = type_scores[best_type] / sum(type_scores.values())
        
        return best_type, confidence
    
    def extract_article_tags(self, article: Dict[str, Any]) -> ArticleTagging:
        """为单篇文章提取标签"""
        article_id = str(article.get('id', ''))
        title = article.get('title', '')
        content = article.get('content', '')
        author = article.get('author', '')
        
        # 提取技术关键词
        tech_keywords = self.extract_keywords_from_text(f"{title} {content}")
        
        # 按分类统计标签
        category_scores = defaultdict(lambda: {"count": 0, "keywords": [], "confidence": 0})
        
        for keyword, category, weight in tech_keywords:
            category_scores[category]["count"] += weight
            category_scores[category]["keywords"].append(keyword)
        
        # 生成标签
        tags = []
        tech_stack = []
        
        for category, data in category_scores.items():
            if data["count"] > 0:
                confidence = min(data["count"] / 5, 1.0)  # 最高置信度为1.0
                
                tag_info = TagInfo(
                    name=category,
                    category="技术栈",
                    confidence=confidence,
                    frequency=int(data["count"]),
                    related_keywords=data["keywords"][:5]
                )
                tags.append(tag_info)
                tech_stack.extend(data["keywords"][:3])
        
        # 评估难度级别
        difficulty_level, difficulty_confidence = self.assess_difficulty_level(title, content)
        
        # 检测内容类型
        content_type, type_confidence = self.detect_content_type(title, content)
        
        # 添加难度和类型标签
        tags.append(TagInfo(
            name=difficulty_level,
            category="难度级别",
            confidence=difficulty_confidence,
            frequency=1,
            related_keywords=[]
        ))
        
        tags.append(TagInfo(
            name=content_type,
            category="内容类型",
            confidence=type_confidence,
            frequency=1,
            related_keywords=[]
        ))
        
        # 确定主要分类
        if category_scores:
            main_category = max(category_scores, key=lambda x: category_scores[x]["count"])
        else:
            main_category = "general"
        
        # 计算总体置信度
        overall_confidence = sum(tag.confidence for tag in tags) / len(tags) if tags else 0
        
        return ArticleTagging(
            article_id=article_id,
            tags=tags,
            difficulty_level=difficulty_level,
            main_category=main_category,
            tech_stack=list(set(tech_stack))[:5],
            confidence_score=overall_confidence
        )
    
    def batch_tag_articles(self, limit: int = None) -> Dict[str, Any]:
        """批量为文章添加标签"""
        logger.info("开始批量标签提取")
        
        try:
            # 获取文章数据
            if self.db.use_mongodb:
                query = {}
                if limit:
                    articles = list(self.db.articles_collection.find(query).limit(limit))
                else:
                    articles = list(self.db.articles_collection.find(query))
            else:
                with self.db.get_session() as session:
                    from storage.models import ArticleDB
                    query = session.query(ArticleDB)
                    if limit:
                        query = query.limit(limit)
                    articles = query.all()
                    articles = [article.to_dict() for article in articles]
            
            if not articles:
                return {"error": "没有找到文章数据"}
            
            # 处理每篇文章
            tagged_articles = []
            tag_statistics = defaultdict(Counter)
            
            for article in articles:
                try:
                    tagging_result = self.extract_article_tags(article)
                    tagged_articles.append(tagging_result)
                    
                    # 统计标签频率
                    for tag in tagging_result.tags:
                        tag_statistics[tag.category][tag.name] += 1
                        
                except Exception as e:
                    logger.warning(f"处理文章 {article.get('id', 'unknown')} 时出错: {str(e)}")
                    continue
            
            # 生成统计报告
            summary = {
                "total_articles_processed": len(articles),
                "successfully_tagged": len(tagged_articles),
                "tag_categories": {
                    category: dict(counter.most_common(10))
                    for category, counter in tag_statistics.items()
                },
                "most_common_tags": {
                    "技术栈": dict(tag_statistics["技术栈"].most_common(10)),
                    "难度级别": dict(tag_statistics["难度级别"].most_common()),
                    "内容类型": dict(tag_statistics["内容类型"].most_common())
                },
                "processing_time": datetime.now().isoformat()
            }
            
            return {
                "summary": summary,
                "tagged_articles": [
                    {
                        "article_id": result.article_id,
                        "main_category": result.main_category,
                        "difficulty_level": result.difficulty_level,
                        "tech_stack": result.tech_stack,
                        "confidence_score": round(result.confidence_score, 3),
                        "tags": [
                            {
                                "name": tag.name,
                                "category": tag.category,
                                "confidence": round(tag.confidence, 3),
                                "related_keywords": tag.related_keywords
                            }
                            for tag in result.tags
                        ]
                    }
                    for result in tagged_articles[:50]  # 返回前50个结果用于预览
                ]
            }
            
        except Exception as e:
            logger.error(f"批量标签提取失败: {str(e)}")
            return {"error": str(e)}
    
    def get_tag_recommendations(self, article_text: str) -> List[str]:
        """为新文章推荐标签"""
        try:
            # 创建临时文章对象
            temp_article = {
                "id": "temp",
                "title": article_text[:100],  # 使用前100字符作为标题
                "content": article_text,
                "author": ""
            }
            
            # 提取标签
            tagging_result = self.extract_article_tags(temp_article)
            
            # 返回推荐标签
            recommendations = []
            for tag in tagging_result.tags:
                if tag.confidence > 0.3:  # 置信度阈值
                    recommendations.append(f"{tag.name} ({tag.category})")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"标签推荐失败: {str(e)}")
            return []
    
    def analyze_tag_trends(self, days: int = 30) -> Dict[str, Any]:
        """分析标签趋势"""
        logger.info(f"分析最近 {days} 天的标签趋势")
        
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 获取最近的文章
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
            
            # 提取所有标签
            all_tags = defaultdict(list)
            daily_tags = defaultdict(lambda: defaultdict(int))
            
            for article in articles:
                tagging_result = self.extract_article_tags(article)
                
                # 按日期统计标签
                article_date = article.get('publish_time', article.get('crawl_time', ''))
                if article_date:
                    try:
                        if isinstance(article_date, str):
                            date_obj = datetime.fromisoformat(article_date.replace('Z', '+00:00'))
                        else:
                            date_obj = article_date
                        date_key = date_obj.strftime('%Y-%m-%d')
                        
                        for tag in tagging_result.tags:
                            all_tags[tag.category].append(tag.name)
                            daily_tags[date_key][f"{tag.category}:{tag.name}"] += 1
                    except:
                        continue
            
            # 计算趋势统计
            trending_tags = {}
            for category, tag_list in all_tags.items():
                tag_counter = Counter(tag_list)
                trending_tags[category] = [
                    {"tag": tag, "count": count, "percentage": round(count/len(tag_list)*100, 1)}
                    for tag, count in tag_counter.most_common(10)
                ]
            
            return {
                "period_days": days,
                "total_articles": len(articles),
                "trending_tags": trending_tags,
                "daily_distribution": dict(daily_tags),
                "summary": {
                    "most_popular_category": max(all_tags, key=lambda x: len(all_tags[x])) if all_tags else "无",
                    "total_unique_tags": sum(len(set(tags)) for tags in all_tags.values()),
                    "average_tags_per_article": round(sum(len(tags) for tags in all_tags.values()) / len(articles), 1)
                },
                "analysis_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"标签趋势分析失败: {str(e)}")
            return {"error": str(e)}
        finally:
            self.db.close()